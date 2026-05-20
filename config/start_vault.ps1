# ============================================
# Script de démarrage automatique de Vault
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Démarrage de HashiCorp Vault" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$VAULT_ADDR = "http://127.0.0.1:8200"
$VAULT_TOKEN = "mon_token_secret"

# Fonction pour vérifier si Vault est installé
function Test-VaultInstalled {
    try {
        $null = vault version 2>$null
        return $true
    } catch {
        return $false
    }
}

# Fonction pour vérifier si Vault est actif
function Test-VaultActive {
    try {
        $env:VAULT_ADDR = $VAULT_ADDR
        $env:VAULT_TOKEN = $VAULT_TOKEN
        $result = vault status 2>$null
        return $LASTEXITCODE -in @(0, 2)
    } catch {
        return $false
    }
}

# Vérifier si Vault est installé
Write-Host "[1/5] Vérification de l'installation de Vault..." -ForegroundColor Yellow
if (-not (Test-VaultInstalled)) {
    Write-Host "✗ Vault n'est pas installé sur ce système" -ForegroundColor Red
    Write-Host ""
    Write-Host "Veuillez installer Vault depuis:" -ForegroundColor Yellow
    Write-Host "https://developer.hashicorp.com/vault/downloads" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}
Write-Host "✓ Vault est installé" -ForegroundColor Green

# Vérifier si Vault est déjà actif
Write-Host ""
Write-Host "[2/5] Vérification de l'état de Vault..." -ForegroundColor Yellow
if (Test-VaultActive) {
    Write-Host "✓ Vault est déjà actif" -ForegroundColor Green
} else {
    Write-Host "→ Démarrage du serveur Vault..." -ForegroundColor Yellow
    
    # Démarrer Vault en arrière-plan
    $vaultJob = Start-Job -ScriptBlock {
        vault server -dev -dev-root-token-id="mon_token_secret"
    }
    
    # Attendre que Vault soit prêt (max 20 secondes)
    $maxAttempts = 40
    $attempt = 0
    $vaultReady = $false
    
    while ($attempt -lt $maxAttempts -and -not $vaultReady) {
        Start-Sleep -Milliseconds 500
        $attempt++
        
        try {
            $env:VAULT_ADDR = $VAULT_ADDR
            $env:VAULT_TOKEN = $VAULT_TOKEN
            $null = vault status 2>$null
            if ($LASTEXITCODE -in @(0, 2)) {
                $vaultReady = $true
            }
        } catch {
            # Continuer à attendre
        }
    }
    
    if ($vaultReady) {
        Write-Host "✓ Serveur Vault démarré avec succès" -ForegroundColor Green
    } else {
        Write-Host "✗ Timeout lors du démarrage de Vault" -ForegroundColor Red
        Stop-Job -Job $vaultJob
        Remove-Job -Job $vaultJob
        Write-Host ""
        Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}

# Configurer les variables d'environnement
$env:VAULT_ADDR = $VAULT_ADDR
$env:VAULT_TOKEN = $VAULT_TOKEN

# Activer le moteur TOTP
Write-Host ""
Write-Host "[3/5] Configuration du moteur TOTP..." -ForegroundColor Yellow
$result = vault secrets enable totp 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Moteur TOTP activé" -ForegroundColor Green
} elseif ($result -like "*path is already in use*") {
    Write-Host "✓ Moteur TOTP déjà activé" -ForegroundColor Green
} else {
    Write-Host "⚠ Erreur lors de l'activation du moteur TOTP" -ForegroundColor Yellow
    Write-Host $result -ForegroundColor Gray
}

# Activer le moteur Transit
Write-Host ""
Write-Host "[4/5] Configuration du moteur Transit..." -ForegroundColor Yellow
$result = vault secrets enable transit 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Moteur Transit activé" -ForegroundColor Green
} elseif ($result -like "*path is already in use*") {
    Write-Host "✓ Moteur Transit déjà activé" -ForegroundColor Green
} else {
    Write-Host "⚠ Erreur lors de l'activation du moteur Transit" -ForegroundColor Yellow
    Write-Host $result -ForegroundColor Gray
}

# Créer la clé de chiffrement
Write-Host ""
Write-Host "[5/5] Création de la clé de chiffrement..." -ForegroundColor Yellow
$result = vault write transit/keys/clinique-hmac type=aes256-gcm96 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Clé de chiffrement créée" -ForegroundColor Green
} elseif ($result -like "*already exists*") {
    Write-Host "✓ Clé de chiffrement déjà existante" -ForegroundColor Green
} else {
    Write-Host "⚠ Erreur lors de la création de la clé" -ForegroundColor Yellow
    Write-Host $result -ForegroundColor Gray
}

# Résumé
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Vault configuré avec succès!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor White
Write-Host "  • Adresse: $VAULT_ADDR" -ForegroundColor Gray
Write-Host "  • Token: $VAULT_TOKEN" -ForegroundColor Gray
Write-Host "  • Moteur TOTP: Activé" -ForegroundColor Gray
Write-Host "  • Moteur Transit: Activé" -ForegroundColor Gray
Write-Host "  • Clé de chiffrement: clinique-hmac" -ForegroundColor Gray
Write-Host ""
Write-Host "Vous pouvez maintenant lancer l'application!" -ForegroundColor Green
Write-Host ""
Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
