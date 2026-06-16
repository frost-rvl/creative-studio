"""
download_styles.py
------------------
Downloads the three reference style images used by the style transfer engine.
Run this ONCE before starting the Flask app:

    python download_styles.py

Images sourced from Wikimedia Commons (public domain).
"""

import os
import urllib.request
from pathlib import Path

STYLE_IMG_DIR = Path(__file__).parent / "static" / "style_images"
STYLE_IMG_DIR.mkdir(parents=True, exist_ok=True)

# Public-domain images from Wikimedia Commons
STYLE_IMAGES = {
    "vangogh_starry_night.jpg": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/"
        "Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/"
        "1280px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg"
    ),
    "munch_scream.jpg": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/"
        "Edvard_Munch%2C_1893%2C_The_Scream%2C_oil%2C_tempera_and_pastel_on_cardboard%2C"
        "_91_x_73_cm%2C_National_Gallery_of_Norway.jpg/"
        "800px-Edvard_Munch%2C_1893%2C_The_Scream%2C_oil%2C_tempera_and_pastel_on_cardboard%2C"
        "_91_x_73_cm%2C_National_Gallery_of_Norway.jpg"
    ),
    "picasso_weeping_woman.jpg": (
        "https://upload.wikimedia.org/wikipedia/en/1/14/Picasso_The_Weeping_Woman_Tate_identifier_T05010_10.jpg"
    ),
}


def download_all() -> None:
    headers = {"User-Agent": "Mozilla/5.0 (StyleTransferApp/1.0)"}

    for filename, url in STYLE_IMAGES.items():
        dest = STYLE_IMG_DIR / filename
        if dest.exists():
            print(f"  ✓ Already exists: {filename}")
            continue

        print(f"  ↓ Downloading {filename} …", end=" ", flush=True)
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()
            dest.write_bytes(data)
            print(f"done ({len(data) // 1024} KB)")
        except Exception as exc:
            print(f"FAILED — {exc}")
            print(f"    → Manually download from:\n      {url}")
            print(f"    → Save to: {dest}\n")


if __name__ == "__main__":
    print("Downloading style reference images …\n")
    download_all()
    print("\nAll done. You can now run the Flask app.")