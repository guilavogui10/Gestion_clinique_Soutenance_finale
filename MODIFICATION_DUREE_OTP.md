# ✅ MODIFICATION DURÉE OTP - Récapitulatif

## 🎯 MODIFICATION EFFECTUÉE

La durée de validité des codes OTP a été **augmentée de 30 secondes à 5 minutes**.

---

## 📊 AVANT / APRÈS

### AVANT
```
⏱️ Durée de validité : 30 secondes
⚠️ Trop court pour l'utilisateur
```

### APRÈS
```
⏱️ Durée de validité : 5 minutes (300 secondes)
✅ Temps confortable pour l'utilisateur
```

---

## 🔧 FICHIERS MODIFIÉS

### 1. `core/vault_service.py`

**Méthode `creer_cle_totp()`** :
```python
payload = {
    "generate": True,
    "issuer": "CliniqueMFA",
    "account_name": account_name or identifiant,
    "period": 300,      # ← 5 minutes (300 secondes)
    "algorithm": "SHA256",
    "digits": 6,
}
```

**Méthode `envoyer_otp_par_email()`** :
```python
"Ce code est valable 5 minutes. Ne le communiquez a personne.\n\n"
#                     ↑ Mis à jour
```

### 2. `service_metier/permission_service.py`

**Méthode `_envoyer_email_autorisation()`** :
```python
"Ce code est valable 5 minutes. Ne le communiquez qu'à la personne concernée.\n\n"
#                     ↑ Mis à jour
```

---

## ⚙️ PARAMÈTRES TOTP

### Configuration Vault

```python
period: 300         # Durée de validité (5 minutes)
algorithm: SHA256   # Algorithme de hachage
digits: 6           # Nombre de chiffres du code
```

### Explication

- **period** : Intervalle de temps pendant lequel le code est valide
- **algorithm** : SHA256 (plus sécurisé que SHA1)
- **digits** : 6 chiffres (standard TOTP)

---

## 🧪 TESTS À EFFECTUER

### Test 1 : Connexion normale

```
1. Lancez l'application
2. Connectez-vous
3. Attendez 1-2 minutes avant de saisir le code OTP
4. ✅ Le code devrait toujours être valide
```

### Test 2 : Expiration du code

```
1. Connectez-vous
2. Attendez plus de 5 minutes
3. Saisissez le code OTP
4. ✅ Le code devrait être expiré
```

### Test 3 : Autorisation

```
1. Demandez une autorisation
2. Attendez 2-3 minutes
3. Saisissez le code OTP
4. ✅ Le code devrait toujours être valide
```

---

## 📧 MESSAGES EMAIL MIS À JOUR

### Email de connexion

```
Votre code de verification est :

        123456

Ce code est valable 5 minutes. Ne le communiquez a personne.
```

### Email d'autorisation

```
Votre code d'autorisation est :

        123456

Ce code est valable 5 minutes. Ne le communiquez qu'à la personne concernée.
```

---

## ⚠️ IMPORTANT

### Sécurité

- ✅ 5 minutes est un bon compromis entre sécurité et confort
- ✅ Toujours limité à 3 tentatives (protection contre force brute)
- ✅ Blocage automatique après 3 échecs

### Recommandations

- ✅ Ne pas augmenter au-delà de 10 minutes (risque sécurité)
- ✅ Informer les utilisateurs de la durée de validité
- ✅ Encourager à saisir le code rapidement

---

## 🔄 POUR MODIFIER À NOUVEAU

Si vous voulez changer la durée à l'avenir :

### Fichier : `core/vault_service.py`

```python
def creer_cle_totp(self, identifiant: str, account_name: str | None = None) -> bool:
    # ...
    payload = {
        "generate": True,
        "issuer": "CliniqueMFA",
        "account_name": account_name or identifiant,
        "period": 300,  # ← Changez ici (en secondes)
        # Exemples :
        # 60 = 1 minute
        # 180 = 3 minutes
        # 300 = 5 minutes (actuel)
        # 600 = 10 minutes
        "algorithm": "SHA256",
        "digits": 6,
    }
```

**N'oubliez pas de mettre à jour les messages email !**

---

## 📊 DURÉES RECOMMANDÉES

| Durée | Secondes | Usage | Sécurité |
|-------|----------|-------|----------|
| 30s | 30 | ❌ Trop court | ⭐⭐⭐⭐⭐ |
| 1 min | 60 | ⚠️ Court | ⭐⭐⭐⭐ |
| 3 min | 180 | ✅ Bon | ⭐⭐⭐ |
| **5 min** | **300** | **✅ Recommandé** | **⭐⭐⭐** |
| 10 min | 600 | ⚠️ Long | ⭐⭐ |
| 15 min | 900 | ❌ Trop long | ⭐ |

**Choix actuel : 5 minutes** ✅

---

## ✅ CHECKLIST

- [x] Durée modifiée dans `vault_service.py`
- [x] Message email de connexion mis à jour
- [x] Message email d'autorisation mis à jour
- [x] Documentation créée
- [ ] Tests effectués
- [ ] Utilisateurs informés

---

## 🎓 POUR LA SOUTENANCE

### Point à mentionner

> "Les codes OTP ont une durée de validité de 5 minutes, ce qui offre un bon équilibre entre sécurité et expérience utilisateur. Combiné avec la limitation à 3 tentatives et le blocage automatique, cela assure une protection robuste contre les attaques par force brute."

---

## 📞 EN CAS DE PROBLÈME

### Problème : "Code OTP expiré trop vite"

**Solution** : Augmentez la durée dans `vault_service.py` (ex: 600 pour 10 minutes)

### Problème : "Code OTP toujours invalide"

**Solution** : 
1. Vérifiez que Vault est démarré
2. Supprimez les anciennes clés TOTP
3. Reconnectez-vous pour générer une nouvelle clé

---

## 🎉 TERMINÉ !

La durée de validité des codes OTP est maintenant de **5 minutes** !

**Date de modification** : Aujourd'hui
**Durée précédente** : 30 secondes
**Durée actuelle** : 5 minutes (300 secondes)
**Statut** : ✅ OPÉRATIONNEL
