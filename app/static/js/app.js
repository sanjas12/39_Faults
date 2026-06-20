// Глобальные переменные
let currentUser = null;

// Функция для обновления UI пользователя
// app/static/js/app.js

// Функция для обновления UI пользователя
function updateUserUI() {
    const userInfo = document.getElementById('userInfo');
    const logoutBtn = document.getElementById('logoutBtn');
    const loginLink = document.getElementById('loginLink');
    
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
    } else {
        // Гость
        userInfo.innerHTML = `<small>Гость</small>`;
        if (logoutBtn) {
            logoutBtn.style.display = 'none';
        }
        if (loginLink) {
            loginLink.style.display = 'block';
        }
    }
}

// Функция выхода (глобальная, доступна из onclick)
function logout() {
    console.log('🚪 logout вызван');
    
    // Очищаем localStorage
    localStorage.removeItem('auth_token');
    localStorage.removeItem('current_user');
    
    // Удаляем токен из заголовков axios
    delete axios.defaults.headers.common['Authorization'];
    
    // Сбрасываем пользователя
    currentUser = null;
    
    // Обновляем UI
    updateUserUI();
    
    // Редирект на страницу логина
    window.location.href = '/login';
}

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

        axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;

        updateUserUI();
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
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM загружен');
    
    const token = localStorage.getItem('auth_token');
    const userData = localStorage.getItem('current_user');
    
    if (token && userData && userData !== 'undefined' && userData !== 'null') {
        try {
            currentUser = JSON.parse(userData);
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            console.log('✅ Пользователь восстановлен:', currentUser.username);
        } catch (e) {
            console.error('❌ Ошибка восстановления:', e);
            localStorage.removeItem('auth_token');
            localStorage.removeItem('current_user');
            currentUser = null;
        }
    }
    
    updateUserUI();
    
    // ✅ Дублируем обработчик для кнопки выхода (на случай если onclick не сработает)
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


axios.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401) {
            console.warn('🔒 Неавторизован, редирект на логин');
            localStorage.removeItem('auth_token');
            localStorage.removeItem('current_user');
            currentUser = null;
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);