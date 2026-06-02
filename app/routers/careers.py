from app import models
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.database import get_db

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

# 一覧画面の取得
@router.get("/careers-page")
def careers_page(request: Request, db: Session = Depends(get_db)):
    careers = db.query(models.Career).all()

    return templates.TemplateResponse(
        request,
        "careers.html",
        {
            "careers": careers,
            "is_logged_in": "user_id" in request.session
        }
    )


# 新規登録画面の取得
@router.get("/careers-page/new")
def new_career_page(
    request: Request,
):
    return templates.TemplateResponse(
        request,
        "new_career.html",
        {
            "is_logged_in": "user_id" in request.session
        }
    )


# 詳細画面の取得
@router.get("/careers-page/{career_id}")
def career_detail_page(
    career_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    career = (
        db.query(models.Career)
        .filter(models.Career.id == career_id)
        .first()
    )

    posts = (
        db.query(models.Post)
        .filter(models.Post.career_id == career.id)
        .all()
    )

    total_minutes = sum(
        post.work_time_minutes
        for post in posts
    )

    career.post_count = len(posts)
    career.total_minutes = total_minutes
    career.total_hours = total_minutes // 60
    career.remaining_minutes = total_minutes % 60

    return templates.TemplateResponse(
        request,
        "career_detail.html",
        {
            "career": career,
            "posts": posts,
            "is_logged_in": "user_id" in request.session
        }
    )


# 新規登録の処理
@router.post("/careers-page")
def create_career(
    title: str = Form(...),
    company: str = Form(...),
    period: str = Form(...),
    description: str = Form(...),
    technologies: str = Form(...),
    db: Session = Depends(get_db)
):
    new_career = models.Career(
        title=title,
        company=company,
        period=period,
        description=description,
        technologies=technologies
    )

    db.add(new_career)
    db.commit()

    return RedirectResponse(url="/careers-page", status_code=303)    