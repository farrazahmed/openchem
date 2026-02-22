"""
Seed script: creates users and sample Urea/Steel/Sulphur deals.
Run: python seed_data.py
"""

from datetime import date
from app.database import engine, SessionLocal, Base
from app.models import Deal, CashFlow, MarketPrice, User, AuditLog
from app.auth import hash_password

Base.metadata.create_all(bind=engine)

USERS = [
    {"username": "admin", "full_name": "Admin", "email": "admin@openchem.com",
     "password": "admin123", "role": "admin", "desk": None},
    {"username": "farraz", "full_name": "Farraz Ahmed", "email": "farraz@openchem.com",
     "password": "pass123", "role": "trader", "desk": "Fertilizers"},
    {"username": "omar", "full_name": "Omar Khalid", "email": "omar@openchem.com",
     "password": "pass123", "role": "trader", "desk": "Steel"},
    {"username": "li.wei", "full_name": "Li Wei", "email": "li.wei@openchem.com",
     "password": "pass123", "role": "trader", "desk": "Sulphur"},
    {"username": "priya", "full_name": "Priya Sharma", "email": "priya@openchem.com",
     "password": "pass123", "role": "viewer", "desk": None},
]

DEALS = [
    # ── UREA ──
    {
        "deal": {
            "deal_ref": "OC-2025-001",
            "commodity": "Urea (Granular)",
            "trader": "Farraz Ahmed",
            "desk": "Fertilizers",
            "counterparty_buy": "Ma'aden (Saudi Arabia)",
            "counterparty_sell": "IFFCO (India)",
            "quantity_mt": 25000,
            "buy_price_per_mt": 310.00,
            "sell_price_per_mt": 335.00,
            "total_capital_deployed": 3_500_000,
            "leverage_amount": 4_250_000,
            "trade_date": date(2025, 7, 1),
            "expected_close_date": date(2025, 9, 15),
            "actual_close_date": date(2025, 9, 10),
            "hurdle_rate_pct": 15.0,
            "status": "closed",
            "created_by": "farraz",
            "notes": "Jubail to Kandla. Smooth execution, good margin.",
        },
        "cash_flows": [
            ("initial_outflow", -3_500_000, date(2025, 7, 1), "Equity + LC margin"),
            ("financing_cost", -42_000, date(2025, 7, 15), "LC issuance + LIBOR margin"),
            ("freight_cost", -280_000, date(2025, 7, 10), "Handymax Jubail-Kandla"),
            ("insurance_cost", -18_000, date(2025, 7, 1), "Cargo insurance"),
            ("inspection_cost", -8_000, date(2025, 7, 5), "SGS inspection at load port"),
            ("hedge_pnl", 25_000, date(2025, 9, 1), "Urea swap hedge gain"),
            ("final_settlement", 4_148_000, date(2025, 9, 10), "IFFCO LC payment"),
        ],
    },
    {
        "deal": {
            "deal_ref": "OC-2025-002",
            "commodity": "Urea (Prilled)",
            "trader": "Farraz Ahmed",
            "desk": "Fertilizers",
            "counterparty_buy": "OCP (Morocco)",
            "counterparty_sell": "Coromandel International (India)",
            "quantity_mt": 30000,
            "buy_price_per_mt": 295.00,
            "sell_price_per_mt": 318.00,
            "total_capital_deployed": 4_000_000,
            "leverage_amount": 4_850_000,
            "trade_date": date(2025, 10, 15),
            "expected_close_date": date(2026, 1, 15),
            "actual_close_date": date(2026, 1, 10),
            "hurdle_rate_pct": 15.0,
            "status": "closed",
            "created_by": "farraz",
            "notes": "Jorf Lasfar to Vizag. Minor quality dispute resolved.",
        },
        "cash_flows": [
            ("initial_outflow", -4_000_000, date(2025, 10, 15), "Capital deployed"),
            ("financing_cost", -58_000, date(2025, 11, 1), "Trade finance interest (90d)"),
            ("freight_cost", -350_000, date(2025, 10, 25), "Supramax Morocco-Vizag"),
            ("insurance_cost", -22_000, date(2025, 10, 15), "Marine cargo insurance"),
            ("inspection_cost", -12_000, date(2025, 10, 20), "Intertek load + discharge"),
            ("demurrage", -35_000, date(2025, 12, 20), "Discharge port demurrage 2 days"),
            ("final_settlement", 4_527_000, date(2026, 1, 10), "Coromandel payment"),
        ],
    },
    {
        "deal": {
            "deal_ref": "OC-2026-003",
            "commodity": "Urea (Granular)",
            "trader": "Farraz Ahmed",
            "desk": "Fertilizers",
            "counterparty_buy": "QAFCO (Qatar)",
            "counterparty_sell": "ETG (East Africa)",
            "quantity_mt": 20000,
            "buy_price_per_mt": 320.00,
            "sell_price_per_mt": 348.00,
            "total_capital_deployed": 3_000_000,
            "leverage_amount": 3_400_000,
            "trade_date": date(2026, 1, 5),
            "expected_close_date": date(2026, 4, 15),
            "actual_close_date": None,
            "hurdle_rate_pct": 15.0,
            "status": "open",
            "created_by": "farraz",
            "notes": "Mesaieed to Dar es Salaam. Vessel loading.",
        },
        "cash_flows": [
            ("initial_outflow", -3_000_000, date(2026, 1, 5), "Equity deployed"),
            ("financing_cost", -38_000, date(2026, 1, 20), "LC + financing charges"),
            ("freight_cost", -240_000, date(2026, 1, 12), "Handymax Qatar-Dar"),
            ("insurance_cost", -16_000, date(2026, 1, 5), "Cargo insurance"),
        ],
        "mtm": [
            (date(2026, 1, 15), 325.00, "Argus"),
            (date(2026, 2, 1), 332.00, "Argus"),
            (date(2026, 2, 15), 340.00, "Argus"),
        ],
    },
    # ── STEEL ──
    {
        "deal": {
            "deal_ref": "OC-2025-004",
            "commodity": "Steel (HRC)",
            "trader": "Omar Khalid",
            "desk": "Steel",
            "counterparty_buy": "ArcelorMittal (CIS)",
            "counterparty_sell": "Al Tuwairqi (Saudi Arabia)",
            "quantity_mt": 10000,
            "buy_price_per_mt": 520.00,
            "sell_price_per_mt": 555.00,
            "total_capital_deployed": 5_000_000,
            "leverage_amount": 200_000,
            "trade_date": date(2025, 8, 15),
            "expected_close_date": date(2025, 11, 30),
            "actual_close_date": date(2025, 11, 25),
            "hurdle_rate_pct": 15.0,
            "status": "closed",
            "created_by": "omar",
            "notes": "Black Sea to Jeddah. Good arb on CIS discount.",
        },
        "cash_flows": [
            ("initial_outflow", -5_000_000, date(2025, 8, 15), "Capital deployed"),
            ("financing_cost", -72_000, date(2025, 9, 1), "Trade finance"),
            ("freight_cost", -180_000, date(2025, 8, 25), "Bulk carrier Black Sea-Jeddah"),
            ("insurance_cost", -28_000, date(2025, 8, 15), "Cargo + war risk insurance"),
            ("customs_duty", -55_000, date(2025, 11, 10), "Saudi import duty"),
            ("final_settlement", 5_490_000, date(2025, 11, 25), "Al Tuwairqi payment"),
        ],
    },
    {
        "deal": {
            "deal_ref": "OC-2025-005",
            "commodity": "Steel (Rebar)",
            "trader": "Omar Khalid",
            "desk": "Steel",
            "counterparty_buy": "Tosyali (Turkey)",
            "counterparty_sell": "Dangote Industries (Nigeria)",
            "quantity_mt": 15000,
            "buy_price_per_mt": 490.00,
            "sell_price_per_mt": 475.00,
            "total_capital_deployed": 6_000_000,
            "leverage_amount": 1_350_000,
            "trade_date": date(2025, 9, 1),
            "expected_close_date": date(2025, 12, 15),
            "actual_close_date": date(2025, 12, 20),
            "hurdle_rate_pct": 15.0,
            "status": "closed",
            "created_by": "omar",
            "notes": "Iskenderun to Lagos. Market dropped during transit - loss maker.",
        },
        "cash_flows": [
            ("initial_outflow", -6_000_000, date(2025, 9, 1), "Capital deployed"),
            ("financing_cost", -85_000, date(2025, 9, 15), "Trade finance interest"),
            ("freight_cost", -320_000, date(2025, 9, 10), "Supramax Turkey-Lagos"),
            ("insurance_cost", -35_000, date(2025, 9, 1), "Cargo insurance"),
            ("demurrage", -48_000, date(2025, 12, 5), "Lagos port congestion 4 days"),
            ("customs_duty", -110_000, date(2025, 12, 10), "Nigeria import levy"),
            ("final_settlement", 5_998_000, date(2025, 12, 20), "Dangote payment - discounted"),
        ],
    },
    {
        "deal": {
            "deal_ref": "OC-2026-006",
            "commodity": "Steel (Billet)",
            "trader": "Omar Khalid",
            "desk": "Steel",
            "counterparty_buy": "JSW Steel (India)",
            "counterparty_sell": "Azovstal (via trader, UAE)",
            "quantity_mt": 12000,
            "buy_price_per_mt": 450.00,
            "sell_price_per_mt": 478.00,
            "total_capital_deployed": 4_500_000,
            "leverage_amount": 900_000,
            "trade_date": date(2026, 1, 20),
            "expected_close_date": date(2026, 4, 30),
            "actual_close_date": None,
            "hurdle_rate_pct": 15.0,
            "status": "open",
            "created_by": "omar",
            "notes": "Mormugao to Jebel Ali. In transit.",
        },
        "cash_flows": [
            ("initial_outflow", -4_500_000, date(2026, 1, 20), "Equity deployed"),
            ("financing_cost", -55_000, date(2026, 2, 1), "Trade finance charges"),
            ("freight_cost", -200_000, date(2026, 1, 28), "Handymax India-UAE"),
            ("insurance_cost", -25_000, date(2026, 1, 20), "Marine insurance"),
        ],
        "mtm": [
            (date(2026, 2, 1), 458.00, "Platts"),
            (date(2026, 2, 10), 465.00, "Platts"),
            (date(2026, 2, 20), 470.00, "Platts"),
        ],
    },
    # ── SULPHUR ──
    {
        "deal": {
            "deal_ref": "OC-2025-007",
            "commodity": "Sulphur (Granular)",
            "trader": "Li Wei",
            "desk": "Sulphur",
            "counterparty_buy": "ADNOC (UAE)",
            "counterparty_sell": "OCP (Morocco)",
            "quantity_mt": 35000,
            "buy_price_per_mt": 128.00,
            "sell_price_per_mt": 148.00,
            "total_capital_deployed": 2_500_000,
            "leverage_amount": 1_980_000,
            "trade_date": date(2025, 11, 1),
            "expected_close_date": date(2026, 1, 31),
            "actual_close_date": date(2026, 1, 25),
            "hurdle_rate_pct": 15.0,
            "status": "closed",
            "created_by": "li.wei",
            "notes": "Ruwais to Jorf Lasfar. Strong sulphur demand from phosphate season.",
        },
        "cash_flows": [
            ("initial_outflow", -2_500_000, date(2025, 11, 1), "Capital deployed"),
            ("financing_cost", -32_000, date(2025, 11, 15), "LC charges"),
            ("freight_cost", -210_000, date(2025, 11, 10), "Handymax Ruwais-Jorf Lasfar"),
            ("insurance_cost", -15_000, date(2025, 11, 1), "Cargo insurance"),
            ("storage_cost", -20_000, date(2025, 12, 1), "Terminal storage Jorf"),
            ("hedge_pnl", 18_000, date(2026, 1, 15), "Sulphur forward hedge"),
            ("final_settlement", 3_059_000, date(2026, 1, 25), "OCP payment"),
        ],
    },
    {
        "deal": {
            "deal_ref": "OC-2026-008",
            "commodity": "Sulphur (Lump)",
            "trader": "Li Wei",
            "desk": "Sulphur",
            "counterparty_buy": "Kuwait Petroleum Corp",
            "counterparty_sell": "Yunnan Yuntianhua (China)",
            "quantity_mt": 40000,
            "buy_price_per_mt": 118.00,
            "sell_price_per_mt": 138.00,
            "total_capital_deployed": 2_800_000,
            "leverage_amount": 1_920_000,
            "trade_date": date(2026, 2, 1),
            "expected_close_date": date(2026, 5, 15),
            "actual_close_date": None,
            "hurdle_rate_pct": 15.0,
            "status": "open",
            "created_by": "li.wei",
            "notes": "Shuaiba to Fangcheng. Vessel nominated, loading next week.",
        },
        "cash_flows": [
            ("initial_outflow", -2_800_000, date(2026, 2, 1), "Equity deployed"),
            ("financing_cost", -35_000, date(2026, 2, 10), "Trade finance charges"),
            ("insurance_cost", -18_000, date(2026, 2, 1), "Cargo insurance"),
        ],
        "mtm": [
            (date(2026, 2, 10), 122.00, "Argus"),
            (date(2026, 2, 20), 126.00, "Argus"),
        ],
    },
]


def seed():
    db = SessionLocal()
    try:
        db.query(AuditLog).delete()
        db.query(MarketPrice).delete()
        db.query(CashFlow).delete()
        db.query(Deal).delete()
        db.query(User).delete()
        db.commit()

        # Create users
        for u in USERS:
            db.add(User(
                username=u["username"],
                full_name=u["full_name"],
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                role=u["role"],
                desk=u["desk"],
            ))
        db.commit()
        print(f"Created {len(USERS)} users (admin/admin123, traders use pass123)")

        # Create deals
        for entry in DEALS:
            deal = Deal(**entry["deal"])
            db.add(deal)
            db.flush()

            for cf_type, amount, cf_date, desc in entry["cash_flows"]:
                db.add(CashFlow(
                    deal_id=deal.id,
                    flow_type=cf_type,
                    amount=amount,
                    flow_date=cf_date,
                    description=desc,
                ))

            for mtm_date, price, source in entry.get("mtm", []):
                db.add(MarketPrice(
                    deal_id=deal.id,
                    price_date=mtm_date,
                    market_price_per_mt=price,
                    source=source,
                ))

            db.commit()

        print(f"Seeded {len(DEALS)} deals with cash flows and MTM prices.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
