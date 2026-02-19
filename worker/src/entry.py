from urllib.parse import urlparse
from workers import Response, Request
from routes import health, docs, openapi_json, connect
from services import CredentialService
from providers import get_provider
from utils import error


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

    # ── Provider routes: /api/v1/:provider/:resource ─────────────────
    parts = path.strip("/").split("/")  # ["api", "v1", "<provider>", "<resource>"]
    if len(parts) == 4 and parts[0] == "api" and parts[1] == "v1" and method == "GET":
        return with_cors(await handle_provider_request(env, request, parts[2], parts[3]))

    return with_cors(Response("Not Found", status=404))


async def handle_provider_request(env, request, provider_name: str, resource: str) -> Response:
    """Resolve credentials, init the provider, call the right method."""
    creds = await CredentialService(env).resolve(request)
    if creds is None:
        return error("Missing or invalid Authorization header", 401)

    if creds.get("provider") != provider_name:
        return error(f"connectionId is for '{creds['provider']}', not '{provider_name}'", 400)

    provider = get_provider(provider_name, creds["credentials"])
    if provider is None:
        return error(f"Unknown provider: {provider_name}", 400)

    import json
    try:
        if resource == "projects":
            data = await provider.get_projects()
        elif resource == "compute":
            data = await provider.get_compute()
        elif resource == "metrics":
            data = await provider.get_metrics(request)
        elif resource == "billing":
            data = await provider.get_billing()
        else:
            return error(f"Unknown resource: {resource}", 404)

        return Response(json.dumps(data), headers={"Content-Type": "application/json"})
    except Exception as e:
        return error(str(e), 500)
