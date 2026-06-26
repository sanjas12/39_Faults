from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from app.services.backup_service import BackupService
from app.core.database import SessionLocal

scheduler = BackgroundScheduler()
backup_service = BackupService()


def scheduled_backup():
    """Автоматический бэкап по расписанию"""
    print(f"🔄 Запуск автоматического бэкапа в {datetime.now()}")
    db = SessionLocal()
    try:
        result = backup_service.create_backup(db)
        print(f"✅ Бэкап создан: {result}")
    except Exception as e:
        print(f"❌ Ошибка бэкапа: {e}")
    finally:
        db.close()


def start_scheduler():
    """Запуск планировщика"""
    # Ежедневно в 3:00 ночи
    scheduler.add_job(
        scheduled_backup,
        trigger=CronTrigger(hour=3, minute=0),
        id="daily_backup",
        replace_existing=True
    )

    scheduler.start()
    print("🔄 Планировщик бэкапов запущен (ежедневно в 3:00)")

    import atexit
    atexit.register(lambda: scheduler.shutdown())