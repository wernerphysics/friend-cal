import calendar
from datetime import date

from sqlmodel import select

from models import Event


def build_calendar(year: int, month: int):
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
    today = date.today()
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        w = []
        for d in week:
            w.append({
                "day": d.day,
                "date": d.isoformat(),
                "is_current_month": d.month == month,
                "is_today": d == today,
            })
        weeks.append(w)
    return weeks


async def get_month_events(year: int, month: int, session):
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    result = await session.execute(
        select(Event).where(Event.date >= start, Event.date < end)
    )
    return result.scalars().all()


def group_events_by_date(events):
    by_date = {}
    for ev in events:
        ds = ev.date.isoformat()
        by_date.setdefault(ds, []).append(ev)
    return by_date


def get_nav_dates(year: int, month: int):
    prev_month = month - 1 if month > 1 else 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year
    return prev_year, prev_month, next_year, next_month


async def calendar_context(year: int, month: int, request, session):
    today = date.today()
    weeks = build_calendar(year, month)
    events = await get_month_events(year, month, session)
    events_by_date = group_events_by_date(events)
    prev_year, prev_month, next_year, next_month = get_nav_dates(year, month)
    return {
        "request": request,
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "weeks": weeks,
        "events_by_date": events_by_date,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    }
