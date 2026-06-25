import base64
import io

import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageOps


def pil_to_b64(img: Image.Image, fmt="PNG") -> str:
    buffer = io.BytesIO()
    img.save(buffer, format=fmt)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def load_image(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def apply_grayscale(img: Image.Image) -> Image.Image:
    return ImageOps.grayscale(img).convert("RGB")


def apply_sepia(img: Image.Image) -> Image.Image:
    arr = np.array(img, dtype=np.float64)

    r = arr[:, :, 0] * 0.393 + arr[:, :, 1] * 0.769 + arr[:, :, 2] * 0.189
    g = arr[:, :, 0] * 0.349 + arr[:, :, 1] * 0.686 + arr[:, :, 2] * 0.168
    b = arr[:, :, 0] * 0.272 + arr[:, :, 1] * 0.534 + arr[:, :, 2] * 0.131

    sepia = np.stack([r, g, b], axis=2).clip(0, 255).astype(np.uint8)
    return Image.fromarray(sepia)


def apply_invert(img: Image.Image) -> Image.Image:
    return ImageOps.invert(img)


def apply_neon(img: Image.Image) -> Image.Image:
    arr = np.array(img)
    edges = cv2.Canny(arr, 80, 180)

    neon = np.zeros_like(arr)
    neon[:, :, 1] = edges
    neon[:, :, 2] = edges

    blurred = cv2.GaussianBlur(neon, (7, 7), 0)
    result = cv2.addWeighted(arr // 3, 1, blurred, 2, 0)

    return Image.fromarray(result.clip(0, 255).astype(np.uint8))


def apply_glitch(img: Image.Image) -> Image.Image:
    arr = np.array(img)
    rng = np.random.default_rng(42)

    for _ in range(18):
        row = rng.integers(0, arr.shape[0])
        shift = rng.integers(-40, 40)
        arr[row] = np.roll(arr[row], shift, axis=0)

    arr[:, :, 0] = np.roll(arr[:, :, 0], 8, axis=1)
    arr[:, :, 2] = np.roll(arr[:, :, 2], -8, axis=1)

    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))


def apply_pixelate(img: Image.Image, block: int = 14) -> Image.Image:
    w, h = img.size
    small = img.resize((max(1, w // block), max(1, h // block)), Image.NEAREST)
    return small.resize((w, h), Image.NEAREST)


def apply_blur(img: Image.Image, radius: int = 6) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def apply_watercolor(img: Image.Image) -> Image.Image:
    arr = np.array(img)

    for _ in range(3):
        arr = cv2.bilateralFilter(arr, 9, 75, 75)

    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    edges = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        7,
        2
    )

    edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    result = cv2.bitwise_and(arr, edges_rgb)

    return Image.fromarray(result)


def apply_mirror(img: Image.Image) -> Image.Image:
    left = img.crop((0, 0, img.width // 2, img.height))
    right = ImageOps.mirror(left)

    result = Image.new("RGB", img.size)
    result.paste(left, (0, 0))
    result.paste(right, (img.width // 2, 0))

    return result


def apply_rotate(img: Image.Image, angle: int = 90) -> Image.Image:
    return img.rotate(angle, expand=True)


def apply_contour(img: Image.Image) -> Image.Image:
    arr = np.array(img)

    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

    return Image.fromarray(rgb)


EFFECTS = {
    "grayscale": apply_grayscale,
    "sepia": apply_sepia,
    "invert": apply_invert,
    "neon": apply_neon,
    "glitch": apply_glitch,
    "pixelate": apply_pixelate,
    "blur": apply_blur,
    "watercolor": apply_watercolor,
    "mirror": apply_mirror,
    "rotate": apply_rotate,
    "contour": apply_contour,
}


EFFECT_META = {
    "grayscale": {"label": "Grayscale", "icon": "🌫️", "category": "colour"},
    "sepia": {"label": "Sépia", "icon": "🟤", "category": "colour"},
    "invert": {"label": "Inversion", "icon": "🔄", "category": "colour"},
    "neon": {"label": "Neon", "icon": "💜", "category": "colour"},
    "glitch": {"label": "Glitch", "icon": "⚡", "category": "distort"},
    "pixelate": {"label": "Pixelation", "icon": "🟧", "category": "distort"},
    "blur": {"label": "Flou", "icon": "🌀", "category": "distort"},
    "watercolor": {"label": "Aquarelle", "icon": "🎨", "category": "distort"},
    "mirror": {"label": "Miroir", "icon": "🪞", "category": "geometric"},
    "rotate": {"label": "Rotation", "icon": "🔁", "category": "geometric"},
    "contour": {"label": "Contours", "icon": "✏️", "category": "geometric"},
}


def process_image(path: str, effect: str, **kwargs) -> tuple[Image.Image, str]:
    img = load_image(path)

    fn = EFFECTS.get(effect)
    if fn is None:
        raise ValueError(f"Effet inconnu : {effect}")

    result = fn(img, **kwargs)
    b64 = pil_to_b64(result)

    return result, b64