import socket
import ipaddress
import httpx
from urllib.parse import urlparse
from fastapi import APIRouter, Request, Response, HTTPException, Body

router = APIRouter(prefix="/api/v1/proxy", tags=["Proxy"])

def is_private_ip(ip_str: str) -> bool:
    """Проверяет, является ли IP-адрес приватным, локальным или зарезервированным."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified
    except ValueError:
        return True

# 1. Главная функция-курьер с защитой от SSRF и TOCTOU DNS Rebinding
async def do_proxy(path: str, request: Request, target_url: str):
    if not target_url:
        raise HTTPException(status_code=400, detail="Missing target_url parameter")

    # Извлекаем оригинальный хост
    parsed_url = urlparse(target_url)
    hostname = parsed_url.hostname

    if not hostname:
        raise HTTPException(status_code=400, detail="Invalid target_url")

    # Двойная резолюция с фиксацией IP: 
    # Сначала резолвим домен через socket, чтобы проверить IP
    try:
        resolved_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        raise HTTPException(status_code=400, detail=f"Could not resolve hostname: {hostname}")

    # Проверка на приватные/локальные адреса
    if is_private_ip(resolved_ip):
        raise HTTPException(status_code=403, detail="Access to local/private networks is forbidden (SSRF protection)")

    # Формируем безопасный URL, используя уже проверенный IP-адрес.
    # Это предотвращает атаку TOCTOU (DNS Rebinding), так как httpx не будет повторно резолвить домен перед самим запросом.
    port_str = f":{parsed_url.port}" if parsed_url.port else ""
    safe_target_url = f"{parsed_url.scheme}://{resolved_ip}{port_str}{parsed_url.path}"
    
    url = f"{safe_target_url.rstrip('/')}/{path}"
    
    headers = dict(request.headers)
    # Обязательно возвращаем оригинальный домен в заголовок Host, иначе веб-серверы (виртуальные хосты) не поймут запрос
    headers["host"] = hostname

    # Наш исправленный клиент с таймаутом
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            proxy_req = client.build_request(
                method=request.method,
                url=url,
                headers=headers,
                content=await request.body(),
                params=request.query_params
            )
            proxy_resp = await client.send(proxy_req)
            
            return Response(
                content=proxy_resp.content,
                status_code=proxy_resp.status_code,
                headers=dict(proxy_resp.headers)
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Bad Gateway: {str(e)}")

# 2. Пять независимых ручек, чтобы Swagger не путался
@router.get("/{path:path}")
async def proxy_get(path: str, request: Request, target_url: str):
    return await do_proxy(path, request, target_url)

@router.post("/{path:path}")
async def proxy_post(path: str, request: Request, target_url: str, body: dict = Body(None)):
    return await do_proxy(path, request, target_url)

@router.put("/{path:path}")
async def proxy_put(path: str, request: Request, target_url: str, body: dict = Body(None)):
    return await do_proxy(path, request, target_url)

@router.patch("/{path:path}")
async def proxy_patch(path: str, request: Request, target_url: str, body: dict = Body(None)):
    return await do_proxy(path, request, target_url)

@router.delete("/{path:path}")
async def proxy_delete(path: str, request: Request, target_url: str):
    return await do_proxy(path, request, target_url)