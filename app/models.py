from sqlalchemy import (
    Column, Integer, Float, String, Date, DateTime, Enum, ForeignKey, Text,
    func,
)
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class DealStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class CashFlowType(str, enum.Enum):
    INITIAL_OUTFLOW = "initial_outflow"        # Capital deployed at deal start
    MARGIN_CALL = "margin_call"                # Additional capital calls
    FINANCING_COST = "financing_cost"          # LC costs, interest, bank charges
    STORAGE_COST = "storage_cost"              # Warehousing / tank rental
    FREIGHT_COST = "freight_cost"              # Shipping / logistics
    INSURANCE_COST = "insurance_cost"          # Cargo / credit insurance
    HEDGE_PNL = "hedge_pnl"                    # Futures / options hedge P&L
    INTERIM_RECEIPT = "interim_receipt"         # Partial payments received
    FINAL_SETTLEMENT = "final_settlement"      # Final sale proceeds


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

    # Quantities
    quantity_mt = Column(Float, nullable=False)  # Metric tonnes
    buy_price_per_mt = Column(Float, nullable=False)
    sell_price_per_mt = Column(Float, nullable=False)

    # Capital
    total_capital_deployed = Column(Float, nullable=False)  # Own funds used
    leverage_amount = Column(Float, default=0.0)  # Borrowed funds if any

    # Dates
    trade_date = Column(Date, nullable=False)
    expected_close_date = Column(Date, nullable=False)
    actual_close_date = Column(Date, nullable=True)

    # Hurdle
    hurdle_rate_pct = Column(Float, default=15.0)  # Required annualized ROE %

    # Notes
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    cash_flows = relationship("CashFlow", back_populates="deal", cascade="all, delete-orphan")


class CashFlow(Base):
    __tablename__ = "cash_flows"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    flow_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)  # Negative = outflow, Positive = inflow
    flow_date = Column(Date, nullable=False)
    description = Column(String(300), nullable=True)

    deal = relationship("Deal", back_populates="cash_flows")
