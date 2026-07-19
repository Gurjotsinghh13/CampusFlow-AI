from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.schemas.common import APIResponse
from app.schemas.constraint import ConstraintCreate, ConstraintRead, ConstraintUpdate
from app.services.constraint import ConstraintService

router = APIRouter(prefix="/constraints", tags=["Constraints"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=APIResponse[ConstraintRead])
def get_constraints(db: Session = Depends(get_db)):
    obj = ConstraintService(db).get_constraints()
    return APIResponse(data=ConstraintRead.model_validate(obj))


@router.put("", response_model=APIResponse[ConstraintRead])
def save_constraints(payload: ConstraintCreate, db: Session = Depends(get_db)):
    obj = ConstraintService(db).save_constraints(payload)
    return APIResponse(message="Constraints saved", data=ConstraintRead.model_validate(obj))


@router.patch("", response_model=APIResponse[ConstraintRead])
def patch_constraints(payload: ConstraintUpdate, db: Session = Depends(get_db)):
    obj = ConstraintService(db).patch_constraints(payload)
    return APIResponse(message="Constraints updated", data=ConstraintRead.model_validate(obj))
