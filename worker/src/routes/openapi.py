import json
from workers import Response
from docs import OPENAPI_SPEC


SWAGGER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trim API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css">
    <style>
        body { margin: 0; padding: 0; }
        .swagger-ui .topbar { display: none; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script>
        window.onload = () => {
            SwaggerUIBundle({
                url: '/openapi.json',
                dom_id: '#swagger-ui',
                presets: [SwaggerUIBundle.presets.apis],
                layout: 'BaseLayout',
                deepLinking: true,
            });
        };
    </script>
</body>
</html>"""


async def docs() -> Response:
    return Response(SWAGGER_HTML, status=200, headers={"Content-Type": "text/html"})


async def openapi_json() -> Response:
    return Response(
        json.dumps(OPENAPI_SPEC),
        status=200,
        headers={"Content-Type": "application/json"},
    )
