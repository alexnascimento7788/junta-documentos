# DocJoin

Aplicativo desktop com interface gráfica moderna (PySide6) com duas ferramentas para PDF: **Unir PDFs** (mescla vários arquivos em um só, com reordenação visual, preservando 100% da qualidade original) e **Editar PDF** (anonimização real de campos e inserção de texto, página a página).

Desenvolvido para o **CEASAMINAS** (Centrais de Abastecimento de Minas Gerais) — a identidade visual (cores, marca) segue o padrão institucional do órgão.

## Funcionalidades

### Aba "Unir PDFs"

- Seleção de diretório contendo PDFs.
- Lista visual dos PDFs encontrados, cada item com ícone circular colorido, nome (truncado com reticências quando muito longo), número de páginas e posição.
- Reordenação por **drag & drop** (arrastar itens na lista) ou pelos botões **↑ / ↓**.
- Seleção de pasta e nome do arquivo de saída.
- Geração do PDF final em thread separada (interface não trava), com indicador de progresso circular animado (vermelho → dourado → verde).
- Mesclagem via `pypdf` (`PdfWriter.append`), que copia páginas sem recomprimir — qualidade idêntica ao original.

### Aba "Editar PDF"

- Seleção de um PDF de origem e navegação página a página (testado com documentos de até 50 páginas).
- **Anonimização real**: arraste sobre uma área da página para marcá-la para redação — ao salvar, o conteúdo original sob essa área é **removido de verdade** do PDF (não apenas coberto visualmente com um retângulo preto por cima, o que deixaria o texto original ainda extraível).
- **Inserção de texto**: clique num ponto da página e digite o texto a inserir.
- Botão para desfazer a última marcação feita na página atual.
- Seleção de pasta e nome do arquivo de saída (documento original nunca é sobrescrito).
- Salvamento em thread separada, com o mesmo indicador de progresso circular.

### Geral

- Tema visual claro institucional (verde/dourado CEASAMINAS, QSS customizado).
- Rodapé com identificação do órgão e versão do aplicativo.

## Estrutura do projeto

```
DocJoin/
├── main.py                        # ponto de entrada
├── requirements.txt
├── src/
│   ├── core/
│   │   ├── pdf_merger.py          # lógica de leitura/mesclagem de PDFs (sem dependência de GUI)
│   │   └── pdf_editor.py          # anonimização (redação real) e inserção de texto (PyMuPDF)
│   ├── gui/
│   │   ├── main_window.py         # janela principal (abas) e orquestração dos eventos da aba "Unir PDFs"
│   │   ├── edit_tab.py            # aba "Editar PDF": painel de ações + orquestração de edição
│   │   ├── pdf_edit_canvas.py     # canvas que exibe a página e captura marcações do mouse
│   │   ├── pdf_list_widget.py     # lista customizada com drag&drop e ícones circulares
│   │   ├── circular_progress.py   # indicador de progresso circular com cor por limiar
│   │   ├── brand_logo.py          # marca CEASAMINAS desenhada vetorialmente (QPainter)
│   │   └── styles.py              # paleta de cores e QSS (tema institucional)
│   └── utils/
│       └── file_utils.py          # sanitização de nome de arquivo, path único, tamanho legível
├── build_scripts/
│   ├── junta_documentos.spec      # spec do PyInstaller (compartilhado entre as 3 plataformas)
│   ├── build_windows.ps1
│   ├── build_macos.sh
│   └── build_linux.sh
└── assets/
    └── icon.ico                   # ícone gerado a partir da marca vetorial (ver "Ícones" abaixo)
```

### Como cada módulo funciona

- **`src/core/pdf_merger.py`** — camada pura de domínio, sem nenhuma dependência de Qt. Expõe:
  - `list_pdfs_in_directory`: lista `.pdf` de uma pasta.
  - `read_pdf_info`: lê metadados (nº de páginas) e detecta arquivos corrompidos.
  - `merge_pdfs`: concatena os PDFs na ordem recebida, com callback de progresso.
  - Pode ser testada e reutilizada independente da interface (ex.: em um script CLI).

- **`src/core/pdf_editor.py`** — camada pura de domínio (também sem Qt) para a aba "Editar PDF", usando `pymupdf` (PyMuPDF). Expõe a classe `PdfEditSession`:
  - `open`/`close`: abre/fecha o documento (rejeita PDFs protegidos por senha).
  - `render_page`: renderiza uma página como RGB puro, para exibição na GUI.
  - `add_redaction`: marca uma área para anonimização — usa `page.add_redact_annot`, que **não apaga nada ainda**, apenas fica pendente.
  - `add_text`: insere um texto como anotação `FreeText` (permite desfazer antes de salvar).
  - `undo_last_on_page` / `has_marks_on_page`: desfazer e verificar marcações pendentes por página.
  - `save`: aplica todas as redações pendentes via `page.apply_redactions()` — **é esse o passo que remove de verdade** o conteúdo original sob as áreas marcadas — e então salva o PDF final. Só depois disso a anonimização é irreversível.
  - PyMuPDF não carrega o documento inteiro em memória; `render_page` só materializa a página pedida, então o consumo de memória não cresce com o número de páginas.

- **`src/gui/pdf_edit_canvas.py`** — `QWidget` que desenha o `QPixmap` da página atual em tamanho real (1 px de tela = 1 px renderizado) e escuta eventos de mouse. No modo "anonimizar", arrastar o mouse desenha um retângulo de pré-visualização e emite `redaction_requested` com as coordenadas já convertidas de pixels de tela para pontos PDF (dividindo pelo zoom de renderização). No modo "adicionar texto", um clique emite `text_position_requested`.

