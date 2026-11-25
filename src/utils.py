import sys
import os

def resource_path(relative_path: str) -> str:
    """Absolute path to resource, works for dev and for PyInstaller --onefile."""
    try:
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)
