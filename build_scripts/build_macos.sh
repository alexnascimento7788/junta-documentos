#!/usr/bin/env bash
# Gera o pacote macOS (.app) do DocJoin.
# Deve ser executado EM UM MAC — o PyInstaller não faz cross-compile.
# Uso: ./build_scripts/build_macos.sh   (a partir da raiz do projeto)

set -euo pipefail

echo "Criando ambiente virtual (.venv)..."
python3 -m venv .venv
source .venv/bin/activate

echo "Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Empacotando com PyInstaller..."
pyinstaller build_scripts/junta_documentos.spec --distpath dist/macos --workpath build/macos --clean --noconfirm

echo "Concluído! Aplicativo em dist/macos/DocJoin.app"
echo "Para distribuir fora do seu Mac, assine e faça notarização com sua Apple Developer ID:"
echo "  codesign --deep --force --options runtime --sign \"Developer ID Application: SEU NOME\" dist/macos/DocJoin.app"
