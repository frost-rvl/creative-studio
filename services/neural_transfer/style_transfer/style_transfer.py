"""
style_transfer.py
-----------------
Neural Style Transfer engine using TensorFlow Hub pre-trained models.
Supports Van Gogh, Munch, and Picasso style presets.

Usage (standalone):
    from style_transfer import StyleTransferEngine
    engine = StyleTransferEngine()
    result_path = engine.transfer(content_path="photo.jpg", painter="vangogh")
"""

import sys
import types

# ── Patch pkg_resources ─────────────────────────────────────────────────────
if 'pkg_resources' not in sys.modules:
    pkg_resources = types.ModuleType('pkg_resources')
    pkg_resources.parse_version = lambda x: x
    sys.modules['pkg_resources'] = pkg_resources

import os
import time
import logging
import numpy as np
from pathlib import Path
from typing import Literal, Optional

import tensorflow as tf
import tensorflow_hub as hub
from PIL import Image

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Types
# ──────────────────────────────────────────────
PainterName = Literal["vangogh", "munch", "picasso"]

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
STYLE_IMG_DIR   = BASE_DIR / "static" / "style_images"
OUTPUT_DIR      = BASE_DIR / "static" / "outputs"
UPLOAD_DIR      = BASE_DIR / "static" / "uploads"

