import qtawesome as qta
from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from views.rendez_vous.animated_stack import AnimatedStack
from views.rendez_vous.graphe_rendez_vous import RendezVousAnalyseGraph
from views.rendez_vous.patients_rendez_vous_attente import PatientsAttenteRendezVousView
from views.rendez_vous.styles import RendezVousStyles
from views.shared.theme_manager import theme_manager


class AnimatedFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_animation()

    def _setup_animation(self):
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
    _TOGGLE_CONFIG = {
        0: {"label": " Patients en Attente", "icon": "fa5s.user-clock", "key": "warning"},
        1: {"label": " Tableau Rendez-vous", "icon": "fa5s.calendar-alt", "key": "primary"},
    }

    def __init__(self, rendez_vous_ctrl):
        super().__init__()
        self.ctrl = rendez_vous_ctrl
        self.code_session = None
        self._init_ui()
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        self._setup_top_bar()
        self._setup_stats_section()
        self._setup_action_bar()
        self._setup_bottom_section()

    def apply_theme(self):
        c = theme_manager.colors()
        self.search_bar.setStyleSheet(RendezVousStyles.search_bar())
        self.btn_add.setStyleSheet(RendezVousStyles.button_primary())

        round_btn = RendezVousStyles.button_secondary()
        self.btn_notification.setStyleSheet(round_btn)
        self.btn_export.setStyleSheet(round_btn)
        self.btn_import.setStyleSheet(round_btn)

        self.frame_table.setStyleSheet(RendezVousStyles.card())
        self.frame_graph.setStyleSheet(RendezVousStyles.card())
        self.table.setStyleSheet(RendezVousStyles.table())
        self.setStyleSheet(f"background: {c['bg_main']};")

        self.btn_add.setIcon(qta.icon("fa5s.plus-square", color=c["text_inverse"]))
        for btn, ico in [
            (self.btn_notification, "fa5s.bell"),
            (self.btn_export, "fa5s.file-export"),
            (self.btn_import, "fa5s.file-import"),
        ]:
            btn.setIcon(qta.icon(ico, color=c["primary"]))

        for card, key in [
            (self.card_jour, "primary"),
            (self.card_session, "success"),
            (self.card_attente, "warning"),
        ]:
            color = c[key]
            card.setStyleSheet(RendezVousStyles.stat_card_style(color))
            card._icon_lbl.setPixmap(qta.icon(card._icon_name, color=color).pixmap(QSize(20, 20)))
            card._title_lbl.setStyleSheet(
                f"font-weight:bold; color:{c['text_secondary']}; font-size:11px; border:none;"
            )
            card.value_label.setStyleSheet(
                f"font-size:28px; font-weight:bold; color:{color}; border:none;"
            )

        for frame in [self.frame_table, self.frame_graph]:
            frame._icon_lbl.setPixmap(qta.icon(frame._icon_name, color=c["primary"]).pixmap(QSize(16, 16)))
            frame._title_lbl.setStyleSheet(
                f"font-weight:bold; color:{c['text_primary']}; font-size:12px; border:none;"
            )
            frame._separator.setStyleSheet(f"background:{c['border_light']}; border:none;")

        self.table.verticalScrollBar().setStyleSheet(RendezVousStyles.scrollbar())
        self._action_bar.setStyleSheet(
            f"background: {c['bg_card']}; border-radius: 8px; border: 1px solid {c['border_light']};"
        )
        self._lbl_vue.setStyleSheet(
            f"font-size: 11px; color: {c['text_muted']}; font-weight: 600; border: none;"
        )
        self._update_toggle_btn()

    def _setup_top_bar(self):
        hbox = QHBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(" Rechercher un rendez-vous...")
        self.search_bar.setFixedHeight(45)
        self.search_bar.textChanged.connect(self._filtrer_rendez_vous)

        self.btn_add = QPushButton(qta.icon("fa5s.plus-square", color="white"), " Ajouter")
        self.btn_add.setFixedSize(120, 45)
        self.btn_add.clicked.connect(self._ouvrir_formulaire_rendez_vous)

        self.btn_notification = QPushButton()
        self.btn_notification.setFixedSize(45, 45)
        self.btn_notification.setToolTip("Notifications")

        self.btn_export = QPushButton()
        self.btn_export.setFixedSize(45, 45)
        self.btn_export.setToolTip("Exporter")

        self.btn_import = QPushButton()
        self.btn_import.setFixedSize(45, 45)
        self.btn_import.setToolTip("Importer")

        hbox.addWidget(self.search_bar)
        hbox.addWidget(self.btn_add)
        hbox.addSpacing(10)
        hbox.addWidget(self.btn_notification)
        hbox.addWidget(self.btn_export)
        hbox.addWidget(self.btn_import)
        self.main_layout.addLayout(hbox)

    def _setup_stats_section(self):
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_jour = self._create_stat_card("Rendez-vous du Jour", "0", "fa5s.calendar-day", "primary")
        self.card_session = self._create_stat_card("Total Session", "0", "fa5s.calendar-check", "success")
        self.card_attente = self._create_stat_card("Patients en Attente", "0", "fa5s.user-clock", "warning")

        stats_layout.addWidget(self.card_jour)
        stats_layout.addWidget(self.card_session)
        stats_layout.addWidget(self.card_attente)
        self.main_layout.addLayout(stats_layout)

    def _create_stat_card(self, titre, valeur, icone, accent_key):
        c = theme_manager.colors()
        couleur = c.get(accent_key, accent_key)
        card = AnimatedFrame()
        card.setObjectName("StatCard")
        card.setFixedHeight(120)
        card._icon_name = icone
        card._accent_key = accent_key
        card.setStyleSheet(RendezVousStyles.stat_card_style(couleur))

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)

        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icone, color=couleur).pixmap(QSize(20, 20)))
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        card._icon_lbl = icon_lbl

        title_lbl = QLabel(titre)
        title_lbl.setStyleSheet(
            f"font-weight:bold; color:{c['text_secondary']}; font-size:11px; border:none;"
        )
        card._title_lbl = title_lbl
        header.addWidget(icon_lbl)
        header.addSpacing(8)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        value_lbl = QLabel(valeur)
        value_lbl.setStyleSheet(f"font-size:28px; font-weight:bold; color:{couleur}; border:none;")
        value_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_lbl)
        layout.addStretch()

        card.value_label = value_lbl
        return card

    def _setup_action_bar(self):
        self._action_bar = QFrame()
        self._action_bar.setFixedHeight(46)

        bar_layout = QHBoxLayout(self._action_bar)
        bar_layout.setContentsMargins(14, 0, 14, 0)
        bar_layout.setSpacing(10)

        self._lbl_vue = QLabel("Vue :")
        bar_layout.addWidget(self._lbl_vue)
        bar_layout.addStretch()

        self._btn_toggle = QPushButton()
        self._btn_toggle.setFixedHeight(34)
        self._btn_toggle.setMinimumWidth(180)
        self._btn_toggle.setCursor(Qt.PointingHandCursor)
        self._btn_toggle.clicked.connect(self._toggle_vue)
        bar_layout.addWidget(self._btn_toggle)

        self.main_layout.addWidget(self._action_bar)

    def _setup_bottom_section(self):
        self._stack = AnimatedStack()

        self._page_stats = QWidget()
        stats_layout = QHBoxLayout(self._page_stats)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(12)

        self.frame_table = self._create_rounded_frame("Liste des Rendez-vous", "fa5s.calendar-alt")
        self._setup_table()

        self.frame_graph = self._create_rounded_frame("Rendez-vous par Mois", "fa5s.chart-line")
        self._setup_graph()

        stats_layout.addWidget(self.frame_table, 3)
        stats_layout.addWidget(self.frame_graph, 2)

        self._page_attente_container = QWidget()
        attente_layout = QVBoxLayout(self._page_attente_container)
        attente_layout.setContentsMargins(0, 0, 0, 0)

        self._scroll_attente = QScrollArea()
        self._scroll_attente.setWidgetResizable(True)
        self._scroll_attente.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_attente.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll_attente.setFrameShape(QFrame.NoFrame)

        self._vue_attente = None
        attente_layout.addWidget(self._scroll_attente)

        self._stack.add_page(self._page_stats)
        self._stack.add_page(self._page_attente_container)
        self.main_layout.addWidget(self._stack, 1)
        self._update_toggle_btn()

    def _toggle_vue(self):
        target = 1 if self._stack.current_index() == 0 else 0
        self._stack.slide_to(target)
        self._update_toggle_btn(override_index=target)

    def _update_toggle_btn(self, override_index=None):
        c = theme_manager.colors()
        idx = override_index if override_index is not None else self._stack.current_index()
        cfg = self._TOGGLE_CONFIG[idx]
        color = c.get(cfg["key"], c["primary"])
        self._btn_toggle.setText(cfg["label"])
        self._btn_toggle.setIcon(qta.icon(cfg["icon"], color=color))
        self._btn_toggle.setStyleSheet(
            f"""
            QPushButton {{
                background: {color}18;
                border: 1.5px solid {color}66;
                border-radius: 8px;
                color: {color};
                font-size: 12px;
                font-weight: 600;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background: {color}30;
                border: 1.5px solid {color};
            }}
            QPushButton:pressed {{
                background: {color}45;
            }}
            """
        )

    def _create_rounded_frame(self, titre: str, icone_name: str):
        c = theme_manager.colors()
        frame = AnimatedFrame()
        frame._icon_name = icone_name
        frame.setStyleSheet(RendezVousStyles.card())

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icone_name, color=c["primary"]).pixmap(QSize(16, 16)))
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        frame._icon_lbl = icon_lbl

        title_lbl = QLabel(titre)
        title_lbl.setStyleSheet(
            f"font-weight:bold; color:{c['text_primary']}; font-size:12px; border:none;"
        )
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

    def _setup_table(self):
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Code", "Patient", "Personnel", "Date/Heure", "Statut", "Actions"])
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._apply_scrollbar_style(self.table)

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
        self.frame_table.layout().addWidget(self.table)

    def _apply_scrollbar_style(self, widget):
        widget.verticalScrollBar().setStyleSheet(RendezVousStyles.scrollbar())

    def _setup_graph(self):
        self.graphe = RendezVousAnalyseGraph(parent=self.frame_graph, width=8, height=6)
        self.frame_graph.layout().addWidget(self.graphe)

    def charger_rendez_vous(self, code_session: str):
        self.code_session = code_session
        rendez_vous = self.ctrl.lister_rendez_vous(self.code_session)
        self._remplir_table(rendez_vous)
        self._mettre_a_jour_stats()
        self._mettre_a_jour_graphe()
        self._charger_vue_attente()

    def _charger_vue_attente(self):
        if self._vue_attente is None:
            self._vue_attente = PatientsAttenteRendezVousView(
                ctrl=self.ctrl,
                code_session=self.code_session,
            )
            self._vue_attente.rdv_cree.connect(self._rafraichir_apres_rdv)
            self._scroll_attente.setWidget(self._vue_attente)
        else:
            self._vue_attente.code_session = self.code_session
            self._vue_attente.charger_patients()

        self._scroll_attente.verticalScrollBar().setStyleSheet(RendezVousStyles.scrollbar())
        self._scroll_attente.setStyleSheet("QScrollArea { background: transparent; border: none; }")

    def _rafraichir_apres_rdv(self):
        if self.code_session:
            rendez_vous = self.ctrl.lister_rendez_vous(self.code_session)
            self._remplir_table(rendez_vous)
            self._mettre_a_jour_stats()
            self._mettre_a_jour_graphe()

    def _filtrer_rendez_vous(self, texte):
        critere = texte.strip()
        try:
            if not critere:
                rendez_vous = self.ctrl.lister_rendez_vous(self.code_session)
            else:
                rendez_vous = self.ctrl.rechercher_rendez_vous(critere, self.code_session)
            self._remplir_table(rendez_vous)
        except Exception as e:
            print(f"Erreur lors de la recherche rendez-vous : {e}")

    def _remplir_table(self, rendez_vous: list):
        self.table.setRowCount(0)
        self.table.setUpdatesEnabled(False)

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

        self.table.setUpdatesEnabled(True)

    def _mettre_a_jour_stats(self):
        if not self.code_session:
            return
        self.card_jour.value_label.setText(str(self.ctrl.obtenir_rendez_vous_aujourd_hui(self.code_session)))
        self.card_session.value_label.setText(str(self.ctrl.obtenir_total_rendez_vous_session(self.code_session)))
        attente = self.ctrl.obtenir_patients_attente_rendez_vous(self.code_session) or []
        self.card_attente.value_label.setText(str(len(attente)))

    def _mettre_a_jour_graphe(self):
        if not self.code_session:
            return
        stats = self.ctrl.obtenir_rendez_vous_par_mois(self.code_session)
        self.graphe.update_graph(stats)

    def _action_voir(self, rdv):
        from views.rendez_vous.detail_rendez_vous_modal import DetailsRendezVousModal

        modal = DetailsRendezVousModal(self, rdv.code_rendez_vous, self.ctrl)
        modal.exec()

    def _ouvrir_formulaire_rendez_vous(self):
        from views.rendez_vous.rendez_vous_form import RendezVousFormDialog

        dialog = RendezVousFormDialog(
            controleur=self.ctrl,
            code_session=self.code_session,
            rendez_vous_obj=None,
            parent=self,
        )
        if dialog.exec():
            self.charger_rendez_vous(self.code_session)

    def _action_modifier(self, rdv):
        from views.rendez_vous.rendez_vous_form import RendezVousFormDialog

        dialog = RendezVousFormDialog(
            controleur=self.ctrl,
            code_session=self.code_session,
            rendez_vous_obj=rdv,
            parent=self,
        )
        if dialog.exec():
            self.charger_rendez_vous(self.code_session)

    def _action_supprimer(self, rdv):
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
            QMessageBox.information(self, "Succes", msg)
            self.charger_rendez_vous(self.code_session)
        else:
            QMessageBox.critical(self, "Erreur", msg)

    def _make_handler(self, func, rdv):
        def handler():
            func(rdv)

        return handler

    def _ajouter_boutons_actions(self, row: int, rdv):
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
        mapping = {
            "attente": "En attente",
            "confirme": "Confirme",
            "en_cours": "En cours",
            "termine": "Termine",
            "annule": "Annule",
            "absent": "Absent",
            "reporte": "Reporte",
        }
        return mapping.get(str(statut or "").strip().lower(), str(statut or "-"))
