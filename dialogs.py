"""
ComicEditor — Ayarlar diyaloğu
"""
from PyQt6.QtWidgets import (  # type: ignore
    QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QLineEdit, QLabel, QDialogButtonBox
)
from PyQt6.QtCore import Qt  # type: ignore


# ── Ayarlar Dialog Stili ──
SETTINGS_DIALOG_STYLE = """
QDialog {
    background-color: #13151a;
    color: #e8eaed;
    border-radius: 18px;
}
QWidget {
    color: #e8eaed;
    background-color: transparent;
}
QLineEdit, QComboBox {
    background-color: #0d0e13;
    border: 1px solid rgba(255,255,255,0.06);
    padding: 10px 14px;
    border-radius: 12px;
    color: #e8eaed;
    font-size: 13px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid rgba(124,108,247,0.5);
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox QAbstractItemView {
    background-color: #13151a;
    border: 1px solid rgba(255,255,255,0.08);
    selection-background-color: #7c6cf7;
    color: #e8eaed;
    border-radius: 10px;
    padding: 4px;
}
QPushButton {
    background-color: #1a1d25;
    padding: 9px 18px;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    color: #e8eaed;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #22252f;
    border-color: rgba(255,255,255,0.12);
}
QPushButton:pressed {
    background-color: #7c6cf7;
}
QLabel {
    background-color: transparent;
    color: #9ca0ab;
    font-size: 13px;
}
"""


class SettingsDialog(QDialog):
    """Uygulama ayarları diyaloğu — çeviri motoru, API key, font ve hizalama."""

    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)  # type: ignore
        self.setWindowTitle("⚙️ Ayarlar")
        self.resize(440, 240)
        self.current_settings = current_settings or {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(14)

        self.combo_engine = QComboBox()
        self.combo_engine.addItems(["Otomatik (Gemini > Google)", "Sadece Ücretsiz (Google)"])
        self.combo_engine.setCurrentText(str(self.current_settings.get("engine", "Otomatik (Gemini > Google)")))

        self.txt_api = QLineEdit(str(self.current_settings.get("api_key", "")))
        self.txt_api.setEchoMode(QLineEdit.EchoMode.Password)

        self.combo_font = QComboBox()
        fonts = [
            "Anime Ace (Manga)",
            "Patrick Hand (Tam Türkçe Destekli)",
            "Comic Neue Bold (Klasik)",
            "Arial", "Comic Sans MS", "Impact"
        ]
        self.combo_font.addItems(fonts)
        if str(self.current_settings.get("font", "")) in fonts:
            self.combo_font.setCurrentText(str(self.current_settings.get("font", "")))

        self.combo_align = QComboBox()
        self.combo_align.addItems(["Orta", "Sol", "Sağ"])
        self.combo_align.setCurrentText(str(self.current_settings.get("align", "Orta")))

        form.addRow("Çeviri Motoru:", self.combo_engine)
        form.addRow("Gemini API (Opsiyonel):", self.txt_api)
        form.addRow("Varsayılan Font:", self.combo_font)
        form.addRow("Hizalama:", self.combo_align)
        layout.addLayout(form)

        lbl_dev = QLabel(
            'Geliştirici: <a href="https://github.com/Sefflex" '
            'style="color: #a78bfa; text-decoration: none;">Sefflex</a> | v0.8'
        )
        lbl_dev.setOpenExternalLinks(True)
        lbl_dev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_dev)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.setStyleSheet(SETTINGS_DIALOG_STYLE)

    def get_settings(self) -> dict:
        return {
            "engine": self.combo_engine.currentText(),
            "api_key": self.txt_api.text().strip(),
            "font": self.combo_font.currentText(),
            "align": self.combo_align.currentText(),
        }
