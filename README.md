# Junta Documentos

Aplicativo desktop com interface gráfica moderna (PySide6) para unir vários arquivos PDF em um único documento, com reordenação visual por arrastar-e-soltar, preservando 100% da qualidade original dos arquivos.

## Funcionalidades

- Seleção de diretório contendo PDFs.
- Lista visual dos PDFs encontrados, cada item com ícone circular colorido, nome, número de páginas e posição.
- Reordenação por **drag & drop** (arrastar itens na lista) ou pelos botões **↑ / ↓**.
- Seleção de pasta e nome do arquivo de saída.
- Geração do PDF final em thread separada (interface não trava), com barra de progresso.
- Mesclagem via `pypdf` (`PdfWriter.append`), que copia páginas sem recomprimir — qualidade idêntica ao original.
- Tema visual dark moderno (QSS customizado).

## Estrutura do projeto

```
Junta Documentos/
├── main.py                        # ponto de entrada
├── requirements.txt
├── src/
│   ├── core/
│   │   └── pdf_merger.py          # lógica de leitura/mesclagem de PDFs (sem dependência de GUI)
│   ├── gui/
│   │   ├── main_window.py         # janela principal, layout e orquestração dos eventos
│   │   ├── pdf_list_widget.py     # lista customizada com drag&drop e ícones circulares
│   │   └── styles.py              # folha de estilos QSS (tema dark)
│   └── utils/
│       └── file_utils.py          # sanitização de nome de arquivo, path único, tamanho legível
├── build_scripts/
│   ├── junta_documentos.spec      # spec do PyInstaller (compartilhado entre as 3 plataformas)
│   ├── build_windows.ps1
│   ├── build_macos.sh
│   └── build_linux.sh
└── assets/                        # ícones (icon.ico / icon.icns / icon.png) — adicione os seus aqui
```

### Como cada módulo funciona

- **`src/core/pdf_merger.py`** — camada pura de domínio, sem nenhuma dependência de Qt. Expõe:
  - `list_pdfs_in_directory`: lista `.pdf` de uma pasta.
  - `read_pdf_info`: lê metadados (nº de páginas) e detecta arquivos corrompidos.
  - `merge_pdfs`: concatena os PDFs na ordem recebida, com callback de progresso.
  - Pode ser testada e reutilizada independente da interface (ex.: em um script CLI).

- **`src/gui/pdf_list_widget.py`** — `QListWidget` especializado. Cada item usa um widget customizado (`PdfListItemWidget`) com avatar circular gerado via `QPainter`. Como o Qt destrói o widget customizado de um item quando ele é movido/removido de um `QListWidget`, a reordenação (drag & drop ou botões) reconstrói a lista inteira preservando a nova ordem — abordagem simples e robusta.

- **`src/gui/main_window.py`** — monta o layout (barra superior + painel esquerdo de ações + painel direito com a lista), conecta os eventos aos métodos `_on_*`, e roda a mesclagem em uma `QThread` (`MergeWorker`) para manter a UI responsiva.

- **`src/gui/styles.py`** — paleta de cores e QSS aplicados via `setStyleSheet` na janela principal.

- **`src/utils/file_utils.py`** — pequenas funções auxiliares (nome de saída seguro, evitar sobrescrita silenciosa de arquivos existentes).

## Como rodar em modo desenvolvimento

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Como gerar os executáveis

⚠️ **Importante:** o PyInstaller empacota para a plataforma em que ele é executado — não existe cross-compile. Para gerar os três executáveis, rode cada script na respectiva plataforma (ou use CI com runners Windows/macOS/Linux, ex. GitHub Actions).

### Windows (.exe)

```powershell
.\build_scripts\build_windows.ps1
```
Gera `dist\windows\JuntaDocumentos\JuntaDocumentos.exe`.

### macOS (.app)

```bash
chmod +x build_scripts/build_macos.sh
./build_scripts/build_macos.sh
```
Gera `dist/macos/JuntaDocumentos.app`. Para distribuir fora da sua máquina, assine com sua Apple Developer ID (comando sugerido no próprio script) e faça notarização via `notarytool`.

### Linux (binário + AppImage opcional)

```bash
chmod +x build_scripts/build_linux.sh
./build_scripts/build_linux.sh
```
Gera `dist/linux/JuntaDocumentos/JuntaDocumentos`. Se `appimagetool` estiver instalado e disponível no `PATH`, também gera `dist/linux/JuntaDocumentos-x86_64.AppImage`.

## Ícones

Coloque seus próprios ícones em `assets/`:
- `assets/icon.ico` (Windows)
- `assets/icon.icns` (macOS)
- `assets/icon.png` (Linux/AppImage)

O `.spec` já detecta automaticamente o ícone correto por plataforma, se o arquivo existir.

## Sugestões de melhorias futuras

- Miniaturas reais da primeira página de cada PDF (via `pypdf` + renderização com `pymupdf`/`pdf2image`), em vez dos ícones com iniciais.
- Suporte a arrastar arquivos PDF diretamente do explorador de arquivos do SO para dentro da lista (drag & drop externo), sem precisar selecionar um diretório inteiro.
- Opção de remover PDFs individuais da lista antes de gerar o resultado.
- Pré-visualização em miniatura ao passar o mouse sobre um item.
- Suporte a subpastas (busca recursiva opcional).
- Compressão/otimização opcional do PDF final (ex.: via `pikepdf`) para quem preferir arquivo menor em vez de qualidade máxima.
- Internacionalização (i18n) da interface.
- Testes automatizados para `src/core/pdf_merger.py` (pytest) e pipeline de CI que já builda os 3 executáveis a cada release.
