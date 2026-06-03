from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import top as top_router
from app.routers import posts as posts_router
from app.routers import works as works_router
from app.routers import login as login_router
from app.routers import blogs as blogs_router
from app.routers import careers as careers_router

from app.database import engine
from app import models

from starlette.middleware.sessions import SessionMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(top_router.router)
app.include_router(posts_router.router)
app.include_router(works_router.router)
app.include_router(login_router.router)
app.include_router(blogs_router.router)
app.include_router(careers_router.router)

# ログイン
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key"
)


@app.get("/test-wordpress")
def test_wordpress():
    import requests

    url = "https://ki-hi-ro.com/wp-json/wp/v2/posts?per_page=1"

    response = requests.get(
        url,
        timeout=10,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    return {
        "status": response.status_code,
        "headers": dict(response.headers),
        "body": response.text[:300]
    }