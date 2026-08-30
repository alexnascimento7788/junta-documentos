# Gera o executável Windows (.exe) do DocJoin.
# Execute a partir da raiz do projeto: .\build_scripts\build_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "Criando ambiente virtual (.venv)..." -ForegroundColor Cyan
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

Write-Host "Instalando dependências..." -ForegroundColor Cyan
pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Empacotando com PyInstaller..." -ForegroundColor Cyan
pyinstaller build_scripts\junta_documentos.spec --distpath dist\windows --workpath build\windows --clean --noconfirm

Write-Host "Concluído! Executável em dist\windows\DocJoin.exe" -ForegroundColor Green
