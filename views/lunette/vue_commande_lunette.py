"""
=============================================================================
 VUE COMMANDE LUNETTE — version onglets (pattern consultation/chirurgie)
=============================================================================
 Tabs :
   0 — Statistiques  (KPI cards + graphe)
   1 — Nouvelle commande  (CommandeLunetteFormWidget)
   2 — Liste  (CommandesTable)
   3 — Patients en attente  (PatientsAttenteView)
   4 — Historique patient   (HistoriqueCommandeLunetteView)
=============================================================================
"""

import qtawesome as qta
from PySide6.QtCore    import Qt, QSize, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QTabWidget, QDialog, QDialogButtonBox, QDateEdit,
    QFormLayout,
)

from views.shared.theme_manager import theme_manager
from views.lunette.styles       import LunetteStyles
from views.lunette.commande_lunette_form_widget import CommandeLunetteFormWidget
from views.lunette.composants   import (
    CommandesTable,
    PatientsAttenteView,
    PatientsAttenteDialog,
    LunetteKpiCardsSection,
    LunetteQuickActions,
)
from views.lunette.graphiques        import CommandeLunetteChartsSection
from views.lunette.modals            import DetailsCommandeLunetteModal
from views.lunette.historique_lunette import HistoriqueCommandeLunetteView


# =============================================================================
# VUE PRINCIPALE
# =============================================================================

