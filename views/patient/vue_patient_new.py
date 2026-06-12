"""
Vue Patient - Interface principale de gestion des patients
Architecture à onglets identique à Consultation
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                                QTabWidget, QFrame, QLabel, QPushButton)
from PySide6.QtCore import Qt, QSize
from views.shared.theme_manager import theme_manager
from .components import (
    KpiCardsSection,
    PatientsTable,
    QuickActions,
    ChartsSection
)
from .patient_form import PatientFormDialog
from views.shared.message_box import CustomMessageBox, PatientDetailDialog
from .fonctions_avancees import HistoriquePatientWidget


class VuePatient(QWidget):
    """Vue principale patient avec onglets"""
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        
        # Importer le contrôleur historique
        from controllers.controleur_historique_patient import HistoriquePatientControleur
        self.controleur_historique = HistoriquePatientControleur()
        
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(0)
        
        # Frame principal blanc
        main_frame = QFrame()
        main_frame.setObjectName("MainWhiteFrame")
        main_frame_layout = QVBoxLayout(main_frame)
        main_frame_layout.setContentsMargins(0, 0, 0, 0)
        main_frame_layout.setSpacing(0)
        
        # Tabs Widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setIconSize(QSize(20, 20))
        main_frame_layout.addWidget(self.tabs)
        
        # Onglet 1: Statistiques
        self.tab_stats = self._create_stats_tab()
        icon_stats = self._get_icon("chart-bar")
        self.tabs.addTab(self.tab_stats, icon_stats, "Statistiques")
        
        # Onglet 2: Nouveau Patient
        self.tab_nouveau = self._create_nouveau_tab()
        icon_nouveau = self._get_icon("plus")
        self.tabs.addTab(self.tab_nouveau, icon_nouveau, "Nouveau Patient")
        
        # Onglet 3: Liste des patients
        self.tab_liste = self._create_liste_tab()
        icon_liste = self._get_icon("list")
        self.tabs.addTab(self.tab_liste, icon_liste, "Liste des Patients")
        
        # Onglet 4: Historique Patient
        self.tab_historique = self._create_historique_tab()
        icon_historique = self._get_icon("history")
        self.tabs.addTab(self.tab_historique, icon_historique, "Historique Patient")
        
        # Quick Actions (toujours visible en bas)
        self.quick_actions = QuickActions()
        self.quick_actions.new_patient_clicked.connect(self.on_new_patient)
        self.quick_actions.refresh_clicked.connect(self.charger_donnees)
        self.quick_actions.stats_clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        self.quick_actions.export_clicked.connect(self._show_export_menu)
        main_frame_layout.addWidget(self.quick_actions)
        
        # Ajouter le frame principal
        main_layout.addWidget(main_frame)
        
        # Appliquer le style
        self._apply_main_frame_style(main_frame)
    
    def _create_stats_tab(self):
        """Crée l'onglet Statistiques"""
        tab = QWidget()
        tab.setStyleSheet(f"background: {theme_manager.colors()['bg_card']};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(20)  # Augmenter l'espacement
        layout.setAlignment(Qt.AlignTop)
        
        # KPI Cards
        self.kpi_cards = KpiCardsSection(self.controleur)
        layout.addWidget(self.kpi_cards)
        
        # Charts Section
        self.charts = ChartsSection(self.controleur)
        layout.addWidget(self.charts, 1)
        
        return tab
    
    def _create_nouveau_tab(self):
        """Crée l'onglet Nouveau Patient"""
        from .patient_form_widget import PatientFormWidget

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._scroll_nouveau = QScrollArea()
        self._scroll_nouveau.setWidgetResizable(True)
        self._scroll_nouveau.setFrameShape(QFrame.NoFrame)
        self._scroll_nouveau.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.form_widget = PatientFormWidget(self.controleur)
        self.form_widget.patient_saved.connect(self._on_patient_saved)
        self._scroll_nouveau.setWidget(self.form_widget)

        layout.addWidget(self._scroll_nouveau)

        return tab
    
    def _on_patient_saved(self):
        """Appelé quand un patient est enregistré"""
        self.charger_donnees()
        # Revenir à l'onglet Liste
        self.tabs.setCurrentIndex(2)
    
    def _create_liste_tab(self):
        """Crée l'onglet Liste des Patients"""
        tab = QWidget()
        tab.setStyleSheet(f"background: {theme_manager.colors()['bg_card']};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        
        # Tableau des patients
        self.table = PatientsTable(self.controleur)
        self.table.view_clicked.connect(self.on_view_patient)
        self.table.edit_clicked.connect(self.on_edit_patient)
        self.table.visit_clicked.connect(self.on_patient_row_clicked)  # Ouvre l'historique
        self.table.facture_clicked.connect(self.on_facture_patient)
        self.table.imprimer_dossier_clicked.connect(self.on_imprimer_dossier_patient)
        self.table.new_clicked.connect(self.on_new_patient)
        
        # Connecter le signal de clic sur ligne pour ouvrir l'historique
        self.table.row_clicked.connect(self.on_patient_row_clicked)
        
        layout.addWidget(self.table)
        
        return tab
    
    def charger_donnees(self):
        """Charge toutes les données"""
        try:
            # Charger les patients
            patients = self.controleur.reed_Allpatient()
            
            # Mettre à jour le tableau
            if hasattr(self, 'table'):
                self.table.load_patients(patients)
            
            # Mettre à jour les KPI
            if hasattr(self, 'kpi_cards'):
                self.kpi_cards.rafraichir()
            
            # Mettre à jour les graphiques
            if hasattr(self, 'charts'):
                self.charts.update_data()
        
        except Exception as e:
            print(f"Erreur chargement données: {e}")
    
    def on_new_patient(self):
        """Ouvre l'onglet Nouveau"""
        self.tabs.setCurrentIndex(1)
    
    def ouvrir_formulaire(self, patient_obj=None):
        """Ouvre le formulaire d'ajout/modification"""
        dialog = PatientFormDialog(self.controleur, patient_obj=patient_obj, parent=self)
        if dialog.exec():
            self.charger_donnees()
            if patient_obj:
                CustomMessageBox("Succès", "Patient modifié avec succès", is_success=True, parent=self).exec()
            else:
                CustomMessageBox("Succès", "Patient ajouté avec succès", is_success=True, parent=self).exec()
                # Revenir à la liste
                self.tabs.setCurrentIndex(2)
    
    def _create_historique_tab(self):
        """Crée l'onglet Historique Patient"""
        self.historique_widget = HistoriquePatientWidget(
            controleur_patient=self.controleur,
            controleur_visite=self.controleur_historique,
            controleur_consultation=self.controleur_historique,
            controleur_acte=self.controleur_historique,
            controleur_historique=self.controleur_historique,
            parent=self
        )
        
        # Connecter les signaux
        self.historique_widget.nouvelle_visite_clicked.connect(self._on_nouvelle_visite)
        self.historique_widget.voir_resultat_clicked.connect(self._on_voir_resultat)
        
        return self.historique_widget
    
    def on_patient_row_clicked(self, patient):
        """Appelé quand on clique sur une ligne du tableau patient"""
        # Basculer vers l'onglet Historique
        self.tabs.setCurrentIndex(3)
        
        # Charger l'historique du patient
        if hasattr(self, 'historique_widget'):
            self.historique_widget.charger_patient(patient)
    
    def on_view_patient(self, patient):
        """Affiche les détails d'un patient"""
        dialog = PatientDetailDialog(patient, self)
        dialog.exec()
    
    def on_edit_patient(self, patient):
        """Modifie un patient - ouvre l'onglet Nouveau avec les données"""
        # Basculer vers l'onglet Nouveau
        self.tabs.setCurrentIndex(1)
        # Recharger le formulaire avec les données du patient
        if hasattr(self, 'form_widget'):
            self.form_widget.recharger_pour_patient(patient)
    
    def on_create_visit(self, patient):
        """Crée une visite pour un patient"""
        CustomMessageBox(
            "Information",
            f"Fonctionnalité en cours d'implémentation.\n\n"
            f"Patient : {patient.get_nom()} {patient.get_prenom()}\n"
            f"Code : {patient.get_code_patient()}\n\n"
            f"Utilisez la vue Visite pour créer une nouvelle visite.",
            is_success=False,
            parent=self
        ).exec()
    
    def on_facture_patient(self, patient):
        """Affiche la liste des factures par visite dans un popover"""
        from views.patient.fonctions_avancees.factures_visites_popover import FacturesVisitesPopover
        from PySide6.QtGui import QCursor
        
        # Le controleur historique est déjà initialisé dans __init__
        popover = FacturesVisitesPopover(patient, self.controleur_historique, self)
        
        # Positionner AU-DESSUS du curseur pour rester visible
        from PySide6.QtWidgets import QApplication
        pos = QCursor.pos()
        screen = QApplication.screenAt(pos)
        if screen:
            screen_geo = screen.availableGeometry()
            x = max(screen_geo.x(), pos.x() - popover.width() // 2)
            y = pos.y() - popover.maximumHeight() - 10  # Au-dessus du curseur
            # Si ça dépasse en haut, on met en dessous
            if y < screen_geo.y():
                y = pos.y() + 15
            # Si ça dépasse à droite
            if x + popover.width() > screen_geo.right():
                x = screen_geo.right() - popover.width()
            popover.move(x, y)
        else:
            popover.move(pos.x() - 200, pos.y() - popover.maximumHeight() - 10)
        
        popover.exec()
    
    def on_imprimer_dossier_patient(self, patient):
        """Génère et affiche l'aperçu du dossier médical PDF complet du patient."""
        import os
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog

        try:
            code_patient = patient.get_code_patient()
            chemin_pdf   = self.controleur.generer_dossier_medical(code_patient)
            if chemin_pdf and os.path.exists(chemin_pdf):
                nom = f"{patient.get_prenom()} {patient.get_nom()}".strip()
                dlg = ApercuPDFDialog(
                    chemin_pdf,
                    titre=f"Dossier médical — {nom}",
                    parent=self
                )
                dlg.exec()
        except Exception as e:
            CustomMessageBox(
                "Erreur",
                f"Impossible de générer le dossier médical :\n{e}",
                is_success=False,
                parent=self
            ).exec()
    
    def _show_export_menu(self):
        """Affiche le menu export/import avec aperçu visuel au-dessus du bouton."""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtCore import QPoint
        from .export_import_patient import ApercuPatientModal
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
                min-width: 210px;
            }}
            QMenu::item:selected {{
                background: {c['primary_light']};
                color: {c['primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {c['border']};
                margin: 4px 10px;
            }}
        """)

        act_export_excel = menu.addAction(
            qta.icon("fa5s.file-excel", color="#217346"), "  Exporter en Excel (.xlsx)"
        )
        act_export_csv = menu.addAction(
            qta.icon("fa5s.file-csv", color="#0070c0"), "  Exporter en CSV (.csv)"
        )
        menu.addSeparator()
        act_import_excel = menu.addAction(
            qta.icon("fa5s.upload", color="#217346"), "  Importer depuis Excel (.xlsx)"
        )
        act_import_csv = menu.addAction(
            qta.icon("fa5s.upload", color="#0070c0"), "  Importer depuis CSV (.csv)"
        )
        menu.addSeparator()
        act_print = menu.addAction(
            qta.icon("fa5s.print", color=c['danger']), "  Imprimer Tout"
        )

        # Positionner le menu au-dessus du bouton export
        btn = self.quick_actions.btn_export
        menu.adjustSize()
        menu_h = menu.sizeHint().height()
        pos_global = btn.mapToGlobal(QPoint(0, 0))
        target = QPoint(pos_global.x(), pos_global.y() - menu_h - 6)
        action = menu.exec(target)

        if action == act_export_excel:
            ApercuPatientModal.ouvrir_export(self, self.controleur, "excel")
        elif action == act_export_csv:
            ApercuPatientModal.ouvrir_export(self, self.controleur, "csv")
        elif action == act_import_excel:
            ApercuPatientModal.ouvrir_import(self, self.controleur, "excel")
        elif action == act_import_csv:
            ApercuPatientModal.ouvrir_import(self, self.controleur, "csv")
        elif action == act_print:
            self._print_all()

    def _print_all(self):
        """Génère et affiche l'aperçu PDF de tous les patients (identique à consultation)."""
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        try:
            pdf_path = self.controleur.generer_rapport_patients()
            ApercuPDFDialog(pdf_path, "Rapport — Liste des patients", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Impossible de générer le rapport :\n{e}",
                             msg_type="error", parent=self).exec()
    
    def _get_icon(self, icon_name):
        """Récupère une icône Font Awesome"""
        try:
            import qtawesome as qta
            icon_map = {
                "chart-bar": "fa5s.chart-bar",
                "list": "fa5s.list",
                "plus": "fa5s.plus-circle",
                "history": "fa5s.history",
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
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
        """)
    
    def apply_theme(self):
        """Applique le thème actuel — cascade + propagation explicite à tous les enfants."""
        c = theme_manager.colors()

        # Fond du widget racine
        self.setStyleSheet(f"background: {c['bg_main']};")

        if hasattr(self, 'tabs'):
            from .styles import PatientStyles
            self.tabs.setStyleSheet(PatientStyles.tab_widget())

            # Cascade via QWidget{} pour atteindre scroll areas et tous descendants
            for tab in (getattr(self, 'tab_stats', None), getattr(self, 'tab_liste', None)):
                if tab:
                    tab.setStyleSheet(f"QWidget {{ background: {c['bg_card']}; }}")
            if hasattr(self, 'tab_nouveau'):
                self.tab_nouveau.setStyleSheet(f"QWidget {{ background: {c['bg_main']}; }}")
            # Scroll area du formulaire
            if hasattr(self, '_scroll_nouveau'):
                self._scroll_nouveau.setStyleSheet(
                    f"QScrollArea {{ background: {c['bg_main']}; border: none; }}"
                )

            main_frame = self.findChild(QFrame, "MainWhiteFrame")
            if main_frame:
                self._apply_main_frame_style(main_frame)

        # Propagation explicite à chaque composant enfant (belt + suspenders)
        for widget in (
            getattr(self, 'kpi_cards', None),
            getattr(self, 'charts', None),
            getattr(self, 'table', None),
            getattr(self, 'quick_actions', None),
            getattr(self, 'form_widget', None),
            getattr(self, 'historique_widget', None),
        ):
            if widget and hasattr(widget, 'apply_theme'):
                try:
                    widget.apply_theme()
                except Exception:
                    pass
        
        # Style du bouton dans l'onglet Nouveau - Plus nécessaire car formulaire intégré
        # if hasattr(self, 'btn_open_form'):
        #     from .styles import PatientStyles
        #     self.btn_open_form.setStyleSheet(PatientStyles.button_primary())
    
    def _on_nouvelle_visite(self):
        """Ouvre le formulaire de nouvelle visite"""
        CustomMessageBox(
            "Information",
            "Fonctionnalité en cours d'implémentation.\n\n"
            "Utilisez la vue Visite pour créer une nouvelle visite.",
            is_success=False,
            parent=self
        ).exec()
    
    def _on_voir_resultat(self, type_acte, code_acte):
        """Navigue vers la page résultats médicaux"""
        CustomMessageBox(
            "Information",
            f"Navigation vers résultats de l'acte {code_acte} ({type_acte})\n\n"
            f"Fonctionnalité en cours d'implémentation.",
            is_success=True,
            parent=self
        ).exec()
