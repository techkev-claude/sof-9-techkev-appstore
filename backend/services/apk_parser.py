import os

from androguard.core.apk import APK
from PIL import Image

from config import settings


def parse_apk(apk_path: str) -> dict:
    """Liest Metadaten aus einer APK-Datei aus."""
    try:
        apk = APK(apk_path)
        package_name = apk.get_package()
        if not package_name:
            raise ValueError("Kein Package-Name gefunden")
        return {
            "package_name": package_name,
            "display_name": apk.get_app_name() or package_name,
            "version_name": apk.get_androidversion_name() or "1.0",
            "version_code": int(apk.get_androidversion_code() or 1),
            "min_sdk": int(apk.get_min_sdk_version() or 0) or None,
            "target_sdk": int(apk.get_target_sdk_version() or 0) or None,
        }
    except Exception as e:
        raise ValueError(f"APK konnte nicht gelesen werden: {e}")


def extract_icon(apk_path: str, package_name: str) -> str | None:
    """Extrahiert das App-Icon und speichert es als PNG (best-effort)."""
    tmp_path = None
    try:
        apk = APK(apk_path)
        icon_name = apk.get_app_icon()
        if not icon_name:
            return None

        icon_data = apk.get_file(icon_name)
        if not icon_data:
            return None

        icon_filename = f"{package_name}.png"
        icon_path = os.path.join(settings.ICON_STORAGE_PATH, icon_filename)
        tmp_path = icon_path + ".tmp"

        with open(tmp_path, "wb") as f:
            f.write(icon_data)

        with Image.open(tmp_path) as img:
            img = img.convert("RGBA")
            img = img.resize((192, 192), Image.LANCZOS)
            img.save(icon_path, "PNG")

        return icon_filename
    except Exception:
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
