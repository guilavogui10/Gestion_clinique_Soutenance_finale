"""
=============================================================================
 EXAMEN VIEW  — version avec panneau bas animé
=============================================================================
 Modifications par rapport à la version originale :
   • _setup_bottom_section  → remplacé intégralement
   • _setup_action_bar      → NOUVEAU  (barre toggle entre les pages)
   • _toggle_vue            → NOUVEAU  (bascule page 0 ↔ page 1)
   • _update_toggle_btn     → NOUVEAU  (met à jour le bouton + thème)
   • _ouvrir_formulaire     → redirige vers le toggle attente
   • apply_theme            → MAJ du bouton toggle
   • charger_examens        → rafraîchit aussi la vue attente
=============================================================================
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QPoint, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QHeaderView, QFrame, QLabel, QGraphicsDropShadowEffect,
    QTableWidgetItem, QMessageBox
)

from .graphe_examen import ExamenAnalyseGraph
from views.shared.theme_manager import theme_manager
from views.examen.styles import ExamenStyles
from views.examen.animated_stack import AnimatedStack
from views.examen.patients_examen_attente import PatientsAttenteExamenView
from views.examen.examen_form import ExamenFormDialog
from views.examen.detail_examen_modal import DetailsExamenModal
from views.shared.message_box import CustomMessageBox


# =============================================================================
# ANIMATED FRAME
# =============================================================================

class AnimatedFrame(QFrame):
    """Cadre arrondi avec effet d'ombre et légère élévation au survol."""

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


# =============================================================================
# EXAMEN VIEW
# =============================================================================

