import asyncio
import secrets

from db import init_db, engine
from models import InviteCode
from sqlmodel.ext.asyncio.session import AsyncSession


async def generate():
    await init_db()
    async with AsyncSession(engine) as session:
        code = secrets.token_urlsafe(12)
        invite = InviteCode(code=code)
        session.add(invite)
        await session.commit()
        print(f"Invite code: {code}")
    await engine.dispose()


def main():
    asyncio.run(generate())
