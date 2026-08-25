// Глобальные переменные
let currentUser = null;

// Функция для обновления UI пользователя
// app/static/js/app.js

// Функция для обновления UI пользователя
function updateUserUI() {
    const userInfo = document.getElementById('userInfo');
    const logoutBtn = document.getElementById('logoutBtn');
    const loginLink = document.getElementById('loginLink');
    const settingsNav = document.getElementById('settingsNavItem');
    const adminNav = document.getElementById('adminNavItem');

    console.log('🔄 updateUserUI вызван');
    console.log('🔍 currentUser:', currentUser);

    if (!userInfo) return;

    if (currentUser) {
        // Пользователь авторизован
        userInfo.innerHTML = `
            <strong style="font-size: 0.9rem; display: block; overflow: hidden; text-overflow: ellipsis;">${currentUser.full_name || currentUser.username}</strong>
            <small class="text-muted" style="font-size: 0.7rem; display: block;">${currentUser.role}</small>
        `;

        if (logoutBtn) {
            logoutBtn.style.display = 'block';
            console.log('✅ Кнопка выхода показана');
        }
        if (loginLink) {
            loginLink.style.display = 'none';
        }

        // ✅ Показываем пункт "Настройки"
        if (settingsNav) {
            settingsNav.style.display = 'block';
        }

        // ✅ Показываем пункт "Админ-панель" только для администраторов
        if (adminNav) {
            if (currentUser.role === 'admin') {
                adminNav.style.display = 'block';
                console.log('✅ Админ-панель показана (admin)');
            } else {
                adminNav.style.display = 'none';
                console.log('🔒 Админ-панель скрыта (роль: ' + currentUser.role + ')');
            }
        }
    } else {
        // Гость
        userInfo.innerHTML = `<small>Гость</small>`;
        if (logoutBtn) {
            logoutBtn.style.display = 'none';
        }
        if (loginLink) {
            loginLink.style.display = 'block';
        }

        if (settingsNav) {
            settingsNav.style.display = 'none';
        }
        if (adminNav) {
            adminNav.style.display = 'none';
        }
    }
}

// Функция выхода (глобальная, доступна из onclick)
async function logout() {
    console.log('🚪 logout вызван');

    try {
        // Cookie авторизации создаётся сервером, поэтому и удаляем её сервером.
        await axios.post('/api/auth/logout');
    } catch (error) {
        console.error('Ошибка серверного выхода:', error);
    }

    // Очищаем localStorage
    localStorage.removeItem('auth_token');
    localStorage.removeItem('current_user');

    // Удаляем токен из заголовков axios
    delete axios.defaults.headers.common['Authorization'];

    // ✅ Удаляем cookie
    document.cookie = 'access_token=; path=/; max-age=0; samesite=lax';

    currentUser = null;

    // Обновляем UI
    updateUserUI();

    // Редирект на страницу логина
    window.location.href = '/login';
}

// Функция входа
// Функция входа
async function login(username, password) {
    console.log('🔑 login вызван');

    try {
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);

        const response = await axios.post('/api/auth/login', params, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        });

        const data = response.data;

        // Сохраняем данные
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('current_user', JSON.stringify(data.user));
        currentUser = data.user;

        // ✅ Устанавливаем токен в заголовки axios
        axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;

        // ✅ Устанавливаем cookie для middleware
        document.cookie = `access_token=${data.access_token}; path=/; max-age=86400; samesite=lax`;

        // ✅ ПРИНУДИТЕЛЬНО обновляем UI
        updateUserUI();

        // ✅ ДОПОЛНИТЕЛЬНО: если admin, показываем админ-панель
        const adminNav = document.getElementById('adminNavItem');
        if (adminNav && currentUser && currentUser.role === 'admin') {
            adminNav.style.display = 'block';
            console.log('✅ Админ-панель принудительно показана после входа');
        }

        // ✅ Обновляем настройки
        const settingsNav = document.getElementById('settingsNavItem');
        if (settingsNav) {
            settingsNav.style.display = 'block';
        }

        return { success: true, user: currentUser };
    } catch (error) {
        console.error('❌ Ошибка входа:', error);
        return {
            success: false,
            error: error.response?.data?.detail || 'Ошибка входа'
        };
    }
}

