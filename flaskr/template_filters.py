from flask import current_app

MODULE_DISPLAY_NAMES = {
    "zelija": "Zelija",
    "sablier": "Sablier",
    "aquarium": "Aquarium",
    "neural_transfer": "Neural Transfer",
    "image_processing": "Image Processing",
    "data_visualization": "Data Visualization",
}

def module_display_name(name: str) -> str:
    """Return a human‑readable display name for a module."""
    return MODULE_DISPLAY_NAMES.get(name, name.replace("_", " ").title())