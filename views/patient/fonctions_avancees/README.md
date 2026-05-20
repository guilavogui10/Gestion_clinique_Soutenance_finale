# 📋 HISTORIQUE PATIENT - Architecture Modulaire

## 🎯 Vue d'ensemble

Module de gestion avancée de l'historique patient avec navigation hiérarchique dynamique.

```
Patient → Visites → Consultations → Actes Médicaux → Résultats
```

---

## 📁 Structure des fichiers

```
views/patient/fonctions_avancees/
├── __init__.py                          # Point d'entrée du module
├── historique_patient_widget.py         # Widget principal (orchestrateur)
├── visites_table_widget.py              # Tableau des visites
├── consultations_table_widget.py        # Tableau des consultations
├── actes_table_widget.py                # Tableau des actes médicaux
└── README.md                            # Cette documentation
```

---

## 🔄 Flux de navigation

### Niveau 1 : Visites
**Fichier** : `visites_table_widget.py`

**Affichage** :
- Tableau des visites du patient sélectionné
- Colonnes : Code, Date, Motif, Statut, Session, Action
- Bouton "Voir Info" sur chaque ligne

**Actions** :
- Clic sur "Voir Info" → Affiche les consultations de cette visite

---

### Niveau 2 : Consultations
**Fichier** : `consultations_table_widget.py`

**Affichage** :
- Tableau des consultations de la visite sélectionnée
- Colonnes : Code, Date, Diagnostique, Frais, Statut Facture, Action
- Bouton "Retour aux visites"
- Bouton "Voir Actes" sur chaque ligne

**Actions** :
- Clic sur "Voir Actes" → Affiche les actes de cette consultation
- Clic sur "Retour" → Retour au tableau des visites

---

### Niveau 3 : Actes Médicaux
**Fichier** : `actes_table_widget.py`

**Affichage** :
- Tableau des actes de la consultation sélectionnée
- Colonnes : Code, Type, Libellé, Décision, Statut, Info, Résultats
- Bouton "Retour aux consultations"
- Bouton "Info" : Affiche les détails de l'acte
- Bouton "Résultats" : Ouvre la page résultats médicaux

**Actions** :
- Clic sur "Info" → Popup avec détails de l'acte
- Clic sur "Résultats" → Navigation vers module résultats
- Clic sur "Retour" → Retour au tableau des consultations

---

## 🎨 Composants visuels

### Fil d'Ariane (Breadcrumb)
Affiche la position actuelle dans la hiérarchie :

```
Patient : Jean Dupont
Patient : Jean Dupont → Visite : VIS-00000001
Patient : Jean Dupont → Visite : VIS-00000001 → Consultation : CON-00000001
```

### Bouton "Nouvelle Visite"
- Toujours visible en haut
- Activé uniquement quand un patient est sélectionné
- Émet le signal `nouvelle_visite_clicked`

### Barres de recherche
Chaque tableau a sa propre barre de recherche pour filtrer les données.

---

## 🔌 Signaux émis

### HistoriquePatientWidget
```python
nouvelle_visite_clicked = Signal()
voir_resultat_clicked = Signal(str, str)  # (type_acte, code_acte)
```

### VisitesTableWidget
```python
visite_clicked = Signal(dict)  # Émet la visite sélectionnée
```

### ConsultationsTableWidget
```python
consultation_clicked = Signal(dict)  # Émet la consultation sélectionnée
retour_clicked = Signal()
```

### ActesTableWidget
```python
voir_resultat_clicked = Signal(str, str)  # (type_acte, code_acte)
retour_clicked = Signal()
```

---

## 🔗 Intégration dans vue_patient_new.py

### Étape 1 : Importer le module
```python
from .fonctions_avancees import HistoriquePatientWidget
```

### Étape 2 : Créer l'onglet
```python
def _create_historique_tab(self):
    """Crée l'onglet Historique Patient"""
    self.historique_widget = HistoriquePatientWidget(
        controleur_patient=self.controleur,
        controleur_visite=self.controleur_visite,
        controleur_consultation=self.controleur_consultation,
        controleur_acte=self.controleur_acte,
        parent=self
    )
    
    # Connecter les signaux
    self.historique_widget.nouvelle_visite_clicked.connect(self._on_nouvelle_visite)
    self.historique_widget.voir_resultat_clicked.connect(self._on_voir_resultat)
    
    return self.historique_widget
```

### Étape 3 : Ajouter l'onglet au QTabWidget
```python
self.tab_historique = self._create_historique_tab()
icon_historique = self._get_icon("history")
self.tabs.addTab(self.tab_historique, icon_historique, "Historique Patient")
```

### Étape 4 : Charger le patient sélectionné
```python
def on_view_patient(self, patient):
    """Affiche l'historique d'un patient"""
    # Basculer vers l'onglet Historique
    self.tabs.setCurrentIndex(3)  # Index de l'onglet Historique
    
    # Charger les données du patient
    self.historique_widget.charger_patient(patient)
```

---

## 📊 Méthodes des contrôleurs requises

### ControleurVisite
```python
def lister_visites_patient(self, code_patient) -> list:
    """Retourne toutes les visites d'un patient"""
    pass
```

### ControleurConsultation
```python
def lister_consultations_visite(self, code_visite) -> list:
    """Retourne toutes les consultations d'une visite"""
    pass
```

### ControleurActe
```python
def lister_actes_consultation(self, code_consultation) -> list:
    """Retourne tous les actes d'une consultation"""
    pass
```

---

## 🎨 Thème

Tous les widgets utilisent `theme_manager` pour un style cohérent :
- Couleurs primaires, secondaires, accent
- Bordures arrondies
- Hover effects
- Responsive design

---

## ✅ Avantages de cette architecture

1. **Modulaire** : Chaque niveau est dans son propre fichier
2. **Réutilisable** : Les widgets peuvent être utilisés ailleurs
3. **Maintenable** : Facile à modifier et déboguer
4. **Extensible** : Facile d'ajouter de nouveaux niveaux
5. **Testable** : Chaque composant peut être testé indépendamment

---

## 🚀 Prochaines étapes

1. ✅ Créer les méthodes dans les contrôleurs
2. ✅ Intégrer dans `vue_patient_new.py`
3. ✅ Tester la navigation
4. ✅ Connecter avec le module résultats médicaux
5. ✅ Ajouter les permissions si nécessaire

---

## 📝 Notes

- Les données sont chargées dynamiquement à chaque niveau
- La navigation est fluide avec QStackedWidget
- Les boutons "Retour" permettent de remonter dans la hiérarchie
- Le fil d'Ariane indique toujours la position actuelle
