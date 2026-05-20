# 📊 Guide Visuel - Système de Permissions v2.0

## 🎯 Architecture globale

```
┌─────────────────────────────────────────────────────────────────┐
│                        UTILISATEUR                              │
│  (Admin/DG, Responsable, Non-responsable)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COUCHE VUE (Views)                           │
│  ┌──────────────────┐  ┌──────────────────────────────────┐    │
│  │ otp_dialog.py    │  │ otp_autorisation_dialog.py       │    │
│  │ (Connexion MFA)  │  │ (Autorisations actions)          │    │
│  └──────────────────┘  └──────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              COUCHE CONTRÔLEUR (Controllers)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ controleur_permission.py                                 │  │
│  │ - verifier_permission()                                  │  │
│  │ - demander_autorisation()                                │  │
│  │ - valider_autorisation()                                 │  │
│  │ - refuser_autorisation()          ✨ NOUVEAU             │  │
│  │ - obtenir_demandes_en_attente()   ✨ NOUVEAU             │  │
│  │ - obtenir_historique_utilisateur() ✨ NOUVEAU            │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│           COUCHE SERVICE MÉTIER (Services)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ permission_service.py                                    │  │
│  │ - verifier_permission()                                  │  │
│  │ - demander_autorisation_otp()                            │  │
│  │ - valider_autorisation_otp()                             │  │
│  │ - refuser_autorisation()          ✨ NOUVEAU             │  │
│  │ - obtenir_demandes_en_attente()   ✨ NOUVEAU             │  │
│  │ - obtenir_historique_utilisateur() ✨ NOUVEAU            │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              COUCHE DONNÉES (Data/DAO)                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ dao_personnel.py │  │ dao_audit_       │  │ dao_otp_     │ │
│  │                  │  │ permission.py    │  │ tentatives.py│ │
│  │                  │  │ ✨ NOUVEAU       │  │ ✨ NOUVEAU   │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         COUCHE INFRASTRUCTURE (Core + DB)                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ vault_service.py │  │ MySQL            │  │ HashiCorp    │ │
│  │ - TOTP           │  │ - audit_         │  │ Vault        │ │
│  │ - Transit        │  │   permissions    │  │ - TOTP       │ │
│  │ - Email          │  │ - otp_tentatives │  │ - Transit    │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flux 1 : Connexion utilisateur (MFA)

```
┌──────────┐
│Utilisateur│
└─────┬────┘
      │ 1. Saisit login + mot de passe
      ▼
┌─────────────────┐
│  UserService    │
│ gerer_          │
│ authentification│
└────────┬────────┘
         │ 2. Vérifie bcrypt
         │ 3. Crée clé TOTP Vault
         │ 4. Génère code OTP
         ▼
┌─────────────────┐
│  VaultService   │
│ generer_code_otp│
└────────┬────────┘
         │ 5. Code OTP à 6 chiffres
         ▼
┌─────────────────┐
│  Email SMTP     │
│ Envoi du code   │
└────────┬────────┘
         │ 6. Email reçu
         ▼
┌──────────┐
│Utilisateur│ 7. Saisit code OTP
└─────┬────┘
      │
      ▼
┌─────────────────┐
│  UserService    │
│ verifier_otp_   │
│ connexion       │
└────────┬────────┘
         │ 8. Vérifie via Vault
         ▼
┌─────────────────┐
│  VaultService   │
│ verifier_code_  │
│ otp             │
└────────┬────────┘
         │ 9. Valide = True/False
         ▼
┌──────────┐
│Utilisateur│ ✅ Connecté ou ❌ Refusé
└──────────┘
```

---

## 🔄 Flux 2 : Action non autorisée (Non-responsable)

```
┌──────────────┐
│Non-responsable│
└──────┬───────┘
       │ 1. Clique "Modifier"
       ▼
