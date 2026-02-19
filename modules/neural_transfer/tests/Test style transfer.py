"""
tests/test_style_transfer.py
-----------------------------
Unit & integration tests for the Style Transfer ML component.

Run with:
    pytest tests/ -v

Requires style images to be present (run download_styles.py first).
Tests that invoke the actual model are marked @pytest.mark.integration
and can be skipped in CI with:
    pytest tests/ -v -m "not integration"
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def tmp_dir():
    """Session-scoped temporary directory."""
    d = tempfile.mkdtemp(prefix="style_transfer_tests_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_content_image(tmp_dir) -> str:
    """Create a small synthetic content image (100×100 solid colour)."""
    path = os.path.join(tmp_dir, "content_sample.jpg")
    img  = Image.fromarray(
        np.full((100, 100, 3), fill_value=[100, 149, 237], dtype=np.uint8)
    )
    img.save(path, format="JPEG")
    return path


@pytest.fixture
def sample_style_image(tmp_dir) -> str:
    """Create a small synthetic style image (80×80 gradient)."""
    path = os.path.join(tmp_dir, "style_sample.jpg")
    arr  = np.zeros((80, 80, 3), dtype=np.uint8)
    for i in range(80):
        arr[i, :] = [i * 3, 200 - i * 2, 128]
    Image.fromarray(arr).save(path, format="JPEG")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# image_utils tests
# ─────────────────────────────────────────────────────────────────────────────

class TestImageUtils:

    def test_allowed_extension_valid(self):
        from utils.image_utils import allowed_extension
        for name in ["photo.jpg", "img.JPEG", "pic.png", "file.webp", "img.bmp"]:
            assert allowed_extension(name), f"Should be allowed: {name}"

    def test_allowed_extension_invalid(self):
        from utils.image_utils import allowed_extension
        for name in ["doc.pdf", "video.mp4", "script.py", "noextension"]:
            assert not allowed_extension(name), f"Should NOT be allowed: {name}"

    def test_validate_image_file_valid(self, sample_content_image):
        from utils.image_utils import validate_image_file
        w, h = validate_image_file(sample_content_image)
        assert w == 100
        assert h == 100

    def test_validate_image_file_not_found(self):
        from utils.image_utils import validate_image_file, ImageValidationError
        with pytest.raises(ImageValidationError, match="not found"):
            validate_image_file("/nonexistent/path/image.jpg")

    def test_validate_image_file_too_small(self, tmp_dir):
        from utils.image_utils import validate_image_file, ImageValidationError
        path = os.path.join(tmp_dir, "tiny.jpg")
        Image.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(path)
        with pytest.raises(ImageValidationError, match="too small"):
            validate_image_file(path)

    def test_validate_image_file_corrupt(self, tmp_dir):
        from utils.image_utils import validate_image_file, ImageValidationError
        path = os.path.join(tmp_dir, "corrupt.jpg")
        Path(path).write_bytes(b"not_an_image_at_all_!!!!")
        with pytest.raises(ImageValidationError, match="Invalid or corrupt"):
            validate_image_file(path)

    def test_preprocess_image_resize(self, tmp_dir, sample_content_image):
        from utils.image_utils import preprocess_image
        out = os.path.join(tmp_dir, "resized.jpg")
        # Create a large image first
        large_path = os.path.join(tmp_dir, "large.jpg")
        Image.fromarray(
            np.zeros((800, 600, 3), dtype=np.uint8)
        ).save(large_path)

        preprocess_image(large_path, dest_path=out, max_dim=256)

        with Image.open(out) as img:
            w, h = img.size
        assert max(w, h) <= 256

    def test_preprocess_image_rgba_to_rgb(self, tmp_dir):
        from utils.image_utils import preprocess_image
        rgba_path = os.path.join(tmp_dir, "rgba.png")
        out_path  = os.path.join(tmp_dir, "rgba_out.jpg")
        Image.fromarray(
            np.zeros((100, 100, 4), dtype=np.uint8), mode="RGBA"
        ).save(rgba_path, format="PNG")

        preprocess_image(rgba_path, dest_path=out_path)

        with Image.open(out_path) as img:
            assert img.mode == "RGB"

    def test_cleanup_old_outputs(self, tmp_dir):
        from utils.image_utils import cleanup_old_outputs
        out_dir = os.path.join(tmp_dir, "outputs_cleanup")
        os.makedirs(out_dir, exist_ok=True)

        # Create 5 dummy files
        for i in range(5):
            p = os.path.join(out_dir, f"output_{i}.jpg")
            Image.fromarray(
                np.zeros((50, 50, 3), dtype=np.uint8)
            ).save(p)

        deleted = cleanup_old_outputs(out_dir, keep_latest=3)
        remaining = list(Path(out_dir).glob("*.jpg"))

        assert deleted == 2
        assert len(remaining) == 3


# ─────────────────────────────────────────────────────────────────────────────
# StyleTransferEngine unit tests (model mocked)
# ─────────────────────────────────────────────────────────────────────────────

class TestStyleTransferEngineMocked:
    """Tests that mock the TF Hub model — no GPU/internet required."""

    @pytest.fixture(autouse=True)
    def patch_hub_and_style(self, sample_content_image, sample_style_image, monkeypatch):
        """
        - Patches hub.load so no network call is made.
        - Patches PAINTER_STYLES to point at our synthetic style image.
        - Resets the cached _hub_model before each test.
        """
        import style_transfer as st_module

        # Reset cached model
        st_module.StyleTransferEngine._hub_model = None

        # Mock hub.load → returns a callable that outputs a fake stylized tensor
        import tensorflow as tf
        fake_output = tf.zeros([1, 100, 100, 3])

        mock_model      = MagicMock()
        mock_model.return_value = (fake_output,)

        monkeypatch.setattr(st_module.hub, "load", lambda url: mock_model)

        # Redirect style paths to our sample image
        monkeypatch.setattr(
            st_module,
            "PAINTER_STYLES",
            {
                "vangogh" : sample_style_image,
                "munch"   : sample_style_image,
                "picasso" : sample_style_image,
            },
        )

        self.sample_content = sample_content_image
        self.sample_style   = sample_style_image

    def _make_engine(self):
        from style_transfer import StyleTransferEngine
        return StyleTransferEngine()

    def test_engine_loads(self):
        engine = self._make_engine()
        assert engine.model is not None

    def test_transfer_vangogh(self, tmp_dir):
        from style_transfer import StyleTransferEngine
        import style_transfer as st_module
        st_module.OUTPUT_DIR = Path(tmp_dir)

        engine = self._make_engine()
        result = engine.transfer(self.sample_content, "vangogh")

        assert result["painter"] == "vangogh"
        assert "Van Gogh" in result["display_name"]
        assert os.path.isfile(result["output_path"])
        assert result["elapsed_sec"] >= 0

    def test_transfer_munch(self, tmp_dir):
        from style_transfer import StyleTransferEngine
        import style_transfer as st_module
        st_module.OUTPUT_DIR = Path(tmp_dir)

        engine = self._make_engine()
        result = engine.transfer(self.sample_content, "munch")
        assert result["painter"] == "munch"

    def test_transfer_picasso(self, tmp_dir):
        from style_transfer import StyleTransferEngine
        import style_transfer as st_module
        st_module.OUTPUT_DIR = Path(tmp_dir)

        engine = self._make_engine()
        result = engine.transfer(self.sample_content, "picasso")
        assert result["painter"] == "picasso"

    def test_transfer_invalid_painter(self):
        engine = self._make_engine()
        with pytest.raises(ValueError, match="Unknown painter"):
            engine.transfer(self.sample_content, "dali")  # type: ignore

    def test_transfer_missing_content(self):
        engine = self._make_engine()
        with pytest.raises(FileNotFoundError, match="Content image not found"):
            engine.transfer("/nonexistent/image.jpg", "vangogh")

    def test_transfer_custom_style(self, tmp_dir):
        from style_transfer import StyleTransferEngine
        import style_transfer as st_module
        st_module.OUTPUT_DIR = Path(tmp_dir)

        engine = self._make_engine()
        result = engine.transfer_with_custom_style(
            self.sample_content, self.sample_style
        )
        assert result["painter"] == "custom"
        assert os.path.isfile(result["output_path"])

    def test_model_cached_across_instances(self):
        from style_transfer import StyleTransferEngine
        e1 = self._make_engine()
        e2 = StyleTransferEngine()
        assert e1.model is e2.model, "Model should be shared (singleton)"


# ─────────────────────────────────────────────────────────────────────────────
# Integration tests — require real TF Hub model + internet on first run
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestStyleTransferIntegration:
    """
    Runs the REAL TF Hub model.
    Skipped by default in CI.  Run with:
        pytest tests/ -v -m integration
    """

    @pytest.fixture(autouse=True)
    def check_style_images(self):
        from style_transfer import PAINTER_STYLES
        for painter, path in PAINTER_STYLES.items():
            if not os.path.isfile(path):
                pytest.skip(
                    f"Style image for '{painter}' not found at {path}. "
                    "Run `python download_styles.py` first."
                )

    def test_real_vangogh_transfer(self, sample_content_image, tmp_dir):
        from style_transfer import StyleTransferEngine
        import style_transfer as st_module
        st_module.StyleTransferEngine._hub_model = None   # force reload
        st_module.OUTPUT_DIR = Path(tmp_dir)

        engine = StyleTransferEngine()
        result = engine.transfer(sample_content_image, "vangogh")

        assert os.path.isfile(result["output_path"])
        with Image.open(result["output_path"]) as img:
            assert img.mode == "RGB"
            assert img.size[0] > 0

    def test_output_is_visually_different(self, sample_content_image, tmp_dir):
        """Stylized image should differ from the content image."""
        from style_transfer import StyleTransferEngine
        import style_transfer as st_module
        st_module.OUTPUT_DIR = Path(tmp_dir)

        engine = StyleTransferEngine()
        result = engine.transfer(sample_content_image, "munch")

        content_arr  = np.array(Image.open(sample_content_image).convert("RGB"))
        stylized_arr = np.array(Image.open(result["output_path"]).convert("RGB"))

        # Resize to same dims for comparison
        c_img = Image.fromarray(content_arr).resize(
            Image.open(result["output_path"]).size
        )
        c_arr = np.array(c_img).astype(float)
        s_arr = stylized_arr.astype(float)

        mean_diff = np.mean(np.abs(c_arr - s_arr))
        assert mean_diff > 1.0, "Stylized output looks identical to input — model may have failed"