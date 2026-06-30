import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth import require_login
from config import settings
from database import get_db
from models.app import App, AppVersion
from services.apk_parser import extract_icon, parse_apk
from services.storage import delete_apk, delete_icon, save_apk

router = APIRouter(tags=["Web Interface"], dependencies=[Depends(require_login)])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    apps = (
        db.query(App)
        .filter(App.is_active == True)  # noqa: E712
        .order_by(App.updated_at.desc())
        .all()
    )
    return templates.TemplateResponse("index.html", {"request": request, "apps": apps})


@router.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request, "error": None})


@router.post("/upload")
async def upload_apk(
    request: Request,
    file: UploadFile = File(...),
    category: str = Form(default="Sonstige"),
    description: str = Form(default=""),
    changelog: str = Form(default=""),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".apk"):
        return templates.TemplateResponse(
            "upload.html",
            {"request": request, "error": "Nur .apk Dateien sind erlaubt."},
            status_code=400,
        )

    apk_filename = f"{uuid.uuid4().hex}.apk"
    apk_path = os.path.join(settings.APK_STORAGE_PATH, apk_filename)

    try:
        size = await save_apk(file, apk_filename)
        meta = parse_apk(apk_path)
    except ValueError as e:
        if os.path.exists(apk_path):
            os.remove(apk_path)
        return templates.TemplateResponse(
            "upload.html", {"request": request, "error": str(e)}, status_code=400
        )

    app = db.query(App).filter(App.package_name == meta["package_name"]).first()

    if app and any(v.version_code == meta["version_code"] for v in app.versions):
        delete_apk(apk_filename)
        return templates.TemplateResponse(
            "upload.html",
            {
                "request": request,
                "error": (
                    f"Version {meta['version_code']} ({meta['version_name']}) von "
                    f"{meta['package_name']} wurde bereits hochgeladen."
                ),
            },
            status_code=400,
        )

    icon_filename = extract_icon(apk_path, meta["package_name"])

    if not app:
        app = App(
            package_name=meta["package_name"],
            display_name=meta["display_name"],
            category=category,
            description=description,
            icon_filename=icon_filename,
        )
        db.add(app)
    else:
        app.display_name = meta["display_name"]
        app.category = category
        app.description = description
        if icon_filename:
            delete_icon(app.icon_filename)
            app.icon_filename = icon_filename
    db.flush()

    version = AppVersion(
        app_id=app.id,
        version_name=meta["version_name"],
        version_code=meta["version_code"],
        changelog=changelog,
        apk_filename=apk_filename,
        apk_size_bytes=size,
        min_sdk=meta["min_sdk"],
        target_sdk=meta["target_sdk"],
    )
    db.add(version)
    db.commit()

    return RedirectResponse(url=f"/apps/{app.id}", status_code=303)


@router.get("/apps/{app_id}", response_class=HTMLResponse)
def app_detail(app_id: int, request: Request, db: Session = Depends(get_db)):
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("app_detail.html", {"request": request, "app": app})


@router.post("/apps/{app_id}/delete")
def delete_app(app_id: int, db: Session = Depends(get_db)):
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404)
    for version in app.versions:
        delete_apk(version.apk_filename)
    delete_icon(app.icon_filename)
    db.delete(app)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@router.post("/apps/{app_id}/versions/{version_id}/delete")
def delete_version(app_id: int, version_id: int, db: Session = Depends(get_db)):
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404)
    version = next((v for v in app.versions if v.id == version_id), None)
    if not version:
        raise HTTPException(status_code=404)

    if len(app.versions) <= 1:
        raise HTTPException(
            status_code=400,
            detail="Letzte verbleibende Version kann nicht geloescht werden. "
            "Stattdessen die gesamte App loeschen.",
        )

    delete_apk(version.apk_filename)
    db.delete(version)
    db.commit()
    return RedirectResponse(url=f"/apps/{app_id}", status_code=303)