┌──────────────────┐
│PermissionService │
│ verifier_        │
│ permission       │
└────────┬─────────┘
         │ 2. Retourne (False, "Seuls les responsables...")
         ▼
┌──────────────┐
│   Vue        │ 3. Affiche message
│   Dialog     │    "Demander autorisation ?"
└──────┬───────┘
       │ 4. Utilisateur clique "Oui"
       ▼
┌──────────────────┐
│PermissionService │
│ demander_        │
│ autorisation_otp │
└────────┬─────────┘
         │ 5. Trouve responsable du service
         │ 6. Crée clé TOTP unique
         │ 7. Génère code OTP
         ▼
┌──────────────────┐
│  VaultService    │
│ generer_code_otp │
└────────┬─────────┘
         │ 8. Code OTP à 6 chiffres
         ▼
┌──────────────────┐
│  Email SMTP      │
│ Envoi au         │
│ responsable      │
└────────┬─────────┘
         │ 9. Email reçu par responsable
         ▼
┌──────────────────┐
│  AuditDAO        │ 10. Enregistre demande
│ creer_demande    │     Statut: en_attente
└────────┬─────────┘
         │
         ▼
┌──────────────┐
│   Vue        │ 11. Affiche dialog OTP
│ OTPAutorisation│     "Demandez le code au responsable"
└──────┬───────┘
       │ 12. Responsable donne le code
       │ 13. Non-responsable saisit le code
       ▼
┌──────────────────┐
│PermissionService │
│ valider_         │
│ autorisation_otp │
└────────┬─────────┘
         │ 14. Vérifie via Vault
         ▼
┌──────────────────┐
│  VaultService    │
│ verifier_code_otp│
└────────┬─────────┘
         │ 15. Valide = True/False
         ▼
┌──────────────────┐
│  AuditDAO        │ 16. Met à jour statut
│ mettre_a_jour_   │     Statut: autorise
│ statut           │
└────────┬─────────┘
         │
         ▼
┌──────────────┐
│Non-responsable│ ✅ Action autorisée
└──────────────┘
```

---

## 🔄 Flux 3 : Limitation des tentatives OTP

```
┌──────────┐
│Utilisateur│
└─────┬────┘
      │ 1. Saisit code OTP (1ère tentative)
      ▼
┌──────────────────┐
│PermissionService │
│ valider_         │
│ autorisation_otp │
└────────┬─────────┘
         │ 2. Vérifie si bloqué
         ▼
┌──────────────────┐
│ OTPTentativesDAO │
│ est_bloque()     │
└────────┬─────────┘
         │ 3. Non bloqué
         ▼
┌──────────────────┐
│ OTPTentativesDAO │
│ incrementer_     │ 4. Incrémente tentative
│ tentative()      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  VaultService    │
│ verifier_code_otp│ 5. Vérifie code
└────────┬─────────┘
         │ 6. Code invalide
         ▼
┌──────────────────┐
│ OTPTentativesDAO │
│ incrementer_     │ 7. Incrémente échec
│ tentative(echec) │
└────────┬─────────┘
         │ 8. nb_echecs = 1
         ▼
┌──────────┐
│Utilisateur│ ❌ "Code invalide. 2 tentative(s) restante(s)."
└─────┬────┘
      │ 9. Saisit code OTP (2ème tentative)
      ▼
      ... (même processus)
      │ nb_echecs = 2
      ▼
┌──────────┐
│Utilisateur│ ❌ "Code invalide. 1 tentative(s) restante(s)."
└─────┬────┘
      │ 10. Saisit code OTP (3ème tentative)
      ▼
      ... (même processus)
      │ nb_echecs = 3
      ▼
┌──────────────────┐
│ OTPTentativesDAO │
│ _verifier_et_    │ 11. nb_echecs >= MAX_TENTATIVES
│ bloquer()        │     Bloque l'utilisateur
└────────┬─────────┘
         │ 12. est_bloque = TRUE
         │     date_blocage = NOW()
         ▼
