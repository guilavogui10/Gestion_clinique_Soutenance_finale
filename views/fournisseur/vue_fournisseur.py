"""
Vue Fournisseur - interface principale de gestion des fournisseurs.
Architecture à onglets pour une interface moins chargée (identique à consultation)
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                                QTabWidget, QFrame, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox
from .components import (
    KpiCardsSection,
    FournisseursTable,
    QuickActions,
    ChartsSection
)


class VueFournisseur(QWidget):
    """Vue principale fournisseur."""
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.code_session = None
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
        
        # Onglet 1: Statistiques
        self.tab_stats = self._create_stats_tab()
        icon_stats = self._get_icon("chart-line")
        self.tabs.addTab(self.tab_stats, icon_stats, "Statistiques")
        
        # Onglet 2: Nouveau
        self.tab_nouveau = self._create_nouveau_tab()
        icon_nouveau = self._get_icon("plus")
        self.tabs.addTab(self.tab_nouveau, icon_nouveau, "Nouveau")
        
        # Onglet 3: Liste des fournisseurs
        self.tab_liste = self._create_liste_tab()
        icon_liste = self._get_icon("list")
        self.tabs.addTab(self.tab_liste, icon_liste, "Liste des fournisseurs")
        
        # Onglet 4: Activités
        self.tab_activites = self._create_activites_tab()
        icon_activites = self._get_icon("briefcase")
        self.tabs.addTab(self.tab_activites, icon_activites, "Activités")
        
        # Quick Actions (toujours visible en bas)
        self.quick_actions = QuickActions()
        self.quick_actions.new_fournisseur_clicked.connect(self.on_new_fournisseur)
        self.quick_actions.export_clicked.connect(self.on_export)
        self.quick_actions.import_clicked.connect(self.on_import)
        self.quick_actions.notifications_clicked.connect(self.on_notifications)
        self.quick_actions.reports_clicked.connect(self.on_reports)
        self.quick_actions.search_clicked.connect(self.on_search)
        main_frame_layout.addWidget(self.quick_actions)
        
        # Ajouter le frame principal au layout
        main_layout.addWidget(main_frame)
        
        # Appliquer le style au frame principal
        self._apply_main_frame_style(main_frame)
    
    def charger_fournisseurs(self, code_session):
        self.code_session = code_session
        self.charger_donnees()
    
    def charger_donnees(self):
        if not self.code_session:
            return
        
        # Rafraîchir les KPI
        self.kpi_cards.rafraichir(self.code_session)
        
        # Rafraîchir les graphiques
        if hasattr(self, 'charts'):
            self.charts.update_data(self.code_session)
        
        # Rafraîchir la table
        self.table.load_fournisseurs(self.code_session)
        
        # Rafraîchir la vue activités
        if hasattr(self, 'activites_view'):
            self.activites_view.charger_fournisseurs()
    
    def on_view_fournisseur(self, fournisseur):
        from .detail_fournisseur_modal import DetailsFournisseurModal
        dialog = DetailsFournisseurModal(self, fournisseur, self.ctrl)
        dialog.exec()
    
    def on_edit_fournisseur(self, fournisseur):
        # Passer à l'onglet Nouveau et pré-remplir
        self.tabs.setCurrentIndex(1)
        if hasattr(self, 'form_widget'):
            self.form_widget.fournisseur_obj = fournisseur
            self.form_widget._remplir_champs()
    
    def on_delete_fournisseur(self, fournisseur):
        mail = fournisseur.get("email_fournisseur", "")
        if not mail:
            self.show_message(False, "Email introuvable.")
            return

        rep = QMessageBox.question(
            self,
            "Confirmation",
            f"Supprimer le fournisseur {mail} ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep == QMessageBox.Yes:
            ok, msg = self.ctrl.delete_fournisseur(mail)
            self.show_message(ok, msg)
            if ok:
                self.charger_donnees()
    
    def on_work_fournisseur(self, fournisseur):
        # Passer à l'onglet Activités et afficher ce fournisseur
        self.tabs.setCurrentIndex(3)
        if hasattr(self, 'activites_view'):
            # Trouver l'index du fournisseur dans le combo
            for i in range(self.activites_view.combo_fournisseur.count()):
                data = self.activites_view.combo_fournisseur.itemData(i)
                if data and data.get("email_fournisseur") == fournisseur.get("email_fournisseur"):
                    self.activites_view.combo_fournisseur.setCurrentIndex(i)
                    break
    
    def on_new_fournisseur(self):
        self.tabs.setCurrentIndex(1)
    
    def on_export(self):
        chemin, _ = QFileDialog.getSaveFileName(
            self, "Exporter fournisseurs", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not chemin:
            return
        if chemin.lower().endswith(".csv"):
            ok, msg = self.ctrl.exporter_fournisseurs_to_csv(chemin)
        else:
            if not chemin.lower().endswith(".xlsx"):
                chemin = chemin + ".xlsx"
            ok, msg = self.ctrl.exporter_fournisseurs_to_excel(chemin)
        self.show_message(ok, msg)
    
    def on_import(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Importer fournisseurs", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not chemin:
            return
        if chemin.lower().endswith(".csv"):
            ok, msg = self.ctrl.importer_fournisseurs_from_csv(chemin)
        else:
            ok, msg = self.ctrl.importer_fournisseurs_from_excel(chemin)
        self.show_message(ok, msg)
        if ok:
            self.charger_donnees()
    
    def on_notifications(self):
        print("Notifications")
    
    def on_reports(self):
        print("Rapports & exports")
    
    def on_search(self):
        print("Recherche avancée")
    
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
            import qtawesome as qta
            icon_map = {
                "chart-line": "fa5s.chart-line",
                "list": "fa5s.list",
                "briefcase": "fa5s.briefcase",
                "plus": "fa5s.plus-circle"
            }
            return qta.icon(icon_map.get(icon_name, "fa5s.circle"), color=theme_manager.colors()['primary'])
        except:
            from PySide6.QtWidgets import QStyle
            style_map = {
                "chart-line": QStyle.SP_FileDialogDetailedView,
                "list": QStyle.SP_FileDialogListView,
                "briefcase": QStyle.SP_DirIcon
            }
            return self.style().standardIcon(style_map.get(icon_name, QStyle.SP_FileIcon))
    
    def _create_nouveau_tab(self):
        """Crée l'onglet Nouveau avec le formulaire de fournisseur"""
        from .fournisseur_form_widget import FournisseurFormWidget
        
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area pour le formulaire
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Widget formulaire
        self.form_widget = FournisseurFormWidget(self.ctrl)
        self.form_widget.fournisseur_saved.connect(self._on_fournisseur_saved)
        scroll.setWidget(self.form_widget)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _on_fournisseur_saved(self):
        """Appelé quand un fournisseur est enregistré"""
        self.charger_donnees()
        # Revenir à l'onglet Liste
        self.tabs.setCurrentIndex(2)
    
    def _create_stats_tab(self):
        """Crée l'onglet Statistiques"""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)
        
        # KPI Cards directement dans le layout
        self.kpi_cards = KpiCardsSection(self.ctrl)
        layout.addWidget(self.kpi_cards)
        
        # Charts Section - 3 graphiques
        self.charts = ChartsSection(self.ctrl)
        layout.addWidget(self.charts, 1)
        
        return tab
    
    def _create_liste_tab(self):
        """Crée l'onglet Liste des fournisseurs"""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        
        self.table = FournisseursTable(self.ctrl)
        self.table.view_clicked.connect(self.on_view_fournisseur)
        self.table.edit_clicked.connect(self.on_edit_fournisseur)
        self.table.delete_clicked.connect(self.on_delete_fournisseur)
        self.table.work_clicked.connect(self.on_work_fournisseur)
        self.table.new_clicked.connect(self.on_new_fournisseur)
        layout.addWidget(self.table)
        
        return tab
    
    def _create_activites_tab(self):
        """Crée l'onglet Activités"""
        from .activites_fournisseur_view import ActivitesFournisseurView
        
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.activites_view = ActivitesFournisseurView(
            self.ctrl,
            self.code_session if hasattr(self, 'code_session') and self.code_session else "",
            parent=tab
        )
        layout.addWidget(self.activites_view)
        
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
        from .styles import FournisseurStyles
        self.tabs.setStyleSheet(FournisseurStyles.tab_widget())
    
    def show_message(self, reussite, message):
        titre = "Succès" if reussite else "Information / Erreur"
        dialog = CustomMessageBox(titre, message, is_success=reussite, parent=self)
        dialog.exec()
