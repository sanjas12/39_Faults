from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.all_models import Fault
from app.schemas.fault import FaultCreate, FaultResponse

router = APIRouter(prefix="/faults", tags=["faults"])


@router.post("/", response_model=FaultResponse)
def create_fault(fault: FaultCreate, db: Session = Depends(get_db)):
    db_fault = Fault(**fault.model_dump())
    db.add(db_fault)
    db.commit()
    db.refresh(db_fault)
    return db_fault


@router.get("/", response_model=List[FaultResponse])
def list_faults(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    faults = db.query(Fault).offset(skip).limit(limit).all()
    return faults


@router.get("/{fault_id}", response_model=FaultResponse)
def get_fault(fault_id: int, db: Session = Depends(get_db)):
    fault = db.query(Fault).filter(Fault.id == fault_id).first()
    if not fault:
        raise HTTPException(status_code=404, detail="Неисправность не найдена")
    return fault
