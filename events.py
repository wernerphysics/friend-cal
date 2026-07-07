import calendar
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from calendar_service import calendar_context
from db import get_session
from models import Event
from templating import templates

router = APIRouter()


def _user_id(request: Request) -> int:
    return request.session["user_id"]


def _user_name(request: Request) -> str:
    return request.session.get("user_name", "")


@router.post("/events", response_class=HTMLResponse)
async def create_event(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    form = await request.form()
    title = form.get("title", "").strip()
    event_date = form.get("date", "")
    year = int(form.get("year", date.today().year))
    month = int(form.get("month", date.today().month))

    if not title or not event_date:
        return await _render_calendar(request, year, month, session)

    ev = Event(
        title=title,
        date=date.fromisoformat(event_date),
        time=form.get("time") or None,
        end_time=form.get("end_time") or None,
        description=form.get("description") or None,
        location=form.get("location") or None,
        color=form.get("color") or None,
        created_by=_user_id(request),
    )
    session.add(ev)
    await session.commit()
    return await _render_calendar(request, year, month, session)


@router.get("/events/{event_id}", response_class=HTMLResponse)
async def event_detail(
    request: Request,
    event_id: int,
    session: AsyncSession = Depends(get_session),
):
    ev = await session.get(Event, event_id)
    if not ev:
        return HTMLResponse("", status_code=404)

    uid = _user_id(request)
    year, month = ev.date.year, ev.date.month

    return templates.TemplateResponse(request, "events/detail.html", {
        "event": ev,
        "is_owner": ev.created_by == uid,
        "year": year,
        "month": month,
    })


@router.get("/events/{event_id}/edit", response_class=HTMLResponse)
async def event_edit_form(
    request: Request,
    event_id: int,
    session: AsyncSession = Depends(get_session),
):
    ev = await session.get(Event, event_id)
    if not ev:
        return HTMLResponse("", status_code=404)

    uid = _user_id(request)
    if ev.created_by != uid:
        return HTMLResponse("", status_code=403)

    return templates.TemplateResponse(request, "events/edit_form.html", {
        "event": ev,
        "year": ev.date.year,
        "month": ev.date.month,
    })


@router.put("/events/{event_id}", response_class=HTMLResponse)
async def update_event(
    request: Request,
    event_id: int,
    session: AsyncSession = Depends(get_session),
):
    ev = await session.get(Event, event_id)
    if not ev:
        return HTMLResponse("", status_code=404)

    if ev.created_by != _user_id(request):
        return HTMLResponse("", status_code=403)

    ev_year = ev.date.year
    ev_month = ev.date.month

    form = await request.form()
    ev.title = form.get("title", ev.title)
    ev.time = form.get("time") or None
    ev.end_time = form.get("end_time") or None
    ev.description = form.get("description") or None
    ev.location = form.get("location") or None
    ev.color = form.get("color") or None

    date_str = form.get("date")
    if date_str:
        ev.date = date.fromisoformat(date_str)
        ev_year = ev.date.year
        ev_month = ev.date.month

    year_str = form.get("year")
    month_str = form.get("month")
    year = int(year_str) if year_str else ev_year
    month = int(month_str) if month_str else ev_month

    session.add(ev)
    await session.commit()

    return await _render_calendar(request, year, month, session)


@router.delete("/events/{event_id}", response_class=HTMLResponse)
async def delete_event(
    request: Request,
    event_id: int,
    session: AsyncSession = Depends(get_session),
):
    ev = await session.get(Event, event_id)
    if not ev:
        return HTMLResponse("", status_code=404)

    if ev.created_by != _user_id(request):
        return HTMLResponse("", status_code=403)

    year, month = ev.date.year, ev.date.month
    await session.delete(ev)
    await session.commit()

    return await _render_calendar(request, year, month, session)


async def _render_calendar(request, year, month, session):
    ctx = await calendar_context(year, month, request, session)
    return templates.TemplateResponse(request, "calendar.html", ctx)
