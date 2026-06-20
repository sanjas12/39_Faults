from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from app.core.security import decode_token
from app.core.database import SessionLocal
from app.models.all_models import User

async def auth_middleware(request: Request, call_next):
    """Проверка авторизации для защищённых страниц"""
    
    # Публичные маршруты (не требуют авторизации)
    public_paths = ['/login', '/static', '/docs', '/redoc', '/openapi.json', '/health']
    
    if request.url.path in public_paths or request.url.path.startswith('/static'):
        return await call_next(request)
    
    # Проверяем токен
    token = request.cookies.get('access_token') or request.headers.get('Authorization')
    
    if token:
        # Убираем "Bearer " если есть
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = decode_token(token)
        if payload:
            # Проверяем пользователя в БД
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.username == payload.get('sub')).first()
                if user and user.is_active:
                    request.state.user = user
                    return await call_next(request)
            finally:
                db.close()
    
    # Если не авторизован — редирект на логин
    return RedirectResponse(url='/login')