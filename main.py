"""
ComicEditor — Ana Uygulama
═══════════════════════════════════════════════════
Profesyonel Çizgi Roman Dizgi ve Çeviri Aracı
Premium Modern UI — v0.9

Geliştirici: Sefflex (https://github.com/Sefflex)
═══════════════════════════════════════════════════
"""
import sys
import os
import zipfile
import platform
import ctypes
import pickle

import cv2  # type: ignore
import numpy as np  # type: ignore
import easyocr  # type: ignore
from PIL import Image  # type: ignore
from deep_translator import GoogleTranslator  # type: ignore

from PyQt6.QtWidgets import (  # type: ignore
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QLabel, QPushButton, QTextEdit,
    QSpinBox, QFormLayout, QFileDialog, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QListWidgetItem,
    QProgressDialog, QMessageBox, QSlider, QCheckBox,
    QColorDialog, QScrollArea
)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QIcon, QPen, QColor, QBrush  # type: ignore
from PyQt6.QtCore import Qt, QSize, QRectF, QByteArray, QBuffer, QIODevice  # type: ignore
import rarfile  # type: ignore

# ── Proje modülleri ──
from utils import base_dir, get_font_path
from nodes import DraggableTextNode
from threads import AutoScanlationThread
from canvas import CanvasView
from dialogs import SettingsDialog
from components import CollapsibleSection, GlowButton
from styles import PREMIUM_DARK_THEME


