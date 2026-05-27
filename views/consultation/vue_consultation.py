"""
Vue Consultation - interface principale de gestion des consultations.
Architecture à onglets pour une interface moins chargée
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                                QTabWidget, QFrame, QDialog, QDialogButtonBox,
                                QLabel, QDateEdit, QFormLayout, QPushButton)
from PySide6.QtCore import Qt, QSize, QDate
from views.shared.theme_manager import theme_manager
from .components import (
    KpiCardsSection,
    ConsultationsTable,
    QuickActions,
    ChartsSection
)
from .historique_consultation import HistoriqueConsultationView


class VueConsultation(QWidget):
    """Vue principale consultation."""
    
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
        
        # Onglet 1: Statistiques
        self.tab_stats = self._create_stats_tab()
        icon_stats = self._get_icon("chart-line")
        self.tabs.addTab(self.tab_stats, icon_stats, "Statistiques")
        
        # Onglet 2: Nouveau
        self.tab_nouveau = self._create_nouveau_tab()
        icon_nouveau = self._get_icon("plus")
        self.tabs.addTab(self.tab_nouveau, icon_nouveau, "Nouveau")
        
        # Onglet 3: Liste des consultations
        self.tab_liste = self._create_liste_tab()
        icon_liste = self._get_icon("list")
        self.tabs.addTab(self.tab_liste, icon_liste, "Liste des consultations")
        
        # Onglet 4: Statut patients
        self.tab_statut = self._create_statut_tab()
        icon_statut = self._get_icon("clock")
        self.tabs.addTab(self.tab_statut, icon_statut, "Statut patients")

        # Onglet 5: Historique patient
        self.tab_historique = self._create_historique_tab()
        icon_hist = self._get_icon("history")
        self.tabs.addTab(self.tab_historique, icon_hist, "Historique patient")
        
        # Quick Actions (toujours visible en bas)
        self.quick_actions = QuickActions()
        self.quick_actions.new_consultation_clicked.connect(self.on_new_consultation)
        self.quick_actions.patients_waiting_clicked.connect(self.on_patients_waiting)
        self.quick_actions.advanced_search_clicked.connect(self.on_advanced_search)
        self.quick_actions.reports_clicked.connect(self.on_reports)
        self.quick_actions.patient_history_clicked.connect(self.on_patient_history)
        self.quick_actions.imprimer_tous_rapports_clicked.connect(self._on_imprimer_tous_rapports)
        self.quick_actions.imprimer_rapport_date_clicked.connect(self._on_imprimer_rapport_par_date)
        main_frame_layout.addWidget(self.quick_actions)
        
        # Ajouter le frame principal au layout
        main_layout.addWidget(main_frame)
        
        # Appliquer le style au frame principal
        self._apply_main_frame_style(main_frame)
    
    def charger_consultations(self, code_session):
        self.code_session = code_session
        if hasattr(self, 'patients_attente_view'):
            self.patients_attente_view.code_session = code_session
        if hasattr(self, 'form_widget'):
            self.form_widget.code_session = code_session
            self.form_widget.edit_session.setText(code_session or "")
            self.form_widget.recharger_liste_visites(code_session)
        if hasattr(self, 'vue_historique'):
            self.vue_historique.set_session(code_session)
        self.charger_donnees()
    
    def charger_donnees(self):
        if not self.code_session:
            return
        consultations = self.ctrl.lister_consultations(self.code_session)
        self.table.load_consultations(consultations, self.code_session)
        self.kpi_cards.rafraichir(self.code_session)
        if hasattr(self, 'charts'):
            self.charts.update_data(self.code_session)
        if hasattr(self, 'patients_attente_view'):
            self.patients_attente_view.charger_patients()
        if hasattr(self, 'vue_historique'):
            self.vue_historique.set_session(self.code_session)
    
    def on_view_consultation(self, consultation):
        from .detail_consultation_modal import DetailsConsultationModal

        DetailsConsultationModal(self, consultation.code, self.ctrl).exec()
    
    def on_edit_consultation(self, consultation):
        """Modifier une consultation - Vérification des permissions"""
        if not self.permission_helper:
            print(f"Éditer consultation: {consultation.code}")
            return
        
        def executer_modification():
            print(f"Éditer consultation: {consultation.code}")
        
        self.permission_helper.verifier_et_executer(
            action=self.permission_ctrl.ACTION_MODIFICATION,
            contexte=f"Consultation {consultation.code}",
            callback_success=executer_modification
        )
    
    def on_new_consultation(self):
        """Créer une nouvelle consultation - Vérification des permissions"""
        if not self.permission_helper:
            self.tabs.setCurrentIndex(1)
            return
        
        if not self.permission_helper.peut_creer():
            def executer_creation():
                self.tabs.setCurrentIndex(1)
            
            self.permission_helper.verifier_et_executer(
                action=self.permission_ctrl.ACTION_MODIFICATION,
                contexte="Création d'une nouvelle consultation",
                callback_success=executer_creation
            )
        else:
            self.tabs.setCurrentIndex(1)
    
    def on_patients_waiting(self):
        self.tabs.setCurrentIndex(3)

    def on_patient_history(self):
        self.tabs.setCurrentIndex(4)

    def _ouvrir_nouveau_avec_visite(self, code_visite: str):
        self.tabs.setCurrentIndex(1)
        if hasattr(self, 'form_widget'):
            self.form_widget.recharger_pour_patient(code_visite, self.code_session)

    def _on_changer_statut_patient(self, patient):
        """Confirmation + changement de statut depuis l'onglet Statut patients."""
        from views.shared.message_box import CustomMessageBox
        code_visite    = patient.get("code_visite", "") if isinstance(patient, dict) else getattr(patient, "code_visite", "")
        statut_patient = (patient.get("statut_patient", "") if isinstance(patient, dict) else getattr(patient, "statut_patient", "")).strip()
        nom    = patient.get("nom", "")    if isinstance(patient, dict) else getattr(patient, "nom", "")
        prenom = patient.get("prenom", "") if isinstance(patient, dict) else getattr(patient, "prenom", "")
        nom_complet = f"{nom} {prenom}".strip() or "ce patient"

        if statut_patient == "En consultation":
            question = (
                f"Voulez-vous mettre fin à la consultation de {nom_complet} ?\n\n"
                "Vous serez redirigé vers le formulaire pour saisir les informations."
            )
            action = "terminer"
        else:
            question = f"Voulez-vous mettre {nom_complet} en consultation ?"
            action = "demarrer"

        if not CustomMessageBox.confirm(self, "Changement de statut", question):
            return

        if action == "demarrer":
            # Démarrer consultation : simple changement de statut
            ok, msg = self.ctrl.demarrer_consultation(code_visite)
            if ok:
                self.charger_donnees()
                if hasattr(self, 'patients_attente_view'):
                    self.patients_attente_view.charger_patients()
                self._rafraichir_acte_medical()
            else:
                from views.shared.message_box import CustomMessageBox
                CustomMessageBox("Erreur", msg, False, self).exec()
        else:
            # Fin consultation : rediriger vers le formulaire de saisie.
            # C'est l'enregistrement du formulaire qui déclenchera terminer_consultation
            # et le refresh de la file d'attente acte médical.
            self._code_visite_fin_consultation = code_visite
            self._ouvrir_nouveau_avec_visite(code_visite)
            # Connecter un handler one-shot sur consultation_saved
            try:
                self.form_widget.consultation_saved.disconnect(self._on_fin_consultation_apres_saisie)
            except Exception:
                pass
            self.form_widget.consultation_saved.connect(self._on_fin_consultation_apres_saisie)

    def _on_fin_consultation_apres_saisie(self):
        """
        Déclenché après que le médecin a enregistré la consultation depuis
        le formulaire (suite à un clic 'Fin consultation').
        — Change statut_patient → 'Consultation terminée'
        — Rafraîchit la file d'attente acte médical
        """
        # Déconnecter immédiatement (one-shot)
        try:
            self.form_widget.consultation_saved.disconnect(self._on_fin_consultation_apres_saisie)
        except Exception:
            pass

        code_visite = getattr(self, '_code_visite_fin_consultation', None)
        self._code_visite_fin_consultation = None

        if code_visite:
            self.ctrl.terminer_consultation(code_visite)

        if hasattr(self, 'patients_attente_view'):
            self.patients_attente_view.charger_patients()
        self._rafraichir_acte_medical()

    def _rafraichir_acte_medical(self):
        """Demande à la page actes médicaux de rafraîchir sa file d'attente."""
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == "DashboardView":
                if hasattr(parent, "page_actes"):
                    parent.page_actes._update_file_attente()
                return
            parent = parent.parent()

    def on_advanced_search(self):
        if not self.code_session:
            return
        dialog = _RechercheEntresDatesDialog(self.ctrl, self.code_session, parent=self)
        if dialog.exec():
            resultats = dialog.resultats
            self.table.load_consultations(resultats)
            self.tabs.setCurrentIndex(2)

    def on_reports(self):
        if not self.code_session:
            return
        _ResumeSessionDialog(self.ctrl, self.code_session, parent=self).exec()

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
                "clock": "fa5s.clock",
                "plus": "fa5s.plus-circle",
                "history": "fa5s.history",
            }
            return qta.icon(icon_map.get(icon_name, "fa5s.circle"), color=theme_manager.colors()['primary'])
        except:
            from PySide6.QtWidgets import QStyle
            style_map = {
                "chart-line": QStyle.SP_FileDialogDetailedView,
                "list": QStyle.SP_FileDialogListView,
                "clock": QStyle.SP_BrowserReload
            }
            return self.style().standardIcon(style_map.get(icon_name, QStyle.SP_FileIcon))
    
    def _create_nouveau_tab(self):
        """Crée l'onglet Nouveau avec le formulaire de consultation"""
        from .consultation_form_widget import ConsultationFormWidget
        
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
        self.form_widget = ConsultationFormWidget(self.ctrl, self.code_session)
        self.form_widget.consultation_saved.connect(self._on_consultation_saved)
        scroll.setWidget(self.form_widget)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _on_consultation_saved(self):
        """Appelé quand une consultation est enregistrée"""
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
        """Crée l'onglet Liste des consultations"""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        
        self.table = ConsultationsTable(self.ctrl)
        self.table.view_clicked.connect(self.on_view_consultation)
        self.table.edit_clicked.connect(self.on_edit_consultation)
        self.table.new_clicked.connect(self.on_new_consultation)
        self.table.imprimer_info_clicked.connect(self._on_imprimer_info_consultation)
        self.table.imprimer_avec_resultat_clicked.connect(self._on_imprimer_avec_resultat)
        self.table.new_resultat_clicked.connect(self._on_new_resultat_consultation)
        layout.addWidget(self.table)
        
        return tab
    
    def _create_statut_tab(self):
        """Crée l'onglet Statut patients"""
        import qtawesome as qta
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)

        # Barre d'actions rapides
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addStretch()

        btn_acte = QPushButton(qta.icon("fa5s.arrow-right", color="#ffffff"), "  Aller sur acte médical")
        btn_acte.setFixedHeight(32)
        btn_acte.setCursor(Qt.PointingHandCursor)
        btn_acte.setStyleSheet("""
            QPushButton {
                background: #2563EB;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 14px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover  { background: #1D4ED8; }
            QPushButton:pressed{ background: #1E40AF; }
        """)
        btn_acte.clicked.connect(self._aller_sur_acte_medical)
        toolbar.addWidget(btn_acte)

        layout.addLayout(toolbar)

        # Importer et afficher la vue des patients en attente
        from .patients_consultation_attente import PatientsAttenteConsultationView

        self.patients_attente_view = PatientsAttenteConsultationView(
            self.ctrl,
            self.code_session if hasattr(self, 'code_session') and self.code_session else "",
            parent=tab
        )
        self.patients_attente_view.ouvrir_formulaire.connect(self._ouvrir_nouveau_avec_visite)
        self.patients_attente_view.changer_statut_signal.connect(self._on_changer_statut_patient)
        layout.addWidget(self.patients_attente_view)

        return tab

    def _aller_sur_acte_medical(self):
        """Navigue vers la page acte médical dans le dashboard."""
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == "DashboardView":
                if hasattr(parent, "workspace_stack") and hasattr(parent, "page_actes"):
                    parent.workspace_stack.setCurrentWidget(parent.page_actes)
                return
            parent = parent.parent()

    def _get_dashboard(self):
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == "DashboardView":
                return parent
            parent = parent.parent()
        return None

    def _on_imprimer_info_consultation(self, consultation):
        """Génère et affiche une fiche PDF de la consultation."""
        from services.pdf_actes.consultation_pdf import ConsultationPDF
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from views.shared.message_box import CustomMessageBox
        code = consultation.code
        try:
            detail = self.ctrl.obtenir_consultation_complete(code)
            if not detail:
                CustomMessageBox("Erreur", f"Impossible de récupérer les détails de la consultation {code}.",
                                 "error", parent=self).exec()
                return
            try:
                info_cabinet = self.ctrl.get_cabinet_info()
            except Exception:
                info_cabinet = {}
            pdf_path = ConsultationPDF.generer_pdf_consultation(detail, info_cabinet, None)
            ApercuPDFDialog(pdf_path, f"Aperçu - Consultation {code}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()

    def _on_imprimer_avec_resultat(self, consultation):
        """Génère et affiche un PDF combiné consultation + résultat médical (même format que imprimer info)."""
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from services.pdf_actes.consultation_pdf import ConsultationPDF
        code = consultation.code
        try:
            detail = self.ctrl.obtenir_consultation_complete(code)
            if not detail:
                CustomMessageBox("Erreur", f"Impossible de récupérer les détails de la consultation {code}.",
                                 "error", parent=self).exec()
                return
            try:
                info_cabinet = self.ctrl.get_cabinet_info()
            except Exception:
                info_cabinet = {}

            resultat_data = {}
            dashboard = self._get_dashboard()
            if dashboard and hasattr(dashboard, "page_resultats"):
                try:
                    resultat_ctrl = dashboard.page_resultats.ctrl
                    resultats = resultat_ctrl.lister_par_consultation(code) or []
                    if resultats:
                        premier = resultats[0]
                        id_resultat = getattr(premier, "id_resultat", None) or (
                            premier.get("id_resultat") if isinstance(premier, dict) else None
                        )
                        if id_resultat:
                            resultat_data = resultat_ctrl.get_detail_resultat(id_resultat) or {}
                except Exception:
                    pass

            if not resultat_data:
                CustomMessageBox(
                    "Information",
                    "Aucun résultat médical trouvé pour cette consultation.",
                    "info", parent=self
                ).exec()
                return

            # Tenter de récupérer les bytes du fichier (image) depuis MinIO
            fichier_bytes = None
            type_fichier_res = resultat_data.get('type_fichier', '') if isinstance(resultat_data, dict) else ''
            if type_fichier_res == 'image' and dashboard and hasattr(dashboard, "page_resultats"):
                try:
                    id_res = resultat_data.get('id_resultat') if isinstance(resultat_data, dict) else None
                    if id_res:
                        fichier_bytes = dashboard.page_resultats.ctrl.lire_fichier_bytes(id_res)
                except Exception:
                    pass

            pdf_path = ConsultationPDF.generer_pdf_consultation_avec_resultat(
                detail, resultat_data, info_cabinet, None,
                fichier_bytes=fichier_bytes, type_fichier_res=type_fichier_res
            )
            ApercuPDFDialog(pdf_path, f"Consultation avec résultat — {code}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()

    def _on_new_resultat_consultation(self, consultation):
        """Navigue vers le formulaire nouveau résultat pré-rempli pour cette consultation."""
        from PySide6.QtCore import QTimer
        dashboard = self._get_dashboard()
        if not dashboard or not hasattr(dashboard, "page_resultats"):
            return
        page_res = dashboard.page_resultats
        dashboard.workspace_stack.setCurrentWidget(page_res)
        # Aller sur l'onglet "Enregistrer" (index 5)
        page_res.tabs.setCurrentIndex(5)
        # Pré-sélectionner "consultation" et le code
        if hasattr(page_res, "n_type_source"):
            idx_type = page_res.n_type_source.findText("consultation")
            if idx_type >= 0:
                page_res.n_type_source.setCurrentIndex(idx_type)

        def _select_code():
            if hasattr(page_res, "n_code_source"):
                combo = page_res.n_code_source
                for i in range(combo.count()):
                    if combo.itemData(i) == consultation.code or combo.itemText(i) == consultation.code:
                        combo.setCurrentIndex(i)
                        break

        QTimer.singleShot(300, _select_code)

    def _on_imprimer_tous_rapports(self):
        """Génère et affiche le PDF rapport de toutes les consultations groupées par date."""
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from views.shared.message_box import CustomMessageBox
        if not self.code_session:
            CustomMessageBox("Information", "Aucune session active.", "info", parent=self).exec()
            return
        try:
            pdf_path = self.ctrl.generer_pdf_rapport_consultations_par_date(self.code_session)
            ApercuPDFDialog(pdf_path, "Rapport des consultations par date", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()

    def _on_imprimer_rapport_par_date(self):
        """Affiche le dialog de sélection de date puis génère le PDF pour ce jour."""
        from views.shared.message_box import CustomMessageBox
        if not self.code_session:
            CustomMessageBox("Information", "Aucune session active.", "info", parent=self).exec()
            return
        dialog = _DateSelectDialog(parent=self)
        if dialog.exec():
            date_cible = dialog.date_selectionnee
            try:
                from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
                pdf_path = self.ctrl.generer_pdf_rapport_date_precise(self.code_session, date_cible)
                date_str = date_cible.strftime('%d/%m/%Y') if hasattr(date_cible, 'strftime') else str(date_cible)
                ApercuPDFDialog(pdf_path, f"Rapport du {date_str}", self).exec()
            except Exception as e:
                CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()

    def _create_historique_tab(self):
        """Crée l'onglet Historique patient"""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(0, 0, 0, 0)
        self.vue_historique = HistoriqueConsultationView(
            self.ctrl,
            self.code_session or "",
            parent=tab,
        )
        lay.addWidget(self.vue_historique)
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
    
    def _apply_statut_frame_style(self, frame):
        """Applique le style aux frames de l'onglet statut"""
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame#StatutFrame {{
                background: white;
                border: 1px solid {c['border']};
                border-radius: 8px;
            }}
        """)
    
    def _apply_tab_styles(self):
        """Applique les styles aux onglets"""
        from .styles import ConsultationStyles
        self.tabs.setStyleSheet(ConsultationStyles.tab_widget())


# ─── Dialogues auxiliaires ────────────────────────────────────────────────────

class _RechercheEntresDatesDialog(QDialog):
    """Recherche de consultations entre deux dates."""

    def __init__(self, ctrl, code_session: str, parent=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.code_session = code_session
        self.resultats = []
        self.setWindowTitle("Recherche entre deux dates")
        self.setFixedSize(400, 220)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self._init_ui()

    def _init_ui(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_card']}; color: {c['text_primary']};")
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        layout.addWidget(QLabel("<b>Rechercher des consultations entre deux dates</b>"))

        form = QFormLayout()
        form.setSpacing(10)
        today = QDate.currentDate()

        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(today.addDays(-30))
        self.date_debut.setDisplayFormat("dd/MM/yyyy")

        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(today)
        self.date_fin.setDisplayFormat("dd/MM/yyyy")

        form.addRow("Date début :", self.date_debut)
        form.addRow("Date fin :", self.date_fin)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._rechercher)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _rechercher(self):
        debut = self.date_debut.date().toPython()
        fin = self.date_fin.date().toPython()
        try:
            self.resultats = self.ctrl.rechercher_entre_dates(self.code_session, debut, fin) or []
        except Exception:
            self.resultats = []
        self.accept()


class _ResumeSessionDialog(QDialog):
    """Résumé statistique de la session de consultation."""

    def __init__(self, ctrl, code_session: str, parent=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.code_session = code_session
        self.setWindowTitle("Résumé de la session")
        self.setFixedSize(450, 360)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self._init_ui()

    def _init_ui(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_card']}; color: {c['text_primary']};")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        layout.addWidget(QLabel(f"<b style='font-size:15px'>Résumé — Session {self.code_session}</b>"))

        try:
            resume = self.ctrl.obtenir_resume_session(self.code_session) or {}
        except Exception:
            resume = {}

        def _row(label, val):
            lbl = QLabel(f"<b>{label}</b>&nbsp;&nbsp;{val}")
            lbl.setStyleSheet(f"padding: 6px 0; border-bottom: 1px solid {c['border_light']};")
            layout.addWidget(lbl)

        total = resume.get("total_consultations", 0)
        aujourd_hui = resume.get("consultations_du_jour", 0)
        en_attente = resume.get("patients_en_attente", 0)
        revenu = resume.get("revenu_total", 0.0)
        taux = resume.get("taux_services", {})

        _row("Consultations totales :", total)
        _row("Consultations du jour :", aujourd_hui)
        _row("Patients en attente :", en_attente)
        _row("Revenu total :", f"{float(revenu):,.0f} GNF".replace(",", " "))
        if taux:
            taux_str = " | ".join(f"{k}: {v}%" for k, v in taux.items())
            _row("Taux services :", taux_str)

        layout.addStretch()
        close_btn = QDialogButtonBox(QDialogButtonBox.Close)
        close_btn.rejected.connect(self.reject)
        layout.addWidget(close_btn)


class _DateSelectDialog(QDialog):
    """Dialog de sélection d'une date pour le rapport PDF par date."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.date_selectionnee = None
        self.setWindowTitle("Sélectionner une date")
        self.setFixedSize(360, 170)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self._init_ui()

    def _init_ui(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_card']}; color: {c['text_primary']};")
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        layout.addWidget(QLabel("<b>Sélectionner une date pour le rapport</b>"))

        form = QFormLayout()
        form.setSpacing(10)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setFixedHeight(36)
        self.date_edit.setStyleSheet(f"""
            QDateEdit {{
                background: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 0 10px;
                font-size: 13px;
                color: {c['text_primary']};
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 28px;
            }}
        """)
        form.addRow("Date :", self.date_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._valider)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _valider(self):
        self.date_selectionnee = self.date_edit.date().toPython()
        self.accept()
