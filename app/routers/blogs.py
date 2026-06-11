from typing import Optional
from datetime import datetime
import os
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Form
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session
import pandas as pd
import requests
from bs4 import BeautifulSoup

from app import models
from app.database import get_db


templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/blogs",
    tags=["Blogs"]
)


# 一覧ページ取得
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
            "imported": imported,
            "is_production": os.getenv("APP_ENV") == "production"
         }
    )


# 新規登録ページを取得する
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


# 新規登録の処理
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


# WordPressから取得
def get_slug_from_url(url: str) -> str:
    parsed = urlparse(url)

    path = parsed.path.rstrip("/")

    return path.split("/")[-1]


def get_tech_blog_urls_from_sheet():
    sheet_csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS3wbw1oz179Lc_HXNLo6BKO1P7xyD1xnjxTVF6CwNZ-6DpnYIxcYDnR9oSKpp_p-EOWm1uTfKmq8eC/pub?output=csv"

    df = pd.read_csv(sheet_csv_url)

    tech_blogs = df[
        df["技術ブログ"] == "◯"
    ]

    urls = tech_blogs["記事URL"].dropna().tolist()

    return urls


@router.post("/import-wordpress")
def import_wordpress(
    db: Session = Depends(get_db)
):
    
    base_url = "https://ki-hi-ro.com/wp-json/wp/v2/posts"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/html,*/*",
        "Referer": "https://ki-hi-ro.com/"
    }

    target_urls = get_tech_blog_urls_from_sheet()

    imported = 0
    updated = 0
    skipped = 0
    wp_urls = []

    for target_url in target_urls:
        slug = get_slug_from_url(target_url)

        response = requests.get(
            f"{base_url}?slug={slug}&_embed",
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            skipped += 1
            continue

        posts = response.json()

        if not posts:
            skipped += 1
            continue

        post = posts[0]

        title = post["title"]["rendered"]
        blog_url = post["link"]
        content = post["content"]["rendered"]

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

        wp_urls.append(blog_url)

        exists = (
            db.query(models.Blog)
            .filter(models.Blog.url == blog_url)
            .first()
        )

        if exists:
            exists.title = title
            exists.summary = summary
            exists.content = content
            exists.published_at = published_at
            exists.tags = tags
            updated += 1
            continue

        blog = models.Blog(
            title=title,
            url=blog_url,
            summary=summary,
            content=content,
            published_at=published_at,
            tags=tags
        )

        db.add(blog)
        imported += 1

    deleted = 0

    if wp_urls:
        deleted = (
            db.query(models.Blog)
            .filter(models.Blog.url.notin_(wp_urls))
            .delete(synchronize_session=False)
        )

    db.commit()

    return RedirectResponse(
        url=(
            f"/blogs-page"
            f"?imported={imported}"
            f"&updated={updated}"
            f"&deleted={deleted}"
            f"&skipped={skipped}"
        ),
        status_code=303
    )