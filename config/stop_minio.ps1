# ============================================
# Script d'arrêt de MinIO
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Arrêt de MinIO Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Arrêter le processus MinIO
Write-Host "[1/2] Arrêt du serveur MinIO..." -ForegroundColor Yellow
$minioProcess = Get-Process -Name "minio" -ErrorAction SilentlyContinue

if ($minioProcess) {
    Stop-Process -Name "minio" -Force
    Write-Host "✓ Serveur MinIO arrêté avec succès" -ForegroundColor Green
} else {
    Write-Host "⚠ Aucun processus MinIO en cours d'exécution" -ForegroundColor Yellow
}

# Nettoyer les fichiers temporaires
Write-Host ""
Write-Host "[2/2] Nettoyage des fichiers temporaires..." -ForegroundColor Yellow

$tempFiles = @(
    "minio.log",
    "minio.pid"
)

$cleaned = 0
foreach ($file in $tempFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "✓ Supprimé: $file" -ForegroundColor Green
        $cleaned++
    }
}

if ($cleaned -eq 0) {
    Write-Host "✓ Aucun fichier temporaire à nettoyer" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   MinIO arrêté avec succès!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