┌──────────┐
│Utilisateur│ 🔒 "Trop de tentatives. Compte bloqué pour 15 minutes."
└──────────┘

... 15 minutes plus tard ...

┌──────────┐
│Utilisateur│ 13. Tente à nouveau
└─────┬────┘
      │
      ▼
┌──────────────────┐
│ OTPTentativesDAO │
│ est_bloque()     │ 14. Vérifie date_blocage
└────────┬─────────┘
         │ 15. NOW() >= date_blocage + 15 min
         │     Débloque automatiquement
         ▼
┌──────────┐
│Utilisateur│ ✅ Peut réessayer
└──────────┘
```

---

## 📊 Matrice des permissions

```
┌─────────────────┬──────────┬────────────┬──────────────┬──────────────┬─────────────┐
│     RÔLE        │ LECTURE  │ IMPRESSION │ CONSULTATION │ MODIFICATION │ SUPPRESSION │
├─────────────────┼──────────┼────────────┼──────────────┼──────────────┼─────────────┤
│ Non-responsable │ ✅ Direct│ ✅ Direct  │ ❌ OTP Resp. │ ❌ OTP Resp. │ ❌ OTP DG   │
├─────────────────┼──────────┼────────────┼──────────────┼──────────────┼─────────────┤
│ Responsable     │ ✅ Direct│ ✅ Direct  │ 🔐 OTP Soi   │ ✅ Direct    │ ❌ OTP DG   │
├─────────────────┼──────────┼────────────┼──────────────┼──────────────┼─────────────┤
│ DG/Admin        │ ✅ Direct│ ✅ Direct  │ 🔐 OTP Soi   │ ✅ Direct    │ 🔐 OTP Soi  │
└─────────────────┴──────────┴────────────┴──────────────┴──────────────┴─────────────┘

Légende:
✅ Direct      = Accès immédiat sans validation
🔐 OTP Soi     = Nécessite OTP envoyé à soi-même (confirmation)
❌ OTP Resp.   = Nécessite OTP du responsable du service
❌ OTP DG      = Nécessite OTP du Directeur Général
```

---

## 🗄️ Schéma de la base de données

```
┌─────────────────────────────────────────────────────────────────┐
│                    TABLE: audit_permissions                     │
├─────────────────────────────────────────────────────────────────┤
│ id                    INT AUTO_INCREMENT PRIMARY KEY            │
│ code_demandeur        VARCHAR(20) NOT NULL                      │
│ role_demandeur        VARCHAR(100) NOT NULL                     │
│ est_responsable       BOOLEAN DEFAULT FALSE                     │
│ action                VARCHAR(50) NOT NULL                      │
│ contexte              TEXT                                      │
│ code_autorisateur     VARCHAR(20)                               │
│ statut                VARCHAR(20) NOT NULL                      │
│ code_otp_envoye       VARCHAR(10)                               │
│ email_destinataire    VARCHAR(255)                              │
│ date_demande          DATETIME DEFAULT CURRENT_TIMESTAMP        │
│ date_reponse          DATETIME NULL                             │
│ ip_demandeur          VARCHAR(45)                               │
│ user_agent            TEXT                                      │
├─────────────────────────────────────────────────────────────────┤
│ INDEX idx_demandeur (code_demandeur)                            │
│ INDEX idx_autorisateur (code_autorisateur)                      │
│ INDEX idx_statut (statut)                                       │
│ INDEX idx_date_demande (date_demande)                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    TABLE: otp_tentatives                        │
├─────────────────────────────────────────────────────────────────┤
│ id                    INT AUTO_INCREMENT PRIMARY KEY            │
│ code_utilisateur      VARCHAR(20) NOT NULL                      │
│ identifiant_otp       VARCHAR(255) NOT NULL                     │
│ nb_tentatives         INT DEFAULT 0                             │
│ nb_echecs             INT DEFAULT 0                             │
│ est_bloque            BOOLEAN DEFAULT FALSE                     │
│ date_blocage          DATETIME NULL                             │
│ date_creation         DATETIME DEFAULT CURRENT_TIMESTAMP        │
│ date_derniere_tentative DATETIME NULL                           │
├─────────────────────────────────────────────────────────────────┤
│ UNIQUE KEY unique_otp (identifiant_otp)                         │
│ INDEX idx_utilisateur (code_utilisateur)                        │
│ INDEX idx_bloque (est_bloque)                                   │
└─────────────────────────────────────────────────────────────────┘

