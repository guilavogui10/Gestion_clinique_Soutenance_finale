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
        tab.setStyleSheet("background: white;")
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
        self.form_widget = PatientFormWidget(self.controleur)
        self.form_widget.patient_saved.connect(self._on_patient_saved)
        scroll.setWidget(self.form_widget)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _on_patient_saved(self):
        """Appelé quand un patient est enregistré"""
        self.charger_donnees()
        # Revenir à l'onglet Liste
        self.tabs.setCurrentIndex(2)
    
    def _create_liste_tab(self):
        """Crée l'onglet Liste des Patients"""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
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
        """Affiche la facture d'un patient"""
        CustomMessageBox(
            "Information",
            f"Facture du patient\n\n"
            f"Patient : {patient.get_nom()} {patient.get_prenom()}\n"
            f"Code : {patient.get_code_patient()}\n\n"
            f"Fonctionnalité en cours d'implémentation.",
            is_success=False,
            parent=self
        ).exec()
    
    def on_imprimer_dossier_patient(self, patient):
        """Imprime le dossier complet d'un patient"""
        CustomMessageBox(
            "Information",
            f"Impression du dossier\n\n"
            f"Patient : {patient.get_nom()} {patient.get_prenom()}\n"
            f"Code : {patient.get_code_patient()}\n\n"
            f"Fonctionnalité en cours d'implémentation.",
            is_success=False,
            parent=self
        ).exec()
    
    def _show_export_menu(self):
        """Affiche le menu d'export"""
        from PySide6.QtWidgets import QMenu, QFileDialog
        import qtawesome as qta
        
        menu = QMenu(self)
        c = theme_manager.colors()
        
        # Actions d'export
        action_excel = menu.addAction(qta.icon("fa5s.file-excel", color=c['success']), "Exporter Excel")
        action_csv = menu.addAction(qta.icon("fa5s.file-csv", color=c['primary']), "Exporter CSV")
        menu.addSeparator()
        action_print = menu.addAction(qta.icon("fa5s.print", color=c['danger']), "Imprimer Tout")
        
        # Connexions
        action_excel.triggered.connect(self._export_excel)
        action_csv.triggered.connect(self._export_csv)
        action_print.triggered.connect(self._print_all)
        
        # Afficher le menu à la position du curseur
        from PySide6.QtGui import QCursor
        menu.exec(QCursor.pos())
    
    def _export_excel(self):
        """Exporte vers Excel"""
        from PySide6.QtWidgets import QFileDialog
        chemin, _ = QFileDialog.getSaveFileName(self, "Exporter en Excel", "", "Excel Files (*.xlsx)")
        if chemin:
            reussite, message = self.controleur.export_to_excel(chemin)
            CustomMessageBox("Succès" if reussite else "Erreur", message, is_success=reussite, parent=self).exec()
    
    def _export_csv(self):
        """Exporte vers CSV"""
        from PySide6.QtWidgets import QFileDialog
        chemin, _ = QFileDialog.getSaveFileName(self, "Exporter en CSV", "", "CSV Files (*.csv)")
        if chemin:
            reussite, message = self.controleur.export_to_csv(chemin)
            CustomMessageBox("Succès" if reussite else "Erreur", message, is_success=reussite, parent=self).exec()
    
    def _print_all(self):
        """Imprime tous les patients"""
        from PySide6.QtWidgets import QFileDialog
        dossier = QFileDialog.getExistingDirectory(self, "Choisir le dossier d'enregistrement")
        if dossier:
            success, message = self.controleur.generer_liste_total_patient(dossier)
            CustomMessageBox("Succès" if success else "Erreur", message, is_success=success, parent=self).exec()
    
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
                background: white;
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
        """)
    
    def apply_theme(self):
        """Applique le thème actuel"""
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_main']};
            }}
        """)
        
        # Style des onglets
        if hasattr(self, 'tabs'):
            from .styles import PatientStyles
            self.tabs.setStyleSheet(PatientStyles.tab_widget())
            
            # Mettre à jour le frame principal
            main_frame = self.findChild(QFrame, "MainWhiteFrame")
            if main_frame:
                self._apply_main_frame_style(main_frame)
        
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
