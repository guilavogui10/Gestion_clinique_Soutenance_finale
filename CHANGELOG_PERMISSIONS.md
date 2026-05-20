# 📝 CHANGELOG - Système de Permissions

## Version 2.0.0 - Améliorations majeures (2024)

### 🎉 Nouvelles fonctionnalités

#### 1. Système d'audit complet
- ✅ Nouvelle table `audit_permissions` pour tracer toutes les demandes
- ✅ Enregistrement automatique de chaque demande d'autorisation
- ✅ Statuts : `en_attente`, `autorise`, `refuse`, `expire`
- ✅ Horodatage complet (date demande + date réponse)
- ✅ Traçabilité de l'autorisateur et du demandeur
- ✅ Méthode `obtenir_historique_utilisateur()` pour consulter l'historique
- ✅ Méthode `obtenir_statistiques()` pour les rapports

**Fichiers ajoutés** :
- `data/dao_audit_permission.py`

**Fichiers modifiés** :
- `service_metier/permission_service.py`
- `controllers/controleur_permission.py`

---

#### 2. Limitation des tentatives OTP
- ✅ Nouvelle table `otp_tentatives` pour gérer les tentatives
- ✅ Maximum 3 tentatives par code OTP
- ✅ Blocage automatique pendant 15 minutes après 3 échecs
- ✅ Compteur de tentatives restantes affiché à l'utilisateur
- ✅ Déblocage automatique après expiration du délai
- ✅ Méthode `est_bloque()` pour vérifier le statut
- ✅ Méthode `debloquer()` pour déblocage manuel

**Fichiers ajoutés** :
- `data/dao_otp_tentatives.py`

**Fichiers modifiés** :
- `service_metier/permission_service.py`

**Configuration** :
```python
MAX_TENTATIVES = 3              # Modifiable dans dao_otp_tentatives.py
DUREE_BLOCAGE_MINUTES = 15      # Modifiable dans dao_otp_tentatives.py
```

---

#### 3. Gestion des refus d'autorisation
- ✅ Nouvelle méthode `refuser_autorisation()` dans PermissionService
- ✅ Le responsable peut refuser explicitement une demande
- ✅ Raison du refus enregistrée dans l'audit
- ✅ Statut `refuse` dans la base de données
- ✅ Nettoyage automatique des clés TOTP et tentatives

**Fichiers modifiés** :
- `service_metier/permission_service.py`
- `controllers/controleur_permission.py`

**Utilisation** :
```python
permission_service.refuser_autorisation(
    code_utilisateur="U0001",
    action="modification",
    contexte="Chirurgie #CH001",
    code_autorisateur="U0002",
    raison="Action non justifiée"
)
```

---

#### 4. Consultation des demandes en attente
- ✅ Nouvelle méthode `obtenir_demandes_en_attente()` dans PermissionService
- ✅ Le responsable peut voir toutes ses demandes en attente
- ✅ Affichage du temps écoulé depuis la demande
- ✅ Filtrage par autorisateur

**Fichiers modifiés** :
- `service_metier/permission_service.py`
- `controllers/controleur_permission.py`

**Utilisation** :
```python
demandes = permission_service.obtenir_demandes_en_attente("U0002")
# Retourne la liste des demandes en attente pour U0002
```

---

### 🔧 Améliorations

#### 1. Vérification HMAC robuste
- ✅ Amélioration de la méthode `verifier_hmac()` dans VaultService
- ✅ Comparaison réelle des hash (avant/après)
- ✅ Déchiffrement des deux côtés pour vérification
- ✅ Logging détaillé des opérations
- ✅ Détection fiable des altérations de fichiers

**Fichiers modifiés** :
- `core/vault_service.py`

**Avant** :
```python
# Vérifiait juste si le déchiffrement réussissait
return resp is not None
```

**Après** :
```python
# Compare les données déchiffrées
donnees_attendues = resp["data"]["plaintext"]
donnees_actuelles = resp_actuel["data"]["plaintext"]
return donnees_attendues == donnees_actuelles
```

---

#### 2. Suppression du cache redondant
- ✅ Suppression de `_otp_cache` dans PermissionService
- ✅ Vault gère maintenant tout
- ✅ Code plus simple et maintenable
- ✅ Moins de risques d'incohérence

