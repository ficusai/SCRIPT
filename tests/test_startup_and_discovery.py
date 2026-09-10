import os
import pytest
from PyQt6.QtWidgets import QApplication
from opencode_extractor.discovery.discover_all_databases import discover_all_databases
from opencode_extractor.constants.db_candidate_paths import DB_CANDIDATE_PATHS
from opencode_extractor.constants.text_dump_paths import TEXT_DUMP_PATHS
from gui.startup_dialog import StartupDialog


@pytest.fixture(scope="session")
def qapp():
    """Provides a single QApplication instance for Qt GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_db_candidate_paths_no_hardcoded_user():
    """Ensure candidate paths definition file does not contain hardcoded usernames."""
    import inspect
    import opencode_extractor.constants.db_candidate_paths as db_mod
    src = inspect.getsource(db_mod)
    assert "/home/ficus-pro" not in src, "Hardcoded user found in db_candidate_paths source code"


def test_text_dump_paths_no_hardcoded_user():
    """Ensure text dump paths definition file does not contain hardcoded usernames."""
    import inspect
    import opencode_extractor.constants.text_dump_paths as txt_mod
    src = inspect.getsource(txt_mod)
    assert "/home/ficus-pro" not in src, "Hardcoded user found in text_dump_paths source code"


def test_discover_all_databases_returns_list():
    """Verify discover_all_databases executes without raising errors."""
    sources = discover_all_databases()
    assert isinstance(sources, list)


def test_startup_dialog_initialization(qapp):
    """Test that StartupDialog initializes cleanly and updates selected path on selection."""
    dialog = StartupDialog()
    assert dialog.windowTitle() == "SCRIPT by FICUS (ficusai) — Select Session Database"
    assert dialog.continue_btn.isEnabled() == (len(dialog.path_input.text().strip()) > 0)

    dialog.path_input.setText("/tmp/test_opencode.db")
    assert dialog.continue_btn.isEnabled() is True
    assert dialog.get_selected_path() == "/tmp/test_opencode.db"
