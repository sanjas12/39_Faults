from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Faults"
    debug: bool = True

    # База данных
    database_url: str = "sqlite:///./faults.db"

    # JWT
    secret_key: str = "your-secret-key-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 часа

    # Email настройки
    smtp_host: str = "smtp.gmail.com"  # или ваш SMTP сервер
    smtp_port: int = 587
    smtp_user: str = "your-email@gmail.com"
    smtp_password: str = "your-app-password"
    smtp_from: str = "your-email@gmail.com"
    email_enabled: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
