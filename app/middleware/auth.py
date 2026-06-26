from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
from app.core.security import decode_token
from app.core.database import SessionLocal
from app.models.all_models import User

async def auth_middleware(request: Request, call_next):
    """Проверка авторизации для защищённых страниц"""
    
    # Публичные маршруты
    public_paths = ['/login', '/register', '/static', '/docs', '/redoc', '/openapi.json', '/health']
    
    # Проверяем, является ли путь публичным
    if request.url.path in public_paths or request.url.path.startswith('/static'):
        return await call_next(request)
    
    # ✅ Если это API-запрос — пропускаем (авторизация через JWT в headers)
    if request.url.path.startswith('/api/'):
        return await call_next(request)
    
    # Проверяем токен в cookies
    token = request.cookies.get('access_token')
    
    if token:
        payload = decode_token(token)
        if payload:
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