// Проверка роли
function hasRole(roles) {
    if (!currentUser) return false;
    return roles.includes(currentUser.role);
}

// Интерсептор для 401 ошибок
axios.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401) {
            console.warn('🔒 Неавторизован, редирект на логин');
            localStorage.removeItem('auth_token');
            localStorage.removeItem('current_user');
            currentUser = null;
            if (!['/login', '/register'].includes(window.location.pathname)) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

async function restoreAuthentication() {
    const cookieToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('access_token='))
        ?.split('=')
        .slice(1)
        .join('=');
    let token = cookieToken || localStorage.getItem('auth_token');
    const userData = localStorage.getItem('current_user');

    // Серверная авторизация использует cookie, старые скрипты страниц — localStorage.
    // Синхронизируем их до DOMContentLoaded, чтобы страницы не запускали ложный редирект.
    if (cookieToken) {
        localStorage.setItem('auth_token', cookieToken);
        axios.defaults.headers.common['Authorization'] = `Bearer ${cookieToken}`;
    } else if (!['/login', '/register'].includes(window.location.pathname)) {
        // Защищённая HTML-страница уже подтверждена сервером по cookie. Если
        // JavaScript её не видит (например, HttpOnly), не отправляем поверх
        // действующей cookie старый Bearer-токен из localStorage.
        localStorage.removeItem('auth_token');
        delete axios.defaults.headers.common['Authorization'];
        token = null;
    }

    if (token && userData && userData !== 'undefined' && userData !== 'null') {
        try {
            currentUser = JSON.parse(userData);
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            document.cookie = `access_token=${token}; path=/; max-age=86400; samesite=lax`;
            return currentUser;
        } catch (e) {
            console.error('❌ Ошибка восстановления:', e);
            localStorage.removeItem('auth_token');
            localStorage.removeItem('current_user');
            delete axios.defaults.headers.common['Authorization'];
        }
    }

    if (['/login', '/register'].includes(window.location.pathname)) {
        return null;
    }

    try {
        const response = await axios.get('/api/auth/me');
        currentUser = response.data;
        localStorage.setItem('current_user', JSON.stringify(currentUser));
        return currentUser;
    } catch (error) {
        currentUser = null;
        throw error;
    }
}

// Единая точка готовности авторизации для скриптов отдельных страниц.
window.authReady = restoreAuthentication();

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 DOM загружен');

    try {
        await window.authReady;
    } catch (_) {
        return;
    }

    // ✅ Обновляем UI
    updateUserUI();

    // ✅ Дополнительная проверка для админ-панели (на случай если updateUserUI не сработал)
    const adminNav = document.getElementById('adminNavItem');
    if (adminNav && currentUser && currentUser.role === 'admin') {
        adminNav.style.display = 'block';
        console.log('✅ Админ-панель показана при загрузке (доп. проверка)');
    }

    // Кнопка выхода
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    }
});


// Функция регистрации
async function register(username, email, password, fullName) {
    console.log('register вызван с username:', username);

    try {
        const response = await axios.post('/api/auth/register', {
            username: username,
            email: email,
            password: password,
            full_name: fullName || null,
            role: 'operator'  // По умолчанию оператор
        });

        console.log('Ответ от сервера (регистрация):', response.data);

        const data = response.data;

        // ✅ Автоматически входим после регистрации
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('current_user', JSON.stringify(data.user));
        currentUser = data.user;

        axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;

        updateUserUI();
        return { success: true, user: currentUser };
    } catch (error) {
        console.error('Ошибка регистрации:', error.response?.data || error);
        return {
            success: false,
            error: error.response?.data?.detail || 'Ошибка регистрации'
        };
    }
}

function isAdmin() {
    return currentUser && currentUser.role === 'admin';
}
