@echo off
TITLE KAIROS FINANCIAL OS - Launcher
COLOR 0B

echo ========================================================
echo       KAIROS FINANCIAL OS - SYSTEM INITIALIZATION
echo ========================================================
echo.

:: 1. VERIFICA PYTHON
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    COLOR 0C
    echo [ERRORE] Python non trovato!
    echo Per favore installa Python dal Microsoft Store o da python.org
    echo e assicurati di spuntare "Add Python to PATH" durante l'installazione.
    echo.
    PAUSE
    EXIT
)

:: 2. VERIFICA/CREAZIONE AMBIENTE VIRTUALE
IF NOT EXIST ".venv" (
    echo [INFO] Primo avvio rilevato. Creazione ambiente virtuale protetto...
    python -m venv .venv
    echo [OK] Ambiente creato.
)

:: 3. ATTIVAZIONE E AGGIORNAMENTO DIPENDENZE
echo [INFO] Caricamento moduli di sistema...
call .venv\Scripts\activate

echo [INFO] Verifica aggiornamenti librerie...
pip install -r requirements.txt -q --disable-pip-version-check

:: 4. AVVIO APPLICAZIONE
CLS
echo ========================================================
echo                 KAIROS IS ONLINE
echo ========================================================
echo.
echo    Status:     ACTIVE
echo    Address:    http://localhost:8501
echo.
echo [!] Non chiudere questa finestra mentre usi l'app.
echo.
echo Avvio del browser in corso...

streamlit run app.py

pause