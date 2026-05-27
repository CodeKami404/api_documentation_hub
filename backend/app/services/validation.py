from openapi_spec_validator import validate_spec
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

def validate_openapi_spec(spec: dict) -> bool:
    """Валидация спецификации на соответствие OpenAPI 3.x"""
    if "openapi" not in spec:
        raise ValueError("Отсутствует обязательное поле 'openapi'")
    
    version = spec.get("openapi", "")
    if not version.startswith("3."):
        raise ValueError(f"Поддерживается только OpenAPI 3.x.x, получена: {version}")

    try:
        validate_spec(spec)
        return True
    except OpenAPIValidationError as e:
        raise ValueError(f"Ошибка валидации OpenAPI: {str(e)}")