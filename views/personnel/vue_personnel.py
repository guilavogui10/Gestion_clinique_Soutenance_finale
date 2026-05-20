"""
Vue Personnel - interface principale de gestion du personnel.
Architecture à onglets pour une interface moins chargée (identique à consultation/fournisseur)
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                                QTabWidget, QFrame, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox
from .components import (
    KpiCardsSection,
    PersonnelTable,
    QuickActions,
    ChartsSection
)


class VuePersonnel(QWidget):
    """Vue principale personnel."""
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
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
        
        # Onglet 3: Liste du personnel
        self.tab_liste = self._create_liste_tab()
        icon_liste = self._get_icon("list")
        self.tabs.addTab(self.tab_liste, icon_liste, "Liste du personnel")
        
        # Onglet 4: Cartes membres
        self.tab_cartes = self._create_cartes_tab()
        icon_cartes = self._get_icon("id-card")
        self.tabs.addTab(self.tab_cartes, icon_cartes, "Cartes membres")
        
        # Quick Actions (toujours visible en bas)
        self.quick_actions = QuickActions()
        self.quick_actions.new_personnel_clicked.connect(self.on_new_personnel)
        self.quick_actions.export_clicked.connect(self.on_export)
        self.quick_actions.import_clicked.connect(self.on_import)
        self.quick_actions.pdf_clicked.connect(self.on_pdf)
        self.quick_actions.reports_clicked.connect(self.on_reports)
        self.quick_actions.search_clicked.connect(self.on_search)
        main_frame_layout.addWidget(self.quick_actions)
        
        # Ajouter le frame principal au layout
        main_layout.addWidget(main_frame)
        
        # Appliquer le style au frame principal
        self._apply_main_frame_style(main_frame)
    
    def charger_personnels(self, _code_session: str = None):
        self.charger_donnees()
    
    def charger_donnees(self):
        # Rafraîchir les statistiques
        if hasattr(self, 'stats_widget'):
            self.stats_widget.charger_donnees()
        
        # Rafraîchir la table
        self.table.load_personnel()
        
        # Rafraîchir la vue cartes
        if hasattr(self, 'cartes_view'):
            self.cartes_view.charger_personnel()
    
    def on_view_personnel(self, personnel):
        from .detail_personnel_modal import DetailsPersonnelModal
        dialog = DetailsPersonnelModal(self, personnel, self.ctrl)
        dialog.exec()
    
    def on_edit_personnel(self, personnel):
        # Passer à l'onglet Nouveau et pré-remplir
        self.tabs.setCurrentIndex(1)
        if hasattr(self, 'form_widget'):
            self.form_widget.personnel_obj = personnel
            self.form_widget._remplir_champs()
    
    def on_delete_personnel(self, personnel):
        mail = personnel.get("mail", "")
        if not mail:
            self.show_message(False, "Email introuvable.")
            return

        rep = QMessageBox.question(
            self,
            "Confirmation",
            f"Supprimer le personnel {mail} ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep == QMessageBox.Yes:
            ok, msg = self.ctrl.delete_personnel(mail)
            self.show_message(ok, msg)
            if ok:
                self.charger_donnees()
    
    def on_card_personnel(self, personnel):
        # Passer à l'onglet Cartes et afficher ce personnel
        self.tabs.setCurrentIndex(3)
        if hasattr(self, 'cartes_view'):
            # Trouver l'index du personnel dans le combo
            for i in range(self.cartes_view.combo_personnel.count()):
                data = self.cartes_view.combo_personnel.itemData(i)
                if data and data.get("code") == personnel.get("code"):
                    self.cartes_view.combo_personnel.setCurrentIndex(i)
                    break
    
    def on_new_personnel(self):
        self.tabs.setCurrentIndex(1)
    
    def on_export(self):
        chemin, _ = QFileDialog.getSaveFileName(
            self, "Exporter personnel", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not chemin:
            return
        if chemin.lower().endswith(".csv"):
            ok, msg = self.ctrl.export_to_csv(chemin)
        else:
            if not chemin.lower().endswith(".xlsx"):
                chemin = chemin + ".xlsx"
            ok, msg = self.ctrl.export_to_excel(chemin)
        self.show_message(ok, msg)
    
    def on_import(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Importer personnel", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not chemin:
            return
        if chemin.lower().endswith(".csv"):
            ok, msg = self.ctrl.import_from_csv(chemin)
        else:
            ok, msg = self.ctrl.import_from_excel(chemin)
        self.show_message(ok, msg)
        if ok:
            self.charger_donnees()
    
    def on_pdf(self):
        chemin, _ = QFileDialog.getSaveFileName(
            self, "Exporter la liste du personnel", "", "PDF Files (*.pdf)"
        )
        if not chemin:
            return
        ok, msg = self.ctrl.generer_liste_pdf(chemin)
        self.show_message(ok, msg)
    
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
                "id-card": "fa5s.id-card",
                "plus": "fa5s.plus-circle"
            }
            return qta.icon(icon_map.get(icon_name, "fa5s.circle"), color=theme_manager.colors()['primary'])
        except:
            from PySide6.QtWidgets import QStyle
            style_map = {
                "chart-line": QStyle.SP_FileDialogDetailedView,
                "list": QStyle.SP_FileDialogListView,
                "id-card": QStyle.SP_DirIcon
            }
            return self.style().standardIcon(style_map.get(icon_name, QStyle.SP_FileIcon))
    
    def _create_nouveau_tab(self):
        """Crée l'onglet Nouveau avec le formulaire de personnel"""
        from .personnel_form_widget import PersonnelFormWidget
        
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
        self.form_widget = PersonnelFormWidget(self.ctrl)
        self.form_widget.personnel_saved.connect(self._on_personnel_saved)
        scroll.setWidget(self.form_widget)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _on_personnel_saved(self):
        """Appelé quand un personnel est enregistré"""
        self.charger_donnees()
        # Revenir à l'onglet Liste
        self.tabs.setCurrentIndex(2)
    
    def _create_stats_tab(self):
        """Crée l'onglet Statistiques"""
        from .statistiques_personnel_widget import StatistiquesPersonnelWidget
        
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Widget de statistiques
        self.stats_widget = StatistiquesPersonnelWidget(self.ctrl)
        layout.addWidget(self.stats_widget)
        
        return tab
    
    def _create_liste_tab(self):
        """Crée l'onglet Liste du personnel"""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        
        self.table = PersonnelTable(self.ctrl)
        self.table.view_clicked.connect(self.on_view_personnel)
        self.table.edit_clicked.connect(self.on_edit_personnel)
        self.table.delete_clicked.connect(self.on_delete_personnel)
        self.table.card_clicked.connect(self.on_card_personnel)
        self.table.new_clicked.connect(self.on_new_personnel)
        layout.addWidget(self.table)
        
        return tab
    
    def _create_cartes_tab(self):
        """Crée l'onglet Cartes membres"""
        from .cartes_personnel_view import CartesPersonnelView
        
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.cartes_view = CartesPersonnelView(self.ctrl, parent=tab)
        layout.addWidget(self.cartes_view)
        
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
        from .styles import PersonnelStyles
        self.tabs.setStyleSheet(PersonnelStyles.tab_widget())
    
    def show_message(self, reussite, message):
        titre = "Succès" if reussite else "Information / Erreur"
        dialog = CustomMessageBox(titre, message, is_success=reussite, parent=self)
        dialog.exec()
