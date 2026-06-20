// Хранение токена
let authToken = localStorage.getItem('auth_token');
let currentUser = JSON.parse(localStorage.getItem('current_user') || 'null');

// Установка токена в заголовки
if (authToken) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
}

// Функция логина
async function login(username, password) {
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await axios.post('/api/auth/login', formData);
        const data = response.data;

        authToken = data.access_token;
        currentUser = data.user;

        localStorage.setItem('auth_token', authToken);
        localStorage.setItem('current_user', JSON.stringify(currentUser));

        axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;

        updateUserUI();
        return { success: true, user: currentUser };
    } catch (error) {
        console.error('Ошибка входа:', error);
        return { success: false, error: error.response?.data?.detail || 'Ошибка входа' };
    }
}

// Функция выхода
function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('current_user');
    delete axios.defaults.headers.common['Authorization'];
    authToken = null;
    currentUser = null;
    updateUserUI();
    window.location.href = '/login';
}

// Обновление UI пользователя
function updateUserUI() {
    const userInfo = document.getElementById('userInfo');
    if (currentUser) {
        userInfo.innerHTML = `
            <strong>${currentUser.full_name || currentUser.username}</strong>
            <br><small class="text-muted">${currentUser.role}</small>
        `;
    } else {
        userInfo.innerHTML = `<small>Гость</small>`;
    }
}

// Проверка роли
function hasRole(roles) {
    if (!currentUser) return false;
    return roles.includes(currentUser.role);
}

// Инициализация UI
document.addEventListener('DOMContentLoaded', function() {
    updateUserUI();

    // Кнопка выхода
    document.getElementById('logoutBtn')?.addEventListener('click', function(e) {
        e.preventDefault();
        logout();
    });
});
