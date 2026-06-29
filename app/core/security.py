from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.all_models import User
from app.schemas.user import UserRole

# Настройки JWT
SECRET_KEY = "your-secret-key-change-me-in-production"  # В продакшене использовать переменную окружения
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Декодирование JWT токена"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Получение текущего пользователя по токену"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # ✅ Сначала пробуем получить токен из header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
    # ✅ Если нет в header, пробуем из cookie
    elif not token:
        token = request.cookies.get("access_token")
    
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь заблокирован"
        )

    return user


def check_role(user: User, required_roles: List[str]) -> bool:
    """Проверка роли пользователя"""
    return user.role in required_roles


# Декораторы для проверки ролей
def require_admin(user: User = Depends(get_current_user)):
    """Только для администраторов"""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора",
        )
    return user


def require_engineer(user: User = Depends(get_current_user)):
    """Для инженеров и администраторов"""
    if user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Требуются права инженера"
        )
    return user


def require_operator(user: User = Depends(get_current_user)):
    """Для всех авторизованных пользователей"""
    return user
