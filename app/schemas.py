from pydantic import BaseModel, Field
from datetime import date, datetime


# ── Cash Flow ──

class CashFlowCreate(BaseModel):
    flow_type: str
    amount: float
    flow_date: date
    description: str | None = None


class CashFlowOut(BaseModel):
    id: int
    deal_id: int
    flow_type: str
    amount: float
    flow_date: date
    description: str | None

    model_config = {"from_attributes": True}


# ── Deal ──

class DealCreate(BaseModel):
    deal_ref: str = Field(..., max_length=50)
    commodity: str
    trader: str
    desk: str | None = None
    counterparty_buy: str
    counterparty_sell: str
    quantity_mt: float = Field(..., gt=0)
    buy_price_per_mt: float = Field(..., gt=0)
    sell_price_per_mt: float = Field(..., gt=0)
    total_capital_deployed: float = Field(..., gt=0)
    leverage_amount: float = Field(default=0.0, ge=0)
    trade_date: date
    expected_close_date: date
    actual_close_date: date | None = None
    hurdle_rate_pct: float = Field(default=15.0, ge=0)
    status: str = "open"
    notes: str | None = None
    cash_flows: list[CashFlowCreate] = Field(default_factory=list)


class DealUpdate(BaseModel):
    commodity: str | None = None
    trader: str | None = None
    desk: str | None = None
    counterparty_buy: str | None = None
    counterparty_sell: str | None = None
    quantity_mt: float | None = None
    buy_price_per_mt: float | None = None
    sell_price_per_mt: float | None = None
    total_capital_deployed: float | None = None
    leverage_amount: float | None = None
    expected_close_date: date | None = None
    actual_close_date: date | None = None
    hurdle_rate_pct: float | None = None
    status: str | None = None
    notes: str | None = None


class DealOut(BaseModel):
    id: int
    deal_ref: str
    commodity: str
    trader: str
    desk: str | None
    counterparty_buy: str
    counterparty_sell: str
    status: str
    quantity_mt: float
    buy_price_per_mt: float
    sell_price_per_mt: float
    total_capital_deployed: float
    leverage_amount: float
    trade_date: date
    expected_close_date: date
    actual_close_date: date | None
    hurdle_rate_pct: float
    notes: str | None
    created_at: datetime | None
    updated_at: datetime | None
    cash_flows: list[CashFlowOut] = []

    model_config = {"from_attributes": True}


# ── Analytics ──

class DealMetrics(BaseModel):
    deal_id: int
    deal_ref: str
    commodity: str
    trader: str
    status: str
    capital_deployed: float
    total_pnl: float
    roe_pct: float
    annualized_return_pct: float
    irr_pct: float | None
    duration_days: int
    meets_hurdle: bool
    hurdle_rate_pct: float


class PortfolioSummary(BaseModel):
    total_deals: int
    total_capital_deployed: float
    capital_utilization_pct: float
    total_pnl: float
    weighted_avg_roe_pct: float
    weighted_avg_annualized_pct: float
    deals_meeting_hurdle: int
    deals_missing_hurdle: int
    hurdle_pass_rate_pct: float
    firm_level_roe_pct: float


class TraderSummary(BaseModel):
    trader: str
    deal_count: int
    total_capital_deployed: float
    total_pnl: float
    weighted_avg_annualized_pct: float
    hurdle_pass_rate_pct: float
