"""
ComicEditor — Premium Dark Theme (QSS)
═══════════════════════════════════════════════════
Canva / Figma / Adobe CC seviyesinde modern, yumuşak
ve premium hissiyat veren karanlık tema.

Tasarım Felsefesi:
  • Sert kenarlar yok → her yerde yuvarlak köşeler (16-20px)
  • Düz renkler yok → katmanlı yüzey sistemi (4 seviye derinlik)
  • Sert kenarlıklar yok → yarı-saydam, neredeyse görünmez kenarlıklar
  • Sıkışık düzen yok → ferah padding ve margin
  • Gradient aksanlar (mor → mavi → pembe)
  • Zengin hover/focus/pressed durumları
  • Ultra-ince scrollbar'lar
  • Modern tipografi hiyerarşisi

Renk Sistemi:
  bg-deep     : #08090d   (en derin arka plan)
  bg-base     : #0d0e13   (ana arka plan)
  surface-0   : #111318   (input arka planı)
  surface-1   : #161820   (panel arka planı)
  surface-2   : #1c1e28   (kart/buton arka planı)
  surface-3   : #22252f   (hover arka planı)
  surface-4   : #2a2d38   (aktif/pressed arka planı)
  accent-1    : #7c6cf7   (mor - ana vurgu)
  accent-2    : #4ea8de   (mavi - ikincil vurgu)
  accent-3    : #e879a0   (pembe - üçüncül vurgu)
  success     : #34d399   (yeşil)
  danger      : #f87171   (kırmızı)
"""

