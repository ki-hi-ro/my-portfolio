from fastapi import Request
from sqlalchemy.orm import Session

from app import models


def get_current_user(
    request: Request,
    db: Session
):
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    return (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )