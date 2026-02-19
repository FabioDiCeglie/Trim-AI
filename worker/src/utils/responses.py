import json
from workers import Response


def error(message: str, status: int) -> Response:
    return Response(
        json.dumps({"error": message}),
        status=status,
        headers={"Content-Type": "application/json"},
    )


def ok(data: dict, status: int = 200) -> Response:
    return Response(
        json.dumps(data),
        status=status,
        headers={"Content-Type": "application/json"},
    )
