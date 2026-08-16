"""Motor de mesclagem de PDFs, preservando a qualidade original dos documentos."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

from pypdf import PdfWriter
from pypdf.errors import PdfReadError


class PdfMergeError(Exception):
    """Erro genérico ao mesclar PDFs."""


@dataclass(frozen=True)
class PdfInfo:
    """Metadados básicos de um PDF listado para o usuário."""

    path: Path
    page_count: int

    @property
    def name(self) -> str:
        return self.path.name


def list_pdfs_in_directory(directory: Path) -> list[Path]:
    """Retorna todos os arquivos .pdf de um diretório (não recursivo), ordenados por nome."""
    if not directory.is_dir():
        raise PdfMergeError(f"Diretório inválido: {directory}")
    return sorted(directory.glob("*.pdf"), key=lambda p: p.name.lower())


def read_pdf_info(path: Path) -> Optional[PdfInfo]:
    """Lê metadados de um PDF. Retorna None se o arquivo estiver corrompido/ilegível."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return PdfInfo(path=path, page_count=len(reader.pages))
    except (PdfReadError, OSError, ValueError):
        return None


def merge_pdfs(
    ordered_paths: Iterable[Path],
    output_path: Path,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Path:
    """
    Mescla os PDFs na ordem fornecida em um único arquivo de saída.

    Usa PdfWriter.append, que copia as páginas sem recodificar conteúdo,
    preservando a qualidade original (texto, imagens e vetores intactos).

    :param ordered_paths: caminhos dos PDFs na ordem final desejada.
    :param output_path: caminho completo do arquivo PDF de saída.
    :param progress_callback: chamado como (indice_atual, total, nome_arquivo) a cada arquivo processado.
    :return: o caminho do arquivo gerado.
    """
    paths = list(ordered_paths)
    if not paths:
        raise PdfMergeError("Nenhum PDF selecionado para mesclagem.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    writer = PdfWriter()
    total = len(paths)
    try:
        for index, path in enumerate(paths, start=1):
            if not path.is_file():
                raise PdfMergeError(f"Arquivo não encontrado: {path}")
            try:
                writer.append(str(path))
            except (PdfReadError, OSError, ValueError) as exc:
                raise PdfMergeError(f"Falha ao ler '{path.name}': {exc}") from exc
            if progress_callback:
                progress_callback(index, total, path.name)

        with open(output_path, "wb") as fh:
            writer.write(fh)
    finally:
        writer.close()

    return output_path
