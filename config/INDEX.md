# 📁 Dossier Config - Index des fichiers

Ce dossier contient tous les fichiers de configuration et scripts de gestion pour l'application Clinique VisionCare.

## 📋 Liste des fichiers

### Scripts Vault

| Fichier | Description | Utilisation |
|---------|-------------|-------------|
| `start_vault.ps1` | Démarre et configure Vault | `.\config\start_vault.ps1` |
| `stop_vault.ps1` | Arrête proprement Vault | `.\config\stop_vault.ps1` |
| `README_VAULT.md` | Documentation complète de Vault | Lecture |

### Configuration

| Fichier | Description | Emplacement final |
|---------|-------------|-------------------|
| `.env.example` | Modèle de configuration | Copier à la racine en `.env` |

### Documentation

| Fichier | Description |
|---------|-------------|
| `README_VAULT.md` | Guide complet de Vault |
| Ce fichier | Index des fichiers de configuration |

---

## 🚀 Démarrage rapide

### Pour l'utilisateur final

**Vous n'avez rien à faire !** L'application démarre automatiquement Vault.

Lancez simplement :
```powershell
.\lancer_application.bat
```

### Pour l'administrateur

Si vous devez démarrer Vault manuellement :

1. **Démarrer Vault** :
   ```powershell
   cd config
   .\start_vault.ps1
   ```

2. **Lancer l'application** :
   ```powershell
   cd ..
   .\venv\Scripts\Activate.ps1
   python main.py
   ```

3. **Arrêter Vault** (à la fin) :
   ```powershell
   cd config
   .\stop_vault.ps1
   ```

---

## 📝 Configuration initiale

### Première installation

1. **Copier le fichier de configuration** :
   ```powershell
   copy config\.env.example .env
   ```

2. **Éditer le fichier `.env`** avec vos paramètres :
   - Identifiants email (pour l'envoi des codes OTP)
   - Identifiants base de données
   - Identifiants MinIO (si utilisé)

3. **Installer Vault** (si pas déjà fait) :
   - Télécharger : https://developer.hashicorp.com/vault/downloads
   - Extraire `vault.exe` dans `C:\HashiCorp\Vault\`
   - Ajouter au PATH système

4. **Lancer l'application** :
   ```powershell
   .\lancer_application.bat
   ```

---

## 🔒 Sécurité

### Fichiers sensibles

⚠️ **NE JAMAIS COMMITER** ces fichiers dans Git :
- `.env` (contient les mots de passe)
- `vault.log` (contient des informations sensibles)
- `vault.pid` (fichier temporaire)

### Bonnes pratiques

✅ **À faire** :
- Utiliser des mots de passe forts
- Changer le token Vault en production
- Utiliser des mots de passe d'application pour l'email
- Sauvegarder régulièrement la configuration

❌ **À ne pas faire** :
- Partager le fichier `.env`
- Utiliser le token par défaut en production
- Stocker des mots de passe en clair dans le code

---

## 📂 Structure du dossier

```
config/
├── start_vault.ps1          # Script de démarrage Vault
├── stop_vault.ps1           # Script d'arrêt Vault
├── README_VAULT.md          # Documentation Vault
├── .env.example             # Modèle de configuration
├── INDEX.md                 # Ce fichier
└── __init__.py              # Fichier Python (vide)
```

---

## 🆘 Aide

### Problèmes courants

**Vault ne démarre pas** :
- Vérifiez que Vault est installé : `vault version`
- Vérifiez que le port 8200 est libre
- Consultez `README_VAULT.md` pour plus de détails

**Erreur de configuration** :
- Vérifiez que le fichier `.env` existe à la racine
- Vérifiez que les paramètres sont corrects
- Consultez `.env.example` pour le format

**Erreur d'authentification** :
- Vérifiez les identifiants dans `.env`
- Vérifiez que Vault est actif
- Consultez les logs de l'application

### Documentation complète

- `README_VAULT.md` : Guide complet de Vault
- `GUIDE_UTILISATEUR.md` (racine) : Guide utilisateur
- `VAULT_README.md` (racine) : Documentation technique Vault

---

## 📞 Support

Pour toute question ou problème :
1. Consultez la documentation dans ce dossier
2. Consultez les logs de l'application
3. Contactez l'administrateur système

---

**Dernière mise à jour** : 2026-05-09
**Version** : 1.0
