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
        """Menu export — même pattern que examen/chirurgie."""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QCursor
        from PySide6.QtCore import QPoint
        import qtawesome as qta
        c = theme_manager.colors()

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 6px 4px;
            }}
            QMenu::item {{
                padding: 9px 20px 9px 12px;
                border-radius: 6px;
                font-size: 13px;
                color: {c['text_primary']};
                min-width: 220px;
            }}
            QMenu::item:selected {{
                background: {c.get('primary_light', c['hover'])};
                color: {c['primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {c['border']};
                margin: 4px 10px;
            }}
        """)
        act_xl = menu.addAction(qta.icon("fa5s.file-excel", color=c['success']), "  Exporter Excel (.xlsx)")
        act_cs = menu.addAction(qta.icon("fa5s.file-csv",   color=c['info']),    "  Exporter CSV (.csv)")
        menu.addSeparator()
        act_print = menu.addAction(qta.icon("fa5s.print", color=c['danger']), "  Imprimer Tout")

        act_xl.triggered.connect(lambda: self._apercu_export("excel"))
        act_cs.triggered.connect(lambda: self._apercu_export("csv"))
        act_print.triggered.connect(self._print_all)

        menu.adjustSize()
        pos = QCursor.pos()
        menu.exec(QPoint(pos.x(), pos.y() - menu.sizeHint().height() - 6))

    def _print_all(self):
        """Génère et affiche l'aperçu PDF de tous les fournisseurs."""
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from views.shared.message_box import CustomMessageBox
        try:
            pdf_path = self.ctrl.generer_rapport_fournisseurs()
            ApercuPDFDialog(pdf_path, "Rapport — Liste des fournisseurs", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Impossible de générer le rapport :\n{e}",
                             msg_type="error", parent=self).exec()

    def on_import(self):
        """Menu import — même pattern que examen/chirurgie."""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QCursor
        from PySide6.QtCore import QPoint
        import qtawesome as qta
        c = theme_manager.colors()

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 6px 4px;
            }}
            QMenu::item {{
                padding: 9px 20px 9px 12px;
                border-radius: 6px;
                font-size: 13px;
                color: {c['text_primary']};
                min-width: 220px;
            }}
            QMenu::item:selected {{
                background: {c.get('primary_light', c['hover'])};
                color: {c['primary']};
            }}
        """)
        act_xl = menu.addAction(qta.icon("fa5s.upload", color=c['success']), "  Depuis Excel (.xlsx)")
        act_cs = menu.addAction(qta.icon("fa5s.upload", color=c['info']),    "  Depuis CSV (.csv)")

        act_xl.triggered.connect(lambda: self._apercu_import("excel"))
        act_cs.triggered.connect(lambda: self._apercu_import("csv"))

        menu.adjustSize()
        pos = QCursor.pos()
        menu.exec(QPoint(pos.x(), pos.y() - menu.sizeHint().height() - 6))

    def _apercu_export(self, format_fichier: str):
        """Export fournisseurs avec aperçu avant enregistrement (ApercuActeModal)."""
        from views.acte_medical.export_import_acte import ApercuActeModal
        from views.shared.message_box import CustomMessageBox

        donnees_dicts = self.ctrl.obtenir_donnees_export()
        if not donnees_dicts:
            CustomMessageBox("Export Fournisseurs", "Aucun fournisseur à exporter.",
                             msg_type="info", parent=self).exec()
            return

        colonnes = ['email_fournisseur', 'nom_entreprise', 'telephone', 'adresse']
        donnees  = [[str(d.get(col, "")) for col in colonnes] for d in donnees_dicts]
        ext      = "xlsx" if format_fichier == "excel" else "csv"

        modal = ApercuActeModal(
            self,
            f"Aperçu export {ext.upper()} — Fournisseurs",
            f"{len(donnees)} fournisseur(s) prêt(s) à exporter",
            colonnes, donnees, mode="export"
        )
        if not (modal.exec() and modal._confirme):
            return

        filtre = "Excel Files (*.xlsx)" if format_fichier == "excel" else "CSV Files (*.csv)"
        chemin, _ = QFileDialog.getSaveFileName(
            self, f"Enregistrer — {ext.upper()}", f"fournisseurs_export.{ext}", filtre
        )
        if not chemin:
            return

        ok, msg = self.ctrl.export_to_excel(chemin) \
                  if format_fichier == "excel" \
                  else self.ctrl.export_to_csv(chemin)
        CustomMessageBox(
            "Export réussi" if ok else "Erreur export",
            msg, msg_type="success" if ok else "error", parent=self
        ).exec()

    def _apercu_import(self, format_fichier: str):
        """Import fournisseurs avec aperçu du fichier avant import (ApercuActeModal)."""
        from views.acte_medical.export_import_acte import ApercuActeModal
        from views.shared.message_box import CustomMessageBox

        ext    = "xlsx" if format_fichier == "excel" else "csv"
        filtre = "Excel Files (*.xlsx)" if format_fichier == "excel" else "CSV Files (*.csv)"

        chemin, _ = QFileDialog.getOpenFileName(
            self, f"Sélectionner le fichier {ext.upper()} — Fournisseurs", "", filtre
        )
        if not chemin:
            return

        try:
            import pandas as pd
            df = pd.read_excel(chemin, dtype=str) \
                 if format_fichier == "excel" \
                 else pd.read_csv(chemin, dtype=str, sep=None, engine='python', encoding="utf-8-sig")
            df = df.fillna("")
            if df.empty:
                CustomMessageBox("Import", "Le fichier ne contient aucune donnée.",
                                 msg_type="warning", parent=self).exec()
                return
            colonnes = list(df.columns)
            donnees  = [[str(v) for v in row] for _, row in df.iterrows()]
        except Exception as e:
            CustomMessageBox("Erreur de lecture", f"Impossible de lire le fichier :\n{e}",
                             msg_type="error", parent=self).exec()
            return

        modal = ApercuActeModal(
            self,
            f"Aperçu import {ext.upper()} — Fournisseurs",
            f"{len(donnees)} ligne(s) détectée(s) dans le fichier",
            colonnes, donnees, mode="import"
        )
        if not (modal.exec() and modal._confirme):
            return

        ok, msg = self.ctrl.importer_fournisseurs_from_excel(chemin) \
                  if format_fichier == "excel" \
                  else self.ctrl.importer_fournisseurs_from_csv(chemin)
        CustomMessageBox(
            "Import réussi" if ok else "Import — résultat",
            msg, msg_type="success" if ok else "warning", parent=self
        ).exec()
        if ok:
            self.charger_donnees()
    
    def on_notifications(self):
        print("Notifications")
    
    def on_reports(self):
        """Affiche le rapport PDF global des activités de tous les fournisseurs."""
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from views.shared.message_box import CustomMessageBox
        try:
            pdf_path = self.ctrl.generer_rapport_toutes_activites_fournisseurs(self.code_session)
            ApercuPDFDialog(pdf_path, "Rapport Global — Activités des Fournisseurs", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Impossible de générer le rapport :\n{e}",
                             msg_type="error", parent=self).exec()
    
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
        bg = f"background: {c['bg_card']};"
        for attr in ('tab_stats', 'tab_nouveau', 'tab_liste', 'tab_activites'):
            tab_w = getattr(self, attr, None)
            if tab_w:
                tab_w.setStyleSheet(bg)
    
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

        c = theme_manager.colors()
        tab = QWidget()
        tab.setStyleSheet(f"background: {c['bg_card']};")
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
        c = theme_manager.colors()
        tab = QWidget()
        tab.setStyleSheet(f"background: {c['bg_card']};")
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
        c = theme_manager.colors()
        tab = QWidget()
        tab.setStyleSheet(f"background: {c['bg_card']};")
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

        c = theme_manager.colors()
        tab = QWidget()
        tab.setStyleSheet(f"background: {c['bg_card']};")
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
                background: {c['bg_card']};
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
