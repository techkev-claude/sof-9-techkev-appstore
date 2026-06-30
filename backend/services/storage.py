import os

import aiofiles
from fastapi import UploadFile

from config import settings


async def save_apk(file: UploadFile, filename: str) -> int:
    """Speichert eine APK-Datei als Stream und gibt die Dateigroesse in Bytes
    zurueck. Bricht ab und loescht die Datei, falls das Groessenlimit
    ueberschritten wird."""
    path = os.path.join(settings.APK_STORAGE_PATH, filename)
    size = 0
    max_bytes = settings.APK_MAX_SIZE_MB * 1024 * 1024
    too_large = False
    async with aiofiles.open(path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                too_large = True
                break
            await f.write(chunk)
    if too_large:
        os.remove(path)
        raise ValueError(f"APK ueberschreitet {settings.APK_MAX_SIZE_MB} MB Limit")
    return size


def delete_apk(filename: str) -> None:
    if not filename:
        return
    path = os.path.join(settings.APK_STORAGE_PATH, filename)
    if os.path.exists(path):
        os.remove(path)


def delete_icon(filename: str | None) -> None:
    if not filename:
        return
    path = os.path.join(settings.ICON_STORAGE_PATH, filename)
    if os.path.exists(path):
        os.remove(path)
