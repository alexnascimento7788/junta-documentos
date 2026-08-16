"""Lista visual de PDFs com reordenação por arrastar-e-soltar e botões ↑ / ↓."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.pdf_merger import PdfInfo

_ACCENT_PALETTE = [
    "#7c5cff", "#3ddc97", "#ff9f5b", "#5bc0ff",
    "#ff6b81", "#c792ea", "#ffd166", "#4dd0e1",
]


def _circle_pixmap(text: str, seed: int, diameter: int = 40) -> QPixmap:
    """Gera um ícone circular colorido com as iniciais do nome do arquivo."""
    color = QColor(_ACCENT_PALETTE[seed % len(_ACCENT_PALETTE)])
    pixmap = QPixmap(diameter, diameter)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(color)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, diameter, diameter)

    painter.setPen(QColor("#ffffff"))
    font = QFont("Segoe UI", 13, QFont.Bold)
    painter.setFont(font)
    initials = "".join(part[0].upper() for part in text.replace("_", " ").replace("-", " ").split()[:2]) or "P"
    painter.drawText(pixmap.rect(), Qt.AlignCenter, initials)
    painter.end()
    return pixmap


class PdfListItemWidget(QWidget):
    """Widget exibido para cada PDF: círculo colorido, nome, número de páginas e posição."""

    def __init__(self, pdf_info: PdfInfo, order: int, seed: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.pdf_path = pdf_info.path

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        self.order_label = QLabel(f"{order:02d}")
        self.order_label.setFixedWidth(28)
        self.order_label.setStyleSheet("color: #9a9cb5; font-weight: 600; font-size: 13px;")
        layout.addWidget(self.order_label)

        avatar = QLabel()
        avatar.setPixmap(_circle_pixmap(pdf_info.name, seed))
        avatar.setFixedSize(40, 40)
        layout.addWidget(avatar)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        name_label = QLabel(pdf_info.name)
        name_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        name_label.setToolTip(str(pdf_info.path))
        pages_label = QLabel(f"{pdf_info.page_count} página(s)")
        pages_label.setStyleSheet("color: #9a9cb5; font-size: 11px;")
        text_layout.addWidget(name_label)
        text_layout.addWidget(pages_label)
        layout.addLayout(text_layout, stretch=1)

        drag_hint = QLabel("⠿")
        drag_hint.setStyleSheet("color: #5a5d78; font-size: 16px;")
        layout.addWidget(drag_hint)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_order(self, order: int) -> None:
        self.order_label.setText(f"{order:02d}")


class PdfListWidget(QListWidget):
    """QListWidget configurada para reordenação interna via drag & drop."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setSpacing(2)
        self._infos: dict[str, PdfInfo] = {}

    def add_pdf(self, pdf_info: PdfInfo) -> None:
        self._infos[str(pdf_info.path)] = pdf_info
        self._append_item(pdf_info, order=self.count() + 1, seed=self.count())

    def _append_item(self, pdf_info: PdfInfo, order: int, seed: int) -> None:
        item = QListWidgetItem(self)
        item.setData(Qt.UserRole, str(pdf_info.path))
        item.setSizeHint(QSize(0, 64))
        widget = PdfListItemWidget(pdf_info, order=order, seed=seed)
        self.setItemWidget(item, widget)

    def clear_pdfs(self) -> None:
        self.clear()
        self._infos.clear()

    def ordered_paths(self) -> list[Path]:
        paths: list[Path] = []
        for i in range(self.count()):
            item = self.item(i)
            paths.append(Path(item.data(Qt.UserRole)))
        return paths

    def refresh_order_labels(self) -> None:
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, PdfListItemWidget):
                widget.set_order(i + 1)

    def _rebuild_from_paths(self, paths: list[Path], selected_row: int) -> None:
        """Reconstrói todos os itens na ordem de `paths` (necessário pois o Qt destrói
        widgets customizados ao mover/remover itens de um QListWidget)."""
        self.clear()
        for seed, path in enumerate(paths):
            info = self._infos[str(path)]
            self._append_item(info, order=seed + 1, seed=seed)
        if 0 <= selected_row < self.count():
            self.setCurrentRow(selected_row)

    def move_selected(self, offset: int) -> None:
        row = self.currentRow()
        if row < 0:
            return
        new_row = row + offset
        if not (0 <= new_row < self.count()):
            return
        paths = self.ordered_paths()
        paths[row], paths[new_row] = paths[new_row], paths[row]
        self._rebuild_from_paths(paths, selected_row=new_row)

    def dropEvent(self, event) -> None:  # noqa: N802 (nome definido pela API do Qt)
        super().dropEvent(event)
        # Após o drop interno, os widgets customizados dos itens movidos são perdidos;
        # reconstruímos a lista inteira preservando a nova ordem.
        paths = self.ordered_paths()
        self._rebuild_from_paths(paths, selected_row=self.currentRow())
