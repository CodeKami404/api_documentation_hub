from openapi_spec_validator import validate_spec
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

class OpenAPI_AST_Linter:
    def __init__(self, spec: dict):
        self.spec = spec
        self.history = set()

    def resolve_ref(self, ref_path: str) -> dict:
        """Рекурсивный резолвинг локальных ссылок $ref"""
        if ref_path in self.history:
            raise ValueError(f"Обнаружена циклическая ссылка: {ref_path}")
        self.history.add(ref_path)

        # По политике безопасности мы не обрабатываем внешние ссылки, чтобы избежать SSRF и RFI векторов
        if not ref_path.startswith("#/"):
            raise ValueError(f"Внешние ссылки запрещены политикой безопасности Хаба: {ref_path}")

        parts = ref_path.split("/")[1:]
        current_node = self.spec
        
        for part in parts:
            # Обработка экранирования спецсимволов JSON Pointer (согласно стандарту RFC 6901)
            part = part.replace("~1", "/").replace("~0", "~")
            if isinstance(current_node, dict) and part in current_node:
                current_node = current_node[part]
            else:
                raise ValueError(f"Невозможно разрешить ссылку внутри документа: {ref_path}")
        
        # Если найденный узел сам является ссылкой, продолжаем рекурсивный спуск
        if isinstance(current_node, dict) and "$ref" in current_node:
            return self.resolve_ref(current_node["$ref"])
            
        self.history.remove(ref_path)
        return current_node

    def lint_node(self, node, path: str):
        """Глубокий рекурсивный обход AST (Abstract Syntax Tree) документа"""
        if isinstance(node, dict):
            # Если узел содержит ссылку, мы валидируем саму ссылку, резолвим её
            # и прогоняем через линтер тот кусок AST, на который она указывает.
            if "$ref" in node:
                resolved_node = self.resolve_ref(node["$ref"])
                self.lint_node(resolved_node, f"{path}->{node['$ref']}")
                return

            # Семантические AST-проверки, дополняющие стандартный валидатор
            if path.endswith("/responses") and not node:
                raise ValueError(f"Семантическая ошибка: блок ответов пуст по пути {path}")
                
            for key, value in node.items():
                self.lint_node(value, f"{path}/{key}")

        elif isinstance(node, list):
            for index, item in enumerate(node):
                self.lint_node(item, f"{path}[{index}]")


def validate_openapi_spec(spec: dict) -> bool:
    """Валидация спецификации на соответствие OpenAPI 3.x с глубоким AST-линтингом"""
    if not isinstance(spec, dict):
        raise ValueError("Спецификация должна быть JSON-объектом (словарем)")

    if "openapi" not in spec:
        raise ValueError("Отсутствует обязательное корневое поле 'openapi'")
    
    version = spec.get("openapi", "")
    if not version.startswith("3."):
        raise ValueError(f"Поддерживается только OpenAPI 3.x.x, получена версия: {version}")

    # 1. Синтаксическая валидация через стандартную библиотеку (JSON Schema validation)
    try:
        validate_spec(spec)
    except OpenAPIValidationError as e:
        raise ValueError(f"Ошибка синтаксической валидации OpenAPI: {str(e)}")

    # 2. Семантическая валидация и резолвинг (Глубокий AST-линтинг)
    linter = OpenAPI_AST_Linter(spec)
    try:
        linter.lint_node(spec, "#")
    except Exception as e:
        raise ValueError(f"Ошибка семантического AST-линтинга: {str(e)}")

    return True