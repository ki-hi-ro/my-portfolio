from fastapi import Depends, Request
from app import models
from sqlalchemy.orm import Session
from app.database import get_db

from fastapi import APIRouter
from fastapi.templating import Jinja2Templates

from datetime import datetime


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# 画面の取得
@router.get("/")
def top_page(
    request: Request,
    db: Session = Depends(get_db)
):
    
    user_id = request.session.get("user_id")
    is_logged_in = "user_id" in request.session

    works = (
        db.query(models.Work)
        .order_by(models.Work.id.asc())
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

    works_count = db.query(models.Work).count()

    blogs_count = db.query(models.Blog).count()

    career_years = datetime.now().year - 2017 

    return templates.TemplateResponse(
        request,
        "top.html",
        {
            "works": works,
            "blogs": blogs,
            "recent_careers": recent_careers,
            "user_id": user_id,
            "is_logged_in": is_logged_in,
            "works_count": works_count,
            "blogs_count": blogs_count,
            "career_years": career_years
        }
    )