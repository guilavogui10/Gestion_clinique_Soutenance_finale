"""
Vue Examen - interface principale de gestion des examens.
Architecture à onglets pour une interface cohérente avec consultation
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea,
                                QTabWidget, QFrame, QDialog, QHBoxLayout,
                                QLabel, QPushButton, QDateEdit,
                                QComboBox, QSizePolicy, QLineEdit)
from PySide6.QtCore import Qt, QSize, QDate
from views.shared.theme_manager import theme_manager
from .components import (
    KpiCardsSection,
    ExamensTable,
    QuickActions,
    ChartsSection
)
from .historique_examen import HistoriquePatientView


class ExamenView(QWidget):
    """Vue principale examen."""
    
    def __init__(self, examen_ctrl, permission_ctrl=None, user_info=None, parent=None):
        super().__init__(parent)
        self.ctrl = examen_ctrl
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
        
        # Onglet 3: Liste des examens
        self.tab_liste = self._create_liste_tab()
        icon_liste = self._get_icon("list")
        self.tabs.addTab(self.tab_liste, icon_liste, "Liste des examens")
        
        # Onglet 4: Patients en attente
        self.tab_attente = self._create_attente_tab()
        icon_attente = self._get_icon("clock")
        self.tabs.addTab(self.tab_attente, icon_attente, "Patients en attente")

        # Onglet 5: Historique patient
        self.tab_historique = self._create_historique_tab()
        icon_hist = self._get_icon("history")
        self.tabs.addTab(self.tab_historique, icon_hist, "Historique patient")
        
        # Quick Actions (toujours visible en bas)
        self.quick_actions = QuickActions()
        self.quick_actions.new_examen_clicked.connect(self.on_new_examen)
        self.quick_actions.patients_waiting_clicked.connect(self.on_patients_waiting)
        self.quick_actions.advanced_search_clicked.connect(self.on_advanced_search)
        self.quick_actions.reports_clicked.connect(self.on_reports)
        self.quick_actions.patient_history_clicked.connect(self.on_patient_history)
        self.quick_actions.imprimer_tous_rapports_clicked.connect(self._on_imprimer_tous_rapports)
        self.quick_actions.imprimer_rapport_date_clicked.connect(self._on_imprimer_rapport_par_date)
        self.quick_actions.export_excel_clicked.connect(lambda: self._on_export_import("export", "excel"))
        self.quick_actions.export_csv_clicked.connect(  lambda: self._on_export_import("export", "csv"))
        self.quick_actions.import_excel_clicked.connect(lambda: self._on_export_import("import", "excel"))
        self.quick_actions.import_csv_clicked.connect(  lambda: self._on_export_import("import", "csv"))
        main_frame_layout.addWidget(self.quick_actions)
        
        # Ajouter le frame principal au layout
        main_layout.addWidget(main_frame)
        
        # Appliquer le style au frame principal
        self._apply_main_frame_style(main_frame)
    
    def charger_examens(self, code_session):
        self.code_session = code_session
        # Mettre à jour les sous-vues AVANT charger_donnees
        if hasattr(self, 'vue_attente'):
            self.vue_attente.code_session = code_session
        if hasattr(self, 'form_widget'):
            self.form_widget.code_session = code_session
            self.form_widget.edit_session.setText(code_session or "")
        self.charger_donnees()
    
    def charger_donnees(self):
        if not self.code_session:
            return
        examens = self.ctrl.lister_examens(self.code_session)
        self.table.load_examens(examens, self.code_session)
        self.kpi_cards.rafraichir(self.code_session)
        # Rafraîchir les graphiques
        if hasattr(self, 'charts'):
            self.charts.update_data(self.code_session)
        # Rafraîchir la vue des patients en attente
        if hasattr(self, 'vue_attente'):
            self.vue_attente.charger_patients()
        # Rafraîchir le combo patient de l'historique
        if hasattr(self, 'vue_historique'):
            self.vue_historique.set_session(self.code_session)
    
    def on_view_examen(self, examen):
        from .detail_examen_modal import DetailsExamenModal
        DetailsExamenModal(self, examen.code, self.ctrl).exec()
    
    def on_delete_examen(self, examen):
        """Supprime un examen — nécessite OTP du DG via permission_helper."""
        from views.shared.message_box import CustomMessageBox

        if not self.permission_helper:
            ok, msg = self.ctrl.supprimer_examen(examen.code)
            CustomMessageBox("Succès" if ok else "Erreur", msg, ok, self).exec()
            if ok:
                self.charger_donnees()
            return

        def executer_suppression():
            ok, msg = self.ctrl.supprimer_examen(examen.code)
            CustomMessageBox("Succès" if ok else "Erreur", msg, ok, self).exec()
            if ok:
                self.charger_donnees()

        self.permission_helper.verifier_et_executer(
            action=self.permission_ctrl.ACTION_SUPPRESSION,
            contexte=f"Examen {examen.code}",
            callback_success=executer_suppression
        )

    def on_edit_examen(self, examen):
        """Modifier un examen - Vérification des permissions"""
        if not self.permission_helper:
            print(f"Éditer examen: {examen.code}")
            return
        
        def executer_modification():
            print(f"Éditer examen: {examen.code}")
        
        self.permission_helper.verifier_et_executer(
            action=self.permission_ctrl.ACTION_MODIFICATION,
            contexte=f"Examen {examen.code}",
            callback_success=executer_modification
        )
    
    def on_new_examen(self):
        """Créer un nouvel examen - Vérification des permissions"""
        if not self.permission_helper:
            self.tabs.setCurrentIndex(1)
            return
        
        if not self.permission_helper.peut_creer():
            def executer_creation():
                self.tabs.setCurrentIndex(1)
            
            self.permission_helper.verifier_et_executer(
                action=self.permission_ctrl.ACTION_MODIFICATION,
                contexte="Création d'un nouvel examen",
                callback_success=executer_creation
            )
        else:
            self.tabs.setCurrentIndex(1)

    def on_patients_waiting(self):
        """Bascule vers l'onglet Patients en attente."""
        self.tabs.setCurrentIndex(3)

    def _ouvrir_nouveau_avec_consultation(self, code_consultation: str):
        self.tabs.setCurrentIndex(1)
        if hasattr(self, 'form_widget'):
            self.form_widget.recharger_pour_patient(code_consultation, self.code_session)
    
    def on_advanced_search(self):
        """Recherche avancée entre deux dates."""
        if not self.code_session:
            return
        dialog = _RechercheEntresDatesDialog(self.ctrl, self.code_session, parent=self)
        if dialog.exec() == QDialog.Accepted:
            resultats = dialog.resultats
            self.tabs.setCurrentIndex(2)
            self.table.load_examens(resultats, self.code_session)

    def on_reports(self):
        """Affiche le menu export/import au-dessus du bouton Rapports & exports."""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QCursor
        from views.acte_medical.export_import_acte import ApercuActeModal
        import qtawesome as qta
        c = __import__('views.shared.theme_manager', fromlist=['theme_manager']).theme_manager.colors()

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {c['bg_card']}; border: 1px solid {c['border']};
                border-radius: 10px; padding: 6px 4px;
            }}
            QMenu::item {{
                padding: 9px 20px 9px 12px; border-radius: 6px;
                font-size: 13px; color: {c['text_primary']}; min-width: 220px;
            }}
            QMenu::item:selected {{ background: {c['primary_light']}; color: {c['primary']}; }}
            QMenu::separator {{ height: 1px; background: {c['border']}; margin: 4px 10px; }}
        """)
        act_exp_xl = menu.addAction(qta.icon("fa5s.file-excel", color="#217346"), "  Exporter Excel (.xlsx)")
        act_exp_cs = menu.addAction(qta.icon("fa5s.file-csv",   color="#0070c0"), "  Exporter CSV (.csv)")
        menu.addSeparator()
        act_imp_xl = menu.addAction(qta.icon("fa5s.upload", color="#217346"),     "  Importer Excel (.xlsx)")
        act_imp_cs = menu.addAction(qta.icon("fa5s.upload", color="#0070c0"),     "  Importer CSV (.csv)")

        act_exp_xl.triggered.connect(lambda: ApercuActeModal.ouvrir_export(self, self.ctrl, "examen", "excel"))
        act_exp_cs.triggered.connect(lambda: ApercuActeModal.ouvrir_export(self, self.ctrl, "examen", "csv"))
        act_imp_xl.triggered.connect(lambda: ApercuActeModal.ouvrir_import(self, self.ctrl, "examen", "excel"))
        act_imp_cs.triggered.connect(lambda: ApercuActeModal.ouvrir_import(self, self.ctrl, "examen", "csv"))

        from PySide6.QtGui import QCursor
        from PySide6.QtCore import QPoint
        menu.adjustSize()
        cursor_pos = QCursor.pos()
        menu.exec(QPoint(cursor_pos.x(), cursor_pos.y() - menu.sizeHint().height() - 6))

    def on_patient_history(self):
        """Bascule vers l'onglet Historique patient."""
        self.tabs.setCurrentIndex(4)
    
    def _on_export_import(self, mode: str, format_fichier: str):
        from views.acte_medical.export_import_acte import ApercuActeModal
        if mode == "export":
            ApercuActeModal.ouvrir_export(self, self.ctrl, "examen", format_fichier)
        else:
            ApercuActeModal.ouvrir_import(self, self.ctrl, "examen", format_fichier)

    def _on_imprimer_tous_rapports(self):
        """Génère un PDF de tous les examens de la session groupés par date."""
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        if not self.code_session:
            CustomMessageBox("Avertissement", "Aucune session active.", "warning", self).exec()
            return
        try:
            pdf_path = self.ctrl.generer_pdf_rapport_examens_par_date(self.code_session)
            ApercuPDFDialog(pdf_path, "Rapport — Tous les examens", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", self).exec()

    def _on_imprimer_rapport_par_date(self):
        """Ouvre le sélecteur de date puis génère un PDF pour ce jour."""
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        if not self.code_session:
            CustomMessageBox("Avertissement", "Aucune session active.", "warning", self).exec()
            return
        dialog = _DateSelectDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        date_cible = dialog.date_selectionnee
        try:
            pdf_path = self.ctrl.generer_pdf_rapport_date_precise_examens(self.code_session, date_cible)
            date_fmt = date_cible.strftime('%d/%m/%Y') if hasattr(date_cible, 'strftime') else str(date_cible)
            ApercuPDFDialog(pdf_path, f"Rapport examens du {date_fmt}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", self).exec()

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_main']};")
        self._apply_tab_styles()

        if hasattr(self, 'tabs'):
            for tab, bg in (
                (getattr(self, 'tab_stats',      None), c['bg_card']),
                (getattr(self, 'tab_nouveau',    None), c['bg_main']),
                (getattr(self, 'tab_liste',      None), c['bg_card']),
                (getattr(self, 'tab_statut',     None), c['bg_card']),
                (getattr(self, 'tab_historique', None), c['bg_card']),
            ):
                if tab:
                    tab.setStyleSheet(f"QWidget {{ background: {bg}; }}")

            main_frame = self.findChild(QFrame, "MainWhiteFrame")
            if main_frame:
                self._apply_main_frame_style(main_frame)

        # Propagation aux composants enfants
        for widget in (
            getattr(self, 'kpi_cards',       None),
            getattr(self, 'charts',          None),
            getattr(self, 'table',           None),
            getattr(self, 'quick_actions',   None),
            getattr(self, 'form_widget',     None),
            getattr(self, 'vue_attente',     None),
            getattr(self, 'vue_historique',  None),
        ):
            if widget:
                fn = getattr(widget, 'apply_theme', None) or getattr(widget, '_apply_theme', None)
                if fn:
                    try:
                        fn()
                    except Exception:
                        pass
    
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
        """Crée l'onglet Nouveau avec le formulaire d'examen"""
        from .examen_form_widget import ExamenFormWidget
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area pour le formulaire
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Widget formulaire
        self.form_widget = ExamenFormWidget(self.ctrl, self.code_session)
        self.form_widget.examen_saved.connect(self._on_examen_saved)
        scroll.setWidget(self.form_widget)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _on_examen_saved(self):
        """Appelé quand un examen est enregistré"""
        self.charger_donnees()
        # Revenir à l'onglet Liste
        self.tabs.setCurrentIndex(2)
    
    def _create_stats_tab(self):
        """Crée l'onglet Statistiques"""
        tab = QWidget()
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
        """Crée l'onglet Liste des examens"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)

        self.table = ExamensTable(self.ctrl)
        self.table.view_clicked.connect(self.on_view_examen)
        self.table.edit_clicked.connect(self.on_edit_examen)
        self.table.delete_clicked.connect(self.on_delete_examen)
        self.table.new_clicked.connect(self.on_new_examen)
        self.table.imprimer_info_clicked.connect(self._on_imprimer_info_examen)
        self.table.imprimer_avec_resultat_clicked.connect(self._on_imprimer_avec_resultat_examen)
        self.table.new_resultat_clicked.connect(self._on_new_resultat_examen)
        layout.addWidget(self.table)

        return tab

    def _create_attente_tab(self):
        """Crée l'onglet Patients en attente"""
        import qtawesome as qta
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)

        # Barre d'actions rapides
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addStretch()

        _c = theme_manager.colors()
        btn_acte = QPushButton(qta.icon("fa5s.arrow-right", color=_c['text_inverse']), "  Aller sur acte médical")
        btn_acte.setFixedHeight(32)
        btn_acte.setCursor(Qt.PointingHandCursor)
        btn_acte.setStyleSheet(f"""
            QPushButton {{
                background: {_c['primary']};
                color: {_c['text_inverse']};
                border: none;
                border-radius: 6px;
                padding: 0 14px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover   {{ background: {_c['primary_hover']}; }}
            QPushButton:pressed {{ background: {_c['primary_hover']}; }}
        """)
        btn_acte.clicked.connect(self._aller_sur_acte_medical)
        toolbar.addWidget(btn_acte)

        layout.addLayout(toolbar)

        # Importer et afficher la vue des patients en attente
        from .patients_examen_attente import PatientsAttenteExamenView

        self.vue_attente = PatientsAttenteExamenView(
            self.ctrl,
            self.code_session if hasattr(self, 'code_session') and self.code_session else "",
            parent=tab
        )
        self.vue_attente.ouvrir_formulaire.connect(self._ouvrir_nouveau_avec_consultation)
        self.vue_attente.changer_statut_signal.connect(self._on_changer_statut_patient_examen)
        layout.addWidget(self.vue_attente)

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

    def _rafraichir_acte_medical(self):
        """Demande à la page acte médical de rafraîchir sa file d'attente."""
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == "DashboardView":
                if hasattr(parent, "page_actes"):
                    try:
                        parent.page_actes._update_file_attente()
                    except Exception:
                        pass
                return
            parent = parent.parent()

    def _on_changer_statut_patient_examen(self, patient):
        """Gère le clic sur Démarrer/Fin examen depuis la carte patient."""
        from views.shared.message_box import CustomMessageBox
        if isinstance(patient, dict):
            code_visite     = patient.get("code_visite", "")
            statut_patient  = (patient.get("statut_patient", "") or "").strip()
            nom             = patient.get("nom", "")
            prenom          = patient.get("prenom", "")
            code_consultation = patient.get("code_consultation", "")
        else:
            code_visite     = getattr(patient, "code_visite", "")
            statut_patient  = (getattr(patient, "statut_patient", "") or "").strip()
            nom             = getattr(patient, "nom", "")
            prenom          = getattr(patient, "prenom", "")
            code_consultation = getattr(patient, "code_consultation", "")

        nom_complet = f"{nom} {prenom}".strip() or "ce patient"

        if statut_patient == "En examen":
            question = (
                f"Voulez-vous mettre fin à l'examen de {nom_complet} ?\n\n"
                "Vous serez redirigé vers le formulaire."
            )
            action = "terminer"
        else:
            question = f"Voulez-vous démarrer l'examen de {nom_complet} ?"
            action = "demarrer"

        if not CustomMessageBox.confirm(self, "Changement de statut", question):
            return

        if action == "demarrer":
            ok, msg = self.ctrl.demarrer_examen(code_visite)
            if ok:
                self.charger_donnees()
                self._rafraichir_acte_medical()
            else:
                CustomMessageBox("Erreur", msg, False, self).exec()
        else:
            self._code_visite_fin_examen = code_visite
            self._ouvrir_nouveau_avec_consultation(code_consultation)
            try:
                self.form_widget.examen_saved.disconnect(self._on_fin_examen_apres_saisie)
            except Exception:
                pass
            self.form_widget.examen_saved.connect(self._on_fin_examen_apres_saisie)

    def _on_fin_examen_apres_saisie(self):
        """Appelé après soumission du formulaire quand on termine un examen."""
        try:
            self.form_widget.examen_saved.disconnect(self._on_fin_examen_apres_saisie)
        except Exception:
            pass
        code_visite = getattr(self, "_code_visite_fin_examen", None)
        if code_visite:
            self.ctrl.terminer_examen(code_visite)
        self.charger_donnees()
        self._rafraichir_acte_medical()

    def _on_imprimer_info_examen(self, examen):
        """Génère et affiche une fiche PDF de l'examen."""
        from services.pdf_actes.examen_pdf import ExamenPDF
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from views.shared.message_box import CustomMessageBox
        code = examen.code
        try:
            detail = self.ctrl.obtenir_examen_complet(code)
            if not detail:
                CustomMessageBox("Erreur", f"Impossible de récupérer les détails de l'examen {code}.",
                                 "error", parent=self).exec()
                return
            try:
                info_cabinet = self.ctrl.get_cabinet_info()
            except Exception:
                info_cabinet = {}
            pdf_path = ExamenPDF.generer_pdf_examen(detail, info_cabinet, None)
            ApercuPDFDialog(pdf_path, f"Aperçu - Examen {code}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()

    def _on_imprimer_avec_resultat_examen(self, examen):
        """Génère et affiche un PDF combiné examen + résultat médical."""
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from services.pdf_actes.examen_pdf import ExamenPDF
        code = examen.code
        try:
            detail = self.ctrl.obtenir_examen_complet(code)
            if not detail:
                CustomMessageBox("Erreur", f"Impossible de récupérer les détails de l'examen {code}.",
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
                    code_acte = getattr(examen, 'code_acte', None)
                    if code_acte:
                        resultats = resultat_ctrl.lister_par_acte(code_acte) or []
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
                    "Aucun résultat médical trouvé pour cet examen.",
                    "info", parent=self
                ).exec()
                return

            fichier_bytes = None
            type_fichier_res = resultat_data.get('type_fichier', '') if isinstance(resultat_data, dict) else ''
            if type_fichier_res == 'image' and dashboard and hasattr(dashboard, "page_resultats"):
                try:
                    id_res = resultat_data.get('id_resultat') if isinstance(resultat_data, dict) else None
                    if id_res:
                        fichier_bytes = dashboard.page_resultats.ctrl.lire_fichier_bytes(id_res)
                except Exception:
                    pass

            pdf_path = ExamenPDF.generer_pdf_examen_avec_resultat(
                detail, resultat_data, info_cabinet, None,
                fichier_bytes=fichier_bytes, type_fichier_res=type_fichier_res
            )
            ApercuPDFDialog(pdf_path, f"Examen avec résultat — {code}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()

    def _on_new_resultat_examen(self, examen):
        """Navigue vers le formulaire nouveau résultat pré-rempli pour cet examen."""
        from PySide6.QtCore import QTimer
        dashboard = self._get_dashboard()
        if not dashboard or not hasattr(dashboard, "page_resultats"):
            return
        page_res = dashboard.page_resultats
        dashboard.workspace_stack.setCurrentWidget(page_res)
        page_res.tabs.setCurrentIndex(5)
        if hasattr(page_res, "n_type_source"):
            idx_type = page_res.n_type_source.findText("examen")
            if idx_type >= 0:
                page_res.n_type_source.setCurrentIndex(idx_type)

        def _select_code():
            if hasattr(page_res, "n_code_source"):
                combo = page_res.n_code_source
                for i in range(combo.count()):
                    if combo.itemData(i) == examen.code or combo.itemText(i) == examen.code:
                        combo.setCurrentIndex(i)
                        break

        QTimer.singleShot(300, _select_code)

    def _create_historique_tab(self):
        """Crée l'onglet Historique patient (5ème onglet)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.vue_historique = HistoriquePatientView(
            self.ctrl,
            self.code_session if hasattr(self, 'code_session') and self.code_session else "",
            parent=tab
        )
        layout.addWidget(self.vue_historique)
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
        from .styles import ExamenStyles
        self.tabs.setStyleSheet(ExamenStyles.tab_widget())


# ---------------------------------------------------------------------------
# Dialogs pour les Quick Actions
# ---------------------------------------------------------------------------

class _RechercheEntresDatesDialog(QDialog):
    """Recherche des examens entre deux dates."""

    def __init__(self, ctrl, code_session, parent=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.code_session = code_session
        self.resultats = []
        self._build()

    def _build(self):
        self.setWindowTitle("Recherche avancée — entre deux dates")
        self.setMinimumWidth(480)
        self.setModal(True)
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QDialog {{ background: {c['bg_main']}; }}
            QLabel {{ color: {c['text_primary']}; font-size: 13px; }}
            QDateEdit {{
                background: {c['bg_input']}; border: 1px solid {c['border']};
                border-radius: 8px; padding: 6px 12px;
                color: {c['text_primary']}; font-size: 13px; min-height: 32px;
            }}
            QDateEdit:focus {{ border-color: {c['primary']}; }}
            QPushButton#PrimaryBtn {{
                background: {c['primary']}; color: {c['text_inverse']}; border: none;
                border-radius: 8px; padding: 8px 24px; font-weight: 700; font-size: 13px;
            }}
            QPushButton#PrimaryBtn:hover {{ background: {c['primary_hover']}; }}
            QPushButton#SecondaryBtn {{
                background: {c['bg_card']}; color: {c['text_primary']};
                border: 1px solid {c['border']}; border-radius: 8px;
                padding: 8px 20px; font-size: 13px;
            }}
            QPushButton#SecondaryBtn:hover {{ background: {c['hover']}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        layout.addWidget(QLabel("<b>Définir la plage de dates :</b>"))

        grid = QHBoxLayout()
        date_debut_lbl = QLabel("Du :")
        date_debut_lbl.setFixedWidth(40)
        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate().addMonths(-1))
        self.date_debut.setDisplayFormat("dd/MM/yyyy")

        date_fin_lbl = QLabel("Au :")
        date_fin_lbl.setFixedWidth(40)
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setDisplayFormat("dd/MM/yyyy")

        grid.addWidget(date_debut_lbl)
        grid.addWidget(self.date_debut, 1)
        grid.addSpacing(16)
        grid.addWidget(date_fin_lbl)
        grid.addWidget(self.date_fin, 1)
        layout.addLayout(grid)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(f"color: {c['text_secondary']}; font-size: 12px;")
        layout.addWidget(self.lbl_count)

        btns = QHBoxLayout()
        btn_annuler = QPushButton("Annuler")
        btn_annuler.setObjectName("SecondaryBtn")
        btn_annuler.clicked.connect(self.reject)
        btn_rechercher = QPushButton("Rechercher")
        btn_rechercher.setObjectName("PrimaryBtn")
        btn_rechercher.clicked.connect(self._rechercher)
        btns.addStretch()
        btns.addWidget(btn_annuler)
        btns.addWidget(btn_rechercher)
        layout.addLayout(btns)

    def _rechercher(self):
        from datetime import date
        d_debut = self.date_debut.date().toPython()
        d_fin   = self.date_fin.date().toPython()
        try:
            self.resultats = self.ctrl.rechercher_entre_dates(
                self.code_session, d_debut, d_fin
            ) or []
        except Exception:
            self.resultats = []
        self.lbl_count.setText(f"{len(self.resultats)} résultat(s) trouvé(s)")
        if self.resultats:
            self.accept()


class _ResumeSessionDialog(QDialog):
    """Rapport / résumé de la session courante."""

    def __init__(self, ctrl, code_session, parent=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.code_session = code_session
        self._build()

    def _build(self):
        self.setWindowTitle("Rapport de session")
        self.setMinimumWidth(480)
        self.setModal(True)
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QDialog {{ background: {c['bg_main']}; }}
            QLabel {{ color: {c['text_primary']}; font-size: 13px; }}
            QPushButton#SecondaryBtn {{
                background: {c['bg_card']}; color: {c['text_primary']};
                border: 1px solid {c['border']}; border-radius: 8px;
                padding: 8px 20px; font-size: 13px;
            }}
            QPushButton#SecondaryBtn:hover {{ background: {c['hover']}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        layout.addWidget(QLabel(f"<b>Session :</b> {self.code_session}"))

        try:
            resume = self.ctrl.obtenir_resume_session(self.code_session) or {}
        except Exception:
            resume = {}

        donnees = [
            ("Total examens (session)",   resume.get("total_examens", 0)),
            ("Examens aujourd'hui",        resume.get("examens_aujourd_hui", 0)),
            ("Examens en attente",         resume.get("en_attente", 0)),
            ("Patients distincts",         resume.get("patients_distincts", 0)),
            ("Revenu total (GNF)",         self._fmt_money(resume.get("revenu_total", 0))),
            ("Revenu aujourd'hui (GNF)",   self._fmt_money(resume.get("revenu_aujourd_hui", 0))),
            ("Moyenne / examen (GNF)",     self._fmt_money(resume.get("moyenne_par_examen", 0))),
        ]

        for libelle, valeur in donnees:
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0)
            lbl_lib = QLabel(libelle)
            lbl_lib.setStyleSheet(f"color: {c['text_secondary']}; font-size: 12px;")
            lbl_val = QLabel(str(valeur))
            lbl_val.setStyleSheet(f"color: {c['text_primary']}; font-size: 13px; font-weight: 700;")
            lbl_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_l.addWidget(lbl_lib)
            row_l.addStretch()
            row_l.addWidget(lbl_val)
            layout.addWidget(row_w)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {c['border']};")
        layout.addWidget(sep)

        # Top libellés
        try:
            tops = self.ctrl.obtenir_top_libelles(self.code_session, 5) or []
        except Exception:
            tops = []

        if tops:
            layout.addWidget(QLabel("<b>Top 5 libellés les plus fréquents :</b>"))
            for item in tops:
                lib  = item.get("libelle_examen", "-") if isinstance(item, dict) else str(item)
                nb   = item.get("nb", "") if isinstance(item, dict) else ""
                row_w = QWidget()
                row_l = QHBoxLayout(row_w)
                row_l.setContentsMargins(0, 0, 0, 0)
                row_l.addWidget(QLabel(f"• {lib}"))
                row_l.addStretch()
                if nb:
                    cnt = QLabel(f"{nb} fois")
                    cnt.setStyleSheet(f"color: {c['primary']}; font-weight: 700;")
                    row_l.addWidget(cnt)
                layout.addWidget(row_w)

        btns = QHBoxLayout()
        btn_fermer = QPushButton("Fermer")
        btn_fermer.setObjectName("SecondaryBtn")
        btn_fermer.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(btn_fermer)
        layout.addLayout(btns)

    @staticmethod
    def _fmt_money(val):
        try:
            return f"{float(val):,.0f}".replace(",", " ")
        except Exception:
            return str(val or 0)


class _DateSelectDialog(QDialog):
    """Sélection d'une date pour le rapport examen par date."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.date_selectionnee = None
        self.setWindowTitle("Sélectionner une date")
        self.setFixedSize(360, 170)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self._init_ui()

    def _init_ui(self):
        from PySide6.QtWidgets import QFormLayout, QDialogButtonBox
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QDialog {{ background: {c['bg_main']}; }}
            QLabel {{ color: {c['text_primary']}; font-size: 13px; }}
            QDateEdit {{
                background: {c['bg_input']}; border: 1px solid {c['border']};
                border-radius: 8px; padding: 6px 12px;
                color: {c['text_primary']}; font-size: 13px; min-height: 32px;
            }}
            QDateEdit:focus {{ border-color: {c['primary']}; }}
            QDialogButtonBox QPushButton {{
                background: {c['primary']}; color: {c['text_inverse']}; border: none;
                border-radius: 8px; padding: 8px 20px; font-weight: 700; font-size: 13px;
                min-width: 80px;
            }}
            QDialogButtonBox QPushButton:hover {{ background: {c['primary_hover']}; }}
            QDialogButtonBox QPushButton[text="Annuler"] {{
                background: {c['bg_card']}; color: {c['text_primary']};
                border: 1px solid {c['border']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        form = QFormLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date :", self.date_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._valider)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _valider(self):
        self.date_selectionnee = self.date_edit.date().toPython()
        self.accept()

