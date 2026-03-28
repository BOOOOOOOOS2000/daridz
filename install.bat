@echo off
REM ============================================================
REM Script d'installation rapide ZKTeco iClock Manager
REM ============================================================

echo ========================================
echo   ZKTeco iClock Manager
echo   Installation rapide
echo ========================================
echo.

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERREUR: Python n'est pas installe!
    echo.
    echo Veuillez installer Python 3.8 ou superieur depuis:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Python detecte:
python --version
echo.

REM Créer l'environnement virtuel
if not exist "venv" (
    echo Creation de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 (
        echo ERREUR: Impossible de creer l'environnement virtuel
        pause
        exit /b 1
    )
)

REM Activer l'environnement
call venv\Scripts\activate.bat

REM Installer les dépendances
echo.
echo Installation des dependances...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERREUR: Impossible d'installer les dependances
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Installation terminee avec succes!
echo ========================================
echo.
echo Pour lancer l'application:
echo   - Double-cliquez sur run.bat
echo   - Ou utilisez: python main.py
echo.
echo Pour creer l'executable .exe:
echo   - Double-cliquez sur build.bat
echo.
pause
