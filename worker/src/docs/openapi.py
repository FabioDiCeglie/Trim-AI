OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Trim API",
        "description": "Cloud waste detection engine — surfaces idle, oversized, and unused resources across cloud providers.",
        "version": "0.1.0",
    },
    "tags": [
        {"name": "Health", "description": "Service health"},
    ],
    "paths": {
        "/health": {
            "get": {
                "tags": ["Health"],
                "summary": "Health check",
                "operationId": "health",
                "responses": {
                    "204": {"description": "Service is healthy"}
                },
            }
        },
    },
    "components": {
        "schemas": {
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"}
                },
            }
        }
    },
}
