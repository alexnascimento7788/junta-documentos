#!/usr/bin/env bash
# Gera o binário Linux e, opcionalmente, um AppImage do Junta Documentos.
# Deve ser executado EM LINUX — o PyInstaller não faz cross-compile.
# Uso: ./build_scripts/build_linux.sh   (a partir da raiz do projeto)

set -euo pipefail

echo "Criando ambiente virtual (.venv)..."
python3 -m venv .venv
source .venv/bin/activate

echo "Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Empacotando com PyInstaller..."
pyinstaller build_scripts/junta_documentos.spec --distpath dist/linux --workpath build/linux --clean --noconfirm

echo "Binário gerado em dist/linux/JuntaDocumentos/JuntaDocumentos"

# --- Geração opcional de AppImage ---
# Requer appimagetool: https://github.com/AppImage/AppImageKit/releases
if command -v appimagetool >/dev/null 2>&1; then
    echo "Montando AppImage..."
    APPDIR="build/linux/JuntaDocumentos.AppDir"
    rm -rf "$APPDIR"
    mkdir -p "$APPDIR/usr/bin"
    cp -r dist/linux/JuntaDocumentos/* "$APPDIR/usr/bin/"

    cat > "$APPDIR/JuntaDocumentos.desktop" <<EOF
[Desktop Entry]
Name=Junta Documentos
Exec=JuntaDocumentos
Icon=icon
Type=Application
Categories=Office;Utility;
EOF

    if [ -f "assets/icon.png" ]; then
        cp assets/icon.png "$APPDIR/icon.png"
    fi

    ln -sf usr/bin/JuntaDocumentos "$APPDIR/AppRun"

    appimagetool "$APPDIR" "dist/linux/JuntaDocumentos-x86_64.AppImage"
    echo "AppImage gerado em dist/linux/JuntaDocumentos-x86_64.AppImage"
else
    echo "appimagetool não encontrado — pulei a geração do .AppImage."
    echo "Instale-o em https://github.com/AppImage/AppImageKit/releases e rode este script novamente para gerar o .AppImage."
fi