**Fichiers modifiés** :
- `service_metier/permission_service.py`

**Avant** :
```python
self._otp_cache: Dict[str, str] = {}
# ...
self._otp_cache[identifiant_otp] = code_otp
```

**Après** :
```python
# Supprimé - Vault gère tout
```

---

#### 3. Amélioration de la méthode demander_autorisation_otp
- ✅ Ajout du paramètre `est_responsable`
- ✅ Gestion différenciée selon le rôle
- ✅ Pour consultation : responsable/DG reçoit l'OTP à lui-même
- ✅ Pour suppression : toujours envoyé au DG
- ✅ Pour autres actions : envoyé au responsable du service

**Fichiers modifiés** :
- `service_metier/permission_service.py`
- `controllers/controleur_permission.py`

**Nouvelle signature** :
```python
def demander_autorisation_otp(
    self,
    code_utilisateur: str,
    role: str,
    action: str,
    contexte: str = "",
    est_responsable: bool = False  # NOUVEAU
) -> Tuple[bool, str, Optional[str]]
```

---

### 🧹 Maintenance

#### 1. Nettoyage automatique des audits
- ✅ Méthode `nettoyer_anciennes_demandes()` dans AuditPermissionDAO
- ✅ Suppression des demandes de plus de X jours (configurable)
- ✅ Recommandation : tâche planifiée quotidienne

**Utilisation** :
```python
audit_dao.nettoyer_anciennes_demandes(jours=90)
```

---

#### 2. Nettoyage automatique des tentatives
- ✅ Méthode `nettoyer_anciennes_tentatives()` dans OTPTentativesDAO
- ✅ Suppression des tentatives de plus de X heures (configurable)
- ✅ Recommandation : tâche planifiée quotidienne

**Utilisation** :
```python
tentatives_dao.nettoyer_anciennes_tentatives(heures=24)
```

---

### 📊 Statistiques et reporting

#### 1. Statistiques globales
- ✅ Méthode `obtenir_statistiques()` dans AuditPermissionDAO
- ✅ Total des demandes par statut
- ✅ Temps moyen de réponse
- ✅ Filtrage par période

**Utilisation** :
```python
stats = audit_dao.obtenir_statistiques(date_debut, date_fin)
# Retourne : total_demandes, autorisees, refusees, expirees, en_attente, temps_moyen_reponse_sec
```

---

### 📁 Nouveaux fichiers

#### Scripts
- ✅ `scripts/create_audit_table.sql` - Script SQL pour créer les tables
- ✅ `scripts/init_audit_tables.py` - Script Python d'initialisation
- ✅ `scripts/test_permissions_ameliorees.py` - Tests automatisés

#### DAO
- ✅ `data/dao_audit_permission.py` - Gestion des audits
- ✅ `data/dao_otp_tentatives.py` - Gestion des tentatives OTP

#### Documentation
- ✅ `GUIDE_MISE_A_JOUR_PERMISSIONS.md` - Guide de mise à jour
- ✅ `README_PERMISSIONS_AMELIOREES.md` - Documentation complète
- ✅ `CHANGELOG_PERMISSIONS.md` - Ce fichier

---

### 🔄 Fichiers modifiés

| Fichier | Modifications |
|---------|---------------|
| `service_metier/permission_service.py` | + Audit, + Limitation tentatives, + Refus, + Historique, - Cache |
| `controllers/controleur_permission.py` | + Nouvelles méthodes (refus, historique, demandes en attente) |
| `core/vault_service.py` | Amélioration `verifier_hmac()` |

---

### 🗄️ Modifications de la base de données

#### Nouvelles tables

**audit_permissions** :
```sql
CREATE TABLE audit_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code_demandeur VARCHAR(20) NOT NULL,
    role_demandeur VARCHAR(100) NOT NULL,
    est_responsable BOOLEAN DEFAULT FALSE,
    action VARCHAR(50) NOT NULL,
    contexte TEXT,
    code_autorisateur VARCHAR(20),
    statut VARCHAR(20) NOT NULL,
    code_otp_envoye VARCHAR(10),
    email_destinataire VARCHAR(255),
    date_demande DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_reponse DATETIME NULL,
    ip_demandeur VARCHAR(45),
    user_agent TEXT,
    INDEX idx_demandeur (code_demandeur),
    INDEX idx_autorisateur (code_autorisateur),
    INDEX idx_statut (statut),
    INDEX idx_date_demande (date_demande)
);
```

