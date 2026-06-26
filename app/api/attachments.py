import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all_models import Fault, FaultAttachment
from app.schemas.attachment import AttachmentResponse, AttachmentCreate
from app.schemas.user import UserResponse

router = APIRouter(prefix="/faults/{fault_id}/attachments", tags=["attachments"])

# Папка для хранения файлов
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    fault_id: int,
    file: UploadFile = File(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Загрузить файл к неисправности"""
    # Проверяем существование неисправности
    fault = db.query(Fault).filter(Fault.id == fault_id).first()
    if not fault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Неисправность не найдена"
        )

    # Проверяем размер файла (максимум 10MB)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Файл слишком большой. Максимальный размер 10MB"
        )

    # Создаём папку для неисправности
    fault_dir = UPLOAD_DIR / str(fault_id)
    fault_dir.mkdir(exist_ok=True)

    # Сохраняем файл
    safe_filename = f"{current_user.username}_{file.filename}"
    file_path = fault_dir / safe_filename
    
    # Проверяем, не существует ли файл
    counter = 1
    while file_path.exists():
        name, ext = os.path.splitext(safe_filename)
        file_path = fault_dir / f"{name}_{counter}{ext}"
        counter += 1

    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Создаём запись в БД
    attachment = FaultAttachment(
        fault_id=fault_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        file_type=file.content_type,
        description=description,
        uploaded_by=current_user.username
    )
    
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return attachment


@router.get("/", response_model=List[AttachmentResponse])
def list_attachments(
    fault_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Получить список всех вложений для неисправности"""
    fault = db.query(Fault).filter(Fault.id == fault_id).first()
    if not fault:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Неисправность не найдена"
        )

    attachments = db.query(FaultAttachment).filter(
        FaultAttachment.fault_id == fault_id
    ).order_by(FaultAttachment.created_at.desc()).all()
    
    return attachments


@router.get("/{attachment_id}/download")
def download_attachment(
    fault_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Скачать файл вложения"""
    attachment = db.query(FaultAttachment).filter(
        FaultAttachment.id == attachment_id,
        FaultAttachment.fault_id == fault_id
    ).first()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вложение не найдено"
        )

    file_path = Path(attachment.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден на сервере"
        )

    return FileResponse(
        path=file_path,
        filename=attachment.filename,
        media_type=attachment.file_type or "application/octet-stream"
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    fault_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Удалить вложение"""
    attachment = db.query(FaultAttachment).filter(
        FaultAttachment.id == attachment_id,
        FaultAttachment.fault_id == fault_id
    ).first()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вложение не найдено"
        )

    # Удаляем файл
    file_path = Path(attachment.file_path)
    if file_path.exists():
        file_path.unlink()

    # Удаляем запись из БД
    db.delete(attachment)
    db.commit()

    return None