# 📁 Dossier de Configuration - Vault

Ce dossier contient tous les fichiers de configuration pour HashiCorp Vault.

## 📄 Fichiers

### `start_vault.ps1`
Script PowerShell pour démarrer et configurer Vault manuellement.

**Utilisation** :
```powershell
cd config
.\start_vault.ps1
```

**Ce qu'il fait** :
1. ✅ Vérifie si Vault est installé
2. ✅ Vérifie si Vault est déjà actif
3. ✅ Démarre Vault en mode développement
4. ✅ Active le moteur TOTP (codes OTP)
5. ✅ Active le moteur Transit (chiffrement)
6. ✅ Crée la clé de chiffrement `clinique-hmac`

### `stop_vault.ps1`
Script PowerShell pour arrêter proprement Vault.

**Utilisation** :
```powershell
cd config
.\stop_vault.ps1
```

**Ce qu'il fait** :
1. ✅ Arrête tous les processus Vault
2. ✅ Nettoie les fichiers temporaires

### `vault_config.json` (optionnel)
Fichier de configuration pour Vault en mode production.

---

## 🚀 Démarrage automatique

**Important** : Vous n'avez normalement **PAS besoin** d'exécuter ces scripts manuellement !

L'application démarre automatiquement Vault au lancement via `main.py`.

### Quand utiliser ces scripts ?

- **Dépannage** : Si Vault ne démarre pas automatiquement
- **Test manuel** : Pour tester Vault indépendamment de l'application
- **Mode production** : Pour configurer Vault en mode production

---

## 🔧 Configuration

### Variables d'environnement

Les paramètres de connexion sont dans le fichier `.env` à la racine :

```env
VAULT_URL=http://127.0.0.1:8200
VAULT_TOKEN=mon_token_secret
```

### Mode développement vs Production

**Mode développement** (actuel) :
- ✅ Démarrage rapide
- ✅ Pas de configuration complexe
- ⚠️ Données en mémoire (perdues au redémarrage)
- ⚠️ NE PAS utiliser en production

**Mode production** (à configurer) :
- ✅ Stockage persistant (fichier, base de données)
- ✅ Certificats SSL/TLS
- ✅ Authentification sécurisée
- ✅ Haute disponibilité

---

## 📝 Notes importantes

### Sécurité

⚠️ **ATTENTION** : Le token `mon_token_secret` est un token de développement.

En production, vous devez :
1. Générer un token sécurisé
2. Le stocker dans un coffre-fort sécurisé
3. Utiliser des certificats SSL/TLS
4. Configurer l'authentification appropriée

### Ports utilisés

- **8200** : Port par défaut de Vault
- Si ce port est occupé, modifiez `VAULT_URL` dans `.env`

### Logs

Les logs de Vault sont affichés dans :
- La console PowerShell (si démarrage manuel)
- Les logs de l'application Python (si démarrage automatique)

---

## 🐛 Dépannage

### Vault ne démarre pas

```powershell
# Vérifier si Vault est installé
vault version

# Vérifier si un processus Vault tourne
Get-Process -Name "vault"

# Arrêter tous les processus Vault
Stop-Process -Name "vault" -Force

# Relancer le script
.\start_vault.ps1
```

### Port 8200 déjà utilisé

```powershell
# Trouver quel processus utilise le port 8200
netstat -ano | findstr :8200

# Arrêter le processus (remplacer PID par le numéro trouvé)
Stop-Process -Id PID -Force
```

### Erreur "Vault n'est pas installé"

1. Téléchargez Vault : https://developer.hashicorp.com/vault/downloads
2. Extrayez `vault.exe` dans `C:\HashiCorp\Vault\`
3. Ajoutez `C:\HashiCorp\Vault\` au PATH système
4. Redémarrez PowerShell
5. Vérifiez : `vault version`

---

## 📞 Support

Pour toute question :
- Consultez `VAULT_README.md` à la racine du projet
- Consultez `GUIDE_UTILISATEUR.md` à la racine du projet
- Contactez l'administrateur système

---

## ✅ Checklist de configuration

Avant de démarrer l'application, vérifiez :

- [ ] Vault est installé (`vault version`)
- [ ] Vault est dans le PATH système
- [ ] Le fichier `.env` est configuré
- [ ] Le port 8200 est disponible
- [ ] Aucun autre processus Vault ne tourne

Si tout est OK, lancez simplement l'application avec `python main.py` !
