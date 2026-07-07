import calendar
from datetime import date
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    today = date.today()
    weeks = build_calendar(today.year, today.month)
    prev_month = today.month - 1 if today.month > 1 else 12
    prev_year = today.year - 1 if today.month == 1 else today.year
    next_month = today.month + 1 if today.month < 12 else 1
    next_year = today.year + 1 if today.month == 12 else today.year
    return templates.TemplateResponse(request, "index.html", {
        "year": today.year,
        "month": today.month,
        "month_name": calendar.month_name[today.month],
        "weeks": weeks,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    })


@app.get("/calendar", response_class=HTMLResponse)
async def calendar_month(request: Request, year: int, month: int):
    if month < 1 or month > 12:
        month = date.today().month
    weeks = build_calendar(year, month)
    prev_month = month - 1 if month > 1 else 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year
    return templates.TemplateResponse(request, "calendar.html", {
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "weeks": weeks,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    })


def run():
    import uvicorn
    uvicorn.run("main:app")
