"""Marca CEASAMINAS (losango verde/dourado) desenhada vetorialmente com QPainter.

Recriação aproximada do logotipo oficial (4 triângulos formando um losango: três em
verde e um em dourado, apontando para fora). Usada como ícone da janela/aplicativo
enquanto os arquivos oficiais (PNG/ICO) não são incorporados ao projeto — ver README
para instruções de como substituir por assets exatos em `assets/`.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap, QPolygonF

from src.gui.styles import COLOR_GOLD, COLOR_GREEN

_TRIANGLES = [
    # (ponta_x, ponta_y, é_dourado) em coordenadas normalizadas (-1..1), ponta para fora
    ("up", False),
    ("down", False),
    ("left", False),
    ("right", True),
]


def _triangle_points(direction: str, size: float, center: float) -> QPolygonF:
    """Triângulo apontando para `direction`, com a base voltada para o centro do losango."""
    tip = {
        "up": QPointF(center, center - size),
        "down": QPointF(center, center + size),
        "left": QPointF(center - size, center),
        "right": QPointF(center + size, center),
    }[direction]

    half_base = size * 0.62
    if direction in ("up", "down"):
        base_y = center + (size * 0.12 if direction == "up" else -size * 0.12)
        p1 = QPointF(center - half_base, base_y)
        p2 = QPointF(center + half_base, base_y)
    else:
        base_x = center + (size * 0.12 if direction == "left" else -size * 0.12)
        p1 = QPointF(base_x, center - half_base)
        p2 = QPointF(base_x, center + half_base)

    return QPolygonF([tip, p1, p2])


def ceasaminas_mark_pixmap(diameter: int = 64) -> QPixmap:
    """Gera o losango CEASAMINAS como QPixmap com fundo transparente."""
    pixmap = QPixmap(diameter, diameter)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)

    center = diameter / 2
    size = diameter * 0.42

    for direction, is_gold in _TRIANGLES:
        painter.setBrush(QColor(COLOR_GOLD if is_gold else COLOR_GREEN))
        painter.drawPolygon(_triangle_points(direction, size, center))

    painter.end()
    return pixmap
