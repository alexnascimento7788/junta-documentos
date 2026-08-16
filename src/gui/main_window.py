"""Janela principal do Junta Documentos."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.pdf_merger import PdfMergeError, list_pdfs_in_directory, merge_pdfs, read_pdf_info
from src.gui.circular_progress import CircularProgressWidget
from src.gui.pdf_list_widget import PdfListWidget
from src.gui.styles import STYLE_SHEET
from src.utils.file_utils import sanitize_output_filename, unique_path

APP_TITLE = "Junta Documentos"

# Duração "de faz de conta" da animação de progresso: quanto mais arquivos, mais longa,
# para transmitir a sensação de trabalho proporcional ao tamanho da tarefa.
# 2 arquivos -> 8s, 3 arquivos -> 11s (passo de 3s por arquivo).
PROGRESS_BASE_SECONDS = 2
PROGRESS_SECONDS_PER_FILE = 3
PROGRESS_TICK_MS = 30


def estimated_duration_seconds(file_count: int) -> float:
    return PROGRESS_BASE_SECONDS + PROGRESS_SECONDS_PER_FILE * max(file_count, 1)


class MergeWorker(QThread):
    """Executa a mesclagem dos PDFs em uma thread separada para não travar a UI."""

    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, ordered_paths: list[Path], output_path: Path) -> None:
        super().__init__()
        self._ordered_paths = ordered_paths
        self._output_path = output_path

    def run(self) -> None:
        try:
            result = merge_pdfs(self._ordered_paths, self._output_path)
            self.finished_ok.emit(str(result))
        except PdfMergeError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - queremos reportar qualquer falha inesperada na UI
            self.failed.emit(f"Erro inesperado: {exc}")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(980, 640)
        self.setStyleSheet(STYLE_SHEET)

        self._source_dir: Path | None = None
        self._output_dir: Path | None = None
        self._worker: MergeWorker | None = None

        self._anim_timer: QTimer | None = None
        self._anim_start_time = 0.0
        self._anim_duration = 0.0
        self._anim_done = False
        self._merge_done = False
        self._merge_result: tuple[bool, str] | None = None  # (sucesso, mensagem_ou_caminho)

        self._build_ui()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_top_bar())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self._build_left_panel(), stretch=0)
        body_layout.addWidget(self._build_right_panel(), stretch=1)
        root_layout.addWidget(body, stretch=1)

    def _build_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(64)
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(0)

        title = QLabel(APP_TITLE)
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Una múltiplos PDFs em um único arquivo, na ordem que você escolher")
        subtitle.setObjectName("SubtitleLabel")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return bar

    def _build_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("LeftPanel")
        panel.setFixedWidth(320)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        layout.addWidget(self._section_label("Diretório de origem"))
        self.source_dir_label = QLabel("Nenhum diretório selecionado")
        self.source_dir_label.setObjectName("PathLabel")
        self.source_dir_label.setWordWrap(True)
        layout.addWidget(self.source_dir_label)

        btn_select_dir = QPushButton("📁  Selecionar diretório")
        btn_select_dir.clicked.connect(self._on_select_directory)
        layout.addWidget(btn_select_dir)

        layout.addSpacing(12)
        layout.addWidget(self._section_label("Reordenar"))
        reorder_row = QHBoxLayout()
        btn_up = QPushButton("↑")
        btn_up.setObjectName("IconButton")
        btn_up.clicked.connect(lambda: self.pdf_list.move_selected(-1))
        btn_down = QPushButton("↓")
        btn_down.setObjectName("IconButton")
        btn_down.clicked.connect(lambda: self.pdf_list.move_selected(1))
        reorder_row.addWidget(btn_up)
        reorder_row.addWidget(btn_down)
        reorder_row.addStretch(1)
        layout.addLayout(reorder_row)

        layout.addSpacing(12)
        layout.addWidget(self._section_label("Arquivo de saída"))

        self.output_name_edit = QLineEdit("documento_unificado.pdf")
        layout.addWidget(self.output_name_edit)

        self.output_dir_label = QLabel("Nenhuma pasta de destino selecionada")
        self.output_dir_label.setObjectName("PathLabel")
        self.output_dir_label.setWordWrap(True)
        layout.addWidget(self.output_dir_label)

        btn_select_output = QPushButton("💾  Selecionar pasta de destino")
        btn_select_output.clicked.connect(self._on_select_output_dir)
        layout.addWidget(btn_select_output)

        layout.addStretch(1)

        progress_row = QHBoxLayout()
        self.progress_widget = CircularProgressWidget()
        self.progress_widget.setVisible(False)
        progress_row.addStretch(1)
        progress_row.addWidget(self.progress_widget)
        progress_row.addStretch(1)
        layout.addLayout(progress_row)

        self.progress_status_label = QLabel("")
        self.progress_status_label.setAlignment(Qt.AlignCenter)
        self.progress_status_label.setStyleSheet("color: #9a9cb5; font-size: 11px;")
        self.progress_status_label.setVisible(False)
        layout.addWidget(self.progress_status_label)

        self.generate_button = QPushButton("Gerar PDF")
        self.generate_button.setObjectName("PrimaryButton")
        self.generate_button.setEnabled(False)
        self.generate_button.clicked.connect(self._on_generate_clicked)
        layout.addWidget(self.generate_button)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("RightPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.addWidget(self._section_label("PDFs encontrados (arraste para reordenar)"))
        header_row.addStretch(1)
        layout.addLayout(header_row)

        self.pdf_list = PdfListWidget()
        layout.addWidget(self.pdf_list, stretch=1)

        return panel

    @staticmethod
    def _section_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionLabel")
        return label

    # ------------------------------------------------------------- ações

    def _on_select_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Selecionar diretório com PDFs")
        if not directory:
            return
        self._source_dir = Path(directory)
        self.source_dir_label.setText(str(self._source_dir))
        self._load_pdfs()

    def _load_pdfs(self) -> None:
        assert self._source_dir is not None
        self.pdf_list.clear_pdfs()

        try:
            pdf_paths = list_pdfs_in_directory(self._source_dir)
        except PdfMergeError as exc:
            QMessageBox.warning(self, APP_TITLE, str(exc))
            return

        skipped = []
        for path in pdf_paths:
            info = read_pdf_info(path)
            if info is None:
                skipped.append(path.name)
                continue
            self.pdf_list.add_pdf(info)

        if skipped:
            QMessageBox.warning(
                self,
                APP_TITLE,
                "Os seguintes arquivos não puderam ser lidos e foram ignorados:\n\n"
                + "\n".join(skipped),
            )

        if self.pdf_list.count() == 0:
            QMessageBox.information(self, APP_TITLE, "Nenhum PDF válido encontrado nesse diretório.")

        self._update_generate_button_state()

    def _on_select_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Selecionar pasta de destino")
        if not directory:
            return
        self._output_dir = Path(directory)
        self.output_dir_label.setText(str(self._output_dir))
        self._update_generate_button_state()

    def _update_generate_button_state(self) -> None:
        self.generate_button.setEnabled(
            self.pdf_list.count() > 0 and self._output_dir is not None and self._worker is None
        )

    def _on_generate_clicked(self) -> None:
        if self._output_dir is None or self.pdf_list.count() == 0:
            return

        ordered_paths = self.pdf_list.ordered_paths()
        filename = sanitize_output_filename(self.output_name_edit.text())
        output_path = unique_path(self._output_dir / filename)

        self._anim_done = False
        self._merge_done = False
        self._merge_result = None

        self.progress_widget.setValue(0)
        self.progress_widget.setVisible(True)
        self.progress_status_label.setText("Preparando arquivos...")
        self.progress_status_label.setVisible(True)
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Gerando...")

        self._anim_duration = estimated_duration_seconds(len(ordered_paths))
        self._anim_start_time = time.monotonic()
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._on_animation_tick)
        self._anim_timer.start(PROGRESS_TICK_MS)

        self._worker = MergeWorker(ordered_paths, output_path)
        self._worker.finished_ok.connect(self._on_merge_success)
        self._worker.failed.connect(self._on_merge_failed)
        self._worker.start()

    def _on_animation_tick(self) -> None:
        elapsed = time.monotonic() - self._anim_start_time
        fraction = min(1.0, elapsed / self._anim_duration) if self._anim_duration > 0 else 1.0
        value = int(fraction * 100)
        self.progress_widget.setValue(value)

        if value < 70:
            self.progress_status_label.setText("Lendo páginas dos PDFs...")
        elif value < 95:
            self.progress_status_label.setText("Unindo documentos...")
        else:
            self.progress_status_label.setText("Finalizando...")

        if fraction >= 1.0:
            self._anim_timer.stop()
            self._anim_done = True
            self._maybe_finalize()

    def _on_merge_success(self, output_path: str) -> None:
        self._merge_done = True
        self._merge_result = (True, output_path)
        self._maybe_finalize()

    def _on_merge_failed(self, message: str) -> None:
        # Uma falha real interrompe a animação imediatamente — não faz sentido
        # continuar "fingindo" progresso quando a mesclagem já deu errado.
        self._merge_done = True
        self._merge_result = (False, message)
        if self._anim_timer is not None:
            self._anim_timer.stop()
        self._anim_done = True
        self._maybe_finalize()

    def _maybe_finalize(self) -> None:
        if not (self._anim_done and self._merge_done):
            return
        if self._merge_result is None:
            return

        success, payload = self._merge_result
        self._reset_progress_ui()

        if success:
            self.progress_widget.setValue(100)
            QMessageBox.information(self, APP_TITLE, f"PDF gerado com sucesso em:\n{payload}")
        else:
            QMessageBox.critical(self, APP_TITLE, f"Falha ao gerar o PDF:\n{payload}")

    def _reset_progress_ui(self) -> None:
        self._worker = None
        self._anim_timer = None
        self.progress_widget.setVisible(False)
        self.progress_status_label.setVisible(False)
        self.generate_button.setText("Gerar PDF")
        self._update_generate_button_state()
