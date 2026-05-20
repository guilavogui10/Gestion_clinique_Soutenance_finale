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
                        color=c.get("primary", "#2ecc71"))

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
            f"background:{c.get('primary','#2ecc71')}22; border-radius:10px; border:none;"
        )
        ib_lay = QVBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ic = QLabel()
        ic.setAlignment(Qt.AlignCenter)
        ic.setPixmap(
            qta.icon("fa5s.glasses", color=c.get("primary", "#2ecc71")).pixmap(QSize(22, 22))
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
        tab.setStyleSheet("background:white;")
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
        color = c.get(accent, '#2ecc71')
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
        ic_lbl.setStyleSheet("border:none; background:transparent;")
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
        tab.setStyleSheet("background:white;")
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
        tab.setStyleSheet("background:white;")
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(12, 8, 12, 12)

        self.table = CommandesTable(self.ctrl)
        self.table.view_clicked.connect(self._on_view_commande)
        self.table.edit_clicked.connect(self._on_edit_commande)
        self.table.new_clicked.connect(self._on_new_commande)
        lay.addWidget(self.table)
        return tab

    def _create_attente_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background:white;")
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(12, 8, 12, 12)
        lay.setSpacing(0)

        self.vue_attente = PatientsAttenteView(
            ctrl         = self.ctrl,
            code_session = self.code_session or "",
            parent       = tab,
        )
        self.vue_attente.ouvrir_formulaire.connect(
            self._ouvrir_nouveau_avec_consultation
        )
        lay.addWidget(self.vue_attente)
        return tab

    def _create_historique_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background: white;")
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
        if not self.code_session:
            return
        _ResumeSessionDialog(self, self.ctrl, self.code_session).exec()

    def _on_historique(self):
        self.tabs.setCurrentIndex(4)

    def _ouvrir_nouveau_avec_consultation(self, code_consultation: str):
        self.tabs.setCurrentIndex(1)
        if hasattr(self, 'form_widget'):
            self.form_widget.recharger_pour_patient(
                code_consultation, self.code_session or ""
            )

    def _on_commande_saved(self):
        self.charger_donnees()
        self.tabs.setCurrentIndex(2)

    # =========================================================================
    # STYLE
    # =========================================================================

    def _apply_main_frame_style(self, frame: QFrame):
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame#MainWhiteFrame {{
                background   : white;
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


