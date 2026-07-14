from uuid import uuid4

from fastapi import Request


async def ensure_poster_token(request: Request, call_next):
    response = await call_next(request)
    if "poster_token" not in request.cookies:
        response.set_cookie("poster_token", uuid4().hex, max_age=365 * 24 * 3600, httponly=True)
    return response
