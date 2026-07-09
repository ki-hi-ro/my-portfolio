import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.timeline import load_timeline_dataset, normalize_category_key


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def is_dev_page_allowed(request: Request) -> bool:
    app_env = os.getenv("APP_ENV", "development").lower()

    if app_env != "production":
        return True

    if os.getenv("ALLOW_DEV_PAGES", "").lower() in {"1", "true", "yes", "on"}:
        return True

    dev_page_token = os.getenv("DEV_PAGE_TOKEN", "")

    return bool(dev_page_token and request.query_params.get("token") == dev_page_token)


@router.get("/")
def top_page(
    request: Request,
    year: int | None = None,
    category: str | None = None,
):
    timeline = load_timeline_dataset()
    selected_year = year if year in timeline.years else timeline.current_year
    category_key = normalize_category_key(category)
    selected_category = category_key if category_key in timeline.category_counts else None
    records = timeline.items_for_filters(selected_year, selected_category)
    latest_record = timeline.timeline_items[0] if timeline.timeline_items else None

    return templates.TemplateResponse(
        request,
        "top.html",
        {
            "timeline": timeline,
            "records": records,
            "latest_record": latest_record,
            "selected_year": selected_year,
            "active_category": selected_category,
            "active_year": selected_year,
            "current_item_year": None,
            "is_logged_in": "user_id" in request.session,
            "user_id": request.session.get("user_id"),
            "is_home": True,
            "page_title": "My Portfolio｜これまでの実績",
        },
    )


@router.get("/records/{record_id}")
def record_detail_page(
    record_id: str,
    request: Request,
):
    timeline = load_timeline_dataset()
    record = timeline.find_public_item(record_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    same_year_records = [
        item
        for item in timeline.timeline_items
        if item.year == record.year and item.id != record.id
    ]
    adjacent_records = [
        item
        for item in timeline.timeline_items
        if item.id != record.id and item not in same_year_records
    ]
    related_records = tuple((same_year_records + adjacent_records)[:6])

    return templates.TemplateResponse(
        request,
        "record_detail.html",
        {
            "timeline": timeline,
            "record": record,
            "related_records": related_records,
            "active_year": record.year,
            "current_item_year": record.year,
            "active_category": record.category,
            "is_logged_in": "user_id" in request.session,
            "user_id": request.session.get("user_id"),
            "is_home": False,
            "is_record_detail": True,
            "page_title": f"{record.title}｜My Portfolio",
        },
    )


def render_timeline_admin_page(request: Request):
    if not is_dev_page_allowed(request):
        raise HTTPException(status_code=404, detail="Not found")

    timeline = load_timeline_dataset()

    return templates.TemplateResponse(
        request,
        "timeline_drafts.html",
        {
            "timeline": timeline,
            "records": timeline.draft_items,
            "active_year": None,
            "current_item_year": None,
            "active_category": None,
            "is_logged_in": "user_id" in request.session,
            "user_id": request.session.get("user_id"),
            "is_home": True,
            "is_timeline_admin": True,
            "page_title": "タイムライン管理｜My Portfolio",
        },
    )


@router.get("/admin/timeline")
def timeline_admin_page(request: Request):
    return render_timeline_admin_page(request)


@router.get("/dev/timeline-drafts")
def timeline_drafts_page(request: Request):
    return render_timeline_admin_page(request)
