"""Canvas de edição: exibe a página renderizada e captura marcações do usuário (mouse)."""

from __future__ import annotations

from typing import Literal, Optional

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPaintEvent, QPen, QPixmap
from PySide6.QtWidgets import QWidget

ToolMode = Literal["redact", "text"]

_MIN_DRAG_PX = 4  # abaixo disso, tratamos como clique acidental e ignoramos


class PdfEditCanvas(QWidget):
    """Mostra a página atual em tamanho real (px) e emite sinais com coordenadas em pontos PDF.

    As redações ainda não salvas são desenhadas por este widget, com a cor exata escolhida
    pelo usuário — o MuPDF, por padrão, renderiza uma marcação de redação pendente (ainda
    não aplicada) com um "X" vermelho fixo, ignorando a cor configurada; essa aparência só
    reflete a cor real depois que o PDF é salvo. Para a pré-visualização ficar correta desde
    já, desenhamos nós mesmos um retângulo sólido com a cor escolhida por cima da página.
    """

    redaction_requested = Signal(tuple)  # (x0, y0, x1, y1) em pontos PDF
    text_position_requested = Signal(tuple)  # (x, y) em pontos PDF

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: Optional[QPixmap] = None
        self._zoom = 1.0
        self._tool: ToolMode = "redact"
        self._redact_color = QColor("#000000")
        self._pending_redactions: list[tuple[tuple[float, float, float, float], str]] = []
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

    def set_redact_color(self, color_hex: str) -> None:
        """Cor usada no retângulo de pré-visualização enquanto o usuário arrasta o mouse."""
        self._redact_color = QColor(color_hex)
        self.update()

    def set_page(self, width_px: int, height_px: int, rgb_bytes: bytes, zoom: float) -> None:
        """Recebe os pixels RGB (3 bytes/pixel, sem alfa) já renderizados pela sessão de edição."""
        image = QImage(rgb_bytes, width_px, height_px, width_px * 3, QImage.Format_RGB888).copy()
        self._pixmap = QPixmap.fromImage(image)
        self._zoom = zoom
        self.setFixedSize(width_px, height_px)
        self.update()

    def set_pending_redactions(self, overlays: list[tuple[tuple[float, float, float, float], str]]) -> None:
        """Retângulos (em pontos PDF) + cor de cada redação já marcada nesta página, mas
        ainda não salva — desenhados por cima da página para uma pré-visualização fiel."""
        self._pending_redactions = overlays
        self.update()

    def clear_page(self) -> None:
        self._pixmap = None
        self._pending_redactions = []
        self.setFixedSize(200, 200)
        self.update()

    def _to_pdf_point(self, pos: QPoint) -> tuple[float, float]:
        return pos.x() / self._zoom, pos.y() / self._zoom

    def _to_pixel_rect(self, rect_pt: tuple[float, float, float, float]) -> QRect:
        x0, y0, x1, y1 = rect_pt
        return QRect(
            int(x0 * self._zoom),
            int(y0 * self._zoom),
            int((x1 - x0) * self._zoom),
            int((y1 - y0) * self._zoom),
        )

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        if self._pixmap is not None:
            painter.drawPixmap(0, 0, self._pixmap)
        else:
            painter.fillRect(self.rect(), QColor("#e8ebe8"))

        # Redações já marcadas nesta página (cor final, sólida — como ficará após salvar).
        painter.setPen(Qt.NoPen)
        for rect_pt, color_hex in self._pending_redactions:
            painter.setBrush(QColor(color_hex))
            painter.drawRect(self._to_pixel_rect(rect_pt))

        # Retângulo sendo arrastado agora (ainda não confirmado) — mesma cor, semitransparente.
        if self._tool == "redact" and self._drag_start is not None and self._drag_current is not None:
            rect = QRect(self._drag_start, self._drag_current).normalized()
            preview_fill = QColor(self._redact_color)
            preview_fill.setAlpha(140)
            painter.setPen(QPen(self._redact_color, 2))
            painter.setBrush(preview_fill)
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
