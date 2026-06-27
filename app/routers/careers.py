from datetime import datetime

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app import models
from app.database import get_db
from app.utils.auth import get_current_user


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# 一覧画面の取得
@router.get("/careers-page")
def careers_page(
    request: Request, 
    page: int = 1,
    db: Session = Depends(get_db)
):
    
    per_page = 4
    total_careers = db.query(models.Career).count()
    total_pages = (total_careers + per_page - 1) // per_page    

    current_user = get_current_user(
        request,
        db
    )   

    careers = (
        db.query(models.Career)
        .order_by(models.Career.end_date.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "careers.html",
        {
            "page": page,
            "total_pages": total_pages,
            "careers_count": total_careers,
            "careers": careers,
            "is_logged_in": "user_id" in request.session,
            "current_user": current_user
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

    role = request.session.get("role")    

    is_partner = role in [
        "partner",
        "admin"
    ]    

    is_admin = role == "admin"

    return templates.TemplateResponse(
        request,
        "career_detail.html",
        {
            "career": career,
            "is_logged_in": "user_id" in request.session,
            "is_partner": is_partner,
            "is_admin": is_admin
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
    start_date: str = Form(""),
    end_date: str = Form(""),
    db: Session = Depends(get_db)
):
    
    start_date_value = (
        datetime.strptime(start_date, "%Y-%m-%d").date()
        if start_date
        else None
    )

    end_date_value = (
        datetime.strptime(end_date, "%Y-%m-%d").date()
        if end_date
        else None
    )    
    
    new_career = models.Career(
        title=title,
        company=company,
        period=period,
        description=description,
        technologies=technologies,
        start_date = start_date_value,
        end_date = end_date_value        
    )

    db.add(new_career)
    db.commit()

    return RedirectResponse(url="/careers-page", status_code=303)


# 編集画面を取得
@router.get("/careers-page/{career_id}/edit")
def career_edit_page(
    career_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    career = (
        db.query(models.Career)
        .filter(models.Career.id == career_id)
        .first()
    )

    return templates.TemplateResponse(
        request,
        "edit_career.html",
        {
            "career": career,
            "is_logged_in": "user_id" in request.session
        }
    )


# 編集処理
@router.post("/careers-page/{career_id}/edit")
def career_update(
    career_id: int,
    title: str = Form(...),
    company: str = Form(""),
    period: str = Form(""),
    description: str = Form(""),
    tech_stack: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    db: Session = Depends(get_db)
):
    
    start_date_value = (
        datetime.strptime(start_date, "%Y-%m-%d").date()
        if start_date
        else None
    )

    end_date_value = (
        datetime.strptime(end_date, "%Y-%m-%d").date()
        if end_date
        else None
    )

    career = (
        db.query(models.Career)
        .filter(models.Career.id == career_id)
        .first()
    )

    career.title = title
    career.company = company
    career.period = period
    career.description = description
    career.tech_stack = tech_stack
    career.start_date = start_date_value
    career.end_date = end_date_value    

    db.commit()

    return RedirectResponse(
        url=f"/careers-page/{career.id}",
        status_code=303
    )


# Delete（処理）
@router.post("/careers-page/{career_id}/delete")
def delete_career_from_page(career_id: int, db: Session = Depends(get_db)):
    db_career = db.query(models.Career).filter(models.Career.id == career_id).first()

    if db_career:
        db.delete(db_career)
        db.commit()

    return RedirectResponse(
        url="/careers-page",
        status_code=303
    )
