"""Synthetic source-review fixture; it is not an application to run."""
from pathlib import Path

from fastapi.responses import FileResponse, JSONResponse


PUBLIC_DIR = Path(__file__).parent / "public"


def unsafe_asset(request_path: str):
    """Vulnerable control: a string prefix does not remove `..` segments."""
    candidate = PUBLIC_DIR / request_path
    if candidate.is_file() and str(candidate).startswith(str(PUBLIC_DIR)):
        return FileResponse(candidate)
    return JSONResponse({"detail": "not found"}, status_code=404)


def safe_asset(request_path: str):
    """Negative control: the final path must remain below the public root."""
    root = PUBLIC_DIR.resolve()
    candidate = (root / request_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return JSONResponse({"detail": "not found"}, status_code=404)
    if not candidate.is_file():
        return JSONResponse({"detail": "not found"}, status_code=404)
    return FileResponse(candidate)
