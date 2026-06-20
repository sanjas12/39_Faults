const API = {
    // Вспомогательный метод для получения заголовков
    getHeaders() {
        const token = localStorage.getItem('auth_token');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    },

    // Основной метод запросов
    async request(method, url, data = null) {
        try {
            const response = await axios({
                method: method,
                url: url,
                data: data,
                headers: this.getHeaders() // Автоматическая подстановка токена
            });
            return response.data;
        } catch (error) {
            // Если сервер возвращает 401, сессия невалидна
            if (error.response?.status === 401) {
                console.warn('Сессия истекла или токен невалиден');
                if (typeof logout === 'function') {
                    logout(); // Вызываем функцию выхода из app.js
                }
            }
            console.error(`API Error [${method.toUpperCase()} ${url}]:`, error);
            throw error;
        }
    },

    // Методы для работы с неисправностями
    getFaults: () => API.request('get', '/api/faults'),
    getFault: (id) => API.request('get', `/api/faults/${id}`),
    createFault: (data) => API.request('post', '/api/faults', data),
    updateFault: (id, data) => API.request('patch', `/api/faults/${id}`, data),
    deleteFault: (id) => API.request('delete', `/api/faults/${id}`),

    // Методы для работы с проектами
    getProjects: () => API.request('get', '/api/projects'),

    // Методы для комментариев
    getComments: (faultId) => API.request('get', `/api/faults/${faultId}/comments`),
    addComment: (faultId, content, isInternal) =>
        API.request('post', `/api/faults/${faultId}/comments`, {
            content,
            is_internal: isInternal,
            author: 'Пользователь'
        })
};
