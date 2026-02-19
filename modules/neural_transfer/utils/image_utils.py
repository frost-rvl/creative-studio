"""
utils/image_utils.py
--------------------
Image validation, preprocessing helpers, and file management utilities
for the style transfer pipeline.
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS  = {"jpg", "jpeg", "png", "webp", "bmp"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024          # 10 MB
MIN_DIMENSION       = 64                         # pixels
MAX_DIMENSION       = 4096                       # pixels


# ── Validation ────────────────────────────────────────────────────────────────

class ImageValidationError(ValueError):
    """Raised when an uploaded image fails validation."""


def allowed_extension(filename: str) -> bool:
    """Return True if the file extension is in the allowed set."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def validate_image_file(filepath: str) -> Tuple[int, int]:
    """
    Validate an image file for size, format, and dimensions.

    Parameters
    ----------
    filepath : str
        Path to the image file on disk.

    Returns
    -------
    (width, height) tuple of the image.

    Raises
    ------
    ImageValidationError
        If the file fails any validation check.
    """
    path = Path(filepath)

    # 1. File exists
    if not path.is_file():
        raise ImageValidationError(f"File not found: {filepath}")

    # 2. File size
    size_bytes = path.stat().st_size
    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise ImageValidationError(
            f"File too large: {size_bytes / 1e6:.1f} MB "
            f"(max {MAX_FILE_SIZE_BYTES / 1e6:.0f} MB)"
        )

    # 3. Actually an image
    try:
        with Image.open(filepath) as img:
            img.verify()          # checks file integrity without full decode
    except (UnidentifiedImageError, Exception) as exc:
        raise ImageValidationError(f"Invalid or corrupt image file: {exc}")

    # 4. Dimensions (re-open after verify)
    with Image.open(filepath) as img:
        w, h = img.size

    if w < MIN_DIMENSION or h < MIN_DIMENSION:
        raise ImageValidationError(
            f"Image too small: {w}×{h} px (min {MIN_DIMENSION} px per side)"
        )
    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        raise ImageValidationError(
            f"Image too large: {w}×{h} px (max {MAX_DIMENSION} px per side)"
        )

    return (w, h)


# ── Preprocessing ─────────────────────────────────────────────────────────────

def preprocess_image(
    src_path: str,
    dest_path: Optional[str] = None,
    max_dim: int = 1024,
    convert_to_rgb: bool = True,
) -> str:
    """
    Resize and normalise an image before feeding it to the model.

    - Converts RGBA / palette images to RGB.
    - Resizes so that the longest side ≤ max_dim (aspect preserved).
    - Saves as JPEG to dest_path (or overwrites src_path if dest_path=None).

    Returns the path to the processed file.
    """
    with Image.open(src_path) as img:
        if convert_to_rgb and img.mode != "RGB":
            img = img.convert("RGB")

        # Resize
        w, h   = img.size
        scale  = min(max_dim / max(w, h), 1.0)   # never upscale
        new_w  = max(1, int(w * scale))
        new_h  = max(1, int(h * scale))

        if scale < 1.0:
            img = img.resize((new_w, new_h), Image.LANCZOS)
            logger.debug(f"Resized {w}×{h} → {new_w}×{new_h}")

        out_path = dest_path or src_path
        img.save(out_path, format="JPEG", quality=90)

    return out_path


def secure_save_upload(
    file_storage,          # werkzeug FileStorage object
    upload_dir: str,
    max_dim: int = 1024,
) -> str:
    """
    Securely save a werkzeug FileStorage upload to upload_dir.

    1. Generates a UUID-based filename (prevents path traversal).
    2. Saves the raw upload.
    3. Validates it is a real image.
    4. Preprocesses (resize + RGB normalise).

    Parameters
    ----------
    file_storage : werkzeug.datastructures.FileStorage
        The uploaded file from request.files.
    upload_dir : str
        Directory to save the file into.
    max_dim : int
        Max dimension after preprocessing.

    Returns
    -------
    str — absolute path to the saved, preprocessed image.

    Raises
    ------
    ImageValidationError
        If the file is not a valid image or fails size checks.
    """
    original_name = file_storage.filename or ""
    if not allowed_extension(original_name):
        raise ImageValidationError(
            f"File type not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    ext      = original_name.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest     = os.path.join(upload_dir, filename)

    file_storage.save(dest)

    # Validate
    validate_image_file(dest)

    # Preprocess (convert + resize)
    preprocess_image(dest, max_dim=max_dim)

    return dest


# ── Output helpers ─────────────────────────────────────────────────────────────

def cleanup_old_outputs(output_dir: str, keep_latest: int = 100) -> int:
    """
    Delete old output files beyond the `keep_latest` most recent ones.

    Returns the number of files deleted.
    """
    files = sorted(
        Path(output_dir).glob("*.jpg"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    to_delete = files[keep_latest:]
    for f in to_delete:
        f.unlink(missing_ok=True)
    return len(to_delete)