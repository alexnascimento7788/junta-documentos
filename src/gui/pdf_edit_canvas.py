"""Canvas de edição: exibe a página renderizada e captura marcações do usuário (mouse)."""

from __future__ import annotations

from typing import Literal, Optional

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPaintEvent, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from src.gui.styles import COLOR_DANGER

ToolMode = Literal["redact", "text"]

_MIN_DRAG_PX = 4  # abaixo disso, tratamos como clique acidental e ignoramos


class PdfEditCanvas(QWidget):
    """Mostra a página atual em tamanho real (px) e emite sinais com coordenadas em pontos PDF."""

    redaction_requested = Signal(tuple)  # (x0, y0, x1, y1) em pontos PDF
    text_position_requested = Signal(tuple)  # (x, y) em pontos PDF

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: Optional[QPixmap] = None
        self._zoom = 1.0
        self._tool: ToolMode = "redact"
        self._drag_start: Optional[QPoint] = None
        self._drag_current: Optional[QPoint] = None
        self.setMinimumSize(200, 200)
        self.setCursor(Qt.CrossCursor)

    def set_tool(self, tool: ToolMode) -> None:
        self._tool = tool
        self._drag_start = None
        self._drag_current = None
        self.setCursor(Qt.CrossCursor if tool == "redact" else Qt.IBeamCursor)
        self.update()

    def set_page(self, width_px: int, height_px: int, rgb_bytes: bytes, zoom: float) -> None:
        """Recebe os pixels RGB (3 bytes/pixel, sem alfa) já renderizados pela sessão de edição."""
        image = QImage(rgb_bytes, width_px, height_px, width_px * 3, QImage.Format_RGB888).copy()
        self._pixmap = QPixmap.fromImage(image)
        self._zoom = zoom
        self.setFixedSize(width_px, height_px)
        self.update()

    def clear_page(self) -> None:
        self._pixmap = None
        self.setFixedSize(200, 200)
        self.update()

    def _to_pdf_point(self, pos: QPoint) -> tuple[float, float]:
        return pos.x() / self._zoom, pos.y() / self._zoom

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        if self._pixmap is not None:
            painter.drawPixmap(0, 0, self._pixmap)
        else:
            painter.fillRect(self.rect(), QColor("#e8ebe8"))

        if self._tool == "redact" and self._drag_start is not None and self._drag_current is not None:
            rect = QRect(self._drag_start, self._drag_current).normalized()
            painter.setPen(QPen(QColor(COLOR_DANGER), 2))
            fill = QColor(COLOR_DANGER)
            fill.setAlpha(90)
            painter.setBrush(fill)
            painter.drawRect(rect)
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._pixmap is None:
            return
        pos = event.position().toPoint()
        if self._tool == "redact":
            self._drag_start = pos
            self._drag_current = pos
        elif self._tool == "text":
            self.text_position_requested.emit(self._to_pdf_point(pos))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._tool == "redact" and self._drag_start is not None:
            self._drag_current = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._tool != "redact" or self._drag_start is None:
            return
        end = event.position().toPoint()
        rect = QRect(self._drag_start, end).normalized()
        self._drag_start = None
        self._drag_current = None
        self.update()

        if rect.width() < _MIN_DRAG_PX or rect.height() < _MIN_DRAG_PX:
            return

        x0, y0 = self._to_pdf_point(rect.topLeft())
        x1, y1 = self._to_pdf_point(rect.bottomRight())
        self.redaction_requested.emit((x0, y0, x1, y1))