Relations:
audit_permissions.code_demandeur     → personnel.code
audit_permissions.code_autorisateur  → personnel.code
otp_tentatives.code_utilisateur      → utilisateur.code
```

---

## 📈 Cycle de vie d'une demande d'autorisation

```
┌──────────────┐
│  CRÉATION    │ demander_autorisation_otp()
│  Demande     │ → Statut: en_attente
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  EN_ATTENTE  │ Code OTP envoyé au responsable
│              │ Timer: 5 minutes
└──────┬───────┘
       │
       ├─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
┌──────────────┐                    ┌──────────────┐
│  AUTORISÉ    │                    │   REFUSÉ     │
│              │                    │              │
│ Code valide  │                    │ Refus        │
│ saisi        │                    │ explicite    │
└──────┬───────┘                    └──────┬───────┘
       │                                     │
       │                                     │
       ▼                                     ▼
┌──────────────┐                    ┌──────────────┐
│  NETTOYAGE   │                    │  NETTOYAGE   │
│              │                    │              │
│ - Supprime   │                    │ - Supprime   │
│   tentative  │                    │   tentative  │
│ - Supprime   │                    │ - Supprime   │
│   clé TOTP   │                    │   clé TOTP   │
└──────────────┘                    └──────────────┘

       OU (si timeout)
       │
       ▼
┌──────────────┐
│   EXPIRÉ     │
│              │
│ Timer écoulé │
│ (5 minutes)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  NETTOYAGE   │
│              │
│ - Supprime   │
│   tentative  │
│ - Supprime   │
│   clé TOTP   │
└──────────────┘
```

---

## 🔄 Cycle de vie des tentatives OTP

```
┌──────────────┐
│  CRÉATION    │ creer_ou_obtenir_tentative()
│  Tentative   │ → nb_tentatives = 0
│              │ → nb_echecs = 0
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  TENTATIVE 1 │ incrementer_tentative()
│              │ → nb_tentatives = 1
└──────┬───────┘
       │
       ├─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
┌──────────────┐                    ┌──────────────┐
│   SUCCÈS     │                    │   ÉCHEC 1    │
│              │                    │              │
│ Code valide  │                    │ nb_echecs=1  │
└──────┬───────┘                    └──────┬───────┘
       │                                     │
       ▼                                     ▼
┌──────────────┐                    ┌──────────────┐
│  SUPPRESSION │                    │  TENTATIVE 2 │
│              │                    │              │
│ supprimer_   │                    │ nb_tentatives│
│ tentative()  │                    │ = 2          │
└──────────────┘                    └──────┬───────┘
                                            │
                                            ├─────────────────┐
                                            │                 │
                                            ▼                 ▼
                                    ┌──────────────┐  ┌──────────────┐
                                    │   SUCCÈS     │  │   ÉCHEC 2    │
                                    │              │  │              │
                                    │ Code valide  │  │ nb_echecs=2  │
                                    └──────┬───────┘  └──────┬───────┘
                                            │                 │
                                            ▼                 ▼
                                    ┌──────────────┐  ┌──────────────┐
                                    │  SUPPRESSION │  │  TENTATIVE 3 │
                                    └──────────────┘  │              │
                                                      │ nb_tentatives│
                                                      │ = 3          │
                                                      └──────┬───────┘
                                                             │
                                                             ├─────────────────┐
                                                             │                 │
                                                             ▼                 ▼
                                                     ┌──────────────┐  ┌──────────────┐
                                                     │   SUCCÈS     │  │   ÉCHEC 3    │
                                                     │              │  │              │
                                                     │ Code valide  │  │ nb_echecs=3  │
                                                     └──────┬───────┘  └──────┬───────┘
                                                             │                 │
                                                             ▼                 ▼
                                                     ┌──────────────┐  ┌──────────────┐
                                                     │  SUPPRESSION │  │   BLOQUÉ     │
                                                     └──────────────┘  │              │
                                                                       │ est_bloque=  │
                                                                       │ TRUE         │
                                                                       │ Durée: 15min │
                                                                       └──────┬───────┘
                                                                              │
                                                                              │ Après 15 min
                                                                              ▼
                                                                       ┌──────────────┐
                                                                       │  DÉBLOQUÉ    │
                                                                       │              │
                                                                       │ debloquer()  │
                                                                       │ automatique  │
                                                                       └──────────────┘
