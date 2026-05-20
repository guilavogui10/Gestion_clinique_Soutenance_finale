"""
=============================================================================
 CHIRURGIE VIEW  â€” version onglets (alignÃ©e sur vue_examen.py)
=============================================================================
 Tabs :
   0 â€” Statistiques  (KPI + Charts)
   1 â€” Nouvelle chirurgie  (ChirurgieFormWidget)
   2 â€” Liste  (ChirurgiesTable)
   3 â€” Patients en attente  (PatientsAttenteChirurgieView)
=============================================================================
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QTabWidget, QPushButton, QMessageBox,
    QDialog, QDateEdit, QSizePolicy,
)

from views.shared.theme_manager import theme_manager
from views.chirurgie.styles import ChirurgieStyles
from views.chirurgie.chirurgie_form_widget import ChirurgieFormWidget
from views.chirurgie.patients_chirurgie_attente import (
    PatientsAttenteChirurgieView, PatientsAttenteDialog
)
from views.chirurgie.historique_chirurgie import HistoriquePatientChirurgieView
from views.chirurgie.detail_chirurgie_modal import DetailsChirurgieModal
from views.shared.message_box import CustomMessageBox
from .components import (
    KPICards,
    ChartsSection,
    QuickActions,
    ChirurgiesTable
)


# =============================================================================
# CHIRURGIE VIEW
# =============================================================================

class ChirurgieView(QWidget):
    """
    Vue principale pour la gestion des interventions chirurgicales.
    Quatre onglets : Statistiques, Nouvelle chirurgie, Liste, Patients en attente.
    """

    def __init__(self, chirurgie_ctrl, permission_ctrl=None, user_info=None):
        super().__init__()
        self.ctrl         = chirurgie_ctrl
        self.permission_ctrl = permission_ctrl
        self.user_info = user_info or {}
        self.code_session = None
        
        # Créer le helper de permissions si disponible
        self.permission_helper = None
        if self.permission_ctrl and self.user_info:
            from views.shared.permission_helper import PermissionHelper
            self.permission_helper = PermissionHelper(self, self.permission_ctrl, self.user_info)
        
        self._init_ui()
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # CONSTRUCTION DE L'INTERFACE
    # =========================================================================

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Frame principal blanc avec ombre
        main_frame = QFrame()
        main_frame.setObjectName("MainWhiteFrame")
        main_frame_layout = QVBoxLayout(main_frame)
        main_frame_layout.setContentsMargins(0, 0, 0, 0)
        main_frame_layout.setSpacing(0)

        # Onglets
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)

        self.tab_stats   = self._create_stats_tab()
        self.tab_form    = self._create_form_tab()
        self.tab_liste   = self._create_liste_tab()
        self.tab_attente = self._create_attente_tab()
        self.tab_historique = self._create_historique_tab()

        self.tabs.addTab(self.tab_stats,      self._get_icon("chart-bar"),   "Statistiques")
        self.tabs.addTab(self.tab_form,       self._get_icon("plus-circle"),  "Nouvelle chirurgie")
        self.tabs.addTab(self.tab_liste,      self._get_icon("list"),         "Liste des chirurgies")
        self.tabs.addTab(self.tab_attente,    self._get_icon("clock"),        "Patients en attente")
        self.tabs.addTab(self.tab_historique, self._get_icon("history"),      "Historique patient")

        main_frame_layout.addWidget(self.tabs, 1)

        # Quick Actions
        self.quick_actions = QuickActions()
        self.quick_actions.new_chirurgie_clicked.connect(self.on_new_chirurgie)
        self.quick_actions.patients_waiting_clicked.connect(self.on_patients_waiting)
        self.quick_actions.advanced_search_clicked.connect(self.on_advanced_search)
        self.quick_actions.reports_clicked.connect(self.on_reports)
        self.quick_actions.patient_history_clicked.connect(self.on_patient_history)
        main_frame_layout.addWidget(self.quick_actions)

        main_layout.addWidget(main_frame)
        self._apply_main_frame_style(main_frame)

    def _get_icon(self, name):
        mapping = {
            "chart-bar":   "fa5s.chart-bar",
            "plus-circle": "fa5s.plus-circle",
            "list":        "fa5s.list",
            "clock":       "fa5s.hourglass-half",
            "history":     "fa5s.history",
        }
        c = theme_manager.colors()
        return qta.icon(mapping.get(name, "fa5s.circle"), color=c.get("primary", "#3498db"))

    # â”€â”€â”€ Onglets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _create_stats_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)

        self.kpi_cards = KPICards(self.ctrl)
        layout.addWidget(self.kpi_cards)

        self.charts = ChartsSection(self.ctrl)
        layout.addWidget(self.charts, 1)

        return tab

    def _create_form_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.form_widget = ChirurgieFormWidget(
            controleur=self.ctrl,
            code_session=self.code_session or "",
        )
        self.form_widget.chirurgie_saved.connect(self._on_chirurgie_saved)
        layout.addWidget(self.form_widget)

        return tab

    def _create_liste_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)

        self.table = ChirurgiesTable(self.ctrl)
        self.table.view_clicked.connect(self.on_view_chirurgie)
        self.table.edit_clicked.connect(self.on_edit_chirurgie)
        self.table.new_clicked.connect(self.on_new_chirurgie)
        layout.addWidget(self.table)

        return tab

    def _create_attente_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(0)

        self.vue_attente = PatientsAttenteChirurgieView(
            ctrl=self.ctrl,
            code_session=self.code_session or "",
            parent=tab,
        )
        self.vue_attente.ouvrir_formulaire.connect(self._ouvrir_nouveau_avec_consultation)
        layout.addWidget(self.vue_attente)

        return tab

    def _create_historique_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.vue_historique = HistoriquePatientChirurgieView(
            ctrl=self.ctrl,
            code_session=self.code_session or "",
            parent=tab,
        )
        layout.addWidget(self.vue_historique)

        return tab

    # =========================================================================
    # CHARGEMENT DONNÃ‰ES
    # =========================================================================

    def charger_chururgies(self, code_session: str):
        """Charge les chirurgies et met Ã  jour toutes les vues."""
        self.code_session = code_session

        # Mettre Ã  jour les sous-vues AVANT charger_donnees
        if hasattr(self, 'vue_attente'):
            self.vue_attente.code_session = code_session
        if hasattr(self, 'form_widget'):
            self.form_widget.code_session = code_session

        self.charger_donnees()

    def charger_donnees(self):
        if not self.code_session:
            return

        chirurgies = self.ctrl.lister_chururgies(self.code_session)
        self.table.load_chirurgies(chirurgies, self.code_session)

        self.kpi_cards.rafraichir(self.code_session)

        if hasattr(self, 'charts'):
            self.charts.update_data(self.code_session)

        if hasattr(self, 'vue_attente'):
            self.vue_attente.charger_patients()

        if hasattr(self, 'vue_historique'):
            self.vue_historique.set_session(self.code_session)

    # =========================================================================
    # ACTIONS
    # =========================================================================

    def on_view_chirurgie(self, chirurgie):
        """Voir les détails d'une chirurgie - Pas de restriction"""
        DetailsChirurgieModal(self, chirurgie.code, self.ctrl).exec()
    
    def on_view_resultats_chirurgie(self, chirurgie):
        """Voir les résultats d'une chirurgie - Nécessite OTP"""
        if not self.permission_helper:
            # Mode dégradé sans permissions
            CustomMessageBox.info(self, "Résultats", f"Affichage des résultats de {chirurgie.code}")
            return
        
        # Vérifier et exécuter avec gestion OTP (même pour les responsables)
        def afficher_resultats():
            CustomMessageBox.success(
                self,
                "Accès autorisé",
                f"Affichage des résultats de la chirurgie {chirurgie.code}"
            )
            # TODO: Ouvrir l'interface des résultats
        
        self.permission_helper.verifier_et_executer(
            action=self.permission_ctrl.ACTION_CONSULTATION,
            contexte=f"Résultats chirurgie {chirurgie.code}",
            callback_success=afficher_resultats
        )

    def on_edit_chirurgie(self, chirurgie):
        """Modifier une chirurgie - Vérification des permissions"""
        if not self.permission_helper:
            # Mode dégradé sans permissions
            print(f"Éditer chirurgie: {chirurgie.code}")
            return
        
        # Vérifier et exécuter avec gestion OTP
        def executer_modification():
            print(f"Éditer chirurgie: {chirurgie.code}")
            # TODO: Ouvrir le formulaire de modification
        
        self.permission_helper.verifier_et_executer(
            action=self.permission_ctrl.ACTION_MODIFICATION,
            contexte=f"Chirurgie {chirurgie.code}",
            callback_success=executer_modification
        )

    def on_new_chirurgie(self):
        """Créer une nouvelle chirurgie - Vérification des permissions"""
        if not self.permission_helper:
            # Mode dégradé sans permissions
            self.tabs.setCurrentIndex(1)
            return
        
        # Vérifier si l'utilisateur peut créer
        if not self.permission_helper.peut_creer():
            # Demander l'autorisation au responsable
            def executer_creation():
                self.tabs.setCurrentIndex(1)
            
            self.permission_helper.verifier_et_executer(
                action=self.permission_ctrl.ACTION_CREATION,
                contexte="Création d'une nouvelle chirurgie",
                callback_success=executer_creation
            )
        else:
            # Autorisation directe pour les responsables
            self.tabs.setCurrentIndex(1)

    def on_patients_waiting(self):
        self.tabs.setCurrentIndex(3)

    def on_advanced_search(self):
        if not self.code_session:
            return
        dlg = _RechercheEntresDatesDialog(self.ctrl, self.code_session, parent=self)
        dlg.exec()

    def on_reports(self):
        if not self.code_session:
            return
        dlg = _ResumeSessionDialog(self.ctrl, self.code_session, parent=self)
        dlg.exec()

    def on_patient_history(self):
        self.tabs.setCurrentIndex(4)

    def _ouvrir_nouveau_avec_consultation(self, code_consultation: str):
        self.tabs.setCurrentIndex(1)
        if hasattr(self, 'form_widget'):
            self.form_widget.recharger_pour_patient(
                code_consultation, self.code_session or ""
            )

    def _on_chirurgie_saved(self):
        self.charger_donnees()
        self.tabs.setCurrentIndex(2)

    # =========================================================================
    # STYLE
    # =========================================================================

    def _apply_main_frame_style(self, frame):
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame#MainWhiteFrame {{
                background: white;
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
        """)

    def _apply_tab_styles(self):
        from .styles import ChirurgieStyles
        self.tabs.setStyleSheet(ChirurgieStyles.tab_widget())

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_main']};")
        self._apply_tab_styles()


# =============================================================================
# DIALOGS INTERNES
# =============================================================================

class _RechercheEntresDatesDialog(QDialog):
    """Recherche des chirurgies entre deux dates."""

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
            QDateEdit:focus {{ border-color: {c.get('danger', '#dc2626')}; }}
            QPushButton#PrimaryBtn {{
                background: {c.get('danger', '#dc2626')}; color: white; border: none;
                border-radius: 8px; padding: 8px 24px; font-weight: 700; font-size: 13px;
            }}
            QPushButton#PrimaryBtn:hover {{ background: {c.get('danger', '#dc2626')}cc; }}
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
    """Rapport / résumé de la session chirurgie courante."""

    def __init__(self, ctrl, code_session, parent=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.code_session = code_session
        self._build()

    def _build(self):
        self.setWindowTitle("Rapport de session — Chirurgie")
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
            total    = self.ctrl.obtenir_total_chururgies_session(self.code_session) or 0
        except Exception:
            total = 0
        try:
            auj      = self.ctrl.obtenir_chururgies_aujourd_hui(self.code_session) or 0
        except Exception:
            auj = 0
        try:
            attente  = self.ctrl.obtenir_chururgies_en_attente(self.code_session) or 0
        except Exception:
            attente = 0
        try:
            montant  = self.ctrl.obtenir_montant_total_par_session(self.code_session) or 0
        except Exception:
            montant = 0
        try:
            m_auj    = self.ctrl.obtenir_montant_total_aujourdhui(self.code_session) or 0
        except Exception:
            m_auj = 0

        donnees = [
            ("Total chirurgies (session)",    total),
            ("Chirurgies aujourd'hui",         auj),
            ("Chirurgies en attente",          attente),
            ("Montant total session (GNF)",    self._fmt_money(montant)),
            ("Montant aujourd'hui (GNF)",      self._fmt_money(m_auj)),
        ]

        for libelle, valeur in donnees:
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0)
            lbl_lib = QLabel(libelle)
            lbl_lib.setStyleSheet(f"color: {c['text_secondary']}; font-size: 12px;")
            lbl_val = QLabel(str(valeur))
            lbl_val.setStyleSheet(
                f"color: {c['text_primary']}; font-size: 13px; font-weight: 700;"
            )
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
            layout.addWidget(QLabel("<b>Top 5 chirurgies les plus fréquentes :</b>"))
            for item in tops:
                lib = item.get("libelle_chururgie", "-") if isinstance(item, dict) else str(item)
                nb  = item.get("nb", "") if isinstance(item, dict) else ""
                row_w = QWidget()
                row_l = QHBoxLayout(row_w)
                row_l.setContentsMargins(0, 0, 0, 0)
                row_l.addWidget(QLabel(f"• {lib}"))
                row_l.addStretch()
                if nb:
                    cnt = QLabel(f"{nb} fois")
                    cnt.setStyleSheet(
                        f"color: {c.get('danger', '#dc2626')}; font-weight: 700;"
                    )
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

