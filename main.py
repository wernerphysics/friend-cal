import calendar
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from auth import router as auth_router
from db import init_db, engine
from templating import templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth_router)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    public_paths = {"/login", "/signup"}
    if request.url.path in public_paths or request.url.path.startswith("/static/"):
        return await call_next(request)

    user_id = request.session.get("user_id")
    if not user_id:
        if request.headers.get("hx-request") == "true":
            return HTMLResponse(
                status_code=200, headers={"HX-Redirect": "/login"}
            )
        return RedirectResponse(url="/login", status_code=302)

    return await call_next(request)


app.add_middleware(
    SessionMiddleware,
    secret_key="change-this-secret-key-in-production",
)


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
