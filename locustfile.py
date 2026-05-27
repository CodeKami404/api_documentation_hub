from locust import HttpUser, task, between

class APIHubUser(HttpUser):
    # Пауза между действиями пользователя (от 1 до 3 секунд)
    wait_time = between(1, 3)

    @task(4)
    def view_dashboard(self):
        # Имитация открытия дашборда (частая операция)
        self.client.get("/api/v1/specifications/services", name="GET /services")

    @task(3)
    def view_specification(self):
        # Имитация открытия документации демо-сервиса
        self.client.get("/api/v1/specifications/demo-service/latest", name="GET /latest_spec")

    @task(1)
    def register_new_spec(self):
        # Имитация регистрации спецификации (редкая, но тяжелая операция)
        headers = {
            "X-Service-Name": "load-test-service",
            "X-Service-Version": "1.0.0",
            "Content-Type": "application/json"
        }
        payload = {
            "openapi": "3.0.3",
            "info": {"title": "Load Test API", "version": "1.0.0"},
            "paths": {}
        }
        self.client.post("/api/v1/specifications/", json=payload, headers=headers, name="POST /specifications")


