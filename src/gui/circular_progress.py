"""Indicador de progresso circular com transição de cor (vermelho → amarelo → verde)."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

COLOR_TRACK = QColor("#3a3d54")
COLOR_RED = QColor("#ff6b81")
COLOR_YELLOW = QColor("#ffd166")
COLOR_GREEN = QColor("#3ddc97")
COLOR_TEXT = QColor("#e8e8f0")

THRESHOLD_YELLOW = 70
THRESHOLD_GREEN = 95


def color_for_value(value: int) -> QColor:
    if value >= THRESHOLD_GREEN:
        return COLOR_GREEN
    if value >= THRESHOLD_YELLOW:
        return COLOR_YELLOW
    return COLOR_RED


class CircularProgressWidget(QWidget):
    """Anel de progresso desenhado manualmente, com percentual no centro."""

    def __init__(self, parent: QWidget | None = None, diameter: int = 150, stroke_width: int = 12) -> None:
        super().__init__(parent)
        self._value = 0  # 0..100
        self._diameter = diameter
        self._stroke_width = stroke_width
        self._label = ""
        self.setFixedSize(diameter, diameter)

    def setValue(self, value: int) -> None:  # noqa: N802 - convenção Qt de nomeação
        self._value = max(0, min(100, value))
        self.update()

    def value(self) -> int:
        return self._value

    def setLabel(self, text: str) -> None:  # noqa: N802
        self._label = text
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        margin = self._stroke_width / 2 + 2
        rect = QRectF(margin, margin, self._diameter - 2 * margin, self._diameter - 2 * margin)

        # Trilha de fundo
        track_pen = QPen(COLOR_TRACK, self._stroke_width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 0, 360 * 16)

        # Arco de progresso
        if self._value > 0:
            progress_pen = QPen(color_for_value(self._value), self._stroke_width, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(progress_pen)
            span_angle = int(360 * 16 * (self._value / 100))
            start_angle = 90 * 16  # começa no topo
            painter.drawArc(rect, start_angle, -span_angle)

        # Percentual no centro
        painter.setPen(COLOR_TEXT)
        font = QFont("Segoe UI", 20, QFont.Bold)
        painter.setFont(font)
        text_rect = QRectF(0, 0, self._diameter, self._diameter)
        painter.drawText(text_rect, Qt.AlignCenter, f"{self._value}%")

        painter.end()
