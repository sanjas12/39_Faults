#!/usr/bin/env python
"""
Скрипт для автоматического бэкапа базы данных
Запускается через cron или планировщик Windows
"""

import sys
import os
from pathlib import Path

# Добавляем путь к проекту
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

# ✅ Добавляем путь к папке app
sys.path.insert(0, str(PROJECT_DIR / "app"))

# Устанавливаем переменную окружения для корректной работы
os.environ.setdefault("DATABASE_URL", "sqlite:///./faults.db")

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
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    from datetime import datetime
    create_backup()