import httpx
from fastapi import APIRouter, Request, Response, HTTPException, Body

router = APIRouter(prefix="/api/v1/proxy", tags=["Proxy"])

# 1. Главная функция-курьер (без роутера, просто делает работу)
async def do_proxy(path: str, request: Request, target_url: str):
    if not target_url:
        raise HTTPException(status_code=400, detail="Missing target_url parameter")

    url = f"{target_url.rstrip('/')}/{path}"
    
    headers = dict(request.headers)
    headers.pop("host", None)

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