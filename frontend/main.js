// Пример обновления функции загрузки данных
async function loadServices() {
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch('http://localhost:8080/api/v1/specifications/services', {
            method: 'GET',
            headers: {
                // Добавляем токен в каждый запрос
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.status === 401) {
            // Если бэкенд ответил, что токен просрочен или невалиден — сбрасываем его и шлем на логин
            localStorage.removeItem('access_token');
            window.location.href = '/login.html';
            return;
        }
        
        const services = await response.json();
        // ... логика отрисовки карточек дашборда ...
    } catch (err) {
        console.error('Ошибка загрузки:', err);
    }
}

document.getElementById('logoutBtn').addEventListener('click', () => {
    // Стираем токен из памяти браузера
    localStorage.removeItem('access_token');
    // Отправляем на авторизацию
    window.location.href = '/login.html';
});s