"""
Vue Facturation avec architecture à onglets.
Structure similaire à la vue produit avec 3 onglets.
"""
import qtawesome as qta
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QFrame, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QSize
from views.shared.theme_manager import theme_manager


class FacturationView(QWidget):
    """
    Vue principale pour la gestion de la facturation avec onglets.
    3 onglets : Statistiques Financières, Facture Patient, Facture Fournisseur
    """

    def __init__(self, facture_ctrl=None, panier_ctrl=None, parent=None):
        super().__init__(parent)
        self.facture_ctrl = facture_ctrl
        self.panier_ctrl = panier_ctrl
        self.code_session = None
        self.logger = logging.getLogger(__name__)
        
        self._init_ui()
        
        # Appliquer le thème
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _init_ui(self):
        """Initialise l'interface avec onglets"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(0)
        
        # Frame principal blanc
        main_frame = QFrame()
        main_frame.setObjectName("MainWhiteFrame")
        main_frame_layout = QVBoxLayout(main_frame)
        main_frame_layout.setContentsMargins(0, 0, 0, 0)
        main_frame_layout.setSpacing(0)
        
        # Tabs Widget (sans barre de titre)
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setIconSize(QSize(20, 20))
        self._apply_tab_styles()
        main_frame_layout.addWidget(self.tabs)
        
        # Créer les 3 onglets
        self._create_tabs()
        
        # Ajouter le frame principal
        main_layout.addWidget(main_frame)
        self._apply_main_frame_style(main_frame)

    def _setup_top_bar(self, parent_layout):
        """Barre du haut avec titre"""
        top_frame = QFrame()
        top_frame.setStyleSheet("background: transparent; border: none;")
        hbox = QHBoxLayout(top_frame)
        hbox.setContentsMargins(15, 10, 15, 10)
        hbox.setSpacing(10)
        
        # Titre
        titre = QLabel("Gestion de la Facturation")
        c = theme_manager.colors()
        titre.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {c['primary']};")
        self._titre_label = titre
        
        hbox.addWidget(titre)
        hbox.addStretch()
        
        parent_layout.addWidget(top_frame)

    def _create_tabs(self):
        """Crée les 4 onglets"""
        # Onglet 1: Statistiques Financières
        self.tab_stats = self._create_stats_tab()
        icon_stats = self._get_icon("chart-line")
        self.tabs.addTab(self.tab_stats, icon_stats, "Statistiques Financières")
        
        # Onglet 2: Comptabilité journalière
        self.tab_compta_jour = self._create_compta_journaliere_tab()
        icon_compta = self._get_icon("calendar-day")
        self.tabs.addTab(self.tab_compta_jour, icon_compta, "Comptabilité journalière")
        
        # Onglet 3: Facture Patient
        self.tab_facture_patient = self._create_facture_patient_tab()
        icon_patient = self._get_icon("user-injured")
        self.tabs.addTab(self.tab_facture_patient, icon_patient, "Facture Patient")
        
        # Onglet 4: Facture Fournisseur
        self.tab_facture_fournisseur = self._create_facture_fournisseur_tab()
        icon_fournisseur = self._get_icon("truck")
        self.tabs.addTab(self.tab_facture_fournisseur, icon_fournisseur, "Facture Fournisseur")

    def _create_stats_tab(self):
        """Onglet Statistiques Financières"""
        from .statistiques_financieres_widget import StatistiquesFinancieresWidget
        
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Widget de statistiques financières
        self.stats_widget = StatistiquesFinancieresWidget()
        layout.addWidget(self.stats_widget)
        
        return tab
    
    def _create_compta_journaliere_tab(self):
        """Onglet Comptabilité journalière"""
        from .comptabilite_journaliere_widget import ComptabiliteJournaliereWidget
        
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Widget de comptabilité journalière
        self.compta_jour_widget = ComptabiliteJournaliereWidget()
        layout.addWidget(self.compta_jour_widget)
        
        return tab

    def _create_facture_patient_tab(self):
        """Onglet Facture Patient - Interface existante"""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Importer et utiliser le widget existant
        from .patient.panier.facture_patient_widget import FacturePatientWidget
        
        self.facture_patient_widget = FacturePatientWidget(
            facture_ctrl=self.facture_ctrl,
            panier_ctrl=self.panier_ctrl
        )
        layout.addWidget(self.facture_patient_widget)
        
        return tab

    def _create_facture_fournisseur_tab(self):
        """Onglet Facture Fournisseur avec widget de paiement"""
        from .fournisseur.facture_fournisseur_payment_widget import FactureFournisseurPaymentWidget
        from controllers.controleur_fournisseur import FournisseurControleur
        from controllers.controleur_factureFournisseur import FactureFournisseurControleur
        
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Widget de paiement
        fournisseur_ctrl = FournisseurControleur()
        facture_four_ctrl = FactureFournisseurControleur()
        self.payment_widget = FactureFournisseurPaymentWidget(
            facture_ctrl=facture_four_ctrl,
            fournisseur_ctrl=fournisseur_ctrl
        )
        
        # Connecter le signal de paiement validé
        self.payment_widget.paiement_valide.connect(self._on_paiement_valide)
        
        layout.addWidget(self.payment_widget)
        
        return tab
    
    def _on_paiement_valide(self, code_facture_four: str):
        """Callback quand un paiement est validé"""
        self.logger.info(f"Paiement validé pour facture {code_facture_four}")
        # Retourner à l'onglet statistiques ou actualiser les données
        self.tabs.setCurrentIndex(0)
    
    def charger_facture_pour_paiement(self, code_facture_four: str):
        """Charge une facture dans l'onglet paiement et active l'onglet"""
        if hasattr(self, 'payment_widget'):
            self.payment_widget.charger_facture(code_facture_four)
            # Activer l'onglet Facture Fournisseur (index 2)
            self.tabs.setCurrentIndex(2)

    def _get_icon(self, icon_name):
        """Récupère une icône Font Awesome"""
        try:
            icon_map = {
                "chart-line": "fa5s.chart-line",
                "calendar-day": "fa5s.calendar-day",
                "user-injured": "fa5s.user-injured",
                "truck": "fa5s.truck"
            }
            return qta.icon(icon_map.get(icon_name, "fa5s.circle"), color=theme_manager.colors()['primary'])
        except:
            from PySide6.QtWidgets import QStyle
            return self.style().standardIcon(QStyle.SP_FileIcon)

    def _apply_main_frame_style(self, frame):
        """Applique le style au frame principal"""
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame#MainWhiteFrame {{
                background: white;
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
        """)

    def _apply_tab_styles(self):
        """Applique les styles aux onglets"""
        c = theme_manager.colors()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: white;
                border-radius: 12px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {c['text_secondary']};
                padding: 10px 20px;
                margin-right: 4px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 13px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                color: {c['primary']};
                border-bottom: 2px solid {c['primary']};
                font-weight: 600;
            }}
            QTabBar::tab:hover {{
                color: {c['primary']};
                background: {c['hover']};
            }}
        """)

    def apply_theme(self):
        """Applique le thème actif"""
        c = theme_manager.colors()
        self.setStyleSheet(f"background-color: {c['bg_main']};")
        
        if hasattr(self, 'tabs'):
            self._apply_tab_styles()
            main_frame = self.findChild(QFrame, "MainWhiteFrame")
            if main_frame:
                self._apply_main_frame_style(main_frame)

    # =========================================================================
    # API PUBLIQUE
    # =========================================================================

    def charger_donnees(self, code_session: str) -> None:
        """Charge les données pour la session"""
        if code_session:
            self.code_session = code_session
        
        # Charger les données de l'onglet facture patient
        if hasattr(self, 'facture_patient_widget'):
            self.facture_patient_widget.charger_donnees(code_session)
        
        # Charger les statistiques financières
        if hasattr(self, 'stats_widget'):
            self.stats_widget.charger_donnees(code_session)
        
        # Charger la comptabilité journalière
        if hasattr(self, 'compta_jour_widget'):
            self.compta_jour_widget.charger_donnees(code_session)
        
        # Charger la comptabilité journalière
        if hasattr(self, 'compta_jour_widget'):
            self.compta_jour_widget.charger_donnees(code_session)
