# Standard library imports
import logging

# Third-party imports
import qtawesome as qta
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QPoint, QEasingCurve, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QHeaderView, QFrame, QLabel,
    QScrollArea, QTableWidgetItem, QDialog, QGraphicsDropShadowEffect
)

# Local imports
from .graphe_visite import VisiteAnalyseGraph, AgeAnalyseGraph
from .details_visite_modal import DetailsVisiteModal
from .visite_form import VisiteFormDialog
from .notification_panel import NotificationPanel
from .performance_dashboard import PerformanceDashboard
from views.shared.theme_manager import theme_manager
from views.visite.styles import VisiteStyles


class AnimatedFrame(QFrame):
    """Frame personnalisé avec animation de survol."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_animation()

    def setup_animation(self):
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(0, 4)
        self.shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(self.shadow)

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

    def enterEvent(self, event):
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(QPoint(self.pos().x(), self.pos().y() - 5))
        self.shadow.setBlurRadius(25)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(QPoint(self.pos().x(), self.pos().y() + 5))
        self.shadow.setBlurRadius(15)
        self.animation.start()
        super().leaveEvent(event)


class VisiteView(QWidget):
    """Vue principale pour la gestion des visites médicales."""

    def __init__(self, visite_controleur):
        super().__init__()
        self.ctrl = visite_controleur
        self.logger = logging.getLogger(__name__)

        self.init_ui()
        self.notification_panel = NotificationPanel(controleur=self.ctrl, parent=self)
        self.load_data()
        self.setup_auto_refresh()

        # Appliquer le thème initial et écouter les changements
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def apply_theme(self):
        """Applique le thème actif à tous les composants de la vue visite."""
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_main']};")
        self.search_bar.setStyleSheet(VisiteStyles.search_bar())
        self.btn_add.setStyleSheet(VisiteStyles.button_primary())
        self.btn_add.setIcon(qta.icon("fa5s.plus-square", color=c['text_inverse']))
        round_btn = VisiteStyles.button_secondary()
        for btn, ico in [(self.btn_dashboard, "fa5s.tachometer-alt"), (self.btn_notif, "fa5s.bell")]:
            btn.setStyleSheet(round_btn)
            btn.setIcon(qta.icon(ico, color=c['primary']))
        for frame in [self.frame_mensuel, self.frame_age, self.frame_table, self.frame_flux]:
            frame.setStyleSheet(VisiteStyles.card())
            frame._icon_lbl.setPixmap(qta.icon(frame._icon_name, color=c['primary']).pixmap(QSize(16, 16)))
            frame._title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_primary']}; font-size:12px; border:none;")
            frame._separator.setStyleSheet(f"background:{c['border_light']}; border:none;")
        self.table.setStyleSheet(VisiteStyles.table())
        self.table.verticalScrollBar().setStyleSheet(VisiteStyles.scrollbar())

    # ── Timer ──────────────────────────────────────────────────────────
    def setup_auto_refresh(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.safe_load_data)
        self.timer.start(30_000)

    def safe_load_data(self):
        try:
            self.load_data()
        except Exception as e:
            self.logger.error(f"Erreur rafraîchissement automatique: {e}")

    # ── Construction UI ────────────────────────────────────────────────
    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(12)

        self.setup_top_bar()
        self._setup_graphs_section()
        self._setup_bottom_section()

    def _setup_graphs_section(self):
        graphs_layout = QHBoxLayout()
        graphs_layout.setSpacing(12)

        self.frame_mensuel = self.creer_cadre_arondi("Flux Mensuel des Visites", "fa5s.chart-line")
        self.frame_age     = self.creer_cadre_arondi("Analyse par Tranches d'Âge", "fa5s.chart-pie")

        self.graph_mensuel_plot = VisiteAnalyseGraph(self.frame_mensuel)
        self.frame_mensuel.layout().addWidget(self.graph_mensuel_plot)

        self.graph_age_plot = AgeAnalyseGraph(self.frame_age)
        self.frame_age.layout().addWidget(self.graph_age_plot)

        self.frame_mensuel.setMinimumHeight(220)
        self.frame_age.setMinimumHeight(220)

        graphs_layout.addWidget(self.frame_mensuel, 1)
        graphs_layout.addWidget(self.frame_age, 1)
        self.main_layout.addLayout(graphs_layout, 2)

    def _setup_bottom_section(self):
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        self.frame_table = self.creer_cadre_arondi("Registre des Visites", "fa5s.list-ul")
        self.setup_table_minimal()

        self.frame_flux = self.creer_cadre_arondi("Suivi des Services (Workflow)", "fa5s.project-diagram")
        self.setup_workflow_rings()

        bottom_layout.addWidget(self.frame_table, 4)
        bottom_layout.addWidget(self.frame_flux, 6)
        self.main_layout.addLayout(bottom_layout, 3)

    # ── Barre du haut ──────────────────────────────────────────────────
    def setup_top_bar(self):
        hbox = QHBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(" Rechercher un patient ou un code de visite...")
        self.search_bar.setFixedHeight(45)
        self.search_bar.textChanged.connect(self.filtrer_visite)

        self.btn_add = QPushButton(qta.icon("fa5s.plus-square", color="white"), " Enregistrer")
        self.btn_add.setFixedSize(150, 45)
        self.btn_add.clicked.connect(self.ouvrir_formulaire_visite)

        self.btn_dashboard = QPushButton(qta.icon("fa5s.tachometer-alt", color=theme_manager.colors()['primary']), "")
        self.btn_dashboard.setFixedSize(45, 45)
        self.btn_dashboard.setToolTip("Tableau de bord performance")
        self.btn_dashboard.clicked.connect(self._ouvrir_dashboard)

        self.btn_notif = QPushButton(qta.icon("fa5s.bell", color=theme_manager.colors()['primary']), "")
        self.btn_notif.setFixedSize(45, 45)
        self.btn_notif.clicked.connect(self._toggle_notifications)

        hbox.addWidget(self.search_bar)
        hbox.addWidget(self.btn_add)
        hbox.addSpacing(10)
        hbox.addWidget(self.btn_dashboard)
        hbox.addWidget(self.btn_notif)
        self.main_layout.addLayout(hbox)

    # ── Cadre arrondi ──────────────────────────────────────────────────
    def creer_cadre_arondi(self, titre: str, icone_name: str) -> AnimatedFrame:
        c = theme_manager.colors()
        frame = AnimatedFrame()
        frame._icon_name = icone_name
        frame.setStyleSheet(VisiteStyles.card())
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icone_name, color=c['primary']).pixmap(QSize(16, 16)))
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        frame._icon_lbl = icon_lbl
        title_lbl = QLabel(titre)
        title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_primary']}; font-size:12px; border:none;")
        frame._title_lbl = title_lbl
        header.addWidget(icon_lbl)
        header.addSpacing(6)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{c['border_light']}; border:none;")
        frame._separator = sep
        layout.addWidget(sep)

        return frame

    # ── Table ──────────────────────────────────────────────────────────
    def setup_table_minimal(self):
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Code", "Patient", "Statut", "Actions"])
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.apply_modern_scrollbar(self.table)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 100)

        self.table.setStyleSheet(VisiteStyles.table())
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setAlternatingRowColors(True)
        self.frame_table.layout().addWidget(self.table)

    def apply_modern_scrollbar(self, widget):
        widget.verticalScrollBar().setStyleSheet(VisiteStyles.scrollbar())

    # ── Workflow ───────────────────────────────────────────────────────
    def setup_workflow_rings(self):
        self.workflow_scroll = QScrollArea()
        self.workflow_scroll.setWidgetResizable(True)
        self.workflow_scroll.setStyleSheet("border: none; background: transparent;")

        self.workflow_container = QWidget()
        self.workflow_container.setStyleSheet("background: transparent;")
        self.workflow_layout = QVBoxLayout(self.workflow_container)
        self.workflow_layout.setContentsMargins(4, 4, 4, 4)
        self.workflow_layout.setSpacing(8)
        self.workflow_layout.setAlignment(Qt.AlignTop)

        self.workflow_scroll.setWidget(self.workflow_container)
        self.frame_flux.layout().addWidget(self.workflow_scroll)

    # ── Notifications ──────────────────────────────────────────────────
    def _toggle_notifications(self):
        self.notification_panel.toggle()
        count = self.notification_panel.get_alert_count()
        if count > 0:
            c = theme_manager.colors()
            self.btn_notif.setText(f" {count}")
            self.btn_notif.setStyleSheet(
                f"background: {c.get('danger_bg','#FEF2F2')}; border: 2px solid {c['danger']}; "
                f"border-radius: 22px; color: {c['danger']}; font-weight: 800; font-size: 11px;"
            )
        else:
            c = theme_manager.colors()
            self.btn_notif.setText("")
            self.btn_notif.setStyleSheet(VisiteStyles.button_secondary())

    def _ouvrir_dashboard(self):
        try:
            dlg = PerformanceDashboard(controleur=self.ctrl, parent=self)
            dlg.exec()
        except Exception as e:
            self.logger.error(f"Erreur ouverture dashboard: {e}")

    # ── Mise à jour UI ─────────────────────────────────────────────────
    def update_table_ui(self, visites):
        self.table.setRowCount(0)
        for v in visites:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(v.get_code_visite()).upper()))
            nom_complet = (
                f"{getattr(v, 'nom_patient', '')} {getattr(v, 'prenom_patient', '')}"
                .strip().title()
            )
            self.table.setItem(row, 1, QTableWidgetItem(nom_complet))

            item_statut = QTableWidgetItem(str(v.get_statut_visite()).capitalize())
            item_statut.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, item_statut)

            actions_container = QWidget()
            actions_layout = QHBoxLayout(actions_container)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)

            c = theme_manager.colors()
            btn_view   = QPushButton(qta.icon("fa5s.eye",       color=c['info']), "")
            btn_edit   = QPushButton(qta.icon("fa5s.edit",      color=c['primary']), "")
            btn_consult = QPushButton(qta.icon("fa5s.stethoscope", color=c['success']),"")
            btn_delete = QPushButton(qta.icon("fa5s.trash-alt", color=c['danger']), "")

            btn_style = VisiteStyles.button_table_action()
            for btn in [btn_view, btn_edit,btn_consult, btn_delete]:
                btn.setFixedSize(26, 26)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet(btn_style)
                actions_layout.addWidget(btn)

            btn_view.clicked.connect(self.create_action_handler(self.action_voir,        v))
            btn_edit.clicked.connect(self.create_action_handler(self.action_editer,      v))
            btn_consult.clicked.connect(self.create_action_handler(self._ouvrir_consultation, v))
            btn_delete.clicked.connect(self.create_action_handler(self.action_supprimer, v))

            self.table.setCellWidget(row, 3, actions_container)

    def update_workflow_ui(self, visites_objets):
        from .workflow_tracker import PatientRowWidget

        while self.workflow_layout.count():
            item = self.workflow_layout.takeAt(0)
            if item.widget():
                if hasattr(item.widget(), 'cleanup'):
                    item.widget().cleanup()
                item.widget().deleteLater()

        count = 0
        for v in visites_objets:
            statut_p = v.get_statut_patient() or ""
            statut_v = v.get_statut_visite()  or ""

            if statut_p.lower() != "libéré" and statut_v.lower() != "terminée":
                nom_complet = (
                    f"{getattr(v, 'nom_patient', '')} {getattr(v, 'prenom_patient', '')}"
                    .strip()
                )
                row = PatientRowWidget(
                    patient_name=nom_complet,
                    statut_db=statut_p,
                    controleur=self.ctrl,
                    code_visite=v.get_code_visite()
                )
                self.workflow_layout.addWidget(row)
                count += 1

        if count == 0:
            empty_lbl = QLabel("Aucune visite active dans les services")
            empty_lbl.setStyleSheet(
                f"color: {theme_manager.colors()['text_muted']}; font-style: italic; font-size: 11px; border: none;"
            )
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.workflow_layout.addWidget(empty_lbl)

    def filtrer_visite(self, texte: str):
        texte = texte.strip()
        if not texte:
            self.load_data()
        else:
            visites = self.ctrl.rechercher_visites(texte)
            self.update_table_ui(visites)

    # ── Chargement des données ─────────────────────────────────────────
    def load_data(self):
        try:
            actif, _ = self.ctrl.verifier_session_active()
            if not actif:
                return

            visites = self.ctrl.obtenir_visites_prioritaires()
            self.update_table_ui(visites)
            self.update_workflow_ui(visites)

            self.graph_mensuel_plot.update_graph(self.ctrl.obtenir_stats_mensuelles())
            self.graph_age_plot.update_graph(self.ctrl.get_stat_visites_par_age())

        except Exception as e:
            self.logger.error(f"Erreur lors du chargement: {e}")

    # ── Handlers actions ───────────────────────────────────────────────
    def create_action_handler(self, action_func, visite_obj):
        def handler():
            action_func(visite_obj)
        return handler

    def action_voir(self, visite):
        try:
            details = self.ctrl.obtenir_dossier_complet_visite(visite.get_code_visite())
            patient_name = (
                f"{getattr(visite, 'nom_patient', '')} {getattr(visite, 'prenom_patient', '')}"
                .strip()
            )
            modal = DetailsVisiteModal(
                self, visite.get_code_visite(), patient_name,
                details, self.ctrl.get_cabinet_info()
            )
            modal.exec()
        except Exception as e:
            self.logger.error(f"Erreur ouverture détails: {e}")

    def ouvrir_formulaire_visite(self, visite_obj=None):
        try:
            dialog = VisiteFormDialog(
                controleur=self.ctrl, visite_obj=visite_obj, parent=self
            )
            if dialog.exec() == QDialog.Accepted:
                self.load_data()
        except Exception as e:
            self.logger.error(f"Erreur formulaire: {e}")

    def action_editer(self, visite):
        self.ouvrir_formulaire_visite(visite)

    def action_supprimer(self, visite):
        self.logger.info(f"Suppression demandée pour: {visite.get_code_visite()}")
        pass
    
    def _ouvrir_consultation(self, code_visite: str, code_personnel: str):
        from views.consultation.consultation_form import ConsultationFormDialog
        dialog = ConsultationFormDialog(
            controleur     = self.consultation_ctrl,
            code_session   = self.code_session,
            code_visite    = code_visite,      # ← pré-rempli et verrouillé
            code_personnel = code_personnel,   # ← pré-sélectionné
            parent         = self
        )
        if dialog.exec():
            self.rafraichir()  # ou votre méthode de rechargement