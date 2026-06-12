@echo off
echo =========================================================
echo       Sauvegarde Incrementielle des fichiers MinIO
echo =========================================================

REM --- Configuration des chemins ---
REM %~dp0 correspond au dossier où se trouve le script actuel (scripts/)
REM On recule d'un dossier (..) pour arriver à la racine du projet
set "SOURCE_DIR=%~dp0..\minio_data"
set "BACKUP_DIR=%~dp0..\sauvegardes_incrementielles\minio_backup"

echo Source : %SOURCE_DIR%
echo Destination : %BACKUP_DIR%
echo.

REM --- Exécution de la copie incrémentielle avec ROBOCOPY ---
REM Paramètres utilisés :
REM /E : Copie les sous-répertoires, y compris ceux qui sont vides.
REM /XO : Exclut les fichiers plus anciens (sauvegarde incrémentielle).
REM /Z : Copie les fichiers en mode redémarrable (utile si la copie est interrompue).
REM /R:3 : Nombre de tentatives en cas d'échec de lecture.
REM /W:1 : Temps d'attente entre les tentatives (en secondes).
REM /NP : Pas de progression pour éviter d'inonder les logs.
REM /LOG+: permet d'ajouter les logs à un fichier si besoin (ici on affiche juste).

robocopy "%SOURCE_DIR%" "%BACKUP_DIR%" /E /XO /Z /R:3 /W:1 /NP

REM Robocopy retourne des codes d'erreur spécifiques :
REM 0 = Aucun changement (fichiers déjà à jour)
REM 1 = Fichiers copiés avec succès
REM 2 = Fichiers supplémentaires dans la destination
REM 3 = Fichiers copiés ET fichiers supplémentaires présents
REM Si le code est inférieur à 8, c'est généralement un succès.
if %ERRORLEVEL% LSS 8 (
    echo ✅ Sauvegarde des fichiers MinIO terminee avec succes !
) else (
    echo ❌ Une erreur est survenue lors de la sauvegarde (Code d'erreur: %ERRORLEVEL%).
)
