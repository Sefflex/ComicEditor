"""
ComicEditor — Canvas görünümü (CanvasView)
Zoom, pan, fırça, damlalık, dolgu ve seçim modlarını yönetir.
"""
from PyQt6.QtWidgets import QGraphicsView  # type: ignore
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush  # type: ignore
from PyQt6.QtCore import Qt, QRectF  # type: ignore
from nodes import DraggableTextNode


class CanvasView(QGraphicsView):
    """Ana canvas görünümü — çizim, boyama ve metin düğümü etkileşimi."""

    def __init__(self, main_app, parent=None):
        super().__init__(parent)  # type: ignore
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
            from PyQt6.QtWidgets import QGraphicsRectItem  # type: ignore
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
                        self.main_app.lbl_current_color.setStyleSheet(
                            f"background-color: {color.name()}; border: 2px solid rgba(255,255,255,0.08); border-radius: 12px;"
                        )
                        self.main_app.btn_picker.setChecked(False)
                        self.main_app.btn_paint.setChecked(True)
                        self.main_app.toggle_paint_mode(True)
            return

        if self.fill_mode and event.button() == Qt.MouseButton.LeftButton:
            from PyQt6.QtWidgets import QGraphicsRectItem  # type: ignore
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
                if "undo_stack" not in page:
                    page["undo_stack"] = []
                page["undo_stack"].append(page["clean_qpix"].copy())
                if len(page["undo_stack"]) > 20:
                    page["undo_stack"].pop(0)
            self.last_point = self.mapToScene(event.pos())
            self.paint_on_bg(self.last_point, self.last_point)
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.select_mode and self.selection_start and (event.buttons() & Qt.MouseButton.LeftButton):
            curr = self.mapToScene(event.pos())
            r = QRectF(self.selection_start, curr).normalized()
            if self.selection_rect_item:
                self.selection_rect_item.setRect(r)  # type: ignore
            return

        if self.fill_mode and self.fill_start and (event.buttons() & Qt.MouseButton.LeftButton):
            curr = self.mapToScene(event.pos())
            r = QRectF(self.fill_start, curr).normalized()
            if self.fill_rect_item:
                self.fill_rect_item.setRect(r)  # type: ignore
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
            if self.selection_rect_item:
                self.scene().removeItem(self.selection_rect_item)
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
            if self.fill_rect_item:
                self.scene().removeItem(self.fill_rect_item)
            self.fill_start = None
            self.fill_rect_item = None

            if self.main_app.current_page_idx != -1:
                page = self.main_app.pages[self.main_app.current_page_idx]
                if "undo_stack" not in page:
                    page["undo_stack"] = []
                page["undo_stack"].append(page["clean_qpix"].copy())
                if len(page["undo_stack"]) > 20:
                    page["undo_stack"].pop(0)
            self.fill_on_bg(rect)
            return

        if self.paint_mode and event.button() == Qt.MouseButton.LeftButton:
            self.last_point = None
            return
        super().mouseReleaseEvent(event)

    def fill_on_bg(self, rect: QRectF):
        if self.main_app.current_page_idx == -1:
            return
        page = self.main_app.pages[self.main_app.current_page_idx]
        if "clean_qpix" not in page:
            return

        qpix = page["clean_qpix"]
        painter = QPainter(qpix)
        painter.setBrush(QBrush(self.brush_color))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawRect(rect)
        painter.end()
        page["bg_item"].setPixmap(qpix)

    def paint_on_bg(self, p1, p2):
        if self.main_app.current_page_idx == -1:
            return
        page = self.main_app.pages[self.main_app.current_page_idx]
        if "clean_qpix" not in page:
            return

        qpix = page["clean_qpix"]
        painter = QPainter(qpix)
        pen = QPen(self.brush_color, self.brush_size, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(p1, p2)
        painter.end()
        page["bg_item"].setPixmap(qpix)

    def keyPressEvent(self, event):
        from PyQt6.QtGui import QKeySequence  # type: ignore
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
        if event.angleDelta().y() > 0:
            self.scale(self.zoom_factor, self.zoom_factor)
        else:
            self.scale(1.0 / self.zoom_factor, 1.0 / self.zoom_factor)
