"""
Vue principale — Gestion des actes médicaux.
Architecture à onglets :
  • Statistiques  : KPIs + graphiques répartition
  • Liste actes   : tableau paginé + filtres + actions
  • File d'attente: actes en_attente / en_cours par type
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QTabWidget, QFrame, QPushButton, QLabel,
    QLineEdit, QComboBox, QTextEdit, QGridLayout, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon

from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox

from .components import KpiCardsSection, ActesTable, QuickActions, ChartsSection
from .acte_form_dialog import ActeFormDialog
from .choix_patient_dialog import ChoixPatientDialog
from .detail_acte_modal import DetailActeModal


def _acte_to_dict(acte) -> dict:
    """Convertit un objet ActeMedical en dict pour les composants vue."""
    if isinstance(acte, dict):
        return acte
    return {
        "id_acte":           getattr(acte, "id_acte",           None),
        "code_consultation": getattr(acte, "code_consultation",  None),
        "type_acte":         getattr(acte, "type_acte",          None),
        "decision_medicale": getattr(acte, "decision_medicale",  None),
        "choix_patient":     getattr(acte, "choix_patient",      None),
        "mode_realisation":  getattr(acte, "mode_realisation",   None),
        "statut_acte":       getattr(acte, "statut_acte",        None),
        "raison_refus":      getattr(acte, "raison_refus",       None),
        "date_creation":     getattr(acte, "date_creation",      None),
        "source_acte":       getattr(acte, "source_acte",        None),
    }


class VueActeMedical(QWidget):
    """Vue principale pour la gestion des actes médicaux."""

    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl   = controleur
        self.logger = logging.getLogger(__name__)

        self.init_ui()
        self.connect_signals()
        self.load_data()
        self._setup_auto_refresh()

        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    # =========================================================================
    # CONSTRUCTION UI
    # =========================================================================

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(0)

        main_frame = QFrame()
        main_frame.setObjectName("MainWhiteFrame")
        main_frame_layout = QVBoxLayout(main_frame)
        main_frame_layout.setContentsMargins(0, 0, 0, 0)
        main_frame_layout.setSpacing(0)

        # ── Tabs ──────────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setIconSize(QSize(20, 20))
        self._apply_tab_styles()
        main_frame_layout.addWidget(self.tabs)

        self.tab_stats   = self._create_stats_tab()
        self.tab_liste   = self._create_liste_tab()
        self.tab_attente = self._create_file_attente_tab()
        self.tab_nouveau = self._create_nouveau_tab()

        self.tabs.addTab(self.tab_stats,   self._icon("fa5s.chart-pie"),      "Statistiques")
        self.tabs.addTab(self.tab_liste,   self._icon("fa5s.list"),           "Liste des actes")
        self.tabs.addTab(self.tab_attente, self._icon("fa5s.hourglass-half"), "File d'attente")
        self.tabs.addTab(self.tab_nouveau, self._icon("fa5s.plus-circle"),    "Nouveau")

        # ── Quick actions ─────────────────────────────────────────────────────
        self.quick_actions = QuickActions()
        main_frame_layout.addWidget(self.quick_actions)

        main_layout.addWidget(main_frame)
        self._style_main_frame(main_frame)

    # ── Onglet Statistiques ───────────────────────────────────────────────────
    def _create_stats_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 8, 0, 8)
        inner_layout.setSpacing(8)

        self.kpi_section   = KpiCardsSection()
        self.charts_section = ChartsSection()

        inner_layout.addWidget(self.kpi_section)
        inner_layout.addWidget(self.charts_section)
        inner_layout.addStretch()

        scroll.setWidget(inner)
        layout.addWidget(scroll)
        return tab

    # ── Onglet Liste ──────────────────────────────────────────────────────────
    def _create_liste_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 8)
        self.actes_table = ActesTable(self.ctrl)
        layout.addWidget(self.actes_table)
        return tab

    # ── Onglet File d'attente ─────────────────────────────────────────────────
    def _create_file_attente_tab(self) -> QWidget:
        from PySide6.QtWidgets import QScrollArea
        import qtawesome as qta

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # ── Barre de titre + bouton refresh ──────────────────────────────────
        header_frame = QFrame()
        header_frame.setObjectName("FileAttenteHeader")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 10, 16, 10)

        self._lbl_patient_count = QLabel("Chargement…")
        self._lbl_patient_count.setObjectName("FileAttenteTitle")

        btn_refresh = QPushButton("  Actualiser")
        btn_refresh.setIcon(qta.icon("fa5s.sync-alt", color="white"))
        btn_refresh.setObjectName("BtnRefreshFile")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setFixedHeight(34)
        btn_refresh.clicked.connect(self._update_file_attente)

        header_layout.addWidget(self._lbl_patient_count)
        header_layout.addStretch()
        header_layout.addWidget(btn_refresh)
        layout.addWidget(header_frame)

        # ── Zone scrollable des cartes patients ───────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setSpacing(10)
        self._cards_layout.setContentsMargins(0, 4, 0, 4)
        self._cards_layout.addStretch()

        scroll.setWidget(self._cards_container)
        layout.addWidget(scroll)

        # ── État clignotement  (liste de (label, style_on, style_off)) ───────
        self._blink_widgets = []
        self._blink_state   = True
        return tab

    # ── Onglet Nouveau ────────────────────────────────────────────────────────
    def _create_nouveau_tab(self) -> QWidget:
        """Formulaire compact — icônes seules, 3 colonnes, sans titres de section."""
        import qtawesome as qta

        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)

        # ── En-tête ───────────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("NouveauPageHeader")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 6, 20, 6)
        hl.setSpacing(12)

        icon_box = QLabel()
        icon_box.setFixedSize(36, 36)
        icon_box.setObjectName("NouveauPageIcon")
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setPixmap(qta.icon("fa5s.clipboard-list", color="white").pixmap(18, 18))

        texts = QVBoxLayout()
        texts.setSpacing(1)
        title_lbl = QLabel("Enregistrement d'un Acte Médical")
        title_lbl.setObjectName("NouveauPageTitle")
        sub_lbl = QLabel("Remplir les informations de l'acte")
        sub_lbl.setObjectName("NouveauPageSub")
        texts.addWidget(title_lbl)
        texts.addWidget(sub_lbl)

        hl.addWidget(icon_box)
        hl.addLayout(texts)
        hl.addStretch()
        tab_layout.addWidget(header)

        # ── Corps ─────────────────────────────────────────────────────────────
        body = QWidget()
        body.setObjectName("NouveauBody")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(20, 12, 20, 8)
        bl.setSpacing(0)

        g = QGridLayout()
        g.setHorizontalSpacing(12)
        g.setVerticalSpacing(4)
        g.setColumnStretch(0, 1)
        g.setColumnStretch(1, 1)
        g.setColumnStretch(2, 1)

        # ── Ligne 1 : Code Acte | Consultation | Type d'acte ──────────────────
        g.addWidget(self._icon_lbl(qta, "fa5s.tag",         "#EF4444", "Code Acte *"),        0, 0)
        g.addWidget(self._icon_lbl(qta, "fa5s.stethoscope", "#2563EB", "Consultation *"),     0, 1)
        g.addWidget(self._icon_lbl(qta, "fa5s.list",        "#D97706", "Type d'acte *"),      0, 2)
        self.form_code_acte   = self._nouveau_input("Code acte")
        self.form_consultation = self._nouveau_combo("Consultation")
        self.form_type_acte   = self._nouveau_combo("Type")
        self.form_type_acte.addItems(["examen", "chirurgie", "lunette", "prescription"])
        g.addWidget(self.form_code_acte,    1, 0)
        g.addWidget(self.form_consultation, 1, 1)
        g.addWidget(self.form_type_acte,    1, 2)

        # ── Ligne 2 : Choix patient | Mode réalisation | Statut ───────────────
        g.addWidget(self._icon_lbl(qta, "fa5s.user-check", "#D97706", "Choix patient *"),    2, 0)
        g.addWidget(self._icon_lbl(qta, "fa5s.cog",        "#2563EB", "Mode réalisation (auto)"), 2, 1)
        g.addWidget(self._icon_lbl(qta, "fa5s.shield-alt", "#7C3AED", "Statut acte (auto)"),      2, 2)
        self.form_choix  = self._nouveau_combo("Choix patient")
        self.form_choix.addItems(["maintenant", "plus_tard", "ailleurs"])
        self.form_mode   = self._nouveau_combo("Mode réalisation")
        self.form_mode.addItems(["interne", "externe"])
        self.form_mode.setEnabled(False)  # Lecture seule (défini automatiquement)
        self.form_statut = self._nouveau_combo("Statut")
        # Seuls les statuts initiaux sont sélectionnables manuellement
        # en_cours et termine sont gérés automatiquement par demarrer_passage() et terminer_passage()
        self.form_statut.addItems(["en_attente", "planifie", "refuse"])
        self.form_statut.setEnabled(False)  # Lecture seule (défini automatiquement)
        g.addWidget(self.form_choix,  3, 0)
        g.addWidget(self.form_mode,   3, 1)
        g.addWidget(self.form_statut, 3, 2)

        # ── Ligne 3 : Décision médicale | Raison du refus (2 colonnes) ────────
        g.addWidget(self._icon_lbl(qta, "fa5s.file-medical",  "#059669", "Décision médicale *"), 4, 0)
        g.addWidget(self._icon_lbl(qta, "fa5s.times-circle",  "#EF4444", "Raison du refus"),     4, 1, 1, 2)
        self.form_decision = self._nouveau_textarea("Décision médicale")
        self.form_raison   = self._nouveau_textarea("Raison du refus (si applicable)")
        g.addWidget(self.form_decision, 5, 0)
        g.addWidget(self.form_raison,   5, 1, 1, 2)

        # ── Ligne 4 : Session | Personnel ────────────────────────────────────
        g.addWidget(self._icon_lbl(qta, "fa5s.graduation-cap",    "#D97706", "Session *"),   6, 0)
        g.addWidget(self._icon_lbl(qta, "fa5s.users",             "#2563EB", "Personnel *"), 6, 1)
        self.form_session    = self._nouveau_combo("Session")
        self.form_personnel  = self._nouveau_combo("Personnel")
        g.addWidget(self.form_session,   7, 0)
        g.addWidget(self.form_personnel, 7, 1)

        # La ligne des textareas s'étire pour remplir l'espace disponible
        g.setRowStretch(5, 1)

        bl.addLayout(g, 1)
        tab_layout.addWidget(body, 1)

        # ── Pied de page ──────────────────────────────────────────────────────
        footer = QWidget()
        footer.setObjectName("NouveauFooter")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(20, 6, 20, 6)
        fl.setSpacing(8)
        fl.addStretch()

        self.form_btn_cancel = QPushButton("  Annuler")
        self.form_btn_cancel.setObjectName("NouveauBtnCancel")
        self.form_btn_cancel.setFixedHeight(34)
        self.form_btn_cancel.setCursor(Qt.PointingHandCursor)
        self.form_btn_cancel.setIcon(qta.icon("fa5s.times", color="#6B7280"))
        self.form_btn_cancel.clicked.connect(self._reset_nouveau_form)

        self.form_btn_save = QPushButton("  Enregistrer")
        self.form_btn_save.setObjectName("NouveauBtnSave")
        self.form_btn_save.setFixedHeight(34)
        self.form_btn_save.setCursor(Qt.PointingHandCursor)
        self.form_btn_save.setIcon(qta.icon("fa5s.clipboard-list", color="white"))
        self.form_btn_save.clicked.connect(self._save_nouveau_form)

        fl.addWidget(self.form_btn_cancel)
        fl.addWidget(self.form_btn_save)
        tab_layout.addWidget(footer)

        return tab

    # ── Helpers constructeurs champs ──────────────────────────────────────────

    def _nouveau_section_header(self, title: str, icon_name: str, color: str) -> QWidget:
        """En-tête de section avec icône colorée et ligne de séparation."""
        import qtawesome as qta
        w = QWidget()
        hl = QHBoxLayout(w)
        hl.setContentsMargins(0, 2, 0, 0)
        hl.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(20, 20)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setPixmap(qta.icon(icon_name, color="white").pixmap(11, 11))
        icon_lbl.setStyleSheet(
            f"background:{color};border-radius:10px;border:none;"
        )

        txt_lbl = QLabel(title)
        txt_lbl.setStyleSheet(
            f"font-size:11px;font-weight:700;color:{color};background:transparent;"
        )

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background:{color};border:none;")

        hl.addWidget(icon_lbl)
        hl.addWidget(txt_lbl)
        hl.addWidget(line, 1)
        return w

    def _nouveau_field_label(self, text: str, icon_name: str = "",
                              icon_color: str = "", required: bool = False) -> QLabel:
        """Label de champ compact."""
        lbl = QLabel()
        star = " <span style='color:#EF4444;font-weight:700;'>*</span>" if required else ""
        lbl.setText(f"{text}{star}")
        lbl.setTextFormat(Qt.RichText)
        lbl.setStyleSheet(
            "font-size:10px;font-weight:600;color:#374151;background:transparent;"
        )
        return lbl

    def _nouveau_input(self, placeholder: str) -> QLineEdit:
        w = QLineEdit()
        w.setPlaceholderText(placeholder)
        w.setObjectName("NouveauField")
        w.setFixedHeight(32)
        return w

    def _nouveau_combo(self, placeholder: str) -> QComboBox:
        w = QComboBox()
        w.setPlaceholderText(placeholder)
        w.setObjectName("NouveauField")
        w.setFixedHeight(32)
        return w

    def _nouveau_textarea(self, placeholder: str) -> QTextEdit:
        w = QTextEdit()
        w.setPlaceholderText(placeholder)
        w.setObjectName("NouveauField")
        w.setMinimumHeight(60)
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return w

    def _icon_lbl(self, qta, icon_name: str, color: str, tooltip: str = "") -> QLabel:
        """Label icône seule (avec tooltip) pour les champs du formulaire."""
        lbl = QLabel()
        lbl.setFixedSize(18, 18)
        lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(13, 13))
        lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lbl.setStyleSheet("background:transparent;")
        if tooltip:
            lbl.setToolTip(tooltip)
        return lbl

    # =========================================================================
    # CONNEXIONS
    # =========================================================================

    def connect_signals(self):
        # Table principale
        self.actes_table.new_clicked.connect(self.on_new_acte)
        self.actes_table.view_clicked.connect(self.on_view_acte)
        self.actes_table.edit_clicked.connect(self.on_edit_acte)
        self.actes_table.delete_clicked.connect(self.on_delete_acte)
        self.actes_table.choix_clicked.connect(self.on_choix_patient)

        # Quick actions
        self.quick_actions.new_acte_clicked.connect(self.on_new_acte)
        self.quick_actions.file_attente_clicked.connect(lambda: self.tabs.setCurrentIndex(2))

        # Chargement des combos quand l'onglet Nouveau est affiché
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.quick_actions.planifies_clicked.connect(self._show_planifies)
        self.quick_actions.parcours_clicked.connect(self._show_parcours)
        self.quick_actions.export_clicked.connect(self._on_export)
        
        # Liaison automatique : choix_patient → mode_realisation + statut_acte
        self.form_choix.currentTextChanged.connect(self._on_choix_patient_changed)

    # =========================================================================
    # CHARGEMENT DES DONNÉES
    # =========================================================================

    def load_data(self):
        """Charge tous les actes et met à jour les composants."""
        try:
            actes_obj = self.ctrl.lister_par_statut(None) if hasattr(self.ctrl, "lister_tous") \
                        else self._lister_tous()
            actes = [_acte_to_dict(a) for a in actes_obj]
        except Exception as e:
            self.logger.warning("Impossible de charger les actes : %s", e)
            actes = []

        self.actes_table.load_actes(actes)
        self._update_kpis(actes)
        self._update_charts(actes)
        self._update_file_attente()

    def _lister_tous(self) -> list:
        """Agrège tous les statuts."""
        result = []
        for statut in ("en_attente", "planifie", "en_cours", "termine", "refuse"):
            try:
                result += self.ctrl.lister_par_statut(statut) or []
            except Exception:
                pass
        return result

    def _update_kpis(self, actes: list):
        stats = {}
        for a in actes:
            s = a.get("statut_acte", "inconnu")
            stats[s] = stats.get(s, 0) + 1
        self.kpi_section.update_kpis(stats)

    def _update_charts(self, actes: list):
        stats_type = {}
        stats_stat = {}
        for a in actes:
            t = a.get("type_acte", "autre")
            stats_type[t] = stats_type.get(t, 0) + 1
            s = a.get("statut_acte", "autre")
            stats_stat[s] = stats_stat.get(s, 0) + 1
        self.charts_section.update_charts(stats_type, stats_stat)

    def _toggle_blink(self):
        """Inverse l'état du clignotement sur tous les chips actifs."""
        self._blink_state = not self._blink_state
        for lbl, style_on, style_off in self._blink_widgets:
            try:
                lbl.setStyleSheet(style_on if self._blink_state else style_off)
            except RuntimeError:
                pass  # widget déjà détruit

    def _update_file_attente(self):
        """
        Reconstruit les cartes de suivi des patients actifs.
        — Une carte par patient (groupé par code_visite).
        — Pipeline horizontal des étapes avec clignotement sur l'étape courante.
        — Durée écoulée sur l'étape courante + durées passées sur les étapes terminées.
        """
        from datetime import datetime
        now = datetime.now()

        # Vider les cartes existantes
        self._blink_widgets.clear()
        while self._cards_layout.count() > 0:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards_layout.addStretch()

        # Charger les données
        raw = []
        try:
            raw = self.ctrl.get_suivi_file_attente() or []
        except Exception as e:
            self.logger.warning("Erreur suivi file attente: %s", e)

        if not raw:
            empty = QLabel("✓   Aucun patient en attente actuellement")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                "color:#6B7280;font-size:14px;padding:48px;background:transparent;"
            )
            self._cards_layout.insertWidget(0, empty)
            self._lbl_patient_count.setText("File d'attente vide")
            return

        # Grouper par visite (un dict par patient)
        patients: dict = {}
        for row in raw:
            cv = row.get('code_visite')
            if cv not in patients:
                patients[cv] = {
                    'code_visite'   : cv,
                    'code_patient'  : row.get('code_patient'),
                    'nom'           : row.get('nom', ''),
                    'prenom'        : row.get('prenom', ''),
                    'date_visite'   : row.get('date_visite'),
                    'statut_patient': row.get('statut_patient', ''),
                    'urgent'        : bool(row.get('urgent', 0)),
                    'actes'         : [],
                }
            code_acte = row.get('code_acte')
            if code_acte:
                existing = [a['code_acte'] for a in patients[cv]['actes']]
                if code_acte not in existing:
                    patients[cv]['actes'].append({
                        'code_acte'          : code_acte,
                        'type_acte'          : row.get('type_acte'),
                        'decision_medicale'  : row.get('decision_medicale'),
                        'statut_acte'        : row.get('statut_acte'),
                        'date_entre'         : row.get('date_entre'),
                        'date_debut_execution': row.get('date_debut_execution'),
                        'date_sortie'        : row.get('date_sortie'),
                    })

        n = len(patients)
        self._lbl_patient_count.setText(
            f"Suivi en temps réel  —  {n} patient{'s' if n > 1 else ''} "
            f"actif{'s' if n > 1 else ''}"
        )
        for i, patient in enumerate(patients.values()):
            card = self._build_patient_card(patient, now)
            self._cards_layout.insertWidget(i, card)

    # ── Construction des cartes patients ──────────────────────────────────────

    # Séquence globale des statuts patients (ordre chronologique)
    _STAGE_SEQUENCE = [
        ("Attente consultation", "Att. consultation", False),
        ("En consultation",      "Consultation",      True),
        ("Attente examen",       "Att. examen",       False),
        ("En examen",            "Examen",            True),
        ("Examen terminé",       "Examen fini",       False),
        ("Attente chirurgie",    "Att. chirurgie",    False),
        ("En chirurgie",         "Chirurgie",         True),
        ("Chirurgie terminée",   "Chir. finie",       False),
        ("Attente pharmacie",    "Att. pharmacie",    False),
        ("En pharmacie",         "Pharmacie",         True),
        ("Pharmacie terminée",   "Pharm. finie",      False),
        ("Attente lunette",      "Att. lunette",      False),
        ("En lunette",           "Lunette",           True),
        ("Lunette terminée",     "Lun. finie",        False),
        ("Attente payement",     "Att. paiement",     False),
    ]
    # type_acte → (clé "attente", clé "en cours", clé "terminé") dans _STAGE_SEQUENCE
    _TYPE_TO_STAGES = {
        "examen"      : ("Attente examen",     "En examen",    "Examen terminé"),
        "chirurgie"   : ("Attente chirurgie",  "En chirurgie", "Chirurgie terminée"),
        "prescription": ("Attente pharmacie",  "En pharmacie", "Pharmacie terminée"),
        "lunette"     : ("Attente lunette",    "En lunette",   "Lunette terminée"),
    }
    # Ensemble des statuts "terminé" en attente de décision médecin
    _STATUTS_TERMINE = {"examen terminé", "chirurgie terminée", "pharmacie terminée", "lunette terminée", "consultation terminée"}

    @staticmethod
    def _fmt_mins(dt_start, dt_end=None) -> str:
        """Formate une durée en minutes/heures entre deux datetimes."""
        if dt_start is None:
            return "—"
        from datetime import datetime
        end = dt_end or datetime.now()
        mins = int((end - dt_start).total_seconds() / 60)
        if mins < 60:
            return f"{mins} min"
        return f"{mins // 60}h{mins % 60:02d}"

    def _build_patient_card(self, patient: dict, now) -> QWidget:
        """Ligne compacte sans cadre : nom · heure · durée totale  +  barre pipeline + boutons d'action."""
        import qtawesome as qta
        c = theme_manager.colors()

        row_widget = QWidget()
        row_widget.setStyleSheet("background:transparent;")
        vb = QVBoxLayout(row_widget)
        vb.setContentsMargins(8, 3, 8, 4)
        vb.setSpacing(2)

        # ── En-tête : nom + heure d'arrivée ──────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(6)
        header.setContentsMargins(0, 0, 0, 0)

        if patient.get('urgent'):
            bolt = QLabel()
            bolt.setPixmap(qta.icon("fa5s.bolt", color="#F59E0B").pixmap(10, 10))
            bolt.setStyleSheet("background:transparent;")
            header.addWidget(bolt)

        name_lbl = QLabel(
            f"{patient['nom'].upper()} {patient['prenom'].capitalize()}"
        )
        name_lbl.setStyleSheet(
            f"font-size:11px;font-weight:700;"
            f"color:{c['text_primary']};background:transparent;"
        )

        dv = patient.get('date_visite')
        arrival = dv.strftime("%H:%M") if dv and hasattr(dv, 'strftime') else "—"
        total   = self._fmt_mins(dv, now) if dv else "—"

        info_lbl = QLabel(f"{arrival}  ·  {total}")
        info_lbl.setStyleSheet(
            f"font-size:9px;color:{c['text_secondary']};background:transparent;"
        )

        # Couleur et texte du statut
        statut_raw = patient.get('statut_patient', '')
        statut_lower = statut_raw.lower()
        if 'en cours' in statut_lower or statut_lower.startswith('en '):
            statut_color = "#3B82F6"   # bleu — en cours
        elif 'attente' in statut_lower:
            statut_color = "#F59E0B"   # orange — en attente
        else:
            statut_color = c['text_secondary']

        statut_lbl = QLabel(statut_raw)
        statut_lbl.setStyleSheet(
            f"font-size:8px;font-weight:700;color:{statut_color};background:transparent;"
        )

        header.addWidget(name_lbl)
        header.addSpacing(8)
        header.addWidget(info_lbl)
        header.addStretch()
        header.addWidget(statut_lbl)
        vb.addLayout(header)

        # ── Barre pipeline ────────────────────────────────────────────────────
        vb.addWidget(self._build_pipeline_widget(patient, now))
        
        # ── Boutons d'action ──────────────────────────────────────────────────
        statut_lower = patient.get('statut_patient', '').lower()
        
        if 'attente consultation' in statut_lower:
            # Patient attend la consultation
            vb.addWidget(self._build_consultation_buttons(patient, c))
        elif statut_lower in self._STATUTS_TERMINE:
            # Acte terminé → décision médecin (nouvel acte ou aller en paiement)
            vb.addWidget(self._build_decision_medecin_buttons(patient, c))
        elif 'attente payement' in statut_lower or 'attente rendez-vous' in statut_lower:
            # Patient en attente de paiement ou de rendez-vous :
            # l'acte n'a pas encore démarré, aucun bouton "Démarrer" à afficher.
            # Le bouton Démarrer n'apparaîtra que quand le RDV arrive et que
            # statut_patient passe en "Attente examen/chirurgie/etc."
            pass
        else:
            # Patient en file d'attente ou en cours d'un acte
            acte_actif = self._trouver_acte_actif(patient)
            if acte_actif:
                vb.addWidget(self._build_action_buttons(acte_actif, c))

        # ── Séparateur fin ────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{c['border']};border:none;")
        vb.addWidget(sep)

        return row_widget
    
    def _build_decision_medecin_buttons(self, patient: dict, c: dict) -> QWidget:
        """
        Boutons affichés quand un acte est terminé (statut = 'X terminé').
        Le médecin choisit : créer un autre acte ou valider la séance et aller en paiement.
        """
        import qtawesome as qta

        container = QWidget()
        container.setStyleSheet("background:transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 2)
        layout.setSpacing(8)

        code_visite = patient.get('code_visite')
        code_consultation = None
        
        # Récupérer code_consultation via le contrôleur
        if code_visite:
            try:
                code_consultation = self.ctrl.obtenir_consultation_par_visite(code_visite)
            except Exception as e:
                self.logger.warning(f"Erreur récupération consultation: {e}")

        statut_lower_loc = patient.get('statut_patient', '').lower()
        # Étiquette d'info
        if "consultation terminée" in statut_lower_loc:
            lbl_text = "Consultation terminée — Décision médecin :"
        else:
            lbl_text = "Acte terminé — Décision médecin :"
        lbl = QLabel(lbl_text)
        lbl.setStyleSheet(
            f"font-size:9px;font-weight:600;color:{c['text_secondary']};background:transparent;"
        )
        layout.addWidget(lbl)
        layout.addSpacing(6)

        # Bouton "Nouvel acte"
        if code_consultation:
            btn_new = QPushButton("  Nouvel acte")
            btn_new.setIcon(qta.icon("fa5s.plus", color="white"))
            btn_new.setObjectName("BtnNewActe")
            btn_new.setFixedHeight(28)
            btn_new.setCursor(Qt.PointingHandCursor)
            btn_new.setStyleSheet("""
                QPushButton#BtnNewActe {
                    background:#10B981;color:white;border:none;
                    border-radius:6px;font-size:10px;font-weight:600;
                    padding:0 12px;
                }
                QPushButton#BtnNewActe:hover { background:#059669; }
            """)
            btn_new.clicked.connect(lambda chk=False, cc=code_consultation: self._filtrer_par_consultation(cc))
            layout.addWidget(btn_new)
        else:
            self.logger.warning(f"Code consultation non trouvé pour visite {code_visite}")

        # Bouton "Aller en paiement"
        if code_visite:
            btn_pay = QPushButton("  Aller en paiement")
            btn_pay.setIcon(qta.icon("fa5s.cash-register", color="white"))
            btn_pay.setObjectName("BtnGoPaiement")
            btn_pay.setFixedHeight(28)
            btn_pay.setCursor(Qt.PointingHandCursor)
            btn_pay.setStyleSheet("""
                QPushButton#BtnGoPaiement {
                    background:#3B82F6;color:white;border:none;
                    border-radius:6px;font-size:10px;font-weight:600;
                    padding:0 12px;
                }
                QPushButton#BtnGoPaiement:hover { background:#2563EB; }
            """)
            btn_pay.clicked.connect(lambda chk=False, cv=code_visite: self._valider_sejour(cv))
            layout.addWidget(btn_pay)

        # Bouton "Contrôle" — patient revient pour un contrôle du même acte
        actes = patient.get('actes', [])
        if actes:
            code_acte_ctrl = actes[0].get('code_acte')
            if code_acte_ctrl:
                btn_ctrl = QPushButton("  Contrôle")
                btn_ctrl.setIcon(qta.icon("fa5s.redo", color="white"))
                btn_ctrl.setObjectName("BtnControle")
                btn_ctrl.setFixedHeight(28)
                btn_ctrl.setCursor(Qt.PointingHandCursor)
                btn_ctrl.setStyleSheet("""
                    QPushButton#BtnControle {
                        background:#8B5CF6;color:white;border:none;
                        border-radius:6px;font-size:10px;font-weight:600;
                        padding:0 12px;
                    }
                    QPushButton#BtnControle:hover { background:#7C3AED; }
                """)
                btn_ctrl.clicked.connect(
                    lambda chk=False, ca=code_acte_ctrl: self._enregistrer_controle(ca)
                )
                layout.addWidget(btn_ctrl)

        layout.addStretch()
        return container

    def _trouver_acte_actif(self, patient: dict) -> dict | None:
        """
        Trouve l'acte correspondant au statut courant du patient.
        Utile quand un patient a plusieurs actes (ex: examen terminé + prescription en attente).
        """
        statut = patient.get('statut_patient', '').lower()
        actes  = patient.get('actes', [])
        if not actes:
            return None

        # 1. Chercher l'acte de type correspondant au statut courant, non terminé
        for type_acte, (att_key, enc_key, _fin_key) in self._TYPE_TO_STAGES.items():
            if statut in (att_key.lower(), enc_key.lower()):
                for acte in actes:
                    if (acte.get('type_acte', '').lower() == type_acte
                            and acte.get('date_sortie') is None):
                        return acte

        # 2. Fallback : premier acte non terminé (date_sortie = None)
        for acte in actes:
            if acte.get('date_sortie') is None:
                return acte

        # 3. Dernier recours : premier acte de la liste
        return actes[0]

    def _valider_sejour(self, code_visite: str):
        """Passe le patient en 'Attente payement' (fin de séance)."""
        ok, msg = self.ctrl.valider_sejour_patient(code_visite)
        if ok:
            # Mise à jour INSTANTANÉE de la file d'attente
            self._update_file_attente()
            self.load_data()
            
            CustomMessageBox.success(self, "Séance terminée",
                                     "Le patient est passé en Attente paiement.")
        else:
            CustomMessageBox.warning(self, "Erreur", str(msg))

    def _enregistrer_controle(self, code_acte: str):
        """
        Enregistre l'arrivée du patient pour une visite de contrôle.
        Crée une nouvelle visite + acte_visite(role='controle').
        Le patient va directement au service (Attente examen/chirurgie/etc.).
        """
        # Récupérer la session active depuis le dashboard
        code_session = None
        try:
            dashboard = self._trouver_dashboard_parent()
            if dashboard and hasattr(dashboard, 'visite_ctrl'):
                _, code_session = dashboard.visite_ctrl.verifier_session_active()
        except Exception:
            pass

        if not code_session:
            CustomMessageBox.warning(
                self, "Session requise",
                "Aucune session active. Veuillez démarrer une session avant d'enregistrer un contrôle."
            )
            return

        ok, result = self.ctrl.enregistrer_controle(code_acte, code_session)
        if ok:
            # Mise à jour INSTANTANÉE de la file d'attente
            self._update_file_attente()
            self.load_data()
            
            CustomMessageBox.success(
                self, "Contrôle enregistré",
                f"Le patient a été placé en file d'attente pour le contrôle (visite {result})."
            )
        else:
            CustomMessageBox.warning(self, "Erreur", str(result))

    def _build_consultation_buttons(self, patient: dict, c: dict) -> QWidget:
        """Construit le bouton pour démarrer la consultation."""
        import qtawesome as qta
        
        container = QWidget()
        container.setStyleSheet("background:transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 2)
        layout.setSpacing(6)
        layout.addStretch()
        
        code_visite = patient.get('code_visite')
        
        # Bouton Démarrer consultation
        if code_visite:
            btn_start = QPushButton("  Démarrer consultation")
            btn_start.setIcon(qta.icon("fa5s.play", color="white"))
            btn_start.setObjectName("BtnStartConsultation")
            btn_start.setFixedHeight(28)
            btn_start.setCursor(Qt.PointingHandCursor)
            btn_start.setStyleSheet(f"""
                QPushButton#BtnStartConsultation {{
                    background:#10B981;color:white;border:none;
                    border-radius:6px;font-size:10px;font-weight:600;
                    padding:0 12px;
                }}
                QPushButton#BtnStartConsultation:hover {{
                    background:#059669;
                }}
            """)
            btn_start.clicked.connect(lambda: self._demarrer_consultation(code_visite))
            layout.addWidget(btn_start)
        
        layout.addStretch()
        return container
    
    def _build_action_buttons(self, acte: dict, c: dict) -> QWidget:
        """Construit les boutons d'action selon l'état de l'acte."""
        import qtawesome as qta
        
        container = QWidget()
        container.setStyleSheet("background:transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 2)
        layout.setSpacing(6)
        layout.addStretch()
        
        id_acte_visite = acte.get('code_acte')
        date_debut = acte.get('date_debut_execution')
        date_sortie = acte.get('date_sortie')
        
        # Bouton Démarrer (visible si date_debut_execution est NULL)
        if id_acte_visite and date_debut is None:
            btn_start = QPushButton("  Démarrer")
            btn_start.setIcon(qta.icon("fa5s.play", color="white"))
            btn_start.setObjectName("BtnStartPassage")
            btn_start.setFixedHeight(28)
            btn_start.setCursor(Qt.PointingHandCursor)
            btn_start.setStyleSheet(f"""
                QPushButton#BtnStartPassage {{
                    background:#10B981;color:white;border:none;
                    border-radius:6px;font-size:10px;font-weight:600;
                    padding:0 12px;
                }}
                QPushButton#BtnStartPassage:hover {{
                    background:#059669;
                }}
            """)
            btn_start.clicked.connect(lambda: self._demarrer_passage(id_acte_visite))
            layout.addWidget(btn_start)
        
        # Bouton Terminer (visible si date_debut_execution != NULL ET date_sortie = NULL)
        if id_acte_visite and date_debut is not None and date_sortie is None:
            # Récupérer le type d'acte pour savoir quel formulaire ouvrir
            type_acte = acte.get('type_acte', '').lower()
            
            btn_end = QPushButton("  Terminer")
            btn_end.setIcon(qta.icon("fa5s.check", color="white"))
            btn_end.setObjectName("BtnEndPassage")
            btn_end.setFixedHeight(28)
            btn_end.setCursor(Qt.PointingHandCursor)
            btn_end.setStyleSheet(f"""
                QPushButton#BtnEndPassage {{
                    background:#3B82F6;color:white;border:none;
                    border-radius:6px;font-size:10px;font-weight:600;
                    padding:0 12px;
                }}
                QPushButton#BtnEndPassage:hover {{
                    background:#2563EB;
                }}
            """)
            # Connecter selon le type d'acte
            if type_acte == 'examen':
                btn_end.clicked.connect(lambda: self._ouvrir_formulaire_examen(id_acte_visite))
            elif type_acte == 'chirurgie':
                btn_end.clicked.connect(lambda: self._ouvrir_formulaire_chirurgie(id_acte_visite))
            elif type_acte == 'lunette':
                btn_end.clicked.connect(lambda: self._ouvrir_formulaire_lunette(id_acte_visite))
            elif type_acte == 'prescription':
                btn_end.clicked.connect(lambda: self._ouvrir_formulaire_prescription(id_acte_visite))
            else:
                # Par défaut, terminer directement
                btn_end.clicked.connect(lambda: self._terminer_passage(id_acte_visite))
            layout.addWidget(btn_end)
        
        # Bouton Détails (toujours visible)
        if id_acte_visite:
            btn_details = QPushButton("  Détails")
            btn_details.setIcon(qta.icon("fa5s.info-circle", color=c['text_secondary']))
            btn_details.setObjectName("BtnDetailsPassage")
            btn_details.setFixedHeight(28)
            btn_details.setCursor(Qt.PointingHandCursor)
            btn_details.setStyleSheet(f"""
                QPushButton#BtnDetailsPassage {{
                    background:{c['bg_card']};color:{c['text_secondary']};
                    border:1px solid {c['border']};border-radius:6px;
                    font-size:10px;font-weight:600;padding:0 12px;
                }}
                QPushButton#BtnDetailsPassage:hover {{
                    background:{c['hover']};color:{c['text_primary']};
                }}
            """)
            btn_details.clicked.connect(lambda: self.on_view_acte({'id_acte': id_acte_visite}))
            layout.addWidget(btn_details)
        
        layout.addStretch()
        return container

    def _build_pipeline_widget(self, patient: dict, now) -> QWidget:
        """
        Barre ultra-compacte : durée flottante au-dessus du rond courant,
        puis ronds reliés par une ligne fine. Aucun cadre, aucune couleur de fond.
        """
        from PySide6.QtWidgets import QSizePolicy
        statut = patient.get('statut_patient', '').strip()
        actes  = patient.get('actes', [])
        dv     = patient.get('date_visite')

        has = {a['type_acte'] for a in actes if a.get('type_acte')}
        relevant_keys = ["Attente consultation", "En consultation"]
        for type_key, stages in self._TYPE_TO_STAGES.items():
            if type_key in has:
                relevant_keys += list(stages)  # (att, enc, terminé)
        seen = set()
        ordered_keys = []
        for k in relevant_keys:
            if k not in seen:
                ordered_keys.append(k)
                seen.add(k)
        ordered_keys.append("Attente payement")

        statut_lower = statut.lower()
        current_idx = -1
        for i, key in enumerate(ordered_keys):
            if key.lower() == statut_lower:
                current_idx = i
                break

        stages_meta = []
        for i, key in enumerate(ordered_keys):
            if i < current_idx:
                # Marquer en vert uniquement si l'étape a réellement eu lieu
                # (vérifié par les timestamps dans les actes)
                if self._stage_was_actually_done(key, actes):
                    stages_meta.append(('done',   self._past_stage_duration(key, actes, dv), key))
                else:
                    # Étape contournée (ex : planifiée via RDV sans passer par le service)
                    stages_meta.append(('future', None, key))
            elif i == current_idx:
                stages_meta.append(('current', self._current_stage_duration(key, actes, dv, now), key))
            else:
                stages_meta.append(('future',  None, key))

        CIRCLE = 20

        container = QWidget()
        container.setStyleSheet("background:transparent;")
        outer = QVBoxLayout(container)
        outer.setContentsMargins(2, 0, 2, 0)
        outer.setSpacing(1)

        # Rangée durée : label seulement au-dessus du rond courant, espaceurs sinon
        dur_row = QHBoxLayout()
        dur_row.setContentsMargins(0, 0, 0, 0)
        dur_row.setSpacing(0)

        # Rangée ronds : cercles + lignes connectrices
        dots_row = QHBoxLayout()
        dots_row.setContentsMargins(0, 0, 0, 0)
        dots_row.setSpacing(0)

        DUR_H = 12  # hauteur fixe de la rangée durée

        for i, (state, dur, key) in enumerate(stages_meta):
            # -- Slot durée (fixe NODE_W, vide sauf pour current) --
            if state == 'current' and dur:
                is_waiting = key.lower().startswith("attente")
                dur_color  = "#D97706" if is_waiting else "#3B82F6"
                d = QLabel(str(dur))
                d.setAlignment(Qt.AlignCenter)
                d.setFixedHeight(DUR_H)
                d.setMinimumWidth(CIRCLE)
                d.setStyleSheet(
                    f"font-size:8px;font-weight:700;color:{dur_color};"
                    f"background:transparent;"
                )
                dur_row.addWidget(d, 0, Qt.AlignHCenter)
            else:
                sp = QWidget()
                sp.setFixedHeight(DUR_H)
                sp.setMinimumWidth(CIRCLE)
                sp.setStyleSheet("background:transparent;")
                dur_row.addWidget(sp, 0)

            # -- Rond --
            circle = self._make_dot_circle(state, key, CIRCLE)
            dot_wrap = QWidget()
            dot_wrap.setFixedWidth(CIRCLE)
            dot_wrap.setStyleSheet("background:transparent;")
            dw = QHBoxLayout(dot_wrap)
            dw.setContentsMargins(0, 0, 0, 0)
            dw.addWidget(circle)
            dots_row.addWidget(dot_wrap, 0, Qt.AlignVCenter)

            if i < len(stages_meta) - 1:
                # Espaceur expandable dans dur_row
                sp2 = QWidget()
                sp2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                sp2.setFixedHeight(DUR_H)
                sp2.setStyleSheet("background:transparent;")
                dur_row.addWidget(sp2, 1)

                # Ligne connectrice dans dots_row
                line = QFrame()
                line.setFixedHeight(2)
                line.setMinimumWidth(6)
                line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                line.setStyleSheet(
                    f"background:{'#10B981' if state == 'done' else '#E2E8F0'};border:none;"
                )
                dots_row.addWidget(line, 1, Qt.AlignVCenter)

        outer.addLayout(dur_row)
        outer.addLayout(dots_row)
        return container

    def _make_dot_circle(self, state: str, key: str, size: int = 20) -> QLabel:
        """Retourne un QLabel circulaire (icône qtawesome) sans aucun texte ni cadre externe."""
        import qtawesome as qta
        radius = size // 2
        is_waiting = key.lower().startswith("attente")

        circle = QLabel()
        circle.setFixedSize(size, size)
        circle.setAlignment(Qt.AlignCenter)

        icon_size = max(size - 10, 6)

        if state == 'done':
            circle.setPixmap(qta.icon("fa5s.check", color="white").pixmap(icon_size, icon_size))
            circle.setStyleSheet(
                f"QLabel{{background:#10B981;border-radius:{radius}px;border:none;}}"
            )
        elif state == 'current':
            if is_waiting:
                px    = qta.icon("fa5s.clock", color="white").pixmap(icon_size, icon_size)
                s_on  = f"QLabel{{background:#F59E0B;border-radius:{radius}px;border:none;}}"
                s_off = f"QLabel{{background:#FDE68A;border-radius:{radius}px;border:none;}}"
            else:
                px    = qta.icon("fa5s.play",  color="white").pixmap(icon_size - 2, icon_size - 2)
                s_on  = f"QLabel{{background:#3B82F6;border-radius:{radius}px;border:none;}}"
                s_off = f"QLabel{{background:#BFDBFE;border-radius:{radius}px;border:none;}}"
            circle.setPixmap(px)
            circle.setStyleSheet(s_on)
            self._blink_widgets.append((circle, s_on, s_off))
        else:  # future
            circle.setPixmap(qta.icon("fa5s.circle", color="#CBD5E1").pixmap(icon_size - 2, icon_size - 2))
            circle.setStyleSheet(
                f"QLabel{{background:#F1F5F9;border-radius:{radius}px;border:none;}}"
            )

        return circle

    def _stage_was_actually_done(self, key: str, actes: list) -> bool:
        """
        Vérifie si une étape a réellement eu lieu grâce aux timestamps.
        Évite d'afficher des étapes en vert quand elles ont été contournées
        (ex : patient planifié via RDV sans passer par le service).
        """
        # La consultation est toujours considérée comme faite si on est dans le pipeline
        if key in ("Attente consultation", "En consultation"):
            return True
        # Pour les étapes de service, vérifier les timestamps de l'acte
        for type_acte, (att_key, enc_key, fin_key) in self._TYPE_TO_STAGES.items():
            acte = next((a for a in actes if a.get('type_acte') == type_acte), None)
            if not acte:
                continue
            if key == att_key:
                return acte.get('date_entre') is not None
            if key == enc_key:
                return acte.get('date_debut_execution') is not None
            if key == fin_key:
                return acte.get('date_sortie') is not None
        # Par défaut (étape inconnue) : on considère faite
        return True

    def _past_stage_duration(self, key: str, actes: list, dv) -> str:
        """Retourne la durée formatée d'une étape terminée."""
        if key == "Attente consultation":
            return None
        if key == "En consultation":
            return None  # pas de timestamp précis pour la fin
        for att_key, enc_key, *_ in self._TYPE_TO_STAGES.values():
            if key == att_key:
                ta = next((k for k, s in self._TYPE_TO_STAGES.items() if s[0] == att_key), None)
                if ta:
                    acte = next((a for a in actes if a.get('type_acte') == ta), None)
                    if acte and acte.get('date_entre') and acte.get('date_debut_execution'):
                        return self._fmt_mins(acte['date_entre'], acte['date_debut_execution'])
            if key == enc_key:
                ta = next((k for k, s in self._TYPE_TO_STAGES.items() if s[1] == enc_key), None)
                if ta:
                    acte = next((a for a in actes if a.get('type_acte') == ta), None)
                    if acte and acte.get('date_debut_execution') and acte.get('date_sortie'):
                        return self._fmt_mins(acte['date_debut_execution'], acte['date_sortie'])
        return None

    def _current_stage_duration(self, key: str, actes: list, dv, now) -> str:
        """Retourne la durée écoulée sur l'étape courante (sans emoji)."""
        if key == "Attente consultation":
            return self._fmt_mins(dv, now) if dv else None
        if key == "En consultation":
            return self._fmt_mins(dv, now) if dv else None
        if key == "Attente payement":
            return None
        for type_acte, stages in self._TYPE_TO_STAGES.items():
            att_key, enc_key = stages[0], stages[1]
            acte = next((a for a in actes if a.get('type_acte') == type_acte), None)
            if not acte:
                continue
            if key == att_key and acte.get('date_entre'):
                return self._fmt_mins(acte['date_entre'], now)
            if key == enc_key and acte.get('date_debut_execution'):
                return self._fmt_mins(acte['date_debut_execution'], now)
        return None

    # =========================================================================
    # ACTIONS
    # =========================================================================

    def on_new_acte(self):
        dlg = ActeFormDialog(self.ctrl, parent=self)
        dlg.saved.connect(self._save_new_acte)
        dlg.exec()

    def _save_new_acte(self, data: dict):
        try:
            from models.model_acte_medicale import ActeMedical
            acte = ActeMedical(
                code_consultation=data["code_consultation"],
                type_acte=data["type_acte"],
                decision_medicale=data["decision_medicale"],
                mode_realisation=data.get("mode_realisation", "interne"),
                source_acte=data.get("source_acte", "consultation"),
                raison_refus=data.get("raison_refus"),
            )
            ok, msg, acte_cree = self.ctrl.creer_acte(acte)
            if ok:
                CustomMessageBox.success(self, "Succès", "Acte médical créé avec succès.")
                self.load_data()
            else:
                CustomMessageBox.warning(self, "Erreur", str(msg))
        except Exception as e:
            self.logger.error("Erreur création acte : %s", e)
            CustomMessageBox.warning(self, "Erreur", str(e))

    def on_view_acte(self, acte_row: dict):
        dlg = DetailActeModal(self, acte_row, self.ctrl)
        dlg.exec()

    def on_edit_acte(self, acte_row: dict):
        id_acte = acte_row.get("id_acte")
        acte_obj = self.ctrl.obtenir_acte(id_acte) if id_acte else None
        dlg = ActeFormDialog(self.ctrl, acte=acte_obj, parent=self)
        dlg.saved.connect(self._save_edit_acte)
        dlg.exec()

    def _save_edit_acte(self, data: dict):
        try:
            id_acte = data.get("id_acte")
            acte_obj = self.ctrl.obtenir_acte(id_acte)
            if not acte_obj:
                CustomMessageBox.warning(self, "Erreur", "Acte introuvable.")
                return
            acte_obj.type_acte         = data["type_acte"]
            acte_obj.decision_medicale = data["decision_medicale"]
            acte_obj.mode_realisation  = data.get("mode_realisation", acte_obj.mode_realisation)
            acte_obj.source_acte       = data.get("source_acte", acte_obj.source_acte)
            acte_obj.raison_refus      = data.get("raison_refus")
            ok, msg = self.ctrl.modifier_acte(acte_obj)
            if ok:
                CustomMessageBox.success(self, "Succès", "Acte mis à jour.")
                self.load_data()
            else:
                CustomMessageBox.warning(self, "Erreur", str(msg))
        except Exception as e:
            CustomMessageBox.warning(self, "Erreur", str(e))

    def on_delete_acte(self, acte_row: dict):
        id_acte = acte_row.get("id_acte")
        confirm = CustomMessageBox.confirm(
            self,
            "Confirmation",
            f"Supprimer l'acte #{id_acte} ? Cette action est irréversible."
        )
        if not confirm:
            return
        ok, msg = self.ctrl.supprimer_acte(id_acte)
        if ok:
            CustomMessageBox.success(self, "Supprimé", "Acte supprimé.")
            self.load_data()
        else:
            CustomMessageBox.warning(self, "Erreur", str(msg))

    def on_choix_patient(self, acte_row: dict):
        dlg = ChoixPatientDialog(self.ctrl, acte_row, parent=self)
        dlg.choix_valide.connect(self._apply_choix_patient)
        dlg.exec()

    def _apply_choix_patient(self, id_acte: int, choix: str, options: dict):
        try:
            ok, msg = self.ctrl.enregistrer_choix_patient(id_acte, choix)
            if not ok:
                CustomMessageBox.warning(self, "Erreur", str(msg))
                return

            # Actions complémentaires selon le choix
            if choix == "maintenant":
                code_visite = options.get("code_visite")
                if code_visite:
                    self.ctrl.entrer_en_file(id_acte, code_visite)

            elif choix == "plus_tard":
                date_rdv = options.get("date_rdv")
                if date_rdv:
                    rdv_ok, rdv_msg = self.ctrl.planifier_rendez_vous(id_acte, date_rdv)
                    if not rdv_ok:
                        CustomMessageBox.warning(
                            self, "Avertissement planification",
                            f"Le choix 'plus tard' a été enregistré, mais :\n{rdv_msg}\n\n"
                            "Vous pouvez créer le rendez-vous manuellement depuis l'interface Rendez-vous."
                        )

            elif choix == "ailleurs":
                raison = options.get("raison")
                if raison:
                    self.ctrl.refuser_acte(id_acte, raison)

            CustomMessageBox.success(self, "Choix enregistré",
                                     f"Choix « {choix} » enregistré pour l'acte #{id_acte}.")
            # Mise à jour INSTANTANÉE de la file d'attente
            self._update_file_attente()
            self.load_data()

        except Exception as e:
            self.logger.error("Erreur choix patient : %s", e)
            CustomMessageBox.warning(self, "Erreur", str(e))

    def _demarrer_consultation(self, code_visite: str):
        """
        Démarre la consultation pour une visite.
        - Renseigne date_debut_consultation
        - Change statut_patient à "En consultation"
        """
        if not code_visite:
            return
        
        try:
            ok, msg = self.ctrl.demarrer_consultation(code_visite)
            
            if ok:
                # Mise à jour INSTANTANÉE de la file d'attente
                self._update_file_attente()
                self.load_data()
                
                CustomMessageBox.success(
                    self, "Démarré",
                    f"Consultation démarrée pour la visite {code_visite}"
                )
            else:
                CustomMessageBox.warning(self, "Impossible de démarrer", str(msg))
        except Exception as e:
            self.logger.error(f"Erreur _demarrer_consultation: {e}")
            CustomMessageBox.warning(self, "Erreur", str(e))

    def _demarrer_passage(self, code_acte: int):
        """
        Démarre un passage depuis la file d'attente :
          - Renseigne date_debut_execution
          - Change statut_passage en en_cours
          - Change statut_acte en en_cours
          - Met à jour statut_patient (Attente X -> En X)
        """
        if code_acte is None:
            return
        ok, msg = self.ctrl.demarrer_passage_par_code_acte(code_acte)
        if ok:
            # Mise à jour INSTANTANÉE de la file d'attente (statut + boutons)
            self._update_file_attente()
            self.load_data()
            
            CustomMessageBox.success(
                self, "Démarré",
                f"Passage pour l'acte #{code_acte} démarré avec succès."
            )
        else:
            CustomMessageBox.warning(self, "Impossible de démarrer", str(msg))

    def _terminer_passage(self, code_acte: int):
        """
        Termine un passage en cours :
          - Renseigne date_sortie
          - Change statut_passage en termine
          - Change statut_acte en termine
          - Calcule durée_attente = date_debut_execution - date_entre
          - Calcule durée_execution = date_sortie - date_debut_execution
          - Calcule durée_totale = date_sortie - date_entre
          - Met à jour statut_patient (En X -> Attente prochaine étape ou Attente paiement)
        """
        if code_acte is None:
            return
        ok, msg = self.ctrl.terminer_passage_par_code_acte(code_acte)
        if ok:
            # Mise à jour INSTANTANÉE de la file d'attente (statut + boutons)
            self._update_file_attente()
            self.load_data()
            
            CustomMessageBox.success(
                self, "Terminé",
                f"Passage pour l'acte #{code_acte} terminé avec succès."
            )
        else:
            CustomMessageBox.warning(self, "Impossible de terminer", str(msg))
    
    def _ouvrir_formulaire_examen(self, code_acte: str):
        """
        Ouvre le formulaire d'examen avec le code_acte pré-rempli.
        Après l'enregistrement, termine automatiquement le passage.
        """
        try:
            self.logger.info(f"Ouverture formulaire examen pour code_acte: {code_acte}")
            
            # Récupérer le dashboard parent
            dashboard = self._trouver_dashboard_parent()
            if not dashboard:
                CustomMessageBox.warning(self, "Erreur", "Impossible de trouver le dashboard")
                return
            
            # Basculer vers l'onglet Examen
            if hasattr(dashboard, 'page_examens'):
                # Trouver l'index de l'onglet Examen (index 5 selon dashboard_view.py)
                dashboard.workspace_stack.setCurrentIndex(5)
                
                # Attendre que la page soit chargée
                from PySide6.QtCore import QTimer
                QTimer.singleShot(100, lambda: self._pre_remplir_formulaire_examen(dashboard, code_acte))
            else:
                CustomMessageBox.warning(self, "Erreur", "Page examen non trouvée")
        except Exception as e:
            self.logger.error(f"Erreur _ouvrir_formulaire_examen: {e}")
            CustomMessageBox.warning(self, "Erreur", str(e))
    
    def _pre_remplir_formulaire_examen(self, dashboard, code_acte: str):
        """Pré-remplit le formulaire d'examen après le chargement de la page."""
        try:
            self.logger.info(f"Pré-remplissage formulaire pour code_acte: {code_acte}")
            
            # Récupérer le code_session actif depuis le dashboard
            code_session = None
            if hasattr(dashboard, 'visite_ctrl'):
                try:
                    actif, code_session = dashboard.visite_ctrl.verifier_session_active()
                    self.logger.info(f"Session active: {actif}, code_session: {code_session}")
                except Exception as e:
                    self.logger.error(f"Erreur récupération session: {e}")
            
            if not code_session:
                self.logger.error("Aucune session active trouvée")
                CustomMessageBox.warning(self, "Erreur", "Aucune session active. Veuillez démarrer une session.")
                return
            
            # Ouvrir l'onglet Nouveau avec le code_acte
            if hasattr(dashboard.page_examens, 'tabs'):
                dashboard.page_examens.tabs.setCurrentIndex(1)  # Onglet Nouveau
                # Pré-remplir le formulaire avec le code_acte
                if hasattr(dashboard.page_examens, 'form_widget'):
                    self.logger.info("Form widget trouvé, appel de pre_remplir_code_acte")
                    
                    # Définir le code_session dans le formulaire
                    dashboard.page_examens.form_widget.code_session = code_session
                    dashboard.page_examens.form_widget.edit_session.setText(code_session)
                    self.logger.info(f"Code session défini dans le formulaire: {code_session}")
                    print(f"[VueActeMedical] Code session défini: {code_session}")
                    print(f"[VueActeMedical] Texte dans edit_session: {dashboard.page_examens.form_widget.edit_session.text()}")
                    
                    # Pré-remplir le code_acte
                    dashboard.page_examens.form_widget.pre_remplir_code_acte(code_acte)
                    # Stocker le code_acte pour terminer le passage après enregistrement
                    dashboard.page_examens.form_widget.code_acte_passage = code_acte
                    self.logger.info(f"code_acte_passage défini: {code_acte}")
                else:
                    self.logger.error("Form widget non trouvé")
                    CustomMessageBox.warning(self, "Erreur", "Formulaire non trouvé")
            else:
                self.logger.error("Onglets non trouvés")
                CustomMessageBox.warning(self, "Erreur", "Onglets non trouvés dans la page examen")
        except Exception as e:
            self.logger.error(f"Erreur _pre_remplir_formulaire_examen: {e}", exc_info=True)
            CustomMessageBox.warning(self, "Erreur", str(e))
    
    def _ouvrir_formulaire_chirurgie(self, code_acte: str):
        """Navigue vers le formulaire de chirurgie pré-rempli avec code_acte."""
        try:
            dashboard = self._trouver_dashboard_parent()
            if not dashboard:
                CustomMessageBox.warning(self, "Erreur", "Impossible de trouver le dashboard")
                return

            code_consultation = self.ctrl.obtenir_code_consultation_par_acte(code_acte)
            code_session = None
            if hasattr(dashboard, 'visite_ctrl'):
                try:
                    _, code_session = dashboard.visite_ctrl.verifier_session_active()
                except Exception:
                    pass

            dashboard.workspace_stack.setCurrentIndex(6)
            if hasattr(dashboard, 'lbl_page_title'):
                dashboard.lbl_page_title.setText("Gestion des Chirurgies")

            def _pre_remplir_chirurgie():
                page = dashboard.page_chirurgies
                page.tabs.setCurrentIndex(1)
                if hasattr(page, 'form_widget') and code_consultation:
                    page.form_widget.recharger_pour_patient(
                        code_consultation, code_session or ""
                    )
                    page.form_widget.edit_acte.setText(code_acte)
                    # Connexion one-shot : terminer le passage après sauvegarde
                    def _apres_sauvegarde():
                        try:
                            page.form_widget.chirurgie_saved.disconnect(_apres_sauvegarde)
                        except Exception:
                            pass
                        self._terminer_et_rediriger(code_acte)
                    page.form_widget.chirurgie_saved.connect(_apres_sauvegarde)

            QTimer.singleShot(100, _pre_remplir_chirurgie)

        except Exception as e:
            self.logger.error(f"Erreur _ouvrir_formulaire_chirurgie: {e}")
            CustomMessageBox.warning(self, "Erreur", str(e))

    def _ouvrir_formulaire_lunette(self, code_acte: str):
        """Navigue vers le formulaire de commande lunette pré-rempli avec code_acte."""
        try:
            dashboard = self._trouver_dashboard_parent()
            if not dashboard:
                CustomMessageBox.warning(self, "Erreur", "Impossible de trouver le dashboard")
                return

            code_consultation = self.ctrl.obtenir_code_consultation_par_acte(code_acte)
            code_session = None
            if hasattr(dashboard, 'visite_ctrl'):
                try:
                    _, code_session = dashboard.visite_ctrl.verifier_session_active()
                except Exception:
                    pass

            dashboard.workspace_stack.setCurrentIndex(7)
            if hasattr(dashboard, 'lbl_page_title'):
                dashboard.lbl_page_title.setText("Gestion des Commandes Lunette")

            def _pre_remplir_lunette():
                page = dashboard.page_lunettes
                page.tabs.setCurrentIndex(1)
                if hasattr(page, 'form_widget') and code_acte:
                    page.form_widget.recharger_pour_patient(
                        code_acte, code_session or ""
                    )
                    # Connexion one-shot : terminer le passage après sauvegarde
                    def _apres_sauvegarde():
                        try:
                            page.form_widget.commande_saved.disconnect(_apres_sauvegarde)
                        except Exception:
                            pass
                        self._terminer_et_rediriger(code_acte)
                    page.form_widget.commande_saved.connect(_apres_sauvegarde)

            QTimer.singleShot(100, _pre_remplir_lunette)

        except Exception as e:
            self.logger.error(f"Erreur _ouvrir_formulaire_lunette: {e}")
            CustomMessageBox.warning(self, "Erreur", str(e))

    def _ouvrir_formulaire_prescription(self, code_acte: str):
        """Navigue vers le panier prescription pré-rempli avec code_acte."""
        try:
            dashboard = self._trouver_dashboard_parent()
            if not dashboard:
                CustomMessageBox.warning(self, "Erreur", "Impossible de trouver le dashboard")
                return

            # Utiliser show_prescription() pour déclencher charger_donnees() avec la session active
            if hasattr(dashboard, 'show_prescription'):
                dashboard.show_prescription()
            else:
                dashboard.workspace_stack.setCurrentIndex(9)
                if hasattr(dashboard, 'lbl_page_title'):
                    dashboard.lbl_page_title.setText("Gestion des Prescriptions")

            def _pre_remplir_prescription():
                page = dashboard.page_prescription
                if hasattr(page, '_ouvrir_panier_avec_acte'):
                    page._ouvrir_panier_avec_acte(code_acte)
                # Connexion one-shot : terminer le passage après validation
                if hasattr(page, 'prescription_widget'):
                    def _apres_validation():
                        try:
                            page.prescription_widget.prescription_validee.disconnect(_apres_validation)
                        except Exception:
                            pass
                        self._terminer_et_rediriger(code_acte)
                    page.prescription_widget.prescription_validee.connect(_apres_validation)

            QTimer.singleShot(300, _pre_remplir_prescription)

        except Exception as e:
            self.logger.error(f"Erreur _ouvrir_formulaire_prescription: {e}")
            CustomMessageBox.warning(self, "Erreur", str(e))

    def _terminer_et_rediriger(self, code_acte: str):
        """Termine le passage en file d'attente et redirige vers acte_médical."""
        ok, msg = self.ctrl.terminer_passage_par_code_acte(code_acte)
        if ok:
            code_consultation = self.ctrl.obtenir_code_consultation_par_acte(code_acte)
            dashboard = self._trouver_dashboard_parent()
            if dashboard:
                dashboard.workspace_stack.setCurrentIndex(15)
                if hasattr(dashboard, 'lbl_page_title'):
                    dashboard.lbl_page_title.setText("Gestion des Actes Médicaux")
                
                # Rafraîchir la file d'attente immédiatement
                if hasattr(dashboard, 'page_actes'):
                    QTimer.singleShot(100, lambda: dashboard.page_actes._update_file_attente())
                    if code_consultation:
                        QTimer.singleShot(200, lambda c=code_consultation: dashboard.page_actes._filtrer_par_consultation(c))
        else:
            self.logger.warning(f"[_terminer_et_rediriger] Impossible de terminer le passage: {msg}")
    
    def _rediriger_vers_rendez_vous(self, code_consultation: str,
                                      code_acte: str = None, code_visite: str = None):
        """
        Redirige vers l'onglet 'Nouveau rendez-vous' après création d'un acte 'plus_tard'.
        - Navigue directement sur l'onglet Nouveau (index 3).
        - Pré-sélectionne le combo acte et le combo visite avec les valeurs de l'acte créé.
        - Une fois le RDV créé (rdv_cree), passe automatiquement le patient en Attente payement.
        """
        dashboard = self._trouver_dashboard_parent()
        if not dashboard or not hasattr(dashboard, 'show_rendez_vous'):
            return

        # Récupérer code_visite si non fourni
        if not code_visite:
            code_visite = self.ctrl.obtenir_code_visite_par_consultation(code_consultation)

        # Naviguer vers la page rendez-vous (charge les données via charger_rendez_vous)
        dashboard.show_rendez_vous()

        def _setup_rdv_panel():
            page_rdv = getattr(dashboard, 'page_rendez_vous', None)
            if not page_rdv:
                return

            # Pré-sélectionner acte + visite ET naviguer vers l'onglet Nouveau (index 3)
            if hasattr(page_rdv, 'preselectionner_acte_visite'):
                page_rdv.preselectionner_acte_visite(code_acte, code_visite)
            elif hasattr(page_rdv, 'tabs'):
                page_rdv.tabs.setCurrentIndex(3)

            # Connecter rdv_cree → valider_sejour_patient (one-shot)
            # Le signal rdv_cree est émis par RendezVousView._soumettre_form
            if code_visite and hasattr(page_rdv, 'rdv_cree'):
                def _on_rdv_cree():
                    try:
                        page_rdv.rdv_cree.disconnect(_on_rdv_cree)
                    except Exception:
                        pass
                    self.ctrl.valider_sejour_patient(code_visite)
                    self._update_file_attente()
                    self.load_data()
                page_rdv.rdv_cree.connect(_on_rdv_cree)

        # Délai pour laisser charger_rendez_vous et _recharger_form_combos se terminer
        QTimer.singleShot(500, _setup_rdv_panel)

    def _trouver_dashboard_parent(self):
        """Remonte la hiérarchie des widgets pour trouver le DashboardView."""
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == 'DashboardView':
                return parent
            parent = parent.parent()
        return None

    def _show_planifies(self):
        """Filtre la table sur les actes planifiés."""
        self.tabs.setCurrentIndex(1)
        self.actes_table.filter_statut.setCurrentText("planifie")

    def _filtrer_par_consultation(self, code_consultation: str):
        """
        Bascule sur l'onglet Nouveau avec la consultation pré-sélectionnée.
        Appelé après la fin d'un acte pour prescrire un nouvel acte sur la même consultation.
        """
        self.tabs.setCurrentIndex(3)  # onglet Nouveau — déclenche _on_tab_changed → _load_nouveau_combos
        # Attendre que les combos soient peuplés, puis sélectionner
        QTimer.singleShot(150, lambda: self._appliquer_preselection_consultation(code_consultation))

    def _appliquer_preselection_consultation(self, code_consultation: str):
        """Sélectionne la consultation dans le combo et pré-remplit choix_patient = maintenant."""
        # Pré-sélectionner la consultation
        for i in range(self.form_consultation.count()):
            if self.form_consultation.itemData(i) == code_consultation:
                self.form_consultation.setCurrentIndex(i)
                break
        # Pré-sélectionner choix_patient = "maintenant"
        # Le signal currentTextChanged déclenchera automatiquement
        # la mise à jour de mode_realisation=interne et statut_acte=en_attente
        idx = self.form_choix.findText("maintenant")
        if idx >= 0:
            self.form_choix.setCurrentIndex(idx)

    # ── Onglet Nouveau — chargement / sauvegarde / réinitialisation ───────────

    def _on_tab_changed(self, index: int):
        """Charge les combos du formulaire quand l'onglet Nouveau est activé."""
        if index == 3:
            self._load_nouveau_combos()
    
    def _on_choix_patient_changed(self, choix: str):
        """
        Liaison automatique : quand le choix patient change, met à jour
        automatiquement mode_realisation et statut_acte selon les règles métier.
        
        Règles :
          - maintenant → interne + en_attente
          - plus_tard  → interne + planifie
          - ailleurs   → externe + refuse
        
        Gestion du champ raison_refus :
          - ailleurs   → champ éditable (raison obligatoire)
          - autres     → champ grisé et vidé
        """
        if not choix or choix.startswith("Sélectionnez"):
            return
        
        # Mapping choix → (mode_realisation, statut_acte)
        mapping = {
            "maintenant": ("interne", "en_attente"),
            "plus_tard":  ("interne", "planifie"),
            "ailleurs":   ("externe", "refuse"),
        }
        
        if choix in mapping:
            mode, statut = mapping[choix]
            
            # Mettre à jour mode_realisation
            idx_mode = self.form_mode.findText(mode)
            if idx_mode >= 0:
                self.form_mode.setCurrentIndex(idx_mode)
            
            # Mettre à jour statut_acte
            idx_statut = self.form_statut.findText(statut)
            if idx_statut >= 0:
                self.form_statut.setCurrentIndex(idx_statut)
        
        # Gestion conditionnelle du champ raison_refus
        if choix == "ailleurs":
            # Activer le champ raison_refus (obligatoire pour justifier le refus)
            self.form_raison.setEnabled(True)
            self.form_raison.setPlaceholderText("Raison du refus (obligatoire pour 'ailleurs')")
        else:
            # Désactiver et vider le champ raison_refus
            self.form_raison.setEnabled(False)
            self.form_raison.clear()
            self.form_raison.setPlaceholderText("Raison du refus (non applicable)")

    def _set_default_values(self):
        """
        Définit les valeurs par défaut intelligentes pour le formulaire Nouveau.
        Par défaut : choix_patient=maintenant → mode_realisation=interne + statut_acte=en_attente
        """
        # Choix patient par défaut : maintenant
        idx_choix = self.form_choix.findText("maintenant")
        if idx_choix >= 0:
            self.form_choix.setCurrentIndex(idx_choix)
            # Le signal currentTextChanged déclenchera automatiquement la mise à jour
            # de mode_realisation, statut_acte ET l'état du champ raison_refus
        else:
            # Fallback manuel si le signal ne se déclenche pas
            idx_mode = self.form_mode.findText("interne")
            if idx_mode >= 0:
                self.form_mode.setCurrentIndex(idx_mode)
            
            idx_statut = self.form_statut.findText("en_attente")
            if idx_statut >= 0:
                self.form_statut.setCurrentIndex(idx_statut)
            
            # Désactiver raison_refus par défaut (car choix != ailleurs)
            self.form_raison.setEnabled(False)
            self.form_raison.setPlaceholderText("Raison du refus (non applicable)")
    
    def _load_nouveau_combos(self):
        """Charge toutes les listes déroulantes du formulaire Nouveau."""
        self.form_consultation.clear()
        try:
            for row in self.ctrl.lister_consultations_form():
                label = row.get('label') or row.get('code', '')
                code  = row.get('code', '')
                self.form_consultation.addItem(label, code)
        except Exception as e:
            self.logger.warning("load_nouveau_combos consultations: %s", e)

        self.form_session.clear()
        try:
            for row in self.ctrl.lister_sessions_form():
                code = row.get('code_session', '')
                self.form_session.addItem(code, code)
        except Exception as e:
            self.logger.warning("load_nouveau_combos sessions: %s", e)

        self.form_personnel.clear()
        try:
            for row in self.ctrl.lister_personnel_form():
                label = row.get('label') or row.get('code', '')
                code  = row.get('code', '')
                self.form_personnel.addItem(label, code)
        except Exception as e:
            self.logger.warning("load_nouveau_combos personnel: %s", e)
        
        # Définir les valeurs par défaut intelligentes
        self._set_default_values()

    def _save_nouveau_form(self):
        """Valide et enregistre l'acte médical depuis le formulaire Nouveau."""
        code_cons = (
            self.form_consultation.currentData()
            or self.form_consultation.currentText().strip()
        )
        type_acte = self.form_type_acte.currentText().strip()
        decision  = self.form_decision.toPlainText().strip()
        choix_val = self.form_choix.currentText().strip()

        if not code_cons or code_cons.startswith("Sélectionnez"):
            CustomMessageBox.warning(
                self, "Champ manquant", "Le code consultation est obligatoire.")
            return
        if not type_acte or type_acte.startswith("Sélectionnez"):
            CustomMessageBox.warning(
                self, "Champ manquant", "Le type d'acte est obligatoire.")
            return
        if not decision:
            CustomMessageBox.warning(
                self, "Champ manquant", "La décision médicale est obligatoire.")
            return
        
        # Validation spécifique : raison_refus obligatoire si choix = "ailleurs"
        raison_val = self.form_raison.toPlainText().strip() or None
        if choix_val == "ailleurs" and not raison_val:
            CustomMessageBox.warning(
                self, "Champ manquant",
                "La raison du refus est obligatoire lorsque le patient choisit 'ailleurs'.")
            return

        try:
            from models.model_acte_medicale import ActeMedical
            mode_val   = self.form_mode.currentText().strip()
            statut_val = self.form_statut.currentText().strip()

            acte = ActeMedical(
                code_consultation = code_cons,
                type_acte         = type_acte,
                decision_medicale = decision,
                choix_patient     = choix_val  if not choix_val.startswith("Sélectionnez")  else None,
                mode_realisation  = mode_val   if not mode_val.startswith("Sélectionnez")   else "interne",
                statut_acte       = statut_val if not statut_val.startswith("Sélectionnez") else "en_attente",
                raison_refus      = raison_val,
            )
            ok, msg, acte_cree = self.ctrl.creer_acte(acte)
            if ok and acte_cree:
                # Récupérer le code_acte généré depuis l'objet retourné
                code_acte_cree = acte_cree.id_acte
                
                # Rafraîchir les données AVANT le message
                self._reset_nouveau_form()
                self._load_nouveau_combos()
                # Mise à jour INSTANTANÉE de la file d'attente
                self._update_file_attente()
                self.load_data()
                
                CustomMessageBox.success(self, "Succès", "Acte médical enregistré avec succès.")
                
                # Si choix = plus_tard → rediriger vers rendez-vous avec pré-sélection
                if choix_val == "plus_tard" and code_acte_cree:
                    code_visite_rdv = self.ctrl.obtenir_code_visite_par_consultation(code_cons)
                    QTimer.singleShot(300, lambda c=code_cons, ca=code_acte_cree, cv=code_visite_rdv:
                        self._rediriger_vers_rendez_vous(c, code_acte=ca, code_visite=cv))
                else:
                    self.tabs.setCurrentIndex(2)  # Aller à l'onglet File d'attente
            else:
                CustomMessageBox.warning(self, "Erreur", str(msg))
        except Exception as e:
            self.logger.error("Erreur enregistrement acte Nouveau: %s", e)
            CustomMessageBox.warning(self, "Erreur", str(e))

    def _reset_nouveau_form(self):
        """Remet le formulaire Nouveau dans son état initial."""
        self.form_code_acte.clear()
        self.form_decision.clear()
        self.form_raison.clear()
        for combo in (
            self.form_consultation, self.form_type_acte,
            self.form_choix, self.form_mode, self.form_statut,
            self.form_session, self.form_personnel,
        ):
            combo.setCurrentIndex(-1)

    def _show_parcours(self):
        CustomMessageBox.info(
            self, "Parcours patient",
            "Saisissez un code consultation dans la recherche pour filtrer le parcours."
        )

    def _on_export(self):
        CustomMessageBox.info(self, "Export", "Fonctionnalité d'export à venir.")

    # =========================================================================
    # RAFRAÎCHISSEMENT AUTO
    # =========================================================================

    def _setup_auto_refresh(self):
        # Rafraîchissement RAPIDE de la file d'attente toutes les 3s (instantané)
        self._timer_file = QTimer(self)
        self._timer_file.setInterval(3_000)
        self._timer_file.timeout.connect(self._update_file_attente)
        self._timer_file.start()
        # Rafraîchissement global (table actes + KPIs) toutes les 30s
        self._timer = QTimer(self)
        self._timer.setInterval(30_000)
        self._timer.timeout.connect(self.load_data)
        self._timer.start()
        # Clignotement de l'étape courante toutes les 800ms
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(800)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blink_timer.start()

    # =========================================================================
    # THÈME
    # =========================================================================

    def _icon(self, name: str):
        try:
            import qtawesome as qta
            return qta.icon(name, color=theme_manager.colors()["primary"])
        except Exception:
            return QIcon()

    def _apply_tab_styles(self):
        from .styles import get_styles
        self.tabs.setStyleSheet(get_styles())

    def _style_main_frame(self, frame: QFrame):
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame#MainWhiteFrame {{
                background-color: {c['bg_card']};
                border-radius: 16px;
                border: 1px solid {c['border']};
            }}
        """)

    def apply_theme(self):
        c = theme_manager.colors()
        self._apply_tab_styles()
        self.setStyleSheet(f"background-color: {c['bg_main']};")
        # Barre de titre file d'attente
        try:
            header = self.tab_attente.findChild(QFrame, "FileAttenteHeader")
            if header:
                header.setStyleSheet(
                    f"""QFrame#FileAttenteHeader {{
                        background:{c['bg_card']};
                        border:1px solid {c['border']};
                        border-radius:10px;
                    }}
                    QLabel#FileAttenteTitle {{
                        font-size:13px;font-weight:700;
                        color:{c['text_primary']};background:transparent;
                    }}
                    QPushButton#BtnRefreshFile {{
                        background:{c['primary']};color:white;border:none;
                        border-radius:7px;font-size:12px;font-weight:600;
                        padding:0 14px;
                    }}
                    QPushButton#BtnRefreshFile:hover {{
                        background:{c['primary_hover']};
                    }}"""
                )
        except Exception:
            pass
        # Styles onglet Nouveau
        try:
            self.tab_nouveau.setStyleSheet(f"""
                QWidget#NouveauPageHeader {{
                    background:{c['bg_card']};
                    border-bottom:1px solid {c['border']};
                }}
                QLabel#NouveauPageIcon {{
                    background:{c['primary']};
                    border-radius:10px;
                }}
                QLabel#NouveauPageTitle {{
                    font-size:14px;font-weight:700;color:{c['text_primary']};
                    background:transparent;
                }}
                QLabel#NouveauPageSub {{
                    font-size:11px;color:{c['text_secondary']};
                    background:transparent;
                }}
                QFrame#NouveauSep {{
                    background:{c['border']};border:none;max-height:1px;
                }}
                QWidget#NouveauBody {{
                    background:{c['bg_main']};
                }}
                QLineEdit#NouveauField, QComboBox#NouveauField, QTextEdit#NouveauField {{
                    background:{c['bg_card']};
                    border:1px solid {c['border']};
                    border-radius:8px;
                    padding:4px 10px;
                    font-size:12px;
                    color:{c['text_primary']};
                }}
                QLineEdit#NouveauField:focus, QComboBox#NouveauField:focus,
                QTextEdit#NouveauField:focus {{
                    border:2px solid {c['primary']};
                    background:{c['bg_card']};
                }}
                QComboBox#NouveauField:disabled {{
                    background:{c['bg_main']};
                    color:{c['text_secondary']};
                    border:1px dashed {c['border']};
                }}
                QTextEdit#NouveauField:disabled {{
                    background:{c['bg_main']};
                    color:{c['text_secondary']};
                    border:1px dashed {c['border']};
                }}
                QComboBox#NouveauField::drop-down {{
                    border:none;width:28px;
                }}
                QComboBox#NouveauField::down-arrow {{
                    width:10px;height:10px;
                }}
                QWidget#NouveauInfoBanner {{
                    background:#EFF6FF;
                    border:1px solid #BFDBFE;
                    border-radius:10px;
                }}
                QLabel#NouveauInfoIconCircle {{
                    background:#2563EB;border-radius:14px;
                }}
                QLabel#NouveauInfoL1 {{
                    font-size:12px;font-weight:600;color:#1E40AF;
                    background:transparent;
                }}
                QLabel#NouveauInfoL2 {{
                    font-size:11px;color:#3B82F6;background:transparent;
                }}
                QPushButton#NouveauBtnSearch {{
                    background:#2563EB;border:none;border-radius:8px;
                }}
                QPushButton#NouveauBtnSearch:hover {{
                    background:#1D4ED8;
                }}
                QWidget#NouveauFooter {{
                    background:{c['bg_card']};
                    border-top:1px solid {c['border']};
                }}
                QPushButton#NouveauBtnSave {{
                    background:{c['primary']};color:white;border:none;
                    border-radius:8px;font-size:12px;font-weight:600;
                    padding:0 16px;
                }}
                QPushButton#NouveauBtnSave:hover {{
                    background:{c['primary_hover']};
                }}
                QPushButton#NouveauBtnCancel {{
                    background:{c['bg_main']};color:{c['text_secondary']};
                    border:1px solid {c['border']};border-radius:8px;
                    font-size:12px;padding:0 12px;
                }}
                QPushButton#NouveauBtnCancel:hover {{
                    background:{c['border']};
                }}
            """)
        except Exception:
            pass
