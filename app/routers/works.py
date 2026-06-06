from app import models
from app.schemas import Work, WorkResponse
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.database import get_db
from datetime import datetime

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


# 作成処理
@router.post("/works-page")
def create_work_from_page(
    title: str = Form(...),
    description: str = Form(...),
    github_url: str = Form(""),
    app_url: str = Form(""),
    tech_stack: str = Form(""),
    db: Session = Depends(get_db),
    image_url: str = Form(""),
    started_at: str = Form(""),
):

    started_at = datetime.strptime(
        started_at,
        "%Y-%m-%d"
    ).date()
    
    new_work = models.Work(
        title=title,
        description=description,
        github_url=github_url,
        app_url=app_url,
        tech_stack=tech_stack,
        image_url=image_url,
        started_at=started_at,
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
    
    per_page = 6
    total_works = db.query(models.Work).count()
    total_pages = (total_works + per_page - 1) // per_page

    works_count = db.query(models.Work).count()

    tech_set = set()

    works = (
        db.query(models.Work)
        .order_by(models.Work.started_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    
    for work in works:
        if work.tech_stack:
            for tech in work.tech_stack.split(","):
                tech_set.add(tech.strip())

    tech_count = len(tech_set)    


    return templates.TemplateResponse(
        request,
        "works.html",
        {
            "page": page,
            "total_pages": total_pages,
            "works": works,
            "is_logged_in": "user_id" in request.session,
            "works_count": works_count,
            "tech_count": tech_count,            
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

    role = request.session.get("role")
    is_admin = role == "admin"

    return templates.TemplateResponse(
        request,
        "work_detail.html",
        {
            "work": work,
            "is_logged_in": "user_id" in request.session,
            "is_admin": is_admin
        }
    )


# 編集画面
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


# 更新（編集）処理
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
    started_at: str = Form(""),
):
    
    work = db.query(models.Work).filter(models.Work.id == work_id).first()

    if not work:
        return RedirectResponse(
            url="/works-page",
            status_code=303
        )    

    started_at_date = (
        datetime.strptime(started_at, "%Y-%m-%d").date()
        if started_at
        else None
    )    

    if work:
        work.title = title
        work.description = description
        work.github_url = github_url
        work.app_url = app_url
        work.tech_stack = tech_stack
        work.image_url = image_url
        work.started_at = started_at_date
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