from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from app.routers import posts as posts_router
from app.routers import works as works_router
from app.routers import login as login_router
from app.routers import blogs as blogs_router
from app.routers import careers as careers_router
from app.database import engine
from app import models
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(posts_router.router)
app.include_router(works_router.router)
app.include_router(login_router.router)
app.include_router(blogs_router.router)
app.include_router(careers_router.router)

templates = Jinja2Templates(directory="app/templates")


# Read
@app.get("/")
def top_page(
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
    is_logged_in = "user_id" in request.session

    works = (
        db.query(models.Work)
        .order_by(models.Work.id.desc())
        .limit(2)
        .all()
    )

    blogs = (
        db.query(models.Blog)
        .order_by(models.Blog.published_at.desc())
        .limit(2)
        .all()
    )    

    recent_careers = (
        db.query(models.Career)
        .order_by(models.Career.id.desc())
        .limit(2)
        .all()
    )    

    career = models.Career(
        title="Python API開発エンジニア",
        company="物流システム開発",
        period="2025.07 - 2026.06",
        description="""
    FastAPIを用いたAPI開発。
    WCSとAGVの連携システム開発。
    Linux環境での障害調査や
    PostgreSQLを利用したデータ管理を担当。
    """,
        technologies="Python,FastAPI,PostgreSQL,Linux"
    )

    db.add(career)
    db.commit()    

    return templates.TemplateResponse(
        request,
        "top.html",
        {
            "works": works,
            "blogs": blogs,
            "recent_careers": recent_careers,
            "user_id": user_id,
            "is_logged_in": is_logged_in
        }
    )

# ログイン
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key"
)
