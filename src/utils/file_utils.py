"""Utilitários de arquivo compartilhados pela interface."""

from __future__ import annotations

from pathlib import Path


def sanitize_output_filename(name: str) -> str:
    """Garante que o nome do arquivo de saída termine em .pdf e não esteja vazio."""
    name = name.strip()
    if not name:
        name = "documento_unificado"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name


def unique_path(path: Path) -> Path:
    """Se `path` já existir, retorna uma variante com sufixo numérico (evita sobrescrever sem avisar)."""
    if not path.exists():
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def human_readable_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
