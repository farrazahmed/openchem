"""
Seed script to populate the database with sample commodity trading deals.
Run: python seed_data.py
"""

from datetime import date
from app.database import engine, SessionLocal, Base
from app.models import Deal, CashFlow

Base.metadata.create_all(bind=engine)

DEALS = [
    {
        "deal": {
            "deal_ref": "OC-2026-001",
            "commodity": "Crude Oil (Brent)",
            "trader": "Ahmed Khan",
            "desk": "Energy",
            "counterparty_buy": "Saudi Aramco",
            "counterparty_sell": "Reliance Industries",
            "quantity_mt": 50000,
            "buy_price_per_mt": 580.00,
            "sell_price_per_mt": 598.00,
            "total_capital_deployed": 8_000_000,
            "leverage_amount": 21_000_000,
            "trade_date": date(2025, 9, 1),
            "expected_close_date": date(2025, 11, 15),
            "actual_close_date": date(2025, 11, 10),
            "hurdle_rate_pct": 15.0,
            "status": "closed",
            "notes": "VLCC cargo Ras Tanura to Jamnagar. Clean execution.",
        },
        "cash_flows": [
            ("initial_outflow", -8_000_000, date(2025, 9, 1), "Equity deployed for margin + LC"),
            ("financing_cost", -120_000, date(2025, 9, 15), "LC issuance fee 0.15%"),
            ("insurance_cost", -45_000, date(2025, 9, 1), "Cargo insurance"),
            ("freight_cost", -650_000, date(2025, 9, 10), "VLCC charter Ras Tanura-Jamnagar"),
            ("hedge_pnl", 80_000, date(2025, 11, 1), "Brent futures hedge closed at profit"),
            ("final_settlement", 9_715_000, date(2025, 11, 10), "Final payment from Reliance"),
        ],
    },
    {
        "deal": {
            "deal_ref": "OC-2026-002",
            "commodity": "Copper Cathode",
            "trader": "Sarah Chen",
            "desk": "Metals",
            "counterparty_buy": "Codelco",
            "counterparty_sell": "Jiangxi Copper",
            "quantity_mt": 5000,
            "buy_price_per_mt": 8200.00,
            "sell_price_per_mt": 8420.00,
            "total_capital_deployed": 12_000_000,
            "leverage_amount": 29_000_000,
            "trade_date": date(2025, 10, 1),
            "expected_close_date": date(2026, 1, 31),
            "actual_close_date": date(2026, 1, 20),
            "hurdle_rate_pct": 15.0,
            "status": "closed",
            "notes": "Chilean copper to China. Good arb on LME spread.",
        },
        "cash_flows": [
            ("initial_outflow", -12_000_000, date(2025, 10, 1), "Equity for LC margin"),
            ("financing_cost", -180_000, date(2025, 10, 15), "Trade finance interest (3mo)"),
            ("storage_cost", -30_000, date(2025, 11, 1), "Bonded warehouse Antofagasta"),
            ("freight_cost", -450_000, date(2025, 10, 20), "Bulk carrier Chile-Shanghai"),
            ("insurance_cost", -60_000, date(2025, 10, 1), "Marine cargo + credit insurance"),
            ("hedge_pnl", -120_000, date(2026, 1, 15), "LME hedge loss on spread"),
            ("final_settlement", 13_260_000, date(2026, 1, 20), "Jiangxi Copper payment received"),
        ],
    },
    {
        "deal": {
            "deal_ref": "OC-2026-003",
            "commodity": "Wheat (SRW)",
            "trader": "Mike Torres",
            "desk": "Agriculture",
            "counterparty_buy": "Cargill",
            "counterparty_sell": "Egyptian GASC",
            "quantity_mt": 30000,
            "buy_price_per_mt": 245.00,
            "sell_price_per_mt": 262.00,
            "total_capital_deployed": 3_500_000,
            "leverage_amount": 3_850_000,
            "trade_date": date(2025, 11, 15),
            "expected_close_date": date(2026, 2, 28),
            "actual_close_date": date(2026, 2, 15),
            "hurdle_rate_pct": 15.0,
            "status": "closed",
            "notes": "US Gulf to Alexandria. GASC tender won.",
        },
        "cash_flows": [
            ("initial_outflow", -3_500_000, date(2025, 11, 15), "Capital deployed"),
            ("financing_cost", -52_000, date(2025, 12, 1), "Bank financing cost"),
            ("freight_cost", -380_000, date(2025, 11, 25), "Panamax US Gulf-Alexandria"),
            ("insurance_cost", -25_000, date(2025, 11, 15), "Cargo insurance"),
            ("hedge_pnl", 45_000, date(2026, 2, 1), "CBOT wheat hedge gain"),
            ("final_settlement", 4_022_000, date(2026, 2, 15), "GASC payment (LC sight)"),
        ],
    },
    {
        "deal": {
            "deal_ref": "OC-2026-004",
            "commodity": "LNG",
            "trader": "Ahmed Khan",
            "desk": "Energy",
            "counterparty_buy": "QatarEnergy",
            "counterparty_sell": "KOGAS",
            "quantity_mt": 65000,
            "buy_price_per_mt": 420.00,
            "sell_price_per_mt": 445.00,
            "total_capital_deployed": 15_000_000,
            "leverage_amount": 12_300_000,
            "trade_date": date(2025, 12, 1),
            "expected_close_date": date(2026, 3, 15),
            "actual_close_date": None,
            "hurdle_rate_pct": 15.0,
            "status": "open",
            "notes": "Q-Flex cargo Ras Laffan to Pyeongtaek. In transit.",
        },
        "cash_flows": [
            ("initial_outflow", -15_000_000, date(2025, 12, 1), "Equity margin deployed"),
            ("financing_cost", -210_000, date(2025, 12, 15), "SBLC + financing charges"),
            ("insurance_cost", -95_000, date(2025, 12, 1), "LNG cargo insurance"),
            ("freight_cost", -820_000, date(2025, 12, 5), "Q-Flex charter"),
            ("interim_receipt", 5_000_000, date(2026, 1, 15), "Provisional payment 1 from KOGAS"),
        ],
    },
    {
        "deal": {
            "deal_ref": "OC-2026-005",
            "commodity": "Iron Ore (62% Fe)",
            "trader": "Sarah Chen",
            "desk": "Metals",
            "counterparty_buy": "Vale",
            "counterparty_sell": "Baosteel",
            "quantity_mt": 80000,
            "buy_price_per_mt": 105.00,
            "sell_price_per_mt": 112.50,
            "total_capital_deployed": 5_000_000,
            "leverage_amount": 3_400_000,
            "trade_date": date(2026, 1, 10),
            "expected_close_date": date(2026, 4, 30),
            "actual_close_date": None,
            "hurdle_rate_pct": 15.0,
            "status": "open",
            "notes": "Capesize Tubarao to Baoshan. Vessel loading.",
        },
        "cash_flows": [
            ("initial_outflow", -5_000_000, date(2026, 1, 10), "Capital deployed"),
            ("financing_cost", -75_000, date(2026, 1, 20), "Trade finance cost"),
            ("freight_cost", -520_000, date(2026, 1, 15), "Capesize charter Brazil-China"),
            ("insurance_cost", -35_000, date(2026, 1, 10), "Marine insurance"),
        ],
    },
    {
        "deal": {
            "deal_ref": "OC-2026-006",
            "commodity": "Palm Oil (CPO)",
            "trader": "Mike Torres",
            "desk": "Agriculture",
            "counterparty_buy": "Sime Darby",
            "counterparty_sell": "Adani Wilmar",
            "quantity_mt": 10000,
            "buy_price_per_mt": 850.00,
            "sell_price_per_mt": 878.00,
            "total_capital_deployed": 2_500_000,
            "leverage_amount": 6_000_000,
            "trade_date": date(2025, 8, 1),
            "expected_close_date": date(2025, 10, 15),
            "actual_close_date": date(2025, 10, 20),
            "hurdle_rate_pct": 15.0,
            "status": "closed",
            "notes": "Malaysian CPO to Mundra. Slight delay due to port congestion.",
        },
        "cash_flows": [
            ("initial_outflow", -2_500_000, date(2025, 8, 1), "Equity deployed"),
            ("financing_cost", -38_000, date(2025, 8, 15), "LC charges"),
            ("freight_cost", -180_000, date(2025, 8, 10), "Handymax Malaysia-Mundra"),
            ("insurance_cost", -18_000, date(2025, 8, 1), "Cargo insurance"),
            ("storage_cost", -15_000, date(2025, 10, 1), "Port storage - congestion delay"),
            ("hedge_pnl", -35_000, date(2025, 10, 15), "MDEX CPO futures loss"),
            ("final_settlement", 2_834_000, date(2025, 10, 20), "Adani Wilmar final payment"),
        ],
    },
    {
        "deal": {
            "deal_ref": "OC-2026-007",
            "commodity": "Aluminium",
            "trader": "Sarah Chen",
            "desk": "Metals",
            "counterparty_buy": "Rusal",
            "counterparty_sell": "Norsk Hydro",
            "quantity_mt": 3000,
            "buy_price_per_mt": 2350.00,
            "sell_price_per_mt": 2310.00,
            "total_capital_deployed": 4_000_000,
            "leverage_amount": 3_050_000,
            "trade_date": date(2025, 7, 1),
            "expected_close_date": date(2025, 9, 30),
            "actual_close_date": date(2025, 10, 5),
            "hurdle_rate_pct": 15.0,
            "status": "closed",
            "notes": "Loss-making deal. Market moved against us. Lesson: tighter stops needed.",
        },
        "cash_flows": [
            ("initial_outflow", -4_000_000, date(2025, 7, 1), "Capital deployed"),
            ("financing_cost", -62_000, date(2025, 7, 15), "Trade finance interest"),
            ("storage_cost", -40_000, date(2025, 8, 1), "LME warehouse Rotterdam"),
            ("freight_cost", -95_000, date(2025, 7, 10), "Freight cost"),
            ("insurance_cost", -22_000, date(2025, 7, 1), "Insurance"),
            ("hedge_pnl", -180_000, date(2025, 9, 25), "LME aluminium hedge loss"),
            ("final_settlement", 3_851_000, date(2025, 10, 5), "Sale proceeds - below cost"),
        ],
    },
    {
        "deal": {
            "deal_ref": "OC-2026-008",
            "commodity": "Crude Oil (WTI)",
            "trader": "Ahmed Khan",
            "desk": "Energy",
            "counterparty_buy": "ConocoPhillips",
            "counterparty_sell": "Sinopec",
            "quantity_mt": 40000,
            "buy_price_per_mt": 555.00,
            "sell_price_per_mt": 582.00,
            "total_capital_deployed": 10_000_000,
            "leverage_amount": 12_200_000,
            "trade_date": date(2025, 6, 15),
            "expected_close_date": date(2025, 9, 15),
            "actual_close_date": date(2025, 9, 10),
            "hurdle_rate_pct": 15.0,
            "status": "closed",
            "notes": "US Gulf to Qingdao. Strong Brent-WTI arb.",
        },
        "cash_flows": [
            ("initial_outflow", -10_000_000, date(2025, 6, 15), "Equity margin"),
            ("financing_cost", -145_000, date(2025, 7, 1), "LC + financing"),
            ("freight_cost", -750_000, date(2025, 6, 20), "Suezmax US Gulf-Qingdao"),
            ("insurance_cost", -55_000, date(2025, 6, 15), "Cargo + P&I insurance"),
            ("hedge_pnl", 210_000, date(2025, 9, 1), "WTI-Brent spread hedge profit"),
            ("final_settlement", 11_820_000, date(2025, 9, 10), "Sinopec payment via LC"),
        ],
    },
]


def seed():
    db = SessionLocal()
    try:
        # Clear existing data
        db.query(CashFlow).delete()
        db.query(Deal).delete()
        db.commit()

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
            db.commit()

        print(f"Seeded {len(DEALS)} deals with cash flows.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
