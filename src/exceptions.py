from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from src.templates import templates


async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 404 and "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            request, "404.html", {"detail": exc.detail}, status_code=404
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
