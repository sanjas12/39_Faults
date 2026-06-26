import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ✅ Импортируем только после того, как путь настроен
from sqlalchemy.orm import Session

# ✅ Отложенный импорт для избежания циклических ссылок
def get_models():
    from app.models.all_models import (
        User, Project, Fault, FaultComment, 
        FaultHistory, KnowledgeBase
    )
    return User, Project, Fault, FaultComment, FaultHistory, KnowledgeBase


class BackupService:
    """Сервис для создания и управления бэкапами"""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, db: Session) -> Dict:
        """Создание полного бэкапа базы данных"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = self.backup_dir / f"backup_{timestamp}"
        backup_folder.mkdir(exist_ok=True)

        # Собираем данные из всех таблиц
        data = self._collect_all_data(db)

        # Сохраняем JSON с данными
        json_file = backup_folder / "data.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        # Копируем файл базы данных (если существует)
        db_file = Path("faults.db")
        if db_file.exists():
            shutil.copy2(db_file, backup_folder / "faults.db")

        # Создаём информацию о бэкапе
        info = {
            "timestamp": timestamp,
            "size": self._get_folder_size(backup_folder),
            "tables": {
                "users": len(data["users"]),
                "projects": len(data["projects"]),
                "faults": len(data["faults"]),
                "comments": len(data["comments"]),
                "history": len(data["history"]),
                "knowledge": len(data["knowledge"]),
            },
            "total_records": (
                len(data["users"]) + len(data["projects"]) + 
                len(data["faults"]) + len(data["comments"]) + 
                len(data["history"]) + len(data["knowledge"])
            )
        }

        # Сохраняем информацию о бэкапе
        with open(backup_folder / "info.json", "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        # Очищаем старые бэкапы (оставляем последние 10)
        self._cleanup_old_backups(keep=10)

        return info

    def _collect_all_data(self, db: Session) -> Dict:
        """Сбор всех данных из базы"""
        User, Project, Fault, FaultComment, FaultHistory, KnowledgeBase = get_models()
        
        return {
            "users": self._serialize_users(db, User),
            "projects": self._serialize_projects(db, Project),
            "faults": self._serialize_faults(db, Fault),
            "comments": self._serialize_comments(db, FaultComment),
            "history": self._serialize_history(db, FaultHistory),
            "knowledge": self._serialize_knowledge(db, KnowledgeBase),
        }

    def _serialize_users(self, db: Session, User) -> List[Dict]:
        """Сериализация пользователей"""
        users = db.query(User).all()
        return [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role.value if hasattr(u.role, 'value') else str(u.role),
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "updated_at": u.updated_at.isoformat() if u.updated_at else None,
            }
            for u in users
        ]

    def _serialize_projects(self, db: Session, Project) -> List[Dict]:
        """Сериализация проектов"""
        projects = db.query(Project).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "client": p.client,
                "station": p.station,
                "unit": p.unit,
                "type": p.type,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in projects
        ]

    def _serialize_faults(self, db: Session, Fault) -> List[Dict]:
        """Сериализация неисправностей"""
        faults = db.query(Fault).all()
        return [
            {
                "id": f.id,
                "title": f.title,
                "description": f.description,
                "severity": f.severity,
                "status": f.status,
                "project_id": f.project_id,
                "linked_knowledge_ids": f.linked_knowledge_ids,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "resolved_at": f.resolved_at.isoformat() if f.resolved_at else None,
            }
            for f in faults
        ]

    def _serialize_comments(self, db: Session, FaultComment) -> List[Dict]:
        """Сериализация комментариев"""
        comments = db.query(FaultComment).all()
        return [
            {
                "id": c.id,
                "fault_id": c.fault_id,
                "author": c.author,
                "content": c.content,
                "is_internal": bool(c.is_internal),
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in comments
        ]

    def _serialize_history(self, db: Session, FaultHistory) -> List[Dict]:
        """Сериализация истории"""
        history = db.query(FaultHistory).all()
        return [
            {
                "id": h.id,
                "fault_id": h.fault_id,
                "event_type": h.event_type,
                "field": h.field,
                "old_value": h.old_value,
                "new_value": h.new_value,
                "author": h.author,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in history
        ]

    def _serialize_knowledge(self, db: Session, KnowledgeBase) -> List[Dict]:
        """Сериализация базы знаний"""
        knowledge = db.query(KnowledgeBase).all()
        return [
            {
                "id": k.id,
                "title": k.title,
                "content": k.content,
                "category": k.category,
                "tags": k.tags,
                "related_faults": k.related_faults,
                "author": k.author,
                "is_published": bool(k.is_published),
                "views": k.views,
                "created_at": k.created_at.isoformat() if k.created_at else None,
                "updated_at": k.updated_at.isoformat() if k.updated_at else None,
            }
            for k in knowledge
        ]

    def _get_folder_size(self, folder: Path) -> int:
        """Расчёт размера папки в байтах"""
        total = 0
        for path in folder.rglob("*"):
            if path.is_file():
                total += path.stat().st_size
        return total

    def _cleanup_old_backups(self, keep: int = 10):
        """Удаление старых бэкапов, оставляя последние N"""
        backups = sorted(self.backup_dir.glob("backup_*"), key=lambda x: x.stat().st_mtime, reverse=True)
        for old_backup in backups[keep:]:
            shutil.rmtree(old_backup)

    def list_backups(self) -> List[Dict]:
        """Список всех бэкапов с информацией"""
        backups = []
        for folder in sorted(self.backup_dir.glob("backup_*"), key=lambda x: x.stat().st_mtime, reverse=True):
            info_file = folder / "info.json"
            if info_file.exists():
                with open(info_file, "r", encoding="utf-8") as f:
                    info = json.load(f)
                backups.append({
                    "name": folder.name,
                    "timestamp": info.get("timestamp"),
                    "size": info.get("size", 0),
                    "size_mb": round(info.get("size", 0) / (1024 * 1024), 2),
                    "tables": info.get("tables", {}),
                    "total_records": info.get("total_records", 0),
                    "created_at": datetime.fromtimestamp(folder.stat().st_mtime).isoformat()
                })
        return backups

    def get_backup_path(self, backup_name: str) -> Optional[Path]:
        """Получить путь к папке бэкапа"""
        backup_folder = self.backup_dir / backup_name
        if backup_folder.exists():
            return backup_folder
        return None

    def delete_backup(self, backup_name: str) -> bool:
        """Удалить бэкап"""
        backup_folder = self.backup_dir / backup_name
        if backup_folder.exists():
            shutil.rmtree(backup_folder)
            return True
        return False