class ExamenView(QWidget):
    """
    Vue principale pour la gestion des examens médicaux.
    La partie basse est un AnimatedStack à deux pages :
      - Page 0 : tableau + graphe (vue par défaut)
      - Page 1 : grille patients en attente (scrollable)
    """

    # Labels et icônes du bouton toggle selon la page active
    _TOGGLE_CONFIG = {
        0: {   # on est sur stats → on propose d'aller vers attente
            "label": " Patients en Attente",
            "icon":  "fa5s.hourglass-half",
            "key":   "warning",
        },
        1: {   # on est sur attente → on propose de revenir aux stats
            "label": " Statistiques Examen",
            "icon":  "fa5s.chart-bar",
            "key":   "primary",
        },
    }

    def __init__(self, examen_ctrl):
        super().__init__()
        self.ctrl         = examen_ctrl
        self.code_session = None
        self._init_ui()
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # CONSTRUCTION DE L'INTERFACE
    # =========================================================================

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        self._setup_top_bar()
        self._setup_stats_section()
        self._setup_action_bar()
        self._setup_bottom_section()

    # =========================================================================
    # BARRE DU HAUT
    # =========================================================================

    def _setup_top_bar(self):
        hbox = QHBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(" Rechercher un examen...")
        self.search_bar.setFixedHeight(45)
        self.search_bar.textChanged.connect(self._filtrer_examens)

        self.btn_add = QPushButton(qta.icon("fa5s.plus-square", color="white"), " Ajouter")
        self.btn_add.setFixedSize(120, 45)
        self.btn_add.clicked.connect(self._ouvrir_formulaire_examen)

        self.btn_notification = QPushButton(
            qta.icon("fa5s.bell", color=theme_manager.colors()['primary']), "")
        self.btn_notification.setFixedSize(45, 45)
        self.btn_notification.setToolTip("Notifications")

        self.btn_export = QPushButton(
            qta.icon("fa5s.file-export", color=theme_manager.colors()['primary']), "")
        self.btn_export.setFixedSize(45, 45)
        self.btn_export.setToolTip("Exporter")

        self.btn_import = QPushButton(
            qta.icon("fa5s.file-import", color=theme_manager.colors()['primary']), "")
        self.btn_import.setFixedSize(45, 45)
        self.btn_import.setToolTip("Importer")

        hbox.addWidget(self.search_bar)
        hbox.addWidget(self.btn_add)
        hbox.addSpacing(10)
        hbox.addWidget(self.btn_notification)
        hbox.addWidget(self.btn_export)
        hbox.addWidget(self.btn_import)

        self.main_layout.addLayout(hbox)

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def _setup_stats_section(self):
        hbox = QHBoxLayout()
        hbox.setSpacing(15)

        self.card_jour = self._create_stat_card(
            "Examens du Jour", "0", "fa5s.calendar-day", "primary")
        self.card_session = self._create_stat_card(
            "Examens Session", "0", "fa5s.flask", "success")
        self.card_attente = self._create_stat_card(
            "En Attente", "0", "fa5s.hourglass-half", "warning")

        hbox.addWidget(self.card_jour)
        hbox.addWidget(self.card_session)
        hbox.addWidget(self.card_attente)

        self.main_layout.addLayout(hbox)

    def _create_stat_card(self, title: str, value: str, icon_name: str, color_key: str) -> AnimatedFrame:
        card = AnimatedFrame()
        card._icon_name = icon_name
        card.setFixedHeight(120)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)

        c = theme_manager.colors()
        color = c[color_key]

        # Header avec icône
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(QSize(20, 20)))
        card._icon_lbl = icon_lbl

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"font-weight:bold; color:{c['text_secondary']}; font-size:11px; border:none;")
        card._title_lbl = title_lbl

        header.addWidget(icon_lbl)
        header.addSpacing(8)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        # Valeur
        value_label = QLabel(value)
        value_label.setStyleSheet(
            f"font-size:28px; font-weight:bold; color:{color}; border:none;")
        value_label.setAlignment(Qt.AlignCenter)
        card.value_label = value_label
        layout.addWidget(value_label)
        layout.addStretch()

        return card

    # =========================================================================
    # BARRE ACTION (TOGGLE)
    # =========================================================================

    def _setup_action_bar(self):
        """Barre horizontale avec label + bouton toggle."""
        self._action_bar = QFrame()
        self._action_bar.setFixedHeight(50)

        layout = QHBoxLayout(self._action_bar)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(10)

        c = theme_manager.colors()

        self._lbl_vue = QLabel("Vue actuelle : Statistiques")
        self._lbl_vue.setStyleSheet(
            f"font-size: 11px; color: {c['text_muted']}; font-weight: 600; border: none;")

        self._btn_toggle = QPushButton()
        self._btn_toggle.setFixedHeight(38)
        self._btn_toggle.setCursor(Qt.PointingHandCursor)
        self._btn_toggle.clicked.connect(self._toggle_vue)

        layout.addWidget(self._lbl_vue)
        layout.addStretch()
        layout.addWidget(self._btn_toggle)

        self.main_layout.addWidget(self._action_bar)

    # =========================================================================
    # SECTION BASSE (ANIMATED STACK)
    # =========================================================================

    def _setup_bottom_section(self):
        """Conteneur animé à 2 pages : stats (0) et attente (1)."""
        self._stack = AnimatedStack()

        # Page 0 : Tableau + Graphe
        page_stats = QWidget()
        page_stats.setStyleSheet("background: transparent;")
        layout_stats = QHBoxLayout(page_stats)
        layout_stats.setContentsMargins(0, 0, 0, 0)
        layout_stats.setSpacing(15)

        # Tableau
        self.frame_table = self._create_card_frame("Liste des Examens", "fa5s.list")
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Code", "Patient", "Libellé", "Date", "Actions"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Code
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Patient (flexible)
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Libellé (flexible)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(4, QHeaderView.Fixed)             # Actions
        self.table.setColumnWidth(4, 140)  # Largeur fixe pour Actions
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.frame_table.layout().addWidget(self.table)

        layout_stats.addWidget(self.frame_table, 6)

        # Graphe
        self.frame_graph = self._create_card_frame("Analyse Mensuelle", "fa5s.chart-line")
        self.graphe = ExamenAnalyseGraph(parent=self.frame_graph)
        self.frame_graph.layout().addWidget(self.graphe)

        layout_stats.addWidget(self.frame_graph, 4)

        self._stack.add_page(page_stats)

        # Page 1 : Patients en attente
        self._vue_attente = PatientsAttenteExamenView(
            ctrl=self.ctrl,
            code_session=self.code_session or "",
            parent=self
        )
        self._vue_attente.examen_cree.connect(self._on_examen_cree_depuis_attente)
        self._stack.add_page(self._vue_attente)

        self.main_layout.addWidget(self._stack, 1)

    def _create_card_frame(self, title: str, icon_name: str) -> AnimatedFrame:
        """Crée un cadre arrondi avec titre et icône."""
        frame = AnimatedFrame()
        frame._icon_name = icon_name

        c = theme_manager.colors()
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        # Header
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=c['primary']).pixmap(QSize(16, 16)))
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        frame._icon_lbl = icon_lbl

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"font-weight:bold; color:{c['text_primary']}; font-size:12px; border:none;")
        frame._title_lbl = title_lbl

        header.addWidget(icon_lbl)
        header.addSpacing(6)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{c['border_light']}; border:none;")
        frame._separator = sep
        layout.addWidget(sep)

        return frame

    # =========================================================================
    # TOGGLE ENTRE VUES
    # =========================================================================

    def _toggle_vue(self):
        """Bascule entre page 0 (stats) et page 1 (attente)."""
        current = self._stack.current_index()
        target = 1 if current == 0 else 0
        self._stack.slide_to(target)
        self._update_toggle_btn()

        # Mise à jour du label
        if target == 0:
            self._lbl_vue.setText("Vue actuelle : Statistiques")
        else:
            self._lbl_vue.setText("Vue actuelle : Patients en Attente")
            if hasattr(self, '_vue_attente'):
                self._vue_attente.charger_patients()

    def _update_toggle_btn(self):
        """Met à jour le bouton toggle selon la page active."""
        current = self._stack.current_index()
        config = self._TOGGLE_CONFIG[current]
        c = theme_manager.colors()

        self._btn_toggle.setText(config["label"])
        self._btn_toggle.setIcon(
            qta.icon(config["icon"], color=c.get('text_inverse', '#ffffff'))
        )

        color = c[config["key"]]
        self._btn_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {c.get('text_inverse', '#ffffff')};
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
        """)

    # =========================================================================
    # CHARGEMENT DONNÉES
    # =========================================================================

    def charger_examens(self, code_session: str):
        """Charge les examens et met à jour toutes les vues."""
        self.code_session = code_session

        # Statistiques - utiliser les méthodes individuelles
        examens_jour = self.ctrl.obtenir_examens_aujourd_hui(code_session)
        examens_session = self.ctrl.obtenir_total_examens_session(code_session)
        patients_attente = self.ctrl.obtenir_examens_en_attente(code_session)
        
        self.card_jour.value_label.setText(str(examens_jour))
        self.card_session.value_label.setText(str(examens_session))
        self.card_attente.value_label.setText(str(patients_attente))

        # Graphe
        stats_mensuelles = self.ctrl.obtenir_examens_par_mois(code_session)
        self.graphe.update_graph(stats_mensuelles)

        # Tableau
        examens = self.ctrl.lister_examens(code_session)
        self._remplir_tableau(examens)

        # Vue attente
        if hasattr(self, '_vue_attente'):
            self._vue_attente.code_session = code_session
            if self._stack.current_index() == 1:
                self._vue_attente.charger_patients()

    def _remplir_tableau(self, examens):
        """Remplit le tableau avec la liste des examens."""
        self.table.setRowCount(0)

        for examen in examens:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Code
            self.table.setItem(row, 0, QTableWidgetItem(str(examen.code)))

            # Patient
            nom_patient = f"{examen.patient_nom or ''} {examen.patient_prenom or ''}".strip()
            self.table.setItem(row, 1, QTableWidgetItem(nom_patient or "Patient inconnu"))

            # Libellé (tronqué)
            libelle = str(examen.libelle_examen or "—")
            libelle_court = libelle[:50] + "..." if len(libelle) > 50 else libelle
            self.table.setItem(row, 2, QTableWidgetItem(libelle_court))

            # Date
            date_val = examen.date_examen
            date_str = date_val.strftime("%d/%m/%Y %H:%M") if hasattr(date_val, 'strftime') else str(date_val)
            self.table.setItem(row, 3, QTableWidgetItem(date_str))

            # Actions
            actions_widget = self._create_action_buttons(str(examen.code))
            self.table.setCellWidget(row, 4, actions_widget)

    def _create_action_buttons(self, code_examen: str) -> QWidget:
        """Crée les boutons d'action pour une ligne du tableau."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        c = theme_manager.colors()

        # Bouton Voir
        btn_voir = QPushButton(qta.icon("fa5s.eye", color=c['info']), "")
        btn_voir.setFixedSize(36, 36)
        btn_voir.setCursor(Qt.PointingHandCursor)
        btn_voir.setToolTip("Voir les détails")
        btn_voir.clicked.connect(lambda: self._voir_details(code_examen))
        btn_voir.setStyleSheet(ExamenStyles.button_table_action())

        # Bouton Modifier
        btn_edit = QPushButton(qta.icon("fa5s.edit", color=c['warning']), "")
        btn_edit.setFixedSize(36, 36)
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setToolTip("Modifier")
        btn_edit.clicked.connect(lambda: self._modifier_examen(code_examen))
        btn_edit.setStyleSheet(ExamenStyles.button_table_action())

        # Bouton Supprimer
        btn_del = QPushButton(qta.icon("fa5s.trash", color=c['danger']), "")
        btn_del.setFixedSize(36, 36)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setToolTip("Supprimer")
        btn_del.clicked.connect(lambda: self._supprimer_examen(code_examen))
        btn_del.setStyleSheet(ExamenStyles.button_table_action())

        layout.addWidget(btn_voir)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_del)
        layout.addStretch()

        return widget

    # =========================================================================
    # ACTIONS
    # =========================================================================

    def _ouvrir_formulaire_examen(self):
        """Ouvre le formulaire pour créer un nouvel examen."""
        dialog = ExamenFormDialog(
            controleur=self.ctrl,
            code_session=self.code_session or "",
            parent=self
        )
        if dialog.exec():
            self.charger_examens(self.code_session)

    def _voir_details(self, code_examen: str):
        """Ouvre la modal de détails d'un examen."""
        modal = DetailsExamenModal(
            parent=self,
            code_examen=code_examen,
            ctrl=self.ctrl
        )
        modal.exec()

    def _modifier_examen(self, code_examen: str):
        """Ouvre le formulaire en mode modification."""
        examen = self.ctrl.obtenir_par_code(code_examen)
        if not examen:
            CustomMessageBox("Erreur", "Examen introuvable", False, self).exec()
            return

        dialog = ExamenFormDialog(
            controleur=self.ctrl,
            code_session=self.code_session or "",
            examen_obj=examen,
            parent=self
        )
        if dialog.exec():
            self.charger_examens(self.code_session)

    def _supprimer_examen(self, code_examen: str):
        """Supprime un examen après confirmation."""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment supprimer l'examen {code_examen} ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            ok, msg = self.ctrl.supprimer_examen(code_examen)
            CustomMessageBox("Succès" if ok else "Erreur", msg, ok, self).exec()
            if ok:
                self.charger_examens(self.code_session)

    def _filtrer_examens(self, texte: str):
        """Filtre le tableau selon le texte de recherche."""
        texte = texte.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(4):  # Exclure colonne Actions (index 4)
                item = self.table.item(row, col)
                if item and texte in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _on_examen_cree_depuis_attente(self):
        """Callback quand un examen est créé depuis la vue attente."""
        self.charger_examens(self.code_session)

    # =========================================================================
    # THÈME
    # =========================================================================

    def apply_theme(self):
        """Applique le thème actif à tous les composants."""
        c = theme_manager.colors()
        self.search_bar.setStyleSheet(ExamenStyles.search_bar())
        self.btn_add.setStyleSheet(ExamenStyles.button_primary())

        round_btn = ExamenStyles.button_secondary()
        self.btn_notification.setStyleSheet(round_btn)
        self.btn_export.setStyleSheet(round_btn)
        self.btn_import.setStyleSheet(round_btn)

        self.frame_table.setStyleSheet(ExamenStyles.card())
        self.frame_graph.setStyleSheet(ExamenStyles.card())
        self.table.setStyleSheet(ExamenStyles.table())

        self.setStyleSheet(f"background: {c['bg_main']};")

        self.btn_add.setIcon(qta.icon("fa5s.plus-square", color=c['text_inverse']))

        for btn, ico in [
            (self.btn_notification, "fa5s.bell"),
            (self.btn_export,       "fa5s.file-export"),
            (self.btn_import,       "fa5s.file-import"),
        ]:
            btn.setIcon(qta.icon(ico, color=c['primary']))

        for card, key in [
            (self.card_jour,    'primary'),
            (self.card_session, 'success'),
            (self.card_attente, 'warning'),
        ]:
            color = c[key]
            card.setStyleSheet(ExamenStyles.stat_card_style(color))
            card._icon_lbl.setPixmap(qta.icon(card._icon_name, color=color).pixmap(QSize(20, 20)))
            card._title_lbl.setStyleSheet(
                f"font-weight:bold; color:{c['text_secondary']}; font-size:11px; border:none;")
            card.value_label.setStyleSheet(
                f"font-size:28px; font-weight:bold; color:{color}; border:none;")

        for frame in [self.frame_table, self.frame_graph]:
            frame._icon_lbl.setPixmap(
                qta.icon(frame._icon_name, color=c['primary']).pixmap(QSize(16, 16)))
            frame._title_lbl.setStyleSheet(
                f"font-weight:bold; color:{c['text_primary']}; font-size:12px; border:none;")
            frame._separator.setStyleSheet(
                f"background:{c['border_light']}; border:none;")

        self.table.verticalScrollBar().setStyleSheet(ExamenStyles.scrollbar())

        # Barre action
        self._action_bar.setStyleSheet(
            f"background: {c['bg_card']}; border-radius: 8px; border: 1px solid {c['border_light']};")
        self._lbl_vue.setStyleSheet(
            f"font-size: 11px; color: {c['text_muted']}; font-weight: 600; border: none;")

        self._update_toggle_btn()

