from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.all_models import Fault, FaultComment
from app.schemas.comment import CommentCreate, CommentResponse

router = APIRouter(prefix="/faults/{fault_id}/comments", tags=["comments"])


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    fault_id: int, comment: CommentCreate, db: Session = Depends(get_db)
):
    """Добавить комментарий к неисправности"""
    fault = db.query(Fault).filter(Fault.id == fault_id).first()
    if not fault:
        raise HTTPException(status_code=404, detail="Неисправность не найдена")

    db_comment = FaultComment(
        fault_id=fault_id,
        content=comment.content,
        is_internal=1 if comment.is_internal else 0,
        author=comment.author,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


@router.get("/", response_model=List[CommentResponse])
def get_comments(fault_id: int, db: Session = Depends(get_db)):
    """Получить все комментарии к неисправности"""
    comments = (
        db.query(FaultComment)
        .filter(FaultComment.fault_id == fault_id)
        .order_by(FaultComment.created_at.desc())
        .all()
    )
    return comments
