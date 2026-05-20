# ============================================
# Script d'arrêt complet
# Arrête Vault + MinIO
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Arrêt des services" -ForegroundColor Cyan
Write-Host "   Vault + MinIO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Arrêter MinIO
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host "  ÉTAPE 1/2 : Arrêt de MinIO" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host ""

$minioScript = Join-Path $scriptDir "stop_minio.ps1"
if (Test-Path $minioScript) {
    & $minioScript
} else {
    Write-Host "⚠ Script stop_minio.ps1 introuvable" -ForegroundColor Yellow
}

Write-Host ""
Write-Host ""

# Arrêter Vault
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host "  ÉTAPE 2/2 : Arrêt de Vault" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host ""

$vaultScript = Join-Path $scriptDir "stop_vault.ps1"
if (Test-Path $vaultScript) {
    & $vaultScript
} else {
    Write-Host "⚠ Script stop_vault.ps1 introuvable" -ForegroundColor Yellow
}

Write-Host ""
Write-Host ""

# Résumé final
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  ✓ TOUS LES SERVICES SONT ARRÊTÉS" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
