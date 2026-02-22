"""
Core financial calculations for deal return analysis.

All return metrics are computed from the deal's cash flow series:
- IRR: Internal Rate of Return (annualized)
- ROE: Return on Equity (own capital deployed)
- Annualized Return: Simple P&L annualized by deal duration
"""

import numpy as np
from scipy.optimize import brentq
from datetime import date


def compute_deal_metrics(
    cash_flows: list[tuple[date, float]],
    capital_deployed: float,
    trade_date: date,
    close_date: date | None,
    hurdle_rate_pct: float = 15.0,
) -> dict:
    """
    Compute all return metrics for a single deal.

    Args:
        cash_flows: List of (date, amount) tuples. Outflows negative, inflows positive.
        capital_deployed: Own equity deployed (positive number).
        trade_date: Deal inception date.
        close_date: Actual close date (None if still open).
        hurdle_rate_pct: Required annualized return % (e.g. 15.0 for 15%).

    Returns:
        Dict with irr_pct, roe_pct, annualized_return_pct, total_pnl,
        duration_days, meets_hurdle, hurdle_rate_pct.
    """
    effective_close = close_date or date.today()
    duration_days = (effective_close - trade_date).days
    if duration_days <= 0:
        duration_days = 1

    # Total P&L is sum of all cash flows
    total_pnl = sum(amount for _, amount in cash_flows)

    # ROE = total P&L / own capital deployed
    roe_pct = (total_pnl / capital_deployed * 100) if capital_deployed > 0 else 0.0

    # Annualized return (simple)
    years = duration_days / 365.0
    annualized_return_pct = (roe_pct / years) if years > 0 else 0.0

    # IRR via XIRR (day-weighted internal rate of return)
    irr_pct = _compute_xirr(cash_flows, trade_date)

    meets_hurdle = annualized_return_pct >= hurdle_rate_pct

    return {
        "total_pnl": round(total_pnl, 2),
        "roe_pct": round(roe_pct, 4),
        "annualized_return_pct": round(annualized_return_pct, 4),
        "irr_pct": round(irr_pct, 4) if irr_pct is not None else None,
        "duration_days": duration_days,
        "meets_hurdle": meets_hurdle,
        "hurdle_rate_pct": hurdle_rate_pct,
    }


def _compute_xirr(
    cash_flows: list[tuple[date, float]], base_date: date
) -> float | None:
    """
    Compute XIRR (annualized IRR for irregular cash flows).

    Uses the standard XIRR formula:
        sum_i [ CF_i / (1 + r) ^ ((d_i - d_0) / 365) ] = 0

    Returns annualized rate as percentage, or None if not solvable.
    """
    if len(cash_flows) < 2:
        return None

    # Need at least one positive and one negative flow
    amounts = [cf[1] for cf in cash_flows]
    if all(a >= 0 for a in amounts) or all(a <= 0 for a in amounts):
        return None

    day_fractions = [(cf[0] - base_date).days / 365.0 for cf in cash_flows]
    amounts_arr = np.array([cf[1] for cf in cash_flows])
    fractions_arr = np.array(day_fractions)

    def npv_at_rate(r):
        if r <= -1:
            return float("inf")
        return np.sum(amounts_arr / (1.0 + r) ** fractions_arr)

    try:
        irr = brentq(npv_at_rate, -0.99, 10.0, maxiter=1000)
        return irr * 100  # Convert to percentage
    except (ValueError, RuntimeError):
        return None


def compute_portfolio_summary(deal_metrics_list: list[dict], total_firm_capital: float = 200_000_000.0) -> dict:
    """
    Aggregate portfolio-level metrics across all deals.

    Args:
        deal_metrics_list: List of dicts from compute_deal_metrics, each
                           augmented with 'capital_deployed'.
        total_firm_capital: Total firm equity (default $200M).
    """
    if not deal_metrics_list:
        return {
            "total_deals": 0,
            "total_capital_deployed": 0,
            "capital_utilization_pct": 0,
            "total_pnl": 0,
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

    # Capital-weighted average ROE and annualized return
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
        "total_capital_deployed": round(total_deployed, 2),
        "capital_utilization_pct": round(total_deployed / total_firm_capital * 100, 2),
        "total_pnl": round(total_pnl, 2),
        "weighted_avg_roe_pct": round(w_roe, 4),
        "weighted_avg_annualized_pct": round(w_ann, 4),
        "deals_meeting_hurdle": meets,
        "deals_missing_hurdle": total_deals - meets,
        "hurdle_pass_rate_pct": round(meets / total_deals * 100, 2),
        "firm_level_roe_pct": round(total_pnl / total_firm_capital * 100, 4),
    }
