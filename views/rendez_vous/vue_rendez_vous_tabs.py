"""
Vue Rendez-vous avec architecture à onglets.
4 onglets : Statistiques, Liste, Patients en attente, Nouveau
"""
import qtawesome as qta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QFrame, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QMessageBox,
    QComboBox, QLineEdit, QDateTimeEdit, QTextEdit
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
        tab.setStyleSheet("background: white;")
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
                background-color: white;
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding: 4px;
            }}
            QFrame#RdvCard:hover {{
                border-color: {c['primary']};
                background-color: {c.get('hover', '#f5f5f5')};
            }}
        """)
        card.setMinimumHeight(80)

        hbox = QHBoxLayout(card)
        hbox.setContentsMargins(16, 12, 16, 12)
        hbox.setSpacing(16)

        # --- Infos patient ---
        nom_patient = f"{rdv.get('patient_nom', '')} {rdv.get('patient_prenom', '')}".strip() or "Patient inconnu"
        hbox.addWidget(self._info_block("fa5s.user", "#2563EB", nom_patient, c, bold=True, min_width=160))

        # --- Infos personnel ---
        nom_personnel = f"{rdv.get('personnel_nom', '')} {rdv.get('personnel_prenom', '')}".strip() or "-"
        fonction = rdv.get('personnel_fonction', '') or ''
        personnel_text = nom_personnel + (f"  ({fonction})" if fonction else "")
        hbox.addWidget(self._info_block("fa5s.user-md", "#10B981", personnel_text, c, min_width=160))

        # --- Type acte ---
        type_acte = rdv.get('type_acte', '') or rdv.get('code_acte', '') or '—'
        hbox.addWidget(self._info_block("fa5s.clipboard-list", "#D97706", type_acte, c, min_width=120))

        hbox.addStretch()

        # --- Countdown ---
        date_rdv = rdv.get('date_rendez_vous')
        countdown_text = self._compute_countdown(date_rdv)
        date_str = date_rdv.strftime("%d/%m/%Y %H:%M") if hasattr(date_rdv, 'strftime') else str(date_rdv or '—')
        if countdown_text == "Passé":
            cd_color = "#e74c3c"
        elif 'min' in countdown_text and 'j' not in countdown_text and 'h' not in countdown_text:
            cd_color = "#f39c12"
        else:
            cd_color = "#2980b9"
        hbox.addWidget(self._info_block("fa5s.clock", cd_color, f"{countdown_text}  {date_str}", c, min_width=140))

        # --- Statut badge ---
        statut_raw = rdv.get('statut_rendez_vous', 'attente')
        statut_labels = {
            "attente": ("En attente", "#f39c12"),
            "confirme": ("Confirmé", "#27ae60"),
            "en_cours": ("En cours", "#2980b9"),
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
        btn_annuler.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e74c3c;
                border: 1.5px solid #e74c3c;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #fdf0f0;
            }
        """)
        btn_annuler.clicked.connect(lambda checked=False, crdv=code_rdv: self._annuler_rdv_encours(crdv))

        # --- Bouton Reporter ---
        btn_reporter = QPushButton("  Reporter")
        btn_reporter.setIcon(self._circle_icon("fa5s.calendar-plus", "white", "#f39c12", 22))
        btn_reporter.setIconSize(QSize(22, 22))
        btn_reporter.setFixedHeight(34)
        btn_reporter.setMinimumWidth(105)
        btn_reporter.setCursor(Qt.PointingHandCursor)
        btn_reporter.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #f39c12;
                border: 1.5px solid #f39c12;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #fdf8f0;
            }
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
        dialog.setStyleSheet(f"background: white; color: {c['text_primary']};")

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
                background: white;
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
        """Onglet Statistiques + Graphe"""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignTop)

        # KPI Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        self.card_jour = self._create_stat_card("Rendez-vous du Jour", "0", "fa5s.calendar-day", "primary")
        self.card_session = self._create_stat_card("Total Session", "0", "fa5s.calendar-check", "success")
        self.card_attente = self._create_stat_card("Patients en Attente", "0", "fa5s.user-clock", "warning")

        stats_layout.addWidget(self.card_jour, 1)
        stats_layout.addWidget(self.card_session, 1)
        stats_layout.addWidget(self.card_attente, 1)

        layout.addLayout(stats_layout)

        # Graphe
        graph_frame = QFrame()
        graph_frame.setStyleSheet(RendezVousStyles.card())
        graph_layout = QVBoxLayout(graph_frame)
        graph_layout.setContentsMargins(14, 10, 14, 10)

        self.graphe = RendezVousAnalyseGraph(parent=graph_frame, width=10, height=5)
        graph_layout.addWidget(self.graphe)

        layout.addWidget(graph_frame, 1)

        return tab

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
        tab.setStyleSheet("background: white;")
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
        tab.setStyleSheet("background: white;")
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
        tab.setStyleSheet("background: white;")
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
        widget.setStyleSheet("background: white;")
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
        """Header avec titre et boutons"""
        c = theme_manager.colors()
        header_frame = QFrame()
        header_frame.setFixedHeight(72)
        header_frame.setStyleSheet(f"""
            background-color: {c['bg_card']};
            border-radius: 14px;
            border: none;
        """)

        layout = QHBoxLayout(header_frame)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(14)

        # Icône
        icon_box = QFrame()
        icon_box.setFixedSize(46, 46)
        icon_box.setStyleSheet(f"""
            background-color: {c['bg_main']};
            border-radius: 10px;
            border: 1px solid {c['border_light']};
        """)
        ib_layout = QHBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setPixmap(qta.icon("fa5s.calendar-check", color=c['primary']).pixmap(22, 22))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ib_layout.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        # Titre
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_main = QLabel("Enregistrement d'un rendez-vous")
        lbl_main.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {c['text_primary']}; background: transparent; border: none;")
        lbl_sub = QLabel("Saisissez les informations du rendez-vous")
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {c['text_muted']}; background: transparent; border: none;")
        title_col.addWidget(lbl_main)
        title_col.addWidget(lbl_sub)

        layout.addWidget(icon_box)
        layout.addLayout(title_col)
        layout.addStretch()

        # Bouton Annuler
        btn_cancel = QPushButton(qta.icon("fa5s.times", color=c['text_secondary']), " Annuler")
        btn_cancel.setFixedSize(110, 40)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_main']};
                color: {c['text_secondary']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {c['hover']}; }}
        """)
        btn_cancel.clicked.connect(self._reset_form)

        # Bouton Enregistrer
        self.form_btn_save = QPushButton(qta.icon("fa5s.save", color="#ffffff"), " Enregistrer")
        self.form_btn_save.setFixedSize(140, 40)
        self.form_btn_save.setEnabled(False)
        self._apply_form_save_btn_style()
        self.form_btn_save.clicked.connect(self._soumettre_form)

        layout.addWidget(btn_cancel)
        layout.addWidget(self.form_btn_save)
        parent_layout.addWidget(header_frame)

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
        """Card avec les champs en 2 rangées"""
        c = theme_manager.colors()
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1.5px solid {c['border_light']};
                border-radius: 14px;
            }}
        """)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(22, 18, 22, 18)
        vbox.setSpacing(18)

        # Titre section
        hdr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.clipboard-list", color=c['primary']).pixmap(16, 16))
        ico.setStyleSheet("border: none; background: transparent;")
        lbl_t = QLabel("Informations du rendez-vous")
        lbl_t.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {c['primary']};"
            " background: transparent; border: none;"
        )
        hdr.addWidget(ico)
        hdr.addSpacing(8)
        hdr.addWidget(lbl_t)
        hdr.addStretch()
        vbox.addLayout(hdr)

        # Rangée 1: Code | Patient/Visite | Code Visite | Personnel | Session
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        row1.setAlignment(Qt.AlignTop)

        self.form_edit_code_rdv = QLineEdit()
        self.form_edit_code_rdv.setText("AUTO")
        self.form_edit_code_rdv.setEnabled(False)
        vb_code, _ = self._make_field("Code", self.form_edit_code_rdv, "fa5s.hashtag", "#9b59b6")
        row1.addWidget(self._field_widget(vb_code), 1, Qt.AlignTop)

        self.form_combo_visite = QComboBox()
        self.form_combo_visite.addItem("-- Sélectionner un patient --", "")
        vb_visite, self._wrap_visite = self._make_field(
            "Patient / Visite", self.form_combo_visite, "fa5s.user-injured", "#e74c3c"
        )
        self._err_visite = self._err_label()
        vb_visite.addWidget(self._err_visite)
        row1.addWidget(self._field_widget(vb_visite), 1, Qt.AlignTop)

        self.form_edit_code_visite = QLineEdit()
        self.form_edit_code_visite.setEnabled(False)
        self.form_edit_code_visite.setPlaceholderText("Auto-rempli")
        vb_code_visite, _ = self._make_field(
            "Code Visite", self.form_edit_code_visite, "fa5s.shopping-bag", "#3498db"
        )
        row1.addWidget(self._field_widget(vb_code_visite), 1, Qt.AlignTop)

        self.form_combo_personnel = QComboBox()
        self.form_combo_personnel.addItem("-- Sélectionner le personnel --", "")
        vb_personnel, self._wrap_personnel = self._make_field(
            "Personnel", self.form_combo_personnel, "fa5s.user-md", "#1abc9c"
        )
        self._err_personnel = self._err_label()
        vb_personnel.addWidget(self._err_personnel)
        row1.addWidget(self._field_widget(vb_personnel), 1, Qt.AlignTop)

        self.form_edit_session = QLineEdit(self.code_session or "")
        self.form_edit_session.setEnabled(False)
        vb_sess, _ = self._make_field(
            "Code session", self.form_edit_session, "fa5s.graduation-cap", "#9b59b6"
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
            "Date rendez-vous", self.form_edit_date, "fa5s.calendar-alt", "#3498db"
        )
        row2.addWidget(self._field_widget(vb_date), 1, Qt.AlignTop)

        self.form_combo_statut = QComboBox()
        self.form_combo_statut.addItem("-- Sélectionner le statut --", "")
        statuts = [("attente", "En attente"), ("confirme", "Confirmé"), ("en_cours", "En cours"),
                   ("termine", "Terminé"), ("annule", "Annulé"), ("absent", "Absent"), ("reporte", "Reporté")]
        for code, label in statuts:
            self.form_combo_statut.addItem(label, code)
        vb_statut, _ = self._make_field(
            "Statut rendez-vous", self.form_combo_statut, "fa5s.flag", "#e67e22"
        )
        row2.addWidget(self._field_widget(vb_statut), 1, Qt.AlignTop)

        self.form_combo_acte = QComboBox()
        self.form_combo_acte.addItem("-- Sélectionner un acte --", "")
        vb_acte, _ = self._make_field(
            "Code Acte", self.form_combo_acte, "fa5s.file-medical", "#e74c3c"
        )
        row2.addWidget(self._field_widget(vb_acte), 1, Qt.AlignTop)

        vbox.addLayout(row2)
        parent_layout.addWidget(card)

    def _setup_form_info_bas(self, parent_layout):
        """Section info bas"""
        c = theme_manager.colors()
        card = QFrame()
        card.setFixedHeight(80)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c['primary_light']};
                border: 1.5px solid {c['border_light']};
                border-radius: 14px;
            }}
        """)
        hbox = QHBoxLayout(card)
        hbox.setContentsMargins(20, 0, 20, 0)
        hbox.setSpacing(14)

        ico_frame = QFrame()
        ico_frame.setFixedSize(36, 36)
        ico_frame.setStyleSheet(f"background-color: {c['primary']}; border-radius: 18px;")
        ifi = QHBoxLayout(ico_frame)
        ifi.setContentsMargins(0, 0, 0, 0)
        il = QLabel()
        il.setPixmap(qta.icon("fa5s.info", color="#ffffff").pixmap(14, 14))
        il.setAlignment(Qt.AlignCenter)
        ifi.addWidget(il, alignment=Qt.AlignCenter)

        txt = QVBoxLayout()
        txt.setSpacing(2)
        t1 = QLabel("Informations")
        t1.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {c['primary']}; background: transparent;")
        t2 = QLabel("Veuillez remplir tous les champs obligatoires avant d'enregistrer le rendez-vous.")
        t2.setStyleSheet(f"font-size: 11px; color: {c['text_secondary']}; background: transparent;")
        txt.addWidget(t1)
        txt.addWidget(t2)

        hbox.addWidget(ico_frame)
        hbox.addLayout(txt)
        hbox.addStretch()
        parent_layout.addWidget(card)

    def _make_field(self, label_text: str, widget, icon_name: str, icon_color: str,
                    height: int = 42, align_top: bool = False):
        """Retourne (QVBoxLayout, wrapper_QFrame) : label + cadre [badge-icône + widget]."""
        c = theme_manager.colors()
        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {c['text_secondary']};"
            " background: transparent; border: none;"
        )
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
        badge.setStyleSheet(f"background-color: {icon_color}20; border-radius: 7px; border: none;")
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(14, 14))
        ico_lbl.setAlignment(Qt.AlignCenter)
        ico_lbl.setStyleSheet("border: none; background: transparent;")
        bl.addWidget(ico_lbl, alignment=Qt.AlignCenter)

        self._clear_widget_style(widget, c)
        hbox.addWidget(badge, 0, v_align)
        hbox.addWidget(widget, 1)
        vbox.addWidget(wrapper)
        return vbox, wrapper

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
        """Enlève bordure et fond du widget interne — le wrapper reste visible."""
        base = (
            f"border: none; background: transparent;"
            f" font-size: 12px; color: {c['text_primary']};"
        )
        if isinstance(widget, QComboBox):
            widget.setStyleSheet(f"""
                QComboBox {{ {base} padding: 0; min-height: 28px; }}
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
            widget.setStyleSheet(f"QDateTimeEdit {{ {base} padding: 0; }}")
        elif isinstance(widget, QTextEdit):
            widget.setStyleSheet(f"QTextEdit {{ {base} padding: 4px 0; }}")
        else:
            widget.setStyleSheet(f"QLineEdit {{ {base} padding: 0; }}")

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
            for i in range(self.form_combo_visite.count()):
                data = self.form_combo_visite.itemData(i)
                cv = data.get('code_visite') if isinstance(data, dict) else data
                if cv == code_visite:
                    self.form_combo_visite.setCurrentIndex(i)
                    break

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
                background: white;
                border: none;
                border-radius: 8px;
                padding-left: 15px;
                text-align: left;
                font-size: 12px;
                font-weight: 600;
                color: {c['text_primary']};
            }}
            QPushButton#QuickActionButton:hover {{
                background: {c['bg_card']};
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
        """Style du frame principal"""
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame#MainWhiteFrame {{
                background: white;
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
                background: white;
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
        """Applique le thème"""
        c = theme_manager.colors()
        self.setStyleSheet(f"background-color: {c['bg_main']};")

        if hasattr(self, 'tabs'):
            self._apply_tab_styles()
            main_frame = self.findChild(QFrame, "MainWhiteFrame")
            if main_frame:
                self._apply_main_frame_style(main_frame)

        if hasattr(self, 'table'):
            self.table.setStyleSheet(RendezVousStyles.table())

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
        """Met à jour les statistiques"""
        if not self.code_session:
            return
        self.card_jour.value_label.setText(str(self.ctrl.obtenir_rendez_vous_aujourd_hui(self.code_session)))
        self.card_session.value_label.setText(str(self.ctrl.obtenir_total_rendez_vous_session(self.code_session)))
        attente = self.ctrl.obtenir_patients_attente_rendez_vous(self.code_session) or []
        self.card_attente.value_label.setText(str(len(attente)))

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
        self._rdv_timer = QTimer(self)
        self._rdv_timer.setInterval(30_000)  # 30 secondes = 30 000 ms
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
                # Rafraîchir l'onglet "Rendez-vous en cours" si visible
                if self.tabs.currentIndex() == 2:  # Index de l'onglet "Rendez-vous en cours"
                    self._charger_rdv_en_cours()
        except Exception as e:
            print(f"[RDV Auto] Erreur traitement automatique: {e}")
