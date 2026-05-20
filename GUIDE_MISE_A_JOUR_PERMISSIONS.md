# 🔄 Guide de mise à jour - Système de permissions amélioré

## 📋 Nouvelles fonctionnalités

### ✅ Améliorations apportées

1. **Audit complet** : Traçabilité de toutes les demandes d'autorisation
2. **Limitation des tentatives** : Blocage après 3 codes OTP invalides (15 minutes)
3. **Gestion des refus** : Le responsable peut refuser explicitement une demande
4. **Historique** : Consultation de l'historique des demandes par utilisateur
5. **Vérification HMAC améliorée** : Comparaison réelle des hash pour l'intégrité
6. **Suppression du cache redondant** : Vault gère tout

---

## 🚀 Installation des mises à jour

### Étape 1 : Créer les nouvelles tables

```powershell
cd c:\Users\Kaissa BILIVOGUI\Desktop\projet_final\projetSoutenance
.\venv\Scripts\Activate.ps1
python scripts\init_audit_tables.py
```

**Résultat attendu** :
```
✅ Table 'audit_permissions' créée avec succès
✅ Table 'otp_tentatives' créée avec succès
```

### Étape 2 : Vérifier les nouvelles dépendances

Les nouveaux fichiers créés :
- ✅ `data/dao_audit_permission.py`
- ✅ `data/dao_otp_tentatives.py`
- ✅ `scripts/init_audit_tables.py`
- ✅ `scripts/create_audit_table.sql`

Les fichiers modifiés :
- ✅ `service_metier/permission_service.py`
- ✅ `controllers/controleur_permission.py`
- ✅ `core/vault_service.py`

---

## 📊 Nouvelles tables

### Table `audit_permissions`

Stocke toutes les demandes d'autorisation :

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | INT | Identifiant unique |
| `code_demandeur` | VARCHAR(20) | Code de l'utilisateur qui demande |
| `role_demandeur` | VARCHAR(100) | Rôle du demandeur |
| `est_responsable` | BOOLEAN | Si le demandeur est responsable |
| `action` | VARCHAR(50) | Type d'action (modification, suppression, consultation) |
| `contexte` | TEXT | Description de l'action |
| `code_autorisateur` | VARCHAR(20) | Code du responsable/DG qui autorise |
| `statut` | VARCHAR(20) | en_attente, autorise, refuse, expire |
| `code_otp_envoye` | VARCHAR(10) | Code OTP (pour debug) |
| `email_destinataire` | VARCHAR(255) | Email où l'OTP a été envoyé |
| `date_demande` | DATETIME | Date de la demande |
| `date_reponse` | DATETIME | Date de la réponse |
| `ip_demandeur` | VARCHAR(45) | Adresse IP du demandeur |

### Table `otp_tentatives`

Gère les tentatives OTP et le blocage :

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | INT | Identifiant unique |
| `code_utilisateur` | VARCHAR(20) | Code de l'utilisateur |
| `identifiant_otp` | VARCHAR(255) | Identifiant unique de l'OTP |
| `nb_tentatives` | INT | Nombre total de tentatives |
| `nb_echecs` | INT | Nombre d'échecs |
| `est_bloque` | BOOLEAN | Si l'utilisateur est bloqué |
| `date_blocage` | DATETIME | Date du blocage |
| `date_creation` | DATETIME | Date de création |
| `date_derniere_tentative` | DATETIME | Date de la dernière tentative |

---

## 🔧 Nouvelles méthodes disponibles

### Dans `PermissionService`

```python
# Refuser une demande
refuser_autorisation(
    code_utilisateur: str,
    action: str,
    contexte: str,
    code_autorisateur: str,
    raison: str = "Refusé par le responsable"
) -> Tuple[bool, str]

# Obtenir les demandes en attente
obtenir_demandes_en_attente(
    code_autorisateur: str
) -> List[Dict]

# Obtenir l'historique d'un utilisateur
obtenir_historique_utilisateur(
    code_utilisateur: str,
    limite: int = 50
) -> List[Dict]
```

### Dans `PermissionControleur`

```python
# Refuser une autorisation
refuser_autorisation(
    code_utilisateur: str,
    action: str,
    contexte: str,
    code_autorisateur: str,
    raison: str = "Refusé par le responsable"
) -> Dict[str, any]

# Obtenir les demandes en attente
obtenir_demandes_en_attente(
    code_autorisateur: str
) -> Dict[str, any]

# Obtenir l'historique
obtenir_historique_utilisateur(
    code_utilisateur: str,
    limite: int = 50
) -> Dict[str, any]
```

---

## 🎯 Utilisation des nouvelles fonctionnalités

### 1. Limitation des tentatives OTP

**Comportement** :
- L'utilisateur a **3 tentatives** pour saisir le bon code OTP
- Après 3 échecs, le compte est **bloqué pendant 15 minutes**
- Un message indique le nombre de tentatives restantes

**Exemple** :
```python
# Tentative 1 (échec)
valide, message = permission_service.valider_autorisation_otp(...)
# message = "Code invalide. 2 tentative(s) restante(s)."

# Tentative 2 (échec)
valide, message = permission_service.valider_autorisation_otp(...)
# message = "Code invalide. 1 tentative(s) restante(s)."

# Tentative 3 (échec)
valide, message = permission_service.valider_autorisation_otp(...)
# message = "Trop de tentatives. Compte bloqué pour 15 minutes."
```

