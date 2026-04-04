"""
ComicEditor — Özel UI bileşenleri
CollapsibleSection: Açılır/kapanır panel bölümü
GlowButton: Hover'da parıltı efekti veren buton
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton  # type: ignore
from PyQt6.QtGui import QColor  # type: ignore
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve  # type: ignore


class CollapsibleSection(QWidget):
    """Açılır/kapanır modüler panel bölümü (modern inspector tarzı)."""

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
        self.content_layout.setContentsMargins(14, 10, 14, 14)
        self.content_layout.setSpacing(10)

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


class GlowButton(QPushButton):
    """
    Hover'da yumuşak parıltı (glow) efekti veren premium buton.
    QGraphicsDropShadowEffect ile mor glow animasyonu uygular.
    """

    def __init__(self, *args, glow_color=None, glow_radius=22, **kwargs):
        super().__init__(*args, **kwargs)
        self._glow_color = glow_color or QColor(124, 108, 247, 70)
        self._glow_radius = glow_radius

        # QGraphicsDropShadowEffect ile glow efekti
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect  # type: ignore
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0)
        self._shadow.setColor(QColor(0, 0, 0, 0))
        self._shadow.setOffset(0, 2)
        self.setGraphicsEffect(self._shadow)

        # Animasyon
        self._anim = QPropertyAnimation(self._shadow, b"blurRadius")
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def enterEvent(self, event):
        self._shadow.setColor(self._glow_color)
        self._anim.stop()
        self._anim.setStartValue(self._shadow.blurRadius())
        self._anim.setEndValue(self._glow_radius)
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._shadow.blurRadius())
        self._anim.setEndValue(0)
        self._anim.start()
        super().leaveEvent(event)
