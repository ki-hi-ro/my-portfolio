from app import models
from app.database import get_db
from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from urllib.parse import urlparse

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def safe_redirect_path(next_url: str | None) -> str:
    if not next_url:
        return "/"

    parsed_url = urlparse(next_url)

    if parsed_url.scheme or parsed_url.netloc:
        return "/"

    if not next_url.startswith("/") or next_url.startswith("//") or "\\" in next_url:
        return "/"

    return next_url


@router.get("/login")
def login_page(
    request: Request,
    next_url: str = Query("/", alias="next")
):
    redirect_path = safe_redirect_path(next_url)

    if "user_id" in request.session:
        return RedirectResponse(
            redirect_path,
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "error": None,
            "next_url": redirect_path,
            "is_logged_in": False
        }
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next_url: str = Form("/", alias="next"),
    db: Session = Depends(get_db)
):
    redirect_path = safe_redirect_path(next_url)
    
    user = (
        db.query(models.User)
        .filter(models.User.username == username)
        .first()
    )

    if not user:
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": "ユーザー名またはパスワードが違います",
                "next_url": redirect_path,
                "is_logged_in": False
            }
        )

    if not pwd_context.verify(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": "ユーザー名またはパスワードが違います",
                "next_url": redirect_path,
                "is_logged_in": False
            }
        )

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role

    return RedirectResponse(
        redirect_path,
        status_code=303
    )


@router.get("/logout")
def logout(request: Request):
    request.session.clear()

    return RedirectResponse(
        "/",
        status_code=303
    )
