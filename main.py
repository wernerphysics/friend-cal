from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.middleware.sessions import SessionMiddleware

from auth import router as auth_router
from calendar_service import calendar_context
from db import get_session, init_db, engine
from events import router as events_router
from templating import templates


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


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, session=Depends(get_session)):
    today = date.today()
    ctx = await calendar_context(today.year, today.month, request, session)
    ctx["user_name"] = request.session.get("user_name", "")
    return templates.TemplateResponse(request, "index.html", ctx)


@app.get("/calendar", response_class=HTMLResponse)
async def calendar_month(
    request: Request,
    year: int,
    month: int,
    session=Depends(get_session),
):
    if month < 1 or month > 12:
        month = date.today().month
    ctx = await calendar_context(year, month, request, session)
    return templates.TemplateResponse(request, "calendar.html", ctx)


def run():
    import uvicorn
    uvicorn.run("main:app")
