from app import models
from app.database import get_db
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": None}
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    
    user = (
        db.query(models.User)
        .filter(models.User.username == username)
        .first()
    )

    if not user:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "ユーザー名またはパスワードが違います"}
        )

    if not pwd_context.verify(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "ユーザー名またはパスワードが違います"}
        )

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role

    return RedirectResponse(
        "/",
        status_code=303
    )


@router.get("/logout")
def logout(request: Request):
    request.session.clear()

    return RedirectResponse(
        "/",
        status_code=303
    )