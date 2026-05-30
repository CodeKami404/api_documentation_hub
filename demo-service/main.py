import os
import asyncio
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# URL хаба, куда будем отправлять документацию
HUB_URL = os.getenv("HUB_URL", "http://backend:8080/api/v1/specifications/")

app = FastAPI(
    title="Demo Startup API", 
    version="2.0.0",
    servers=[{"url": "http://localhost:8000", "description": "Local Demo Server"}] 
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Разрешаем запросы откуда угодно (для диплома отлично)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

projects_db = [
    {"id": 1, "name": "Cedar", "type": "Business Analytics"},
    {"id": 2, "name": "Pilyulyus", "type": "Medical RAG"}
]

class ProjectCreate(BaseModel):
    name: str
    type: str

async def register_with_hub():
    # Ждем пару секунд, чтобы бэкенд хаба точно успел подняться первым
    await asyncio.sleep(3) 
    spec = app.openapi()
    
    # URL для авторизации (используем внутреннее имя контейнера backend)
    AUTH_REGISTER_URL = "http://backend:8080/api/v1/auth/register"
    AUTH_LOGIN_URL = "http://backend:8080/api/v1/auth/login"
    
    # Учетные данные нашего микросервиса
    service_credentials = {
        "username": "demo_service_account",
        "password": "secure_service_password_123",
        "role": "service" # Выдаем роль service
    }

    async with httpx.AsyncClient() as client:
        try:
            # 1. Пытаемся зарегистрировать сервисный аккаунт
            # Если он уже есть, бэкенд вернет 400 (Пользователь уже существует) - это нормально, просто идем дальше
            await client.post(AUTH_REGISTER_URL, json=service_credentials)

            # 2. Логинимся для получения JWT токена
            # Внимание: эндпоинт OAuth2 требует отправки данных как Form Data (data=...), а не JSON
            login_data = {
                "username": service_credentials["username"], 
                "password": service_credentials["password"]
            }
            login_response = await client.post(AUTH_LOGIN_URL, data=login_data)
            
            if login_response.status_code != 200:
                print(f"--- Ошибка авторизации демо-сервиса: {login_response.text} ---")
                return
                
            # Достаем токен из ответа
            token = login_response.json().get("access_token")

            # 3. Отправляем спецификацию, прикрепив токен к заголовкам
            headers = {
                "X-Service-Name": "demo-service",
                "X-Service-Version": app.version,
                "Authorization": f"Bearer {token}" # <--- ВОТ НАШ ПРОПУСК!
            }
            
            resp = await client.post(HUB_URL, json=spec, headers=headers)
            print(f"--- Документация успешно зарегистрирована! Статус: {resp.status_code} ---")
            
        except Exception as e:
            print(f"--- Ошибка при регистрации документации: {e} ---")

# Эта функция сработает автоматически при запуске микросервиса
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(register_with_hub())

# Пара тестовых эндпоинтов для документации
@app.get("/api/projects")
def get_startup_projects():
    """Возвращает список проектов (пример из твоего диплома)"""
    return projects_db

@app.get("/api/projects/{project_id}")
def get_project_by_id(project_id: int):
    """Возвращает проект по его ID"""
    return {"id": project_id, "name": "Test Project", "status": "active"}

@app.post("/api/projects")
async def create_project(project: ProjectCreate):
    new_id = len(projects_db) + 1
    new_project = {"id": new_id, "name": project.name, "type": project.type}
    projects_db.append(new_project)
    print(f"--- Получен POST запрос через прокси: {new_project} ---")
    return {"message": "Project created!", "project": new_project}

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: int):
    """(НОВОЕ В v2.0.0) Удаление проекта по ID"""
    global projects_db
    projects_db = [p for p in projects_db if p.get("id") != project_id]
    return {"message": f"Project {project_id} deleted successfully"}