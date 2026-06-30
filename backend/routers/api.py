from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import require_api_key
from database import get_db
from models.app import App, AppVersion
from schemas.app import (
    AppListResponse,
    AppResponse,
    AppVersionResponse,
    CategoryListResponse,
    InstallTrackRequest,
    UpdateCheckRequest,
    UpdateCheckResponse,
)

# Alle Endpunkte hier sind fuer die Android-App gedacht und durch den
# X-API-Key Header geschuetzt (siehe docs/ANDROID_INTEGRATION.md).
router = APIRouter(prefix="/api/v1", tags=["Android API"], dependencies=[Depends(require_api_key)])


def to_version_response(v: AppVersion) -> AppVersionResponse:
    return AppVersionResponse(
        id=v.id,
        version_name=v.version_name,
        version_code=v.version_code,
        changelog=v.changelog or "",
        apk_size_bytes=v.apk_size_bytes,
        min_sdk=v.min_sdk,
        target_sdk=v.target_sdk,
        download_count=v.download_count,
        install_count=v.install_count,
        uploaded_at=v.uploaded_at,
        download_url=f"/data/apks/{v.apk_filename}",
    )


def to_app_response(app: App, include_versions: bool = False) -> AppResponse:
    latest = app.latest_version
    return AppResponse(
        id=app.id,
        package_name=app.package_name,
        display_name=app.display_name,
        category=app.category,
        description=app.description,
        is_active=app.is_active,
        icon_url=f"/data/icons/{app.icon_filename}" if app.icon_filename else None,
        created_at=app.created_at,
        updated_at=app.updated_at,
        latest_version=to_version_response(latest) if latest else None,
        versions=[to_version_response(v) for v in app.versions] if include_versions else [],
    )


def _get_active_app(db: Session, package_name: str) -> App:
    app = db.query(App).filter(App.package_name == package_name, App.is_active == True).first()  # noqa: E712
    if not app:
        raise HTTPException(status_code=404, detail="App nicht gefunden")
    return app


@router.get("/apps", response_model=AppListResponse)
def list_apps(
    category: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(App).filter(App.is_active == True)  # noqa: E712
    if category:
        query = query.filter(App.category == category)
    if search:
        like = f"%{search}%"
        query = query.filter(App.display_name.ilike(like) | App.package_name.ilike(like))
    total = query.count()
    apps = query.order_by(App.updated_at.desc()).offset(skip).limit(limit).all()
    return AppListResponse(total=total, apps=[to_app_response(a) for a in apps])


@router.get("/apps/{package_name}", response_model=AppResponse)
def get_app(package_name: str, db: Session = Depends(get_db)):
    app = _get_active_app(db, package_name)
    return to_app_response(app, include_versions=True)


@router.get("/apps/{package_name}/versions", response_model=list[AppVersionResponse])
def list_versions(package_name: str, db: Session = Depends(get_db)):
    app = _get_active_app(db, package_name)
    return [to_version_response(v) for v in app.versions]


@router.post("/apps/check-update", response_model=UpdateCheckResponse)
def check_update(payload: UpdateCheckRequest, db: Session = Depends(get_db)):
    app = db.query(App).filter(
        App.package_name == payload.package_name, App.is_active == True  # noqa: E712
    ).first()
    latest = app.latest_version if app else None
    if not app or not latest:
        return UpdateCheckResponse(package_name=payload.package_name, update_available=False)

    update_available = latest.version_code > payload.version_code
    if not update_available:
        return UpdateCheckResponse(package_name=payload.package_name, update_available=False)

    return UpdateCheckResponse(
        package_name=payload.package_name,
        update_available=True,
        latest_version_name=latest.version_name,
        latest_version_code=latest.version_code,
        changelog=latest.changelog or "",
        download_url=f"/data/apks/{latest.apk_filename}",
        apk_size_bytes=latest.apk_size_bytes,
    )


def _resolve_version(app: App, version_code: Optional[int]) -> AppVersion:
    if version_code is None:
        version = app.latest_version
    else:
        version = next((v for v in app.versions if v.version_code == version_code), None)
    if not version:
        raise HTTPException(status_code=404, detail="Version nicht gefunden")
    return version


@router.post("/apps/{package_name}/download-count")
def increment_download(
    package_name: str,
    payload: InstallTrackRequest = InstallTrackRequest(),
    db: Session = Depends(get_db),
):
    """Wird von der Android-App nach einem erfolgreichen Download aufgerufen."""
    app = _get_active_app(db, package_name)
    version = _resolve_version(app, payload.version_code)
    version.download_count += 1
    db.commit()
    return {"status": "ok", "download_count": version.download_count}


@router.post("/apps/{package_name}/install-count")
def increment_install(
    package_name: str,
    payload: InstallTrackRequest = InstallTrackRequest(),
    db: Session = Depends(get_db),
):
    """Wird von der Android-App nach erfolgreicher Installation aufgerufen
    (Installationstracking)."""
    app = _get_active_app(db, package_name)
    version = _resolve_version(app, payload.version_code)
    version.install_count += 1
    db.commit()
    return {"status": "ok", "install_count": version.install_count}


@router.get("/categories", response_model=CategoryListResponse)
def list_categories(db: Session = Depends(get_db)):
    result = db.query(App.category).filter(App.is_active == True).distinct().all()  # noqa: E712
    return CategoryListResponse(categories=[r[0] for r in result if r[0]])
