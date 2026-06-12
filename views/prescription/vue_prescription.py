"""
Vue Prescription - interface principale de gestion des prescriptions.
Architecture à onglets pour une interface moins chargée
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea,
                                QTabWidget, QFrame, QHBoxLayout, QPushButton,
                                QDialog, QDialogButtonBox, QDateEdit, QFormLayout)
from PySide6.QtCore import Qt, QSize, QDate, QPoint
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
        self._apply_tab_styles()
        if hasattr(self, 'tabs'):
            main_frame = self.findChild(QFrame, "MainWhiteFrame")
            if main_frame:
                self._apply_main_frame_style(main_frame)

        # ── Onglets ──────────────────────────────────────────────────────────
        for attr in ('tab_stats', 'tab_panier', 'tab_attente'):
            tab = getattr(self, attr, None)
            if tab:
                tab.setStyleSheet(f"background: {c['bg_card']};")

        # ── Bouton acte médical ───────────────────────────────────────────────
        if hasattr(self, '_btn_acte'):
            self._btn_acte.setIcon(
                qta.icon("fa5s.arrow-right", color=c['text_inverse'])
            )
            self._btn_acte.setStyleSheet(f"""
                QPushButton {{
                    background: {c['primary']}; color: {c['text_inverse']};
                    border: none; border-radius: 6px;
                    padding: 0 14px; font-size: 13px; font-weight: 600;
                }}
                QPushButton:hover   {{ background: {c['primary_hover']}; }}
                QPushButton:pressed {{ background: {c['primary_hover']}; }}
            """)
    
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
        tab.setStyleSheet(f"background: {theme_manager.colors()['bg_card']};")
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
        self.table.imprimer_info_clicked.connect(self._on_imprimer_info_prescription)
        self.table.imprimer_avec_resultat_clicked.connect(self._on_imprimer_avec_resultat_prescription)
        self.table.new_resultat_clicked.connect(self._on_new_resultat_prescription)
        self.table.imprimer_rapport_clicked.connect(self._show_rapport_prescription_menu)
        layout.addWidget(self.table, 1)

        return tab
    
    def _create_panier_tab(self):
        """Crée l'onglet Panier Prescription optimisé : formulaire à gauche + panier à droite"""
        from PySide6.QtWidgets import QHBoxLayout
        from views.prescription.panier_prescription.prescription_widget_optimized import PrescriptionWidgetOptimized
        from views.prescription.panier_prescription.components.panier_widget import PanierPrescriptionWidget
        
        tab = QWidget()
        tab.setStyleSheet(f"background: {theme_manager.colors()['bg_card']};")
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
        if hasattr(self, 'patients_attente_view'):
            self.patients_attente_view.charger_patients()
        # Revenir à l'onglet Statistiques
        self.tabs.setCurrentIndex(0)
    
    def _create_attente_tab(self):
        """Crée l'onglet Patients en attente"""
        from PySide6.QtWidgets import QHBoxLayout, QPushButton
        tab = QWidget()
        tab.setStyleSheet(f"background: {theme_manager.colors()['bg_card']};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)

        # Barre d'actions rapides
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addStretch()

        _ca = theme_manager.colors()
        self._btn_acte = QPushButton(
            qta.icon("fa5s.arrow-right", color=_ca['text_inverse']),
            "  Aller sur acte médical"
        )
        btn_acte = self._btn_acte
        btn_acte.setFixedHeight(32)
        btn_acte.setCursor(Qt.PointingHandCursor)
        btn_acte.setStyleSheet(f"""
            QPushButton {{
                background: {_ca['primary']};
                color: {_ca['text_inverse']};
                border: none;
                border-radius: 6px;
                padding: 0 14px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover  {{ background: {_ca['primary_hover']}; }}
            QPushButton:pressed{{ background: {_ca['primary_hover']}; }}
        """)
        btn_acte.clicked.connect(self._aller_sur_acte_medical)
        toolbar.addWidget(btn_acte)
        layout.addLayout(toolbar)

        # Vue des patients en attente
        self.patients_attente_view = PatientsAttentePrescriptionView(
            self.ctrl,
            self.code_session if hasattr(self, 'code_session') and self.code_session else "",
            parent=tab
        )
        self.patients_attente_view.ouvrir_formulaire.connect(self._ouvrir_panier_avec_acte)
        self.patients_attente_view.changer_statut_signal.connect(self._on_changer_statut_patient_prescription)
        layout.addWidget(self.patients_attente_view)

        return tab

    def _aller_sur_acte_medical(self):
        dashboard = self._get_dashboard()
        if dashboard and hasattr(dashboard, "workspace_stack") and hasattr(dashboard, "page_actes"):
            dashboard.workspace_stack.setCurrentWidget(dashboard.page_actes)
    
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
        self.tabs.setStyleSheet(PrescriptionStyles.tab_widget())

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _get_dashboard(self):
        widget = self.parent()
        while widget is not None:
            if type(widget).__name__ == "DashboardView":
                return widget
            widget = widget.parent() if hasattr(widget, "parent") else None
        return None

    # =========================================================================
    # WORKFLOW STATUT PATIENT
    # =========================================================================

    def _on_changer_statut_patient_prescription(self, patient):
        from views.shared.message_box import CustomMessageBox
        if isinstance(patient, dict):
            code_visite    = patient.get("code_visite", "")
            statut_patient = (patient.get("statut_patient", "") or "").strip()
            nom            = patient.get("nom", "")
            prenom         = patient.get("prenom", "")
            code_acte      = patient.get("code_acte", "")
        else:
            code_visite    = getattr(patient, "code_visite", "")
            statut_patient = (getattr(patient, "statut_patient", "") or "").strip()
            nom            = getattr(patient, "nom", "")
            prenom         = getattr(patient, "prenom", "")
            code_acte      = getattr(patient, "code_acte", "")

        nom_complet = f"{nom} {prenom}".strip() or "ce patient"

        if statut_patient != "En pharmacie":
            # Démarrer pharmacie
            reponse = CustomMessageBox(
                "Démarrer pharmacie",
                f"Confirmer la prise en charge de {nom_complet} à la pharmacie ?",
                "info", show_cancel=True, parent=self
            ).exec()
            from PySide6.QtWidgets import QDialog
            if reponse != QDialog.Accepted:
                return
            ok, msg = self.ctrl.demarrer_prescription(code_visite)
            if ok:
                CustomMessageBox("Succès", msg, "success", parent=self).exec()
                self.patients_attente_view.charger_patients()
                self.charger_donnees_stats()
            else:
                CustomMessageBox("Erreur", msg, "error", parent=self).exec()
        else:
            # Fin pharmacie → ouvrir le panier avec code_acte pré-chargé
            reponse = CustomMessageBox(
                "Fin pharmacie",
                f"Terminer la prescription pour {nom_complet} ?",
                "info", show_cancel=True, parent=self
            ).exec()
            from PySide6.QtWidgets import QDialog
            if reponse != QDialog.Accepted:
                return
            self._ouvrir_panier_avec_acte(code_acte)

    # =========================================================================
    # PDF HANDLERS
    # =========================================================================

    def _on_imprimer_info_prescription(self, prescription):
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from services.pdf_actes.prescription_pdf import PrescriptionPDF
        code_acte = prescription.get("code_acte", "") if isinstance(prescription, dict) else ""
        try:
            lignes = self.ctrl.lister_par_acte(code_acte) or []
            try:
                info_cabinet = self.ctrl.get_cabinet_info()
            except Exception:
                info_cabinet = {}
            pdf_path = PrescriptionPDF.generer_pdf_prescription(
                prescription, lignes, info_cabinet, None
            )
            ApercuPDFDialog(pdf_path, f"Ordonnance — {code_acte}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()

    def _on_imprimer_avec_resultat_prescription(self, prescription):
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from services.pdf_actes.prescription_pdf import PrescriptionPDF
        code_acte = prescription.get("code_acte", "") if isinstance(prescription, dict) else ""
        try:
            lignes = self.ctrl.lister_par_acte(code_acte) or []
            try:
                info_cabinet = self.ctrl.get_cabinet_info()
            except Exception:
                info_cabinet = {}

            resultat_data = {}
            dashboard = self._get_dashboard()
            if dashboard and hasattr(dashboard, "page_resultats"):
                try:
                    resultat_ctrl = dashboard.page_resultats.ctrl
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
                    "Aucun résultat médical trouvé pour cette prescription.",
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

            pdf_path = PrescriptionPDF.generer_pdf_prescription_avec_resultat(
                prescription, lignes, resultat_data, info_cabinet, None,
                fichier_bytes=fichier_bytes, type_fichier_res=type_fichier_res
            )
            ApercuPDFDialog(pdf_path, f"Ordonnance avec résultat — {code_acte}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()

    def _on_new_resultat_prescription(self, prescription):
        from PySide6.QtCore import QTimer
        dashboard = self._get_dashboard()
        if not dashboard or not hasattr(dashboard, "page_resultats"):
            return
        page_res = dashboard.page_resultats
        dashboard.workspace_stack.setCurrentWidget(page_res)
        page_res.tabs.setCurrentIndex(5)
        code_acte = prescription.get("code_acte", "") if isinstance(prescription, dict) else ""
        if hasattr(page_res, "n_type_source") and hasattr(page_res, "n_code_source"):
            def _select_code():
                try:
                    idx_type = page_res.n_type_source.findText("prescription")
                    if idx_type >= 0:
                        page_res.n_type_source.setCurrentIndex(idx_type)
                    if code_acte:
                        idx_code = page_res.n_code_source.findText(code_acte)
                        if idx_code >= 0:
                            page_res.n_code_source.setCurrentIndex(idx_code)
                except Exception:
                    pass
            QTimer.singleShot(300, _select_code)

    def _show_rapport_prescription_menu(self):
        from PySide6.QtWidgets import QMenu
        import qtawesome as qta
        from views.shared.theme_manager import theme_manager
        c = theme_manager.colors()

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 6px 0;
            }}
            QMenu::item {{
                padding: 10px 20px;
                color: {c['text_primary']};
                font-size: 13px;
                font-weight: 500;
            }}
            QMenu::item:selected {{
                background: {c['primary_light']};
                color: {c['primary']};
                border-radius: 4px;
            }}
            QMenu::separator {{
                height: 1px;
                background: {c['border_light']};
                margin: 4px 8px;
            }}
        """)

        action_tous = menu.addAction(
            qta.icon("fa5s.file-pdf", color=c['primary']),
            "  Imprimer tous les rapports"
        )
        action_tous.triggered.connect(self._on_imprimer_tous_rapports_prescription)

        menu.addSeparator()

        action_date = menu.addAction(
            qta.icon("fa5s.calendar-day", color=c['success']),
            "  Imprimer rapport par date..."
        )
        action_date.triggered.connect(self._on_imprimer_rapport_par_date_prescription)

        menu.addSeparator()
        act_exp_xl = menu.addAction(qta.icon("fa5s.file-excel", color="#217346"), "  Exporter Excel (.xlsx)")
        act_exp_cs = menu.addAction(qta.icon("fa5s.file-csv",   color="#0070c0"), "  Exporter CSV (.csv)")
        menu.addSeparator()
        act_imp_xl = menu.addAction(qta.icon("fa5s.upload", color="#217346"),     "  Importer Excel (.xlsx)")
        act_imp_cs = menu.addAction(qta.icon("fa5s.upload", color="#0070c0"),     "  Importer CSV (.csv)")
        act_exp_xl.triggered.connect(lambda: self._on_export_import_prescription("export", "excel"))
        act_exp_cs.triggered.connect(lambda: self._on_export_import_prescription("export", "csv"))
        act_imp_xl.triggered.connect(lambda: self._on_export_import_prescription("import", "excel"))
        act_imp_cs.triggered.connect(lambda: self._on_export_import_prescription("import", "csv"))

        btn = self.table.btn_rapport
        menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

    def _on_export_import_prescription(self, mode: str, format_fichier: str):
        from views.acte_medical.export_import_acte import ApercuActeModal
        if mode == "export":
            ApercuActeModal.ouvrir_export(self, self.ctrl, "prescription", format_fichier)
        else:
            ApercuActeModal.ouvrir_import(self, self.ctrl, "prescription", format_fichier)

    def _on_imprimer_tous_rapports_prescription(self):
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        if not self.code_session:
            CustomMessageBox("Avertissement", "Aucune session active.", "warning", parent=self).exec()
            return
        try:
            pdf_path = self.ctrl.generer_pdf_rapport_prescriptions_par_date(self.code_session)
            ApercuPDFDialog(pdf_path, "Rapport toutes prescriptions", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()

    def _on_imprimer_rapport_par_date_prescription(self):
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        if not self.code_session:
            CustomMessageBox("Avertissement", "Aucune session active.", "warning", parent=self).exec()
            return
        dlg = _DateSelectDialog(self)
        if dlg.exec() != QDialog.Accepted or dlg.date_selectionnee is None:
            return
        try:
            pdf_path = self.ctrl.generer_pdf_rapport_date_precise_prescriptions(
                self.code_session, dlg.date_selectionnee
            )
            ApercuPDFDialog(pdf_path, f"Rapport prescriptions du {dlg.date_selectionnee}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()


# =============================================================================
# DIALOGUE SÉLECTION DE DATE
# =============================================================================

class _DateSelectDialog(QDialog):
    """Sélection d'une date pour le rapport prescriptions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.date_selectionnee = None
        self.setWindowTitle("Choisir une date")
        self.setMinimumWidth(300)
        self._init_ui()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        form = QFormLayout()
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date :", self.date_edit)
        lay.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._valider)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _valider(self):
        self.date_selectionnee = self.date_edit.date().toPython()
        self.accept()
