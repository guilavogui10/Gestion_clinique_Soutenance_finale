"""
Widget principal de l'historique patient
Affiche dynamiquement : Visites → Consultations → Actes → Résultats
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                QLabel, QFrame, QStackedWidget)
from PySide6.QtCore import Qt, Signal
import qtawesome as qta
from views.shared.theme_manager import theme_manager

from .visites_table_widget import VisitesTableWidget
from .consultations_table_widget import ConsultationsTableWidget
from .actes_table_widget import ActesTableWidget


class HistoriquePatientWidget(QWidget):
    """Widget principal affichant l'historique complet d'un patient"""
    
    # Signaux
    nouvelle_visite_clicked = Signal()
    voir_resultat_clicked = Signal(str, str)  # (type_acte, code_acte)
    
    def __init__(self, controleur_patient, controleur_visite, controleur_consultation, 
                 controleur_acte, controleur_historique, parent=None):
        super().__init__(parent)
        self.controleur_patient = controleur_patient
        self.controleur_visite = controleur_visite
        self.controleur_consultation = controleur_consultation
        self.controleur_acte = controleur_acte
        self.controleur_historique = controleur_historique
        
        self.patient_actuel = None
        self.visite_selectionnee = None
        self.consultation_selectionnee = None
        
        self._init_ui()
        self._connect_signals()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def _init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # En-tête avec fil d'Ariane et bouton
        header = self._create_header()
        layout.addWidget(header)
        
        # Zone de contenu avec navigation dynamique
        self.stacked_widget = QStackedWidget()
        
        # Page 1 : Visites
        self.visites_widget = VisitesTableWidget(self.controleur_historique)
        self.visites_widget.visite_clicked.connect(self._on_visite_clicked)
        self.stacked_widget.addWidget(self.visites_widget)
        
        # Page 2 : Consultations
        self.consultations_widget = ConsultationsTableWidget(self.controleur_historique)
        self.consultations_widget.consultation_clicked.connect(self._on_consultation_clicked)
        self.consultations_widget.retour_clicked.connect(self._retour_visites)
        self.stacked_widget.addWidget(self.consultations_widget)
        
        # Page 3 : Actes médicaux
        self.actes_widget = ActesTableWidget(self.controleur_historique)
        self.actes_widget.voir_resultat_clicked.connect(self._on_voir_resultat)
        self.actes_widget.retour_clicked.connect(self._retour_consultations)
        self.stacked_widget.addWidget(self.actes_widget)
        
        layout.addWidget(self.stacked_widget, 1)
    
    def _create_header(self):
        """Crée l'en-tête avec fil d'Ariane et bouton nouvelle visite"""
        header = QFrame()
        header.setObjectName("HistoriqueHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)
        
        # Fil d'Ariane
        self.breadcrumb = QLabel("Sélectionnez un patient")
        self.breadcrumb.setObjectName("Breadcrumb")
        header_layout.addWidget(self.breadcrumb)
        
        header_layout.addStretch()
        
        # Bouton Nouvelle Visite
        self.btn_nouvelle_visite = QPushButton("  Nouvelle Visite")
        self.btn_nouvelle_visite.setObjectName("BtnNouvelleVisite")
        self.btn_nouvelle_visite.setIcon(qta.icon("fa5s.plus-circle", color="white"))
        self.btn_nouvelle_visite.setFixedHeight(40)
        self.btn_nouvelle_visite.setCursor(Qt.PointingHandCursor)
        self.btn_nouvelle_visite.setEnabled(False)
        header_layout.addWidget(self.btn_nouvelle_visite)
        
        return header
    
    def _connect_signals(self):
        """Connecte les signaux"""
        self.btn_nouvelle_visite.clicked.connect(self.nouvelle_visite_clicked.emit)
    
    def charger_patient(self, patient):
        """Charge l'historique d'un patient"""
        self.patient_actuel = patient
        self.visite_selectionnee = None
        self.consultation_selectionnee = None
        
        # Activer le bouton nouvelle visite
        self.btn_nouvelle_visite.setEnabled(True)
        
        # Mettre à jour le fil d'Ariane
        nom_complet = f"{patient.get_nom()} {patient.get_prenom()}"
        self.breadcrumb.setText(f"Patient : {nom_complet}")
        
        # Charger les visites
        self.visites_widget.charger_visites(patient.get_code_patient())
        
        # Afficher la page des visites
        self.stacked_widget.setCurrentIndex(0)
    
    def _on_visite_clicked(self, visite):
        """Appelé quand une visite est cliquée"""
        self.visite_selectionnee = visite
        
        # Mettre à jour le fil d'Ariane
        nom_complet = f"{self.patient_actuel.get_nom()} {self.patient_actuel.get_prenom()}"
        code_visite = visite.get('code_visite', 'N/A')
        self.breadcrumb.setText(f"Patient : {nom_complet} → Visite : {code_visite}")
        
        # Charger les consultations de cette visite
        self.consultations_widget.charger_consultations(code_visite)
        
        # Afficher la page des consultations
        self.stacked_widget.setCurrentIndex(1)
    
    def _on_consultation_clicked(self, consultation):
        """Appelé quand une consultation est cliquée"""
        self.consultation_selectionnee = consultation
        
        # Mettre à jour le fil d'Ariane
        nom_complet = f"{self.patient_actuel.get_nom()} {self.patient_actuel.get_prenom()}"
        code_visite = self.visite_selectionnee.get('code_visite', 'N/A')
        code_consultation = consultation.get('code', 'N/A')
        self.breadcrumb.setText(
            f"Patient : {nom_complet} → Visite : {code_visite} → Consultation : {code_consultation}"
        )
        
        # Charger les actes de cette consultation
        self.actes_widget.charger_actes(code_consultation)
        
        # Afficher la page des actes
        self.stacked_widget.setCurrentIndex(2)
    
    def _on_voir_resultat(self, type_acte, code_acte):
        """Appelé quand on clique sur voir résultat"""
        self.voir_resultat_clicked.emit(type_acte, code_acte)
    
    def _retour_visites(self):
        """Retour à la liste des visites"""
        self.visite_selectionnee = None
        self.consultation_selectionnee = None
        
        # Mettre à jour le fil d'Ariane
        nom_complet = f"{self.patient_actuel.get_nom()} {self.patient_actuel.get_prenom()}"
        self.breadcrumb.setText(f"Patient : {nom_complet}")
        
        # Afficher la page des visites
        self.stacked_widget.setCurrentIndex(0)
    
    def _retour_consultations(self):
        """Retour à la liste des consultations"""
        self.consultation_selectionnee = None
        
        # Mettre à jour le fil d'Ariane
        nom_complet = f"{self.patient_actuel.get_nom()} {self.patient_actuel.get_prenom()}"
        code_visite = self.visite_selectionnee.get('code_visite', 'N/A')
        self.breadcrumb.setText(f"Patient : {nom_complet} → Visite : {code_visite}")
        
        # Afficher la page des consultations
        self.stacked_widget.setCurrentIndex(1)
    
    def apply_theme(self):
        """Applique le thème"""
        c = theme_manager.colors()

        # Propager aux sous-tableaux (leurs cell-widgets ont besoin d'être recréés)
        for sub in (
            getattr(self, 'visites_widget', None),
            getattr(self, 'consultations_widget', None),
            getattr(self, 'actes_widget', None),
        ):
            if sub and hasattr(sub, 'apply_theme'):
                try:
                    sub.apply_theme()
                except Exception:
                    pass

        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_card']};
            }}
            
            QFrame#HistoriqueHeader {{
                background: {c['bg_card']};
                border: 1.5px solid {c['border_light']};
                border-radius: 12px;
            }}
            
            QLabel#Breadcrumb {{
                font-size: 14px;
                font-weight: 600;
                color: {c['text_primary']};
                background: transparent;
                border: none;
            }}
            
            QPushButton#BtnNouvelleVisite {{
                background: {c['primary']};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 20px;
            }}
            
            QPushButton#BtnNouvelleVisite:hover {{
                background: {c['primary_hover']};
            }}
            
            QPushButton#BtnNouvelleVisite:disabled {{
                background: {c['border']};
                color: {c['text_muted']};
            }}
        """)
