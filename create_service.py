import os
import sys
import yaml

def create_microservice(service_name: str, port: int):
    if os.path.exists(service_name):
        print(f"Directory {service_name} already exists.")
        return

    # 1. Create directory
    os.makedirs(service_name)
    
    # 2. Write Dockerfile
    dockerfile_content = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install fastapi uvicorn httpx
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    with open(os.path.join(service_name, "Dockerfile"), "w", encoding="utf-8") as f:
        f.write(dockerfile_content)

    # 3. Write requirements.txt
    with open(os.path.join(service_name, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write("fastapi\nuvicorn\nhttpx\n")
        
    # 4. Write main.py
    main_py_content = f"""import os
import asyncio
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# URL хаба, куда будем отправлять документацию
HUB_URL = os.getenv("HUB_URL", "http://backend:8080/api/v1/specifications/")

app = FastAPI(
    title="{service_name.replace('-', ' ').title()} API", 
    version="1.0.0",
    servers=[{{"url": f"http://localhost:{port}", "description": "Local Server"}}] 
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
    
    service_credentials = {{
        "username": "{service_name}_account",
        "password": "secure_password",
        "role": "service"
    }}

    async with httpx.AsyncClient() as client:
        try:
            await client.post(AUTH_REGISTER_URL, json=service_credentials)
            login_data = {{
                "username": service_credentials["username"], 
                "password": service_credentials["password"]
            }}
            login_response = await client.post(AUTH_LOGIN_URL, data=login_data)
            
            if login_response.status_code != 200:
                print(f"--- Ошибка авторизации: {{login_response.text}} ---")
                return
                
            token = login_response.json().get("access_token")

            headers = {{
                "X-Service-Name": "{service_name}",
                "X-Service-Version": app.version,
                "Authorization": f"Bearer {{token}}"
            }}
            
            resp = await client.post(HUB_URL, json=spec, headers=headers)
            print(f"--- Документация {{service_name}} успешно зарегистрирована! ---")
            
        except Exception as e:
            print(f"--- Ошибка регистрации: {{e}} ---")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(register_with_hub())

@app.get("/api/items")
def get_items():
    \"\"\"Получить список элементов\"\"\"
    return [{{"id": 1, "name": "Item 1"}}]

@app.post("/api/items")
def create_item(item: Item):
    \"\"\"Создать новый элемент\"\"\"
    return {{"message": "Created", "item": item}}
"""
    with open(os.path.join(service_name, "main.py"), "w", encoding="utf-8") as f:
        f.write(main_py_content)
        
    # 5. Update docker-compose.yml
    docker_compose_path = "docker-compose.yml"
    with open(docker_compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)
        
    if service_name not in compose_data.get("services", {}):
        compose_data["services"][service_name] = {
            "build": f"./{service_name}",
            "ports": [f"{port}:8000"],
            "environment": {
                "HUB_URL": "http://backend:8080/api/v1/specifications/"
            },
            "depends_on": ["backend"]
        }
        
        with open(docker_compose_path, "w", encoding="utf-8") as f:
            yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
        print(f"Service {service_name} successfully generated and added to docker-compose.yml")
    else:
        print(f"Service {service_name} is already in docker-compose.yml")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_service.py <service_name> <port>")
        sys.exit(1)
        
    svc_name = sys.argv[1]
    svc_port = int(sys.argv[2])
    create_microservice(svc_name, svc_port)
