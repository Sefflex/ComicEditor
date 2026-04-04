"""
ComicEditor — Sürüklenebilir metin düğümü (DraggableTextNode)
Canvas üzerinde çeviri metinlerini konumlandırmak için kullanılır.
"""
import textwrap
from PIL import Image, ImageDraw, ImageFont  # type: ignore
from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem  # type: ignore
from PyQt6.QtGui import QPixmap, QImage  # type: ignore
from PyQt6.QtCore import Qt  # type: ignore


class DraggableTextNode(QGraphicsPixmapItem):
    """Canvas üzerinde sürüklenebilir, düzenlenebilir metin kutusu."""

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
        """Metin görselini Pillow ile render edip QPixmap'e çevirir."""
        text = self.translated_text.replace("i", "İ").replace("ı", "I").upper()
        if not text:
            self.setPixmap(QPixmap())
            return

        dummy_img = Image.new('RGBA', (1, 1))
        draw = ImageDraw.Draw(dummy_img)

        if self.is_auto:
            target_size = self.font_size
            best_font = None
            best_wrapped = text
            best_size = 12
            tw, th = 0, 0

            for size in range(target_size + 4, 9, -1):
                try:
                    font = ImageFont.truetype(self.font_path, size)
                except Exception:
                    font = ImageFont.load_default()

                try:
                    avg_char_w = draw.textlength("O", font=font)
                except AttributeError:
                    avg_char_w = font.getsize("O")[0] if hasattr(font, 'getsize') else size * 0.5  # type: ignore

                chars_per_line = max(5, int(self.box_w / (avg_char_w if avg_char_w > 0 else 1)))
                wrapped = textwrap.fill(text, width=chars_per_line)

                try:
                    bbox = draw.textbbox((0, 0), wrapped, font=font, align=self.align)
                    cw, ch = bbox[2] - bbox[0], bbox[3] - bbox[1]
                except AttributeError:
                    cw, ch = draw.textsize(wrapped, font=font)  # type: ignore

                if cw <= self.box_w + 5 and ch <= self.box_h + 5:
                    best_font = font
                    best_wrapped = wrapped
                    best_size = size
                    tw, th = cw, ch
                    break

            if not best_font:
                best_size = 10
                try:
                    best_font = ImageFont.truetype(self.font_path, best_size)
                except Exception:
                    best_font = ImageFont.load_default()

                try:
                    avg_char_w = draw.textlength("O", font=best_font)
                except AttributeError:
                    avg_char_w = best_font.getsize("O")[0] if hasattr(best_font, 'getsize') else 10 * 0.5  # type: ignore

                wrapped = textwrap.fill(text, width=max(4, int(self.box_w / (avg_char_w if avg_char_w > 0 else 1))))
                best_wrapped = wrapped
                try:
                    bbox = draw.textbbox((0, 0), wrapped, font=best_font, align=self.align)
                    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                except AttributeError:
                    tw, th = draw.textsize(wrapped, font=best_font)  # type: ignore

            self.font_size = best_size
            final_font = best_font
            final_wrapped = best_wrapped
        else:
            try:
                final_font = ImageFont.truetype(self.font_path, self.font_size)
            except Exception:
                final_font = ImageFont.load_default()

            try:
                avg_char_w = draw.textlength("O", font=final_font)
            except AttributeError:
                avg_char_w = final_font.getsize("O")[0] if hasattr(final_font, 'getsize') else self.font_size * 0.5  # type: ignore

            chars_per_line = max(5, int(self.box_w / (avg_char_w if avg_char_w > 0 else 1)))
            final_wrapped = textwrap.fill(text, width=chars_per_line)
            try:
                bbox = draw.textbbox((0, 0), final_wrapped, font=final_font, align=self.align)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except AttributeError:
                tw, th = draw.textsize(final_wrapped, font=final_font)  # type: ignore

        tw, th = int(max(1, tw)), int(max(1, th))

        if not self.is_auto:
            final_w = int(max(tw + 20, self.box_w))
            final_h = int(max(th + 20, self.box_h))
        else:
            final_w = int(tw + 20)
            final_h = int(th + 20)

        start_x = (final_w - tw) // 2
        start_y = (final_h - th) // 2

        img = Image.new('RGBA', (final_w, final_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        if getattr(self, 'has_stroke', True):
            stroke_val: int = int(max(1, self.font_size * 0.08))
            min_s: int = -stroke_val
            max_s: int = stroke_val + 1
            for dx in range(min_s, max_s):
                for dy in range(min_s, max_s):
                    if dx * dx + dy * dy <= stroke_val * stroke_val:
                        draw.multiline_text(
                            (start_x + 10 + dx, start_y + 10 + dy),
                            final_wrapped, fill=self.stroke_color,
                            font=final_font, align=self.align
                        )

        if self.is_bold:
            draw.multiline_text((start_x + 9, start_y + 10), final_wrapped, fill=self.text_color, font=final_font, align=self.align)
            draw.multiline_text((start_x + 11, start_y + 10), final_wrapped, fill=self.text_color, font=final_font, align=self.align)
            draw.multiline_text((start_x + 10, start_y + 9), final_wrapped, fill=self.text_color, font=final_font, align=self.align)
            draw.multiline_text((start_x + 10, start_y + 11), final_wrapped, fill=self.text_color, font=final_font, align=self.align)

        draw.multiline_text((start_x + 10, start_y + 10), final_wrapped, fill=self.text_color, font=final_font, align=self.align)

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
            if self.isSelected():
                self.main_app.on_node_selected(self)
        return super().itemChange(change, value)
