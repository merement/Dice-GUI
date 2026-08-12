import pytest
from PyQt6.QtWidgets import QApplication
from dice_gui.widgets.metadata_panel import MetadataPanel, MetadataDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_metadata_panel_init(qapp):
    panel = MetadataPanel()
    assert panel.meta_title_label.text() == "- -"
    assert panel.meta_notes_label.text() == "- -"
    assert panel.meta_created_label.text() == "- -"
    assert panel.meta_base_label.text() == "- -"
    assert not panel.meta_more_button.isEnabled()


def test_metadata_panel_set_metadata(qapp):
    panel = MetadataPanel()
    meta = {
        "has_metadata": True,
        "title": "Simulation Title",
        "notes": "Some notes here",
        "created": "2026-07-13",
        "base": 1,
        "raw_records": [
            {"type": "format", "name": "relaxed-spins", "version": 1},
        ],
    }

    panel.set_metadata(meta)
    assert panel.meta_title_label.text() == "Simulation Title"
    assert panel.meta_notes_label.text() == "Some notes here"
    assert panel.meta_created_label.text() == "2026-07-13"
    assert panel.meta_base_label.text() == "1"
    assert panel.meta_more_button.isEnabled()


def test_metadata_panel_default_base(qapp):
    panel = MetadataPanel()
    meta = {
        "has_metadata": True,
        "title": "No base specified",
    }
    panel.set_metadata(meta)
    assert panel.meta_base_label.text() == "1"


def test_metadata_panel_clear_metadata(qapp):
    panel = MetadataPanel()
    meta = {
        "has_metadata": True,
        "title": "Simulation Title",
        "notes": "Some notes here",
        "created": "2026-07-13",
        "base": 1,
        "raw_records": [{"type": "format"}],
    }

    panel.set_metadata(meta)
    panel.clear_metadata()

    assert panel.meta_title_label.text() == "- -"
    assert panel.meta_notes_label.text() == "- -"
    assert panel.meta_created_label.text() == "- -"
    assert panel.meta_base_label.text() == "- -"
    assert not panel.meta_more_button.isEnabled()


def test_metadata_dialog_html(qapp):
    raw_records = [
        {"type": "format", "name": "relaxed-spins", "version": 1},
    ]
    dialog = MetadataDialog(raw_records)
    html = dialog.text_browser.toHtml()

    # The HTML output should contain the formatted records
    assert "format" in html
    assert "name : relaxed-spins" in html
    assert "version : 1" in html
    assert "\xa0\xa0\xa0\xa0" in html
