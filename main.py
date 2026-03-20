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
    QProgressDialog, QMessageBox, QLineEdit, QDialog, QDialogButtonBox, QSlider, QCheckBox, QColorDialog
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

        lbl_dev = QLabel('Geliştirici: <a href="https://github.com/Sefflex" style="color: #3498db; text-decoration: none;">Sefflex</a> | v0.7')
        lbl_dev.setOpenExternalLinks(True)
        lbl_dev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_dev)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.setStyleSheet("QDialog { background-color: #2b2b2b; color: #ececec; } QWidget { color: #ececec; background-color: #2b2b2b; } QLineEdit, QComboBox { background-color: #1e1e1e; border: 1px solid #555; padding: 4px; border-radius: 4px; } QPushButton { background-color: #3f4244; padding: 6px; border: 1px solid #555; }")
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

            pad = 12
            x1, y1 = max(0, x - pad), max(0, y - pad)
            x2, y2 = min(w_img, x + w + pad), min(h_img, y + h_box + pad)
            crop = img_bgr[y1:y2, x1:x2]
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            box_mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 6)

            kernel_local = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            box_mask = cv2.dilate(box_mask, kernel_local, iterations=1)

            full_mask[y1:y2, x1:x2] = cv2.bitwise_or(full_mask[y1:y2, x1:x2], box_mask)

        if not results:
            self.finished.emit((cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), []))
            return

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        full_mask = cv2.dilate(full_mask, kernel, iterations=2)

        self.progress.emit("Tüm orijinal metinler tek seferde pürüzsüzce siliniyor...")
        cleaned_bgr = cv2.inpaint(img_bgr, full_mask, 7, cv2.INPAINT_TELEA)

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
                        self.main_app.lbl_current_color.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")

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
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        tb = QHBoxLayout()
        btn_load = QPushButton("🖼️ Resim/CBR Yükle")
        btn_load.clicked.connect(self.load_files)
        
        btn_load_proj = QPushButton("📥 Proje Aç")
        btn_load_proj.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_load_proj.clicked.connect(self.load_project)
        
        btn_save_proj = QPushButton("📤 Proje Kaydet")
        btn_save_proj.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold;")
        btn_save_proj.clicked.connect(self.save_project)

        btn_analyze = QPushButton("🚀 Sayfayı Tam Otonom Çıkart")
        btn_analyze.setStyleSheet("background-color: #d35400; color: white; font-weight: bold; padding: 6px 12px;")
        btn_analyze.clicked.connect(self.run_auto_scanlation)

        self.btn_reset = QPushButton("🔄 Sayfayı Sıfırla")
        self.btn_reset.setStyleSheet("background-color: #c0392b; color: white;")
        self.btn_reset.clicked.connect(self.reset_current_page)

        self.btn_add_text = QPushButton("➕ Yazı Kutusu Ekle")
        self.btn_add_text.clicked.connect(self.add_manual_text)

        self.btn_toggle = QPushButton("👁️ Orijinali Gör")
        self.btn_toggle.clicked.connect(self.toggle_original_view)

        btn_export = QPushButton("💾 PDF Olarak Çıkar")
        btn_export.clicked.connect(self.export_to_pdf)
        btn_settings = QPushButton("⚙️ Ayarlar")
        btn_settings.clicked.connect(self.open_settings)

        self.btn_paint = QPushButton("🖌️ Fırça")
        self.btn_paint.setCheckable(True)
        self.btn_paint.clicked.connect(self.toggle_paint_mode)

        self.btn_fill = QPushButton("🔲 Kapla")
        self.btn_fill.setCheckable(True)
        self.btn_fill.clicked.connect(self.toggle_fill_mode)

        self.btn_picker = QPushButton("💧 Damlalık")
        self.btn_picker.setCheckable(True)
        self.btn_picker.clicked.connect(self.toggle_picker_mode)

        self.spin_brush = QSpinBox()
        self.spin_brush.setRange(2, 200)
        self.spin_brush.setValue(15)
        self.spin_brush.valueChanged.connect(self.update_brush_size)

        self.lbl_current_color = QLabel()
        self.lbl_current_color.setFixedSize(20, 20)
        self.lbl_current_color.setStyleSheet("background-color: #ffffff; border: 1px solid gray;")

        tb.addWidget(btn_load); tb.addWidget(btn_load_proj); tb.addWidget(btn_save_proj); tb.addWidget(btn_analyze); tb.addWidget(self.btn_reset); tb.addWidget(self.btn_add_text); tb.addWidget(self.btn_toggle); tb.addWidget(btn_export);
        tb.addWidget(QLabel(" | ")); tb.addWidget(self.btn_paint); tb.addWidget(self.btn_fill); tb.addWidget(self.btn_picker); tb.addWidget(QLabel("Boyut:")); tb.addWidget(self.spin_brush); tb.addWidget(self.lbl_current_color)
        tb.addStretch(); tb.addWidget(btn_settings)
        main_layout.addLayout(tb)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        left = QWidget(); left_lay = QVBoxLayout(left); left_lay.setContentsMargins(0, 0, 0, 0)
        lbl_pages = QLabel("Sayfalar"); lbl_pages.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_list = QListWidget()
        self.page_list.setIconSize(QSize(100, 150)); self.page_list.itemClicked.connect(self.on_page_selected)
        left_lay.addWidget(lbl_pages); left_lay.addWidget(self.page_list)

        left_footer = QLabel('v0.5 | <a href="https://github.com/Sefflex" style="color: #3498db; text-decoration: none;">Sefflex</a>')
        left_footer.setOpenExternalLinks(True)
        left_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_lay.addWidget(left_footer)

        mid = QFrame(); mid_lay = QVBoxLayout(mid)
        self.canvas = CanvasView(self)
        mid_lay.addWidget(self.canvas)

        right = QWidget(); right_lay = QVBoxLayout(right); right_lay.setContentsMargins(10, 10, 10, 10)
        lbl_edit = QLabel("Bireysel Hızlı Ayar Paneli\n(Sahnede Yazıya Tıklayın)"); lbl_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_lay.addWidget(lbl_edit)

        self.txt_original = QTextEdit(); self.txt_original.setMinimumHeight(40)
        self.txt_original.textChanged.connect(self.on_panel_changed)
        self.txt_translated = QTextEdit(); self.txt_translated.setMinimumHeight(60)
        self.txt_translated.textChanged.connect(self.on_panel_changed)

        form_r = QFormLayout()
        self.spin_size = QSpinBox(); self.spin_size.setRange(8, 200)
        self.spin_size.valueChanged.connect(self.on_panel_changed)
        self.slider_width = QSlider(Qt.Orientation.Horizontal); self.slider_width.setRange(50, 800)
        self.slider_width.valueChanged.connect(self.on_panel_changed)
        self.slider_height = QSlider(Qt.Orientation.Horizontal); self.slider_height.setRange(50, 800)
        self.slider_height.valueChanged.connect(self.on_panel_changed)

        self.btn_color_text = QPushButton("Siyah")
        self.btn_color_text.clicked.connect(self.choose_text_color)
        self.btn_color_stroke = QPushButton("Beyaz")
        self.btn_color_stroke.clicked.connect(self.choose_stroke_color)

        self.chk_stroke = QCheckBox("Göster")
        self.chk_stroke.setChecked(True)
        self.chk_stroke.stateChanged.connect(self.on_panel_changed)

        stroke_lay = QHBoxLayout()
        stroke_lay.setContentsMargins(0,0,0,0)
        stroke_lay.addWidget(self.btn_color_stroke)
        stroke_lay.addWidget(self.chk_stroke)

        self.chk_bold = QCheckBox("Kalın (Bold)")
        self.chk_bold.stateChanged.connect(self.on_panel_changed)

        form_r.addRow("Yazı Rengi:", self.btn_color_text)
        form_r.addRow("Dış Çizgi:", stroke_lay)
        form_r.addRow("Stil:", self.chk_bold)
        form_r.addRow("Font Boyutu:", self.spin_size)
        form_r.addRow("Kutu Genişliği:", self.slider_width)
        form_r.addRow("Kutu Yüksekliği:", self.slider_height)

        right_lay.addWidget(QLabel("Orijinal İbare (Değiştirilebilir):")); right_lay.addWidget(self.txt_original)
        right_lay.addWidget(QLabel("Çeviri İçeriği (Anlık Değişir):")); right_lay.addWidget(self.txt_translated)
        right_lay.addLayout(form_r)

        self.btn_save_preset = QPushButton("💾 Ön Ayar Kaydet")
        self.btn_save_preset.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        self.btn_save_preset.clicked.connect(self.save_text_preset)
        right_lay.addWidget(self.btn_save_preset)

        btn_tr = QPushButton("⭐ Sadece Metni Çevir (Seçili Kutu)")
        btn_tr.setStyleSheet("background-color: #1e67b2; color: #ffffff;")
        btn_tr.clicked.connect(self.translate_selected_node)
        right_lay.addWidget(btn_tr)

        self.btn_ocr = QPushButton("🔍 Seçerek Oku && Yeni Kutu Ekle")
        self.btn_ocr.setCheckable(True)
        self.btn_ocr.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.btn_ocr.clicked.connect(self.toggle_ocr_mode)
        right_lay.addWidget(self.btn_ocr)

        right_lay.addStretch()

        tip = QLabel("İpucu: Ekrandaki herhangi bir yazıyı farenizle sürükleyip istediğiniz yere bırakabilirsiniz. Çöpe atmak için Backspace'e basabilirsiniz.")
        tip.setWordWrap(True); tip.setStyleSheet("color: #aaa; font-size: 11px;")
        right_lay.addWidget(tip)

        splitter.addWidget(left); splitter.addWidget(mid); splitter.addWidget(right)
        splitter.setSizes([200, 850, 350])

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
                    node.setPos(nd["pos_x"], nd["pos_y"])
                    node.update_visual()
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
        self.btn_color_text.setStyleSheet(f"background-color: rgb({node.text_color[0]},{node.text_color[1]},{node.text_color[2]}); color: white;")
        self.btn_color_stroke.setStyleSheet(f"background-color: rgb({node.stroke_color[0]},{node.stroke_color[1]},{node.stroke_color[2]}); color: black;")
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
            "has_stroke": getattr(node, 'has_stroke', True)
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
            self.btn_toggle.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
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
        self.setStyleSheet("QMainWindow { background-color: #202020; } QWidget { color: #ececec; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; } QPushButton { background-color: #3f4244; padding: 6px; border: 1px solid #555; border-radius: 4px; } QPushButton:hover { background-color: #4f5254; } QLineEdit { background-color: #1e1e1e; padding: 6px; } QListWidget, QTextEdit, QGraphicsView { background-color: #1a1a1a; border: 1px solid #444; }")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CizgiArsivApp()
    window.show()
    sys.exit(app.exec())

