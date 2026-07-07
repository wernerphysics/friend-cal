# friend-cal conventions

## Tech stack
- Python 3.12+, FastAPI, Jinja2 templates, htmx 1.9.x
- All interactivity via htmx; minimal vanilla JS in static/calendar.js
- CSS in static/style.css
- uv for dependency management (pyproject.toml)

## Project structure
```
main.py              # FastAPI app, routes, calendar logic
templates/           # Jinja2 templates
static/              # JS, CSS
```

## Calendar navigation
- Prev/Next buttons in calendar.html use htmx with hx-swap="innerHTML"
- Target is always #calendar-container in index.html
- AfterSwap re-renders events via calendar.js

## Commands
```bash
uv sync              # install deps
uv run friend-cal    # start dev server
```
