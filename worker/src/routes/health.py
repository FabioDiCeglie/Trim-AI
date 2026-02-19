from workers import Response


async def health() -> Response:
    return Response(None, status=204)
