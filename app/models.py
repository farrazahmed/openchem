from sqlalchemy import (
    Column, Integer, Float, String, Date, DateTime, Boolean, ForeignKey, Text,
    JSON, func,
)
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class DealStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class CashFlowType(str, enum.Enum):
    INITIAL_OUTFLOW = "initial_outflow"
    MARGIN_CALL = "margin_call"
    FINANCING_COST = "financing_cost"
    STORAGE_COST = "storage_cost"
    FREIGHT_COST = "freight_cost"
    INSURANCE_COST = "insurance_cost"
    HEDGE_PNL = "hedge_pnl"
    INTERIM_RECEIPT = "interim_receipt"
    FINAL_SETTLEMENT = "final_settlement"
    DEMURRAGE = "demurrage"
    INSPECTION_COST = "inspection_cost"
    CUSTOMS_DUTY = "customs_duty"


# ── Users ──

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=True)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False, default="trader")  # admin, trader, viewer
    desk = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


# ── Deals ──

class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    deal_ref = Column(String(50), unique=True, nullable=False, index=True)
    commodity = Column(String(100), nullable=False)
    trader = Column(String(100), nullable=False)
    desk = Column(String(100), nullable=True)
    counterparty_buy = Column(String(200), nullable=False)
    counterparty_sell = Column(String(200), nullable=False)
    status = Column(String(20), default=DealStatus.OPEN.value, nullable=False)

    quantity_mt = Column(Float, nullable=False)
    buy_price_per_mt = Column(Float, nullable=False)
    sell_price_per_mt = Column(Float, nullable=False)

    total_capital_deployed = Column(Float, nullable=False)
    leverage_amount = Column(Float, default=0.0)

    trade_date = Column(Date, nullable=False)
    expected_close_date = Column(Date, nullable=False)
    actual_close_date = Column(Date, nullable=True)

    hurdle_rate_pct = Column(Float, default=15.0)

    notes = Column(Text, nullable=True)

    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    cash_flows = relationship("CashFlow", back_populates="deal", cascade="all, delete-orphan")
    market_prices = relationship("MarketPrice", back_populates="deal", cascade="all, delete-orphan")


class CashFlow(Base):
    __tablename__ = "cash_flows"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    flow_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    flow_date = Column(Date, nullable=False)
    description = Column(String(300), nullable=True)

    deal = relationship("Deal", back_populates="cash_flows")


# ── Mark-to-Market ──

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    price_date = Column(Date, nullable=False)
    market_price_per_mt = Column(Float, nullable=False)
    source = Column(String(100), nullable=True)  # e.g. "Argus", "Platts", "manual"
    created_at = Column(DateTime, server_default=func.now())

    deal = relationship("Deal", back_populates="market_prices")


# ── Audit Trail ──

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    user = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)  # create, update, delete
    entity_type = Column(String(50), nullable=False)  # deal, cash_flow, market_price
    entity_id = Column(Integer, nullable=True)
    deal_ref = Column(String(50), nullable=True, index=True)
    details = Column(Text, nullable=True)  # JSON string of changes
    before_state = Column(Text, nullable=True)  # JSON snapshot before
    after_state = Column(Text, nullable=True)  # JSON snapshot after
