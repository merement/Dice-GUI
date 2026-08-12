# dice_gui/widgets/metadata_panel.py

from PyQt6.QtWidgets import (
    QWidget,
    QGroupBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QDialog,
    QTextBrowser,
    QVBoxLayout,
)


class MetadataDialog(QDialog):
    """
    Non-modal dialog for displaying raw metadata records details.
    """
    def __init__(self, raw_records: list[dict], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Metadata Overview")
        self.resize(350, 450)

        # Make dialog non-modal
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.text_browser = QTextBrowser(self)
        # Avoid standard margin/padding inside text browser for a compact feel
        self.text_browser.setFrameStyle(0)  # flat/no border
        layout.addWidget(self.text_browser)

        self.update_records(raw_records)

    def update_records(self, raw_records: list[dict]):
        html_content = ""
        for rec in raw_records:
            if not isinstance(rec, dict):
                continue
            rec_type = rec.get("type", "unknown")
            html_content += f"<b>{rec_type}</b><br>"
            for key, val in rec.items():
                if key == "type":
                    continue
                # Indent key-value lines with 4 non-breaking spaces
                html_content += f"&nbsp;&nbsp;&nbsp;&nbsp;{key} : {val}<br>"
            html_content += "<br>"

        self.text_browser.setHtml(html_content)


class MetadataPanel(QGroupBox):
    """
    Panel displaying simulation metadata summary fields and raw records details.
    """
    def __init__(self, parent: QWidget | None = None):
        super().__init__("Metadata", parent)

        # Create widgets
        self.meta_title_label = QLabel("- -", self)
        self.meta_notes_label = QLabel("- -", self)
        self.meta_created_label = QLabel("- -", self)
        self.meta_base_label = QLabel("- -", self)
        self.meta_more_button = QPushButton("More...", self)
        self.meta_more_button.setEnabled(False)

        self._metadata_dialog = None
        self._raw_records: list[dict] = []

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        metadata_layout = QGridLayout(self)
        metadata_layout.setContentsMargins(8, 4, 8, 4)
        metadata_layout.setSpacing(6)

        # Labels and displays arranged in a grid
        metadata_layout.addWidget(QLabel("Title:", self), 0, 0)
        metadata_layout.addWidget(self.meta_title_label, 0, 1)
        metadata_layout.addWidget(QLabel("Created:", self), 0, 2)
        metadata_layout.addWidget(self.meta_created_label, 0, 3)

        metadata_layout.addWidget(QLabel("Notes:", self), 1, 0)
        metadata_layout.addWidget(self.meta_notes_label, 1, 1)
        metadata_layout.addWidget(QLabel("Base:", self), 1, 2)
        metadata_layout.addWidget(self.meta_base_label, 1, 3)

        # Configure stretch factors for columns in the Metadata grid
        metadata_layout.setColumnStretch(0, 0)
        metadata_layout.setColumnStretch(1, 2)
        metadata_layout.setColumnStretch(2, 0)
        metadata_layout.setColumnStretch(3, 1)
        metadata_layout.setColumnStretch(4, 0)

        metadata_layout.addWidget(self.meta_more_button, 0, 4, 2, 1)
        self.setLayout(metadata_layout)

    def _connect_signals(self):
        self.meta_more_button.clicked.connect(self.show_more_metadata)

    def show_more_metadata(self):
        if self._metadata_dialog is None:
            self._metadata_dialog = MetadataDialog(self._raw_records, self)
        else:
            self._metadata_dialog.update_records(self._raw_records)

        self._metadata_dialog.show()
        self._metadata_dialog.raise_()
        self._metadata_dialog.activateWindow()

    def set_metadata(self, metadata: dict | None):
        if metadata is None or not metadata.get("has_metadata", False):
            self.clear_metadata()
            return

        self.meta_title_label.setText(str(metadata.get("title", "- -")))
        self.meta_notes_label.setText(str(metadata.get("notes", "- -")))
        self.meta_created_label.setText(str(metadata.get("created", "- -")))

        base_val = metadata.get("base")
        if base_val is None:
            base_val = 1
        self.meta_base_label.setText(str(base_val))

        self._raw_records = metadata.get("raw_records", [])
        self.meta_more_button.setEnabled(len(self._raw_records) > 0)

        if self._metadata_dialog is not None and self._metadata_dialog.isVisible():
            self._metadata_dialog.update_records(self._raw_records)

    def clear_metadata(self):
        self.meta_title_label.setText("- -")
        self.meta_notes_label.setText("- -")
        self.meta_created_label.setText("- -")
        self.meta_base_label.setText("- -")
        self.meta_more_button.setEnabled(False)
        self._raw_records = []
        if self._metadata_dialog is not None and self._metadata_dialog.isVisible():
            self._metadata_dialog.update_records([])
