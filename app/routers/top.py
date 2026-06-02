from fastapi import Depends, Request
from app import models
from sqlalchemy.orm import Session
from app.database import get_db

from fastapi import APIRouter
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Read
@router.get("/")
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