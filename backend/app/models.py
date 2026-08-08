import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship

from .database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)
    is_active = Column(Boolean, default=True)
    theme = Column(String, default="dark")  # "dark" or "light"
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    broker_connections = relationship("BrokerConnection", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    risk_settings = relationship("RiskSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reset_tokens")


class BrokerType(str, enum.Enum):
    mt5 = "mt5"
    oanda = "oanda"
    binance = "binance"


class BrokerConnection(Base):
    __tablename__ = "broker_connections"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    broker_type = Column(Enum(BrokerType), nullable=False)
    label = Column(String, default="My Account")
    # Credentials are never stored in plaintext at rest — encrypted with the app SECRET_KEY.
    encrypted_credentials = Column(Text, nullable=False)
    account_login = Column(String, nullable=True)
    server = Column(String, nullable=True)
    status = Column(String, default="disconnected")  # disconnected | connected | error
    last_error = Column(String, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="broker_connections")


class TradeSide(str, enum.Enum):
    buy = "buy"
    sell = "sell"


class TradeStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    rejected = "rejected"


class Trade(Base):
    __tablename__ = "trades"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    broker_connection_id = Column(String, ForeignKey("broker_connections.id"), nullable=True)
    broker_ticket = Column(String, nullable=True)  # ticket id returned by broker
    symbol = Column(String, nullable=False)
    side = Column(Enum(TradeSide), nullable=False)
    lot_size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    status = Column(Enum(TradeStatus), default=TradeStatus.open)
    profit = Column(Float, default=0.0)
    ai_confidence = Column(Float, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    is_auto = Column(Boolean, default=False)

    user = relationship("User", back_populates="trades")


class RiskSettings(Base):
    __tablename__ = "risk_settings"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)

    risk_percent_per_trade = Column(Float, default=1.0)       # % of equity risked per trade
    daily_loss_limit_percent = Column(Float, default=5.0)     # halt trading after this % daily loss
    daily_profit_target_percent = Column(Float, default=10.0) # optional auto-stop after target hit
    max_drawdown_percent = Column(Float, default=15.0)
    max_open_trades = Column(Integer, default=5)
    default_stop_loss_pips = Column(Float, default=50.0)
    default_take_profit_pips = Column(Float, default=100.0)
    use_trailing_stop = Column(Boolean, default=False)
    trailing_stop_pips = Column(Float, default=20.0)
    use_breakeven = Column(Boolean, default=False)
    breakeven_trigger_pips = Column(Float, default=15.0)
    auto_close_on_daily_loss = Column(Boolean, default=True)
    auto_trading_enabled = Column(Boolean, default=False)

    user = relationship("User", back_populates="risk_settings")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    detail = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    level = Column(String, default="info")  # info | warning | error
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
