@echo off
REM ============================================
REM Lanceur d'application - Clinique VisionCare
REM ============================================

echo.
echo ========================================
echo    Clinique VisionCare
echo    Demarrage de l'application...
echo ========================================
echo.

REM Aller dans le dossier du projet
cd /d "%~dp0"

REM Activer l'environnement virtuel
echo [1/2] Activation de l'environnement Python...
call venv\Scripts\activate.bat

REM Lancer l'application
echo [2/2] Lancement de l'application...
echo.
python main.py

REM Si l'application se ferme avec une erreur, garder la console ouverte
if errorlevel 1 (
    echo.
    echo ========================================
    echo    ERREUR lors du lancement
    echo ========================================
    echo.
    pause
)
