import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    )


def rename_user_folder(old_username: str, new_username: str):
    upload_root = current_app.config["UPLOAD_FOLDER"]
    old_path = os.path.join(upload_root, old_username)
    new_path = os.path.join(upload_root, new_username)

    if not os.path.exists(old_path):
        return

    if os.path.exists(new_path):
        raise FileExistsError("Target user folder already exists")

    os.rename(old_path, new_path)


def save_user_image(file, user, kind: str):
    """
    kind = 'avatar' | 'cover' | 'artwork'
    """

    if not file or file.filename == "":
        print("No file or empty filename")
        return None

    if not allowed_file(file.filename):
        print("File not allowed")
        raise ValueError("Invalid file type")

    old_filename = user.avatar_filename if kind == "avatar" else user.cover_filename
    if old_filename:
        old_filepath = os.path.join(
            current_app.config["UPLOAD_FOLDER"], str(user.username), old_filename
        )
        if os.path.exists(old_filepath):
            try:
                os.remove(old_filepath)
            except Exception as e:
                print(f"Error removing old {kind}: {e}")

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}_{secure_filename(f'{kind}.{ext}')}"

    user_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], str(user.username))
    os.makedirs(user_folder, exist_ok=True)
    path = os.path.join(user_folder, filename)
    file.save(path)

    return filename