for _d in [STYLE_IMG_DIR, OUTPUT_DIR, UPLOAD_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# Painter → style image mapping
# ──────────────────────────────────────────────
PAINTER_STYLES: dict[PainterName, str] = {
    "vangogh" : str(STYLE_IMG_DIR / "vangogh_starry_night.jpg"),
    "munch"   : str(STYLE_IMG_DIR / "munch_scream.jpg"),
    "picasso" : str(STYLE_IMG_DIR / "picasso_weeping_woman.jpg"),
}

PAINTER_DISPLAY_NAMES: dict[PainterName, str] = {
    "vangogh" : "Van Gogh — The Starry Night",
    "munch"   : "Munch — The Scream",
    "picasso" : "Picasso — Weeping Woman",
}

# ──────────────────────────────────────────────
# TF Hub model URL
# ──────────────────────────────────────────────
HUB_MODEL_URL = (
    "https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2"
)


# ──────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ──────────────────────────────────────────────────────────────────────────────

def _load_image(path: str, max_dim: int = 512) -> tf.Tensor:
    """
    Load an image from disk, resize so the longest edge ≤ max_dim,
    and return a float32 tensor of shape [1, H, W, 3] in [0, 1].
    """
    img = tf.io.read_file(path)
    img = tf.image.decode_image(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)   # → [0, 1]

    # Resize preserving aspect ratio
    shape  = tf.cast(tf.shape(img)[:-1], tf.float32)
    scale  = max_dim / tf.reduce_max(shape)
    new_h  = tf.cast(shape[0] * scale, tf.int32)
    new_w  = tf.cast(shape[1] * scale, tf.int32)
    img    = tf.image.resize(img, [new_h, new_w])

    return img[tf.newaxis]   # [1, H, W, 3]


def _tensor_to_pil(tensor: tf.Tensor) -> Image.Image:
    """Convert a [1, H, W, 3] float32 tensor → PIL Image (RGB)."""
    arr = np.squeeze(tensor.numpy())          # [H, W, 3]
    arr = np.clip(arr, 0.0, 1.0)
    arr = (arr * 255).astype(np.uint8)
    return Image.fromarray(arr)


# ──────────────────────────────────────────────────────────────────────────────
# Main engine
# ──────────────────────────────────────────────────────────────────────────────

class StyleTransferEngine:
    """
    Wraps the TF-Hub arbitrary image stylization model.

    The model is loaded **once** on first instantiation and cached as a
    class-level attribute so that repeated calls don't reload weights.
    """

    _hub_model = None   # shared across instances

    def __init__(
        self,
        content_max_dim: int = 512,
        style_max_dim:   int = 256,
        output_quality:  int = 92,
    ):
        """
        Parameters
        ----------
        content_max_dim : int
            Resize the content image so its longest side ≤ this value.
        style_max_dim : int
            Resize the style image so its longest side ≤ this value.
        output_quality : int
            JPEG quality for saved outputs (1–95).
        """
        self.content_max_dim = content_max_dim
        self.style_max_dim   = style_max_dim
        self.output_quality  = output_quality
        self._load_model()

    # ── model loading ────────────────────────────────────────────────────────

    def _load_model(self) -> None:
        if StyleTransferEngine._hub_model is None:
            logger.info("Loading TF Hub style transfer model …")
            StyleTransferEngine._hub_model = hub.load(HUB_MODEL_URL)
            logger.info("Model loaded successfully.")

    @property
    def model(self):
        return StyleTransferEngine._hub_model

    # ── public API ───────────────────────────────────────────────────────────

    def transfer(
        self,
        content_path: str,
        painter: PainterName,
        output_filename: Optional[str] = None,
    ) -> dict:
        """
        Apply neural style transfer.

        Parameters
        ----------
        content_path : str
            Absolute or relative path to the user's content image.
        painter : PainterName
            One of "vangogh", "munch", "picasso".
        output_filename : str | None
            Custom filename for the output image (saved in OUTPUT_DIR).
            Defaults to "<timestamp>_<painter>.jpg".

        Returns
        -------
        dict with keys:
            output_path  : str   — absolute path to the styled image
            filename     : str   — just the filename
            painter      : str   — painter key
            display_name : str   — human-readable painter name
            elapsed_sec  : float — processing time
        """
        if painter not in PAINTER_STYLES:
            raise ValueError(
                f"Unknown painter '{painter}'. "
                f"Choose from: {list(PAINTER_STYLES.keys())}"
            )

        style_path = PAINTER_STYLES[painter]
        if not os.path.isfile(style_path):
            raise FileNotFoundError(
                f"Style image not found at '{style_path}'. "
                f"Run `python download_styles.py` to fetch reference images."
            )

        if not os.path.isfile(content_path):
            raise FileNotFoundError(f"Content image not found: '{content_path}'")

        # ── load tensors ─────────────────────────────────────────────────────
        logger.info(f"Loading content image from: {content_path}")
        content_tensor = _load_image(content_path, self.content_max_dim)

        logger.info(f"Loading style image for painter: {painter}")
        style_tensor = _load_image(style_path, self.style_max_dim)

        # ── run inference ────────────────────────────────────────────────────
        logger.info("Running style transfer …")
        t0 = time.perf_counter()
        stylized = self.model(
            tf.constant(content_tensor),
            tf.constant(style_tensor)
        )[0]                          # model returns a tuple; first element is image
        elapsed = time.perf_counter() - t0
        logger.info(f"Style transfer complete in {elapsed:.2f}s")

        # ── save output ──────────────────────────────────────────────────────
        if output_filename is None:
            ts = int(time.time())
            output_filename = f"{ts}_{painter}.jpg"

        output_path = str(OUTPUT_DIR / output_filename)
        pil_image   = _tensor_to_pil(stylized)
        pil_image.save(output_path, format="JPEG", quality=self.output_quality)
        logger.info(f"Styled image saved to: {output_path}")

        return {
            "output_path"  : output_path,
            "filename"     : output_filename,
            "painter"      : painter,
            "display_name" : PAINTER_DISPLAY_NAMES[painter],
            "elapsed_sec"  : round(elapsed, 2),
        }

    def transfer_with_custom_style(
        self,
        content_path: str,
        style_path:   str,
        output_filename: Optional[str] = None,
    ) -> dict:
        """
        Apply style from any arbitrary style image (not limited to presets).

        Parameters
        ----------
        content_path : str
            Path to the content image.
        style_path : str
            Path to a custom style image.
        output_filename : str | None
            Output filename; defaults to "<timestamp>_custom.jpg".

        Returns
        -------
        Same dict structure as `transfer()`, painter set to "custom".
        """
        for p, label in [(content_path, "Content"), (style_path, "Style")]:
            if not os.path.isfile(p):
                raise FileNotFoundError(f"{label} image not found: '{p}'")

        content_tensor = _load_image(content_path, self.content_max_dim)
        style_tensor   = _load_image(style_path,   self.style_max_dim)

        logger.info("Running style transfer with custom style image …")
        t0 = time.perf_counter()
        stylized = self.model(
            tf.constant(content_tensor),
            tf.constant(style_tensor)
        )[0]
        elapsed = time.perf_counter() - t0

        if output_filename is None:
            output_filename = f"{int(time.time())}_custom.jpg"

        output_path = str(OUTPUT_DIR / output_filename)
        _tensor_to_pil(stylized).save(
            output_path, format="JPEG", quality=self.output_quality
        )

        return {
            "output_path"  : output_path,
            "filename"     : output_filename,
            "painter"      : "custom",
            "display_name" : "Custom Style",
            "elapsed_sec"  : round(elapsed, 2),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Quick smoke-test  (python style_transfer.py)
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python style_transfer.py <content_image> <painter>")
        print("       painter ∈ {vangogh, munch, picasso}")
        sys.exit(1)

    engine = StyleTransferEngine()
    result = engine.transfer(
        content_path=sys.argv[1],
        painter=sys.argv[2],
    )
    print(f"\n✅ Done in {result['elapsed_sec']}s")
    print(f"   Painter : {result['display_name']}")
    print(f"   Output  : {result['output_path']}")