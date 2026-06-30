from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import (
    SESSION_COOKIE_NAME,
    create_session_token,
    get_current_user,
    verify_credentials,
)
from config import settings

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/"):
    if get_current_user(request):
        return RedirectResponse(url=next or "/", status_code=303)
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": None, "next": next}
    )


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form(default="/"),
):
    if not verify_credentials(username, password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Benutzername oder Passwort ist falsch.", "next": next},
            status_code=401,
        )

    token = create_session_token(username)
    response = RedirectResponse(url=next or "/", status_code=303)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        max_age=settings.SESSION_MAX_AGE_SECONDS,
    )
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response
