from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from datetime import date

from app.database import engine, Base, get_db
from app.models import Deal, CashFlow
from app.schemas import (
    DealCreate, DealUpdate, DealOut, CashFlowCreate, CashFlowOut,
    DealMetrics, PortfolioSummary, TraderSummary,
)
from app.financial import compute_deal_metrics, compute_portfolio_summary

FIRM_CAPITAL = 200_000_000.0

Base.metadata.create_all(bind=engine)

app = FastAPI(title="OpenChem Deal Tracker", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")


# ── Deal CRUD ──

@app.post("/api/deals", response_model=DealOut, status_code=201)
def create_deal(deal_in: DealCreate, db: Session = Depends(get_db)):
    existing = db.query(Deal).filter(Deal.deal_ref == deal_in.deal_ref).first()
    if existing:
        raise HTTPException(400, f"Deal ref '{deal_in.deal_ref}' already exists")

    cash_flows_data = deal_in.cash_flows
    deal_dict = deal_in.model_dump(exclude={"cash_flows"})
    deal = Deal(**deal_dict)
    db.add(deal)
    db.flush()

    for cf in cash_flows_data:
        db.add(CashFlow(deal_id=deal.id, **cf.model_dump()))

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
    q = db.query(Deal).options(joinedload(Deal.cash_flows))
    if status:
        q = q.filter(Deal.status == status)
    if trader:
        q = q.filter(Deal.trader == trader)
    if commodity:
        q = q.filter(Deal.commodity == commodity)
    return q.order_by(Deal.trade_date.desc()).all()


@app.get("/api/deals/{deal_id}", response_model=DealOut)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).options(joinedload(Deal.cash_flows)).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    return deal


@app.put("/api/deals/{deal_id}", response_model=DealOut)
def update_deal(deal_id: int, deal_in: DealUpdate, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    for field, value in deal_in.model_dump(exclude_unset=True).items():
        setattr(deal, field, value)
    db.commit()
    db.refresh(deal)
    return deal


@app.delete("/api/deals/{deal_id}", status_code=204)
def delete_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    db.delete(deal)
    db.commit()


# ── Cash Flow CRUD ──

@app.post("/api/deals/{deal_id}/cashflows", response_model=CashFlowOut, status_code=201)
def add_cash_flow(deal_id: int, cf_in: CashFlowCreate, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    cf = CashFlow(deal_id=deal_id, **cf_in.model_dump())
    db.add(cf)
    db.commit()
    db.refresh(cf)
    return cf


@app.delete("/api/cashflows/{cf_id}", status_code=204)
def delete_cash_flow(cf_id: int, db: Session = Depends(get_db)):
    cf = db.query(CashFlow).filter(CashFlow.id == cf_id).first()
    if not cf:
        raise HTTPException(404, "Cash flow not found")
    db.delete(cf)
    db.commit()


# ── Analytics ──

def _deal_to_metrics(deal: Deal) -> dict:
    cf_tuples = [(cf.flow_date, cf.amount) for cf in deal.cash_flows]
    metrics = compute_deal_metrics(
        cash_flows=cf_tuples,
        capital_deployed=deal.total_capital_deployed,
        trade_date=deal.trade_date,
        close_date=deal.actual_close_date,
        hurdle_rate_pct=deal.hurdle_rate_pct,
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
    db: Session = Depends(get_db),
):
    q = db.query(Deal).options(joinedload(Deal.cash_flows))
    if status:
        q = q.filter(Deal.status == status)
    if trader:
        q = q.filter(Deal.trader == trader)
    deals = q.all()
    return [_deal_to_metrics(d) for d in deals]


@app.get("/api/analytics/portfolio", response_model=PortfolioSummary)
def portfolio_analytics(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Deal).options(joinedload(Deal.cash_flows))
    if status:
        q = q.filter(Deal.status == status)
    deals = q.all()
    metrics_list = [_deal_to_metrics(d) for d in deals]
    return compute_portfolio_summary(metrics_list, FIRM_CAPITAL)


@app.get("/api/analytics/traders", response_model=list[TraderSummary])
def trader_analytics(db: Session = Depends(get_db)):
    deals = db.query(Deal).options(joinedload(Deal.cash_flows)).all()
    all_metrics = [_deal_to_metrics(d) for d in deals]

    traders: dict[str, list[dict]] = {}
    for m in all_metrics:
        traders.setdefault(m["trader"], []).append(m)

    result = []
    for trader_name, deal_list in sorted(traders.items()):
        total_cap = sum(d["capital_deployed"] for d in deal_list)
        total_pnl = sum(d["total_pnl"] for d in deal_list)
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
            weighted_avg_annualized_pct=round(w_ann, 4),
            hurdle_pass_rate_pct=round(meets / len(deal_list) * 100, 2),
        ))
    return result


@app.get("/api/config")
def get_config():
    return {"firm_capital": FIRM_CAPITAL}