PREMIUM_DARK_THEME = """

/* ══════════════════════════════════════════════════
   ANA PENCERE & GENEL KURALLAR
   ══════════════════════════════════════════════════ */

QMainWindow {
    background-color: #0d0e13;
}

QWidget {
    color: #e8eaed;
    font-family: 'Inter', 'Segoe UI', 'SF Pro Display', sans-serif;
    font-size: 13px;
    background-color: transparent;
}


/* ══════════════════════════════════════════════════
   TOPBAR — Üst navigasyon çubuğu
   Gradient alt çizgi ile derinlik hissiyatı
   ══════════════════════════════════════════════════ */

#topbar {
    background-color: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #161820, stop:1 #13151a
    );
    border: none;
    border-bottom: 2px solid qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(124,108,247,0.4),
        stop:0.5 rgba(78,168,222,0.3),
        stop:1 rgba(232,121,160,0.2)
    );
}

#logoIcon {
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.08);
}

#logoLabel {
    color: #f0f2f5;
    font-size: 19px;
    font-weight: bold;
    letter-spacing: 2px;
}


/* ══════════════════════════════════════════════════
   SIDEBAR — Sol panel (sayfa listesi)
   Yumuşak köşeler, katmanlı yüzey
   ══════════════════════════════════════════════════ */

#sidebar {
    background-color: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #161820, stop:1 #13151a
    );
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 18px;
}

#sectionTitle {
    color: #555860;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 3px;
}

#footerLabel {
    color: #3d4150;
    font-size: 11px;
}


/* ══════════════════════════════════════════════════
   ALT ARAÇ ÇUBUĞU (Tool Strip)
   Gradient kenarlık, yuvarlak tasarım
   ══════════════════════════════════════════════════ */

#toolStrip {
    background-color: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #161820, stop:1 #13151a
    );
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px;
}


/* ══════════════════════════════════════════════════
   SAĞ PANEL — Özellikler paneli
   Floating card hissiyatı
   ══════════════════════════════════════════════════ */

#propertiesScroll {
    background-color: transparent;
    border: none;
}

#propertiesPanel {
    background-color: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #161820, stop:1 #13151a
    );
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 18px;
}

#panelTitle {
    color: #555860;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 3px;
}

#fieldLabel {
    color: #7a7d86;
    font-size: 12px;
    margin-top: 4px;
}

#tipLabel {
    color: #3d4150;
    font-size: 11px;
    padding: 10px 6px;
    font-style: italic;
}


/* ══════════════════════════════════════════════════
   BUTONLAR — Genel tasarım
   Yuvarlak, yumuşak geçişli, katmanlı
   ══════════════════════════════════════════════════ */

QPushButton {
    background-color: #1c1e28;
    padding: 9px 16px;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    color: #e8eaed;
    font-size: 12px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #252830;
    border-color: rgba(255,255,255,0.12);
}
QPushButton:pressed {
    background-color: #7c6cf7;
    border-color: rgba(124,108,247,0.5);
    color: white;
}
QPushButton:checked {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #7c6cf7, stop:1 #6c5ce7
    );
    border: 1px solid rgba(124,108,247,0.4);
    color: white;
    font-weight: bold;
}


/* ── Primary Buton (Proje Aç, Ön Ayar Kaydet) ── */
#btnPrimary {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #7c6cf7, stop:1 #6558e3
    );
    border: 1px solid rgba(124,108,247,0.3);
    color: white;
    font-weight: bold;
    padding: 9px 20px;
}
#btnPrimary:hover {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #8d7eff, stop:1 #7c6cf7
    );
    border-color: rgba(141,126,255,0.5);
}
#btnPrimary:pressed {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #6558e3, stop:1 #5548cf
    );
}


/* ── Secondary Buton (Kaydet) ── */
#btnSecondary {
    background-color: rgba(78,168,222,0.08);
    border: 1px solid rgba(78,168,222,0.25);
    color: #5eb8ee;
    font-weight: 500;
}
#btnSecondary:hover {
    background-color: rgba(78,168,222,0.18);
    border-color: rgba(78,168,222,0.45);
    color: #7ccaf5;
}
#btnSecondary:pressed {
    background-color: #4ea8de;
    color: white;
}


/* ── Hero Buton (Tam Otonom Çıkart) — 3 renk gradient ── */
#btnHero {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c6cf7,
        stop:0.5 #4ea8de,
        stop:1 #e879a0
    );
    border: none;
    color: white;
    font-weight: bold;
    font-size: 13px;
    padding: 10px 24px;
    border-radius: 14px;
}
#btnHero:hover {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #8d7eff,
        stop:0.5 #5eb8ee,
        stop:1 #f08ab0
    );
}
#btnHero:pressed {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #6558e3,
        stop:0.5 #3d96cc,
        stop:1 #d5688e
    );
}


/* ── Danger Buton (Sıfırla) ── */
#btnDanger {
    background-color: rgba(248,113,113,0.06);
    border: 1px solid rgba(248,113,113,0.2);
    color: #f87171;
}
#btnDanger:hover {
    background-color: rgba(248,113,113,0.15);
    border-color: rgba(248,113,113,0.4);
    color: #fca5a5;
}
#btnDanger:pressed {
    background-color: #f87171;
    color: white;
}


/* ── Success Buton (Seçerek Oku) ── */
#btnSuccess {
    background-color: rgba(52,211,153,0.06);
    border: 1px solid rgba(52,211,153,0.2);
    color: #34d399;
    font-weight: bold;
}
#btnSuccess:hover {
    background-color: rgba(52,211,153,0.15);
    border-color: rgba(52,211,153,0.4);
    color: #6ee7b7;
}
#btnSuccess:pressed {
    background-color: #34d399;
    color: white;
}


/* ── Icon Buton (Ayarlar) ── */
#btnIcon {
    background-color: transparent;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    font-size: 16px;
    padding: 0px;
}
#btnIcon:hover {
    background-color: rgba(124,108,247,0.1);
    border-color: rgba(124,108,247,0.3);
}


/* ── Tool Butonlar (Fırça, Kapla, Damlalık) ── */
#btnTool {
    padding: 7px 14px;
    font-size: 12px;
    border-radius: 10px;
}
#btnTool:checked {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #7c6cf7, stop:1 #6c5ce7
    );
    border: 1px solid rgba(124,108,247,0.4);
    color: white;
}


/* ── Renk Butonları ── */
#colorBtn {
    text-align: left;
    padding: 9px 14px;
    border-radius: 12px;
}


/* ══════════════════════════════════════════════════
   COLLAPSIBLE SECTION HEADER
   Zarif alt çizgi, modern tipografi
   ══════════════════════════════════════════════════ */

#sectionHeader {
    background-color: transparent;
    border: none;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    border-radius: 0px;
    text-align: left;
    padding: 12px 14px;
    font-weight: bold;
    font-size: 12px;
    color: #e8eaed;
}
#sectionHeader:hover {
    background-color: rgba(124,108,247,0.05);
    color: #9d8fff;
    border-bottom-color: rgba(124,108,247,0.15);
}


/* ══════════════════════════════════════════════════
   INPUT & TEXT ALANLARI
   Yumuşak arka plan, yuvarlak köşeler, glow focus
   ══════════════════════════════════════════════════ */

QLineEdit {
    background-color: #111318;
    padding: 10px 14px;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    color: #e8eaed;
    selection-background-color: #7c6cf7;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid rgba(124,108,247,0.45);
    background-color: #0f1116;
}

QTextEdit {
    background-color: #111318;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    color: #e8eaed;
    padding: 10px 12px;
    selection-background-color: #7c6cf7;
    font-size: 13px;
}
QTextEdit:focus {
    border: 1px solid rgba(124,108,247,0.45);
    background-color: #0f1116;
}


/* ══════════════════════════════════════════════════
   SPINBOX
   ══════════════════════════════════════════════════ */

QSpinBox {
    background-color: #111318;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 8px 12px;
    color: #e8eaed;
    font-size: 13px;
}
QSpinBox:focus {
    border: 1px solid rgba(124,108,247,0.45);
}
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #1c1e28;
    border: none;
    width: 22px;
    border-radius: 6px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #7c6cf7;
}


/* ══════════════════════════════════════════════════
   COMBOBOX
   ══════════════════════════════════════════════════ */

QComboBox {
    background-color: #111318;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 8px 14px;
    color: #e8eaed;
    font-size: 13px;
}
QComboBox:focus {
    border: 1px solid rgba(124,108,247,0.45);
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox QAbstractItemView {
    background-color: #161820;
    border: 1px solid rgba(255,255,255,0.08);
    selection-background-color: #7c6cf7;
    color: #e8eaed;
    border-radius: 10px;
    padding: 4px;
}
QComboBox QAbstractItemView::item {
    padding: 6px 12px;
    border-radius: 8px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: rgba(124,108,247,0.15);
}


/* ══════════════════════════════════════════════════
   LISTWIDGET — Sayfa listesi
   Yumuşak seçim efekti, gradient active
   ══════════════════════════════════════════════════ */

QListWidget {
    background-color: #111318;
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 14px;
    padding: 6px;
    outline: none;
}
QListWidget::item {
    padding: 8px;
    border-radius: 10px;
    margin: 3px 2px;
    color: #e8eaed;
}
QListWidget::item:hover {
    background-color: rgba(124,108,247,0.08);
}
QListWidget::item:selected {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(124,108,247,0.35),
        stop:1 rgba(78,168,222,0.2)
    );
    color: white;
    border: 1px solid rgba(124,108,247,0.25);
}


/* ══════════════════════════════════════════════════
   CANVAS (QGraphicsView)
   Derin arka plan, ince kenarlık
   ══════════════════════════════════════════════════ */

QGraphicsView {
    background-color: #08090d;
    border: 1px solid rgba(255,255,255,0.03);
    border-radius: 16px;
}


/* ══════════════════════════════════════════════════
   SLIDER
   Gradient sub-page, büyük handle
   ══════════════════════════════════════════════════ */

QSlider::groove:horizontal {
    border: none;
    height: 5px;
    background: #1c1e28;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #8d7eff, stop:1 #7c6cf7
    );
    border: 2px solid rgba(124,108,247,0.3);
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 9px;
}
QSlider::handle:horizontal:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #9d8fff, stop:1 #8d7eff
    );
    border-color: rgba(124,108,247,0.5);
}
QSlider::sub-page:horizontal {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c6cf7,
        stop:0.6 #4ea8de,
        stop:1 #e879a0
    );
    border-radius: 2px;
}


/* ══════════════════════════════════════════════════
   CHECKBOX
   Gradient checked state, yuvarlak indicator
   ══════════════════════════════════════════════════ */

QCheckBox {
    spacing: 10px;
    color: #e8eaed;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 2px solid rgba(255,255,255,0.1);
    background-color: #111318;
}
QCheckBox::indicator:hover {
    border-color: rgba(124,108,247,0.4);
    background-color: rgba(124,108,247,0.05);
}
QCheckBox::indicator:checked {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #7c6cf7, stop:1 #6558e3
    );
    border-color: rgba(124,108,247,0.4);
}


/* ══════════════════════════════════════════════════
   LABEL — Genel
   ══════════════════════════════════════════════════ */

QLabel {
    color: #9ca0ab;
    background-color: transparent;
}


/* ══════════════════════════════════════════════════
   FRAME
   ══════════════════════════════════════════════════ */

QFrame {
    background-color: #161820;
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 18px;
}


/* ══════════════════════════════════════════════════
   PROGRESS DIALOG & BAR
   Gradient progress chunk
   ══════════════════════════════════════════════════ */

QProgressDialog {
    background-color: #161820;
    color: #e8eaed;
    border-radius: 14px;
}
QProgressBar {
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    background-color: #111318;
    text-align: center;
    color: #e8eaed;
    font-size: 12px;
}
QProgressBar::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c6cf7,
        stop:0.5 #4ea8de,
        stop:1 #e879a0
    );
    border-radius: 7px;
}


/* ══════════════════════════════════════════════════
   MESSAGE BOX
   ══════════════════════════════════════════════════ */

QMessageBox {
    background-color: #161820;
    color: #e8eaed;
}
QMessageBox QLabel {
    color: #e8eaed;
    font-size: 13px;
}
QMessageBox QPushButton {
    min-width: 90px;
    padding: 8px 18px;
}


/* ══════════════════════════════════════════════════
   SCROLLBAR — Ultra-ince, minimal
   ══════════════════════════════════════════════════ */

QScrollBar:vertical {
    background: transparent;
    width: 5px;
    border: none;
    margin: 4px 0;
}
QScrollBar::handle:vertical {
    background: rgba(255,255,255,0.08);
    min-height: 40px;
    border-radius: 2px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(124,108,247,0.4);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background: transparent;
    height: 5px;
    border: none;
    margin: 0 4px;
}
QScrollBar::handle:horizontal {
    background: rgba(255,255,255,0.08);
    min-width: 40px;
    border-radius: 2px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(124,108,247,0.4);
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}


/* ══════════════════════════════════════════════════
   TOOLTIP
   Yumuşak köşeler, mor kenarlık
   ══════════════════════════════════════════════════ */

QToolTip {
    background-color: #1c1e28;
    border: 1px solid rgba(124,108,247,0.3);
    border-radius: 10px;
    color: #e8eaed;
    padding: 8px 14px;
    font-size: 12px;
}

"""
