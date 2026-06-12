"""
Vue Rendez-vous avec architecture à onglets.
4 onglets : Statistiques, Liste, Patients en attente, Nouveau
"""
import qtawesome as qta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QFrame, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QMessageBox,
    QComboBox, QLineEdit, QDateTimeEdit, QTextEdit, QDialog, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QColor
from views.shared.theme_manager import theme_manager
from .styles import RendezVousStyles
from .graphe_rendez_vous import RendezVousAnalyseGraph
from .patients_rendez_vous_attente import PatientsAttenteRendezVousView
from .rendez_vous_form import RendezVousFormDialog


class StatusBadge(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumWidth(90)
        self.setFixedHeight(24)

    def set_status(self, statut: str):
        self.setText(RendezVousView.pretty_status(statut))
        self.setStyleSheet(RendezVousStyles.status_badge(statut))


class RendezVousView(QWidget):
    """Vue principale rendez-vous avec onglets"""

    # Émis après création réussie d'un rendez-vous (depuis onglet Nouveau ou Patients en attente)
    rdv_cree = Signal()

    def __init__(self, rendez_vous_ctrl):
        super().__init__()
        self.ctrl = rendez_vous_ctrl
        self.code_session = None
        self._init_ui()
        self._setup_auto_refresh_rdv()
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(0)

        # Frame principal
        main_frame = QFrame()
        main_frame.setObjectName("MainWhiteFrame")
        main_frame_layout = QVBoxLayout(main_frame)
        main_frame_layout.setContentsMargins(0, 0, 0, 0)
        main_frame_layout.setSpacing(0)

        # Barre du haut
        self._setup_top_bar(main_frame_layout)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setIconSize(QSize(20, 20))
        self._apply_tab_styles()
        main_frame_layout.addWidget(self.tabs)

        # Créer les onglets
        self._create_tabs()

        # Quick Actions
        self._setup_quick_actions(main_frame_layout)

        main_layout.addWidget(main_frame)
        self._apply_main_frame_style(main_frame)

    def _setup_top_bar(self, parent_layout):
        """Barre du haut avec titre"""
        top_frame = QFrame()
        top_frame.setStyleSheet("background: transparent; border: none;")
        hbox = QHBoxLayout(top_frame)
        hbox.setContentsMargins(15, 10, 15, 10)
        hbox.setSpacing(10)

        titre = QLabel("Gestion des Rendez-vous")
        c = theme_manager.colors()
        titre.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {c['primary']};")
        self._titre_label = titre

        hbox.addWidget(titre)
        hbox.addStretch()

        parent_layout.addWidget(top_frame)

    def _create_tabs(self):
        """Crée les 5 onglets"""
        # Onglet 1: Statistiques
        self.tab_stats = self._create_stats_tab()
        icon_stats = self._get_icon("chart-bar")
        self.tabs.addTab(self.tab_stats, icon_stats, "Statistiques")

        # Onglet 2: Liste
        self.tab_liste = self._create_liste_tab()
        icon_liste = self._get_icon("list")
        self.tabs.addTab(self.tab_liste, icon_liste, "Liste des rendez-vous")

        # Onglet 3: Patients en attente
        self.tab_attente = self._create_attente_tab()
        icon_attente = self._get_icon("clock")
        self.tabs.addTab(self.tab_attente, icon_attente, "Patients en attente")

        # Onglet 4: Nouveau
        self.tab_nouveau = self._create_nouveau_tab()
        icon_nouveau = self._get_icon("plus")
        self.tabs.addTab(self.tab_nouveau, icon_nouveau, "Nouveau rendez-vous")

        # Onglet 5: Rendez-vous en cours
        self.tab_encours = self._create_encours_tab()
        try:
            icon_encours = qta.icon("fa5s.calendar-alt", color=theme_manager.colors()['primary'])
        except Exception:
            icon_encours = self._get_icon("clock")
        self.tabs.addTab(self.tab_encours, icon_encours, "Rendez-vous en cours")

    # =========================================================================
    # ONGLET RENDEZ-VOUS EN COURS
    # =========================================================================

    def _create_encours_tab(self):
        """Onglet affichant les rendez-vous actifs sous forme de cartes."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Zone scrollable pour les cartes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        self._encours_container = QWidget()
        self._encours_container.setStyleSheet("background: transparent;")
        self._encours_layout = QVBoxLayout(self._encours_container)
        self._encours_layout.setContentsMargins(0, 0, 0, 0)
        self._encours_layout.setSpacing(10)
        self._encours_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self._encours_container)
        layout.addWidget(scroll)
        return tab

    @staticmethod
    def _compute_countdown(date_rdv) -> str:
        """Calcule le temps restant avant un rendez-vous."""
        if not date_rdv:
            return "—"
        from datetime import datetime as dt
        now = dt.now()
        if hasattr(date_rdv, 'timetuple'):
            delta = date_rdv - now
        else:
            return "—"
        if delta.total_seconds() <= 0:
            return "Passé"
        total_s = int(delta.total_seconds())
        days = total_s // 86400
        hours = (total_s % 86400) // 3600
        mins = (total_s % 3600) // 60
        if days > 0:
            return f"{days}j {hours}h {mins}min"
        elif hours > 0:
            return f"{hours}h {mins}min"
        else:
            return f"{mins}min"

    def _charger_rdv_en_cours(self):
        """Récupère et affiche les cartes rendez-vous en cours.
        Traite d'abord automatiquement les RDV du jour pour les placer en file d'attente.
        """
        if not self.code_session or not hasattr(self, '_encours_layout'):
            return

        # Traiter automatiquement les RDV du jour
        try:
            traites = self.ctrl.traiter_rdv_du_jour(self.code_session)
            if traites > 0:
                print(f"[RDV] {traites} patient(s) placé(s) en file d'attente automatiquement.")
        except Exception as e:
            print(f"Erreur traitement RDV du jour: {e}")

        # Vider les cartes existantes
        while self._encours_layout.count():
            item = self._encours_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            rdvs = self.ctrl.lister_rdv_en_cours(self.code_session) or []
        except Exception as e:
            print(f"Erreur chargement rdv en cours: {e}")
            rdvs = []

        if not rdvs:
            c = theme_manager.colors()
            lbl = QLabel("Aucun rendez-vous en cours pour cette session.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {c['text_secondary']}; font-size: 13px; padding: 30px;")
            self._encours_layout.addWidget(lbl)
            return

        for rdv in rdvs:
            card = self._build_rdv_card(rdv)
            self._encours_layout.addWidget(card)

    @staticmethod
    def _circle_icon(icon_name: str, icon_color: str, bg_color: str, size: int = 22):
        """Crée un QIcon avec l'icône centrée sur un cercle de couleur."""
        from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QIcon
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(bg_color)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)
        icon_sz = size - 8
        icon_px = qta.icon(icon_name, color=icon_color).pixmap(icon_sz, icon_sz)
        offset = (size - icon_sz) // 2
        painter.drawPixmap(offset, offset, icon_px)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def _info_block(icon_name: str, icon_color: str, text: str, c: dict,
                    bold: bool = False, min_width: int = 0, center: bool = False) -> QWidget:
        """Bloc icône encerclée + texte pour la carte RDV."""
        from PySide6.QtGui import QIcon
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(w)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(6)
        if min_width:
            w.setMinimumWidth(min_width)
        # Icône dans un cercle coloré
        ico_lbl = QLabel()
        ico_lbl.setFixedSize(28, 28)
        ico_lbl.setAlignment(Qt.AlignCenter)
        ico_lbl.setPixmap(qta.icon(icon_name, color="white").pixmap(13, 13))
        ico_lbl.setStyleSheet(
            f"background-color: {icon_color}; border-radius: 14px; border: none;"
        )
        # Texte
        txt_lbl = QLabel(text)
        weight = "700" if bold else "500"
        font_color = c['text_primary'] if bold else c['text_secondary']
        txt_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: {weight}; color: {font_color}; background: transparent;"
        )
        if center:
            txt_lbl.setAlignment(Qt.AlignCenter)
        hl.addWidget(ico_lbl)
        hl.addWidget(txt_lbl)
        return w

    def _build_rdv_card(self, rdv: dict) -> QFrame:
        """Construit une carte horizontale pour un rendez-vous."""
        from PySide6.QtGui import QIcon
        c = theme_manager.colors()

        card = QFrame()
        card.setObjectName("RdvCard")
        card.setStyleSheet(f"""
            QFrame#RdvCard {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding: 4px;
            }}
            QFrame#RdvCard:hover {{
                border-color: {c['primary']};
                background-color: {c['hover']};
            }}
        """)
        card.setMinimumHeight(80)

        hbox = QHBoxLayout(card)
        hbox.setContentsMargins(16, 12, 16, 12)
        hbox.setSpacing(16)

        # --- Infos patient ---
        nom_patient = f"{rdv.get('patient_nom', '')} {rdv.get('patient_prenom', '')}".strip() or "Patient inconnu"
        hbox.addWidget(self._info_block("fa5s.user", c['primary'], nom_patient, c, bold=True, min_width=160))

        # --- Infos personnel ---
        nom_personnel = f"{rdv.get('personnel_nom', '')} {rdv.get('personnel_prenom', '')}".strip() or "-"
        fonction = rdv.get('personnel_fonction', '') or ''
        personnel_text = nom_personnel + (f"  ({fonction})" if fonction else "")
        hbox.addWidget(self._info_block("fa5s.user-md", c['success'], personnel_text, c, min_width=160))

        # --- Type acte ---
        type_acte = rdv.get('type_acte', '') or rdv.get('code_acte', '') or '—'
        hbox.addWidget(self._info_block("fa5s.clipboard-list", c['warning'], type_acte, c, min_width=120))

        hbox.addStretch()

        # --- Countdown ---
        date_rdv = rdv.get('date_rendez_vous')
        countdown_text = self._compute_countdown(date_rdv)
        date_str = date_rdv.strftime("%d/%m/%Y %H:%M") if hasattr(date_rdv, 'strftime') else str(date_rdv or '—')
        if countdown_text == "Passé":
            cd_color = c['danger']
        elif 'min' in countdown_text and 'j' not in countdown_text and 'h' not in countdown_text:
            cd_color = c['warning']
        else:
            cd_color = c['info']
        hbox.addWidget(self._info_block("fa5s.clock", cd_color, f"{countdown_text}  {date_str}", c, min_width=140))

        # --- Statut badge ---
        statut_raw = rdv.get('statut_rendez_vous', 'attente')
        statut_labels = {
            "attente":  ("En attente", c['warning']),
            "confirme": ("Confirmé",   c['success']),
            "en_cours": ("En cours",   c['info']),
        }
        statut_text, statut_color = statut_labels.get(statut_raw, (statut_raw.capitalize(), c['primary']))
        lbl_statut = QLabel(statut_text)
        lbl_statut.setAlignment(Qt.AlignCenter)
        lbl_statut.setFixedSize(90, 26)
        lbl_statut.setStyleSheet(f"""
            background-color: {statut_color}22;
            color: {statut_color};
            border: 1px solid {statut_color};
            border-radius: 13px;
            font-size: 11px;
            font-weight: 600;
        """)
        hbox.addWidget(lbl_statut)
        hbox.addSpacing(12)

        # --- Bouton Annuler ---
        code_rdv = rdv.get('code_rendez_vous', '')
        btn_annuler = QPushButton("  Annuler")
        btn_annuler.setIcon(self._circle_icon("fa5s.ban", "white", "#e74c3c", 22))
        btn_annuler.setIconSize(QSize(22, 22))
        btn_annuler.setFixedHeight(34)
        btn_annuler.setMinimumWidth(105)
        btn_annuler.setCursor(Qt.PointingHandCursor)
        btn_annuler.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {c['danger']};
                border: 1.5px solid {c['danger']};
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background-color: {c['danger_bg']};
            }}
        """)
        btn_annuler.clicked.connect(lambda checked=False, crdv=code_rdv: self._annuler_rdv_encours(crdv))

        # --- Bouton Reporter ---
        btn_reporter = QPushButton("  Reporter")
        btn_reporter.setIcon(self._circle_icon("fa5s.calendar-plus", "white", "#f39c12", 22))
        btn_reporter.setIconSize(QSize(22, 22))
        btn_reporter.setFixedHeight(34)
        btn_reporter.setMinimumWidth(105)
        btn_reporter.setCursor(Qt.PointingHandCursor)
        btn_reporter.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {c['warning']};
                border: 1.5px solid {c['warning']};
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background-color: {c['warning_bg']};
            }}
        """)
        btn_reporter.clicked.connect(lambda checked=False, r=rdv: self._reporter_rdv_encours(r))

        hbox.addWidget(btn_annuler)
        hbox.addWidget(btn_reporter)

        return card

    def _annuler_rdv_encours(self, code_rdv: str):
        """Annule un rendez-vous depuis l'onglet en cours."""
        from PySide6.QtWidgets import QMessageBox
        rep = QMessageBox.question(
            self,
            "Confirmer l'annulation",
            f"Voulez-vous annuler le rendez-vous {code_rdv} ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if rep != QMessageBox.Yes:
            return
        ok, msg = self.ctrl.changer_statut_rendez_vous(code_rdv, "annule", self.code_session)
        if ok:
            self._charger_rdv_en_cours()
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erreur", msg)

    def _reporter_rdv_encours(self, rdv: dict):
        """Reporte un rendez-vous en demandant une nouvelle date."""
        from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout
        from PySide6.QtCore import QDateTime

        code_rdv = rdv.get('code_rendez_vous', '')
        dialog = QDialog(self)
        dialog.setWindowTitle("Reporter le rendez-vous")
        dialog.setMinimumWidth(320)
        c = theme_manager.colors()
        dialog.setStyleSheet(f"background: {c['bg_card']}; color: {c['text_primary']};")

        form_layout = QFormLayout(dialog)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(12)

        date_edit = QDateTimeEdit()
        date_edit.setDisplayFormat("dd/MM/yyyy HH:mm")
        date_edit.setCalendarPopup(True)
        date_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
        date_edit.setMinimumDateTime(QDateTime.currentDateTime())
        date_edit.setStyleSheet(f"""
            QDateTimeEdit {{
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 12px;
                color: {c['text_primary']};
                background: {c['bg_input']};
            }}
        """)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        form_layout.addRow("Nouvelle date :", date_edit)
        form_layout.addRow(buttons)

        if dialog.exec() != QDialog.Accepted:
            return

        nouvelle_date = date_edit.dateTime().toPython()
        from models.modele_rendez_vous import RendezVous
        rdv_obj = RendezVous(
            code_rendez_vous=code_rdv,
            code_visite=rdv.get('code_visite'),
            code_personnel=rdv.get('code_personnel'),
            code_session=rdv.get('code_session'),
            date_rendez_vous=nouvelle_date,
            statut_rendez_vous='reporte',
            code_acte=rdv.get('code_acte'),
        )
        ok, msg = self.ctrl.modifier_rendez_vous(rdv_obj)
        if ok:
            self._charger_rdv_en_cours()
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erreur", msg)

    def _create_stats_tab(self):
        """Onglet Statistiques — gauche : chiffres clés, droite : graphe"""
        from PySide6.QtGui import QFont

        tab = QWidget()

        outer = QVBoxLayout(tab)
        outer.setContentsMargins(14, 10, 14, 12)
        outer.setSpacing(12)

        # ── Ligne 1 : 3 KPI cards ──────────────────────────────────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)

        self.card_jour    = self._create_stat_card("RDV Aujourd'hui",   "0", "fa5s.calendar-day",   "primary")
        self.card_session = self._create_stat_card("Total Session",     "0", "fa5s.calendar-check", "success")
        self.card_attente = self._create_stat_card("Patients en attente","0","fa5s.user-clock",      "warning")

        kpi_row.addWidget(self.card_jour,    1)
        kpi_row.addWidget(self.card_session, 1)
        kpi_row.addWidget(self.card_attente, 1)
        outer.addLayout(kpi_row)

        # ── Ligne 2 : panneau gauche + graphe droite ───────────────────────────
        body = QHBoxLayout()
        body.setSpacing(12)

        # ── GAUCHE : détails statistiques ─────────────────────────────────────
        left_frame = QFrame()
        left_frame.setStyleSheet(RendezVousStyles.card())
        left_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(14, 12, 14, 12)
        left_layout.setSpacing(6)

        titre_left = QLabel("Détails par statut")
        titre_left.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {theme_manager.colors()['text_primary']}; border:none; background:transparent;")
        left_layout.addWidget(titre_left)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {theme_manager.colors()['border']}; border:none; background:{theme_manager.colors()['border']}; max-height:1px;")
        left_layout.addWidget(sep)
        left_layout.addSpacing(4)

        # Grille 2 colonnes de lignes stats
        grid = QHBoxLayout()
        grid.setSpacing(10)

        col1 = QVBoxLayout(); col1.setSpacing(6)
        col2 = QVBoxLayout(); col2.setSpacing(6)

        # items colonne 1
        self._stat_confirmes  = self._create_stat_row("Confirmés",   "0", "#2196F3")
        self._stat_termines   = self._create_stat_row("Terminés",    "0", "#4CAF50")
        self._stat_annules    = self._create_stat_row("Annulés",     "0", "#F44336")
        self._stat_reportes   = self._create_stat_row("Reportés",    "0", "#FF9800")
        for w in (self._stat_confirmes, self._stat_termines, self._stat_annules, self._stat_reportes):
            col1.addWidget(w)

        # items colonne 2
        self._stat_absents    = self._create_stat_row("Absents",     "0", "#9C27B0")
        self._stat_en_retard  = self._create_stat_row("En retard",   "0", "#E91E63")
        self._stat_taux_pres  = self._create_stat_row("Taux présence",  "0 %", "#009688")
        self._stat_taux_conv  = self._create_stat_row("Taux conversion","0 %", "#607D8B")
        for w in (self._stat_absents, self._stat_en_retard, self._stat_taux_pres, self._stat_taux_conv):
            col2.addWidget(w)

        col1.addStretch(); col2.addStretch()
        grid.addLayout(col1, 1)
        grid.addLayout(col2, 1)
        left_layout.addLayout(grid)
        left_layout.addStretch()

        body.addWidget(left_frame, 5)

        # ── DROITE : graphe ────────────────────────────────────────────────────
        right_frame = QFrame()
        right_frame.setStyleSheet(RendezVousStyles.card())
        right_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(10, 10, 10, 10)

        titre_right = QLabel("Évolution mensuelle")
        titre_right.setStyleSheet("font-size: 13px; font-weight: 700; color: #1e3a5f; border:none; background:transparent;")
        right_layout.addWidget(titre_right)

        self.graphe = RendezVousAnalyseGraph(parent=right_frame, width=6, height=4)
        right_layout.addWidget(self.graphe, 1)

        body.addWidget(right_frame, 4)

        outer.addLayout(body, 1)
        return tab

    def _create_stat_row(self, label: str, valeur: str, couleur: str) -> QFrame:
        """Ligne statistique : pastille colorée + libellé + valeur."""
        from PySide6.QtGui import QFont
        c = theme_manager.colors()

        row = QFrame()
        row.setFixedHeight(38)
        row.setStyleSheet(f"""
            QFrame {{
                background: {c['bg_input']};
                border-radius: 8px;
                border: 1px solid {c['border']};
            }}
        """)

        h = QHBoxLayout(row)
        h.setContentsMargins(10, 0, 10, 0)
        h.setSpacing(8)

        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background:{couleur}; border-radius:5px; border:none;")
        h.addWidget(dot)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color:{c['text_secondary']}; font-size:11px; background:transparent; border:none;")
        h.addWidget(lbl, 1)

        val = QLabel(valeur)
        font = QFont(); font.setBold(True); font.setPointSize(11)
        val.setFont(font)
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val.setStyleSheet(f"color:{couleur}; background:transparent; border:none;")
        h.addWidget(val)

        row._val_label = val
        return row

    def _create_stat_card(self, titre, valeur, icone, accent_key):
        """Crée une card statistique style consultation"""
        c = theme_manager.colors()
        couleur = c.get(accent_key, c['primary'])

        card = QFrame()
        card.setFixedHeight(82)
        card.setStyleSheet(f"""
            QFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Cercle icône
        icon_circle = QFrame()
        icon_circle.setFixedSize(42, 42)
        icon_circle.setStyleSheet(f"background: {couleur}; border: none; border-radius: 21px;")
        icon_layout = QHBoxLayout(icon_circle)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(22, 22)
        icon_label.setPixmap(qta.icon(icone, color="white").pixmap(22, 22))
        icon_layout.addWidget(icon_label)

        # Texte
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(titre)
        title_label.setStyleSheet(f"color: {c['text_secondary']}; font-size: 11px; font-weight: 500; background: transparent; border: none;")

        value_label = QLabel(valeur)
        from PySide6.QtGui import QFont
        font_value = QFont()
        font_value.setPointSize(15)
        font_value.setBold(True)
        value_label.setFont(font_value)
        value_label.setStyleSheet(f"color: {c['text_primary']}; background: transparent; border: none;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)

        layout.addWidget(icon_circle)
        layout.addLayout(text_layout, 1)

        card.value_label = value_label
        card._icon_name = icone
        card._accent_key = accent_key
        return card

    def _create_liste_tab(self):
        """Onglet Liste des rendez-vous"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Code", "Patient", "Personnel", "Date/Heure", "Statut", "Actions"])
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 110)

        self.table.setStyleSheet(RendezVousStyles.table())
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        return tab

    def _create_attente_tab(self):
        """Onglet Patients en attente"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)

        self.vue_attente = PatientsAttenteRendezVousView(
            ctrl=self.ctrl,
            code_session=self.code_session or ""
        )
        self.vue_attente.rdv_cree.connect(self._rafraichir_apres_rdv)
        scroll.setWidget(self.vue_attente)

        layout.addWidget(scroll)

        return tab

    def _create_nouveau_tab(self):
        """Onglet Nouveau rendez-vous avec formulaire intégré"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area pour le formulaire
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Créer le widget formulaire (version simplifiée)
        form_widget = self._create_form_widget()
        scroll.setWidget(form_widget)

        layout.addWidget(scroll)

        return tab

    def _create_form_widget(self):
        """Crée le widget formulaire style consultation avec 2 rangées"""
        widget = QWidget()
        widget.setStyleSheet(f"background: {theme_manager.colors()['bg_main']};")
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(24, 6, 24, 16)
        main_layout.setSpacing(14)

        c = theme_manager.colors()

        # Header avec boutons
        self._setup_form_header(main_layout)

        # Card principale avec les champs
        self._setup_form_fields(main_layout)

        # Info bas
        self._setup_form_info_bas(main_layout)

        main_layout.addStretch()

        # Charger les données
        self._charger_form_combos()

        # Connecter les validations
        self.form_combo_visite.currentIndexChanged.connect(self._on_visite_changed)
        self.form_combo_visite.currentIndexChanged.connect(self._valider_form)
        self.form_combo_personnel.currentIndexChanged.connect(self._valider_form)
        self.form_combo_statut.currentIndexChanged.connect(self._valider_form)
        self.form_edit_date.dateTimeChanged.connect(self._valider_form)

        return widget

    def _setup_form_header(self, parent_layout):
        """Header avec titre et boutons — refs stockées pour apply_theme."""
        c = theme_manager.colors()
        self._form_header_frame = QFrame()
        self._form_header_frame.setFixedHeight(72)

        layout = QHBoxLayout(self._form_header_frame)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(14)

        self._form_icon_box = QFrame()
        self._form_icon_box.setFixedSize(46, 46)
        ib_layout = QHBoxLayout(self._form_icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        self._form_ico_lbl = QLabel()
        self._form_ico_lbl.setAlignment(Qt.AlignCenter)
        ib_layout.addWidget(self._form_ico_lbl, alignment=Qt.AlignCenter)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self._form_lbl_main = QLabel("Enregistrement d'un rendez-vous")
        self._form_lbl_sub  = QLabel("Saisissez les informations du rendez-vous")
        title_col.addWidget(self._form_lbl_main)
        title_col.addWidget(self._form_lbl_sub)

        layout.addWidget(self._form_icon_box)
        layout.addLayout(title_col)
        layout.addStretch()

        self._form_btn_cancel = QPushButton(qta.icon("fa5s.times", color=c['text_secondary']), " Annuler")
        self._form_btn_cancel.setFixedSize(110, 40)
        self._form_btn_cancel.clicked.connect(self._reset_form)

        self.form_btn_save = QPushButton(qta.icon("fa5s.save", color=c['text_inverse']), " Enregistrer")
        self.form_btn_save.setFixedSize(140, 40)
        self.form_btn_save.setEnabled(False)
        self._apply_form_save_btn_style()
        self.form_btn_save.clicked.connect(self._soumettre_form)

        layout.addWidget(self._form_btn_cancel)
        layout.addWidget(self.form_btn_save)
        parent_layout.addWidget(self._form_header_frame)

    def _apply_form_save_btn_style(self):
        c = theme_manager.colors()
        self.form_btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['border']};
                color: {c['text_muted']};
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }}
            QPushButton:enabled {{
                background-color: {c['primary']};
                color: #ffffff;
            }}
            QPushButton:enabled:hover {{ background-color: {c['primary_hover']}; }}
        """)

    def _setup_form_fields(self, parent_layout):
        """Card avec les champs en 2 rangées — refs stockées pour apply_theme."""
        self._form_card_fields = QFrame()
        vbox = QVBoxLayout(self._form_card_fields)
        vbox.setContentsMargins(22, 18, 22, 18)
        vbox.setSpacing(18)

        hdr = QHBoxLayout()
        self._form_ico_section = QLabel()
        self._form_ico_section.setStyleSheet("border: none; background: transparent;")
        self._form_lbl_section = QLabel("Informations du rendez-vous")
        hdr.addWidget(self._form_ico_section)
        hdr.addSpacing(8)
        hdr.addWidget(self._form_lbl_section)
        hdr.addStretch()
        vbox.addLayout(hdr)

        # Rangée 1: Code | Patient/Visite | Code Visite | Personnel | Session
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        row1.setAlignment(Qt.AlignTop)

        self.form_edit_code_rdv = QLineEdit()
        self.form_edit_code_rdv.setText("AUTO")
        self.form_edit_code_rdv.setEnabled(False)
        vb_code, _ = self._make_field("Code", self.form_edit_code_rdv, "fa5s.hashtag", 'accent')
        row1.addWidget(self._field_widget(vb_code), 1, Qt.AlignTop)

        self.form_combo_visite = QComboBox()
        self.form_combo_visite.addItem("-- Sélectionner un patient --", "")
        vb_visite, self._wrap_visite = self._make_field(
            "Patient / Visite", self.form_combo_visite, "fa5s.user-injured", 'danger'
        )
        self._err_visite = self._err_label()
        vb_visite.addWidget(self._err_visite)
        row1.addWidget(self._field_widget(vb_visite), 1, Qt.AlignTop)

        self.form_edit_code_visite = QLineEdit()
        self.form_edit_code_visite.setEnabled(False)
        self.form_edit_code_visite.setPlaceholderText("Auto-rempli")
        vb_code_visite, _ = self._make_field(
            "Code Visite", self.form_edit_code_visite, "fa5s.shopping-bag", 'info'
        )
        row1.addWidget(self._field_widget(vb_code_visite), 1, Qt.AlignTop)

        self.form_combo_personnel = QComboBox()
        self.form_combo_personnel.addItem("-- Sélectionner le personnel --", "")
        vb_personnel, self._wrap_personnel = self._make_field(
            "Personnel", self.form_combo_personnel, "fa5s.user-md", 'primary'
        )
        self._err_personnel = self._err_label()
        vb_personnel.addWidget(self._err_personnel)
        row1.addWidget(self._field_widget(vb_personnel), 1, Qt.AlignTop)

        self.form_edit_session = QLineEdit(self.code_session or "")
        self.form_edit_session.setEnabled(False)
        vb_sess, _ = self._make_field(
            "Code session", self.form_edit_session, "fa5s.graduation-cap", 'accent'
        )
        row1.addWidget(self._field_widget(vb_sess), 1, Qt.AlignTop)

        vbox.addLayout(row1)
        vbox.addSpacing(10)

        # Rangée 2: Date | Statut | Code Acte
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        self.form_edit_date = QDateTimeEdit()
        self.form_edit_date.setCalendarPopup(True)
        from datetime import datetime, timedelta
        dt = datetime.now() + timedelta(minutes=30)
        dt = dt.replace(second=0, microsecond=0)
        from PySide6.QtCore import QDateTime
        self.form_edit_date.setDateTime(QDateTime.fromSecsSinceEpoch(int(dt.timestamp())))
        self.form_edit_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        vb_date, _ = self._make_field(
            "Date rendez-vous", self.form_edit_date, "fa5s.calendar-alt", 'info'
        )
        row2.addWidget(self._field_widget(vb_date), 1, Qt.AlignTop)

        self.form_combo_statut = QComboBox()
        self.form_combo_statut.addItem("-- Sélectionner le statut --", "")
        statuts = [("attente", "En attente"), ("confirme", "Confirmé"), ("en_cours", "En cours"),
                   ("termine", "Terminé"), ("annule", "Annulé"), ("absent", "Absent"), ("reporte", "Reporté")]
        for code, label in statuts:
            self.form_combo_statut.addItem(label, code)
        vb_statut, _ = self._make_field(
            "Statut rendez-vous", self.form_combo_statut, "fa5s.flag", 'warning'
        )
        row2.addWidget(self._field_widget(vb_statut), 1, Qt.AlignTop)

        self.form_combo_acte = QComboBox()
        self.form_combo_acte.addItem("-- Sélectionner un acte --", "")
        vb_acte, _ = self._make_field(
            "Code Acte", self.form_combo_acte, "fa5s.file-medical", 'danger'
        )
        row2.addWidget(self._field_widget(vb_acte), 1, Qt.AlignTop)

        vbox.addLayout(row2)
        parent_layout.addWidget(self._form_card_fields)

    def _setup_form_info_bas(self, parent_layout):
        """Section info bas — refs stockées pour apply_theme."""
        self._form_card_bas = QFrame()
        self._form_card_bas.setFixedHeight(80)
        hbox = QHBoxLayout(self._form_card_bas)
        hbox.setContentsMargins(20, 0, 20, 0)
        hbox.setSpacing(14)

        self._form_ico_bas_frame = QFrame()
        self._form_ico_bas_frame.setFixedSize(36, 36)
        ifi = QHBoxLayout(self._form_ico_bas_frame)
        ifi.setContentsMargins(0, 0, 0, 0)
        self._form_ico_bas_lbl = QLabel()
        self._form_ico_bas_lbl.setAlignment(Qt.AlignCenter)
        ifi.addWidget(self._form_ico_bas_lbl, alignment=Qt.AlignCenter)

        txt = QVBoxLayout()
        txt.setSpacing(2)
        self._form_lbl_bas_title = QLabel("Informations")
        self._form_lbl_bas_desc  = QLabel(
            "Veuillez remplir tous les champs obligatoires avant d'enregistrer le rendez-vous."
        )
        txt.addWidget(self._form_lbl_bas_title)
        txt.addWidget(self._form_lbl_bas_desc)

        hbox.addWidget(self._form_ico_bas_frame)
        hbox.addLayout(txt)
        hbox.addStretch()
        parent_layout.addWidget(self._form_card_bas)

    def _make_field(self, label_text: str, widget, icon_name: str, color_key: str,
                    height: int = 42, align_top: bool = False):
        """Retourne (QVBoxLayout, wrapper_QFrame). Enregistre dans _field_registry."""
        c = theme_manager.colors()
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        lbl = QLabel(label_text)
        vbox.addWidget(lbl)

        wrapper = QFrame()
        wrapper.setObjectName("inputWrapper")
        if align_top:
            wrapper.setMinimumHeight(height)
        else:
            wrapper.setFixedHeight(height)
        self._apply_wrapper_style(wrapper)

        hbox = QHBoxLayout(wrapper)
        hbox.setContentsMargins(8, 5, 8, 5)
        hbox.setSpacing(8)
        v_align = Qt.AlignTop if align_top else Qt.AlignVCenter

        badge = QFrame()
        badge.setFixedSize(28, 28)
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setAlignment(Qt.AlignCenter)
        ico_lbl.setStyleSheet("border: none; background: transparent;")
        bl.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        self._clear_widget_style(widget, c)
        hbox.addWidget(badge, 0, v_align)
        hbox.addWidget(widget, 1)
        vbox.addWidget(wrapper)

        if not hasattr(self, '_field_registry'):
            self._field_registry = []
        self._field_registry.append({
            'wrapper':   wrapper,
            'badge':     badge,
            'ico_lbl':   ico_lbl,
            'lbl':       lbl,
            'icon_name': icon_name,
            'color_key': color_key,
        })
        self._refresh_field(self._field_registry[-1], c)

        return vbox, wrapper

    def _refresh_field(self, entry: dict, c: dict):
        icon_color = c[entry['color_key']]
        entry['badge'].setStyleSheet(
            f"background-color: {icon_color}20; border-radius: 7px; border: none;"
        )
        entry['ico_lbl'].setPixmap(
            qta.icon(entry['icon_name'], color=icon_color).pixmap(14, 14)
        )
        entry['lbl'].setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {c['text_secondary']};"
            " background: transparent; border: none;"
        )
        self._apply_wrapper_style(entry['wrapper'])

    def _apply_wrapper_style(self, wrapper: QFrame, border_color: str = None):
        c = theme_manager.colors()
        bc = border_color or c['border']
        wrapper.setStyleSheet(f"""
            QFrame#inputWrapper {{
                background-color: {c['bg_input']};
                border: 1.5px solid {bc};
                border-radius: 10px;
            }}
        """)

    def _clear_widget_style(self, widget, c):
        """Applique fond + couleur du thème au widget interne."""
        if isinstance(widget, QComboBox):
            widget.setStyleSheet(f"""
                QComboBox {{
                    border: none;
                    background-color: {c['bg_input']};
                    color: {c['text_primary']};
                    font-size: 12px;
                    padding: 0;
                    min-height: 28px;
                }}
                QComboBox::drop-down {{ border: none; width: 20px; }}
                QComboBox QAbstractItemView {{
                    background-color: {c['bg_card']};
                    border: 1px solid {c['border']};
                    border-radius: 8px;
                    color: {c['text_primary']};
                    selection-background-color: {c['primary_light']};
                    outline: none;
                }}
                QComboBox QAbstractItemView::item {{ padding: 6px 10px; min-height: 26px; }}
                QComboBox QAbstractItemView::item:hover {{ background-color: {c['hover']}; }}
                QComboBox QAbstractItemView::item:selected {{
                    background-color: {c['primary_light']}; color: {c['primary']};
                }}
            """)
        elif isinstance(widget, QDateTimeEdit):
            widget.setStyleSheet(f"""
                QDateTimeEdit {{
                    border: none;
                    background-color: {c['bg_input']};
                    color: {c['text_primary']};
                    font-size: 12px;
                    padding: 0;
                }}
                QDateTimeEdit::drop-down {{ border: none; width: 20px; }}
            """)
        elif isinstance(widget, QTextEdit):
            widget.setStyleSheet(f"""
                QTextEdit {{
                    border: none;
                    background: transparent;
                    font-size: 12px;
                    color: {c['text_primary']};
                    padding: 4px 0;
                }}
            """)
        else:
            widget.setStyleSheet(f"""
                QLineEdit {{
                    border: none;
                    background: transparent;
                    font-size: 12px;
                    color: {c['text_primary']};
                    padding: 0;
                }}
            """)

    def _err_label(self) -> QLabel:
        c = theme_manager.colors()
        lbl = QLabel("")
        lbl.setStyleSheet(f"color: {c['danger']}; font-size: 10px; font-style: italic; background: transparent;")
        lbl.setVisible(False)
        return lbl

    def _field_widget(self, vbox: QVBoxLayout) -> QWidget:
        """Enveloppe un QVBoxLayout dans un QWidget transparent pour l'alignement AlignTop."""
        w = QWidget()
        w.setStyleSheet("background: transparent; border: none;")
        w.setLayout(vbox)
        return w

    def _on_visite_changed(self):
        """Remplit le champ code_visite quand une visite est sélectionnée"""
        visite_data = self.form_combo_visite.currentData()
        if visite_data and isinstance(visite_data, dict):
            code_visite = visite_data.get("code_visite", "")
            self.form_edit_code_visite.setText(code_visite)
        else:
            self.form_edit_code_visite.clear()

    def _reset_form(self):
        """Réinitialise le formulaire"""
        self.form_combo_visite.setCurrentIndex(0)
        self.form_combo_personnel.setCurrentIndex(0)
        self.form_combo_statut.setCurrentIndex(0)

    def preselectionner_acte_visite(self, code_acte: str = None, code_visite: str = None):
        """
        Navigue vers l'onglet 'Nouveau rendez-vous' et pré-sélectionne
        le combo acte et le combo visite en fonction des codes fournis.
        Appelé lors d'une redirection depuis la création d'un acte avec choix 'plus_tard'.
        """
        # Aller sur l'onglet Nouveau (index 3)
        if hasattr(self, 'tabs'):
            self.tabs.setCurrentIndex(3)

        # Pré-sélectionner l'acte médical
        if code_acte and hasattr(self, 'form_combo_acte'):
            found = False
            for i in range(self.form_combo_acte.count()):
                if self.form_combo_acte.itemData(i) == code_acte:
                    self.form_combo_acte.setCurrentIndex(i)
                    found = True
                    break
            if not found:
                # Ajouter directement l'acte dans le combo s'il n'y est pas encore
                self.form_combo_acte.addItem(f"{code_acte}  |  (acte créé)", code_acte)
                self.form_combo_acte.setCurrentIndex(self.form_combo_acte.count() - 1)

        # Pré-sélectionner la visite (patient)
        if code_visite and hasattr(self, 'form_combo_visite'):
            def _trouver_et_selectionner():
                for i in range(self.form_combo_visite.count()):
                    data = self.form_combo_visite.itemData(i)
                    cv = data.get('code_visite') if isinstance(data, dict) else data
                    if cv == code_visite:
                        self.form_combo_visite.setCurrentIndex(i)
                        return True
                return False

            if not _trouver_et_selectionner():
                # La visite n'est pas encore dans le combo (statut pas encore à jour).
                # Recharger les combos et retenter la sélection.
                self._charger_form_combos()
                _trouver_et_selectionner()

    def _recharger_form_nouveau(self, code_session: str):
        """Vide et recharge les combos du formulaire Nouveau quand la session est connue."""
        if not code_session or not hasattr(self, 'form_combo_visite'):
            return
        # Mettre à jour le champ session
        if hasattr(self, 'form_edit_session'):
            self.form_edit_session.setText(code_session)
        # Vider les combos avant de recharger
        self.form_combo_visite.clear()
        self.form_combo_visite.addItem("-- Sélectionner un patient --", "")
        self.form_combo_personnel.clear()
        self.form_combo_personnel.addItem("-- Sélectionner le personnel --", "")
        self.form_combo_acte.clear()
        self.form_combo_acte.addItem("-- Sélectionner un acte --", "")
        self._charger_form_combos()

    def _charger_form_combos(self):
        """Charge les données des combos du formulaire"""
        if not self.code_session:
            return

        try:
            # Charger les visites en attente
            visites = self.ctrl.obtenir_patients_attente_rendez_vous(self.code_session) or []
            for visite in visites:
                nom = f"{visite.get('nom', '')} {visite.get('prenom', '')}".strip()
                label = f"{visite.get('code_visite', '')}  |  {nom or 'Patient'}"
                self.form_combo_visite.addItem(label, visite)

            # Charger le personnel
            personnels = self.ctrl.lister_personnel() or []
            for personnel in personnels:
                label = f"{personnel.get('nom', '')} {personnel.get('prenom', '')}  |  {personnel.get('fonction', '')}"
                self.form_combo_personnel.addItem(label, personnel.get("code", ""))

            # Charger les actes médicaux en attente de rendez-vous pour cette session
            try:
                actes = self.ctrl.lister_actes_en_attente_rdv(self.code_session) or []
            except Exception:
                actes = []
            for acte in actes:
                code_a = acte.get('code_acte', '') if isinstance(acte, dict) else getattr(acte, 'code_acte', '')
                type_a = acte.get('type_acte', '') if isinstance(acte, dict) else getattr(acte, 'type_acte', '')
                if code_a:
                    self.form_combo_acte.addItem(f"{code_a}  |  {type_a}", code_a)
        except Exception as e:
            print(f"Erreur chargement combos: {e}")

    def _valider_form(self):
        """Valide le formulaire avec bordures colorées"""
        c = theme_manager.colors()
        tout_valide = True

        # Valider visite
        if not self.form_combo_visite.currentData():
            self._set_field_state(
                self._wrap_visite, self._err_visite,
                False, "Veuillez sélectionner un patient", True
            )
            tout_valide = False
        else:
            self._set_field_state(self._wrap_visite, self._err_visite, True, "", True)

        # Valider personnel
        if not self.form_combo_personnel.currentData():
            self._set_field_state(
                self._wrap_personnel, self._err_personnel,
                False, "Veuillez sélectionner un personnel", True
            )
            tout_valide = False
        else:
            self._set_field_state(self._wrap_personnel, self._err_personnel, True, "", True)

        self.form_btn_save.setEnabled(tout_valide)
        self._apply_form_save_btn_style()

    def _set_field_state(self, wrapper: QFrame, err_lbl: QLabel,
                         valide: bool, msg: str, has_text: bool):
        c = theme_manager.colors()
        if not valide and has_text:
            self._apply_wrapper_style(wrapper, c['danger'])
            err_lbl.setText(msg)
            err_lbl.setVisible(True)
        else:
            bc = c['border_focus'] if (valide and has_text) else c['border']
            self._apply_wrapper_style(wrapper, bc)
            err_lbl.setVisible(False)

    def _soumettre_form(self):
        """Soumet le formulaire"""
        try:
            from models.modele_rendez_vous import RendezVous

            visite_data = self.form_combo_visite.currentData()
            code_visite = visite_data.get("code_visite", "") if isinstance(visite_data, dict) else ""
            code_personnel = self.form_combo_personnel.currentData()
            statut = self.form_combo_statut.currentData() or "attente"
            code_acte = self.form_combo_acte.currentData() or None

            rdv = RendezVous(
                code_rendez_vous=None,
                code_visite=code_visite,
                code_personnel=code_personnel,
                code_session=self.code_session,
                date_rendez_vous=self.form_edit_date.dateTime().toPython(),
                statut_rendez_vous=statut,
                code_acte=code_acte
            )

            ok, msg = self.ctrl.creer_rendez_vous(rdv)

            if ok:
                from views.shared.message_box import CustomMessageBox
                CustomMessageBox("Succès", msg, True, self).exec()
                # Émettre le signal rdv_cree (pour callback valider_sejour depuis acte médical)
                self.rdv_cree.emit()
                # Réinitialiser le formulaire
                self.form_combo_visite.setCurrentIndex(0)
                self.form_combo_personnel.setCurrentIndex(0)
                self.form_combo_statut.setCurrentIndex(0)
                self.form_combo_acte.setCurrentIndex(0)
                # Recharger les données
                self.charger_rendez_vous(self.code_session)
                # Revenir à l'onglet Liste
                self.tabs.setCurrentIndex(1)
            else:
                from views.shared.message_box import CustomMessageBox
                CustomMessageBox("Erreur", msg, False, self).exec()

        except Exception as e:
            from views.shared.message_box import CustomMessageBox
            CustomMessageBox("Erreur Système", str(e), False, self).exec()

    def _setup_quick_actions(self, parent_layout):
        """Barre d'actions rapides en bas"""
        actions_frame = QFrame()
        actions_frame.setStyleSheet("background: transparent; border: none;")
        hbox = QHBoxLayout(actions_frame)
        hbox.setContentsMargins(12, 8, 12, 8)
        hbox.setSpacing(8)

        self.btn_add = self._create_quick_action_btn("fa5s.plus-square", "Nouveau rendez-vous", "primary")
        self.btn_add.clicked.connect(self._ouvrir_formulaire_rendez_vous)

        self.btn_notification = self._create_quick_action_btn("fa5s.bell", "Notifications", "warning")
        self.btn_export = self._create_quick_action_btn("fa5s.file-export", "Exporter", "success")
        self.btn_import = self._create_quick_action_btn("fa5s.file-import", "Importer", "accent")

        hbox.addWidget(self.btn_add)
        hbox.addWidget(self.btn_notification)
        hbox.addWidget(self.btn_export)
        hbox.addWidget(self.btn_import)
        hbox.addStretch()

        parent_layout.addWidget(actions_frame)

    def _create_quick_action_btn(self, icon_name, text, color_key):
        """Crée un bouton d'action rapide"""
        c = theme_manager.colors()
        btn = QPushButton(f"  {text}")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(40)
        btn.setObjectName("QuickActionButton")
        btn.setProperty("color_key", color_key)
        btn.setProperty("icon_name", icon_name)

        color = c.get(color_key, c["primary"])
        btn.setIcon(qta.icon(icon_name, color=color))
        btn.setStyleSheet(f"""
            QPushButton#QuickActionButton {{
                background: {c['bg_card']};
                border: none;
                border-radius: 8px;
                padding-left: 15px;
                text-align: left;
                font-size: 12px;
                font-weight: 600;
                color: {c['text_primary']};
            }}
            QPushButton#QuickActionButton:hover {{
                background: {c['hover']};
            }}
        """)
        return btn

    def _get_icon(self, icon_name):
        """Récupère une icône"""
        try:
            icon_map = {
                "chart-bar": "fa5s.chart-bar",
                "list": "fa5s.list",
                "clock": "fa5s.user-clock",
                "plus": "fa5s.plus-circle"
            }
            return qta.icon(icon_map.get(icon_name, "fa5s.circle"), color=theme_manager.colors()['primary'])
        except:
            from PySide6.QtWidgets import QStyle
            return self.style().standardIcon(QStyle.SP_FileIcon)

    def _apply_main_frame_style(self, frame):
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame#MainWhiteFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
        """)

    def _apply_tab_styles(self):
        """Style des onglets"""
        c = theme_manager.colors()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {c['bg_card']};
                border-radius: 12px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {c['text_secondary']};
                padding: 10px 20px;
                margin-right: 4px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 13px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                color: {c['primary']};
                border-bottom: 2px solid {c['primary']};
                font-weight: 600;
            }}
            QTabBar::tab:hover {{
                color: {c['primary']};
                background: {c['hover']};
            }}
        """)

    def apply_theme(self):
        """Applique le thème — cascade + propagation à tous les enfants."""
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_main']};")

        if hasattr(self, 'tabs'):
            self._apply_tab_styles()

            for tab, bg in (
                (getattr(self, 'tab_stats',    None), c['bg_card']),
                (getattr(self, 'tab_liste',    None), c['bg_card']),
                (getattr(self, 'tab_attente',  None), c['bg_card']),
                (getattr(self, 'tab_nouveau',  None), c['bg_main']),
                (getattr(self, 'tab_encours',  None), c['bg_card']),
            ):
                if tab:
                    tab.setStyleSheet(f"QWidget {{ background: {bg}; }}")

            main_frame = self.findChild(QFrame, "MainWhiteFrame")
            if main_frame:
                self._apply_main_frame_style(main_frame)

        if hasattr(self, 'table'):
            self.table.setStyleSheet(RendezVousStyles.table())

        # ── Titre haut ────────────────────────────────────────────────────
        if hasattr(self, '_titre_label'):
            self._titre_label.setStyleSheet(
                f"font-size: 18px; font-weight: bold; color: {c['primary']};"
            )

        # ── Quick actions ─────────────────────────────────────────────────
        for btn in (
            getattr(self, 'btn_add',          None),
            getattr(self, 'btn_notification', None),
            getattr(self, 'btn_export',       None),
            getattr(self, 'btn_import',       None),
        ):
            if btn:
                color_key = btn.property("color_key") or "primary"
                color = c.get(color_key, c["primary"])
                btn.setIcon(qta.icon(btn.property("icon_name") or "fa5s.circle", color=color))
                btn.setStyleSheet(f"""
                    QPushButton#QuickActionButton {{
                        background: {c['bg_card']};
                        border: none; border-radius: 8px;
                        padding-left: 15px; text-align: left;
                        font-size: 12px; font-weight: 600;
                        color: {c['text_primary']};
                    }}
                    QPushButton#QuickActionButton:hover {{ background: {c['hover']}; }}
                """)

        # ── Formulaire header ─────────────────────────────────────────────
        if hasattr(self, '_form_header_frame'):
            self._form_header_frame.setStyleSheet(
                f"background-color: {c['bg_card']}; border-radius: 14px; border: none;"
            )
        if hasattr(self, '_form_icon_box'):
            self._form_icon_box.setStyleSheet(
                f"background-color: {c['bg_main']}; border-radius: 10px;"
                f" border: 1px solid {c['border_light']};"
            )
        if hasattr(self, '_form_ico_lbl'):
            self._form_ico_lbl.setPixmap(
                qta.icon("fa5s.calendar-check", color=c['primary']).pixmap(22, 22)
            )
        if hasattr(self, '_form_lbl_main'):
            self._form_lbl_main.setStyleSheet(
                f"font-size: 17px; font-weight: bold; color: {c['text_primary']};"
                " background: transparent; border: none;"
            )
        if hasattr(self, '_form_lbl_sub'):
            self._form_lbl_sub.setStyleSheet(
                f"font-size: 12px; color: {c['text_muted']}; background: transparent; border: none;"
            )
        if hasattr(self, '_form_btn_cancel'):
            self._form_btn_cancel.setIcon(qta.icon("fa5s.times", color=c['text_secondary']))
            self._form_btn_cancel.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['bg_main']};
                    color: {c['text_secondary']};
                    border: 1.5px solid {c['border']};
                    border-radius: 10px;
                    font-size: 13px; font-weight: 500;
                }}
                QPushButton:hover {{ background-color: {c['hover']}; }}
            """)
        if hasattr(self, 'form_btn_save'):
            self._apply_form_save_btn_style()

        # ── Formulaire card fields ────────────────────────────────────────
        if hasattr(self, '_form_card_fields'):
            self._form_card_fields.setStyleSheet(f"""
                QFrame {{
                    background-color: {c['bg_card']};
                    border: 1.5px solid {c['border_light']};
                    border-radius: 14px;
                }}
            """)
        if hasattr(self, '_form_ico_section'):
            self._form_ico_section.setPixmap(
                qta.icon("fa5s.clipboard-list", color=c['primary']).pixmap(16, 16)
            )
        if hasattr(self, '_form_lbl_section'):
            self._form_lbl_section.setStyleSheet(
                f"font-size: 14px; font-weight: bold; color: {c['primary']};"
                " background: transparent; border: none;"
            )

        # ── Formulaire card info bas ──────────────────────────────────────
        if hasattr(self, '_form_card_bas'):
            self._form_card_bas.setStyleSheet(f"""
                QFrame {{
                    background-color: {c['primary_light']};
                    border: 1.5px solid {c['border_light']};
                    border-radius: 14px;
                }}
            """)
        if hasattr(self, '_form_ico_bas_frame'):
            self._form_ico_bas_frame.setStyleSheet(
                f"background-color: {c['primary']}; border-radius: 18px;"
            )
        if hasattr(self, '_form_ico_bas_lbl'):
            self._form_ico_bas_lbl.setPixmap(
                qta.icon("fa5s.info", color=c['text_inverse']).pixmap(14, 14)
            )
        if hasattr(self, '_form_lbl_bas_title'):
            self._form_lbl_bas_title.setStyleSheet(
                f"font-size: 13px; font-weight: bold; color: {c['primary']}; background: transparent;"
            )
        if hasattr(self, '_form_lbl_bas_desc'):
            self._form_lbl_bas_desc.setStyleSheet(
                f"font-size: 11px; color: {c['text_secondary']}; background: transparent;"
            )

        # ── Registre champs ───────────────────────────────────────────────
        if hasattr(self, '_field_registry'):
            for entry in self._field_registry:
                self._refresh_field(entry, c)
            for w in (
                getattr(self, 'form_combo_visite',   None),
                getattr(self, 'form_combo_personnel', None),
                getattr(self, 'form_combo_statut',   None),
                getattr(self, 'form_combo_acte',     None),
                getattr(self, 'form_edit_date',      None),
                getattr(self, 'form_edit_code_rdv',  None),
                getattr(self, 'form_edit_code_visite', None),
                getattr(self, 'form_edit_session',   None),
            ):
                if w:
                    self._clear_widget_style(w, c)

        # ── Vue patients en attente ───────────────────────────────────────
        if hasattr(self, 'vue_attente'):
            fn = getattr(self.vue_attente, '_apply_theme', None)
            if fn:
                try:
                    fn()
                except Exception:
                    pass

    def charger_rendez_vous(self, code_session: str):
        """Charge les rendez-vous"""
        self.code_session = code_session

        if hasattr(self, 'vue_attente'):
            self.vue_attente.code_session = code_session

        rendez_vous = self.ctrl.lister_rendez_vous(self.code_session)
        self._remplir_table(rendez_vous)
        self._mettre_a_jour_stats()
        self._mettre_a_jour_graphe()

        # Recharger les combos du formulaire "Nouveau" avec la session active
        self._recharger_form_nouveau(code_session)

        if hasattr(self, 'vue_attente'):
            self.vue_attente.charger_patients()

        # Recharger l'onglet "Rendez-vous en cours"
        self._charger_rdv_en_cours()

    def _remplir_table(self, rendez_vous: list):
        """Remplit le tableau"""
        self.table.setRowCount(0)

        for rdv in rendez_vous:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(rdv.code_rendez_vous)))

            nom = getattr(rdv, "patient_nom", "")
            prenom = getattr(rdv, "patient_prenom", "")
            nom_complet = f"{nom} {prenom}".strip() or "Patient inconnu"
            self.table.setItem(row, 1, QTableWidgetItem(nom_complet))

            personnel_nom = getattr(rdv, "personnel_nom", "")
            personnel_prenom = getattr(rdv, "personnel_prenom", "")
            personnel = f"{personnel_nom} {personnel_prenom}".strip() or str(rdv.code_personnel or "-")
            self.table.setItem(row, 2, QTableWidgetItem(personnel))

            date_val = rdv.date_rendez_vous
            date_str = date_val.strftime("%d/%m/%Y %H:%M") if hasattr(date_val, "strftime") else str(date_val)
            self.table.setItem(row, 3, QTableWidgetItem(date_str))

            badge = StatusBadge()
            badge.set_status(getattr(rdv, "statut_rendez_vous", "attente"))
            self.table.setCellWidget(row, 4, badge)

            self._ajouter_boutons_actions(row, rdv)

    def _mettre_a_jour_stats(self):
        """Met à jour toutes les statistiques de l'onglet."""
        if not self.code_session:
            return
        s = self.code_session

        # KPI cards
        self.card_jour.value_label.setText(str(self.ctrl.obtenir_rendez_vous_aujourd_hui(s)))
        self.card_session.value_label.setText(str(self.ctrl.obtenir_total_rendez_vous_session(s)))
        attente = self.ctrl.obtenir_patients_attente_rendez_vous(s) or []
        self.card_attente.value_label.setText(str(len(attente)))

        # Lignes détail
        try:
            self._stat_confirmes._val_label.setText(str(self.ctrl.obtenir_rendez_vous_confirmes(s)))
        except Exception:
            pass
        try:
            self._stat_termines._val_label.setText(str(self.ctrl.obtenir_rendez_vous_termines(s)))
        except Exception:
            pass
        try:
            self._stat_annules._val_label.setText(str(self.ctrl.obtenir_rendez_vous_annules(s)))
        except Exception:
            pass
        try:
            self._stat_reportes._val_label.setText(str(self.ctrl.obtenir_rendez_vous_reportes(s)))
        except Exception:
            pass
        try:
            self._stat_absents._val_label.setText(str(self.ctrl.obtenir_rendez_vous_absents(s)))
        except Exception:
            pass
        try:
            self._stat_en_retard._val_label.setText(str(self.ctrl.obtenir_nombre_rendez_vous_en_retard(s)))
        except Exception:
            pass
        try:
            taux_p = self.ctrl.obtenir_taux_presence(s)
            self._stat_taux_pres._val_label.setText(f"{round(taux_p * 100)} %")
        except Exception:
            pass
        try:
            taux_c = self.ctrl.obtenir_taux_conversion(s)
            self._stat_taux_conv._val_label.setText(f"{round(taux_c * 100)} %")
        except Exception:
            pass

    def _mettre_a_jour_graphe(self):
        """Met à jour le graphe"""
        if not self.code_session:
            return
        stats = self.ctrl.obtenir_rendez_vous_par_mois(self.code_session)
        self.graphe.update_graph(stats)

    def _rafraichir_apres_rdv(self):
        """Rafraîchit après création de RDV"""
        if self.code_session:
            self.charger_rendez_vous(self.code_session)

    def _ouvrir_formulaire_rendez_vous(self):
        """Ouvre le formulaire de création"""
        dialog = RendezVousFormDialog(
            controleur=self.ctrl,
            code_session=self.code_session,
            rendez_vous_obj=None,
            parent=self,
        )
        if dialog.exec():
            self.charger_rendez_vous(self.code_session)

    def _action_voir(self, rdv):
        """Voir les détails"""
        from .detail_rendez_vous_modal import DetailsRendezVousModal
        modal = DetailsRendezVousModal(self, rdv.code_rendez_vous, self.ctrl)
        modal.exec()

    def _action_modifier(self, rdv):
        """Modifier un RDV"""
        dialog = RendezVousFormDialog(
            controleur=self.ctrl,
            code_session=self.code_session,
            rendez_vous_obj=rdv,
            parent=self,
        )
        if dialog.exec():
            self.charger_rendez_vous(self.code_session)

    def _action_supprimer(self, rdv):
        """Supprimer un RDV"""
        rep = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous supprimer le rendez-vous {rdv.code_rendez_vous} ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if rep != QMessageBox.Yes:
            return

        ok, msg = self.ctrl.supprimer_rendez_vous(rdv.code_rendez_vous)
        if ok:
            QMessageBox.information(self, "Succès", msg)
            self.charger_rendez_vous(self.code_session)
        else:
            QMessageBox.critical(self, "Erreur", msg)

    def _make_handler(self, func, rdv):
        def handler():
            func(rdv)
        return handler

    def _ajouter_boutons_actions(self, row: int, rdv):
        """Ajoute les boutons d'action"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        c = theme_manager.colors()
        btn_view = QPushButton(qta.icon("fa5s.eye", color=c["info"]), "")
        btn_edit = QPushButton(qta.icon("fa5s.edit", color=c["primary"]), "")
        btn_delete = QPushButton(qta.icon("fa5s.trash-alt", color=c["danger"]), "")

        btn_style = RendezVousStyles.button_table_action()
        for btn in [btn_view, btn_edit, btn_delete]:
            btn.setFixedSize(26, 26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(btn_style)
            layout.addWidget(btn)

        btn_view.clicked.connect(self._make_handler(self._action_voir, rdv))
        btn_edit.clicked.connect(self._make_handler(self._action_modifier, rdv))
        btn_delete.clicked.connect(self._make_handler(self._action_supprimer, rdv))

        self.table.setCellWidget(row, 5, container)

    @staticmethod
    def pretty_status(statut: str) -> str:
        """Formate le statut"""
        mapping = {
            "attente": "En attente",
            "confirme": "Confirmé",
            "en_cours": "En cours",
            "termine": "Terminé",
            "annule": "Annulé",
            "absent": "Absent",
            "reporte": "Reporté",
        }
        return mapping.get(str(statut or "").strip().lower(), str(statut or "-"))

    def _setup_auto_refresh_rdv(self):
        """Configure un timer pour traiter automatiquement les RDV du jour toutes les 30 secondes."""
        self._rdv_modals_traites = set()  # codes rdv déjà présentés en modal ce jour
        self._rdv_timer = QTimer(self)
        self._rdv_timer.setInterval(30_000)
        self._rdv_timer.timeout.connect(self._traiter_rdv_automatique)
        self._rdv_timer.start()

    def _traiter_rdv_automatique(self):
        """Traite automatiquement les RDV du jour en arrière-plan."""
        if not self.code_session:
            return
        try:
            traites = self.ctrl.traiter_rdv_du_jour(self.code_session)
            if traites > 0:
                print(f"[RDV Auto] {traites} patient(s) placé(s) en file d'attente automatiquement.")
                if self.tabs.currentIndex() == 2:
                    self._charger_rdv_en_cours()
        except Exception as e:
            print(f"[RDV Auto] Erreur traitement automatique: {e}")

        # Détecter les RDV de première visite (sans acte) arrivés aujourd'hui
        try:
            rdvs_sans_acte = self.ctrl.rdv_du_jour_sans_acte(self.code_session)
            for rdv in rdvs_sans_acte:
                code_rdv = rdv.get('code_rendez_vous', '')
                if code_rdv and code_rdv not in self._rdv_modals_traites:
                    self._rdv_modals_traites.add(code_rdv)
                    self._afficher_modal_rdv_arrive(rdv)
        except Exception as e:
            print(f"[RDV Auto] Erreur détection sans-acte: {e}")

    def ouvrir_nouveau_avec_visite(self, code_visite: str):
        """
        Navigue vers l'onglet 'Nouveau rendez-vous' et pré-sélectionne
        la visite correspondant à code_visite (création depuis formulaire visite).
        """
        if hasattr(self, 'tabs'):
            self.tabs.setCurrentIndex(3)
        if code_visite and hasattr(self, 'form_combo_visite'):
            for i in range(self.form_combo_visite.count()):
                data = self.form_combo_visite.itemData(i)
                cv = data.get('code_visite') if isinstance(data, dict) else data
                if cv == code_visite:
                    self.form_combo_visite.setCurrentIndex(i)
                    break

    def _afficher_modal_rdv_arrive(self, rdv: dict):
        """
        Affiche un dialog quand un RDV de première visite (sans acte) est arrivé.
        3 choix : envoyer en consultation | annuler | reporter.
        """
        from views.shared.message_box import CustomMessageBox
        from PySide6.QtCore import QDateTime

        code_rdv   = rdv.get('code_rendez_vous', '')
        code_visite = rdv.get('code_visite', '')
        nom        = rdv.get('nom', '')
        prenom     = rdv.get('prenom', '')
        date_rdv   = rdv.get('date_rendez_vous', '')

        dialog = QDialog(self)
        dialog.setWindowTitle("Rendez-vous arrivé")
        dialog.setMinimumWidth(420)
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        _c = theme_manager.colors()
        dialog.setStyleSheet(f"background: {_c['bg_card']}; color: {_c['text_primary']};")

        # En-tête
        titre = QLabel(f"Le rendez-vous de {nom} {prenom} est arrivé")
        titre.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {_c['text_primary']};")
        titre.setWordWrap(True)
        layout.addWidget(titre)

        sous_titre = QLabel(f"Prévu le : {date_rdv}")
        sous_titre.setStyleSheet(f"font-size: 11px; color: {_c['text_secondary']};")
        layout.addWidget(sous_titre)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {_c['border']};")
        layout.addWidget(sep)

        layout.addWidget(QLabel("Que souhaitez-vous faire ?"))

        # Zone reporter (cachée par défaut)
        reporter_frame = QFrame()
        reporter_layout = QVBoxLayout(reporter_frame)
        reporter_layout.setContentsMargins(0, 6, 0, 0)
        lbl_date = QLabel("Nouvelle date :")
        lbl_date.setStyleSheet("font-size: 11px; font-weight: 600;")
        reporter_layout.addWidget(lbl_date)
        date_edit = QDateTimeEdit()
        date_edit.setDisplayFormat("dd/MM/yyyy HH:mm")
        date_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
        date_edit.setCalendarPopup(True)
        reporter_layout.addWidget(date_edit)
        reporter_frame.setVisible(False)
        layout.addWidget(reporter_frame)

        # Boutons
        btn_layout = QHBoxLayout()

        _btn_style = "font-weight:700; padding:8px 14px; border-radius:6px; border:none; color:#fff;"
        btn_consultation = QPushButton("Envoyer en consultation")
        btn_consultation.setStyleSheet(f"background:{_c['info']}; {_btn_style}")

        btn_reporter = QPushButton("Reporter")
        btn_reporter.setStyleSheet(f"background:{_c['warning']}; {_btn_style}")

        btn_annuler = QPushButton("Annuler le RDV")
        btn_annuler.setStyleSheet(f"background:{_c['danger']}; {_btn_style}")

        btn_layout.addWidget(btn_consultation)
        btn_layout.addWidget(btn_reporter)
        btn_layout.addWidget(btn_annuler)
        layout.addLayout(btn_layout)

        # Bouton confirmer reporter (caché jusqu'à clic sur Reporter)
        btn_confirmer_report = QPushButton("Confirmer le report")
        btn_confirmer_report.setStyleSheet(f"background:{_c['success']}; {_btn_style}")
        btn_confirmer_report.setVisible(False)
        layout.addWidget(btn_confirmer_report)

        def on_consultation():
            ok, msg = self.ctrl.traiter_rdv_arrive(code_rdv, 'consultation')
            CustomMessageBox("Résultat", msg, ok, self).exec()
            if ok:
                self._rafraichir_apres_rdv()
            dialog.accept()

        def on_reporter():
            reporter_frame.setVisible(True)
            btn_confirmer_report.setVisible(True)
            btn_reporter.setEnabled(False)

        def on_confirmer_report():
            nouvelle_date = date_edit.dateTime().toPython()
            ok, msg = self.ctrl.traiter_rdv_arrive(code_rdv, 'reporter', nouvelle_date)
            CustomMessageBox("Résultat", msg, ok, self).exec()
            if ok:
                self._rdv_modals_traites.discard(code_rdv)
                self._rafraichir_apres_rdv()
            dialog.accept()

        def on_annuler():
            ok, msg = self.ctrl.traiter_rdv_arrive(code_rdv, 'annuler')
            CustomMessageBox("Résultat", msg, ok, self).exec()
            if ok:
                self._rafraichir_apres_rdv()
            dialog.accept()

        btn_consultation.clicked.connect(on_consultation)
        btn_reporter.clicked.connect(on_reporter)
        btn_confirmer_report.clicked.connect(on_confirmer_report)
        btn_annuler.clicked.connect(on_annuler)

        dialog.exec()
