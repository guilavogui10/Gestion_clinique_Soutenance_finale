# ============================================
# Script de démarrage complet
# Démarre Vault + MinIO
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Démarrage des services" -ForegroundColor Cyan
Write-Host "   Vault + MinIO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Démarrer Vault
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host "  ÉTAPE 1/2 : Démarrage de Vault" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host ""

$vaultScript = Join-Path $scriptDir "start_vault.ps1"
if (Test-Path $vaultScript) {
    & $vaultScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "✗ Erreur lors du démarrage de Vault" -ForegroundColor Red
        Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
} else {
    Write-Host "✗ Script start_vault.ps1 introuvable" -ForegroundColor Red
    Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host ""
Write-Host ""

# Démarrer MinIO
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host "  ÉTAPE 2/2 : Démarrage de MinIO" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host ""

$minioScript = Join-Path $scriptDir "start_minio.ps1"
if (Test-Path $minioScript) {
    & $minioScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "✗ Erreur lors du démarrage de MinIO" -ForegroundColor Red
        Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
} else {
    Write-Host "✗ Script start_minio.ps1 introuvable" -ForegroundColor Red
    Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host ""
Write-Host ""

# Résumé final
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  ✓ TOUS LES SERVICES SONT DÉMARRÉS" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "Services actifs:" -ForegroundColor White
Write-Host "  ✓ Vault    → http://127.0.0.1:8200" -ForegroundColor Gray
Write-Host "  ✓ MinIO    → http://127.0.0.1:9000 (API)" -ForegroundColor Gray
Write-Host "  ✓ Console  → http://127.0.0.1:9001 (Web)" -ForegroundColor Gray
Write-Host ""
Write-Host "Vous pouvez maintenant lancer l'application!" -ForegroundColor Green
Write-Host ""
Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
