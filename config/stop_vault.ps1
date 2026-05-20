# ============================================
# Script d'arrêt de Vault
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Arrêt de HashiCorp Vault" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Arrêter le processus Vault
Write-Host "[1/2] Arrêt du serveur Vault..." -ForegroundColor Yellow
$vaultProcess = Get-Process -Name "vault" -ErrorAction SilentlyContinue

if ($vaultProcess) {
    Stop-Process -Name "vault" -Force
    Write-Host "✓ Serveur Vault arrêté avec succès" -ForegroundColor Green
} else {
    Write-Host "⚠ Aucun processus Vault en cours d'exécution" -ForegroundColor Yellow
}

# Nettoyer les fichiers temporaires
Write-Host ""
Write-Host "[2/2] Nettoyage des fichiers temporaires..." -ForegroundColor Yellow

$tempFiles = @(
    "vault.log",
    "vault.pid"
)

foreach ($file in $tempFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "✓ Supprimé: $file" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Vault arrêté avec succès!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
