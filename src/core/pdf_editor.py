"""Motor de edição de PDF: anonimização (redação real) e inserção de texto.

Usa PyMuPDF (pymupdf), que permite redação de verdade — o conteúdo original sob a área
marcada é removido do PDF, não apenas coberto visualmente. Isso é essencial para
anonimização de documentos sensíveis (CPF, RG, etc.): um retângulo preto desenhado por
cima do texto, sem remover o texto original, não anonimiza nada — o conteúdo continua
extraível/selecionável por baixo.

Projetado para documentos grandes (30-50+ páginas): o documento fica aberto via stream
(PyMuPDF não carrega todas as páginas em memória de uma vez) e apenas a página atual é
renderizada por vez.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, Optional

import pymupdf

MarkKind = Literal["redact", "text"]


class PdfEditError(Exception):
    """Erro genérico ao abrir, editar ou salvar um PDF em edição."""


@dataclass
class _Mark:
    kind: MarkKind
    page_index: int
    annot: "pymupdf.Annot"
    # Preenchidos apenas para marcas "redact" — usados pela GUI para desenhar sua própria
    # pré-visualização colorida, já que o MuPDF sempre renderiza uma marcação de redação
    # pendente (ainda não aplicada) com um "X" vermelho padrão, ignorando a cor escolhida.
    rect_pt: Optional[tuple[float, float, float, float]] = None
    color_hex: Optional[str] = None


class PdfEditSession:
    """Mantém um documento PyMuPDF aberto e as marcações (redações/textos) pendentes."""

    def __init__(self) -> None:
        self._doc: Optional[pymupdf.Document] = None
        self._source_path: Optional[Path] = None
        self._marks: list[_Mark] = []

    # ------------------------------------------------------------ ciclo de vida

    def open(self, path: Path) -> int:
        """Abre um PDF para edição. Retorna o número de páginas."""
        self.close()
        try:
            self._doc = pymupdf.open(str(path))
        except Exception as exc:  # noqa: BLE001 - qualquer falha do MuPDF vira erro de domínio
            raise PdfEditError(f"Não foi possível abrir o PDF: {exc}") from exc
        if self._doc.is_encrypted:
            self._doc.close()
            self._doc = None
            raise PdfEditError("O PDF está protegido por senha e não pode ser editado.")
        self._source_path = path
        self._marks.clear()
        return self._doc.page_count

    def close(self) -> None:
        if self._doc is not None:
            self._doc.close()
            self._doc = None
        self._source_path = None
        self._marks.clear()

    @property
    def is_open(self) -> bool:
        return self._doc is not None

    @property
    def page_count(self) -> int:
        return self._doc.page_count if self._doc is not None else 0

    # ------------------------------------------------------------------ leitura

    def _require_doc(self) -> "pymupdf.Document":
        if self._doc is None:
            raise PdfEditError("Nenhum PDF aberto.")
        return self._doc

    def page_size(self, page_index: int) -> tuple[float, float]:
        """Dimensões da página em pontos PDF (1pt = 1/72 polegada)."""
        page = self._require_doc()[page_index]
        rect = page.rect
        return rect.width, rect.height

    def render_page(self, page_index: int, zoom: float) -> tuple[int, int, bytes]:
        """Renderiza a página em RGB puro (sem alfa). Retorna (largura_px, altura_px, bytes)."""
        page = self._require_doc()[page_index]
        matrix = pymupdf.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        return pixmap.width, pixmap.height, bytes(pixmap.samples)

    # ------------------------------------------------------------------ edição

    def add_redaction(
        self,
        page_index: int,
        rect_pt: tuple[float, float, float, float],
        color_hex: str = "#000000",
    ) -> None:
        """Marca uma área para anonimização (remoção real do conteúdo ao salvar).

        `color_hex` é a cor da tarja que substitui a área removida (preto, branco,
        cinza, etc.) — não afeta a remoção do conteúdo original em si, só a aparência.
        """
        doc = self._require_doc()
        page = doc[page_index]
        fill = _hex_to_rgb01(color_hex)
        annot = page.add_redact_annot(pymupdf.Rect(*rect_pt), fill=fill)
        self._marks.append(_Mark("redact", page_index, annot, rect_pt=rect_pt, color_hex=color_hex))

    def pending_redactions_on_page(self, page_index: int) -> list[tuple[tuple[float, float, float, float], str]]:
        """Retângulos e cores das redações marcadas mas ainda não salvas/aplicadas nesta página.

        Usado pela GUI para desenhar sua própria pré-visualização colorida por cima da
        página renderizada (ver comentário em `_Mark`).
        """
        return [
            (mark.rect_pt, mark.color_hex)
            for mark in self._marks
            if mark.kind == "redact" and mark.page_index == page_index
        ]

    def add_text(
        self,
        page_index: int,
        position_pt: tuple[float, float],
        text: str,
        font_size: float = 12.0,
        color_hex: str = "#000000",
    ) -> None:
        """Insere um texto na página, ancorado no ponto `position_pt` (canto superior esquerdo)."""
        if not text.strip():
            raise PdfEditError("O texto a inserir não pode estar vazio.")
        doc = self._require_doc()
        page = doc[page_index]
        color = _hex_to_rgb01(color_hex)
        x, y = position_pt
        # Caixa larga o bastante para a maioria das inserções; PyMuPDF quebra a linha
        # automaticamente se o texto não couber na largura informada.
        rect = pymupdf.Rect(x, y, min(x + 400, page.rect.width), y + font_size * 2.5)
        annot = page.add_freetext_annot(
            rect,
            text,
            fontsize=font_size,
            text_color=color,
            fill_color=None,
            border_color=None,
        )
        self._marks.append(_Mark("text", page_index, annot))

    def has_marks_on_page(self, page_index: int) -> bool:
        return any(mark.page_index == page_index for mark in self._marks)

    def undo_last_on_page(self, page_index: int) -> bool:
        """Remove a última marcação (redação ou texto) feita na página. Retorna False se não houver nenhuma."""
        doc = self._require_doc()
        for mark in reversed(self._marks):
            if mark.page_index == page_index:
                self._marks.remove(mark)
                doc[page_index].delete_annot(mark.annot)
                return True
        return False

    # -------------------------------------------------------------------- salvar

    def save(
        self,
        output_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Path:
        """Aplica as redações pendentes (removendo o conteúdo original) e salva o PDF final."""
        doc = self._require_doc()
        total = doc.page_count

        for i in range(total):
            page = doc[i]
            annots = page.annots()
            has_redaction = annots is not None and any(
                a.type[0] == pymupdf.PDF_ANNOT_REDACT for a in annots
            )
            if has_redaction:
                page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_PIXELS)
            if progress_callback:
                progress_callback(i + 1, total)

        # Redações aplicadas removem os próprios anotações de redação da página;
        # referências antigas deixam de ser válidas para desfazer.
        self._marks = [m for m in self._marks if m.kind != "redact"]

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            doc.save(str(output_path), garbage=4, deflate=True)
        except Exception as exc:  # noqa: BLE001
            raise PdfEditError(f"Falha ao salvar o PDF editado: {exc}") from exc
        return output_path


def _hex_to_rgb01(color_hex: str) -> tuple[float, float, float]:
    color_hex = color_hex.lstrip("#")
    return tuple(int(color_hex[i : i + 2], 16) / 255 for i in (0, 2, 4))