```

---

## 📊 Timeline d'une demande d'autorisation

```
T=0s          T=5s          T=30s         T=60s         T=300s
│             │             │             │             │
│ Demande     │ Email       │ Code        │ Tentative   │ Expiration
│ créée       │ envoyé      │ expire      │ 2           │ (5 min)
│             │             │             │             │
▼             ▼             ▼             ▼             ▼
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ en_attente  │ en_attente  │ en_attente  │ en_attente  │ expire      │
│             │             │ (code       │             │             │
│             │             │  invalide)  │             │             │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘

Si validation réussie à T=45s:
│             │             │             │
│ Demande     │ Email       │ Code        │ Validation
│ créée       │ envoyé      │ saisi       │ réussie
│             │             │             │
▼             ▼             ▼             ▼
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ en_attente  │ en_attente  │ en_attente  │ autorise    │
│             │             │             │             │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

---

## 🎯 Résumé visuel des améliorations

```
AVANT (v1.0)                          APRÈS (v2.0)
═══════════════════════════════════════════════════════════════

┌──────────────────┐                  ┌──────────────────┐
│ Tentatives OTP   │                  │ Tentatives OTP   │
│ ∞ illimitées     │  ────────────>   │ ✅ 3 maximum     │
│ ❌ Pas de limite │                  │ ✅ Blocage 15min │
└──────────────────┘                  └──────────────────┘

┌──────────────────┐                  ┌──────────────────┐
│ Traçabilité      │                  │ Traçabilité      │
│ ❌ Aucune        │  ────────────>   │ ✅ Audit complet │
│ ❌ Pas d'historique│                │ ✅ Statistiques  │
└──────────────────┘                  └──────────────────┘

┌──────────────────┐                  ┌──────────────────┐
│ Refus            │                  │ Refus            │
│ ❌ Impossible    │  ────────────>   │ ✅ Explicite     │
│ ❌ Pas de raison │                  │ ✅ Raison        │
└──────────────────┘                  └──────────────────┘

┌──────────────────┐                  ┌──────────────────┐
│ Cache OTP        │                  │ Cache OTP        │
│ ❌ Redondant     │  ────────────>   │ ✅ Supprimé      │
│ ❌ Source bugs   │                  │ ✅ Vault seul    │
└──────────────────┘                  └──────────────────┘

┌──────────────────┐                  ┌──────────────────┐
│ HMAC             │                  │ HMAC             │
│ ❌ Simplifié     │  ────────────>   │ ✅ Robuste       │
│ ❌ Pas de compare│                  │ ✅ Comparaison   │
└──────────────────┘                  └──────────────────┘
```

---

**Fin du guide visuel** 📊

Pour plus d'informations, consultez :
- `README_PERMISSIONS_AMELIOREES.md`
- `GUIDE_MISE_A_JOUR_PERMISSIONS.md`
- `RECAPITULATIF_COMPLET_PERMISSIONS.md`
