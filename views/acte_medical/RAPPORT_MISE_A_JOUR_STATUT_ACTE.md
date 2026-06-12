# 📋 RAPPORT — Mise à jour du statut acte dans module Acte Médical

## 🎯 Vue d'ensemble

Le module Acte Médical gère le statut des actes via **2 niveaux** :
1. **Statut acte** (`statut_acte`) : État de l'acte médical lui-même
2. **Statut passage** (`statut_passage`) : État du passage du patient dans le service

---

## 📊 États possibles

### Statut acte (`statut_acte`)
| Statut | Description | Transition depuis |
|--------|-------------|-------------------|
| `en_attente` | Patient choisi "maintenant", acte en file d'attente | Création avec `choix_patient="maintenant"` |
| `planifie` | Patient choisi "plus tard", rendez-vous prévu | Création avec `choix_patient="plus_tard"` |
| `en_cours` | Acte en cours d'exécution | `demarrer_passage()` |
| `termine` | Acte terminé avec succès | `terminer_passage()` |
| `refuse` | Patient choisi "ailleurs" | Création avec `choix_patient="ailleurs"` |

### Statut passage (`statut_passage` dans table `actes_visite`)
| Statut | Description |
|--------|-------------|
| `en_attente` | Patient dans la file d'attente du service |
| `en_cours` | Service en cours d'exécution |
| `termine` | Service terminé |

---

## 🔧 Méthodes de mise à jour du statut

### 1️⃣ Démarrage d'un passage (Patient → En cours)

#### 📍 **Localisation VUE**
**Fichier :** `views/acte_medical/vue_acte_medical.py`
**Ligne :** 1198-1213

```python
def _demarrer_passage(self, code_acte: int):
    """
    Démarre un passage depuis la file d'attente :
      - Renseigne date_debut_execution
      - Change statut_passage en en_cours
      - Change statut_acte en en_cours
      - Met à jour statut_patient (Attente X -> En X)
    """
    if code_acte is None:
        return
    ok, msg = self.ctrl.demarrer_passage_par_code_acte(code_acte)
    if ok:
        # Mise à jour INSTANTANÉE de la file d'attente (statut + boutons)
        self._update_file_attente()
        self.load_data()
        
        CustomMessageBox.success(
            self, "Démarré",
            f"Passage pour l'acte #{code_acte} démarré avec succès."
        )
    else:
        CustomMessageBox.warning(self, "Impossible de démarrer", str(msg))
```

