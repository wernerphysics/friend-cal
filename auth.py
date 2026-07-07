from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
import bcrypt

from db import get_session
from models import User, InviteCode
from templating import templates
from datetime import datetime, timezone

router = APIRouter()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash.encode())


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")


@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, session: AsyncSession = Depends(get_session)):
    form = await request.form()
    name = form.get("name")
    password = form.get("password")

    result = await session.execute(select(User).where(User.name == name))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request, "auth/login.html", {"error": "Invalid name or password"}
        )

    request.session["user_id"] = user.id
    request.session["user_name"] = user.name

    if request.headers.get("hx-request") == "true":
        return HTMLResponse(status_code=200, headers={"HX-Redirect": "/"})
    return RedirectResponse(url="/", status_code=302)


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(request, "auth/signup.html")


@router.post("/signup", response_class=HTMLResponse)
async def signup(request: Request, session: AsyncSession = Depends(get_session)):
    form = await request.form()
    name = form.get("name")
    password = form.get("password")
    code = form.get("invite_code")

    if not name or not password or not code:
        return templates.TemplateResponse(
            request, "auth/signup.html", {"error": "All fields are required"}
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            request, "auth/signup.html", {"error": "Password must be at least 6 characters"}
        )

    result = await session.execute(select(User).where(User.name == name))
    if result.scalar_one_or_none():
        return templates.TemplateResponse(
            request, "auth/signup.html", {"error": "Name already taken"}
        )

    result = await session.execute(
        select(InviteCode).where(InviteCode.code == code, InviteCode.used_by == None)
    )
    invite = result.scalar_one_or_none()
    if not invite:
        return templates.TemplateResponse(
            request, "auth/signup.html", {"error": "Invalid or already used invite code"}
        )

    user = User(name=name, password_hash=hash_password(password))
    session.add(user)
    await session.flush()

    user_id = user.id
    user_name = user.name

    invite.used_by = user_id
    invite.used_at = datetime.now(timezone.utc)
    session.add(invite)
    await session.commit()

    request.session["user_id"] = user_id
    request.session["user_name"] = user_name

    if request.headers.get("hx-request") == "true":
        return HTMLResponse(status_code=200, headers={"HX-Redirect": "/"})
    return RedirectResponse(url="/", status_code=302)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    if request.headers.get("hx-request") == "true":
        return HTMLResponse(status_code=200, headers={"HX-Redirect": "/login"})
    return RedirectResponse(url="/login", status_code=302)
