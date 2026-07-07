import uuid
from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from calendar_service import calendar_context
from templating import templates

import nextcloud

router = APIRouter()


def _user_id(request: Request) -> str:
    return str(request.session["user_id"])


def _parse_date(value) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


@router.post("/events", response_class=HTMLResponse)
async def create_event(request: Request):
    form = await request.form()
    title = form.get("title", "").strip()
    event_date = _parse_date(form.get("date")) or date.today()

    if not title or not form.get("date"):
        return await _render_calendar(request, event_date.year, event_date.month)

    ev = {
        "uid": str(uuid.uuid4()),
        "title": title,
        "date": event_date,
        "time": form.get("time") or None,
        "end_time": form.get("end_time") or None,
        "description": form.get("description") or None,
        "location": form.get("location") or None,
        "color": form.get("color") or None,
        "created_by": _user_id(request),
    }
    await nextcloud.create_event(ev)
    return await _render_calendar(request, event_date.year, event_date.month)


@router.get("/events/{event_id}", response_class=HTMLResponse)
async def event_detail(request: Request, event_id: str):
    ev = await nextcloud.get_event(event_id)
    if not ev:
        return HTMLResponse("", status_code=404)

    return templates.TemplateResponse(request, "events/detail.html", {
        "event": ev,
        "is_owner": ev.get("created_by") == _user_id(request),
    })


@router.get("/events/{event_id}/edit", response_class=HTMLResponse)
async def event_edit_form(request: Request, event_id: str):
    ev = await nextcloud.get_event(event_id)
    if not ev:
        return HTMLResponse("", status_code=404)

    if ev.get("created_by") != _user_id(request):
        return HTMLResponse("", status_code=403)

    return templates.TemplateResponse(request, "events/edit_form.html", {
        "event": ev,
    })


@router.put("/events/{event_id}", response_class=HTMLResponse)
async def update_event(request: Request, event_id: str):
    ev = await nextcloud.get_event(event_id)
    if not ev:
        return HTMLResponse("", status_code=404)

    if ev.get("created_by") != _user_id(request):
        return HTMLResponse("", status_code=403)

    form = await request.form()
    ev["title"] = form.get("title", ev["title"])
    ev["time"] = form.get("time") or None
    ev["end_time"] = form.get("end_time") or None
    ev["description"] = form.get("description") or None
    ev["location"] = form.get("location") or None
    ev["color"] = form.get("color") or None

    new_date = _parse_date(form.get("date"))
    if new_date:
        ev["date"] = new_date

    year, month = ev["date"].year, ev["date"].month

    await nextcloud.update_event(event_id, ev)

    return await _render_calendar(request, year, month)


@router.delete("/events/{event_id}", response_class=HTMLResponse)
async def delete_event(request: Request, event_id: str):
    ev = await nextcloud.get_event(event_id)
    if not ev:
        return HTMLResponse("", status_code=404)

    if ev.get("created_by") != _user_id(request):
        return HTMLResponse("", status_code=403)

    year, month = ev["date"].year, ev["date"].month
    await nextcloud.delete_event(event_id)

    return await _render_calendar(request, year, month)


async def _render_calendar(request, year, month):
    ctx = await calendar_context(year, month, request)
    return templates.TemplateResponse(request, "calendar.html", ctx)
