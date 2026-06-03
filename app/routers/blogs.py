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
    page: int = 1,
    imported: Optional[int] = None,
    db: Session = Depends(get_db)
):
    per_page = 4

    total_blogs = db.query(models.Blog).count()
    total_pages = (total_blogs + per_page - 1) // per_page    
    
    blogs = (
        db.query(models.Blog)
        .order_by(models.Blog.published_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    is_logged_in = "user_id" in request.session

    return templates.TemplateResponse(
        request,
        "blogs.html",
        {
            "blogs": blogs, 
            "page": page,
            "total_pages": total_pages,
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

# 詳細ページを取得する
@router.get("-page/{blog_id}")
def blog_detail_page(
    blog_id: int,
    request: Request,
    db: Session = Depends(get_db)
):

    blog = (
        db.query(models.Blog)
        .filter(models.Blog.id == blog_id)
        .first()
    )

    return templates.TemplateResponse(
        request,
        "blog_detail.html",
        {
            "blog": blog,
            "is_logged_in": "user_id" in request.session
        }
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
    
    url = "https://ki-hi-ro.com/wp-json/wp/v2/posts?categories=1191&per_page=100&_embed"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json,text/html,*/*",
        "Referer": "https://ki-hi-ro.com/"
    }    

    response = requests.get(url, headers=headers, timeout=10)    

    if response.status_code != 200:
        return {
            "error": "取得失敗",
            "status_code": response.status_code,
            "text": response.text[:500]
        }

    posts = response.json()

    imported = 0

    for post in posts:

        print(post["title"]["rendered"])

        blog_url = post["link"]

        exists = (
            db.query(models.Blog)
            .filter(models.Blog.url == blog_url)
            .first()
        )

        summary = BeautifulSoup(
            post["excerpt"]["rendered"],
            "html.parser"
        ).get_text()

        published_at = datetime.strptime(
            post["date"],
            "%Y-%m-%dT%H:%M:%S"
        ).date()        

        tag_names = []

        for term_group in post.get("_embedded", {}).get("wp:term", []):
            for term in term_group:
                if term.get("taxonomy") == "post_tag":
                    tag_names.append(term["name"])

        tags = ", ".join(tag_names)

        if exists:
            exists.summary = summary
            exists.content = post["content"]["rendered"]
            exists.published_at = published_at
            exists.tags = tags
            continue        

        blog = models.Blog(
            title=post["title"]["rendered"],
            url=blog_url,
            summary=summary,
            content=post["content"]["rendered"],
            published_at=published_at,
            tags=tags
        )

        db.add(blog)
        imported += 1

    db.commit()

    return RedirectResponse(
        url=f"/blogs-page?imported={imported}",
        status_code=303
    )


@router.get("/test-wordpress")
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