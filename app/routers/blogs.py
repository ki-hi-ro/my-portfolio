from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/blogs",
    tags=["Blogs"]
)


@router.post("/", response_model=schemas.Blog)
def create_blog(
    blog: schemas.BlogCreate,
    db: Session = Depends(get_db)
):
    db_blog = models.Blog(**blog.model_dump())

    db.add(db_blog)
    db.commit()
    db.refresh(db_blog)

    return db_blog


@router.get("/", response_model=list[schemas.Blog])
def read_blogs(
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Blog)
        .order_by(models.Blog.created_at.desc())
        .all()
    )

@router.get("-page")
def blogs_page(
    request: Request,
    db: Session = Depends(get_db)
):
    blogs = db.query(models.Blog).order_by(models.Blog.created_at.desc()).all()

    return templates.TemplateResponse(
        request,
        "blogs.html",
        {"blogs": blogs}
    )

@router.get("/new")
def blog_new_page(
    request: Request
):
    return templates.TemplateResponse(
        request,
        "blog_new.html",
        {}
    )

@router.post("/new")
def create_blog_from_form(
    title: str = Form(...),
    url: str = Form(""),
    summary: str = Form(""),
    tags: str = Form(""),
    db: Session = Depends(get_db)
):
    blog = models.Blog(
        title=title,
        url=url,
        summary=summary,
        tags=tags
    )

    db.add(blog)
    db.commit()

    return RedirectResponse(
        "/blogs-page",
        status_code=303
    )