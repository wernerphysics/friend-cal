import asyncio
import os
from datetime import date, datetime, timezone
from typing import Any

import caldav
import icalendar as ical


_URL = os.getenv("NEXTCLOUD_URL", "")
_USER = os.getenv("NEXTCLOUD_USER", "")
_PASSWORD = os.getenv("NEXTCLOUD_PASSWORD", "")

if not _URL or not _USER or not _PASSWORD:
    raise RuntimeError(
        "NEXTCLOUD_URL, NEXTCLOUD_USER, and NEXTCLOUD_PASSWORD must be set "
        "(via .env file or environment variables)"
    )


def _calendar() -> caldav.Calendar:
    client = caldav.DAVClient(url=_URL, username=_USER, password=_PASSWORD)
    return caldav.Calendar(client=client, url=_URL)


def _event_to_ical(event: dict[str, Any]) -> str:
    cal = ical.Calendar()
    cal.add("prodid", "-//friend-cal//EN")
    cal.add("version", "2.0")

    vevent = ical.Event()
    vevent.add("uid", event["uid"])
    vevent.add("summary", event["title"])

    dt = event["date"]
    if event.get("time"):
        parts = event["time"].split(":")
        dtstart = datetime.combine(dt, datetime.min.time().replace(
            hour=int(parts[0]), minute=int(parts[1])
        ))
        vevent.add("dtstart", dtstart)
        if event.get("end_time"):
            end_parts = event["end_time"].split(":")
            dtend = datetime.combine(dt, datetime.min.time().replace(
                hour=int(end_parts[0]), minute=int(end_parts[1])
            ))
            vevent.add("dtend", dtend)
    else:
        vevent.add("dtstart", dt)

    if event.get("description"):
        vevent.add("description", event["description"])
    if event.get("location"):
        vevent.add("location", event["location"])
    if event.get("color"):
        vevent.add("x-apple-color", event["color"])
    if event.get("created_by"):
        vevent.add("x-friendcal-created-by", str(event["created_by"]))

    vevent.add("dtstamp", datetime.now(timezone.utc))

    cal.add_component(vevent)
    return cal.to_ical().decode("utf-8")


def _ical_to_dict(data: str) -> dict[str, Any] | None:
    cal = ical.Calendar.from_ical(data)
    for component in cal.walk():
        if component.name == "VEVENT":
            uid = str(component.get("uid", ""))
            summary = str(component.get("summary", ""))
            dtstart = component.get("dtstart")
            if not uid or not summary or dtstart is None:
                return None

            raw_date = dtstart.dt
            if isinstance(raw_date, datetime):
                event_date = raw_date.date()
                time_str = raw_date.strftime("%H:%M")
            else:
                event_date = raw_date
                time_str = None

            end = component.get("dtend")
            end_time_str = None
            if end:
                end_dt = end.dt
                if isinstance(end_dt, datetime):
                    end_time_str = end_dt.strftime("%H:%M")

            return {
                "uid": uid,
                "id": uid,
                "title": summary,
                "date": event_date,
                "time": time_str,
                "end_time": end_time_str,
                "description": str(component.get("description", "")),
                "location": str(component.get("location", "")),
                "color": str(component.get("x-apple-color", "")),
                "created_by": str(component.get("x-friendcal-created-by", "")),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
    return None


async def create_event(event: dict[str, Any]) -> dict[str, Any]:
    ical_data = _event_to_ical(event)
    await asyncio.to_thread(
        lambda: _calendar().save_event(ical_data)
    )
    return event


async def get_month_events(year: int, month: int) -> list[dict[str, Any]]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    cal = await asyncio.to_thread(_calendar)
    results = await asyncio.to_thread(cal.date_search, start, end)
    events = []
    for r in results:
        data = r.data
        ev = _ical_to_dict(data)
        if ev:
            events.append(ev)
    return events


async def _find_calendar_objects_by_uid(uid: str, cal) -> list:
    """Search a broad date range and return objects matching the given UID."""
    start = date(2000, 1, 1)
    end = date(2100, 1, 1)
    results = await asyncio.to_thread(cal.date_search, start, end)
    found = []
    for r in results:
        ev = _ical_to_dict(r.data)
        if ev and ev["uid"] == uid:
            found.append(r)
    return found


async def get_event(uid: str) -> dict[str, Any] | None:
    cal = await asyncio.to_thread(_calendar)
    objects = await _find_calendar_objects_by_uid(uid, cal)
    if objects:
        return _ical_to_dict(objects[0].data)
    return None


async def update_event(uid: str, event: dict[str, Any]) -> dict[str, Any] | None:
    cal = await asyncio.to_thread(_calendar)
    objects = await _find_calendar_objects_by_uid(uid, cal)
    for r in objects:
        await asyncio.to_thread(r.delete)
    event["uid"] = uid
    return await create_event(event)


async def delete_event(uid: str) -> None:
    cal = await asyncio.to_thread(_calendar)
    objects = await _find_calendar_objects_by_uid(uid, cal)
    for r in objects:
        await asyncio.to_thread(r.delete)
