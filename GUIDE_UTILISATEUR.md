# 🚀 Guide de démarrage - Clinique VisionCare

## Pour l'utilisateur final (non-informaticien)

### ✅ Démarrage simple de l'application

1. **Double-cliquez sur** `lancer_application.bat` (si disponible)
   
   OU

2. **Ouvrez PowerShell** dans le dossier du projet et tapez :
   ```powershell
   .\venv\Scripts\Activate.ps1
   python main.py
   ```

3. **Attendez quelques secondes** ⏳
   - Un écran de chargement apparaît
   - L'application démarre automatiquement Vault en arrière-plan
   - Le formulaire de connexion s'affiche

4. **Connectez-vous** avec vos identifiants 🔐

C'est tout ! L'application gère tout automatiquement.

---

## 🔧 Pour l'administrateur système

### Prérequis

- **Vault installé** : HashiCorp Vault v2.0.0 ou supérieur
- **Vault dans le PATH** : La commande `vault` doit être accessible
- **Python 3.10+** avec l'environnement virtuel activé

### Que fait l'application au démarrage ?

1. ✅ Vérifie si Vault est installé
2. ✅ Vérifie si Vault est déjà actif
3. ✅ Si non actif, démarre Vault en mode développement
4. ✅ Configure automatiquement les moteurs TOTP et Transit
5. ✅ Crée la clé de chiffrement `clinique-hmac`
6. ✅ Affiche le formulaire de connexion

### Mode dégradé

Si Vault n'est pas installé ou ne peut pas démarrer :
- ⚠️ L'application affiche un avertissement
- ⚠️ L'authentification à deux facteurs sera désactivée
- ⚠️ La vérification d'intégrité des fichiers sera désactivée
- ✅ L'application reste fonctionnelle pour les autres fonctionnalités

### Arrêt de l'application

Quand vous fermez l'application :
- ✅ Vault s'arrête automatiquement
- ✅ Toutes les ressources sont libérées proprement

### Logs

Les logs sont affichés dans la console :
- `INFO` : Informations normales
- `WARNING` : Avertissements (Vault non disponible, etc.)
- `ERROR` : Erreurs critiques

---

## 🐛 Dépannage

### Problème : "Vault n'est pas installé"

**Solution** :
1. Téléchargez Vault : https://developer.hashicorp.com/vault/downloads
2. Extrayez `vault.exe` dans `C:\HashiCorp\Vault\`
3. Ajoutez `C:\HashiCorp\Vault\` au PATH système
4. Redémarrez PowerShell
5. Vérifiez : `vault version`

### Problème : "Vault non disponible - Mode dégradé"

**Causes possibles** :
- Vault n'est pas dans le PATH
- Un autre processus utilise le port 8200
- Permissions insuffisantes

**Solution** :
1. Vérifiez que Vault est installé : `vault version`
2. Vérifiez qu'aucun Vault ne tourne : `Get-Process -Name "vault"`
3. Si un Vault tourne, arrêtez-le : `Stop-Process -Name "vault" -Force`
4. Relancez l'application

### Problème : L'application est lente au démarrage

**Normal** : Le premier démarrage de Vault prend 5-10 secondes.

**Si trop lent** :
- Vérifiez votre antivirus (peut bloquer Vault)
- Vérifiez votre pare-feu (port 8200)

---

## 📞 Support

Pour toute question :
- Consultez `VAULT_README.md` pour plus de détails techniques
- Contactez l'administrateur système
- Consultez les logs dans la console

---

## ✨ Avantages de cette solution

✅ **Simplicité** : Un seul clic pour démarrer
✅ **Automatique** : Vault se configure tout seul
✅ **Transparent** : L'utilisateur ne voit rien
✅ **Robuste** : Mode dégradé si Vault indisponible
✅ **Propre** : Arrêt automatique à la fermeture