**otp_tentatives** :
```sql
CREATE TABLE otp_tentatives (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code_utilisateur VARCHAR(20) NOT NULL,
    identifiant_otp VARCHAR(255) NOT NULL,
    nb_tentatives INT DEFAULT 0,
    nb_echecs INT DEFAULT 0,
    est_bloque BOOLEAN DEFAULT FALSE,
    date_blocage DATETIME NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_derniere_tentative DATETIME NULL,
    UNIQUE KEY unique_otp (identifiant_otp),
    INDEX idx_utilisateur (code_utilisateur),
    INDEX idx_bloque (est_bloque)
);
```

---

### 🚀 Migration

#### Étape 1 : Créer les tables
```powershell
python scripts\init_audit_tables.py
```

#### Étape 2 : Tester
```powershell
python scripts\test_permissions_ameliorees.py
```

#### Étape 3 : Redémarrer l'application
```powershell
python main.py
```

---

### ⚠️ Breaking Changes

**Aucun** - Toutes les modifications sont rétrocompatibles.

Les anciennes méthodes fonctionnent toujours :
- `verifier_permission()` - Inchangée
- `peut_effectuer_action()` - Inchangée
- `peut_acceder_interface()` - Inchangée
- `demander_autorisation_otp()` - Paramètre `est_responsable` optionnel (défaut: False)
- `valider_autorisation_otp()` - Inchangée

---

### 🐛 Corrections de bugs

- ✅ Suppression du cache OTP redondant (source de bugs potentiels)
- ✅ Amélioration de la vérification HMAC (détection fiable des altérations)
- ✅ Gestion correcte des codes OTP expirés

---

### 📈 Performances

- ✅ Indexation optimale des tables d'audit
- ✅ Nettoyage automatique pour éviter la croissance excessive
- ✅ Requêtes SQL optimisées avec index

---

### 🔒 Sécurité

- ✅ Protection contre les attaques par force brute (limitation tentatives)
- ✅ Traçabilité complète pour audit de sécurité
- ✅ Vérification d'intégrité robuste (HMAC)
- ✅ Déblocage automatique après expiration

---

### 📚 Documentation

- ✅ Guide de mise à jour complet
- ✅ README détaillé
- ✅ Commentaires dans le code
- ✅ Tests automatisés documentés
- ✅ Ce CHANGELOG

---

### ✅ Tests

- ✅ Test de limitation des tentatives OTP
- ✅ Test du système d'audit
- ✅ Test du service de permissions
- ✅ Test du nettoyage automatique
- ✅ Script de test automatisé : `test_permissions_ameliorees.py`

---

### 🎯 Prochaines étapes (TODO)

- [ ] Notification au demandeur lors d'un refus
- [ ] Interface graphique pour consulter l'historique
- [ ] Dashboard de statistiques
- [ ] Export des audits en CSV/PDF
- [ ] Délégation temporaire de droits
- [ ] Configuration de la durée de validité des OTP

---

### 👥 Contributeurs

- Développement initial : Équipe projet
- Améliorations v2.0 : Assistant IA

---

### 📞 Support

Pour toute question :
- Consultez `README_PERMISSIONS_AMELIOREES.md`
- Consultez `GUIDE_MISE_A_JOUR_PERMISSIONS.md`
- Exécutez `test_permissions_ameliorees.py`

---

## Version 1.0.0 - Version initiale

### Fonctionnalités de base

- ✅ Authentification à deux facteurs (MFA) avec Vault
- ✅ Génération de codes OTP à 6 chiffres
- ✅ Envoi par email via SMTP
- ✅ Vérification des permissions selon le rôle
- ✅ Mapping rôle → interfaces
- ✅ Actions : lecture, impression, modification, suppression, consultation
- ✅ Dialogues OTP modernes (PySide6)
- ✅ Intégration HashiCorp Vault (TOTP + Transit)

---

**Date de dernière mise à jour** : 2024  
**Version actuelle** : 2.0.0