### 2. Audit des demandes

**Toutes les demandes sont enregistrées** :
```python
# Consulter l'historique d'un utilisateur
historique = permission_controleur.obtenir_historique_utilisateur("U0001")

# Résultat :
{
    "status": "success",
    "historique": [
        {
            "id": 1,
            "action": "modification",
            "contexte": "Chirurgie #CH001",
            "statut": "autorise",
            "code_autorisateur": "U0002",
            "date_demande": "2024-01-15 10:30:00",
            "date_reponse": "2024-01-15 10:31:23",
            "temps_reponse_sec": 83
        },
        ...
    ],
    "count": 5
}
```

### 3. Gestion des refus

**Le responsable peut refuser une demande** :
```python
# Refuser une demande
resultat = permission_controleur.refuser_autorisation(
    code_utilisateur="U0003",
    action="modification",
    contexte="Chirurgie #CH001",
    code_autorisateur="U0002",
    raison="Action non justifiée"
)

# Résultat :
{
    "status": "success",
    "message": "Demande refusée. Raison : Action non justifiée"
}
```

### 4. Consultation des demandes en attente

**Le responsable peut voir toutes ses demandes en attente** :
```python
# Obtenir les demandes en attente
demandes = permission_controleur.obtenir_demandes_en_attente("U0002")

# Résultat :
{
    "status": "success",
    "demandes": [
        {
            "id": 5,
            "code_demandeur": "U0003",
            "role_demandeur": "chirurgien",
            "action": "modification",
            "contexte": "Chirurgie #CH002",
            "email_destinataire": "responsable@clinique.com",
            "date_demande": "2024-01-15 11:00:00",
            "secondes_ecoulees": 120
        },
        ...
    ],
    "count": 3
}
```

---

## 🔐 Configuration

### Paramètres modifiables

Dans `dao_otp_tentatives.py` :

```python
class OTPTentativesDAO:
    # Nombre maximum de tentatives avant blocage
    MAX_TENTATIVES = 3
    
    # Durée du blocage en minutes
    DUREE_BLOCAGE_MINUTES = 15
```

**Pour modifier** :
1. Ouvrez `data/dao_otp_tentatives.py`
2. Changez les valeurs de `MAX_TENTATIVES` et `DUREE_BLOCAGE_MINUTES`
3. Redémarrez l'application

---

## 🧹 Maintenance

### Nettoyage automatique

**Anciennes demandes d'audit** :
```python
# Supprimer les demandes de plus de 90 jours
from data.dao_audit_permission import AuditPermissionDAO
audit_dao = AuditPermissionDAO()
nb_supprime = audit_dao.nettoyer_anciennes_demandes(jours=90)
print(f"{nb_supprime} demandes supprimées")
```

**Anciennes tentatives OTP** :
```python
# Supprimer les tentatives de plus de 24 heures
from data.dao_otp_tentatives import OTPTentativesDAO
tentatives_dao = OTPTentativesDAO()
nb_supprime = tentatives_dao.nettoyer_anciennes_tentatives(heures=24)
print(f"{nb_supprime} tentatives supprimées")
```

**Recommandation** : Créer une tâche planifiée (cron/Task Scheduler) pour exécuter ces nettoyages quotidiennement.

---

## 📈 Statistiques

**Obtenir des statistiques sur les demandes** :
```python
from data.dao_audit_permission import AuditPermissionDAO
from datetime import datetime, timedelta

audit_dao = AuditPermissionDAO()

# Statistiques des 30 derniers jours
date_debut = datetime.now() - timedelta(days=30)
date_fin = datetime.now()

stats = audit_dao.obtenir_statistiques(date_debut, date_fin)

# Résultat :
{
    "total_demandes": 150,
    "autorisees": 120,
    "refusees": 15,
    "expirees": 10,
    "en_attente": 5,
    "temps_moyen_reponse_sec": 95.5
}
```

---

## ✅ Checklist de mise à jour

- [ ] Tables créées (`init_audit_tables.py` exécuté)
- [ ] Nouveaux fichiers DAO présents
- [ ] `permission_service.py` mis à jour
- [ ] `controleur_permission.py` mis à jour
- [ ] `vault_service.py` mis à jour
- [ ] Application redémarrée
- [ ] Test de limitation des tentatives
- [ ] Test de l'audit
- [ ] Test du refus d'autorisation

---

## 🐛 Dépannage

### Erreur "Table doesn't exist"

**Solution** : Exécutez le script d'initialisation
```powershell
python scripts\init_audit_tables.py
```

### Erreur "Module not found: dao_audit_permission"

**Solution** : Vérifiez que les nouveaux fichiers sont présents dans `data/`

### Les tentatives ne sont pas limitées

**Solution** : Vérifiez que la table `otp_tentatives` existe et est accessible

---

## 📞 Support

Pour toute question sur les nouvelles fonctionnalités :
- Consultez ce guide
- Consultez `GUIDE_TEST_PERMISSIONS.md`
- Consultez les commentaires dans le code source

---

**Bon déploiement ! 🚀**
