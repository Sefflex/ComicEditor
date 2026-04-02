import sys
import os
import fitz  # type: ignore
import cv2  # type: ignore
import numpy as np  # type: ignore
import easyocr  # type: ignore
import ssl
from PIL import Image, ImageDraw, ImageFont  # type: ignore
import textwrap
import zipfile
import rarfile  # type: ignore
import platform
import pickle
from PyQt6.QtCore import QByteArray, QBuffer, QIODevice  # type: ignore
from deep_translator import GoogleTranslator  # type: ignore

base_dir = os.path.dirname(os.path.abspath(__file__))

if platform.system() == "Darwin":
    if platform.machine() == "arm64":
        rarfile.UNRAR_TOOL = os.path.join(base_dir, "unrar_mac_arm", "unrar")
    else:
        rarfile.UNRAR_TOOL = os.path.join(base_dir, "unrar_mac_intel", "unrar")
elif platform.system() == "Windows":
    rarfile.UNRAR_TOOL = os.path.join(base_dir, "unrar_windows", "unrar.exe")

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

from PyQt6.QtWidgets import (  # type: ignore
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QListWidget, QLabel, QPushButton, QTextEdit,
    QComboBox, QSpinBox, QFormLayout, QFrame, QFileDialog, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem, QListWidgetItem,
    QProgressDialog, QMessageBox, QLineEdit, QDialog, QDialogButtonBox,
    QSlider, QCheckBox, QColorDialog, QScrollArea
)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QIcon, QPen, QColor, QBrush  # type: ignore
from PyQt6.QtCore import Qt, QSize, QRectF, QThread, pyqtSignal  # type: ignore

def get_font_path(font_name: str) -> str:
    if "Patrick Hand" in font_name:
        return os.path.join(base_dir, "fonts", "PatrickHand.ttf")
    if "Comic Neue" in font_name:
        return os.path.join(base_dir, "fonts", "comic.ttf")

    font_map = {"Arial": "Arial.ttf", "Comic Sans MS": "Comic Sans MS.ttf", "Impact": "Impact.ttf", "Times New Roman": "Times New Roman.ttf"}
    return font_map.get(font_name, "Arial.ttf")

class DraggableTextNode(QGraphicsPixmapItem):
    def __init__(self, rect_data: dict, main_app, global_font_size, font_path, align, is_auto=True):
        super().__init__()
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.main_app = main_app
        self.rect_data = rect_data

        self.original_text = rect_data.get("text", "")
        self.translated_text = rect_data.get("translated_text", "")
        self.font_path = font_path
        self.align = align

        self.box_w = max(50, rect_data["rect"][2])
        self.box_h = rect_data["rect"][3]

        self.is_auto = is_auto
        self.font_size = global_font_size
        self.text_color = (0, 0, 0, 255)
        self.stroke_color = (255, 255, 255, 255)
        self.is_bold = False
        self._initialized = False

        self.update_visual()

    def update_visual(self):
        text = self.translated_text.replace("i", "İ").replace("ı", "I").upper()
        if not text:
            self.setPixmap(QPixmap())
            return

        dummy_img = Image.new('RGBA', (1,1))
        draw = ImageDraw.Draw(dummy_img)

        if self.is_auto:
            target_size = self.font_size
            best_font = None
            best_wrapped = text
            best_size = 12
            tw, th = 0, 0

            for size in range(target_size + 4, 9, -1):
                try: font = ImageFont.truetype(self.font_path, size)
                except: font = ImageFont.load_default()

                try: avg_char_w = draw.textlength("O", font=font)
                except AttributeError: avg_char_w = font.getsize("O")[0] if hasattr(font, 'getsize') else size * 0.5 # type: ignore

                chars_per_line = max(5, int(self.box_w / (avg_char_w if avg_char_w > 0 else 1)))
                wrapped = textwrap.fill(text, width=chars_per_line)

                try:
                    bbox = draw.textbbox((0, 0), wrapped, font=font, align=self.align)
                    cw, ch = bbox[2] - bbox[0], bbox[3] - bbox[1]
                except AttributeError:
                    cw, ch = draw.textsize(wrapped, font=font) # type: ignore

                if cw <= self.box_w + 5 and ch <= self.box_h + 5:
                    best_font = font
                    best_wrapped = wrapped
                    best_size = size
                    tw, th = cw, ch
                    break

            if not best_font:

                best_size = 10
                try: best_font = ImageFont.truetype(self.font_path, best_size)
                except: best_font = ImageFont.load_default()

                try: avg_char_w = draw.textlength("O", font=best_font)
                except AttributeError: avg_char_w = best_font.getsize("O")[0] if hasattr(best_font, 'getsize') else 10 * 0.5 # type: ignore

                wrapped = textwrap.fill(text, width=max(4, int(self.box_w / (avg_char_w if avg_char_w > 0 else 1))))
                best_wrapped = wrapped
                try:
                    bbox = draw.textbbox((0, 0), wrapped, font=best_font, align=self.align)
                    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                except AttributeError:
                    tw, th = draw.textsize(wrapped, font=best_font) # type: ignore

            self.font_size = best_size
            final_font = best_font
            final_wrapped = best_wrapped
        else:

            try: final_font = ImageFont.truetype(self.font_path, self.font_size)
            except: final_font = ImageFont.load_default()

            try: avg_char_w = draw.textlength("O", font=final_font)
            except AttributeError: avg_char_w = final_font.getsize("O")[0] if hasattr(final_font, 'getsize') else self.font_size * 0.5 # type: ignore

            chars_per_line = max(5, int(self.box_w / (avg_char_w if avg_char_w > 0 else 1)))
            final_wrapped = textwrap.fill(text, width=chars_per_line)
            try:
                bbox = draw.textbbox((0, 0), final_wrapped, font=final_font, align=self.align)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except AttributeError:
                tw, th = draw.textsize(final_wrapped, font=final_font) # type: ignore

        tw, th = int(max(1, tw)), int(max(1, th))

        if not self.is_auto:
            final_w = int(max(tw + 20, self.box_w))
            final_h = int(max(th + 20, self.box_h))
        else:
            final_w = int(tw + 20)
            final_h = int(th + 20)

        start_x = (final_w - tw) // 2
        start_y = (final_h - th) // 2

        img = Image.new('RGBA', (final_w, final_h), (0,0,0,0))
        draw = ImageDraw.Draw(img)

        if getattr(self, 'has_stroke', True):
            stroke_val: int = int(max(1, self.font_size * 0.08))
            min_s: int = -stroke_val
            max_s: int = stroke_val + 1
            for dx in range(min_s, max_s):
                for dy in range(min_s, max_s):
                    if dx*dx + dy*dy <= stroke_val*stroke_val:
                        draw.multiline_text((start_x+10+dx, start_y+10+dy), final_wrapped, fill=self.stroke_color, font=final_font, align=self.align)

        if self.is_bold:
            draw.multiline_text((start_x+9, start_y+10), final_wrapped, fill=self.text_color, font=final_font, align=self.align)
            draw.multiline_text((start_x+11, start_y+10), final_wrapped, fill=self.text_color, font=final_font, align=self.align)
            draw.multiline_text((start_x+10, start_y+9), final_wrapped, fill=self.text_color, font=final_font, align=self.align)
            draw.multiline_text((start_x+10, start_y+11), final_wrapped, fill=self.text_color, font=final_font, align=self.align)

        draw.multiline_text((start_x+10, start_y+10), final_wrapped, fill=self.text_color, font=final_font, align=self.align)

        data = img.tobytes("raw", "RGBA")
        qim = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)

        if not self._initialized:

            self.setPixmap(QPixmap.fromImage(qim))
            nx, ny, nw, nh = self.rect_data["rect"]
            cx = nx + nw / 2
            cy = ny + nh / 2
            self.setPos(cx - img.width / 2, cy - img.height / 2)
            self._initialized = True
        else:

            current_pix = self.pixmap()
            if current_pix and not current_pix.isNull():
                cx = self.pos().x() + current_pix.width() / 2
                cy = self.pos().y() + current_pix.height() / 2
            else:
                cx, cy = self.pos().x(), self.pos().y()
            self.setPixmap(QPixmap.fromImage(qim))
            self.setPos(cx - img.width / 2, cy - img.height / 2)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if self.isSelected(): self.main_app.on_node_selected(self)
        return super().itemChange(change, value)

