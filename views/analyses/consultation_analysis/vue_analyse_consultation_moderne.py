"""
Vue Analyse Consultation Moderne - Interface d'analyse complète
Conforme à la nouvelle logique avec acte_medical
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
from PySide6.QtCore import Qt
from views.shared.theme_manager import theme_manager
from .components import (
    KpiCardsAnalyse,
    ChartsAnalyseSection,
    ConsultationsTableAnalyse,
    SidebarStatsAnalyse,
    QuickActionsAnalyse
)


class VueAnalyseConsultationModerne(QWidget):
    """Vue principale d'analyse consultation moderne"""
    
    def __init__(self, controleur, code_session, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.code_session = code_session
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
        self.charger_donnees()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setObjectName("MainScrollArea")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(25)
        
        # KPI Cards (6 cartes)
        self.kpi_cards = KpiCardsAnalyse(self.ctrl)
        content_layout.addWidget(self.kpi_cards)
        
        # Charts Section (3 graphiques)
        self.charts_section = ChartsAnalyseSection(self.ctrl)
        content_layout.addWidget(self.charts_section)
        
        # Section principale : Table + Sidebar
        main_section = QHBoxLayout()
        main_section.setSpacing(20)
        
        # Table (70%)
        self.table = ConsultationsTableAnalyse(self.ctrl)
        self.table.view_clicked.connect(self.on_view_consultation)
        self.table.edit_clicked.connect(self.on_edit_consultation)
        main_section.addWidget(self.table, 7)
        
        # Sidebar (30%)
        self.sidebar = SidebarStatsAnalyse()
        main_section.addWidget(self.sidebar, 3)
        
        content_layout.addLayout(main_section)
        
        # Quick Actions
        self.quick_actions = QuickActionsAnalyse()
        self.quick_actions.new_consultation_clicked.connect(self.on_new_consultation)
        self.quick_actions.patients_waiting_clicked.connect(self.on_patients_waiting)
        self.quick_actions.by_services_clicked.connect(self.on_by_services)
        self.quick_actions.advanced_search_clicked.connect(self.on_advanced_search)
        self.quick_actions.reports_clicked.connect(self.on_reports)
        self.quick_actions.patient_history_clicked.connect(self.on_patient_history)
        content_layout.addWidget(self.quick_actions)
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
    
    def charger_donnees(self):
        """Charge les données initiales"""
        if not self.code_session:
            return
        
        # Charger KPI
        self.kpi_cards.rafraichir(self.code_session)
        
        # Charger graphiques
        self.charts_section.rafraichir(self.code_session)
        
        # Charger consultations
        consultations = self.ctrl.lister_consultations_session(self.code_session)
        self.table.load_consultations(consultations)
    
    def rafraichir(self):
        """Rafraîchit toutes les données"""
        self.charger_donnees()
    
    def on_view_consultation(self, consultation):
        """Voir détails consultation"""
        print(f"Voir consultation: {consultation.code}")
    
    def on_edit_consultation(self, consultation):
        """Éditer consultation"""
        print(f"Éditer consultation: {consultation.code}")
    
    def on_new_consultation(self):
        """Nouvelle consultation"""
        print("Nouvelle consultation")
    
    def on_patients_waiting(self):
        """Patients en attente"""
        print("Patients en attente")
    
    def on_by_services(self):
        """Par services"""
        print("Par services")
    
    def on_advanced_search(self):
        """Recherche avancée"""
        print("Recherche avancée")
    
    def on_reports(self):
        """Rapports & exports"""
        print("Rapports & exports")
    
    def on_patient_history(self):
        """Historique patient"""
        print("Historique patient")
    
    def apply_theme(self):
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_main']};
            }}
            QScrollArea#MainScrollArea {{
                border: none;
                background: {c['bg_main']};
            }}
        """)
