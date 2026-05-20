# 🧪 Guide de test - Système de permissions

## 📋 Prérequis

Avant de tester, vous devez avoir :
- ✅ Vault installé et configuré
- ✅ L'application qui démarre correctement
- ✅ Au moins un compte DG (Directeur Général)

---

## 🚀 Étape 1 : Créer les comptes de test

### 1.1 Créer un compte RESPONSABLE

```powershell
cd c:\Users\Kaissa BILIVOGUI\Desktop\projet_final\projetSoutenance
.\venv\Scripts\Activate.ps1
python create_responsable_user.py
```

**Résultat attendu** :
- Personnel créé : Chirurgien Responsable
- Compte utilisateur créé avec login et mot de passe
- Email : chirurgien.responsable@clinique.com

**Notez le code utilisateur** (ex: U0002)

---

### 1.2 Créer un compte NON-RESPONSABLE

```powershell
python create_test_user.py
```

**Résultat attendu** :
- Personnel créé : Chirurgien Test
- Compte utilisateur créé avec login et mot de passe
- Email : chirurgien.test@clinique.com

**Notez le code utilisateur** (ex: U0003)

---

## 🧪 Étape 2 : Tests des permissions

### Test 1 : Compte NON-RESPONSABLE

#### 2.1 Connexion
1. Lancez l'application : `python main.py`
2. Connectez-vous avec le compte non-responsable
   - Login : U0003 (ou le code noté)
   - Mot de passe : test123
3. Entrez le code OTP reçu par email

#### 2.2 Test : Créer une chirurgie
1. Allez dans **Chirurgies**
2. Cliquez sur **Nouvelle chirurgie**

**Résultat attendu** :
```
❌ Message : "Seuls les responsables peuvent modifier les données."
❓ Question : "Voulez-vous demander l'autorisation au responsable ?"
```

3. Cliquez sur **Oui**

**Résultat attendu** :
```
📧 Message : "Un code d'autorisation a été envoyé à c***@c***.com"
🔐 Dialogue OTP s'affiche
📝 Message : "Demandez le code au responsable"
```

4. **Vérifiez l'email du responsable** (chirurgien.responsable@clinique.com)
5. Copiez le code OTP reçu
6. Saisissez le code dans le dialogue
7. Cliquez sur **Autoriser l'action**

**Résultat attendu** :
```
✅ Message : "Le responsable a autorisé cette action"
✅ Formulaire de création s'affiche
```

#### 2.3 Test : Modifier une chirurgie
1. Dans la liste des chirurgies, cliquez sur **Modifier**

**Résultat attendu** :
```
❌ Message : "Seuls les responsables peuvent modifier les données."
❓ Question : "Voulez-vous demander l'autorisation au responsable ?"
```

2. Suivez le même processus que pour la création

#### 2.4 Test : Voir les résultats
1. Cliquez sur **Voir résultats** (si disponible)

**Résultat attendu** :
```
❌ Message : "Seuls les responsables peuvent consulter les résultats détaillés."
❓ Question : "Voulez-vous demander l'autorisation au responsable ?"
```

2. Suivez le même processus

---

### Test 2 : Compte RESPONSABLE

#### 2.1 Connexion
1. Déconnectez-vous
2. Connectez-vous avec le compte responsable
   - Login : U0002 (ou le code noté)
   - Mot de passe : resp123
3. Entrez le code OTP reçu par email

#### 2.2 Test : Créer une chirurgie
1. Allez dans **Chirurgies**
2. Cliquez sur **Nouvelle chirurgie**

**Résultat attendu** :
```
✅ Formulaire de création s'affiche DIRECTEMENT
✅ Pas de demande d'autorisation
```

#### 2.3 Test : Modifier une chirurgie
1. Dans la liste, cliquez sur **Modifier**

**Résultat attendu** :
```
✅ Formulaire de modification s'affiche DIRECTEMENT
✅ Pas de demande d'autorisation
```

#### 2.4 Test : Voir les résultats
1. Cliquez sur **Voir résultats**

**Résultat attendu** :
```
🔐 Dialogue OTP s'affiche
📧 Message : "Un code de vérification a été envoyé à votre adresse"
📝 Vous devez confirmer avec OTP (envoyé à VOUS-MÊME)
```

2. Vérifiez votre email (chirurgien.responsable@clinique.com)
3. Copiez le code OTP
4. Saisissez-le dans le dialogue
5. Cliquez sur **Autoriser l'action**

**Résultat attendu** :
```
✅ Accès aux résultats autorisé
```

---

### Test 3 : Compte DIRECTEUR GÉNÉRAL

#### 2.1 Connexion
1. Déconnectez-vous
2. Connectez-vous avec votre compte DG

#### 2.2 Test : Toutes les actions
1. Allez dans **Chirurgies**
2. Testez toutes les actions

**Résultat attendu** :
```
✅ Créer → Accès DIRECT
✅ Modifier → Accès DIRECT
✅ Voir résultats → OTP envoyé à VOUS-MÊME (confirmation)
```

---

## 📊 Tableau récapitulatif des permissions

| Action | Non-responsable | Responsable | DG |
|--------|----------------|-------------|-----|
| **Créer** | ❌ OTP responsable | ✅ Direct | ✅ Direct |
| **Modifier** | ❌ OTP responsable | ✅ Direct | ✅ Direct |
| **Voir résultats** | ❌ OTP responsable | 🔐 OTP soi-même | 🔐 OTP soi-même |
| **Supprimer** | ❌ OTP DG | ❌ OTP DG | 🔐 OTP soi-même |

---

## 🐛 Dépannage

### Problème : "Vault est indisponible"
**Solution** : Démarrez Vault avant de lancer l'application
```powershell
.\config\start_vault.ps1
```

### Problème : "Aucun responsable trouvé"
**Solution** : Vérifiez qu'un personnel avec `est_responsable=1` existe pour la fonction "Chirurgien"

### Problème : "Email non reçu"
**Solution** : Vérifiez la configuration email dans le fichier `.env`

### Problème : "Code OTP invalide"
**Solution** : Le code expire après 30 secondes, demandez un nouveau code

---

## ✅ Checklist de test

- [ ] Compte non-responsable créé
- [ ] Compte responsable créé
- [ ] Test création (non-responsable) → OTP responsable
- [ ] Test modification (non-responsable) → OTP responsable
- [ ] Test résultats (non-responsable) → OTP responsable
- [ ] Test création (responsable) → Accès direct
- [ ] Test modification (responsable) → Accès direct
- [ ] Test résultats (responsable) → OTP soi-même
- [ ] Test toutes actions (DG) → Fonctionnel

---

## 📝 Notes

- Les codes OTP sont valides pendant **30 secondes**
- Un nouveau code peut être demandé avec le bouton **Renvoyer le code**
- Le timer affiche le temps restant
- Les emails sont envoyés via SMTP (configuré dans `.env`)

---

**Bon test ! 🚀**
