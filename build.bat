@echo off
setlocal

echo ===============================================
echo Gerador de Plano de Contas - build
echo ===============================================

cd /d "%~dp0"

if not exist ".venv" (
    echo Criando ambiente virtual...
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Falha ao ativar o ambiente virtual.
    exit /b 1
)

echo Instalando dependencias...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo Falha ao instalar dependencias.
    exit /b 1
)

echo Executando testes automatizados...
python -m pytest -q
if errorlevel 1 (
    echo Testes falharam. Build interrompido.
    exit /b 1
)

echo Gerando executavel com PyInstaller...
pyinstaller --noconfirm --clean --onefile --windowed ^
    --name GeradorPlanoContas ^
    app.py
if errorlevel 1 (
    echo Falha ao gerar o executavel.
    exit /b 1
)

echo Copiando config.json para a pasta dist (arquivo de configuracao editavel)...
copy /y "config.json" "dist\config.json" >nul

echo.
echo ===============================================
echo Build concluido com sucesso!
echo Executavel: dist\GeradorPlanoContas.exe
echo ===============================================

endlocal