**Déclenchement :** Bouton "Démarrer" dans la carte patient (onglet File d'attente)

---

#### 📍 **Localisation CONTRÔLEUR**
**Fichier :** `controllers/controleur_acte_medicale.py`
**Lignes :** 159-162

```python
def demarrer_passage_par_code_acte(self, code_acte: int) -> tuple:
    """Démarre un passage en utilisant le code_acte (clé de actes_visite)."""
    return self.service_file.demarrer_passage_par_code_acte(code_acte)
```

**Méthode alternative :** `demarrer_passage(id_acte_visite)` (lignes 155-158)

---

#### 📍 **Localisation SERVICE**
**Fichier :** `service_metier/file_attente_service.py` (déduit)

**Méthode :** `demarrer_passage_par_code_acte(code_acte: int)`

**Actions effectuées :**
1. ✅ Récupère l'enregistrement dans `actes_visite` WHERE `code_acte = ?`
2. ✅ Renseigne `date_debut_execution = NOW()`
3. ✅ Met à jour `statut_passage = 'en_cours'`
4. ✅ Met à jour `statut_acte = 'en_cours'` dans table `actes_medicaux`
5. ✅ Met à jour `statut_patient` dans table `visites` :
   - `"Attente examen"` → `"En examen"`
   - `"Attente chirurgie"` → `"En chirurgie"`
   - `"Attente lunette"` → `"En lunette"`
   - `"Attente pharmacie"` → `"En pharmacie"`

---

### 2️⃣ Fin d'un passage (En cours → Terminé)

#### 📍 **Localisation VUE**
**Fichier :** `views/acte_medical/vue_acte_medical.py`
**Ligne :** 1215-1234

```python
def _terminer_passage(self, code_acte: int):
    """
    Termine un passage en cours :
      - Renseigne date_sortie
      - Change statut_passage en termine
      - Change statut_acte en termine
      - Calcule durée_attente = date_debut_execution - date_entre
      - Calcule durée_execution = date_sortie - date_debut_execution
      - Calcule durée_totale = date_sortie - date_entre
      - Met à jour statut_patient (En X -> X terminé)
    """
    if code_acte is None:
        return
    ok, msg = self.ctrl.terminer_passage_par_code_acte(code_acte)
    if ok:
        # Mise à jour INSTANTANÉE de la file d'attente (statut + boutons)
        self._update_file_attente()
        self.load_data()
        
        CustomMessageBox.success(
            self, "Terminé",
            f"Passage pour l'acte #{code_acte} terminé avec succès."
        )
    else:
        CustomMessageBox.warning(self, "Impossible de terminer", str(msg))
```

**Déclenchement :** Bouton "Terminer" dans la carte patient (onglet File d'attente)

---

#### 📍 **Localisation CONTRÔLEUR**
**Fichier :** `controllers/controleur_acte_medicale.py`
**Lignes :** 167-169

```python
def terminer_passage_par_code_acte(self, code_acte: int, raison: str = None) -> tuple:
    """Termine un passage en utilisant le code_acte."""
    return self.service_file.terminer_passage_par_code_acte(code_acte, raison)
```

**Méthode alternative :** `terminer_passage(id_acte_visite, raison)` (lignes 163-165)

---

#### 📍 **Localisation SERVICE**
**Fichier :** `service_metier/file_attente_service.py` (déduit)

**Méthode :** `terminer_passage_par_code_acte(code_acte: int, raison: str = None)`

**Actions effectuées :**
1. ✅ Récupère l'enregistrement dans `actes_visite` WHERE `code_acte = ?`
2. ✅ Renseigne `date_sortie = NOW()`
3. ✅ Met à jour `statut_passage = 'termine'`
4. ✅ Met à jour `statut_acte = 'termine'` dans table `actes_medicaux`
5. ✅ Calcule les durées :
   - `durée_attente = date_debut_execution - date_entre`
   - `durée_execution = date_sortie - date_debut_execution`
   - `durée_totale = date_sortie - date_entre`
6. ✅ Met à jour `statut_patient` dans table `visites` :
   - `"En examen"` → `"Examen terminé"`
   - `"En chirurgie"` → `"Chirurgie terminée"`
   - `"En lunette"` → `"Lunette terminée"`
   - `"En pharmacie"` → `"Pharmacie terminée"`

---

### 3️⃣ Terminaison via formulaires spécifiques

**Particularité :** Pour certains types d'actes, le bouton "Terminer" ouvre un formulaire au lieu de terminer directement.

#### 📍 **Fichier :** `views/acte_medical/vue_acte_medical.py`
**Lignes :** 1076-1098

```python
# Bouton Terminer (visible si date_debut_execution != NULL ET date_sortie = NULL)
if id_acte_visite and date_debut is not None and date_sortie is None:
    # Récupérer le type d'acte pour savoir quel formulaire ouvrir
    type_acte = acte.get('type_acte', '').lower()
    
    btn_end = QPushButton("  Terminer")
    # ...styles...
    
    # Connecter selon le type d'acte
    if type_acte == 'examen':
        btn_end.clicked.connect(lambda: self._ouvrir_formulaire_examen(id_acte_visite))
    elif type_acte == 'chirurgie':
        btn_end.clicked.connect(lambda: self._ouvrir_formulaire_chirurgie(id_acte_visite))
    elif type_acte == 'lunette':
        btn_end.clicked.connect(lambda: self._ouvrir_formulaire_lunette(id_acte_visite))
    elif type_acte == 'prescription':
        btn_end.clicked.connect(lambda: self._ouvrir_formulaire_prescription(id_acte_visite))
    else:
        # Par défaut, terminer directement
        btn_end.clicked.connect(lambda: self._terminer_passage(id_acte_visite))
    layout.addWidget(btn_end)
```

#### Workflow pour chaque type :

**A. Examen** (lignes 1236-1296)
```python
def _ouvrir_formulaire_examen(self, code_acte: str):
    # 1. Navigue vers page Examen (index 5)
    # 2. Pré-remplit le formulaire avec code_acte
    # 3. Après enregistrement du formulaire → terminer_passage() automatiquement
```

**B. Chirurgie** (lignes 1298-1342)
```python
def _ouvrir_formulaire_chirurgie(self, code_acte: str):
    # 1. Navigue vers page Chirurgie (index 6)
    # 2. Pré-remplit le formulaire avec code_consultation
    # 3. Connexion one-shot : après sauvegarde → _terminer_et_rediriger()
```

**C. Lunette** (lignes 1344-1378)
```python
def _ouvrir_formulaire_lunette(self, code_acte: str):
    # 1. Navigue vers page Lunettes (index 7)
    # 2. Pré-remplit le formulaire avec code_acte
    # 3. Connexion one-shot : après sauvegarde → _terminer_et_rediriger()
```

**D. Prescription** (lignes 1380-1409)
```python
def _ouvrir_formulaire_prescription(self, code_acte: str):
    # 1. Navigue vers page Prescription (index 9)
    # 2. Ouvre le panier avec code_acte pré-rempli
    # 3. Connexion one-shot : après validation → _terminer_et_rediriger()
```

---

### 4️⃣ Méthode auxiliaire : _terminer_et_rediriger()

**Fichier :** `views/acte_medical/vue_acte_medical.py`
**Lignes :** 1411-1426

```python
def _terminer_et_rediriger(self, code_acte: str):
    """Termine le passage en file d'attente et redirige vers acte_médical."""
    ok, msg = self.ctrl.terminer_passage_par_code_acte(code_acte)
    if ok:
        code_consultation = self.ctrl.obtenir_code_consultation_par_acte(code_acte)
        dashboard = self._trouver_dashboard_parent()
        if dashboard:
            dashboard.workspace_stack.setCurrentIndex(15)
            if hasattr(dashboard, 'lbl_page_title'):
                dashboard.lbl_page_title.setText("Gestion des Actes Médicaux")
            
            # Rafraîchir la file d'attente immédiatement
            if hasattr(dashboard, 'page_actes'):
                QTimer.singleShot(100, lambda: dashboard.page_actes._update_file_attente())
                if code_consultation:
                    QTimer.singleShot(200, lambda c=code_consultation: 
                        dashboard.page_actes._filtrer_par_consultation(c))
    else:
        self.logger.warning(f"[_terminer_et_rediriger] Impossible de terminer le passage: {msg}")
```

**Rôle :**
1. ✅ Appelle `terminer_passage_par_code_acte()`
2. ✅ Navigue vers page Acte Médical (index 15)
3. ✅ Rafraîchit la file d'attente immédiatement (QTimer 100ms)
4. ✅ Filtre sur la consultation du patient (QTimer 200ms)

---

## 📊 Autres méthodes de changement de statut

### 5️⃣ Refuser un acte

**Contrôleur :** `refuser_acte(code_acte, raison)` (ligne 114)
- Met `statut_acte = 'refuse'`
- Enregistre la raison dans `raison_refus`

### 6️⃣ Planifier un acte

**Contrôleur :** `planifier_acte(code_acte)` (ligne 118)
- Met `statut_acte = 'planifie'`

### 7️⃣ Terminer un acte (sans passage)

**Contrôleur :** `terminer_acte(code_acte, raison)` (ligne 110)
- Met `statut_acte = 'termine'`
- Utilisé quand l'acte est terminé sans être passé en file (ex: refus puis acceptation ailleurs)

### 8️⃣ Passer en cours (sans passage)

**Contrôleur :** `passer_en_cours(code_acte)` (ligne 106)
- Met `statut_acte = 'en_cours'`
- Utilisé rarement (normalement via `demarrer_passage()`)

---

## 🎬 Workflow complet (Exemple : Examen)

### Étape 1 : Création de l'acte
```
Consultation terminée
  ↓
Médecin prescrit examen (décision médicale)
  ↓
Création acte : type_acte='examen', choix_patient='maintenant'
  ↓
statut_acte = 'en_attente'
mode_realisation = 'interne'
  ↓
Ajout dans file d'attente (actes_visite)
  ↓
statut_passage = 'en_attente'
statut_patient = 'Attente examen'
```

### Étape 2 : Patient dans la file
```
Patient visible dans onglet "File d'attente"
  ↓
Carte affiche : "Attente examen" (orange)
  ↓
Bouton "Démarrer" visible
```

### Étape 3 : Démarrage du passage
```
Clic bouton "Démarrer"
  ↓
Appel : _demarrer_passage(code_acte)
  ↓
Contrôleur : demarrer_passage_par_code_acte()
  ↓
Service : demarrer_passage_par_code_acte()
  ✅ date_debut_execution = NOW()
  ✅ statut_passage = 'en_cours'
  ✅ statut_acte = 'en_cours'
  ✅ statut_patient = 'En examen'
  ↓
Vue : Rafraîchissement instantané (_update_file_attente())
  ↓
Carte affiche : "En examen" (bleu)
  ↓
Bouton "Démarrer" → remplacé par "Terminer"
```

### Étape 4 : Fin du passage
```
Clic bouton "Terminer"
  ↓
Appel : _ouvrir_formulaire_examen(code_acte)
  ↓
Navigation vers page Examen
  ↓
Formulaire pré-rempli avec code_acte
  ↓
Utilisateur remplit et enregistre
  ↓
Signal : examen_saved émis
  ↓
Callback : _apres_sauvegarde() → _terminer_et_rediriger(code_acte)
  ↓
Contrôleur : terminer_passage_par_code_acte()
  ↓
Service : terminer_passage_par_code_acte()
  ✅ date_sortie = NOW()
  ✅ statut_passage = 'termine'
  ✅ statut_acte = 'termine'
  ✅ statut_patient = 'Examen terminé'
  ✅ Calcul durées (attente, exécution, totale)
  ↓
Vue : Rafraîchissement instantané + retour page Acte Médical
  ↓
Carte affiche : "Examen terminé" (gris)
  ↓
Boutons décision médecin : "Nouvel acte" | "Aller en paiement" | "Contrôle"
```

---

## 🔍 Structure des tables (déduite)

### Table `actes_medicaux`
```sql
CREATE TABLE actes_medicaux (
    id_acte INTEGER PRIMARY KEY,
    code_consultation TEXT,
    type_acte TEXT,                  -- 'examen', 'chirurgie', 'lunette', 'prescription'
    decision_medicale TEXT,
    choix_patient TEXT,               -- 'maintenant', 'plus_tard', 'ailleurs'
    mode_realisation TEXT,            -- 'interne', 'externe'
    statut_acte TEXT,                 -- 'en_attente', 'planifie', 'en_cours', 'termine', 'refuse'
    raison_refus TEXT,
    date_creation DATETIME,
    source_acte TEXT
);
```

### Table `actes_visite` (file d'attente)
```sql
CREATE TABLE actes_visite (
    id_acte_visite INTEGER PRIMARY KEY,
    code_acte INTEGER REFERENCES actes_medicaux(id_acte),
    code_visite TEXT REFERENCES visites(code_visite),
    type_acte TEXT,
    date_entre DATETIME,              -- Date d'entrée en file d'attente
    date_debut_execution DATETIME,    -- Date de début du service
    date_sortie DATETIME,             -- Date de fin du service
    statut_passage TEXT,              -- 'en_attente', 'en_cours', 'termine'
    duree_attente INTEGER,            -- En minutes
    duree_execution INTEGER,          -- En minutes
    duree_totale INTEGER              -- En minutes
);
```

### Table `visites`
```sql
CREATE TABLE visites (
    code_visite TEXT PRIMARY KEY,
    code_patient TEXT,
    date_visite DATETIME,
    statut_patient TEXT,              -- 'Attente consultation', 'En consultation', 
                                      -- 'Attente examen', 'En examen', 'Examen terminé',
                                      -- 'Attente chirurgie', 'En chirurgie', 'Chirurgie terminée',
                                      -- 'Attente lunette', 'En lunette', 'Lunette terminée',
                                      -- 'Attente pharmacie', 'En pharmacie', 'Pharmacie terminée',
                                      -- 'Attente payement'
    urgent BOOLEAN
);
```

---

## 📝 Points importants

### ✅ Mise à jour instantanée
Après chaque changement de statut :
```python
# Rafraîchissement IMMÉDIAT de la file d'attente
self._update_file_attente()
self.load_data()
```
→ Pas besoin d'attendre le timer (3s), l'UI se met à jour instantanément

### ✅ Callbacks one-shot
Pour éviter les doubles appels, les signaux sont déconnectés après utilisation :
```python
def _apres_sauvegarde():
    try:
        page.form_widget.examen_saved.disconnect(_apres_sauvegarde)
    except Exception:
        pass
    self._terminer_et_rediriger(code_acte)
```

### ✅ Synchronisation avec statut_patient
Le `statut_patient` dans la table `visites` est TOUJOURS synchronisé avec le `statut_acte` :
- `demarrer_passage()` → `"Attente X"` → `"En X"`
- `terminer_passage()` → `"En X"` → `"X terminé"`

### ✅ Calcul automatique des durées
Le service calcule automatiquement :
- **Durée d'attente** : Temps entre arrivée et début service
- **Durée d'exécution** : Temps du service lui-même
- **Durée totale** : Temps total dans le service

---

## 🎯 Résumé des méthodes clés

| Méthode | Fichier | Ligne | Rôle |
|---------|---------|-------|------|
| `_demarrer_passage()` | `vue_acte_medical.py` | 1198 | Démarre un passage (vue) |
| `demarrer_passage_par_code_acte()` | `controleur_acte_medicale.py` | 159 | Proxy contrôleur |
| `demarrer_passage_par_code_acte()` | `file_attente_service.py` | ? | Logique métier (service) |
| `_terminer_passage()` | `vue_acte_medical.py` | 1215 | Termine un passage directement (vue) |
| `terminer_passage_par_code_acte()` | `controleur_acte_medicale.py` | 167 | Proxy contrôleur |
| `terminer_passage_par_code_acte()` | `file_attente_service.py` | ? | Logique métier (service) |
| `_ouvrir_formulaire_examen()` | `vue_acte_medical.py` | 1236 | Termine via formulaire examen |
| `_ouvrir_formulaire_chirurgie()` | `vue_acte_medical.py` | 1298 | Termine via formulaire chirurgie |
| `_ouvrir_formulaire_lunette()` | `vue_acte_medical.py` | 1344 | Termine via formulaire lunette |
| `_ouvrir_formulaire_prescription()` | `vue_acte_medical.py` | 1380 | Termine via formulaire prescription |
| `_terminer_et_rediriger()` | `vue_acte_medical.py` | 1411 | Termine + retour acte médical |

---

## 🚀 Utilisation pratique

### Pour démarrer un acte depuis la file d'attente :
```python
ok, msg = self.ctrl.demarrer_passage_par_code_acte(code_acte)
if ok:
    self._update_file_attente()  # Rafraîchir immédiatement
```

### Pour terminer un acte depuis la file d'attente :
```python
ok, msg = self.ctrl.terminer_passage_par_code_acte(code_acte)
if ok:
    self._update_file_attente()  # Rafraîchir immédiatement
```

### Pour terminer via formulaire (examen, chirurgie, lunette, prescription) :
```python
# 1. Ouvrir le formulaire pré-rempli
self._ouvrir_formulaire_examen(code_acte)

# 2. Dans le formulaire, après enregistrement, connecter :
def _apres_sauvegarde():
    try:
        form.examen_saved.disconnect(_apres_sauvegarde)
    except:
        pass
    # Terminer le passage automatiquement
    self.ctrl.terminer_passage_par_code_acte(code_acte)
    self._update_file_attente()

form.examen_saved.connect(_apres_sauvegarde)
```

---

**Rapport généré le :** {date_actuelle}
**Fichier source principal :** `views/acte_medical/vue_acte_medical.py`
