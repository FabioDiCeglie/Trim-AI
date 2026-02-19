from urllib.parse import urlparse
from workers import Response, Request
from routes import health, docs, openapi_json, connect


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}


def with_cors(response: Response) -> Response:
    headers = dict(response.headers) if response.headers else {}
    headers.update(CORS_HEADERS)
    return Response(response.body, status=response.status, headers=headers)


async def on_fetch(request: Request, env) -> Response:
    path = urlparse(request.url).path
    method = request.method

    if method == "OPTIONS":
        return Response(None, status=204, headers=CORS_HEADERS)

    if path == "/docs":
        return await docs()

    if path == "/openapi.json":
        return with_cors(await openapi_json())

    if path == "/api/v1/health":
        return with_cors(await health())

    if path == "/api/v1/connect" and method == "POST":
        return with_cors(await connect(env, request))

    return with_cors(Response("Not Found", status=404))
