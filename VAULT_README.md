# Guide d'utilisation de Vault pour l'application

## 📋 Prérequis

- HashiCorp Vault v2.0.0 installé
- PowerShell 5.0 ou supérieur
- Vault ajouté au PATH système

## 🚀 Démarrage rapide

### Option 1 : Utiliser le script automatique (RECOMMANDÉ)

1. **Démarrer Vault** :
   ```powershell
   .\config\start_vault.ps1
   ```
   
   Ce script va automatiquement :
   - Démarrer le serveur Vault en mode développement
   - Configurer les moteurs TOTP et Transit
   - Créer la clé de chiffrement
   - Vérifier que tout fonctionne

2. **Lancer l'application** :
   ```powershell
   .\venv\Scripts\Activate.ps1
   python main.py
   ```

3. **Arrêter Vault** (quand vous avez terminé) :
   ```powershell
   .\config\stop_vault.ps1
   ```

### Option 2 : Démarrage manuel

Si vous préférez démarrer Vault manuellement :

1. **Démarrer le serveur** :
   ```powershell
   vault server -dev -dev-root-token-id="mon_token_secret"
   ```
   ⚠️ Laissez cette fenêtre ouverte

2. **Dans un nouveau PowerShell, configurer les moteurs** :
   ```powershell
   $env:VAULT_ADDR="http://127.0.0.1:8200"
   $env:VAULT_TOKEN="mon_token_secret"
   
   vault secrets enable totp
   vault secrets enable transit
   vault write transit/keys/clinique-hmac type=aes256-gcm96
   ```

3. **Lancer l'application** :
   ```powershell
   .\venv\Scripts\Activate.ps1
   python main.py
   ```

## 🔧 Configuration

Les paramètres de connexion à Vault sont dans le fichier `.env` :

```env
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=mon_token_secret
```

## 📝 Notes importantes

### Mode développement
- ⚠️ Le mode développement (`-dev`) stocke tout en mémoire
- Si vous redémarrez Vault, vous devrez reconfigurer les moteurs
- Les données sont perdues à chaque redémarrage
- **NE PAS utiliser en production**

### Mode production
Pour une utilisation en production, il faudra :
1. Configurer Vault avec un stockage persistant (fichier, base de données)
2. Utiliser des certificats SSL/TLS
3. Configurer l'authentification appropriée
4. Mettre en place la haute disponibilité

## 🔐 Fonctionnalités Vault utilisées

### TOTP (Time-based One-Time Password)
- Génération de codes OTP à 6 chiffres
- Validité de 5 minutes
- Utilisé pour l'authentification à deux facteurs

### Transit (Chiffrement)
- Chiffrement AES256-GCM96
- Utilisé pour sécuriser les données sensibles
- Clé : `clinique-hmac`

## 🐛 Dépannage

### Vault ne démarre pas
```powershell
# Vérifier si Vault est installé
vault version

# Vérifier si un processus Vault tourne déjà
Get-Process -Name "vault"

# Arrêter tous les processus Vault
Stop-Process -Name "vault" -Force
```

### Erreur "Vault est indisponible"
1. Vérifiez que Vault est démarré
2. Vérifiez que les moteurs sont activés :
   ```powershell
   vault secrets list
   ```
3. Vérifiez la connexion :
   ```powershell
   vault status
   ```

### Erreur "impossible d'initialiser la clé TOTP"
1. Vérifiez que le moteur TOTP est activé
2. Vérifiez les logs de Vault
3. Essayez de créer une clé manuellement :
   ```powershell
   vault write totp/keys/test-user generate=true issuer="CliniqueMFA" account_name="test@example.com"
   ```

## 📞 Support

Pour toute question ou problème, consultez :
- Documentation Vault : https://developer.hashicorp.com/vault/docs
- Logs de l'application : Affichés dans la console Python
- Logs Vault : Affichés dans la fenêtre PowerShell du serveur

## ✅ Checklist avant de démarrer l'application

- [ ] Vault est installé et dans le PATH
- [ ] Le fichier `.env` est configuré
- [ ] Le serveur Vault est démarré (via `start_vault.ps1` ou manuellement)
- [ ] Les moteurs TOTP et Transit sont activés
- [ ] La clé `clinique-hmac` est créée
- [ ] L'environnement virtuel Python est activé

Une fois tout vérifié, vous pouvez lancer l'application avec `python main.py` !
