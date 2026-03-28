@echo off
REM ============================================================
REM Script de lancement ZKTeco iClock Manager
REM ============================================================

echo Demarrage de ZKTeco iClock Manager...

REM Vérifier si l'environnement virtuel existe
if exist "venv\Scripts\python.exe" (
    call venv\Scripts\python.exe main.py
) else (
    REM Utiliser Python système
    python main.py
)

if errorlevel 1 (
    echo.
    echo Erreur lors du lancement de l'application.
    echo Verifiez que Python est installe et que les dependances sont installees.
    pause
)
