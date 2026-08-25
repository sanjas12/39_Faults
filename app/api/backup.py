import io
import zipfile

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.schemas.user import UserResponse
from app.services.backup_service import BackupService

router = APIRouter(prefix="/backup", tags=["backup"])
backup_service = BackupService()


@router.post("/create")
def create_backup(
    db: Session = Depends(get_db), current_user: UserResponse = Depends(require_admin)
):
    """Создание бэкапа (только админ)"""
    try:
        result = backup_service.create_backup(db)
        return {
            "status": "success",
            "message": "Бэкап успешно создан",
            "backup": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания бэкапа: {str(e)}",
        ) from e


@router.get("/list")
def list_backups(current_user: UserResponse = Depends(require_admin)):
    """Список всех бэкапов (только админ)"""
    try:
        backups = backup_service.list_backups()
        return {"status": "success", "count": len(backups), "backups": backups}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения списка бэкапов: {str(e)}",
        ) from e


@router.get("/download/{backup_name}")
def download_backup(
    backup_name: str, current_user: UserResponse = Depends(require_admin)
):
    """Скачать бэкап в виде ZIP-архива (только админ)"""
    backup_path = backup_service.get_backup_path(backup_name)

    if not backup_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Бэкап не найден"
        )

    # Создаём ZIP-архив
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in backup_path.rglob("*"):
            zip_file.write(file, file.relative_to(backup_path))

    zip_buffer.seek(0)

    return FileResponse(
        path=zip_buffer, media_type="application/zip", filename=f"{backup_name}.zip"
    )


@router.delete("/{backup_name}")
def delete_backup(
    backup_name: str, current_user: UserResponse = Depends(require_admin)
):
    """Удалить бэкап (только админ)"""
    success = backup_service.delete_backup(backup_name)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Бэкап не найден"
        )

    return {"status": "success", "message": f"Бэкап {backup_name} удалён"}
