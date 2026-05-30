import os
import asyncio
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# URL хаба, куда будем отправлять документацию
HUB_URL = os.getenv("HUB_URL", "http://backend:8080/api/v1/specifications/")

app = FastAPI(
    title="Catalog Service API", 
    version="1.0.0",
    servers=[{"url": f"http://localhost:8003", "description": "Local Server"}] 
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    name: str
    description: str = None

async def register_with_hub():
    await asyncio.sleep(3) 
    spec = app.openapi()
    
    AUTH_REGISTER_URL = "http://backend:8080/api/v1/auth/register"
    AUTH_LOGIN_URL = "http://backend:8080/api/v1/auth/login"
    
    service_credentials = {
        "username": "catalog-service_account",
        "password": "secure_password",
        "role": "service"
    }

    async with httpx.AsyncClient() as client:
        try:
            await client.post(AUTH_REGISTER_URL, json=service_credentials)
            login_data = {
                "username": service_credentials["username"], 
                "password": service_credentials["password"]
            }
            login_response = await client.post(AUTH_LOGIN_URL, data=login_data)
            
            if login_response.status_code != 200:
                print(f"--- Ошибка авторизации: {login_response.text} ---")
                return
                
            token = login_response.json().get("access_token")

            headers = {
                "X-Service-Name": "catalog-service",
                "X-Service-Version": app.version,
                "Authorization": f"Bearer {token}"
            }
            
            resp = await client.post(HUB_URL, json=spec, headers=headers)
            print(f"--- Документация {service_name} успешно зарегистрирована! ---")
            
        except Exception as e:
            print(f"--- Ошибка регистрации: {e} ---")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(register_with_hub())

@app.get("/api/items")
def get_items():
    """Получить список элементов"""
    return [{"id": 1, "name": "Item 1"}]

@app.post("/api/items")
def create_item(item: Item):
    """Создать новый элемент"""
    return {"message": "Created", "item": item}
