import csv
import io
import json
from datetime import date, datetime

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload

from app.database import engine, Base, get_db
from app.models import Deal, CashFlow, MarketPrice, AuditLog, User
from app.schemas import (
    DealCreate, DealUpdate, DealOut, CashFlowCreate, CashFlowOut,
    MarketPriceCreate, MarketPriceOut,
    DealMetrics, PortfolioSummary, TraderSummary,
    UserCreate, UserOut, TokenOut, AuditLogOut,
)
from app.financial import compute_deal_metrics, compute_portfolio_summary
from app.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_auth, require_admin,
)
from app.audit import log_action

FIRM_CAPITAL = 200_000_000.0

Base.metadata.create_all(bind=engine)

app = FastAPI(title="OpenChem Deal Tracker", version="2.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")


# ═══════════════════════════════════════
# AUTH
# ═══════════════════════════════════════

@app.post("/api/auth/register", response_model=UserOut, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(400, "Username already exists")
    user = User(
        username=user_in.username,
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,
        desk=user_in.desk,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, user=user_in.username, action="create", entity_type="user",
               entity_id=user.id, details=f"Registered user {user_in.username}")
    db.commit()
    return user


@app.post("/api/auth/login", response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(403, "Account disabled")
    token = create_access_token({"sub": user.username})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(require_auth)):
    return user


@app.get("/api/auth/users", response_model=list[UserOut])
def list_users(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.full_name).all()


# ═══════════════════════════════════════
# DEAL CRUD
# ═══════════════════════════════════════

def _username(user: User | None) -> str:
    return user.username if user else "system"


@app.post("/api/deals", response_model=DealOut, status_code=201)
def create_deal(
    deal_in: DealCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    existing = db.query(Deal).filter(Deal.deal_ref == deal_in.deal_ref).first()
    if existing:
        raise HTTPException(400, f"Deal ref '{deal_in.deal_ref}' already exists")

    cash_flows_data = deal_in.cash_flows
    deal_dict = deal_in.model_dump(exclude={"cash_flows"})
    deal_dict["created_by"] = _username(user)
    deal = Deal(**deal_dict)
    db.add(deal)
    db.flush()

    for cf in cash_flows_data:
        db.add(CashFlow(deal_id=deal.id, **cf.model_dump()))

    log_action(db, user=_username(user), action="create", entity_type="deal",
               entity_id=deal.id, deal_ref=deal.deal_ref,
               details=f"Created deal {deal.deal_ref}", after=deal)
    db.commit()
    db.refresh(deal)
    return deal


@app.get("/api/deals", response_model=list[DealOut])
def list_deals(
    status: str | None = None,
    trader: str | None = None,
    commodity: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Deal).options(joinedload(Deal.cash_flows), joinedload(Deal.market_prices))
    if status:
        q = q.filter(Deal.status == status)
    if trader:
        q = q.filter(Deal.trader == trader)
    if commodity:
        q = q.filter(Deal.commodity == commodity)
    return q.order_by(Deal.trade_date.desc()).all()


@app.get("/api/deals/{deal_id}", response_model=DealOut)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = (db.query(Deal)
            .options(joinedload(Deal.cash_flows), joinedload(Deal.market_prices))
            .filter(Deal.id == deal_id).first())
    if not deal:
        raise HTTPException(404, "Deal not found")
    return deal


@app.put("/api/deals/{deal_id}", response_model=DealOut)
def update_deal(
    deal_id: int,
    deal_in: DealUpdate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")

    changes = {}
    for field, value in deal_in.model_dump(exclude_unset=True).items():
        old = getattr(deal, field)
        if old != value:
            changes[field] = {"from": str(old), "to": str(value)}
        setattr(deal, field, value)

    if changes:
        log_action(db, user=_username(user), action="update", entity_type="deal",
                   entity_id=deal.id, deal_ref=deal.deal_ref,
                   details=json.dumps(changes), after=deal)
    db.commit()
    db.refresh(deal)
    return deal


@app.delete("/api/deals/{deal_id}", status_code=204)
def delete_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    log_action(db, user=_username(user), action="delete", entity_type="deal",
               entity_id=deal.id, deal_ref=deal.deal_ref,
               details=f"Deleted deal {deal.deal_ref}", before=deal)
    db.delete(deal)
    db.commit()


# ═══════════════════════════════════════
# CASH FLOW CRUD
# ═══════════════════════════════════════

@app.post("/api/deals/{deal_id}/cashflows", response_model=CashFlowOut, status_code=201)
def add_cash_flow(
    deal_id: int,
    cf_in: CashFlowCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    cf = CashFlow(deal_id=deal_id, **cf_in.model_dump())
    db.add(cf)
    db.flush()
    log_action(db, user=_username(user), action="create", entity_type="cash_flow",
               entity_id=cf.id, deal_ref=deal.deal_ref,
               details=f"Added {cf.flow_type}: ${cf.amount:,.2f}")
    db.commit()
    db.refresh(cf)
    return cf


@app.delete("/api/cashflows/{cf_id}", status_code=204)
def delete_cash_flow(
    cf_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    cf = db.query(CashFlow).filter(CashFlow.id == cf_id).first()
    if not cf:
        raise HTTPException(404, "Cash flow not found")
    deal = db.query(Deal).filter(Deal.id == cf.deal_id).first()
    log_action(db, user=_username(user), action="delete", entity_type="cash_flow",
               entity_id=cf.id, deal_ref=deal.deal_ref if deal else None,
               details=f"Deleted {cf.flow_type}: ${cf.amount:,.2f}", before=cf)
    db.delete(cf)
    db.commit()


# ═══════════════════════════════════════
# MARK-TO-MARKET
# ═══════════════════════════════════════

@app.post("/api/deals/{deal_id}/mtm", response_model=MarketPriceOut, status_code=201)
def add_market_price(
    deal_id: int,
    mp_in: MarketPriceCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    mp = MarketPrice(deal_id=deal_id, **mp_in.model_dump())
    db.add(mp)
    db.flush()
    log_action(db, user=_username(user), action="create", entity_type="market_price",
               entity_id=mp.id, deal_ref=deal.deal_ref,
               details=f"MTM: ${mp.market_price_per_mt:,.2f}/MT on {mp.price_date} ({mp.source})")
    db.commit()
    db.refresh(mp)
    return mp


@app.get("/api/deals/{deal_id}/mtm", response_model=list[MarketPriceOut])
def list_market_prices(deal_id: int, db: Session = Depends(get_db)):
    return (db.query(MarketPrice)
            .filter(MarketPrice.deal_id == deal_id)
            .order_by(MarketPrice.price_date.desc()).all())


@app.delete("/api/mtm/{mp_id}", status_code=204)
def delete_market_price(
    mp_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    mp = db.query(MarketPrice).filter(MarketPrice.id == mp_id).first()
    if not mp:
        raise HTTPException(404, "Market price not found")
    deal = db.query(Deal).filter(Deal.id == mp.deal_id).first()
    log_action(db, user=_username(user), action="delete", entity_type="market_price",
               entity_id=mp.id, deal_ref=deal.deal_ref if deal else None,
               details=f"Deleted MTM ${mp.market_price_per_mt}/MT")
    db.delete(mp)
    db.commit()


# ═══════════════════════════════════════
# ANALYTICS
# ═══════════════════════════════════════

def _deal_to_metrics(deal: Deal) -> dict:
    cf_tuples = [(cf.flow_date, cf.amount) for cf in deal.cash_flows]

    latest_mp = None
    latest_mp_date = None
    if deal.market_prices:
        sorted_prices = sorted(deal.market_prices, key=lambda p: p.price_date, reverse=True)
        latest_mp = sorted_prices[0].market_price_per_mt
        latest_mp_date = sorted_prices[0].price_date.isoformat()

    metrics = compute_deal_metrics(
        cash_flows=cf_tuples,
        capital_deployed=deal.total_capital_deployed,
        trade_date=deal.trade_date,
        close_date=deal.actual_close_date,
        hurdle_rate_pct=deal.hurdle_rate_pct,
        quantity_mt=deal.quantity_mt,
        buy_price_per_mt=deal.buy_price_per_mt,
        latest_market_price=latest_mp,
        latest_market_date=latest_mp_date,
    )
    metrics["deal_id"] = deal.id
    metrics["deal_ref"] = deal.deal_ref
    metrics["commodity"] = deal.commodity
    metrics["trader"] = deal.trader
    metrics["status"] = deal.status
    metrics["capital_deployed"] = deal.total_capital_deployed
    return metrics


@app.get("/api/analytics/deals", response_model=list[DealMetrics])
def deal_analytics(
    status: str | None = None,
    trader: str | None = None,
    commodity: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Deal).options(joinedload(Deal.cash_flows), joinedload(Deal.market_prices))
    if status:
        q = q.filter(Deal.status == status)
    if trader:
        q = q.filter(Deal.trader == trader)
    if commodity:
        q = q.filter(Deal.commodity == commodity)
    deals = q.all()
    return [_deal_to_metrics(d) for d in deals]


@app.get("/api/analytics/portfolio", response_model=PortfolioSummary)
def portfolio_analytics(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Deal).options(joinedload(Deal.cash_flows), joinedload(Deal.market_prices))
    if status:
        q = q.filter(Deal.status == status)
    deals = q.all()
    metrics_list = [_deal_to_metrics(d) for d in deals]
    return compute_portfolio_summary(metrics_list, FIRM_CAPITAL)


@app.get("/api/analytics/traders", response_model=list[TraderSummary])
def trader_analytics(db: Session = Depends(get_db)):
    deals = db.query(Deal).options(joinedload(Deal.cash_flows), joinedload(Deal.market_prices)).all()
    all_metrics = [_deal_to_metrics(d) for d in deals]

    traders: dict[str, list[dict]] = {}
    for m in all_metrics:
        traders.setdefault(m["trader"], []).append(m)

    result = []
    for trader_name, deal_list in sorted(traders.items()):
        total_cap = sum(d["capital_deployed"] for d in deal_list)
        total_pnl = sum(d["total_pnl"] for d in deal_list)
        total_unreal = sum(d.get("unrealized_pnl") or 0 for d in deal_list)
        w_ann = (
            sum(d["annualized_return_pct"] * d["capital_deployed"] for d in deal_list) / total_cap
            if total_cap > 0 else 0
        )
        meets = sum(1 for d in deal_list if d["meets_hurdle"])
        result.append(TraderSummary(
            trader=trader_name,
            deal_count=len(deal_list),
            total_capital_deployed=round(total_cap, 2),
            total_pnl=round(total_pnl, 2),
            total_unrealized_pnl=round(total_unreal, 2),
            weighted_avg_annualized_pct=round(w_ann, 4),
            hurdle_pass_rate_pct=round(meets / len(deal_list) * 100, 2),
        ))
    return result


# ═══════════════════════════════════════
# AUDIT TRAIL
# ═══════════════════════════════════════

@app.get("/api/audit", response_model=list[AuditLogOut])
def get_audit_log(
    deal_ref: str | None = None,
    entity_type: str | None = None,
    limit: int = Query(default=200, le=1000),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLog)
    if deal_ref:
        q = q.filter(AuditLog.deal_ref == deal_ref)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    return q.order_by(AuditLog.timestamp.desc()).limit(limit).all()


# ═══════════════════════════════════════
# CSV EXPORT
# ═══════════════════════════════════════

@app.get("/api/export/deals")
def export_deals_csv(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Deal).options(joinedload(Deal.cash_flows), joinedload(Deal.market_prices))
    if status:
        q = q.filter(Deal.status == status)
    deals = q.all()
    metrics = [_deal_to_metrics(d) for d in deals]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Deal Ref", "Commodity", "Trader", "Desk", "Buy From", "Sell To",
        "Qty (MT)", "Buy $/MT", "Sell $/MT", "Capital Deployed", "Leverage",
        "Trade Date", "Exp Close", "Act Close", "Status",
        "Total P&L", "ROE %", "Annualized Return %", "IRR %",
        "Duration Days", "Hurdle %", "Meets Hurdle",
        "MTM Price", "Unrealized P&L",
    ])

    deal_map = {d.id: d for d in deals}
    for m in metrics:
        d = deal_map[m["deal_id"]]
        writer.writerow([
            d.deal_ref, d.commodity, d.trader, d.desk or "",
            d.counterparty_buy, d.counterparty_sell,
            d.quantity_mt, d.buy_price_per_mt, d.sell_price_per_mt,
            d.total_capital_deployed, d.leverage_amount,
            d.trade_date, d.expected_close_date, d.actual_close_date or "",
            d.status,
            m["total_pnl"], m["roe_pct"], m["annualized_return_pct"],
            m["irr_pct"] or "", m["duration_days"],
            m["hurdle_rate_pct"], "YES" if m["meets_hurdle"] else "NO",
            m.get("mtm_price") or "", m.get("unrealized_pnl") or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=openchem_deals_{date.today()}.csv"},
    )


@app.get("/api/export/audit")
def export_audit_csv(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(5000).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "User", "Action", "Entity Type", "Entity ID", "Deal Ref", "Details"])
    for log in logs:
        writer.writerow([
            log.timestamp, log.user, log.action, log.entity_type,
            log.entity_id or "", log.deal_ref or "", log.details or "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=openchem_audit_{date.today()}.csv"},
    )


# ═══════════════════════════════════════
# CSV IMPORT
# ═══════════════════════════════════════

@app.post("/api/import/deals")
async def import_deals_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    created = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        try:
            deal_ref = row.get("Deal Ref", "").strip()
            if not deal_ref:
                errors.append(f"Row {i}: Missing Deal Ref")
                continue
            if db.query(Deal).filter(Deal.deal_ref == deal_ref).first():
                errors.append(f"Row {i}: Deal {deal_ref} already exists, skipped")
                continue

            deal = Deal(
                deal_ref=deal_ref,
                commodity=row.get("Commodity", "").strip(),
                trader=row.get("Trader", "").strip(),
                desk=row.get("Desk", "").strip() or None,
                counterparty_buy=row.get("Buy From", "").strip(),
                counterparty_sell=row.get("Sell To", "").strip(),
                quantity_mt=float(row.get("Qty (MT)", 0)),
                buy_price_per_mt=float(row.get("Buy $/MT", 0)),
                sell_price_per_mt=float(row.get("Sell $/MT", 0)),
                total_capital_deployed=float(row.get("Capital Deployed", 0)),
                leverage_amount=float(row.get("Leverage", 0) or 0),
                trade_date=_parse_date(row.get("Trade Date", "")),
                expected_close_date=_parse_date(row.get("Exp Close", "")),
                actual_close_date=_parse_date(row.get("Act Close", "")) if row.get("Act Close", "").strip() else None,
                status=row.get("Status", "open").strip().lower(),
                hurdle_rate_pct=float(row.get("Hurdle %", 15) or 15),
                created_by=_username(user),
            )
            db.add(deal)
            db.flush()
            log_action(db, user=_username(user), action="create", entity_type="deal",
                       entity_id=deal.id, deal_ref=deal.deal_ref,
                       details=f"Imported from CSV: {deal.deal_ref}")
            created += 1
        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")

    db.commit()
    return {"created": created, "errors": errors}


def _parse_date(s: str) -> date:
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {s}")


# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════

@app.get("/api/config")
def get_config():
    return {
        "firm_capital": FIRM_CAPITAL,
        "commodities": [
            "Urea (Granular)", "Urea (Prilled)",
            "Steel (HRC)", "Steel (Rebar)", "Steel (Billet)",
            "Sulphur (Granular)", "Sulphur (Lump)",
        ],
        "desks": ["Fertilizers", "Steel", "Sulphur"],
    }