- **`src/gui/edit_tab.py`** — painel de ações (selecionar PDF, navegar páginas, trocar ferramenta, desfazer, selecionar saída, salvar) conectado ao `PdfEditCanvas` e à `PdfEditSession`. O salvamento roda em `QThread` (`SaveEditsWorker`), com o canvas desabilitado durante o processo para evitar edições concorrentes no documento em memória.

- **`src/gui/pdf_list_widget.py`** — `QListWidget` especializado. Cada item usa um widget customizado (`PdfListItemWidget`) com avatar circular gerado via `QPainter`. O nome do arquivo é truncado com reticências (`QFontMetrics.elidedText`) conforme a largura disponível, para nunca colar na borda da lista — o nome completo continua acessível via tooltip. Como o Qt destrói o widget customizado de um item quando ele é movido/removido de um `QListWidget`, a reordenação (drag & drop ou botões) reconstrói a lista inteira preservando a nova ordem — abordagem simples e robusta.

- **`src/gui/circular_progress.py`** — anel de progresso desenhado à mão com `QPainter`. Cor muda conforme o valor: vermelho abaixo de 70%, dourado de 70–94%, verde a partir de 95% (limiares em `THRESHOLD_YELLOW`/`THRESHOLD_GREEN`).

- **`src/gui/brand_logo.py`** — recria vetorialmente o losango da marca CEASAMINAS (4 triângulos, 3 verdes + 1 dourado) usado como ícone da janela. É uma aproximação do logotipo oficial — ver seção "Ícones" para substituir pelos arquivos originais.

- **`src/gui/main_window.py`** — monta o layout (barra superior com logo + painel esquerdo de ações + painel direito com a lista + rodapé), conecta os eventos aos métodos `_on_*`, e roda a mesclagem em uma `QThread` (`MergeWorker`) para manter a UI responsiva. A animação de progresso é temporizada (não reflete a velocidade real do merge) — duração em segundos = `2 + 3 × nº de arquivos`.

- **`src/gui/styles.py`** — paleta de cores institucional (verde/dourado CEASAMINAS) e QSS aplicados via `setStyleSheet` na janela principal. Demais módulos importam as cores daqui para manter consistência.

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
Gera `dist\windows\DocJoin.exe`.

### macOS (.app)

```bash
chmod +x build_scripts/build_macos.sh
./build_scripts/build_macos.sh
```
Gera `dist/macos/DocJoin.app`. Para distribuir fora da sua máquina, assine com sua Apple Developer ID (comando sugerido no próprio script) e faça notarização via `notarytool`.

### Linux (binário + AppImage opcional)

```bash
chmod +x build_scripts/build_linux.sh
./build_scripts/build_linux.sh
```
Gera `dist/linux/DocJoin/DocJoin`. Se `appimagetool` estiver instalado e disponível no `PATH`, também gera `dist/linux/DocJoin-x86_64.AppImage`.

## Ícones

O `assets/icon.ico` atual foi **gerado a partir da recriação vetorial** da marca em `src/gui/brand_logo.py` (não é o arquivo oficial da CEASAMINAS, pois o projeto não tem os arquivos-fonte originais). Para usar a marca oficial em pixel perfeito:

1. Salve os arquivos oficiais em `assets/`:
   - `assets/icon.ico` (Windows — multi-resolução: 16/32/48/256px)
   - `assets/icon.icns` (macOS)
   - `assets/icon.png` (Linux/AppImage)
2. O `.spec` já detecta automaticamente o ícone correto por plataforma, se o arquivo existir — não precisa alterar código.
3. Opcionalmente, troque `ceasaminas_mark_pixmap()` em `src/gui/brand_logo.py` por um `QPixmap` carregado do arquivo oficial (`QPixmap("assets/logo_ceasaminas.png")`), para a marca exibida na barra superior do app também ficar pixel-perfeita.

## Licenciamento das dependências

A aba "Editar PDF" usa **PyMuPDF** (`pymupdf`), que é a única biblioteca do projeto com uma licença que exige atenção: é distribuída sob **AGPL v3** (ou licença comercial paga da Artifex, para quem não pode/quer cumprir a AGPL). Isso não afeta o uso interno do DocJoin dentro do CEASAMINAS, mas se o executável vier a ser **distribuído externamente** (fora da organização) sem disponibilizar o código-fonte do projeto, é preciso avaliar com o jurídico/TI se a AGPL é aceitável ou se vale adquirir uma licença comercial da Artifex (fabricante do PyMuPDF). As demais dependências (`PySide6`/Qt sob LGPL, `pypdf` sob BSD) não têm essa restrição.

## Sugestões de melhorias futuras

- Substituir a marca vetorial recriada pelos arquivos oficiais da CEASAMINAS (ver seção "Ícones").
- Miniaturas reais da primeira página de cada PDF (via `pypdf` + renderização com `pymupdf`/`pdf2image`), em vez dos ícones com iniciais.
- Suporte a arrastar arquivos PDF diretamente do explorador de arquivos do SO para dentro da lista (drag & drop externo), sem precisar selecionar um diretório inteiro.
- Opção de remover PDFs individuais da lista antes de gerar o resultado.
- Pré-visualização em miniatura ao passar o mouse sobre um item.
- Suporte a subpastas (busca recursiva opcional).
- Compressão/otimização opcional do PDF final (ex.: via `pikepdf`) para quem preferir arquivo menor em vez de qualidade máxima.
- Internacionalização (i18n) da interface.
- Testes automatizados para `src/core/pdf_merger.py`/`pdf_editor.py` (pytest) e pipeline de CI que já builda os 3 executáveis a cada release.
- Aba "Editar PDF": miniaturas de todas as páginas em uma coluna lateral (navegação visual, não só ◀/▶), opção de cor/tamanho de fonte ao inserir texto, redimensionar/mover uma marcação antes de salvar, atalhos de teclado para navegar entre páginas.
