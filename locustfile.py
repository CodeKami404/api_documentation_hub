import random
from locust import HttpUser, task, between

class ApiHubUser(HttpUser):
    # Имитация реального поведения: пауза между действиями пользователя от 1 до 3 секунд
    wait_time = between(1, 3)
    
    def on_start(self):
        """
        Метод выполняется при старте каждого виртуального пользователя (VUser).
        Здесь мы имитируем аутентификацию микросервиса, чтобы получить JWT-токен
        для последующей публикации контрактов (POST запросов).
        """
        self.service_name = f"load-test-service-{random.randint(10000, 99999)}"
        self.token = None
        self.known_services = ["demo-service"] # Начальный кэш сервисов для просмотра
        
        # 1. Регистрация временного сервисного аккаунта для этого VUser
        creds = {
            "username": f"user_{self.service_name}", 
            "password": "load_test_password", 
            "role": "service"
        }
        self.client.post("/api/v1/auth/register", json=creds)
        
        # 2. Логин и получение токена
        resp = self.client.post(
            "/api/v1/auth/login", 
            data={"username": creds["username"], "password": creds["password"]}
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    @task(6)
    def read_dashboard(self):
        """
        Вес 6 (60%): Чтение дашборда со списком сервисов.
        Основной паттерн потребления для разработчиков и менеджеров.
        """
        with self.client.get("/api/v1/specifications/services", catch_response=True, name="GET /services") as response:
            if response.status_code == 200:
                services = response.json()
                if services:
                    # Обновляем кэш известных сервисов, чтобы 30%-ный таск брал реальные ID
                    self.known_services = [s["name"] for s in services]
            else:
                response.failure(f"Failed to load dashboard: {response.status_code}")

    @task(3)
    def view_spec_detail(self):
        """
        Вес 3 (30%): Просмотр детальной спецификации конкретного сервиса.
        Пользователь кликнул на карточку и изучает OpenAPI.
        """
        if self.known_services:
            target_service = random.choice(self.known_services)
            # В нашей архитектуре детализация - это получение latest версии
            self.client.get(f"/api/v1/specifications/{target_service}/latest", name="GET /service/latest")

    @task(1)
    def register_new_contract(self):
        """
        Вес 1 (10%): Фоновая регистрация нового контракта (CI/CD пайплайны).
        Самая "тяжелая" операция (сохранение в БД + парсинг AST).
        """
        if not self.token:
            return # Если нет токена, пропускаем таск
            
        version = f"1.0.{random.randint(1, 1000)}"
        
        headers = {
            "X-Service-Name": self.service_name,
            "X-Service-Version": version,
            "Authorization": f"Bearer {self.token}"
        }
        
        # Генерация моковой, но валидной OpenAPI 3.0.3 спецификации
        spec_payload = {
            "openapi": "3.0.3",
            "info": {
                "title": f"{self.service_name} API",
                "version": version,
                "description": "Автоматически сгенерированная спецификация нагрузочного теста."
            },
            "paths": {
                "/ping": {
                    "get": {
                        "summary": "Проверка доступности",
                        "responses": {
                            "200": {"description": "Успешный ответ"}
                        }
                    }
                }
            }
        }
        
        self.client.post("/api/v1/specifications/", json=spec_payload, headers=headers, name="POST /specifications")