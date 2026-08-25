import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all_models import Fault, FaultAttachment, FaultHistory
from app.schemas.attachment import AttachmentResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/faults/{fault_id}/attachments", tags=["attachments"])

# Папка для хранения файлов
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

print(f"📁 Папка для загрузок: {UPLOAD_DIR}")


def log_history(
    db: Session,
    fault_id: int,
    event_type: str,
    field: str,
    old_value: str = None,
    new_value: str = None,
    author: str = "system",
):
    """Запись события в историю"""
    try:
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
    except Exception as e:
        print(f"❌ Ошибка записи истории: {e}")
        db.rollback()


@router.post(
    "/", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED
)
async def upload_attachment(
    fault_id: int,
    file: UploadFile = File(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Загрузить файл к неисправности"""
    print(f"📤 Загрузка файла для неисправности #{fault_id}")

    fault = db.query(Fault).filter(Fault.id == fault_id).first()
    if not fault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Неисправность не найдена"
        )

    # Проверяем размер файла (максимум 10MB)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Файл слишком большой. Максимальный размер 10MB",
        )

    # Создаём папку для неисправности
    fault_dir = UPLOAD_DIR / str(fault_id)
    fault_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = (
        f"{timestamp}_{current_user.username}_{file.filename.replace(' ', '_')}"
    )
    file_path = fault_dir / safe_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"✅ Файл сохранён: {file_path}")
    except Exception as e:
        print(f"❌ Ошибка сохранения файла: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сохранения файла: {str(e)}",
        ) from e

    # Создаём запись в БД
    attachment = FaultAttachment(
        fault_id=fault_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        file_type=file.content_type or "application/octet-stream",
        description=description,
        uploaded_by=current_user.username,
    )

    try:
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        print(f"✅ Запись в БД создана: {attachment.id}")
    except Exception as e:
        print(f"❌ Ошибка записи в БД: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка записи в БД: {str(e)}",
        ) from e

    # ✅ Записываем в историю
    log_history(
        db=db,
        fault_id=fault_id,
        event_type="field_change",
        field="Вложение",
        old_value=None,
        new_value=f"Загружен файл: {file.filename} ({description or 'без описания'})",
        author=current_user.username,
    )

    return attachment


@router.get("/", response_model=List[AttachmentResponse])
def list_attachments(
    fault_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Получить список всех вложений для неисправности"""
    fault = db.query(Fault).filter(Fault.id == fault_id).first()
    if not fault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Неисправность не найдена"
        )

    attachments = (
        db.query(FaultAttachment)
        .filter(FaultAttachment.fault_id == fault_id)
        .order_by(FaultAttachment.created_at.desc())
        .all()
    )

    return attachments


@router.get("/{attachment_id}/download")
def download_attachment(
    fault_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Скачать файл вложения"""
    attachment = (
        db.query(FaultAttachment)
        .filter(
            FaultAttachment.id == attachment_id, FaultAttachment.fault_id == fault_id
        )
        .first()
    )

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вложение не найдено"
        )

    file_path = Path(attachment.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден на сервере"
        )

    return FileResponse(
        path=file_path,
        filename=attachment.filename,
        media_type=attachment.file_type or "application/octet-stream",
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    fault_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Удалить вложение"""
    attachment = (
        db.query(FaultAttachment)
        .filter(
            FaultAttachment.id == attachment_id, FaultAttachment.fault_id == fault_id
        )
        .first()
    )

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Вложение не найдено"
        )

    # Сохраняем имя файла для истории
    filename = attachment.filename

    # Удаляем файл
    file_path = Path(attachment.file_path)
    if file_path.exists():
        file_path.unlink()

    # Удаляем запись из БД
    db.delete(attachment)
    db.commit()

    # ✅ Записываем в историю
    log_history(
        db=db,
        fault_id=fault_id,
        event_type="field_change",
        field="Вложение",
        old_value=f"Удалён файл: {filename}",
        new_value=None,
        author=current_user.username,
    )

    return None
