"""
Core financial calculations for deal return analysis.

Metrics computed per deal:
- IRR: Internal Rate of Return (annualized, via XIRR)
- ROE: Return on Equity (own capital deployed)
- Annualized Return: Simple P&L annualized by deal duration
- MTM: Mark-to-market unrealized P&L on open positions
"""

from datetime import date


def compute_deal_metrics(
    cash_flows: list[tuple[date, float]],
    capital_deployed: float,
    trade_date: date,
    close_date: date | None,
    hurdle_rate_pct: float = 15.0,
    # MTM inputs (for open deals)
    quantity_mt: float = 0,
    buy_price_per_mt: float = 0,
    latest_market_price: float | None = None,
    latest_market_date: str | None = None,
) -> dict:
    effective_close = close_date or date.today()
    duration_days = (effective_close - trade_date).days
    if duration_days <= 0:
        duration_days = 1

    total_pnl = sum(amount for _, amount in cash_flows)

    roe_pct = (total_pnl / capital_deployed * 100) if capital_deployed > 0 else 0.0

    years = duration_days / 365.0
    annualized_return_pct = (roe_pct / years) if years > 0 else 0.0

    irr_pct = _compute_xirr(cash_flows, trade_date)

    meets_hurdle = annualized_return_pct >= hurdle_rate_pct

    # Mark-to-market for open deals
    unrealized_pnl = None
    mtm_roe_pct = None
    if latest_market_price is not None and close_date is None and quantity_mt > 0:
        unrealized_pnl = round((latest_market_price - buy_price_per_mt) * quantity_mt, 2)
        mtm_roe_pct = round(unrealized_pnl / capital_deployed * 100, 4) if capital_deployed > 0 else 0.0

    return {
        "total_pnl": round(total_pnl, 2),
        "roe_pct": round(roe_pct, 4),
        "annualized_return_pct": round(annualized_return_pct, 4),
        "irr_pct": round(irr_pct, 4) if irr_pct is not None else None,
        "duration_days": duration_days,
        "meets_hurdle": meets_hurdle,
        "hurdle_rate_pct": hurdle_rate_pct,
        "mtm_price": latest_market_price,
        "mtm_date": latest_market_date,
        "unrealized_pnl": unrealized_pnl,
        "mtm_roe_pct": mtm_roe_pct,
    }


def _compute_xirr(
    cash_flows: list[tuple[date, float]], base_date: date
) -> float | None:
    if len(cash_flows) < 2:
        return None

    amounts = [cf[1] for cf in cash_flows]
    if all(a >= 0 for a in amounts) or all(a <= 0 for a in amounts):
        return None

    day_fractions = [(cf[0] - base_date).days / 365.0 for cf in cash_flows]
    amounts = [cf[1] for cf in cash_flows]

    def npv_at_rate(r):
        if r <= -1:
            return float("inf")
        return sum(a / (1.0 + r) ** f for a, f in zip(amounts, day_fractions))

    # Brent's method (root-finding) — pure Python replacement for scipy.optimize.brentq
    try:
        a, b = -0.99, 10.0
        fa, fb = npv_at_rate(a), npv_at_rate(b)
        if fa * fb > 0:
            return None
        for _ in range(1000):
            mid = (a + b) / 2.0
            fmid = npv_at_rate(mid)
            if abs(fmid) < 1e-12 or (b - a) / 2.0 < 1e-12:
                return mid * 100
            if fa * fmid < 0:
                b, fb = mid, fmid
            else:
                a, fa = mid, fmid
        return mid * 100
    except (ValueError, RuntimeError, ZeroDivisionError):
        return None


def compute_portfolio_summary(deal_metrics_list: list[dict], total_firm_capital: float = 200_000_000.0) -> dict:
    if not deal_metrics_list:
        return {
            "total_deals": 0,
            "open_deals": 0,
            "closed_deals": 0,
            "total_capital_deployed": 0,
            "capital_utilization_pct": 0,
            "total_pnl": 0,
            "total_unrealized_pnl": 0,
            "weighted_avg_roe_pct": 0,
            "weighted_avg_annualized_pct": 0,
            "deals_meeting_hurdle": 0,
            "deals_missing_hurdle": 0,
            "hurdle_pass_rate_pct": 0,
            "firm_level_roe_pct": 0,
        }

    total_deals = len(deal_metrics_list)
    total_pnl = sum(d["total_pnl"] for d in deal_metrics_list)
    total_deployed = sum(d["capital_deployed"] for d in deal_metrics_list)
    total_unrealized = sum(d.get("unrealized_pnl") or 0 for d in deal_metrics_list)
    open_deals = sum(1 for d in deal_metrics_list if d.get("status") == "open")
    closed_deals = sum(1 for d in deal_metrics_list if d.get("status") == "closed")

    if total_deployed > 0:
        w_roe = sum(
            d["roe_pct"] * d["capital_deployed"] for d in deal_metrics_list
        ) / total_deployed
        w_ann = sum(
            d["annualized_return_pct"] * d["capital_deployed"]
            for d in deal_metrics_list
        ) / total_deployed
    else:
        w_roe = 0
        w_ann = 0

    meets = sum(1 for d in deal_metrics_list if d["meets_hurdle"])

    return {
        "total_deals": total_deals,
        "open_deals": open_deals,
        "closed_deals": closed_deals,
        "total_capital_deployed": round(total_deployed, 2),
        "capital_utilization_pct": round(total_deployed / total_firm_capital * 100, 2),
        "total_pnl": round(total_pnl, 2),
        "total_unrealized_pnl": round(total_unrealized, 2),
        "weighted_avg_roe_pct": round(w_roe, 4),
        "weighted_avg_annualized_pct": round(w_ann, 4),
        "deals_meeting_hurdle": meets,
        "deals_missing_hurdle": total_deals - meets,
        "hurdle_pass_rate_pct": round(meets / total_deals * 100, 2),
        "firm_level_roe_pct": round(total_pnl / total_firm_capital * 100, 4),
    }
