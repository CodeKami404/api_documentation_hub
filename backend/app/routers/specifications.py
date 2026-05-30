from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from app.database import get_db
from app.security import RoleChecker
from app.models import Api, SpecificationVersion, User, UserRole
from app.schemas import ApiResponse
from app.services.validation import validate_openapi_spec
import httpx

router = APIRouter(prefix="/api/v1/specifications", tags=["Specifications"])

allow_registration = RoleChecker([UserRole.admin, UserRole.service])

@router.post("/", status_code=201)
async def register_specification(
    spec: dict,
    x_service_name: str = Header(...),
    x_service_version: str = Header(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_registration)
):
    # 1. Валидация
    try:
        validate_openapi_spec(spec)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 2. Поиск или создание API
    result = await db.execute(select(Api).filter(Api.name == x_service_name))
    api = result.scalars().first()
    
    if not api:
        api = Api(name=x_service_name, description=spec.get("info", {}).get("description", ""))
        db.add(api)
        await db.commit()
        await db.refresh(api)

    # 3. Деактивация старой записи с ТАКОЙ ЖЕ версией (если есть)
    await db.execute(
        update(SpecificationVersion)
        .where(SpecificationVersion.api_id == api.id, SpecificationVersion.version == x_service_version)
        .values(is_active=False)
    )

    # 4. Сохранение новой версии
    new_spec = SpecificationVersion(
        api_id=api.id,
        version=x_service_version,
        specification=spec,
        is_active=True
    )
    db.add(new_spec)
    await db.commit()
    
    return {"message": "Specification registered successfully", "id": str(new_spec.id)}


@router.get("/{service_name}/latest")
async def get_latest_spec(service_name: str, db: AsyncSession = Depends(get_db)):
    """Возвращает саму JSON-спецификацию для Swagger UI / ReDoc (последнюю добавленную)"""
    result = await db.execute(
        select(SpecificationVersion)
        .join(Api)
        .filter(Api.name == service_name, SpecificationVersion.is_active == True)
        .order_by(SpecificationVersion.registered_at.desc())
    )
    spec = result.scalars().first()
    if not spec:
        raise HTTPException(status_code=404, detail="Specification not found")
    return spec.specification


@router.get("/{service_name}/version/{version}")
async def get_spec_by_version(service_name: str, version: str, db: AsyncSession = Depends(get_db)):
    """Возвращает JSON-спецификацию конкретной версии"""
    result = await db.execute(
        select(SpecificationVersion)
        .join(Api)
        .filter(Api.name == service_name, SpecificationVersion.version == version, SpecificationVersion.is_active == True)
        .order_by(SpecificationVersion.registered_at.desc())
    )
    spec = result.scalars().first()
    if not spec:
        raise HTTPException(status_code=404, detail="Specification version not found")
    return spec.specification


@router.get("/services")
async def get_active_services(db: AsyncSession = Depends(get_db)):
    """Возвращает список всех зарегистрированных сервисов и их версий для отрисовки карточек"""
    result = await db.execute(
        select(Api, SpecificationVersion)
        .join(SpecificationVersion, Api.id == SpecificationVersion.api_id)
        .filter(SpecificationVersion.is_active == True)
        .order_by(SpecificationVersion.registered_at.desc())
    )
    
    services_dict = {}
    for api, spec in result.all():
        if api.name not in services_dict:
            description = api.description or spec.specification.get("info", {}).get("description", "Описание отсутствует")
            services_dict[api.name] = {
                "name": api.name,
                "versions": [],
                "description": description,
                "latest_version": spec.version
            }
        if spec.version not in services_dict[api.name]["versions"]:
            services_dict[api.name]["versions"].append(spec.version)
            
    return list(services_dict.values())


@router.get("/{service_name}/health")
async def check_service_health(service_name: str):
    """
    Пингует микросервис по его внутреннему имени в Docker (например, demo-service:8000), 
    чтобы фронтенд мог нарисовать зеленый/красный бейдж статуса.
    """
    try:
        # Устанавливаем короткий таймаут, чтобы дашборд не зависал, если сервис мертв
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get(f"http://{service_name}:8000/docs")
            if resp.status_code == 200:
                return {"status": "online"}
            return {"status": "error"}
    except Exception:
        return {"status": "offline"}