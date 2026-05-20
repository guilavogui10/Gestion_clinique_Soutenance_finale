# ============================================
# Script de demarrage automatique de MinIO
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Demarrage de MinIO Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$MINIO_ROOT_USER = "minioadmin"
$MINIO_ROOT_PASSWORD = "minioadmin"
$MINIO_DATA_DIR = "$PSScriptRoot\..\minio_data"
$MINIO_API_PORT = "9000"
$MINIO_CONSOLE_PORT = "9001"

# Fonction pour verifier si MinIO est installe
function Test-MinIOInstalled {
    try {
        $null = minio --version 2>$null
        return $true
    } catch {
        return $false
    }
}

# Fonction pour verifier si MinIO est actif
function Test-MinIOActive {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$MINIO_API_PORT/minio/health/live" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

# Verifier si MinIO est installe
Write-Host "[1/4] Verification de l'installation de MinIO..." -ForegroundColor Yellow
if (-not (Test-MinIOInstalled)) {
    Write-Host "X MinIO n'est pas installe sur ce systeme" -ForegroundColor Red
    Write-Host ""
    Write-Host "Veuillez installer MinIO depuis:" -ForegroundColor Yellow
    Write-Host "https://min.io/download" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}
Write-Host "OK MinIO est installe" -ForegroundColor Green

# Verifier si MinIO est deja actif
Write-Host ""
Write-Host "[2/4] Verification de l'etat de MinIO..." -ForegroundColor Yellow
if (Test-MinIOActive) {
    Write-Host "OK MinIO est deja actif" -ForegroundColor Green
} else {
    Write-Host "-> Demarrage du serveur MinIO..." -ForegroundColor Yellow
    
    # Creer le repertoire de donnees s'il n'existe pas
    if (-not (Test-Path $MINIO_DATA_DIR)) {
        New-Item -ItemType Directory -Path $MINIO_DATA_DIR -Force | Out-Null
        Write-Host "OK Repertoire de donnees cree: $MINIO_DATA_DIR" -ForegroundColor Green
    }
    
    # Definir les variables d'environnement
    $env:MINIO_ROOT_USER = $MINIO_ROOT_USER
    $env:MINIO_ROOT_PASSWORD = $MINIO_ROOT_PASSWORD
    
    # Demarrer MinIO en arriere-plan
    $minioJob = Start-Job -ScriptBlock {
        param($dataDir, $apiPort, $consolePort, $rootUser, $rootPassword)
        $env:MINIO_ROOT_USER = $rootUser
        $env:MINIO_ROOT_PASSWORD = $rootPassword
        minio server $dataDir --address ":$apiPort" --console-address ":$consolePort"
    } -ArgumentList $MINIO_DATA_DIR, $MINIO_API_PORT, $MINIO_CONSOLE_PORT, $MINIO_ROOT_USER, $MINIO_ROOT_PASSWORD
    
    # Attendre que MinIO soit pret (max 30 secondes)
    $maxAttempts = 60
    $attempt = 0
    $minioReady = $false
    
    while ($attempt -lt $maxAttempts -and -not $minioReady) {
        Start-Sleep -Milliseconds 500
        $attempt++
        
        if (Test-MinIOActive) {
            $minioReady = $true
        }
    }
    
    if ($minioReady) {
        Write-Host "OK Serveur MinIO demarre avec succes" -ForegroundColor Green
    } else {
        Write-Host "X Timeout lors du demarrage de MinIO" -ForegroundColor Red
        Stop-Job -Job $minioJob
        Remove-Job -Job $minioJob
        Write-Host ""
        Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}

# Verifier/Creer le bucket
Write-Host ""
Write-Host "[3/4] Configuration du bucket 'clinique-data'..." -ForegroundColor Yellow

# Installer le client MinIO (mc) si necessaire
$mcInstalled = $false
try {
    $null = mc --version 2>$null
    $mcInstalled = $true
} catch {
    Write-Host "! Client MinIO (mc) non installe - creation du bucket ignoree" -ForegroundColor Yellow
    Write-Host "  Vous pouvez creer le bucket manuellement via la console web:" -ForegroundColor Gray
    Write-Host "  http://127.0.0.1:$MINIO_CONSOLE_PORT" -ForegroundColor Cyan
}

if ($mcInstalled) {
    # Configurer l'alias MinIO
    $null = mc alias set local http://127.0.0.1:$MINIO_API_PORT $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD 2>$null
    
    # Verifier si le bucket existe
    $bucketExists = mc ls local/clinique-data 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK Bucket 'clinique-data' deja existant" -ForegroundColor Green
    } else {
        # Creer le bucket
        $result = mc mb local/clinique-data 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "OK Bucket 'clinique-data' cree avec succes" -ForegroundColor Green
        } else {
            Write-Host "! Erreur lors de la creation du bucket" -ForegroundColor Yellow
            Write-Host "  Creez-le manuellement via: http://127.0.0.1:$MINIO_CONSOLE_PORT" -ForegroundColor Gray
        }
    }
}

# Test de connexion
Write-Host ""
Write-Host "[4/4] Test de connexion..." -ForegroundColor Yellow
if (Test-MinIOActive) {
    Write-Host "OK MinIO est accessible" -ForegroundColor Green
} else {
    Write-Host "X MinIO ne repond pas" -ForegroundColor Red
}

# Resume
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   MinIO configure avec succes!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor White
Write-Host "  - API Endpoint: http://127.0.0.1:$MINIO_API_PORT" -ForegroundColor Gray
Write-Host "  - Console Web: http://127.0.0.1:$MINIO_CONSOLE_PORT" -ForegroundColor Gray
Write-Host "  - Username: $MINIO_ROOT_USER" -ForegroundColor Gray
Write-Host "  - Password: $MINIO_ROOT_PASSWORD" -ForegroundColor Gray
Write-Host "  - Bucket: clinique-data" -ForegroundColor Gray
Write-Host "  - Repertoire: $MINIO_DATA_DIR" -ForegroundColor Gray
Write-Host ""
Write-Host "Acces Console Web:" -ForegroundColor Yellow
Write-Host "  http://127.0.0.1:$MINIO_CONSOLE_PORT" -ForegroundColor Cyan
Write-Host ""
Write-Host "Vous pouvez maintenant lancer l'application!" -ForegroundColor Green
Write-Host ""
Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
