from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------- Auth ----------
class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


# ---------- User ----------
class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    theme: str
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    theme: Optional[str] = None  # "dark" | "light"


# ---------- Broker ----------
class MT5ConnectRequest(BaseModel):
    login: str
    password: str
    server: str
    label: Optional[str] = "MT5 Account"
    terminal_path: Optional[str] = None


class BrokerConnectionOut(BaseModel):
    id: str
    broker_type: str
    label: str
    account_login: Optional[str]
    server: Optional[str]
    status: str
    last_error: Optional[str]
    last_checked: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Trading ----------
class PlaceOrderRequest(BaseModel):
    broker_connection_id: str
    symbol: str
    side: str  # "buy" | "sell"
    lot_size: Optional[float] = None
    risk_percent: Optional[float] = None  # if lot_size omitted, calculate from risk
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    is_auto: bool = False


class ModifyOrderRequest(BaseModel):
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class TradeOut(BaseModel):
    id: str
    symbol: str
    side: str
    lot_size: float
    entry_price: float
    exit_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    status: str
    profit: float
    ai_confidence: Optional[float]
    ai_explanation: Optional[str]
    opened_at: datetime
    closed_at: Optional[datetime]
    is_auto: bool

    class Config:
        from_attributes = True


# ---------- Risk ----------
class RiskSettingsOut(BaseModel):
    risk_percent_per_trade: float
    daily_loss_limit_percent: float
    daily_profit_target_percent: float
    max_drawdown_percent: float
    max_open_trades: int
    default_stop_loss_pips: float
    default_take_profit_pips: float
    use_trailing_stop: bool
    trailing_stop_pips: float
    use_breakeven: bool
    breakeven_trigger_pips: float
    auto_close_on_daily_loss: bool
    auto_trading_enabled: bool

    class Config:
        from_attributes = True


class RiskSettingsUpdate(BaseModel):
    risk_percent_per_trade: Optional[float] = None
    daily_loss_limit_percent: Optional[float] = None
    daily_profit_target_percent: Optional[float] = None
    max_drawdown_percent: Optional[float] = None
    max_open_trades: Optional[int] = None
    default_stop_loss_pips: Optional[float] = None
    default_take_profit_pips: Optional[float] = None
    use_trailing_stop: Optional[bool] = None
    trailing_stop_pips: Optional[float] = None
    use_breakeven: Optional[bool] = None
    breakeven_trigger_pips: Optional[float] = None
    auto_close_on_daily_loss: Optional[bool] = None
    auto_trading_enabled: Optional[bool] = None


class LotCalculatorRequest(BaseModel):
    account_balance: float
    risk_percent: float
    stop_loss_pips: float
    pip_value_per_lot: float = 10.0  # standard for most FX pairs; override for others


class LotCalculatorResponse(BaseModel):
    lot_size: float
    risk_amount: float
    formula: str


# ---------- AI ----------
class AIAnalysisResponse(BaseModel):
    symbol: str
    timeframe: str
    trend: str
    confidence: float
    support_levels: List[float]
    resistance_levels: List[float]
    volatility_atr: float
    market_structure: str
    bos_choch: Optional[str]
    fair_value_gaps: List[dict]
    order_blocks: List[dict]
    supply_zones: List[dict]
    demand_zones: List[dict]
    session: str
    recommendation: str
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    explanation: str
    generated_at: datetime


# ---------- Admin ----------
class AdminUserOut(UserOut):
    is_active: bool


class SystemHealthOut(BaseModel):
    status: str
    database: str
    uptime_seconds: float
    total_users: int
    active_broker_connections: int
    open_trades: int
