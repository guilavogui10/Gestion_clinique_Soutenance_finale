@echo off
echo =========================================================
echo       Lancement Automatique des Sauvegardes
echo =========================================================

REM Se placer dans le bon dossier
set "PROJECT_DIR=C:\Users\Parfaite Mamy\Desktop\projet_final\Gestion_clinique_Soutenance_finale"
cd /d "%PROJECT_DIR%"

echo.
echo [1/2] Sauvegarde de la Base de Donnees MySQL...
python scripts\backup_incrementiel.py

echo.
echo [2/2] Sauvegarde des fichiers MinIO...
call scripts\backup_minio.bat

echo.
echo =========================================================
echo            Toutes les sauvegardes sont terminees !
echo =========================================================