class CollapsibleSection(QWidget):
    """Açılır/kapanır modüler panel bölümü (Photoshop tarzı)"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self._is_collapsed = False
        self._title = title
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.toggle_btn = QPushButton(f"  ▾  {title}")
        self.toggle_btn.setObjectName("sectionHeader")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self._toggle)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 8, 12, 12)
        self.content_layout.setSpacing(8)
        lay.addWidget(self.toggle_btn)
        lay.addWidget(self.content)

    def _toggle(self):
        self._is_collapsed = not self._is_collapsed
        self.content.setVisible(not self._is_collapsed)
        arrow = "▸" if self._is_collapsed else "▾"
        self.toggle_btn.setText(f"  {arrow}  {self._title}")

    def addWidget(self, widget):
        self.content_layout.addWidget(widget)

    def addLayout(self, layout):
        self.content_layout.addLayout(layout)

class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent) # type: ignore
        self.setWindowTitle("⚙️ Ayarlar")
        self.resize(400, 200)
        self.current_settings = current_settings or {}
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.combo_engine = QComboBox()
        self.combo_engine.addItems(["Otomatik (Gemini > Google)", "Sadece Ücretsiz (Google)"])
        self.combo_engine.setCurrentText(str(self.current_settings.get("engine", "Otomatik (Gemini > Google)")))
        self.txt_api = QLineEdit(str(self.current_settings.get("api_key", "")))
        self.txt_api.setEchoMode(QLineEdit.EchoMode.Password)
        self.combo_font = QComboBox()
        fonts = ["Patrick Hand (Tam Türkçe Destekli)", "Comic Neue Bold (Klasik)", "Arial", "Comic Sans MS", "Impact"]
        self.combo_font.addItems(fonts)
        if str(self.current_settings.get("font", "")) in fonts: self.combo_font.setCurrentText(str(self.current_settings.get("font", "")))
        self.combo_align = QComboBox()
        self.combo_align.addItems(["Orta", "Sol", "Sağ"])
        self.combo_align.setCurrentText(str(self.current_settings.get("align", "Orta")))
        form.addRow("Çeviri Motoru:", self.combo_engine)
        form.addRow("Gemini API (Opsiyonel):", self.txt_api)
        form.addRow("Varsayılan Font:", self.combo_font)
        form.addRow("Hizalama:", self.combo_align)
        layout.addLayout(form)

        lbl_dev = QLabel('Geliştirici: <a href="https://github.com/Sefflex" style="color: #a78bfa; text-decoration: none;">Sefflex</a> | v0.7')
        lbl_dev.setOpenExternalLinks(True)
        lbl_dev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_dev)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.setStyleSheet("QDialog { background-color: #16181d; color: #f0f0f0; } QWidget { color: #f0f0f0; background-color: #16181d; } QLineEdit, QComboBox { background-color: #12141a; border: 1px solid #2a2d35; padding: 8px; border-radius: 10px; color: #f0f0f0; } QComboBox::drop-down { border: none; } QComboBox QAbstractItemView { background-color: #16181d; border: 1px solid #2a2d35; selection-background-color: #6c5ce7; color: #f0f0f0; } QPushButton { background-color: #1c1f26; padding: 8px 16px; border: 1px solid #2a2d35; border-radius: 10px; color: #f0f0f0; } QPushButton:hover { background-color: #6c5ce7; border-color: #5b4bd6; } QLabel { background-color: transparent; }")
    def get_settings(self) -> dict: return {"engine": self.combo_engine.currentText(),"api_key": self.txt_api.text().strip(),"font": self.combo_font.currentText(),"align": self.combo_align.currentText()}

class AutoScanlationThread(QThread):
    finished = pyqtSignal(tuple); progress = pyqtSignal(str)
    def __init__(self, qimage, settings):
        super().__init__()
        self.qimage = qimage; self.settings = settings
    def run(self):
        self.progress.emit("Metin Blokları Çözümleniyor...")
        qimg = self.qimage.convertToFormat(QImage.Format.Format_RGB32)
        width, height = qimg.width(), qimg.height()
        ptr = qimg.constBits(); ptr.setsize(height * width * 4)
        arr = np.array(ptr).reshape((height, width, 4))
        img_bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)

        try: reader = easyocr.Reader(['en'], gpu=True)
        except: reader = easyocr.Reader(['en'], gpu=False)

        ocr_results = reader.readtext(img_bgr, paragraph=True, text_threshold=0.4, mag_ratio=2.0, bbox_min_score=0.3, x_ths=0.7, y_ths=0.7)

        h_img, w_img, _ = img_bgr.shape
        full_mask = np.zeros((h_img, w_img), dtype=np.uint8)

        results = []
        for i, (bbox, text) in enumerate(ocr_results, 1):
            text = text.strip()
            if len(text) < 2: continue

            x_coords = [p[0] for p in bbox]; y_coords = [p[1] for p in bbox]
            x, y = int(min(x_coords)), int(min(y_coords))
            w, h_box = int(max(x_coords) - x), int(max(y_coords) - y)
            results.append({"rect": (x, y, w, h_box), "text": text})

            pad = 2
            x1, y1 = max(0, x - pad), max(0, y - pad)
            x2, y2 = min(w_img, x + w + pad), min(h_img, y + h_box + pad)
            crop = img_bgr[y1:y2, x1:x2]
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            box_mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 6)

            kernel_local = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            box_mask = cv2.dilate(box_mask, kernel_local, iterations=1)

            full_mask[y1:y2, x1:x2] = cv2.bitwise_or(full_mask[y1:y2, x1:x2], box_mask)

        if not results:
            self.finished.emit((cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), []))
            return

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        full_mask = cv2.dilate(full_mask, kernel, iterations=1)

        self.progress.emit("Tüm orijinal metinler tek seferde pürüzsüzce siliniyor...")
        cleaned_bgr = cv2.inpaint(img_bgr, full_mask, 4, cv2.INPAINT_TELEA)

        self.progress.emit("Yapay Zeka (AI) Çeviri İşlemi Devrede...")
        engine = str(self.settings.get("engine", "Otomatik (Gemini > Google)"))
        api_key = str(self.settings.get("api_key", "")).strip()

        texts_to_translate: dict = {str(i): r["text"] for i, r in enumerate(results)}
        translated_dict: dict[str, str] = {}

        if api_key and "Gemini" in engine:
            try:
                import google.generativeai as genai # type: ignore
                import json
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(("Sen profesyonel bir çizgi roman ve manga çevirmenisin, tüm argo ve kalıpları Türkçe'ye harika uyarla.\nASLA açıklama YAPMA! SADECE JSON ÇEVİR.\n" + json.dumps(texts_to_translate)))
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_text)
                if isinstance(parsed, dict):
                    for k, v in parsed.items():
                        translated_dict[str(k)] = str(v)
            except Exception: pass

        if not translated_dict:
            self.progress.emit("Google Ücretsiz Çeviri Kullanılıyor...")
            try:
                from deep_translator import GoogleTranslator # type: ignore
                translator = GoogleTranslator(source='en', target='tr')
                for i, r in enumerate(results): translated_dict[str(i)] = str(translator.translate(r["text"]))
            except Exception: pass

        for i, res in enumerate(results):
            res["translated_text"] = translated_dict.get(str(i), res["text"])

        self.finished.emit((cv2.cvtColor(cleaned_bgr, cv2.COLOR_BGR2RGB), results))

class CanvasView(QGraphicsView):
    def __init__(self, main_app, parent=None):
        super().__init__(parent) # type: ignore
        self.main_app = main_app
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.zoom_factor = 1.05

        self.paint_mode = False
        self.picker_mode = False
        self.select_mode = False
        self.fill_mode = False
        self.brush_size = 15
        self.brush_color = QColor(255, 255, 255)
        self.last_point = None
        self.selection_start = None
        self.selection_rect_item = None
        self.fill_start = None
        self.fill_rect_item = None

    def mousePressEvent(self, event):
        if self.select_mode and event.button() == Qt.MouseButton.LeftButton:
            from PyQt6.QtWidgets import QGraphicsRectItem # type: ignore
            self.selection_start = self.mapToScene(event.pos())
            self.selection_rect_item = QGraphicsRectItem()
            self.selection_rect_item.setPen(QPen(QColor(0, 255, 0), 2, Qt.PenStyle.DashLine))  # type: ignore
            self.scene().addItem(self.selection_rect_item)
            return

        if self.picker_mode and event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            ix, iy = int(scene_pos.x()), int(scene_pos.y())
            if self.main_app.current_page_idx != -1:
                page = self.main_app.pages[self.main_app.current_page_idx]
                if "clean_qpix" in page:
                    qim = page["clean_qpix"].toImage()
                    if 0 <= ix < qim.width() and 0 <= iy < qim.height():
                        color = qim.pixelColor(ix, iy)
                        self.brush_color = color
                        self.main_app.lbl_current_color.setStyleSheet(f"background-color: {color.name()}; border: 2px solid #2a2d35; border-radius: 12px;")

                        self.main_app.btn_picker.setChecked(False)
                        self.main_app.btn_paint.setChecked(True)
                        self.main_app.toggle_paint_mode(True)
            return

        if self.fill_mode and event.button() == Qt.MouseButton.LeftButton:
            from PyQt6.QtWidgets import QGraphicsRectItem # type: ignore
            self.fill_start = self.mapToScene(event.pos())
            self.fill_rect_item = QGraphicsRectItem()
            self.fill_rect_item.setBrush(QBrush(self.brush_color))  # type: ignore
            self.fill_rect_item.setPen(QPen(Qt.PenStyle.NoPen))  # type: ignore
            self.fill_rect_item.setOpacity(0.5)  # type: ignore
            self.scene().addItem(self.fill_rect_item)
            return

        if self.paint_mode and event.button() == Qt.MouseButton.LeftButton:
            if self.main_app.current_page_idx != -1:
                page = self.main_app.pages[self.main_app.current_page_idx]
                if "undo_stack" not in page: page["undo_stack"] = []
                page["undo_stack"].append(page["clean_qpix"].copy())
                if len(page["undo_stack"]) > 20: page["undo_stack"].pop(0)

            self.last_point = self.mapToScene(event.pos())
            self.paint_on_bg(self.last_point, self.last_point)
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.select_mode and self.selection_start and (event.buttons() & Qt.MouseButton.LeftButton):
            curr = self.mapToScene(event.pos())
            r = QRectF(self.selection_start, curr).normalized()
            if self.selection_rect_item: self.selection_rect_item.setRect(r)  # type: ignore
            return

        if self.fill_mode and self.fill_start and (event.buttons() & Qt.MouseButton.LeftButton):
            curr = self.mapToScene(event.pos())
            r = QRectF(self.fill_start, curr).normalized()
            if self.fill_rect_item: self.fill_rect_item.setRect(r)  # type: ignore
            return

        if self.paint_mode and (event.buttons() & Qt.MouseButton.LeftButton) and self.last_point:
            current_point = self.mapToScene(event.pos())
            self.paint_on_bg(self.last_point, current_point)
            self.last_point = current_point
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.select_mode and self.selection_start and event.button() == Qt.MouseButton.LeftButton:
            curr = self.mapToScene(event.pos())
            rect = QRectF(self.selection_start, curr).normalized()
            if self.selection_rect_item: self.scene().removeItem(self.selection_rect_item)
            self.selection_start = None
            self.selection_rect_item = None
            self.select_mode = False
            self.main_app.btn_ocr.setChecked(False)
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.main_app.run_rect_ocr(rect)
            return

        if self.fill_mode and self.fill_start and event.button() == Qt.MouseButton.LeftButton:
            curr = self.mapToScene(event.pos())
            rect = QRectF(self.fill_start, curr).normalized()
            if self.fill_rect_item: self.scene().removeItem(self.fill_rect_item)
            self.fill_start = None
            self.fill_rect_item = None

            if self.main_app.current_page_idx != -1:
                page = self.main_app.pages[self.main_app.current_page_idx]
                if "undo_stack" not in page: page["undo_stack"] = []
                page["undo_stack"].append(page["clean_qpix"].copy())
                if len(page["undo_stack"]) > 20: page["undo_stack"].pop(0)

            self.fill_on_bg(rect)
            return

        if self.paint_mode and event.button() == Qt.MouseButton.LeftButton:
            self.last_point = None
            return
        super().mouseReleaseEvent(event)

    def fill_on_bg(self, rect: QRectF):
        if self.main_app.current_page_idx == -1: return
        page = self.main_app.pages[self.main_app.current_page_idx]
        if "clean_qpix" not in page: return

        qpix = page["clean_qpix"]
        painter = QPainter(qpix)
        painter.setBrush(QBrush(self.brush_color))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawRect(rect)
        painter.end()

        page["bg_item"].setPixmap(qpix)

    def paint_on_bg(self, p1, p2):
        if self.main_app.current_page_idx == -1: return
        page = self.main_app.pages[self.main_app.current_page_idx]
        if "clean_qpix" not in page: return

        qpix = page["clean_qpix"]
        painter = QPainter(qpix)
        pen = QPen(self.brush_color, self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(p1, p2)
        painter.end()

        page["bg_item"].setPixmap(qpix)

    def keyPressEvent(self, event):
        from PyQt6.QtGui import QKeySequence # type: ignore
        if event.matches(QKeySequence.StandardKey.Undo):
            if self.main_app.current_page_idx != -1:
                page = self.main_app.pages[self.main_app.current_page_idx]
                if "undo_stack" in page and len(page["undo_stack"]) > 0:
                    last_pix = page["undo_stack"].pop()
                    page["clean_qpix"] = last_pix
                    page["bg_item"].setPixmap(last_pix)
            return

        if event.key() == Qt.Key.Key_Backspace or event.key() == Qt.Key.Key_Delete:
            scene = self.scene()
            if scene:
                for item in scene.selectedItems():
                    if isinstance(item, DraggableTextNode):
                        scene.removeItem(item)
                        if self.main_app.active_node == item:
                            self.main_app.active_node = None
                            self.main_app.clear_right_panel()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0: self.scale(self.zoom_factor, self.zoom_factor)
        else: self.scale(1.0 / self.zoom_factor, 1.0 / self.zoom_factor)

class CizgiArsivApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ComicEditör - Profesyonel Çizgi Roman Dizgi ve Çeviri Aracı")
        self.resize(1400, 850)
        self.pages: list[dict] = []
        self.current_page_idx: int = -1
        self.active_node: DraggableTextNode | None = None
        self.analyzer_thread: AutoScanlationThread | None = None # type: ignore
        self.progress_dialog: QProgressDialog | None = None
        self.settings: dict = {"engine": "Otomatik (Gemini > Google)","api_key": "","font": "Patrick Hand (Tam Türkçe Destekli)","align": "Orta"}

        self._is_updating_panel = False

        self.setup_ui()
        self.apply_dark_theme()

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
        topbar.setFixedHeight(52)
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 16, 0)
        tb.setSpacing(8)

        logo = QLabel("⬡ ComicEditör")
        logo.setObjectName("logoLabel")

        btn_load = QPushButton("� Yükle")
        btn_load.clicked.connect(self.load_files)

        btn_load_proj = QPushButton("📥 Proje Aç")
        btn_load_proj.setObjectName("btnPrimary")
        btn_load_proj.clicked.connect(self.load_project)

        btn_save_proj = QPushButton("📤 Kaydet")
        btn_save_proj.setObjectName("btnSecondary")
        btn_save_proj.clicked.connect(self.save_project)

        btn_analyze = QPushButton("🚀 Tam Otonom Çıkart")
        btn_analyze.setObjectName("btnHero")
        btn_analyze.clicked.connect(self.run_auto_scanlation)

        btn_export = QPushButton("💾 PDF Çıkar")
        btn_export.clicked.connect(self.export_to_pdf)

        btn_settings = QPushButton("⚙️")
        btn_settings.setObjectName("btnIcon")
        btn_settings.setFixedSize(38, 38)
        btn_settings.clicked.connect(self.open_settings)

        tb.addWidget(logo)
        tb.addSpacing(20)
        tb.addWidget(btn_load)
        tb.addWidget(btn_load_proj)
        tb.addWidget(btn_save_proj)
        tb.addSpacing(12)
        tb.addWidget(btn_analyze)
        tb.addStretch()
        tb.addWidget(btn_export)
        tb.addWidget(btn_settings)
        main_layout.addWidget(topbar)

        # ═══════════════════ BODY ═══════════════════
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(8, 6, 8, 8)
        body_layout.setSpacing(8)

        # ─────── LEFT SIDEBAR ───────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(180)
        sidebar_lay = QVBoxLayout(sidebar)
        sidebar_lay.setContentsMargins(10, 12, 10, 12)
        sidebar_lay.setSpacing(8)

        lbl_pages = QLabel("SAYFALAR")
        lbl_pages.setObjectName("sectionTitle")
        lbl_pages.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.page_list = QListWidget()
        self.page_list.setIconSize(QSize(100, 150))
        self.page_list.itemClicked.connect(self.on_page_selected)

        left_footer = QLabel('v0.8 · <a href="https://github.com/Sefflex" style="color: #6c5ce7; text-decoration: none;">Sefflex</a>')
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
        center_lay.setSpacing(6)

        self.canvas = CanvasView(self)
        center_lay.addWidget(self.canvas, 1)

        toolbar = QWidget()
        toolbar.setObjectName("toolStrip")
        toolbar.setFixedHeight(44)
        tool_lay = QHBoxLayout(toolbar)
        tool_lay.setContentsMargins(12, 0, 12, 0)
        tool_lay.setSpacing(6)

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

        self.spin_brush = QSpinBox()
        self.spin_brush.setRange(2, 200)
        self.spin_brush.setValue(15)
        self.spin_brush.setPrefix("⌀ ")
        self.spin_brush.valueChanged.connect(self.update_brush_size)

        self.lbl_current_color = QLabel()
        self.lbl_current_color.setFixedSize(24, 24)
        self.lbl_current_color.setStyleSheet("background-color: #ffffff; border: 2px solid #2a2d35; border-radius: 12px;")

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
        tool_lay.addWidget(QLabel("│"))
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
        right_scroll.setFixedWidth(300)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        right = QWidget()
        right.setObjectName("propertiesPanel")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(12, 12, 12, 12)
        right_lay.setSpacing(6)

        panel_title = QLabel("🎛️  ÖZELLİKLER")
        panel_title.setObjectName("panelTitle")
        right_lay.addWidget(panel_title)
        right_lay.addSpacing(4)

        # ── Section: Metin ──
        sec_text = CollapsibleSection("📝  Metin")
        lbl_orig = QLabel("Orijinal İbare:")
        lbl_orig.setObjectName("fieldLabel")
        self.txt_original = QTextEdit()
        self.txt_original.setPlaceholderText("Orijinal metin...")
        self.txt_original.setMinimumHeight(50)
        self.txt_original.setMaximumHeight(80)
        self.txt_original.textChanged.connect(self.on_panel_changed)

        lbl_tr = QLabel("Çeviri:")
        lbl_tr.setObjectName("fieldLabel")
        self.txt_translated = QTextEdit()
        self.txt_translated.setPlaceholderText("Çeviri içeriği...")
        self.txt_translated.setMinimumHeight(60)
        self.txt_translated.setMaximumHeight(100)
        self.txt_translated.textChanged.connect(self.on_panel_changed)

        sec_text.addWidget(lbl_orig)
        sec_text.addWidget(self.txt_original)
        sec_text.addWidget(lbl_tr)
        sec_text.addWidget(self.txt_translated)
        right_lay.addWidget(sec_text)

        # ── Section: Stil ──
        sec_style = CollapsibleSection("🎨  Stil")
        style_form = QFormLayout()
        style_form.setSpacing(10)
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
        size_form.setSpacing(10)
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
        self.btn_save_preset = QPushButton("💾 Ön Ayar Kaydet")
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

    def open_settings(self):
        d = SettingsDialog(self, self.settings)
        if d.exec(): self.settings = d.get_settings()

    def reset_current_page(self):
        if self.current_page_idx == -1: return
        reply = QMessageBox.question(self, "Sayfayı Sıfırla", "Bu sayfadaki yapılan tüm değişiklikleri (yazılar, boyamalar, çeviriler) sıfırlamak istediğinize emin misiniz?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
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

    def load_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Dosya Seç", "", "Resim / PDF / ÇizgiRoman (*.cbz *.cbr *.pdf *.png *.jpg *.jpeg) ;; CBZ/CBR (*.cbr *.cbz) ;; PDF (*.pdf)")
        if not files: return
        self.progress_dialog = QProgressDialog("Okunuyor...", "İptal", 0, 0, self)
        self.progress_dialog.show() # type: ignore
        for f in files:
            ext = f.lower().split('.')[-1]
            if ext == 'pdf': self.load_pdf(f)
            elif ext in ['cbz', 'cbr']: self.load_cbz(f)
            else: self.load_img(f)
        dlg = self.progress_dialog
        if dlg is not None: dlg.close()

    def load_pdf(self, path):
        try:
            doc = fitz.open(path); fn = path.split('/')[-1]
            for i in range(len(doc)):
                page = doc.load_page(i); pix = page.get_pixmap(dpi=300)
                fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
                qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
                self.add_page(QPixmap.fromImage(qimg), f"{fn} - {i+1}")
        except Exception as e: QMessageBox.warning(self, "Hata", str(e))

    def load_cbz(self, path):
        fn = path.split('/')[-1]
        try:
            with zipfile.ZipFile(path, 'r') as z:
                for name in sorted(z.namelist()):
                    if name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        self.add_page(QPixmap.fromImage(QImage.fromData(z.read(name))), f"{fn} - {name.split('/')[-1]}")
            return
        except: pass
        try:
            with rarfile.RarFile(path, 'r') as r:
                for name in sorted(r.namelist()):
                    if name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        self.add_page(QPixmap.fromImage(QImage.fromData(r.read(name))), f"{fn} - {name.split('/')[-1]}")
        except Exception as e: QMessageBox.warning(self, "CBR Hata", "Rar bozuk. Dosyayı klasik Zip yaparak deneyin.")

    def load_img(self, path):
        qpix = QPixmap(path)
        if not qpix.isNull(): self.add_page(qpix, path.split('/')[-1])

    def add_page(self, qpix, title):
        scene = QGraphicsScene()
        scene.setSceneRect(QRectF(qpix.rect()))
        bg = QGraphicsPixmapItem(qpix)
        bg.setZValue(-100)
        scene.addItem(bg)

        self.pages.append({"qpix": qpix, "scene": scene, "title": title, "bg_item": bg, "clean_qpix": qpix.copy(), "undo_stack": []})

        thumb = qpix.scaled(100, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        item = QListWidgetItem(QIcon(thumb), title)
        item.setData(Qt.ItemDataRole.UserRole, len(self.pages) - 1)
        self.page_list.addItem(item)
        if len(self.pages) == 1: self.on_page_selected(item)

    def get_pixmap_bytes(self, qpix: QPixmap) -> bytes:
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        qpix.save(buf, "PNG")
        return ba.data() # type: ignore

    def bytes_to_pixmap(self, data: bytes) -> QPixmap:
        qpix = QPixmap()
        qpix.loadFromData(data, "PNG")
        return qpix

    def save_project(self):
        if not self.pages: return
        path, _ = QFileDialog.getSaveFileName(self, "Projeyi Kaydet", "Calisma_1.comicproj", "ComicEditör Projesi (*.comicproj)")
        if not path: return
        
        self.progress_dialog = QProgressDialog("Proje Paketleniyor...", "İptal", 0, 0, self)
        dlg = self.progress_dialog
        if dlg: dlg.show()
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
                "nodes": nodes_list
            }
            pages_list.append(p_data)
            
        project_data = {"pages": pages_list, "settings": self.settings}
        
        try:
            with open(path, 'wb') as f:
                pickle.dump(project_data, f)
            if dlg: dlg.close()
            QMessageBox.information(self, "Başarılı", "Proje başarıyla kaydedildi! İleride 'Proje Aç' diyerek kaldığınız yerden devam edebilirsiniz.")
        except Exception as e:
            if dlg: dlg.close()
            QMessageBox.critical(self, "Hata", f"Proje kaydedilemedi: {e}")

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Proje Aç", "", "ComicEditör Projesi (*.comicproj)")
        if not path: return
        
        self.progress_dialog = QProgressDialog("Proje Yükleniyor...", "İptal", 0, 0, self)
        dlg = self.progress_dialog
        if dlg: dlg.show()
        QApplication.processEvents()
        
        try:
            with open(path, 'rb') as f:
                project_data = pickle.load(f)
                
            self.settings = project_data.get("settings", self.settings)
            self.pages.clear()
            self.page_list.clear()
            self.active_node = None
            self.clear_right_panel()
            
            fpath = get_font_path(str(self.settings.get("font", "Patrick Hand")))
            
            for p_data in project_data.get("pages", []):
                qpix = self.bytes_to_pixmap(p_data["qpix"])
                clean_qpix = self.bytes_to_pixmap(p_data["clean_qpix"])
                
                scene = QGraphicsScene()
                scene.setSceneRect(QRectF(qpix.rect()))
                bg = QGraphicsPixmapItem(clean_qpix)
                bg.setZValue(-100)
                scene.addItem(bg)
                
                page_dict = {"qpix": qpix, "scene": scene, "title": p_data["title"], "bg_item": bg, "clean_qpix": clean_qpix, "undo_stack": []}
                self.pages.append(page_dict)
                
                thumb = qpix.scaled(100, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                item = QListWidgetItem(QIcon(thumb), p_data["title"])
                item.setData(Qt.ItemDataRole.UserRole, len(self.pages) - 1)
                self.page_list.addItem(item)
                
                for nd in p_data.get("nodes", []):
                    node = DraggableTextNode(nd["rect_data"], self, nd["font_size"], fpath, nd["align"], nd["is_auto"])
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
                
            if dlg: dlg.close()
            QMessageBox.information(self, "Başarılı", "Proje başarıyla yüklendi. Nerede kaldıysak oradan devam!")
        except Exception as e:
            if dlg: dlg.close()
            QMessageBox.critical(self, "Hata", f"Proje dosyası okunamadı veya bozuk: {e}")

    def on_page_selected(self, item):
        self.current_page_idx = int(item.data(Qt.ItemDataRole.UserRole))
        scene = self.pages[self.current_page_idx]["scene"]
        self.canvas.setScene(scene)
        self.canvas.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.active_node = None
        self.clear_right_panel()

    def clear_right_panel(self):
        self._is_updating_panel = True
        self.txt_original.clear(); self.txt_translated.clear()
        self.spin_size.setValue(14); self.slider_width.setValue(100)
        self._is_updating_panel = False

    def choose_text_color(self):
        node = self.active_node
        if node is None: return
        color = QColorDialog.getColor(initial=QColor(*node.text_color[:3]), parent=self)
        if color.isValid():
            node.text_color = (color.red(), color.green(), color.blue(), 255)
            self.on_node_selected(node)
            node.update_visual()

    def choose_stroke_color(self):
        node = self.active_node
        if node is None: return
        color = QColorDialog.getColor(initial=QColor(*node.stroke_color[:3]), parent=self)
        if color.isValid():
            node.stroke_color = (color.red(), color.green(), color.blue(), 255)
            self.on_node_selected(node)
            node.update_visual()

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
        self.btn_color_text.setStyleSheet(f"background-color: rgb({node.text_color[0]},{node.text_color[1]},{node.text_color[2]}); color: white; border-radius: 10px; border: 1px solid #2a2d35; padding: 8px 12px;")
        self.btn_color_stroke.setStyleSheet(f"background-color: rgb({node.stroke_color[0]},{node.stroke_color[1]},{node.stroke_color[2]}); color: black; border-radius: 10px; border: 1px solid #2a2d35; padding: 8px 12px;")
        self._is_updating_panel = False

    def on_panel_changed(self):
        if self._is_updating_panel: return
        node = self.active_node
        if node is None: return
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

    def save_text_preset(self):
        node = self.active_node
        if node is None: return
        self.settings["preset"] = {
            "font_size": node.font_size,
            "text_color": node.text_color,
            "stroke_color": node.stroke_color,
            "is_bold": node.is_bold,
            "has_stroke": getattr(node, 'has_stroke', True),
            "box_w": node.box_w,
            "box_h": node.box_h
        }
        QMessageBox.information(self, "Ön Ayar Kaydedildi", "Yeni eklenecek yazılar ve OCR okumaları artık bu boyutta, bu renkte ve bu formatta çıkacak!")

    def toggle_original_view(self):
        if self.current_page_idx == -1: return
        page = self.pages[self.current_page_idx]
        if "clean_qpix" not in page: return

        if not page.get("is_showing_original", False):
            page["bg_item"].setPixmap(page["qpix"])
            for item in page["scene"].items():
                if isinstance(item, DraggableTextNode): item.hide()
            page["is_showing_original"] = True
            self.btn_toggle.setText("👁️ Çeviriye Dön")
            self.btn_toggle.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; border: 1px solid #27ae60; border-radius: 10px;")
        else:
            page["bg_item"].setPixmap(page["clean_qpix"])
            for item in page["scene"].items():
                if isinstance(item, DraggableTextNode): item.show()
            page["is_showing_original"] = False
            self.btn_toggle.setText("👁️ Orijinali Gör")
            self.btn_toggle.setStyleSheet("")

    def add_manual_text(self):
        if self.current_page_idx == -1: return
        page = self.pages[self.current_page_idx]
        scene = page["scene"]

        view_rect = self.canvas.mapToScene(self.canvas.viewport().rect()).boundingRect()
        cx, cy = view_rect.center().x(), view_rect.center().y()
        w, h = 150, 150

        rect_data = {"rect": (int(cx - w/2), int(cy - h/2), w, h), "text": "", "translated_text": "YENİ YAZI"}
        global_font = 26

        fpath = get_font_path(str(self.settings.get("font", "Patrick Hand")))
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

    def run_rect_ocr(self, rect: QRectF):
        if self.current_page_idx == -1: return
        page = self.pages[self.current_page_idx]
        if "qpix" not in page: return

        qim = page["qpix"].toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        w, h = qim.width(), qim.height()
        ptr = qim.constBits(); ptr.setsize(h * w * 4)
        arr = np.array(ptr).reshape((h, w, 4))
        img_bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)

        x1, y1 = max(0, int(rect.left())), max(0, int(rect.top()))
        x2, y2 = min(w, int(rect.right())), min(h, int(rect.bottom()))
        if x2 <= x1 or y2 <= y1: return

        crop = img_bgr[y1:y2, x1:x2]

        self.progress_dialog = QProgressDialog("Bölge Tanınıyor...", "İptal", 0, 0, self)
        self.progress_dialog.show() # type: ignore
        QApplication.processEvents()

        try: reader = easyocr.Reader(['en'], gpu=True)
        except: reader = easyocr.Reader(['en'], gpu=False)

        ocr_results = reader.readtext(crop, paragraph=True, text_threshold=0.3, mag_ratio=2.0)

        if self.progress_dialog: self.progress_dialog.close()

        if not ocr_results:
            QMessageBox.warning(self, "Bulunamadı", "Seçili bölgede metin algılanamadı.")
            return

        combined_text = " ".join([res[1] for res in ocr_results]).strip()

        rect_data = {"rect": (x1, y1, x2-x1, y2-y1), "text": combined_text, "translated_text": ""}
        global_font = int(h * 0.016)
        if global_font > 100: global_font = 100
        if global_font < 14: global_font = 14

        fpath = get_font_path(str(self.settings.get("font", "Patrick Hand")))
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

    def run_auto_scanlation(self):
        if self.current_page_idx == -1: return
        page = self.pages[self.current_page_idx]
        qpix = page["qpix"]

        self.progress_dialog = QProgressDialog("Gelişmiş Yapay Zeka Katmanları Başladı...", "İptal", 0, 0, self)
        self.progress_dialog.show() # type: ignore

        self.analyzer_thread = AutoScanlationThread(qpix.toImage(), self.settings)
        if self.analyzer_thread:
            self.analyzer_thread.progress.connect(lambda m: self.progress_dialog.setLabelText(m) if self.progress_dialog else None) # type: ignore
            self.analyzer_thread.finished.connect(self.on_auto_scanlation_finished) # type: ignore
            self.analyzer_thread.start() # type: ignore

    def on_auto_scanlation_finished(self, out_data):
        dlg = self.progress_dialog
        if dlg is not None: dlg.close()
        cleaned_rgb, results = out_data

        height, width, _ = cleaned_rgb.shape
        bytes_line = 3 * width
        qim = QImage(cleaned_rgb.data.tobytes(), width, height, bytes_line, QImage.Format.Format_RGB888).copy()
        new_qpix = QPixmap.fromImage(qim)

        page = self.pages[self.current_page_idx]
        page["bg_item"].setPixmap(new_qpix)
        page["clean_qpix"] = new_qpix

        scene = page["scene"]
        for it in scene.items():
            if isinstance(it, DraggableTextNode): scene.removeItem(it)

        global_font = int(height * 0.016)
        if global_font > 100: global_font = 100
        if global_font < 14: global_font = 14

        fpath = get_font_path(str(self.settings.get("font", "Patrick Hand")))
        align_str = str(self.settings.get("align", "Orta")).lower()
        align_pil = "center" if align_str == "orta" else "right" if align_str == "sağ" else "left"

        for res in results:
            node = DraggableTextNode(res, self, global_font, fpath, align_pil, is_auto=True)
            scene.addItem(node)

    def translate_selected_node(self):
        if not self.active_node: return
        text = self.txt_original.toPlainText().strip()
        if not text: return
        api = self.settings.get("api_key", "").strip()
        try:
            if api:
                import google.generativeai as genai # type: ignore
                genai.configure(api_key=api)
                m = genai.GenerativeModel('gemini-1.5-flash')
                response = m.generate_content(("Çevir:\n" + text))
                tr = response.text.strip()
            else:
                tr = str(GoogleTranslator(source='en', target='tr').translate(text))
            self.txt_translated.setPlainText(tr)
        except Exception as e: QMessageBox.critical(self, "Hata", str(e))

    def export_to_pdf(self):
        if not self.pages: return
        path, _ = QFileDialog.getSaveFileName(self, "PDF Olarak Kaydet", "Hikaye_Full.pdf", "PDF Dosyası (*.pdf)")
        if not path: return

        for page in self.pages:
            if page.get("is_showing_original", False):
                page["bg_item"].setPixmap(page.get("clean_qpix", page["qpix"]))
                for item in page["scene"].items():
                    if isinstance(item, DraggableTextNode): item.show()
                page["is_showing_original"] = False
        self.btn_toggle.setText("👁️ Orijinali Gör")
        self.btn_toggle.setStyleSheet("")

        self.progress_dialog = QProgressDialog("Final Render... Yazılar Katmana Gömülüyor...", "İptal", 0, len(self.pages), self)
        dlg2 = self.progress_dialog
        if dlg2 is not None: dlg2.show()

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
            ptr = img.constBits(); ptr.setsize(h * w * 4)
            arr = np.array(ptr).reshape((h, w, 4))
            img_bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
            pil_images.append(Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)))
            if self.progress_dialog is not None: self.progress_dialog.setValue(i+1)

        if len(pil_images) > 0:
            try:
                pil_images[0].save(path, "PDF", resolution=300, save_all=True, append_images=pil_images[1:]) # type: ignore
                QMessageBox.information(self, "Başarılı", "Matbaa Kalitesinde Yayınlandı!")
            except Exception as e: QMessageBox.critical(self, "Hata", str(e))

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

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0f1115; }
            QWidget { color: #f0f0f0; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; background-color: transparent; }

            #topbar { background-color: #16181d; border-bottom: 1px solid #2a2d35; }
            #logoLabel { color: #f0f0f0; font-size: 17px; font-weight: bold; letter-spacing: 1px; }
            #sidebar { background-color: #16181d; border: 1px solid #2a2d35; border-radius: 14px; }
            #sectionTitle { color: #6b6e78; font-size: 11px; font-weight: bold; letter-spacing: 2px; }
            #footerLabel { color: #4a4d56; font-size: 11px; }
            #toolStrip { background-color: #16181d; border: 1px solid #2a2d35; border-radius: 12px; }
            #propertiesScroll { background-color: transparent; border: none; }
            #propertiesPanel { background-color: #16181d; border: 1px solid #2a2d35; border-radius: 14px; }
            #panelTitle { color: #6b6e78; font-size: 11px; font-weight: bold; letter-spacing: 2px; }
            #fieldLabel { color: #8b8e96; font-size: 12px; margin-top: 2px; }
            #tipLabel { color: #4a4d56; font-size: 11px; padding: 8px 4px; }
            QPushButton { background-color: #1c1f26; padding: 8px 14px; border: 1px solid #2a2d35; border-radius: 10px; color: #f0f0f0; font-size: 12px; }
            QPushButton:hover { background-color: #252830; border-color: #3a3d45; }
            QPushButton:pressed { background-color: #6c5ce7; border-color: #5b4bd6; }
            QPushButton:checked { background-color: #6c5ce7; border-color: #5b4bd6; color: white; }
            #btnPrimary { background-color: #6c5ce7; border: 1px solid #5b4bd6; color: white; font-weight: bold; }
            #btnPrimary:hover { background-color: #7c6ef7; border-color: #6c5ce7; }
            #btnSecondary { background-color: #1c1f26; border: 1px solid #4ea8de; color: #4ea8de; }
            #btnSecondary:hover { background-color: #4ea8de; color: white; border-color: #4ea8de; }
            #btnHero { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6c5ce7, stop:1 #4ea8de); border: none; color: white; font-weight: bold; padding: 8px 20px; }
            #btnHero:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c6ef7, stop:1 #5eb8ee); }
            #btnDanger { background-color: #1c1f26; border: 1px solid #e74c3c; color: #e74c3c; }
            #btnDanger:hover { background-color: #e74c3c; color: white; }
            #btnSuccess { background-color: #1c1f26; border: 1px solid #2ecc71; color: #2ecc71; font-weight: bold; }
            #btnSuccess:hover { background-color: #2ecc71; color: white; }
            #btnIcon { background-color: transparent; border: 1px solid #2a2d35; border-radius: 10px; font-size: 16px; padding: 0px; }
            #btnIcon:hover { background-color: #252830; border-color: #6c5ce7; }
            #btnTool { padding: 6px 12px; font-size: 12px; }
            #colorBtn { text-align: left; padding: 8px 12px; }
            #sectionHeader { background-color: transparent; border: none; border-bottom: 1px solid #2a2d35; border-radius: 0px; text-align: left; padding: 10px 12px; font-weight: bold; font-size: 12px; color: #f0f0f0; }
            #sectionHeader:hover { background-color: #1c1f26; color: #6c5ce7; }
            QLineEdit { background-color: #12141a; padding: 8px; border: 1px solid #2a2d35; border-radius: 10px; color: #f0f0f0; selection-background-color: #6c5ce7; }
            QLineEdit:focus { border-color: #6c5ce7; }
            QTextEdit { background-color: #12141a; border: 1px solid #2a2d35; border-radius: 10px; color: #f0f0f0; padding: 8px; selection-background-color: #6c5ce7; }
            QTextEdit:focus { border-color: #6c5ce7; }
            QSpinBox { background-color: #12141a; border: 1px solid #2a2d35; border-radius: 10px; padding: 6px 10px; color: #f0f0f0; }
            QSpinBox:focus { border-color: #6c5ce7; }
            QSpinBox::up-button, QSpinBox::down-button { background-color: #1c1f26; border: none; width: 20px; border-radius: 5px; }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #6c5ce7; }
            QComboBox { background-color: #12141a; border: 1px solid #2a2d35; border-radius: 10px; padding: 6px 12px; color: #f0f0f0; }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox QAbstractItemView { background-color: #16181d; border: 1px solid #2a2d35; selection-background-color: #6c5ce7; color: #f0f0f0; }
            QListWidget { background-color: #12141a; border: 1px solid #2a2d35; border-radius: 10px; padding: 4px; outline: none; }
            QListWidget::item { padding: 6px; border-radius: 8px; margin: 2px; color: #f0f0f0; }
            QListWidget::item:hover { background-color: #1c1f26; }
            QListWidget::item:selected { background-color: #6c5ce7; color: white; }
            QGraphicsView { background-color: #0a0c10; border: 1px solid #2a2d35; border-radius: 12px; }
            QSlider::groove:horizontal { border: none; height: 4px; background: #1c1f26; border-radius: 2px; }
            QSlider::handle:horizontal { background: #6c5ce7; border: none; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
            QSlider::handle:horizontal:hover { background: #7c6ef7; }
            QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6c5ce7, stop:1 #4ea8de); border-radius: 2px; }
            QCheckBox { spacing: 8px; color: #f0f0f0; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px; border: 2px solid #2a2d35; background-color: #12141a; }
            QCheckBox::indicator:hover { border-color: #6c5ce7; }
            QCheckBox::indicator:checked { background-color: #6c5ce7; border-color: #5b4bd6; }
            QLabel { color: #8b8e96; background-color: transparent; }
            QFrame { background-color: #16181d; border: 1px solid #2a2d35; border-radius: 14px; }
            QProgressDialog { background-color: #16181d; color: #f0f0f0; }
            QProgressBar { border: 1px solid #2a2d35; border-radius: 6px; background-color: #12141a; text-align: center; color: #f0f0f0; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6c5ce7, stop:1 #4ea8de); border-radius: 5px; }
            QMessageBox { background-color: #16181d; color: #f0f0f0; }
            QMessageBox QLabel { color: #f0f0f0; }
            QMessageBox QPushButton { min-width: 80px; }
            QScrollBar:vertical { background: transparent; width: 6px; border: none; }
            QScrollBar::handle:vertical { background: #2a2d35; min-height: 30px; border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: #6c5ce7; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar:horizontal { background: transparent; height: 6px; border: none; }
            QScrollBar::handle:horizontal { background: #2a2d35; min-width: 30px; border-radius: 3px; }
            QScrollBar::handle:horizontal:hover { background: #6c5ce7; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
            QToolTip { background-color: #1c1f26; border: 1px solid #6c5ce7; border-radius: 8px; color: #f0f0f0; padding: 6px 10px; }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CizgiArsivApp()
    window.show()
    sys.exit(app.exec())

