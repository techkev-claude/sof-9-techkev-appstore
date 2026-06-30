from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AppVersionResponse(BaseModel):
    id: int
    version_name: str
    version_code: int
    changelog: str = ""
    apk_size_bytes: int
    min_sdk: Optional[int] = None
    target_sdk: Optional[int] = None
    download_count: int
    install_count: int
    uploaded_at: datetime
    download_url: str

    class Config:
        from_attributes = True


class AppResponse(BaseModel):
    id: int
    package_name: str
    display_name: str
    category: Optional[str] = "Sonstige"
    description: Optional[str] = ""
    is_active: bool
    icon_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    latest_version: Optional[AppVersionResponse] = None
    versions: list[AppVersionResponse] = []

    class Config:
        from_attributes = True


class AppListResponse(BaseModel):
    total: int
    apps: list[AppResponse]


class CategoryListResponse(BaseModel):
    categories: list[str]


class UpdateCheckRequest(BaseModel):
    package_name: str
    version_code: int


class UpdateCheckResponse(BaseModel):
    package_name: str
    update_available: bool
    latest_version_name: Optional[str] = None
    latest_version_code: Optional[int] = None
    changelog: Optional[str] = None
    download_url: Optional[str] = None
    apk_size_bytes: Optional[int] = None


class InstallTrackRequest(BaseModel):
    version_code: Optional[int] = None
