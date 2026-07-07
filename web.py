from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse


def is_htmx(request: Request) -> bool:
    return request.headers.get("hx-request") == "true"


def redirect(request: Request, url: str):
    """Redirect that works for both htmx and full-page requests.

    htmx swallows normal 3xx redirects, so we signal the client-side
    redirect via the HX-Redirect header instead.
    """
    if is_htmx(request):
        return HTMLResponse(status_code=200, headers={"HX-Redirect": url})
    return RedirectResponse(url=url, status_code=302)
