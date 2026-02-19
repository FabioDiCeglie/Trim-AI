from workers import Response


async def health() -> Response:
    return Response("", status=204)
