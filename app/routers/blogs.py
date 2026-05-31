from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import requests
from bs4 import BeautifulSoup
from typing import Optional
from datetime import datetime

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
        .order_by(models.Blog.published_at.desc())
        .limit(3)
        .all()        
    )

@router.get("-page")
def blogs_page(
    request: Request,
    imported: Optional[int] = None,
    db: Session = Depends(get_db)
):

    blogs = (
        db.query(models.Blog)
        .order_by(models.Blog.published_at.desc())
        .all()
    )

    is_logged_in = "user_id" in request.session

    return templates.TemplateResponse(
        request,
        "blogs.html",
        {
            "blogs": blogs, 
            "is_logged_in": is_logged_in,
            "imported": imported
         }
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


@router.post("/import-wordpress")
def import_wordpress(
    db: Session = Depends(get_db)
):
    url = "https://ki-hi-ro.com/wp-json/wp/v2/posts?tags=650,440&per_page=100"

    response = requests.get(url)

    if response.status_code != 200:
        return {"error": "取得失敗"}

    posts = response.json()

    imported = 0

    for post in posts:

        blog_url = post["link"]

        exists = (
            db.query(models.Blog)
            .filter(models.Blog.url == blog_url)
            .first()
        )

        if exists:
            continue

        summary = BeautifulSoup(
            post["excerpt"]["rendered"],
            "html.parser"
        ).get_text()

        published_at = datetime.strptime(
            post["date"],
            "%Y-%m-%dT%H:%M:%S"
        ).date()        

        blog = models.Blog(
            title=post["title"]["rendered"],
            url=blog_url,
            summary=summary,
            published_at=published_at
        )

        db.add(blog)
        imported += 1

    db.commit()

    return RedirectResponse(
        url=f"/blogs-page?imported={imported}",
        status_code=303
    )