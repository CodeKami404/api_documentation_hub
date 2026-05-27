import requests

# URL твоего запущенного Хаба
HUB_URL = "http://localhost:8080/api/v1/specifications/"

# Данные двух новых сервисов с валидными OpenAPI спецификациями
mock_services = [
    {
        "name": "kedr-analytics",
        "version": "1.0.0",
        "spec": {
            "openapi": "3.0.3",
            "info": {
                "title": "Kedr Analytics Core API",
                "version": "1.0.0",
                "description": "Аналитическое ядро для предиктивного моделирования, прогнозирования рисков и анализа ключевых бизнес-показателей."
            },
            "paths": {
                "/api/v1/analytics/predict": {
                    "post": {
                        "summary": "Расчет прогнозной модели",
                        "responses": {
                            "200": {"description": "Успешный расчет прогнозных значений"}
                        }
                    }
                }
            }
        }
    },
    {
        "name": "pilyulyus-rag",
        "version": "0.5.0",
        "spec": {
            "openapi": "3.0.3",
            "info": {
                "title": "Pilyulyus Medical RAG API",
                "version": "0.5.0",
                "description": "Мультиагентная система генерации медицинских синопсисов на основе истории болезни и клинических протоколов методом RAG."
            },
            "paths": {
                "/api/v1/rag/synopsis": {
                    "post": {
                        "summary": "Генерация медицинского синопсиса",
                        "responses": {
                            "200": {"description": "Синопсис успешно сгенерирован и нормализован"}
                        }
                    }
                }
            }
        }
    }
]

print("Запуск регистрации дополнительных сервисов...")

for service in mock_services:
    headers = {
        "X-Service-Name": service["name"],
        "X-Service-Version": service["version"],
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(HUB_URL, json=service["spec"], headers=headers)
        if response.status_code == 201:
            print(f"✅ Сервис успешно добавлен: {service['name']} (v{service['version']})")
        else:
            print(f"❌ Ошибка при добавлении {service['name']}: {response.status_code} — {response.text}")
    except Exception as e:
        print(f"💥 Не удалось связаться с Хабом: {e}")