#!/usr/bin/env python
"""
Скрипт для автоматического бэкапа базы данных
Запускается через cron или планировщик Windows
"""

import sys
import shutil
from datetime import datetime
from pathlib import Path

# Добавляем путь к проекту
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from app.services.backup_service import BackupService
from app.core.database import SessionLocal


def create_backup():
    """Создание бэкапа"""
    print(f"🔄 Запуск бэкапа в {datetime.now()}")
    
    backup_service = BackupService()
    db = SessionLocal()
    
    try:
        result = backup_service.create_backup(db)
        print(f"✅ Бэкап создан успешно!")
        print(f"   📁 Папка: backup_{result['timestamp']}")
        print(f"   📊 Записей: {result['total_records']}")
        print(f"   💾 Размер: {result['size'] / (1024 * 1024):.2f} MB")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания бэкапа: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    create_backup()