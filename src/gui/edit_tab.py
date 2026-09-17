"""Aba de edição de PDF: anonimização (redação real) e inserção de texto, página a página."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.core.pdf_editor import PdfEditError, PdfEditSession
from src.gui.circular_progress import CircularProgressWidget
from src.gui.pdf_edit_canvas import PdfEditCanvas
from src.gui.styles import COLOR_BORDER, COLOR_GREEN, COLOR_TEXT_MUTED
from src.utils.file_utils import sanitize_output_filename, unique_path

APP_TITLE = "DocJoin"

# Largura-alvo de renderização (px). A página é escalada para caber nessa largura,
# mantendo a proporção — suficiente para marcar áreas com precisão sem consumir memória
# excessiva mesmo em documentos de 50+ páginas (apenas 1 página fica em memória por vez).
RENDER_TARGET_WIDTH_PX = 900

# Cores rápidas para a tarja de anonimização / texto inserido. Preto e branco cobrem os
# casos mais comuns (branco "some" com o fundo da página); as demais são só atalhos.
_PRESET_COLORS = ["#000000", "#FFFFFF", "#808080", "#D64545", "#1C7C3E"]
_DEFAULT_REDACT_COLOR = "#000000"
_DEFAULT_TEXT_COLOR = "#000000"


class SaveEditsWorker(QThread):
    """Aplica as redações pendentes e salva o PDF editado em uma thread separada."""

    progress = Signal(int, int)
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, session: PdfEditSession, output_path: Path) -> None:
        super().__init__()
        self._session = session
        self._output_path = output_path

    def run(self) -> None:
        try:
            result = self._session.save(
                self._output_path,
                progress_callback=lambda i, total: self.progress.emit(i, total),
            )
            self.finished_ok.emit(str(result))
        except PdfEditError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - reporta qualquer falha inesperada na UI
            self.failed.emit(f"Erro inesperado: {exc}")


class PdfEditTab(QWidget):
    """Painel esquerdo de ações + canvas de edição à direita."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session = PdfEditSession()
        self._source_path: Path | None = None
        self._output_dir: Path | None = None
        self._current_page = 0
        self._save_worker: SaveEditsWorker | None = None
        self._redact_color_hex = _DEFAULT_REDACT_COLOR
        self._text_color_hex = _DEFAULT_TEXT_COLOR

        self._build_ui()
        self.canvas.set_redact_color(self._redact_color_hex)
        self._refresh_color_selection()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_left_panel(), stretch=0)
        layout.addWidget(self._build_canvas_panel(), stretch=1)

    def _build_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("LeftPanel")
        panel.setFixedWidth(320)
        v = QVBoxLayout(panel)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(10)

        v.addWidget(self._section_label("Documento de origem"))
        self.source_label = QLabel("Nenhum PDF selecionado")
        self.source_label.setObjectName("PathLabel")
        self.source_label.setWordWrap(True)
        v.addWidget(self.source_label)

        btn_open = QPushButton("📄  Selecionar PDF")
        btn_open.clicked.connect(self._on_select_source)
        v.addWidget(btn_open)

        v.addSpacing(12)
        v.addWidget(self._section_label("Navegação"))
        nav_row = QHBoxLayout()
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setObjectName("IconButton")
        self.btn_prev.setEnabled(False)
        self.btn_prev.clicked.connect(self._on_prev_page)
        self.page_label = QLabel("Página 0 de 0")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.btn_next = QPushButton("▶")
        self.btn_next.setObjectName("IconButton")
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self._on_next_page)
        nav_row.addWidget(self.btn_prev)
        nav_row.addWidget(self.page_label, stretch=1)
        nav_row.addWidget(self.btn_next)
        v.addLayout(nav_row)

        v.addSpacing(12)
        v.addWidget(self._section_label("Ferramenta"))
        self.tool_combo = QComboBox()
        self.tool_combo.addItem("Anonimizar (cobrir área)", "redact")
        self.tool_combo.addItem("Adicionar texto", "text")
        self.tool_combo.currentIndexChanged.connect(self._on_tool_changed)
        v.addWidget(self.tool_combo)

        hint = QLabel(
            "Anonimizar: arraste sobre a área a ocultar — o conteúdo é removido de "
            "verdade ao salvar, não apenas coberto.\n\n"
            "Adicionar texto: clique no ponto onde o texto deve começar."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        v.addWidget(hint)

        v.addSpacing(6)
        self.color_section_label = self._section_label("Cor da tarja")
        v.addWidget(self.color_section_label)

        color_row = QHBoxLayout()
        color_row.setSpacing(6)
        self._swatch_buttons: dict[str, QPushButton] = {}
        for color_hex in _PRESET_COLORS:
            swatch = QPushButton()
            swatch.setFixedSize(26, 26)
            swatch.setCursor(Qt.PointingHandCursor)
            swatch.setToolTip(color_hex)
            swatch.clicked.connect(lambda _checked=False, c=color_hex: self._on_preset_color_clicked(c))
            color_row.addWidget(swatch)
            self._swatch_buttons[color_hex] = swatch

        self.custom_color_button = QPushButton("+")
        self.custom_color_button.setFixedSize(26, 26)
        self.custom_color_button.setCursor(Qt.PointingHandCursor)
        self.custom_color_button.setToolTip("Cor personalizada...")
        self.custom_color_button.clicked.connect(self._on_pick_custom_color)
        color_row.addWidget(self.custom_color_button)
        color_row.addStretch(1)
        v.addLayout(color_row)

        self.btn_undo = QPushButton("↩  Desfazer última marcação")
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self._on_undo)
        v.addWidget(self.btn_undo)

        v.addSpacing(12)
        v.addWidget(self._section_label("Arquivo de saída"))

        self.output_name_edit = QLineEdit("documento_editado.pdf")
        v.addWidget(self.output_name_edit)

        self.output_dir_label = QLabel("Nenhuma pasta de destino selecionada")
        self.output_dir_label.setObjectName("PathLabel")
        self.output_dir_label.setWordWrap(True)
        v.addWidget(self.output_dir_label)

        btn_output = QPushButton("💾  Selecionar pasta de destino")
        btn_output.clicked.connect(self._on_select_output_dir)
        v.addWidget(btn_output)

        v.addStretch(1)

        progress_row = QHBoxLayout()
        self.progress_widget = CircularProgressWidget(diameter=110, stroke_width=9)
        self.progress_widget.setVisible(False)
        progress_row.addStretch(1)
        progress_row.addWidget(self.progress_widget)
        progress_row.addStretch(1)
        v.addLayout(progress_row)

        self.save_button = QPushButton("Salvar PDF editado")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._on_save_clicked)
        v.addWidget(self.save_button)

        return panel

    def _build_canvas_panel(self) -> QWidget:
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)

        self.canvas = PdfEditCanvas()
        self.canvas.redaction_requested.connect(self._on_redaction_requested)
        self.canvas.text_position_requested.connect(self._on_text_position_requested)
        self.scroll_area.setWidget(self.canvas)
        return self.scroll_area

    @staticmethod
    def _section_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionLabel")
        return label

    # ------------------------------------------------------------- ações

    def _on_select_source(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Selecionar PDF para edição", filter="Arquivos PDF (*.pdf)"
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            page_count = self._session.open(path)
        except PdfEditError as exc:
            QMessageBox.warning(self, APP_TITLE, str(exc))
            return

        self._source_path = path
        self.source_label.setText(str(path))
        self._current_page = 0
        self._render_current_page()
        self._update_nav_state(page_count)
        self._update_undo_state()
        self._update_save_button_state()

    def _render_current_page(self) -> None:
        if self._session.page_count == 0:
            self.canvas.clear_page()
            return
        page_width_pt, _ = self._session.page_size(self._current_page)
        zoom = RENDER_TARGET_WIDTH_PX / page_width_pt if page_width_pt else 1.0
        width_px, height_px, rgb_bytes = self._session.render_page(self._current_page, zoom=zoom)
        self.canvas.set_page(width_px, height_px, rgb_bytes, zoom)
        # O MuPDF sempre renderiza uma redação pendente com um "X" vermelho fixo, então
        # desenhamos nós mesmos a pré-visualização com a cor real escolhida, por cima.
        self.canvas.set_pending_redactions(self._session.pending_redactions_on_page(self._current_page))

    def _update_nav_state(self, total: int | None = None) -> None:
        total = total if total is not None else self._session.page_count
        self.page_label.setText(f"Página {self._current_page + 1} de {total}" if total else "Página 0 de 0")
        self.btn_prev.setEnabled(self._current_page > 0)
        self.btn_next.setEnabled(self._current_page < total - 1)

    def _on_prev_page(self) -> None:
        if self._current_page > 0:
            self._current_page -= 1
            self._render_current_page()
            self._update_nav_state()
            self._update_undo_state()

    def _on_next_page(self) -> None:
        if self._current_page < self._session.page_count - 1:
            self._current_page += 1
            self._render_current_page()
            self._update_nav_state()
            self._update_undo_state()

    def _on_tool_changed(self) -> None:
        self.canvas.set_tool(self.tool_combo.currentData())
        self._refresh_color_selection()

    def _current_color(self) -> str:
        return self._redact_color_hex if self.tool_combo.currentData() == "redact" else self._text_color_hex

    def _on_preset_color_clicked(self, color_hex: str) -> None:
        self._set_current_color(color_hex)

    def _on_pick_custom_color(self) -> None:
        initial = QColor(self._current_color())
        color = QColorDialog.getColor(initial, self, "Escolher cor")
        if color.isValid():
            self._set_current_color(color.name())

    def _set_current_color(self, color_hex: str) -> None:
        if self.tool_combo.currentData() == "redact":
            self._redact_color_hex = color_hex
            self.canvas.set_redact_color(color_hex)
        else:
            self._text_color_hex = color_hex
        self._refresh_color_selection()

    def _refresh_color_selection(self) -> None:
        current = self._current_color()
        for color_hex, swatch in self._swatch_buttons.items():
            selected = color_hex.lower() == current.lower()
            border = f"2px solid {COLOR_GREEN}" if selected else f"1px solid {COLOR_BORDER}"
            swatch.setStyleSheet(f"background-color: {color_hex}; border: {border}; border-radius: 6px;")

        is_preset = current.lower() in (c.lower() for c in _PRESET_COLORS)
        custom_border = f"1px solid {COLOR_BORDER}" if is_preset else f"2px solid {COLOR_GREEN}"
        custom_bg = "transparent" if is_preset else current
        self.custom_color_button.setStyleSheet(
            f"background-color: {custom_bg}; border: {custom_border}; border-radius: 6px; font-weight: 700;"
        )

        is_redact = self.tool_combo.currentData() == "redact"
        self.color_section_label.setText("Cor da tarja" if is_redact else "Cor do texto")

    def _on_redaction_requested(self, rect: tuple) -> None:
        try:
            self._session.add_redaction(self._current_page, rect, color_hex=self._redact_color_hex)
        except PdfEditError as exc:
            QMessageBox.warning(self, APP_TITLE, str(exc))
            return
        self._render_current_page()
        self._update_undo_state()
        self._update_save_button_state()

    def _on_text_position_requested(self, position: tuple) -> None:
        text, ok = QInputDialog.getText(self, "Adicionar texto", "Texto a inserir:")
        if not ok or not text.strip():
            return
        try:
            self._session.add_text(self._current_page, position, text.strip(), color_hex=self._text_color_hex)
        except PdfEditError as exc:
            QMessageBox.warning(self, APP_TITLE, str(exc))
            return
        self._render_current_page()
        self._update_undo_state()
        self._update_save_button_state()

    def _on_undo(self) -> None:
        if self._session.undo_last_on_page(self._current_page):
            self._render_current_page()
            self._update_undo_state()
            self._update_save_button_state()

    def _update_undo_state(self) -> None:
        self.btn_undo.setEnabled(self._session.has_marks_on_page(self._current_page))

    def _on_select_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Selecionar pasta de destino")
        if not directory:
            return
        self._output_dir = Path(directory)
        self.output_dir_label.setText(str(self._output_dir))
        self._update_save_button_state()

    def _update_save_button_state(self) -> None:
        self.save_button.setEnabled(
            self._source_path is not None
            and self._output_dir is not None
            and self._save_worker is None
        )

    def _on_save_clicked(self) -> None:
        if self._output_dir is None or self._source_path is None:
            return

        filename = sanitize_output_filename(self.output_name_edit.text())
        output_path = unique_path(self._output_dir / filename)

        self.progress_widget.setValue(0)
        self.progress_widget.setVisible(True)
        self.save_button.setEnabled(False)
        self.save_button.setText("Salvando...")
        # Evita edições concorrentes no documento enquanto ele é salvo em background.
        self.canvas.setEnabled(False)

        self._save_worker = SaveEditsWorker(self._session, output_path)
        self._save_worker.progress.connect(self._on_save_progress)
        self._save_worker.finished_ok.connect(self._on_save_success)
        self._save_worker.failed.connect(self._on_save_failed)
        self._save_worker.start()

    def _on_save_progress(self, index: int, total: int) -> None:
        if total > 0:
            self.progress_widget.setValue(int(index / total * 100))

    def _on_save_success(self, output_path: str) -> None:
        self._reset_save_ui()
        QMessageBox.information(self, APP_TITLE, f"PDF editado salvo com sucesso em:\n{output_path}")

    def _on_save_failed(self, message: str) -> None:
        self._reset_save_ui()
        QMessageBox.critical(self, APP_TITLE, f"Falha ao salvar o PDF editado:\n{message}")

    def _reset_save_ui(self) -> None:
        self._save_worker = None
        self.progress_widget.setVisible(False)
        self.save_button.setText("Salvar PDF editado")
        self.canvas.setEnabled(True)
        self._update_undo_state()
        self._update_save_button_state()
