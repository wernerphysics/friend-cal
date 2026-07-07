import os
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path


def _load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


_load_env()

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from auth import router as auth_router
from calendar_service import calendar_context
from db import init_db, engine
from events import router as events_router
from templating import templates
from web import redirect


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth_router)
app.include_router(events_router)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    public_paths = {"/login", "/signup"}
    if request.url.path in public_paths or request.url.path.startswith("/static/"):
        return await call_next(request)

    user_id = request.session.get("user_id")
    if not user_id:
        return redirect(request, "/login")

    return await call_next(request)


app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "change-this-secret-key-in-production"),
)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    today = date.today()
    ctx = await calendar_context(today.year, today.month, request)
    ctx["user_name"] = request.session.get("user_name", "")
    return templates.TemplateResponse(request, "index.html", ctx)


@app.get("/calendar", response_class=HTMLResponse)
async def calendar_month(
    request: Request,
    year: int,
    month: int,
):
    if month < 1 or month > 12:
        month = date.today().month
    ctx = await calendar_context(year, month, request)
    return templates.TemplateResponse(request, "calendar.html", ctx)


def run():
    import uvicorn
    uvicorn.run("main:app")