class CommandeLunetteView(QWidget):
    """
    Vue principale Lunettes — 4 onglets.
    """

    def __init__(self, commande_lunette_ctrl):
        super().__init__()
        self.ctrl         = commande_lunette_ctrl
        self.code_session = None
        self._init_ui()
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # CONSTRUCTION
    # =========================================================================

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(0)

        main_frame = QFrame()
        main_frame.setObjectName("MainWhiteFrame")
        mf_lay = QVBoxLayout(main_frame)
        mf_lay.setContentsMargins(0, 0, 0, 0)
        mf_lay.setSpacing(0)

        # Onglets
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)

        self.tab_stats   = self._create_stats_tab()
        self.tab_form    = self._create_form_tab()
        self.tab_liste   = self._create_liste_tab()
        self.tab_attente = self._create_attente_tab()
        self.tab_historique = self._create_historique_tab()

        self.tabs.addTab(self.tab_stats,      self._get_icon("chart-bar"),  "Statistiques")
        self.tabs.addTab(self.tab_form,       self._get_icon("plus"),        "Nouvelle commande")
        self.tabs.addTab(self.tab_liste,      self._get_icon("list"),        "Liste des commandes")
        self.tabs.addTab(self.tab_attente,    self._get_icon("clock"),       "Patients en attente")
        self.tabs.addTab(self.tab_historique, self._get_icon("history"),     "Historique patient")

        mf_lay.addWidget(self.tabs, 1)

        # Boutons actions rapides (toujours visible en bas)
        self.quick_actions = LunetteQuickActions()
        self.quick_actions.new_commande_clicked.connect(self._on_new_commande)
        self.quick_actions.patients_attente_clicked.connect(self._on_patients_attente)
        self.quick_actions.livraisons_clicked.connect(self._on_livraisons)
        self.quick_actions.recherche_clicked.connect(self._on_recherche)
        self.quick_actions.rapports_clicked.connect(self._on_rapports)
        self.quick_actions.historique_clicked.connect(self._on_historique)
        self.quick_actions.imprimer_tous_rapports_clicked.connect(self._on_imprimer_tous_rapports)
        self.quick_actions.imprimer_rapport_date_clicked.connect(self._on_imprimer_rapport_par_date)
        self.quick_actions.export_excel_clicked.connect(lambda: self._on_export_import("export", "excel"))
        self.quick_actions.export_csv_clicked.connect(  lambda: self._on_export_import("export", "csv"))
        self.quick_actions.import_excel_clicked.connect(lambda: self._on_export_import("import", "excel"))
        self.quick_actions.import_csv_clicked.connect(  lambda: self._on_export_import("import", "csv"))
        mf_lay.addWidget(self.quick_actions)

        main_layout.addWidget(main_frame)
        self._apply_main_frame_style(main_frame)

    def _get_icon(self, name: str):
        mapping = {
            "chart-bar": "fa5s.chart-bar",
            "plus":      "fa5s.plus-circle",
            "list":      "fa5s.list",
            "clock":     "fa5s.hourglass-half",
            "history":   "fa5s.history",
        }
        c = theme_manager.colors()
        return qta.icon(mapping.get(name, "fa5s.circle"),
                        color=c['primary'])

    # ── Header ────────────────────────────────────────────────────────────

    def _create_header(self) -> QFrame:
        c = theme_manager.colors()
        header = QFrame()
        header.setObjectName("ViewHeader")
        header.setFixedHeight(64)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(12)

        icon_box = QFrame()
        icon_box.setFixedSize(40, 40)
        icon_box.setStyleSheet(
            f"background:{c['primary']}22; border-radius:10px; border:none;"
        )
        ib_lay = QVBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ic = QLabel()
        ic.setAlignment(Qt.AlignCenter)
        ic.setPixmap(
            qta.icon("fa5s.glasses", color=c['primary']).pixmap(QSize(22, 22))
        )
        ib_lay.addWidget(ic)

        title = QLabel("Gestion des Commandes de Lunettes")
        title.setStyleSheet(
            f"font-size:17px; font-weight:700; color:{c['text_primary']}; border:none;"
        )
        lay.addWidget(icon_box)
        lay.addWidget(title)
        lay.addStretch()
        return header

    # ── Onglets ───────────────────────────────────────────────────────────

    def _create_stats_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background:{theme_manager.colors()['bg_main']};")
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(12, 8, 12, 12)
        lay.setSpacing(8)

        # 6 KPI cards
        self.kpi_cards = LunetteKpiCardsSection(self.ctrl)
        lay.addWidget(self.kpi_cards)

        # 3 graphiques
        self._charts = CommandeLunetteChartsSection(self.ctrl)
        lay.addWidget(self._charts, 1)
        return tab

    def _make_kpi(self, title: str, value: str,
                  icon_name: str, accent: str) -> QFrame:
        c = theme_manager.colors()
        color = c.get(accent, c['primary'])
        card = QFrame()
        card.setFixedHeight(110)
        card.setStyleSheet(
            f"QFrame{{background:{c['bg_card']}; border:1px solid {c['border_light']};"
            f"border-radius:12px;}}"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(4)

        hdr = QHBoxLayout()
        ic_lbl = QLabel()
        ic_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(QSize(18, 18)))
        ic_lbl.setStyleSheet(f"border:none; background:{c['bg_card']};")
        ttl = QLabel(title)
        ttl.setStyleSheet(
            f"font-size:11px; font-weight:700; color:{c['text_secondary']}; border:none;"
        )
        hdr.addWidget(ic_lbl)
        hdr.addSpacing(6)
        hdr.addWidget(ttl)
        hdr.addStretch()
        lay.addLayout(hdr)

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(
            f"font-size:28px; font-weight:700; color:{color}; border:none;"
        )
        val_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(val_lbl)

        card._value_lbl  = val_lbl
        card._icon_lbl   = ic_lbl
        card._icon_name  = icon_name
        card._accent_key = accent
        return card

    def _create_form_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background:{theme_manager.colors()['bg_main']};")
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.form_widget = CommandeLunetteFormWidget(
            controleur   = self.ctrl,
            code_session = self.code_session or "",
        )
        self.form_widget.commande_saved.connect(self._on_commande_saved)
        lay.addWidget(self.form_widget)
        return tab

    def _create_liste_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background:{theme_manager.colors()['bg_main']};")
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(12, 8, 12, 12)

        self.table = CommandesTable(self.ctrl)
        self.table.view_clicked.connect(self._on_view_commande)
        self.table.edit_clicked.connect(self._on_edit_commande)
        self.table.new_clicked.connect(self._on_new_commande)
        self.table.imprimer_info_clicked.connect(self._on_imprimer_info_lunette)
        self.table.imprimer_avec_resultat_clicked.connect(self._on_imprimer_avec_resultat_lunette)
        self.table.new_resultat_clicked.connect(self._on_new_resultat_lunette)
        lay.addWidget(self.table)
        return tab

    def _create_attente_tab(self) -> QWidget:
        from PySide6.QtWidgets import QHBoxLayout
        tab = QWidget()
        tab.setStyleSheet(f"background:{theme_manager.colors()['bg_main']};")
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(12, 8, 12, 12)
        lay.setSpacing(8)

        # Barre d'actions rapides
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addStretch()

        _ca = theme_manager.colors()
        from PySide6.QtWidgets import QPushButton as _QPB
        self._btn_aller_acte = _QPB(
            qta.icon("fa5s.arrow-right", color=_ca['text_inverse']),
            "  Aller sur acte médical"
        )
        self._btn_aller_acte.setFixedHeight(32)
        self._btn_aller_acte.setCursor(Qt.PointingHandCursor)
        self._btn_aller_acte.setStyleSheet(f"""
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
        self._btn_aller_acte.clicked.connect(self._aller_sur_acte_medical)
        toolbar.addWidget(self._btn_aller_acte)
        lay.addLayout(toolbar)

        self.vue_attente = PatientsAttenteView(
            ctrl         = self.ctrl,
            code_session = self.code_session or "",
            parent       = tab,
        )
        self.vue_attente.ouvrir_formulaire.connect(self._ouvrir_nouveau_avec_acte)
        self.vue_attente.changer_statut_signal.connect(self._on_changer_statut_patient_lunette)
        lay.addWidget(self.vue_attente)
        return tab

    def _create_historique_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background:{theme_manager.colors()['bg_main']};")
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(0, 0, 0, 0)
        self.vue_historique = HistoriqueCommandeLunetteView(
            self.ctrl,
            self.code_session or "",
            parent=tab,
        )
        lay.addWidget(self.vue_historique)
        return tab

    # =========================================================================
    # CHARGEMENT DONNÉES
    # =========================================================================

    def charger_commandes(self, code_session: str):
        """Point d'entrée — appelé depuis main_window lors de l'activation du module."""
        self.code_session = code_session

        if hasattr(self, 'vue_attente'):
            self.vue_attente.code_session = code_session
        if hasattr(self, 'form_widget'):
            self.form_widget.code_session = code_session
        if hasattr(self, 'vue_historique'):
            self.vue_historique.set_session(code_session)

        self.charger_donnees()

    def charger_donnees(self):
        if not self.code_session:
            return

        # Table
        commandes = self.ctrl.lister_commandes(self.code_session)
        self.table.load_commandes(commandes, self.code_session)

        # KPI cards
        self.kpi_cards.rafraichir(self.code_session)

        # 3 graphiques
        try:
            self._charts.update_data(self.code_session)
        except Exception as e:
            print(f"[VueLunette] charts: {e}")

        # Patients en attente
        if hasattr(self, 'vue_attente'):
            self.vue_attente.charger_patients()

        # Historique patient
        if hasattr(self, 'vue_historique'):
            self.vue_historique.set_session(self.code_session)

    # =========================================================================
    # ACTIONS
    # =========================================================================

    def _on_view_commande(self, commande):
        DetailsCommandeLunetteModal(self, commande.code, self.ctrl).exec()

    def _on_edit_commande(self, commande):
        self.tabs.setCurrentIndex(1)
        if hasattr(self, 'form_widget'):
            self.form_widget._commande_obj = commande
            self.form_widget.edit_numero_cadre.setText(commande.numero_cadre or "")
            self.form_widget.edit_numero_verre.setText(commande.numero_verre or "")
            self.form_widget.edit_prix.setText(str(commande.prix or ""))

    def _on_new_commande(self):
        self.tabs.setCurrentIndex(1)

    def _on_patients_attente(self):
        self.tabs.setCurrentIndex(3)

    def _on_livraisons(self):
        self.tabs.setCurrentIndex(2)

    def _on_recherche(self):
        if not self.code_session:
            return
        dlg = _RechercheEntresDatesDialog(self, self.ctrl, self.code_session)
        if dlg.exec() == QDialog.Accepted and dlg.resultats is not None:
            self.table.load_commandes(dlg.resultats)
            self.tabs.setCurrentIndex(2)

    def _on_rapports(self):
        """Affiche le menu export/import au-dessus du bouton Rapports."""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtCore import QPoint
        from views.acte_medical.export_import_acte import ApercuActeModal
        import qtawesome as qta
        from views.shared.theme_manager import theme_manager
        c = theme_manager.colors()

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background: {c['bg_card']}; border: 1px solid {c['border']};
                     border-radius: 10px; padding: 6px 4px; }}
            QMenu::item {{ padding: 9px 20px 9px 12px; border-radius: 6px;
                           font-size: 13px; color: {c['text_primary']}; min-width: 220px; }}
            QMenu::item:selected {{ background: {c['primary_light']}; color: {c['primary']}; }}
            QMenu::separator {{ height: 1px; background: {c['border']}; margin: 4px 10px; }}
        """)
        act_exp_xl = menu.addAction(qta.icon("fa5s.file-excel", color="#217346"), "  Exporter Excel (.xlsx)")
        act_exp_cs = menu.addAction(qta.icon("fa5s.file-csv",   color="#0070c0"), "  Exporter CSV (.csv)")
        menu.addSeparator()
        act_imp_xl = menu.addAction(qta.icon("fa5s.upload", color="#217346"),     "  Importer Excel (.xlsx)")
        act_imp_cs = menu.addAction(qta.icon("fa5s.upload", color="#0070c0"),     "  Importer CSV (.csv)")
        act_exp_xl.triggered.connect(lambda: ApercuActeModal.ouvrir_export(self, self.ctrl, "lunette", "excel"))
        act_exp_cs.triggered.connect(lambda: ApercuActeModal.ouvrir_export(self, self.ctrl, "lunette", "csv"))
        act_imp_xl.triggered.connect(lambda: ApercuActeModal.ouvrir_import(self, self.ctrl, "lunette", "excel"))
        act_imp_cs.triggered.connect(lambda: ApercuActeModal.ouvrir_import(self, self.ctrl, "lunette", "csv"))

        from PySide6.QtGui import QCursor
        menu.adjustSize()
        cursor_pos = QCursor.pos()
        menu.exec(QPoint(cursor_pos.x(), cursor_pos.y() - menu.sizeHint().height() - 6))

    def _on_historique(self):
        self.tabs.setCurrentIndex(4)

    def _on_export_import(self, mode: str, format_fichier: str):
        from views.acte_medical.export_import_acte import ApercuActeModal
        if mode == "export":
            ApercuActeModal.ouvrir_export(self, self.ctrl, "lunette", format_fichier)
        else:
            ApercuActeModal.ouvrir_import(self, self.ctrl, "lunette", format_fichier)

    def _on_imprimer_tous_rapports(self):
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        if not self.code_session:
            CustomMessageBox("Avertissement", "Aucune session active.", "warning", parent=self).exec()
            return
        try:
            pdf_path = self.ctrl.generer_pdf_rapport_commandes_par_date(self.code_session)
            ApercuPDFDialog(pdf_path, "Rapport toutes commandes lunettes", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()

    def _on_imprimer_rapport_par_date(self):
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        if not self.code_session:
            CustomMessageBox("Avertissement", "Aucune session active.", "warning", parent=self).exec()
            return
        dlg = _DateSelectDialog(self)
        if dlg.exec() != QDialog.Accepted or dlg.date_selectionnee is None:
            return
        try:
            pdf_path = self.ctrl.generer_pdf_rapport_date_precise_commandes(
                self.code_session, dlg.date_selectionnee
            )
            ApercuPDFDialog(pdf_path, f"Rapport lunettes du {dlg.date_selectionnee}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()

    def _ouvrir_nouveau_avec_acte(self, code_acte: str):
        self.tabs.setCurrentIndex(1)
        if hasattr(self, 'form_widget'):
            self.form_widget.recharger_pour_patient(
                code_acte, self.code_session or ""
            )

    def _on_commande_saved(self):
        """Appelé après l'enregistrement d'une commande."""
        # Recharger toutes les données
        self.charger_donnees()
        # Basculer sur l'onglet liste pour voir la commande créée
        self.tabs.setCurrentIndex(2)

    def _on_fin_lunette_apres_saisie(self):
        """Appelé après soumission du formulaire quand on termine une commande lunette."""
        try:
            self.form_widget.commande_saved.disconnect(self._on_fin_lunette_apres_saisie)
        except Exception:
            pass
        code_visite = getattr(self, "_code_visite_fin_lunette", None)
        if code_visite:
            self.ctrl.terminer_lunette(code_visite)
        self.charger_donnees()

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

    def _aller_sur_acte_medical(self):
        """Navigue vers la page acte médical dans le dashboard."""
        dashboard = self._get_dashboard()
        if dashboard and hasattr(dashboard, "workspace_stack") and hasattr(dashboard, "page_actes"):
            dashboard.workspace_stack.setCurrentWidget(dashboard.page_actes)

    # =========================================================================
    # WORKFLOW STATUT PATIENT
    # =========================================================================

    def _on_changer_statut_patient_lunette(self, patient):
        """Gère le changement de statut patient pour le service lunettes."""
        from views.shared.message_box import CustomMessageBox
        from PySide6.QtWidgets import QDialog
        
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

        if statut_patient != "En lunette":
            # Patient pas encore en lunette -> Démarrer le service lunette
            reponse = CustomMessageBox(
                "Démarrer optique",
                f"Confirmer la prise en charge de {nom_complet} au service optique ?",
                "info", show_cancel=True, parent=self
            ).exec()
            if reponse != QDialog.Accepted:
                return
            ok, msg = self.ctrl.demarrer_lunette(code_visite)
            if ok:
                CustomMessageBox("Succès", msg, "success", parent=self).exec()
                self.charger_donnees()
            else:
                CustomMessageBox("Erreur", msg, "error", parent=self).exec()
        else:
            # Patient déjà en lunette -> "Fin" ouvre le formulaire puis termine après saisie
            self._code_visite_fin_lunette = code_visite
            self._ouvrir_nouveau_avec_acte(code_acte)
            # Connecter le signal pour terminer après l'enregistrement
            try:
                self.form_widget.commande_saved.disconnect(self._on_fin_lunette_apres_saisie)
            except Exception:
                pass
            self.form_widget.commande_saved.connect(self._on_fin_lunette_apres_saisie)

    # =========================================================================
    # PDF HANDLERS
    # =========================================================================

    def _on_imprimer_info_lunette(self, commande):
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from services.pdf_actes.lunette_pdf import LunettePDF
        code = getattr(commande, 'code', None) or (commande.get('code') if isinstance(commande, dict) else '')
        try:
            commande_complete = self.ctrl.obtenir_commande_complete(code) if code else {}
            if not commande_complete:
                commande_complete = commande if isinstance(commande, dict) else {}
            try:
                info_cabinet = self.ctrl.get_cabinet_info()
            except Exception:
                info_cabinet = {}
            pdf_path = LunettePDF.generer_pdf_lunette(
                commande_complete, info_cabinet, None
            )
            ApercuPDFDialog(pdf_path, f"Commande lunette — {code}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()

    def _on_imprimer_avec_resultat_lunette(self, commande):
        from views.shared.message_box import CustomMessageBox
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from services.pdf_actes.lunette_pdf import LunettePDF
        code     = getattr(commande, 'code', None) or (commande.get('code') if isinstance(commande, dict) else '')
        code_acte = getattr(commande, 'code_acte', None) or (commande.get('code_acte') if isinstance(commande, dict) else '')
        try:
            commande_complete = self.ctrl.obtenir_commande_complete(code) if code else {}
            if not commande_complete:
                commande_complete = commande if isinstance(commande, dict) else {}
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
                    "Aucun résultat médical trouvé pour cette commande de lunettes.",
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

            pdf_path = LunettePDF.generer_pdf_lunette_avec_resultat(
                commande_complete, resultat_data, info_cabinet, None,
                fichier_bytes=fichier_bytes, type_fichier_res=type_fichier_res
            )
            ApercuPDFDialog(pdf_path, f"Lunette avec résultat — {code}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Erreur lors de la génération du PDF :\n{e}", "error", parent=self).exec()

    def _on_new_resultat_lunette(self, commande):
        from PySide6.QtCore import QTimer
        dashboard = self._get_dashboard()
        if not dashboard or not hasattr(dashboard, "page_resultats"):
            return
        page_res = dashboard.page_resultats
        dashboard.workspace_stack.setCurrentWidget(page_res)
        page_res.tabs.setCurrentIndex(5)
        code_acte = getattr(commande, 'code_acte', None) or (
            commande.get('code_acte') if isinstance(commande, dict) else ''
        ) or ''
        if hasattr(page_res, "n_type_source") and hasattr(page_res, "n_code_source"):
            def _select_code():
                try:
                    idx_type = page_res.n_type_source.findText("lunette")
                    if idx_type >= 0:
                        page_res.n_type_source.setCurrentIndex(idx_type)
                    if code_acte:
                        idx_code = page_res.n_code_source.findText(code_acte)
                        if idx_code >= 0:
                            page_res.n_code_source.setCurrentIndex(idx_code)
                except Exception:
                    pass
            QTimer.singleShot(300, _select_code)

    # =========================================================================
    # STYLE
    # =========================================================================

    def _apply_main_frame_style(self, frame: QFrame):
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame#MainWhiteFrame {{
                background   : {c['bg_card']};
                border       : 1px solid {c['border']};
                border-radius: 16px;
            }}
        """)

    def _apply_tab_styles(self):
        self.tabs.setStyleSheet(LunetteStyles.tab_widget())

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background:{c['bg_main']};")
        self._apply_tab_styles()

        # ── Onglets ──────────────────────────────────────────────────────────
        for tab in (self.tab_stats, self.tab_form, self.tab_liste,
                    self.tab_attente, self.tab_historique):
            tab.setStyleSheet(f"background:{c['bg_main']};")

        # ── Bouton acte médical ───────────────────────────────────────────────
        if hasattr(self, '_btn_aller_acte'):
            self._btn_aller_acte.setIcon(
                qta.icon("fa5s.arrow-right", color=c['text_inverse'])
            )
            self._btn_aller_acte.setStyleSheet(f"""
                QPushButton {{
                    background: {c['primary']}; color: {c['text_inverse']};
                    border: none; border-radius: 6px;
                    padding: 0 14px; font-size: 13px; font-weight: 600;
                }}
                QPushButton:hover   {{ background: {c['primary_hover']}; }}
                QPushButton:pressed {{ background: {c['primary_hover']}; }}
            """)


# =============================================================================
# DIALOGUES ACTIONS RAPIDES
# =============================================================================

class _RechercheEntresDatesDialog(QDialog):
    """Recherche de commandes de lunettes entre deux dates."""

    def __init__(self, parent, ctrl, code_session: str):
        super().__init__(parent)
        self.ctrl         = ctrl
        self.code_session = code_session
        self.resultats    = None
        self.setWindowTitle("Recherche entre deux dates")
        self.setMinimumWidth(380)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        form = QFormLayout()
        today = QDate.currentDate()

        self._date_debut = QDateEdit(today.addDays(-30))
        self._date_debut.setCalendarPopup(True)
        self._date_debut.setDisplayFormat("dd/MM/yyyy")

        self._date_fin = QDateEdit(today)
        self._date_fin.setCalendarPopup(True)
        self._date_fin.setDisplayFormat("dd/MM/yyyy")

        form.addRow("Date début :", self._date_debut)
        form.addRow("Date fin :",   self._date_fin)
        lay.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btns.accepted.connect(self._rechercher)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _rechercher(self):
        debut = self._date_debut.date().toPython()
        fin   = self._date_fin.date().toPython()
        self.resultats = self.ctrl.rechercher_entre_dates(
            self.code_session, debut, fin
        )
        self.accept()


class _ResumeSessionDialog(QDialog):
    """Résumé statistique de la session en cours."""

    def __init__(self, parent, ctrl, code_session: str):
        super().__init__(parent)
        self.setWindowTitle("Résumé de session")
        self.setMinimumWidth(400)
        self._build(ctrl, code_session)

    def _build(self, ctrl, code_session: str):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        total      = ctrl.obtenir_total_commandes_session(code_session)
        attente    = ctrl.obtenir_commandes_en_attente_livraison(code_session)
        montant    = ctrl.obtenir_revenu_total(code_session)
        delai_info = ctrl.obtenir_delai_moyen_livraison(code_session) or {}

        lignes = [
            ("Total commandes session",     str(total)),
            ("Commandes en attente livraison", str(attente)),
            ("Revenu total (FCFA)",          f"{montant:,.0f}"),
            ("Délai moyen livraison (j)",    str(delai_info.get("moyen", "—"))),
            ("Délai minimum (j)",            str(delai_info.get("minimum", "—"))),
            ("Délai maximum (j)",            str(delai_info.get("maximum", "—"))),
            ("Commandes livrées (base calcul)", str(delai_info.get("nombre_livrees", "—"))),
        ]

        form = QFormLayout()
        for label, valeur in lignes:
            lbl_val = QLabel(valeur)
            lbl_val.setStyleSheet("font-weight: 600;")
            form.addRow(label + " :", lbl_val)
        lay.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)


class _DateSelectDialog(QDialog):
    """Sélection d'une date pour le rapport lunettes."""

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


