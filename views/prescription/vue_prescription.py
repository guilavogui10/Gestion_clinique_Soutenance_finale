"""
Vue Prescription - interface principale de gestion des prescriptions.
Architecture à onglets pour une interface moins chargée
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea,
                                QTabWidget, QFrame)
from PySide6.QtCore import Qt, QSize
from views.shared.theme_manager import theme_manager
from .components import (
    KpiCardsSection,
    PrescriptionsTable,
    PatientsAttentePrescriptionView
)
from .panier_prescription.prescription_widget import PrescriptionWidget
from .styles import PrescriptionStyles
import qtawesome as qta


class PrescriptionView(QWidget):
    """Vue principale prescription."""
    
    def __init__(self, controleur, permission_ctrl=None, user_info=None, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.permission_ctrl = permission_ctrl
        self.user_info = user_info or {}
        self.code_session = None
        
        # Créer le helper de permissions si disponible
        self.permission_helper = None
        if self.permission_ctrl and self.user_info:
            from views.shared.permission_helper import PermissionHelper
            self.permission_helper = PermissionHelper(self, self.permission_ctrl, self.user_info)
        
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(0)
        
        # Frame principal blanc qui contient tout
        main_frame = QFrame()
        main_frame.setObjectName("MainWhiteFrame")
        main_frame_layout = QVBoxLayout(main_frame)
        main_frame_layout.setContentsMargins(0, 0, 0, 0)
        main_frame_layout.setSpacing(0)
        
        # Tabs Widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setIconSize(QSize(20, 20))
        self._apply_tab_styles()
        main_frame_layout.addWidget(self.tabs)
        
        # Onglet 1: Statistiques + Liste
        self.tab_stats = self._create_stats_tab()
        icon_stats = self._get_icon("chart-line")
        self.tabs.addTab(self.tab_stats, icon_stats, "Statistiques")
        
        # Onglet 2: Panier Prescription
        self.tab_panier = self._create_panier_tab()
        icon_panier = self._get_icon("prescription")
        self.tabs.addTab(self.tab_panier, icon_panier, "Panier Prescription")
        
        # Onglet 3: Patients en attente
        self.tab_attente = self._create_attente_tab()
        icon_attente = self._get_icon("clock")
        self.tabs.addTab(self.tab_attente, icon_attente, "Patients en attente")
        
        # Ajouter le frame principal au layout
        main_layout.addWidget(main_frame)
        
        # Appliquer le style au frame principal
        self._apply_main_frame_style(main_frame)
    
    def charger_donnees(self, code_session):
        self.code_session = code_session
        
        # Mettre à jour les sous-vues
        if hasattr(self, 'patients_attente_view'):
            self.patients_attente_view.code_session = code_session
        
        if hasattr(self, 'prescription_widget'):
            self.prescription_widget.charger_donnees(code_session)
        
        self.charger_donnees_stats()
    
    def charger_donnees_stats(self):
        if not self.code_session or not self.ctrl:
            return
        
        # Rafraîchir les KPI cards
        self.kpi_cards.rafraichir(self.code_session)
        
        # Rafraîchir le tableau
        prescriptions = self.ctrl.lister_groupes_par_acte(self.code_session)
        self.table.load_prescriptions(prescriptions)
        
        # Rafraîchir la vue des patients en attente
        if hasattr(self, 'patients_attente_view'):
            self.patients_attente_view.charger_patients()
    
    def on_new_prescription(self):
        """Créer une nouvelle prescription - Vérification des permissions"""
        if not self.permission_helper:
            self.tabs.setCurrentIndex(1)
            return
        
        if not self.permission_helper.peut_creer():
            def executer_creation():
                self.tabs.setCurrentIndex(1)
            
            self.permission_helper.verifier_et_executer(
                action=self.permission_ctrl.ACTION_MODIFICATION,
                contexte="Création d'une nouvelle prescription",
                callback_success=executer_creation
            )
        else:
            self.tabs.setCurrentIndex(1)
    
    def _ouvrir_panier_avec_acte(self, code_acte: str):
        """Ouvre l'onglet panier avec un acte médical pré-sélectionné"""
        self.tabs.setCurrentIndex(1)
        if hasattr(self, 'prescription_widget'):
            widget = self.prescription_widget
            # S'assurer que le combo est chargé avec la session courante
            if self.code_session and hasattr(widget, 'charger_donnees'):
                widget.charger_donnees(self.code_session)
            if hasattr(widget, 'selectionner_acte'):
                widget.selectionner_acte(code_acte)
            elif hasattr(widget, 'charger_patient'):
                widget.charger_patient({'code_acte': code_acte})
    
    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_main']};
            }}
        """)
        self._apply_tab_styles()
        if hasattr(self, 'tabs'):
            main_frame = self.findChild(QFrame, "MainWhiteFrame")
            if main_frame:
                self._apply_main_frame_style(main_frame)
    
    def _get_icon(self, icon_name):
        """Récupère une icône Font Awesome ou standard"""
        try:
            icon_map = {
                "chart-line": "fa5s.chart-line",
                "prescription": "fa5s.prescription",
                "clock": "fa5s.hourglass-half"
            }
            return qta.icon(icon_map.get(icon_name, "fa5s.circle"), color=theme_manager.colors()['primary'])
        except:
            from PySide6.QtWidgets import QStyle
            style_map = {
                "chart-line": QStyle.SP_FileDialogDetailedView,
                "prescription": QStyle.SP_FileDialogListView,
                "clock": QStyle.SP_BrowserReload
            }
            return self.style().standardIcon(style_map.get(icon_name, QStyle.SP_FileIcon))
    
    def _create_stats_tab(self):
        """Crée l'onglet Statistiques + Liste"""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)
        
        # KPI Cards
        self.kpi_cards = KpiCardsSection(self.ctrl)
        layout.addWidget(self.kpi_cards)
        
        # Tableau des prescriptions
        self.table = PrescriptionsTable(self.ctrl)
        self.table.new_clicked.connect(self.on_new_prescription)
        layout.addWidget(self.table, 1)
        
        return tab
    
    def _create_panier_tab(self):
        """Crée l'onglet Panier Prescription optimisé : formulaire à gauche + panier à droite"""
        from PySide6.QtWidgets import QHBoxLayout
        from views.prescription.panier_prescription.prescription_widget_optimized import PrescriptionWidgetOptimized
        from views.prescription.panier_prescription.components.panier_widget import PanierPrescriptionWidget
        
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Formulaire à gauche (stretch 3) - optimisé sans scroll
        self.prescription_widget = PrescriptionWidgetOptimized(
            prescription_ctrl=self.ctrl
        )
        self.prescription_widget.prescription_validee.connect(self._on_prescription_validee)
        
        # Panier à droite (stretch 2) - tableau avec total
        self.panier_widget = PanierPrescriptionWidget(
            prescription_ctrl=self.ctrl
        )
        
        # Connecter les signaux
        self.prescription_widget.ligne_ajoutee.connect(self._on_ligne_ajoutee_panier)
        self.prescription_widget.ligne_supprimee.connect(self._on_ligne_supprimee_panier)
        self.prescription_widget.panier_reinitialise.connect(self._on_panier_reinitialise)
        self.panier_widget.ligne_supprimee_signal.connect(self._supprimer_ligne_panier)
        
        layout.addWidget(self.prescription_widget, 3)
        layout.addWidget(self.panier_widget, 2)
        
        return tab
    
    def _on_ligne_ajoutee_panier(self, form_data: dict):
        """Appelé quand une ligne est ajoutée au panier"""
        self.panier_widget.ajouter_ligne(form_data)
        # Recalculer le total
        if hasattr(self.prescription_widget, 'code_acte') and self.prescription_widget.code_acte:
            total = self.ctrl.obtenir_montant_total_acte(self.prescription_widget.code_acte)
            self.panier_widget.update_total(total)
    
    def _on_ligne_supprimee_panier(self):
        """Appelé quand une ligne est supprimée du panier"""
        # Recharger toutes les lignes depuis le contrôleur
        if hasattr(self.prescription_widget, 'code_acte') and self.prescription_widget.code_acte:
            lignes = self.ctrl.lister_par_acte(self.prescription_widget.code_acte)
            self.panier_widget.recharger_lignes(lignes)
            total = self.ctrl.obtenir_montant_total_acte(self.prescription_widget.code_acte)
            self.panier_widget.update_total(total)
    
    def _on_panier_reinitialise(self):
        """Appelé quand le panier est réinitialisé"""
        self.panier_widget.vider_panier()
    
    def _supprimer_ligne_panier(self, code_prescription: str):
        """Supprime une ligne du panier"""
        # Déléguer au widget prescription
        if hasattr(self.prescription_widget, 'operations'):
            ok, msg = self.prescription_widget.operations.supprimer_ligne_prescription(
                code_prescription, self.prescription_widget
            )
            if ok:
                self._on_ligne_supprimee_panier()
    
    def _on_prescription_validee(self):
        """Appelé quand une prescription est validée"""
        self.charger_donnees_stats()
        # Revenir à l'onglet Statistiques
        self.tabs.setCurrentIndex(0)
    
    def _create_attente_tab(self):
        """Crée l'onglet Patients en attente"""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(0)
        
        # Vue des patients en attente
        self.patients_attente_view = PatientsAttentePrescriptionView(
            self.ctrl, 
            self.code_session if hasattr(self, 'code_session') and self.code_session else "",
            parent=tab
        )
        self.patients_attente_view.ouvrir_formulaire.connect(self._ouvrir_panier_avec_acte)
        layout.addWidget(self.patients_attente_view)
        
        return tab
    
    def _apply_main_frame_style(self, frame):
        """Applique le style au frame principal blanc"""
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
        self.tabs.setStyleSheet(PrescriptionStyles.tab_widget())
