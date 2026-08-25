from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all_models import Fault, FaultComment, FaultHistory
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/faults/{fault_id}/comments", tags=["comments"])


def log_history(
    db: Session,
    fault_id: int,
    event_type: str,
    field: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    author: str = "system",
):
    """Запись события в историю"""
    history = FaultHistory(
        fault_id=fault_id,
        event_type=event_type,
        field=field,
        old_value=old_value,
        new_value=new_value,
        author=author,
    )
    db.add(history)
    db.commit()


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    fault_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Добавить комментарий к неисправности"""
    fault = db.query(Fault).filter(Fault.id == fault_id).first()
    if not fault:
        raise HTTPException(status_code=404, detail="Неисправность не найдена")

    db_comment = FaultComment(
        fault_id=fault_id,
        content=comment.content,
        is_internal=1 if comment.is_internal else 0,
        author=current_user.username,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    # ✅ Записываем в историю добавление комментария
    log_history(
        db=db,
        fault_id=fault_id,
        event_type="comment",
        field="comment",
        old_value=None,
        new_value=f"Добавлен комментарий: {comment.content[:50]}{'...' if len(comment.content) > 50 else ''}",
        author=current_user.username,
    )

    return db_comment


@router.get("/", response_model=List[CommentResponse])
def get_comments(
    fault_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Получить все комментарии к неисправности"""
    comments = (
        db.query(FaultComment)
        .filter(FaultComment.fault_id == fault_id)
        .order_by(FaultComment.created_at.desc())
        .all()
    )
    return comments
