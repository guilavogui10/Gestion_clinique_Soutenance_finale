"""
=============================================================================
 CHIRURGIE VIEW  — version avec panneau bas animé
=============================================================================
 Architecture identique à ExamenView :
   • _setup_bottom_section  → AnimatedStack avec 2 pages
   • _setup_action_bar      → barre toggle entre les pages
   • _toggle_vue            → bascule page 0 ↔ page 1
   • _update_toggle_btn     → met à jour le bouton + thème
   • charger_chururgies     → rafraîchit aussi la vue attente
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

from .graphe_chirurgie import ChirurgieAnalyseGraph
from views.shared.theme_manager import theme_manager
from views.chirurgie.styles import ChirurgieStyles
from views.chirurgie.animated_stack import AnimatedStack
from views.chirurgie.patients_chirurgie_attente import PatientsAttenteChirurgieView
from views.chirurgie.chirurgie_form import ChirurgieFormDialog
from views.chirurgie.detail_chirurgie_modal import DetailsChirurgieModal
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
# CHIRURGIE VIEW
# =============================================================================

class ChirurgieView(QWidget):
    """
    Vue principale pour la gestion des interventions chirurgicales.
    La partie basse est un AnimatedStack à deux pages :
      - Page 0 : tableau + graphe (vue par défaut)
      - Page 1 : grille patients en attente (scrollable)
    """

    # Labels et icônes du bouton toggle selon la page active
    _TOGGLE_CONFIG = {
        0: {   # on est sur stats → on propose d'aller vers attente
            "label": " Patients en Attente",
            "icon":  "fa5s.procedures",
            "key":   "danger",
        },
        1: {   # on est sur attente → on propose de revenir aux stats
            "label": " Statistiques Chirurgie",
            "icon":  "fa5s.chart-bar",
            "key":   "primary",
        },
    }

    def __init__(self, chirurgie_ctrl):
        super().__init__()
        self.ctrl         = chirurgie_ctrl
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
        self.search_bar.setPlaceholderText(" Rechercher une intervention chirurgicale...")
        self.search_bar.setFixedHeight(45)
        self.search_bar.textChanged.connect(self._filtrer_chururgies)

        self.btn_add = QPushButton(qta.icon("fa5s.plus-square", color="white"), " Ajouter")
        self.btn_add.setFixedSize(120, 45)
        self.btn_add.clicked.connect(self._ouvrir_formulaire_chirurgie)

        self.btn_notification = QPushButton(
            qta.icon("fa5s.bell", color=theme_manager.colors()['primary']), "")
        self.btn_notification.setFixedSize(45, 45)
        self.btn_notification.setToolTip("Notifications bloc opératoire")

        self.btn_export = QPushButton(
            qta.icon("fa5s.file-export", color=theme_manager.colors()['primary']), "")
        self.btn_export.setFixedSize(45, 45)
        self.btn_export.setToolTip("Exporter le planning")

        self.btn_import = QPushButton(
            qta.icon("fa5s.file-import", color=theme_manager.colors()['primary']), "")
        self.btn_import.setFixedSize(45, 45)
        self.btn_import.setToolTip("Importer un planning")

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
            "Chirurgies du Jour", "0", "fa5s.procedures", "primary")
        self.card_session = self._create_stat_card(
            "Total Session", "0", "fa5s.hospital-user", "success")
        self.card_attente = self._create_stat_card(
            "En Attente de Bloc", "0", "fa5s.clipboard-list", "danger")

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
        self.frame_table = self._create_card_frame("Liste des Interventions", "fa5s.syringe")
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Code", "Patient", "Libellé", "Actions"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Code
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Patient (flexible)
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Libellé (flexible)
        header.setSectionResizeMode(3, QHeaderView.Fixed)             # Actions
        self.table.setColumnWidth(3, 140)  # Largeur fixe pour Actions
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.frame_table.layout().addWidget(self.table)

        layout_stats.addWidget(self.frame_table, 6)

        # Graphe
        self.frame_graph = self._create_card_frame("Chirurgies par Mois", "fa5s.chart-bar")
        self.graphe = ChirurgieAnalyseGraph(parent=self.frame_graph)
        self.frame_graph.layout().addWidget(self.graphe)

        layout_stats.addWidget(self.frame_graph, 4)

        self._stack.add_page(page_stats)

        # Page 1 : Patients en attente
        self._vue_attente = PatientsAttenteChirurgieView(
            ctrl=self.ctrl,
            code_session=self.code_session or "",
            parent=self
        )
        self._vue_attente.chirurgie_creee.connect(self._on_chirurgie_creee_depuis_attente)
        self._stack.add_page(self._vue_attente)

        self.main_layout.addWidget(self._stack, 1)

    def _create_card_frame(self, title: str, icon_name: str) -> AnimatedFrame:
        """Crée un cadre arrondi avec titre et icône."""
        frame = AnimatedFrame()
        frame._icon_name = icon_name

        c = theme_manager.colors()
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 8, 14, 10)
        layout.setSpacing(4)

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

    def charger_chururgies(self, code_session: str):
        """Charge les chirurgies et met à jour toutes les vues."""
        self.code_session = code_session

        # Statistiques - utiliser les méthodes individuelles du DAO
        try:
            chururgies_jour = self.ctrl.obtenir_chururgies_aujourd_hui(code_session)
            chururgies_session = self.ctrl.obtenir_total_chururgies_session(code_session)
            patients_attente = self.ctrl.obtenir_chururgies_en_attente(code_session)
            
            self.card_jour.value_label.setText(str(chururgies_jour))
            self.card_session.value_label.setText(str(chururgies_session))
            self.card_attente.value_label.setText(str(patients_attente))
        except Exception as e:
            print(f"[ChirurgieView] Erreur stats: {e}")
            self.card_jour.value_label.setText("0")
            self.card_session.value_label.setText("0")
            self.card_attente.value_label.setText("0")

        # Graphe
        try:
            stats_mensuelles = self.ctrl.obtenir_chururgies_par_mois(code_session)
            self.graphe.update_graph(stats_mensuelles)
        except Exception as e:
            print(f"[ChirurgieView] Erreur graphe: {e}")
            self.graphe.update_graph({})

        # Tableau
        chururgies = self.ctrl.lister_chururgies(code_session)
        self._remplir_tableau(chururgies)

        # Vue attente
        if hasattr(self, '_vue_attente'):
            self._vue_attente.code_session = code_session
            if self._stack.current_index() == 1:
                self._vue_attente.charger_patients()

    def _remplir_tableau(self, chururgies):
        """Remplit le tableau avec la liste des chirurgies."""
        self.table.setRowCount(0)

        for chururgie in chururgies:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Code
            self.table.setItem(row, 0, QTableWidgetItem(str(chururgie.code)))

            # Patient
            nom_patient = f"{chururgie.patient_nom or ''} {chururgie.patient_prenom or ''}".strip()
            self.table.setItem(row, 1, QTableWidgetItem(nom_patient or "Patient inconnu"))

            # Libellé (tronqué)
            libelle = str(chururgie.libelle_chururgie or "—")
            libelle_court = libelle[:50] + "..." if len(libelle) > 50 else libelle
            self.table.setItem(row, 2, QTableWidgetItem(libelle_court))

            # Actions
            actions_widget = self._create_action_buttons(str(chururgie.code))
            self.table.setCellWidget(row, 3, actions_widget)

    def _create_action_buttons(self, code_chururgie: str) -> QWidget:
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
        btn_voir.clicked.connect(lambda: self._voir_details(code_chururgie))
        btn_voir.setStyleSheet(ChirurgieStyles.button_table_action())

        # Bouton Modifier
        btn_edit = QPushButton(qta.icon("fa5s.edit", color=c['warning']), "")
        btn_edit.setFixedSize(36, 36)
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setToolTip("Modifier")
        btn_edit.clicked.connect(lambda: self._modifier_chirurgie(code_chururgie))
        btn_edit.setStyleSheet(ChirurgieStyles.button_table_action())

        # Bouton Supprimer
        btn_del = QPushButton(qta.icon("fa5s.trash", color=c['danger']), "")
        btn_del.setFixedSize(36, 36)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setToolTip("Supprimer")
        btn_del.clicked.connect(lambda: self._supprimer_chirurgie(code_chururgie))
        btn_del.setStyleSheet(ChirurgieStyles.button_table_action())

        layout.addWidget(btn_voir)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_del)
        layout.addStretch()

        return widget

    # =========================================================================
    # ACTIONS
    # =========================================================================

    def _ouvrir_formulaire_chirurgie(self):
        """Ouvre le formulaire pour créer une nouvelle chirurgie."""
        dialog = ChirurgieFormDialog(
            controleur=self.ctrl,
            code_session=self.code_session or "",
            parent=self
        )
        if dialog.exec():
            self.charger_chururgies(self.code_session)

    def _voir_details(self, code_chururgie: str):
        """Ouvre la modal de détails d'une chirurgie."""
        modal = DetailsChirurgieModal(
            parent=self,
            code_chururgie=code_chururgie,
            ctrl=self.ctrl
        )
        modal.exec()

    def _modifier_chirurgie(self, code_chururgie: str):
        """Ouvre le formulaire en mode modification."""
        chururgie = self.ctrl.obtenir_par_code(code_chururgie)
        if not chururgie:
            CustomMessageBox("Erreur", "Chirurgie introuvable", False, self).exec()
            return

        dialog = ChirurgieFormDialog(
            controleur=self.ctrl,
            code_session=self.code_session or "",
            chururgie_obj=chururgie,
            parent=self
        )
        if dialog.exec():
            self.charger_chururgies(self.code_session)

    def _supprimer_chirurgie(self, code_chururgie: str):
        """Supprime une chirurgie après confirmation."""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment supprimer la chirurgie {code_chururgie} ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            ok, msg = self.ctrl.supprimer_chururgie(code_chururgie)
            CustomMessageBox("Succès" if ok else "Erreur", msg, ok, self).exec()
            if ok:
                self.charger_chururgies(self.code_session)

    def _filtrer_chururgies(self, texte: str):
        """Filtre le tableau selon le texte de recherche."""
        texte = texte.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(3):  # Exclure colonne Actions (index 3)
                item = self.table.item(row, col)
                if item and texte in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _on_chirurgie_creee_depuis_attente(self):
        """Callback quand une chirurgie est créée depuis la vue attente."""
        self.charger_chururgies(self.code_session)

    # =========================================================================
    # THÈME
    # =========================================================================

    def apply_theme(self):
        """Applique le thème actif à tous les composants."""
        c = theme_manager.colors()
        self.search_bar.setStyleSheet(ChirurgieStyles.search_bar())
        self.btn_add.setStyleSheet(ChirurgieStyles.button_primary())

        round_btn = ChirurgieStyles.button_secondary()
        self.btn_notification.setStyleSheet(round_btn)
        self.btn_export.setStyleSheet(round_btn)
        self.btn_import.setStyleSheet(round_btn)

        self.frame_table.setStyleSheet(ChirurgieStyles.card())
        self.frame_graph.setStyleSheet(ChirurgieStyles.card())
        self.table.setStyleSheet(ChirurgieStyles.table())

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
            (self.card_attente, 'danger'),
        ]:
            color = c[key]
            card.setStyleSheet(ChirurgieStyles.stat_card_style(color))
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

        self.table.verticalScrollBar().setStyleSheet(ChirurgieStyles.scrollbar())

        # Barre action
        self._action_bar.setStyleSheet(
            f"background: {c['bg_card']}; border-radius: 8px; border: 1px solid {c['border_light']};")
        self._lbl_vue.setStyleSheet(
            f"font-size: 11px; color: {c['text_muted']}; font-weight: 600; border: none;")

        self._update_toggle_btn()

