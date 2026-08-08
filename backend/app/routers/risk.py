from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import RiskSettings, User
from ..schemas import RiskSettingsOut, RiskSettingsUpdate

router = APIRouter(prefix="/api/risk", tags=["risk"])


def _get_or_create(db: Session, user_id: str) -> RiskSettings:
    risk = db.query(RiskSettings).filter(RiskSettings.user_id == user_id).first()
    if not risk:
        risk = RiskSettings(user_id=user_id)
        db.add(risk)
        db.commit()
        db.refresh(risk)
    return risk


@router.get("/settings", response_model=RiskSettingsOut)
def get_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_or_create(db, current_user.id)


@router.put("/settings", response_model=RiskSettingsOut)
def update_settings(
    payload: RiskSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    risk = _get_or_create(db, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(risk, field, value)
    db.commit()
    db.refresh(risk)
    return risk
