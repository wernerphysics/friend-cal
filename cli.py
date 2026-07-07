import asyncio
import secrets
import sys
import uuid
from datetime import date

from db import init_db, engine, get_session
from models import InviteCode, User
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

import nextcloud


async def generate():
    await init_db()
    async with AsyncSession(engine) as session:
        code = secrets.token_urlsafe(12)
        invite = InviteCode(code=code)
        session.add(invite)
        await session.commit()
        print(f"Invite code: {code}")
    await engine.dispose()


async def seed():
    await init_db()

    async with AsyncSession(engine) as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        if not users:
            print("No users found. Create a user first via signup.")
            return

        user = users[0]
        today = date.today()
        month = today.month
        year = today.year

        events_data = [
            ("Dinner at Sushi Spot", 10, "19:00", None, "Birthday dinner for Mike", "#ef4444"),
            ("Movie Night", 12, "20:00", None, "New Marvel movie at the IMAX", "#8b5cf6"),
            ("Hiking Trip", 15, "08:00", None, "Trail run at Mt. Tam", "#10b981"),
            ("Game Night", 20, "18:00", None, "Board games at Alex's place", "#f59e0b"),
            ("Farmers Market", 25, "09:00", None, "Weekly farmers market run", "#3b82f6"),
            ("Brunch", 5, "10:30", None, "Bottomless mimosas at Cafe Flora", "#ec4899"),
            ("Tennis Match", 8, "07:00", None, "Doubles match at the club", "#10b981"),
        ]

        for title, day, time, end_time, desc, color in events_data:
            try:
                event_date = date(year, month, day)
            except ValueError:
                event_date = date(year, month, 1)

            ev = {
                "uid": str(uuid.uuid4()),
                "title": title,
                "date": event_date,
                "time": time,
                "end_time": end_time,
                "description": desc,
                "color": color,
                "created_by": str(user.id),
            }
            await nextcloud.create_event(ev)

        user_name = user.name
        print(f"Seeded {len(events_data)} events for {user_name} in {today.strftime('%B %Y')}")
    await engine.dispose()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "seed":
        asyncio.run(seed())
    else:
        asyncio.run(generate())
