from app import models
from app.schemas import Work, WorkResponse
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.database import get_db

router = APIRouter()

def convert_work(work):
    return {
        "id": work.id,
        "title": work.title,
        "description": work.description,
        "github_url": work.github_url,
        "app_url": work.app_url,
        "technologies": work.technologies.split(",") if work.technologies else [],
        "created_at": work.created_at,
    }

templates = Jinja2Templates(directory="app/templates")


# =========================
# API Endpoints
# =========================

# Create
@router.post("/works", response_model=WorkResponse)
def create_work(
    work: Work,
    db: Session = Depends(get_db)
):
    new_work = models.Work(
        title=work.title,
        description=work.description,
        github_url=work.github_url,
        app_url=work.app_url,
        technologies=",".join(work.technologies),
    )

    db.add(new_work)
    db.commit()
    db.refresh(new_work)

    return convert_work(new_work)


# Read
@router.get("/works", response_model=list[WorkResponse])
def read_works(db: Session = Depends(get_db)):
    works = db.query(models.Work).all()

    return [
        convert_work(work)
        for work in works
    ]


# =========================
# HTML Pages
# =========================

# Create（画面）
@router.get("/works-page/new")
def new_work_page(
    request: Request,
):

    return templates.TemplateResponse(
        request,
        "new_work.html",
        {
            "is_logged_in": "user_id" in request.session
        }
    )


#Create（処理）
@router.post("/works-page")
def create_work_from_page(
    title: str = Form(...),
    description: str = Form(...),
    github_url: str = Form(""),
    app_url: str = Form(""),
    tech_stack: str = Form(""),
    db: Session = Depends(get_db),
    image_url: str = Form(""),
):
    new_work = models.Work(
        title=title,
        description=description,
        github_url=github_url,
        app_url=app_url,
        tech_stack=tech_stack,
        image_url=image_url,
    )

    db.add(new_work)
    db.commit()

    return RedirectResponse(url="/", status_code=303)


# Read（一覧）
@router.get("/works-page")
def works_page(
    request: Request, 
    page: int = 1,
    db: Session = Depends(get_db)
):
    per_page = 4
    total_works = db.query(models.Work).count()
    total_pages = (total_works + per_page - 1) // per_page

    works = (
        db.query(models.Work)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    for work in works:
        posts = (
            db.query(models.Post)
            .filter(models.Post.work_id == work.id)
            .offset((page - 1) * per_page)
            .limit(per_page)            
            .all()
        )

        work.post_count = len(posts)

        total_minutes = sum(
            post.work_time_minutes
            for post in posts
        )

        work.total_minutes = total_minutes
        work.total_hours = total_minutes // 60
        work.remaining_minutes = total_minutes % 60        

    return templates.TemplateResponse(
        request,
        "works.html",
        {
            "page": page,
            "total_pages": total_pages,
            "works": works,
            "is_logged_in": "user_id" in request.session
        }
    )


# Read（詳細）
@router.get("/works-page/{work_id}")
def work_detail_page(
    work_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    work = (
        db.query(models.Work)
        .filter(models.Work.id == work_id)
        .first()
    )

    return templates.TemplateResponse(
        request,
        "work_detail.html",
        {
            "work": work,
            "is_logged_in": "user_id" in request.session
        }
    )


# Update（画面）
@router.get("/works-page/{work_id}/edit")
def edit_work_page(work_id: int, request: Request, db: Session = Depends(get_db)):
    work = db.query(models.Work).filter(models.Work.id == work_id).first()

    return templates.TemplateResponse(
        request,
        "edit_work.html",
        {
            "work": work,
            "is_logged_in": "user_id" in request.session
        }
    )


# Update（処理）
@router.post("/works-page/{work_id}/edit")
def update_work_from_page(
    work_id: int,
    title: str = Form(...),
    description: str = Form(...),
    github_url: str = Form(""),
    app_url: str = Form(""),
    tech_stack: str = Form(""),
    db: Session = Depends(get_db),
    image_url: str = Form(""),
):
    work = db.query(models.Work).filter(models.Work.id == work_id).first()

    if work:
        work.title = title
        work.description = description
        work.github_url = github_url
        work.app_url = app_url
        work.tech_stack = tech_stack
        work.image_url = image_url
        db.commit()

    return RedirectResponse(
        url=f"/works-page/{work_id}",
        status_code=303
    )


# Delete（処理）
@router.post("/works-page/{work_id}/delete")
def delete_work_from_page(work_id: int, db: Session = Depends(get_db)):
    db_work = db.query(models.Work).filter(models.Work.id == work_id).first()

    if db_work:
        db.delete(db_work)
        db.commit()

    return RedirectResponse(
        url="/works-page",
        status_code=303
    )