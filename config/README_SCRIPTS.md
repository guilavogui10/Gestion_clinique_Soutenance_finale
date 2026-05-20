# 🚀 Scripts de Démarrage des Services

Ce dossier contient les scripts PowerShell pour démarrer et arrêter automatiquement les services nécessaires à l'application.

## 📋 Scripts disponibles

### 1. **start_all.ps1** ⭐ (RECOMMANDÉ)
Démarre automatiquement **Vault + MinIO** en une seule commande.

```powershell
.\start_all.ps1
```

### 2. **stop_all.ps1** ⭐ (RECOMMANDÉ)
Arrête automatiquement **Vault + MinIO** en une seule commande.

```powershell
.\stop_all.ps1
```

### 3. Scripts individuels

#### Vault
- `start_vault.ps1` : Démarre uniquement Vault
- `stop_vault.ps1` : Arrête uniquement Vault

#### MinIO
- `start_minio.ps1` : Démarre uniquement MinIO
- `stop_minio.ps1` : Arrête uniquement MinIO

## 🎯 Utilisation recommandée

### Démarrage de l'application

1. **Ouvrir PowerShell** dans le dossier `config/`
2. **Exécuter** :
   ```powershell
   .\start_all.ps1
   ```
3. **Attendre** que les deux services soient démarrés
4. **Lancer** l'application Python

### Arrêt de l'application

1. **Fermer** l'application Python
2. **Ouvrir PowerShell** dans le dossier `config/`
3. **Exécuter** :
   ```powershell
   .\stop_all.ps1
   ```

## ⚙️ Configuration

Les scripts lisent automatiquement la configuration depuis le fichier `.env` à la racine du projet :

### Vault
```env
VAULT_URL=http://127.0.0.1:8200
VAULT_TOKEN=mon_token_secret
```

### MinIO
```env
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=clinique-data
MINIO_SECURE=False
```

## 🔧 Prérequis

### 1. Installer Vault
Télécharger depuis : https://developer.hashicorp.com/vault/downloads

### 2. Installer MinIO
Télécharger depuis : https://min.io/download

Ou via PowerShell :
```powershell
Invoke-WebRequest -Uri 'https://dl.min.io/server/minio/release/windows-amd64/minio.exe' -OutFile 'C:\minio\minio.exe'
```

### 3. (Optionnel) Installer MinIO Client (mc)
Pour la création automatique du bucket :
```powershell
Invoke-WebRequest -Uri 'https://dl.min.io/client/mc/release/windows-amd64/mc.exe' -OutFile 'C:\minio\mc.exe'
```

## 📊 Vérification des services

### Vault
- **API** : http://127.0.0.1:8200
- **Vérifier** : `vault status`

### MinIO
- **API** : http://127.0.0.1:9000
- **Console Web** : http://127.0.0.1:9001
- **Identifiants** : minioadmin / minioadmin

## ❗ Résolution de problèmes

### Erreur "Vault n'est pas installé"
→ Installer Vault et ajouter au PATH système

### Erreur "MinIO n'est pas installé"
→ Installer MinIO et ajouter au PATH système

### Erreur "Port déjà utilisé"
→ Un service est déjà en cours d'exécution
→ Exécuter `stop_all.ps1` puis `start_all.ps1`

### Erreur "Bucket non créé"
→ Créer manuellement via la console web : http://127.0.0.1:9001
→ Nom du bucket : `clinique-data`

## 📝 Notes importantes

1. **Toujours démarrer les services AVANT l'application**
2. **Toujours arrêter les services APRÈS l'application**
3. Les données MinIO sont stockées dans `minio_data/`
4. Les scripts créent automatiquement les configurations nécessaires

## 🎓 Pour la soutenance

Démontrer le démarrage automatique :
1. Montrer `start_all.ps1` qui démarre tout
2. Expliquer la vérification automatique des services
3. Montrer la console MinIO (http://127.0.0.1:9001)
4. Montrer que Vault est configuré automatiquement
5. Lancer l'application qui se connecte aux deux services