class CizgiArsivApp(QMainWindow):
    """Ana uygulama penceresi — tüm UI ve iş mantığı burada."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ComicEditör — Profesyonel Çizgi Roman Dizgi ve Çeviri Aracı")
        self.resize(1440, 880)
        self.pages: list[dict] = []
        self.current_page_idx: int = -1
        self.active_node: DraggableTextNode | None = None
        self.analyzer_thread: AutoScanlationThread | None = None  # type: ignore
        self.progress_dialog: QProgressDialog | None = None
        self.settings: dict = {
            "engine": "Otomatik (Gemini > Google)",
            "api_key": "",
            "font": "Anime Ace (Manga)",
            "align": "Orta",
        }

        self._is_updating_panel = False

        # ── Uygulama İkonu ──
        icon_path = os.path.join(base_dir, "icon.jpg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setup_ui()
        self.apply_premium_theme()

        # ── Windows Koyu Başlık Çubuğu (DWM API) ──
        if platform.system() == "Windows":
            self._apply_windows_dark_titlebar()

    def _apply_windows_dark_titlebar(self):
        """Windows 10/11'de başlık çubuğunu koyu temaya çevirir (DWM API)."""
        try:
            hwnd = int(self.winId())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value), ctypes.sizeof(value)
            )
            # Başlık çubuğu rengini temanın ana arka planına ayarla
            DWMWA_CAPTION_COLOR = 35
            # #0d0e13 → RGB olarak: R=13, G=14, B=19 → COLORREF = 0x00130E0D
            caption_color = ctypes.c_int(0x00130E0D)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_CAPTION_COLOR,
                ctypes.byref(caption_color), ctypes.sizeof(caption_color)
            )
            # Başlık çubuğu metin rengini açık yap
            DWMWA_TEXT_COLOR = 36
            text_color = ctypes.c_int(0x00EDEAE8)  # #e8eaed
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_TEXT_COLOR,
                ctypes.byref(text_color), ctypes.sizeof(text_color)
            )
        except Exception:
            pass  # Eski Windows sürümlerinde sessizce geç

    # ═══════════════════════════════════════════════
    #  UI KURULUMU
    # ═══════════════════════════════════════════════

    def setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ═══════════════════ TOPBAR ═══════════════════
        topbar = QWidget()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(58)  # Daha ferah topbar
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(20, 0, 20, 0)
        tb.setSpacing(10)

        # Logo: İkon + Yazı
        logo_layout = QHBoxLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(8)
        logo_icon = QLabel()
        icon_path = os.path.join(base_dir, "icon.jpg")
        if os.path.exists(icon_path):
            logo_pix = QPixmap(icon_path).scaled(
                32, 32, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_icon.setPixmap(logo_pix)
        logo_icon.setFixedSize(34, 34)
        logo_icon.setObjectName("logoIcon")
        logo_text = QLabel("ComicEditör")
        logo_text.setObjectName("logoLabel")
        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(logo_text)
        logo_widget = QWidget()
        logo_widget.setLayout(logo_layout)

        btn_load = QPushButton("📂 Yükle")
        btn_load.clicked.connect(self.load_files)

        btn_load_proj = GlowButton("📥 Proje Aç", glow_color=QColor(124, 108, 247, 60))
        btn_load_proj.setObjectName("btnPrimary")
        btn_load_proj.clicked.connect(self.load_project)

        btn_save_proj = QPushButton("📤 Kaydet")
        btn_save_proj.setObjectName("btnSecondary")
        btn_save_proj.clicked.connect(self.save_project)

        btn_analyze = GlowButton("🚀 Tam Otonom Çıkart",
                                 glow_color=QColor(124, 108, 247, 80), glow_radius=28)
        btn_analyze.setObjectName("btnHero")
        btn_analyze.clicked.connect(self.run_auto_scanlation)

        btn_export = QPushButton("💾 PDF Çıkar")
        btn_export.clicked.connect(self.export_to_pdf)

        btn_settings = QPushButton("⚙️")
        btn_settings.setObjectName("btnIcon")
        btn_settings.setFixedSize(40, 40)
        btn_settings.clicked.connect(self.open_settings)

        tb.addWidget(logo_widget)
        tb.addSpacing(24)
        tb.addWidget(btn_load)
        tb.addWidget(btn_load_proj)
        tb.addWidget(btn_save_proj)
        tb.addSpacing(16)
        tb.addWidget(btn_analyze)
        tb.addStretch()
        tb.addWidget(btn_export)
        tb.addWidget(btn_settings)
        main_layout.addWidget(topbar)

        # ═══════════════════ BODY ═══════════════════
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(12, 10, 12, 12)  # Daha ferah kenar boşlukları
        body_layout.setSpacing(12)  # Paneller arası daha fazla boşluk

        # ─────── LEFT SIDEBAR ───────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)  # Daha geniş sidebar
        sidebar_lay = QVBoxLayout(sidebar)
        sidebar_lay.setContentsMargins(14, 16, 14, 16)  # Ferah iç padding
        sidebar_lay.setSpacing(10)

        lbl_pages = QLabel("SAYFALAR")
        lbl_pages.setObjectName("sectionTitle")
        lbl_pages.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.page_list = QListWidget()
        self.page_list.setIconSize(QSize(100, 150))
        self.page_list.itemClicked.connect(self.on_page_selected)

        left_footer = QLabel(
            'v0.9 · <a href="https://github.com/Sefflex" '
            'style="color: #7c6cf7; text-decoration: none;">Sefflex</a>'
        )
        left_footer.setOpenExternalLinks(True)
        left_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_footer.setObjectName("footerLabel")

        sidebar_lay.addWidget(lbl_pages)
        sidebar_lay.addWidget(self.page_list)
        sidebar_lay.addWidget(left_footer)

        # ─────── CENTER (Canvas + Toolbar) ───────
        center = QWidget()
        center_lay = QVBoxLayout(center)
        center_lay.setContentsMargins(0, 0, 0, 0)
        center_lay.setSpacing(10)  # Canvas ile toolbar arası boşluk

        self.canvas = CanvasView(self)
        center_lay.addWidget(self.canvas, 1)

        # Alt araç çubuğu
        toolbar = QWidget()
        toolbar.setObjectName("toolStrip")
        toolbar.setFixedHeight(50)  # Daha ferah toolbar
        tool_lay = QHBoxLayout(toolbar)
        tool_lay.setContentsMargins(16, 0, 16, 0)
        tool_lay.setSpacing(8)

        self.btn_paint = QPushButton("🖌️ Fırça")
        self.btn_paint.setCheckable(True)
        self.btn_paint.setObjectName("btnTool")
        self.btn_paint.clicked.connect(self.toggle_paint_mode)

        self.btn_fill = QPushButton("🔲 Kapla")
        self.btn_fill.setCheckable(True)
        self.btn_fill.setObjectName("btnTool")
        self.btn_fill.clicked.connect(self.toggle_fill_mode)

        self.btn_picker = QPushButton("💧 Damlalık")
        self.btn_picker.setCheckable(True)
        self.btn_picker.setObjectName("btnTool")
        self.btn_picker.clicked.connect(self.toggle_picker_mode)

        sep_label = QLabel("│")
        sep_label.setStyleSheet("color: rgba(255,255,255,0.08); font-size: 18px;")

        self.spin_brush = QSpinBox()
        self.spin_brush.setRange(2, 200)
        self.spin_brush.setValue(15)
        self.spin_brush.setPrefix("⌀ ")
        self.spin_brush.valueChanged.connect(self.update_brush_size)

        self.lbl_current_color = QLabel()
        self.lbl_current_color.setFixedSize(26, 26)
        self.lbl_current_color.setStyleSheet(
            "background-color: #ffffff; border: 2px solid rgba(255,255,255,0.08); border-radius: 13px;"
        )

        self.btn_reset = QPushButton("🔄 Sıfırla")
        self.btn_reset.setObjectName("btnDanger")
        self.btn_reset.clicked.connect(self.reset_current_page)

        self.btn_add_text = QPushButton("➕ Yazı Ekle")
        self.btn_add_text.clicked.connect(self.add_manual_text)

        self.btn_toggle = QPushButton("👁️ Orijinali Gör")
        self.btn_toggle.clicked.connect(self.toggle_original_view)

        tool_lay.addWidget(self.btn_paint)
        tool_lay.addWidget(self.btn_fill)
        tool_lay.addWidget(self.btn_picker)
        tool_lay.addWidget(sep_label)
        tool_lay.addWidget(self.spin_brush)
        tool_lay.addWidget(self.lbl_current_color)
        tool_lay.addStretch()
        tool_lay.addWidget(self.btn_add_text)
        tool_lay.addWidget(self.btn_toggle)
        tool_lay.addWidget(self.btn_reset)

        center_lay.addWidget(toolbar)

        # ─────── RIGHT PROPERTIES PANEL ───────
        right_scroll = QScrollArea()
        right_scroll.setObjectName("propertiesScroll")
        right_scroll.setWidgetResizable(True)
        right_scroll.setFixedWidth(320)  # Daha geniş özellik paneli
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        right = QWidget()
        right.setObjectName("propertiesPanel")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(16, 16, 16, 16)  # Ferah iç padding
        right_lay.setSpacing(8)

        panel_title = QLabel("🎛️  ÖZELLİKLER")
        panel_title.setObjectName("panelTitle")
        right_lay.addWidget(panel_title)
        right_lay.addSpacing(6)

        # ── Section: Metin ──
        sec_text = CollapsibleSection("📝  Metin")
        lbl_orig = QLabel("Orijinal İbare:")
        lbl_orig.setObjectName("fieldLabel")
        self.txt_original = QTextEdit()
        self.txt_original.setPlaceholderText("Orijinal metin...")
        self.txt_original.setMinimumHeight(55)
        self.txt_original.setMaximumHeight(90)
        self.txt_original.textChanged.connect(self.on_panel_changed)

        lbl_tr = QLabel("Çeviri:")
        lbl_tr.setObjectName("fieldLabel")
        self.txt_translated = QTextEdit()
        self.txt_translated.setPlaceholderText("Çeviri içeriği...")
        self.txt_translated.setMinimumHeight(65)
        self.txt_translated.setMaximumHeight(110)
        self.txt_translated.textChanged.connect(self.on_panel_changed)

        sec_text.addWidget(lbl_orig)
        sec_text.addWidget(self.txt_original)
        sec_text.addWidget(lbl_tr)
        sec_text.addWidget(self.txt_translated)
        right_lay.addWidget(sec_text)

        # ── Section: Stil ──
        sec_style = CollapsibleSection("🎨  Stil")
        style_form = QFormLayout()
        style_form.setSpacing(12)
        style_form.setContentsMargins(0, 0, 0, 0)

        self.btn_color_text = QPushButton("  Siyah")
        self.btn_color_text.setObjectName("colorBtn")
        self.btn_color_text.clicked.connect(self.choose_text_color)

        self.btn_color_stroke = QPushButton("  Beyaz")
        self.btn_color_stroke.setObjectName("colorBtn")
        self.btn_color_stroke.clicked.connect(self.choose_stroke_color)

        self.chk_stroke = QCheckBox("Dış Çizgi Göster")
        self.chk_stroke.setChecked(True)
        self.chk_stroke.stateChanged.connect(self.on_panel_changed)

        self.chk_bold = QCheckBox("Kalın (Bold)")
        self.chk_bold.stateChanged.connect(self.on_panel_changed)

        style_form.addRow("Yazı Rengi:", self.btn_color_text)
        style_form.addRow("Dış Çizgi:", self.btn_color_stroke)
        sec_style.addLayout(style_form)
        sec_style.addWidget(self.chk_stroke)
        sec_style.addWidget(self.chk_bold)
        right_lay.addWidget(sec_style)

        # ── Section: Boyut ──
        sec_size = CollapsibleSection("📐  Boyut")
        size_form = QFormLayout()
        size_form.setSpacing(12)
        size_form.setContentsMargins(0, 0, 0, 0)

        self.spin_size = QSpinBox()
        self.spin_size.setRange(8, 200)
        self.spin_size.valueChanged.connect(self.on_panel_changed)

        self.slider_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_width.setRange(50, 800)
        self.slider_width.valueChanged.connect(self.on_panel_changed)

        self.slider_height = QSlider(Qt.Orientation.Horizontal)
        self.slider_height.setRange(50, 800)
        self.slider_height.valueChanged.connect(self.on_panel_changed)

        size_form.addRow("Font:", self.spin_size)
        size_form.addRow("Genişlik:", self.slider_width)
        size_form.addRow("Yükseklik:", self.slider_height)
        sec_size.addLayout(size_form)
        right_lay.addWidget(sec_size)

        # ── Section: Araçlar ──
        sec_tools = CollapsibleSection("🔧  Araçlar")
        self.btn_save_preset = GlowButton("💾 Ön Ayar Kaydet",
                                          glow_color=QColor(124, 108, 247, 50))
        self.btn_save_preset.setObjectName("btnPrimary")
        self.btn_save_preset.clicked.connect(self.save_text_preset)

        btn_tr = QPushButton("⭐ Sadece Metni Çevir")
        btn_tr.setObjectName("btnSecondary")
        btn_tr.clicked.connect(self.translate_selected_node)

        self.btn_ocr = QPushButton("🔍 Seçerek Oku && Yeni Kutu Ekle")
        self.btn_ocr.setCheckable(True)
        self.btn_ocr.setObjectName("btnSuccess")
        self.btn_ocr.clicked.connect(self.toggle_ocr_mode)

        sec_tools.addWidget(self.btn_save_preset)
        sec_tools.addWidget(btn_tr)
        sec_tools.addWidget(self.btn_ocr)
        right_lay.addWidget(sec_tools)

        right_lay.addStretch()

        tip = QLabel("💡 Yazıları sürükleyin · Backspace ile silin · Ctrl+Z geri alın")
        tip.setWordWrap(True)
        tip.setObjectName("tipLabel")
        right_lay.addWidget(tip)

        right_scroll.setWidget(right)

        # ═══════════════════ ASSEMBLE ═══════════════════
        body_layout.addWidget(sidebar)
        body_layout.addWidget(center, 1)
        body_layout.addWidget(right_scroll)
        main_layout.addWidget(body, 1)

    # ═══════════════════════════════════════════════
    #  TEMA UYGULAMA
    # ═══════════════════════════════════════════════

    def apply_premium_theme(self):
        """Premium karanlık temayı uygular."""
        self.setStyleSheet(PREMIUM_DARK_THEME)

    # ═══════════════════════════════════════════════
    #  AYARLAR
    # ═══════════════════════════════════════════════

    def open_settings(self):
        d = SettingsDialog(self, self.settings)
        if d.exec():
            self.settings = d.get_settings()

    # ═══════════════════════════════════════════════
    #  SAYFA SIFIRLAMA
    # ═══════════════════════════════════════════════

    def reset_current_page(self):
        if self.current_page_idx == -1:
            return
        reply = QMessageBox.question(
            self, "Sayfayı Sıfırla",
            "Bu sayfadaki yapılan tüm değişiklikleri (yazılar, boyamalar, çeviriler) "
            "sıfırlamak istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            page = self.pages[self.current_page_idx]
            original_qpix = page["qpix"]
            page["clean_qpix"] = original_qpix.copy()
            page["bg_item"].setPixmap(original_qpix)

            for item in page["scene"].items():
                if isinstance(item, DraggableTextNode):
                    page["scene"].removeItem(item)
            self.active_node = None
            page["undo_stack"] = []
            page["is_showing_original"] = False
            self.btn_toggle.setText("👁️ Orijinali Gör")
            self.btn_toggle.setStyleSheet("")
            self.clear_right_panel()

    # ═══════════════════════════════════════════════
    #  DOSYA YÜKLEME
    # ═══════════════════════════════════════════════

    def load_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Dosya Seç", "",
            "Resim / PDF / ÇizgiRoman (*.cbz *.cbr *.pdf *.png *.jpg *.jpeg) ;; "
            "CBZ/CBR (*.cbr *.cbz) ;; PDF (*.pdf)"
        )
        if not files:
            return
        self.progress_dialog = QProgressDialog("Okunuyor...", "İptal", 0, 0, self)
        self.progress_dialog.show()  # type: ignore
        for f in files:
            ext = f.lower().split('.')[-1]
            if ext == 'pdf':
                self.load_pdf(f)
            elif ext in ['cbz', 'cbr']:
                self.load_cbz(f)
            else:
                self.load_img(f)
        dlg = self.progress_dialog
        if dlg is not None:
            dlg.close()

    def load_pdf(self, path):
        import fitz  # type: ignore
        try:
            doc = fitz.open(path)
            fn = path.split('/')[-1]
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=300)
                fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
                qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
                self.add_page(QPixmap.fromImage(qimg), f"{fn} - {i+1}")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def load_cbz(self, path):
        fn = path.split('/')[-1]
        try:
            with zipfile.ZipFile(path, 'r') as z:
                for name in sorted(z.namelist()):
                    if name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        self.add_page(
                            QPixmap.fromImage(QImage.fromData(z.read(name))),
                            f"{fn} - {name.split('/')[-1]}"
                        )
            return
        except Exception:
            pass
        try:
            with rarfile.RarFile(path, 'r') as r:
                for name in sorted(r.namelist()):
                    if name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        self.add_page(
                            QPixmap.fromImage(QImage.fromData(r.read(name))),
                            f"{fn} - {name.split('/')[-1]}"
                        )
        except Exception:
            QMessageBox.warning(
                self, "CBR Hata",
                "Rar bozuk. Dosyayı klasik Zip yaparak deneyin."
            )

    def load_img(self, path):
        qpix = QPixmap(path)
        if not qpix.isNull():
            self.add_page(qpix, path.split('/')[-1])

    def add_page(self, qpix, title):
        scene = QGraphicsScene()
        scene.setSceneRect(QRectF(qpix.rect()))
        bg = QGraphicsPixmapItem(qpix)
        bg.setZValue(-100)
        scene.addItem(bg)

        self.pages.append({
            "qpix": qpix, "scene": scene, "title": title,
            "bg_item": bg, "clean_qpix": qpix.copy(), "undo_stack": []
        })

        thumb = qpix.scaled(100, 150, Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation)
        item = QListWidgetItem(QIcon(thumb), title)
        item.setData(Qt.ItemDataRole.UserRole, len(self.pages) - 1)
        self.page_list.addItem(item)
        if len(self.pages) == 1:
            self.on_page_selected(item)

    # ═══════════════════════════════════════════════
    #  PROJE KAYDET / YÜKLE
    # ═══════════════════════════════════════════════

    def get_pixmap_bytes(self, qpix: QPixmap) -> bytes:
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        qpix.save(buf, "PNG")
        return ba.data()  # type: ignore

    def bytes_to_pixmap(self, data: bytes) -> QPixmap:
        qpix = QPixmap()
        qpix.loadFromData(data, "PNG")
        return qpix

    def save_project(self):
        if not self.pages:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Projeyi Kaydet", "Calisma_1.comicproj",
            "ComicEditör Projesi (*.comicproj)"
        )
        if not path:
            return

        self.progress_dialog = QProgressDialog("Proje Paketleniyor...", "İptal", 0, 0, self)
        dlg = self.progress_dialog
        if dlg:
            dlg.show()
        QApplication.processEvents()

        pages_list = []
        for page in self.pages:
            nodes_list = []
            for item in page["scene"].items():
                if isinstance(item, DraggableTextNode):
                    node_data = {
                        "rect_data": item.rect_data,
                        "is_auto": item.is_auto,
                        "font_size": item.font_size,
                        "box_w": item.box_w,
                        "box_h": item.box_h,
                        "align": item.align,
                        "is_bold": item.is_bold,
                        "has_stroke": getattr(item, 'has_stroke', True),
                        "text_color": item.text_color,
                        "stroke_color": item.stroke_color,
                        "pos_x": item.pos().x(),
                        "pos_y": item.pos().y(),
                    }
                    nodes_list.append(node_data)

            p_data = {
                "title": page["title"],
                "qpix": self.get_pixmap_bytes(page["qpix"]),
                "clean_qpix": self.get_pixmap_bytes(page.get("clean_qpix", page["qpix"])),
                "nodes": nodes_list,
            }
            pages_list.append(p_data)

        project_data = {"pages": pages_list, "settings": self.settings}

        try:
            with open(path, 'wb') as f:
                pickle.dump(project_data, f)
            if dlg:
                dlg.close()
            QMessageBox.information(
                self, "Başarılı",
                "Proje başarıyla kaydedildi! İleride 'Proje Aç' diyerek "
                "kaldığınız yerden devam edebilirsiniz."
            )
        except Exception as e:
            if dlg:
                dlg.close()
            QMessageBox.critical(self, "Hata", f"Proje kaydedilemedi: {e}")

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Proje Aç", "", "ComicEditör Projesi (*.comicproj)"
        )
        if not path:
            return

        self.progress_dialog = QProgressDialog("Proje Yükleniyor...", "İptal", 0, 0, self)
        dlg = self.progress_dialog
        if dlg:
            dlg.show()
        QApplication.processEvents()

        try:
            with open(path, 'rb') as f:
                project_data = pickle.load(f)

            self.settings = project_data.get("settings", self.settings)
            self.pages.clear()
            self.page_list.clear()
            self.active_node = None
            self.clear_right_panel()

            fpath = get_font_path(str(self.settings.get("font", "Anime Ace")))

            for p_data in project_data.get("pages", []):
                qpix = self.bytes_to_pixmap(p_data["qpix"])
                clean_qpix = self.bytes_to_pixmap(p_data["clean_qpix"])

                scene = QGraphicsScene()
                scene.setSceneRect(QRectF(qpix.rect()))
                bg = QGraphicsPixmapItem(clean_qpix)
                bg.setZValue(-100)
                scene.addItem(bg)

                page_dict = {
                    "qpix": qpix, "scene": scene, "title": p_data["title"],
                    "bg_item": bg, "clean_qpix": clean_qpix, "undo_stack": []
                }
                self.pages.append(page_dict)

                thumb = qpix.scaled(100, 150, Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
                item = QListWidgetItem(QIcon(thumb), p_data["title"])
                item.setData(Qt.ItemDataRole.UserRole, len(self.pages) - 1)
                self.page_list.addItem(item)

                for nd in p_data.get("nodes", []):
                    node = DraggableTextNode(
                        nd["rect_data"], self, nd["font_size"], fpath,
                        nd["align"], nd["is_auto"]
                    )
                    node.box_w = nd["box_w"]
                    node.box_h = nd["box_h"]
                    node.is_bold = nd["is_bold"]
                    node.has_stroke = nd.get("has_stroke", True)
                    node.text_color = nd["text_color"]
                    node.stroke_color = nd["stroke_color"]
                    node._initialized = True
                    node.update_visual()
                    node.setPos(nd["pos_x"], nd["pos_y"])
                    scene.addItem(node)

            if len(self.pages) > 0:
                self.on_page_selected(self.page_list.item(0))

            if dlg:
                dlg.close()
            QMessageBox.information(
                self, "Başarılı",
                "Proje başarıyla yüklendi. Nerede kaldıysak oradan devam!"
            )
        except Exception as e:
            if dlg:
                dlg.close()
            QMessageBox.critical(
                self, "Hata",
                f"Proje dosyası okunamadı veya bozuk: {e}"
            )

    # ═══════════════════════════════════════════════
    #  SAYFA SEÇİMİ & PANEL YÖNETİMİ
    # ═══════════════════════════════════════════════

    def on_page_selected(self, item):
        self.current_page_idx = int(item.data(Qt.ItemDataRole.UserRole))
        scene = self.pages[self.current_page_idx]["scene"]
        self.canvas.setScene(scene)
        self.canvas.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.active_node = None
        self.clear_right_panel()

    def clear_right_panel(self):
        self._is_updating_panel = True
        self.txt_original.clear()
        self.txt_translated.clear()
        self.spin_size.setValue(14)
        self.slider_width.setValue(100)
        self._is_updating_panel = False

    # ═══════════════════════════════════════════════
    #  RENK SEÇİMİ
    # ═══════════════════════════════════════════════

    def choose_text_color(self):
        node = self.active_node
        if node is None:
            return
        color = QColorDialog.getColor(initial=QColor(*node.text_color[:3]), parent=self)
        if color.isValid():
            node.text_color = (color.red(), color.green(), color.blue(), 255)
            self.on_node_selected(node)
            node.update_visual()

    def choose_stroke_color(self):
        node = self.active_node
        if node is None:
            return
        color = QColorDialog.getColor(initial=QColor(*node.stroke_color[:3]), parent=self)
        if color.isValid():
            node.stroke_color = (color.red(), color.green(), color.blue(), 255)
            self.on_node_selected(node)
            node.update_visual()

    # ═══════════════════════════════════════════════
    #  DÜĞÜM SEÇİMİ & PANEL GÜNCELLEMESİ
    # ═══════════════════════════════════════════════

    def on_node_selected(self, node: DraggableTextNode):
        self.active_node = node
        self._is_updating_panel = True
        self.txt_original.setPlainText(node.original_text)
        self.txt_translated.setPlainText(node.translated_text)
        self.spin_size.setValue(node.font_size)
        self.slider_width.setValue(int(node.box_w))
        self.slider_height.setValue(int(node.box_h))
        self.chk_bold.setChecked(node.is_bold)
        self.chk_stroke.setChecked(getattr(node, 'has_stroke', True))
        # Renk butonları — yeni tema ile uyumlu stiller
        self.btn_color_text.setStyleSheet(
            f"background-color: rgb({node.text_color[0]},{node.text_color[1]},{node.text_color[2]}); "
            f"color: white; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); "
            f"padding: 9px 14px;"
        )
        self.btn_color_stroke.setStyleSheet(
            f"background-color: rgb({node.stroke_color[0]},{node.stroke_color[1]},{node.stroke_color[2]}); "
            f"color: black; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); "
            f"padding: 9px 14px;"
        )
        self._is_updating_panel = False

    def on_panel_changed(self):
        if self._is_updating_panel:
            return
        node = self.active_node
        if node is None:
            return
        node.original_text = self.txt_original.toPlainText()
        node.translated_text = self.txt_translated.toPlainText()
        node.rect_data["text"] = node.original_text
        node.rect_data["translated_text"] = node.translated_text
        node.is_auto = False
        node.font_size = self.spin_size.value()
        node.box_w = self.slider_width.value()
        node.box_h = self.slider_height.value()
        node.is_bold = self.chk_bold.isChecked()
        node.has_stroke = self.chk_stroke.isChecked()
        node.update_visual()

    # ═══════════════════════════════════════════════
    #  ÖN AYAR KAYDET
    # ═══════════════════════════════════════════════

    def save_text_preset(self):
        node = self.active_node
        if node is None:
            return
        self.settings["preset"] = {
            "font_size": node.font_size,
            "text_color": node.text_color,
            "stroke_color": node.stroke_color,
            "is_bold": node.is_bold,
            "has_stroke": getattr(node, 'has_stroke', True),
            "box_w": node.box_w,
            "box_h": node.box_h,
        }
        QMessageBox.information(
            self, "Ön Ayar Kaydedildi",
            "Yeni eklenecek yazılar ve OCR okumaları artık bu boyutta, "
            "bu renkte ve bu formatta çıkacak!"
        )

    # ═══════════════════════════════════════════════
    #  ORİJİNAL GÖRÜNÜM
    # ═══════════════════════════════════════════════

    def toggle_original_view(self):
        if self.current_page_idx == -1:
            return
        page = self.pages[self.current_page_idx]
        if "clean_qpix" not in page:
            return

        if not page.get("is_showing_original", False):
            page["bg_item"].setPixmap(page["qpix"])
            for item in page["scene"].items():
                if isinstance(item, DraggableTextNode):
                    item.hide()
            page["is_showing_original"] = True
            self.btn_toggle.setText("👁️ Çeviriye Dön")
            self.btn_toggle.setStyleSheet(
                "background-color: qlineargradient("
                "x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:1 #2dd4bf);"
                "color: white; font-weight: bold; "
                "border: 1px solid rgba(52,211,153,0.3); border-radius: 12px;"
            )
        else:
            page["bg_item"].setPixmap(page["clean_qpix"])
            for item in page["scene"].items():
                if isinstance(item, DraggableTextNode):
                    item.show()
            page["is_showing_original"] = False
            self.btn_toggle.setText("👁️ Orijinali Gör")
            self.btn_toggle.setStyleSheet("")

    # ═══════════════════════════════════════════════
    #  MANUEL YAZI EKLEME
    # ═══════════════════════════════════════════════

    def add_manual_text(self):
        if self.current_page_idx == -1:
            return
        page = self.pages[self.current_page_idx]
        scene = page["scene"]

        view_rect = self.canvas.mapToScene(self.canvas.viewport().rect()).boundingRect()
        cx, cy = view_rect.center().x(), view_rect.center().y()
        w, h = 150, 150

        rect_data = {
            "rect": (int(cx - w / 2), int(cy - h / 2), w, h),
            "text": "",
            "translated_text": "YENİ YAZI",
        }
        global_font = 26

        fpath = get_font_path(str(self.settings.get("font", "Anime Ace")))
        align_str = str(self.settings.get("align", "Orta")).lower()
        align_pil = "center" if align_str == "orta" else "right" if align_str == "sağ" else "left"

        node = DraggableTextNode(rect_data, self, global_font, fpath, align_pil, is_auto=False)
        if "preset" in self.settings:
            pr = self.settings["preset"]
            node.font_size = pr["font_size"]
            node.text_color = pr["text_color"]
            node.stroke_color = pr["stroke_color"]
            node.is_bold = pr["is_bold"]
            node.has_stroke = pr["has_stroke"]
            if "box_w" in pr:
                node.box_w = pr["box_w"]
            if "box_h" in pr:
                node.box_h = pr["box_h"]
            node.update_visual()

        scene.addItem(node)
        scene.clearSelection()
        node.setSelected(True)
        self.on_node_selected(node)

    # ═══════════════════════════════════════════════
    #  BÖLGESEL OCR
    # ═══════════════════════════════════════════════

    def run_rect_ocr(self, rect: QRectF):
        if self.current_page_idx == -1:
            return
        page = self.pages[self.current_page_idx]
        if "qpix" not in page:
            return

        qim = page["qpix"].toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        w, h = qim.width(), qim.height()
        ptr = qim.constBits()
        ptr.setsize(h * w * 4)
        arr = np.array(ptr).reshape((h, w, 4))
        img_bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)

        x1, y1 = max(0, int(rect.left())), max(0, int(rect.top()))
        x2, y2 = min(w, int(rect.right())), min(h, int(rect.bottom()))
        if x2 <= x1 or y2 <= y1:
            return

        crop = img_bgr[y1:y2, x1:x2]

        self.progress_dialog = QProgressDialog("Bölge Tanınıyor...", "İptal", 0, 0, self)
        self.progress_dialog.show()  # type: ignore
        QApplication.processEvents()

        try:
            reader = easyocr.Reader(['en'], gpu=True)
        except Exception:
            reader = easyocr.Reader(['en'], gpu=False)

        ocr_results = reader.readtext(crop, paragraph=True, text_threshold=0.3, mag_ratio=2.0)

        if self.progress_dialog:
            self.progress_dialog.close()

        if not ocr_results:
            QMessageBox.warning(self, "Bulunamadı", "Seçili bölgede metin algılanamadı.")
            return

        combined_text = " ".join([res[1] for res in ocr_results]).strip()

        rect_data = {
            "rect": (x1, y1, x2 - x1, y2 - y1),
            "text": combined_text,
            "translated_text": "",
        }
        global_font = int(h * 0.016)
        if global_font > 100:
            global_font = 100
        if global_font < 14:
            global_font = 14

        fpath = get_font_path(str(self.settings.get("font", "Anime Ace")))
        align_str = str(self.settings.get("align", "Orta")).lower()
        align_pil = "center" if align_str == "orta" else "right" if align_str == "sağ" else "left"

        node = DraggableTextNode(rect_data, self, global_font, fpath, align_pil, is_auto=False)
        if "preset" in self.settings:
            pr = self.settings["preset"]
            node.font_size = pr["font_size"]
            node.text_color = pr["text_color"]
            node.stroke_color = pr["stroke_color"]
            node.is_bold = pr["is_bold"]
            node.has_stroke = pr["has_stroke"]
            if "box_w" in pr:
                node.box_w = pr["box_w"]
            if "box_h" in pr:
                node.box_h = pr["box_h"]
            node.update_visual()

        page["scene"].addItem(node)
        page["scene"].clearSelection()
        node.setSelected(True)
        self.on_node_selected(node)

        self.translate_selected_node()

    # ═══════════════════════════════════════════════
    #  TAM OTONOM SCANLATION
    # ═══════════════════════════════════════════════

    def run_auto_scanlation(self):
        if self.current_page_idx == -1:
            return
        page = self.pages[self.current_page_idx]
        qpix = page["qpix"]

        self.progress_dialog = QProgressDialog(
            "Gelişmiş Yapay Zeka Katmanları Başladı...", "İptal", 0, 0, self
        )
        self.progress_dialog.show()  # type: ignore

        self.analyzer_thread = AutoScanlationThread(qpix.toImage(), self.settings)
        if self.analyzer_thread:
            self.analyzer_thread.progress.connect(
                lambda m: self.progress_dialog.setLabelText(m) if self.progress_dialog else None
            )  # type: ignore
            self.analyzer_thread.finished.connect(self.on_auto_scanlation_finished)  # type: ignore
            self.analyzer_thread.start()  # type: ignore

    def on_auto_scanlation_finished(self, out_data):
        dlg = self.progress_dialog
        if dlg is not None:
            dlg.close()
        cleaned_rgb, results = out_data

        height, width, _ = cleaned_rgb.shape
        bytes_line = 3 * width
        qim = QImage(
            cleaned_rgb.data.tobytes(), width, height, bytes_line,
            QImage.Format.Format_RGB888
        ).copy()
        new_qpix = QPixmap.fromImage(qim)

        page = self.pages[self.current_page_idx]
        page["bg_item"].setPixmap(new_qpix)
        page["clean_qpix"] = new_qpix

        scene = page["scene"]
        for it in scene.items():
            if isinstance(it, DraggableTextNode):
                scene.removeItem(it)

        global_font = int(height * 0.016)
        if global_font > 100:
            global_font = 100
        if global_font < 14:
            global_font = 14

        fpath = get_font_path(str(self.settings.get("font", "Anime Ace")))
        align_str = str(self.settings.get("align", "Orta")).lower()
        align_pil = "center" if align_str == "orta" else "right" if align_str == "sağ" else "left"

        for res in results:
            node = DraggableTextNode(res, self, global_font, fpath, align_pil, is_auto=True)
            scene.addItem(node)

    # ═══════════════════════════════════════════════
    #  TEKİL ÇEVİRİ
    # ═══════════════════════════════════════════════

    def translate_selected_node(self):
        if not self.active_node:
            return
        text = self.txt_original.toPlainText().strip()
        if not text:
            return
        api = self.settings.get("api_key", "").strip()
        try:
            if api:
                import google.generativeai as genai  # type: ignore
                genai.configure(api_key=api)
                m = genai.GenerativeModel('gemini-1.5-flash')
                response = m.generate_content(("Çevir:\n" + text))
                tr = response.text.strip()
            else:
                tr = str(GoogleTranslator(source='en', target='tr').translate(text))
            self.txt_translated.setPlainText(tr)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    # ═══════════════════════════════════════════════
    #  PDF ÇIKARMA
    # ═══════════════════════════════════════════════

    def export_to_pdf(self):
        if not self.pages:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "PDF Olarak Kaydet", "Hikaye_Full.pdf", "PDF Dosyası (*.pdf)"
        )
        if not path:
            return

        for page in self.pages:
            if page.get("is_showing_original", False):
                page["bg_item"].setPixmap(page.get("clean_qpix", page["qpix"]))
                for item in page["scene"].items():
                    if isinstance(item, DraggableTextNode):
                        item.show()
                page["is_showing_original"] = False
        self.btn_toggle.setText("👁️ Orijinali Gör")
        self.btn_toggle.setStyleSheet("")

        self.progress_dialog = QProgressDialog(
            "Final Render... Yazılar Katmana Gömülüyor...", "İptal",
            0, len(self.pages), self
        )
        dlg2 = self.progress_dialog
        if dlg2 is not None:
            dlg2.show()

        pil_images = []
        for i, page in enumerate(self.pages):
            scene = page["scene"]
            rect = scene.sceneRect()
            img = QImage(rect.size().toSize(), QImage.Format.Format_RGB32)
            img.fill(Qt.GlobalColor.white)
            painter = QPainter(img)
            scene.render(painter)
            painter.end()

            w, h = img.width(), img.height()
            ptr = img.constBits()
            ptr.setsize(h * w * 4)
            arr = np.array(ptr).reshape((h, w, 4))
            img_bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
            pil_images.append(Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)))
            if self.progress_dialog is not None:
                self.progress_dialog.setValue(i + 1)

        if len(pil_images) > 0:
            try:
                pil_images[0].save(
                    path, "PDF", resolution=300, save_all=True,
                    append_images=pil_images[1:]
                )  # type: ignore
                QMessageBox.information(self, "Başarılı", "Matbaa Kalitesinde Yayınlandı!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    # ═══════════════════════════════════════════════
    #  ARAÇ MODLARI
    # ═══════════════════════════════════════════════

    def update_brush_size(self, val: int):
        self.canvas.brush_size = val

    def toggle_paint_mode(self, checked: bool):
        self.canvas.paint_mode = checked
        if checked:
            self.canvas.picker_mode = False
            self.canvas.fill_mode = False
            self.canvas.select_mode = False
            self.btn_picker.setChecked(False)
            self.btn_fill.setChecked(False)
            self.btn_ocr.setChecked(False)
            self.canvas.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.canvas.scene().clearSelection()
            self.active_node = None
        else:
            self.canvas.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def toggle_fill_mode(self, checked: bool):
        self.canvas.fill_mode = checked
        if checked:
            self.canvas.picker_mode = False
            self.canvas.paint_mode = False
            self.canvas.select_mode = False
            self.btn_picker.setChecked(False)
            self.btn_paint.setChecked(False)
            self.btn_ocr.setChecked(False)
            self.canvas.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.canvas.scene().clearSelection()
            self.active_node = None
        else:
            self.canvas.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def toggle_picker_mode(self, checked: bool):
        self.canvas.picker_mode = checked
        if checked:
            self.canvas.paint_mode = False
            self.canvas.fill_mode = False
            self.canvas.select_mode = False
            self.btn_paint.setChecked(False)
            self.btn_fill.setChecked(False)
            self.btn_ocr.setChecked(False)
            self.canvas.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.canvas.scene().clearSelection()
            self.active_node = None
        else:
            if not self.btn_paint.isChecked() and not self.btn_fill.isChecked() and not self.btn_ocr.isChecked():
                self.canvas.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def toggle_ocr_mode(self, checked: bool):
        self.canvas.select_mode = checked
        if checked:
            self.canvas.picker_mode = False
            self.canvas.paint_mode = False
            self.canvas.fill_mode = False
            self.btn_picker.setChecked(False)
            self.btn_paint.setChecked(False)
            self.btn_fill.setChecked(False)
            self.canvas.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.canvas.scene().clearSelection()
            self.active_node = None
        else:
            if not self.btn_paint.isChecked() and not self.btn_fill.isChecked() and not self.btn_picker.isChecked():
                self.canvas.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)


# ═══════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CizgiArsivApp()
    window.show()
    sys.exit(app.exec())
