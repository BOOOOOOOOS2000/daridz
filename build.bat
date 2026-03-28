@echo off
REM ============================================================
REM Script de compilation ZKTeco iClock Manager
REM Crée l'exécutable Windows (.exe)
REM ============================================================

echo ========================================
echo   ZKTeco iClock Manager - Build Script
echo ========================================
echo.

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou n'est pas dans le PATH
    pause
    exit /b 1
)

REM Créer l'environnement virtuel s'il n'existe pas
if not exist "venv" (
    echo Creation de l'environnement virtuel...
    python -m venv venv
)

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Installer les dépendances
echo.
echo Installation des dependances...
pip install --upgrade pip
pip install -r requirements.txt

REM Installer PyInstaller
pip install pyinstaller

REM Nettoyer les anciens builds
echo.
echo Nettoyage des anciens builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Compiler l'application
echo.
echo Compilation de l'application...
pyinstaller zkteco_manager.spec

REM Vérifier le résultat
if exist "dist\ZKTecoManager.exe" (
    echo.
    echo ========================================
    echo   SUCCES: Executable cree!
    echo   Emplacement: dist\ZKTecoManager.exe
    echo ========================================
    
    REM Copier les fichiers nécessaires
    if not exist "dist\data" mkdir dist\data
    if not exist "dist\exports" mkdir dist\exports
    
    echo.
    echo L'executable est pret dans le dossier 'dist'
) else (
    echo.
    echo ERREUR: La compilation a echoue
)

pause
