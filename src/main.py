from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from src.middleware import ensure_poster_token
from src.exceptions import http_exception_handler
from src.boards import router as board_router
from src.posts import router as post_router

app = FastAPI()

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(board_router.router)
app.include_router(post_router.router)

app.middleware("http")(ensure_poster_token)
app.add_exception_handler(HTTPException, http_exception_handler)


@app.get("/")
def get_status():
    return {"status": "ok"}
