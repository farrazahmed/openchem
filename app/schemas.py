from pydantic import BaseModel, Field
from datetime import date, datetime


# ── Auth ──

class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    full_name: str
    email: str | None = None
    password: str = Field(..., min_length=4)
    role: str = "trader"
    desk: str | None = None


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    email: str | None
    role: str
    desk: str | None
    is_active: bool
    created_at: datetime | None

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


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


# ── Market Price (Mark-to-Market) ──

class MarketPriceCreate(BaseModel):
    price_date: date
    market_price_per_mt: float
    source: str | None = "manual"


class MarketPriceOut(BaseModel):
    id: int
    deal_id: int
    price_date: date
    market_price_per_mt: float
    source: str | None
    created_at: datetime | None

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
    created_by: str | None
    created_at: datetime | None
    updated_at: datetime | None
    cash_flows: list[CashFlowOut] = []
    market_prices: list[MarketPriceOut] = []

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
    # MTM fields
    mtm_price: float | None = None
    mtm_date: str | None = None
    unrealized_pnl: float | None = None
    mtm_roe_pct: float | None = None


class PortfolioSummary(BaseModel):
    total_deals: int
    open_deals: int
    closed_deals: int
    total_capital_deployed: float
    capital_utilization_pct: float
    total_pnl: float
    total_unrealized_pnl: float
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
    total_unrealized_pnl: float
    weighted_avg_annualized_pct: float
    hurdle_pass_rate_pct: float


# ── Audit ──

class AuditLogOut(BaseModel):
    id: int
    timestamp: datetime | None
    user: str
    action: str
    entity_type: str
    entity_id: int | None
    deal_ref: str | None
    details: str | None
    before_state: str | None
    after_state: str | None

    model_config = {"from_attributes": True}
