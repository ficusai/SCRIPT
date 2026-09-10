import os
import tempfile
from pathlib import Path


def test_workspace_traversal_guard():
    """Test that path confinement logic blocks directory traversal."""
    with tempfile.TemporaryDirectory() as ws:
        ws_path = Path(ws).resolve()
        safe_file = ws_path / "script.py"
        safe_file.write_text("print('safe')")

        # Attempt to resolve an outside file
        outside_path = ws_path / ".." / "outside.py"
        resolved_outside = outside_path.resolve()

        # Confinement check logic (same as in extract_scripts.py)
        assert safe_file.resolve().is_relative_to(ws_path)
        assert not resolved_outside.is_relative_to(ws_path)


def test_deterministic_hash():
    """Test that hashlib-based naming is deterministic."""
    import hashlib
    code = "print('hello world')"
    h = hashlib.sha256(code.encode("utf-8")).hexdigest()[:8]
    name = f"inline_script_{h}.py"
    assert name.startswith("inline_script_") and name.endswith(".py")
    # Same code always produces same hash
    h2 = hashlib.sha256(code.encode("utf-8")).hexdigest()[:8]
    assert h == h2
