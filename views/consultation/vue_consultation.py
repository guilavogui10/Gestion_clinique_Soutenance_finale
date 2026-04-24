import qtawesome as qta
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QPoint, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QHeaderView, QFrame, QLabel, QGraphicsDropShadowEffect,
    QTableWidgetItem, QMessageBox
)
# Après
from .graphe_consultation import ConsultationAnalyseGraph
from views.shared.theme_manager import theme_manager
from views.consultation.styles import ConsultationStyles


class AnimatedFrame(QFrame):
    """Cadre arrondi avec effet d'ombre et animation de survol."""

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


class ConsultationView(QWidget):
    """
    Vue principale pour la gestion des consultations médicales.
    Reçoit le contrôleur consultation en paramètre (cohérent avec les autres vues).
    La session active est injectée via charger_consultations() depuis le dashboard.
    """

    def __init__(self, consultation_ctrl):
        super().__init__()
        self.ctrl         = consultation_ctrl
        self.code_session = None
        self._init_ui()
        from views.shared.panneau_statistiques import PanneauStatistiques
        self.panneau_stats = PanneauStatistiques(parent=self, ctrl=self.ctrl)

        # Appliquer le thème initial et écouter les changements
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
        self._setup_bottom_section()

    # =========================================================================
    # BARRE DU HAUT
    # =========================================================================

    def apply_theme(self):
        """Applique le thème actif à tous les composants de la vue consultation."""
        c = theme_manager.colors()
        # Fond principal
        self.setStyleSheet(f"background: {c['bg_main']};")
        # Barre de recherche
        self.search_bar.setStyleSheet(ConsultationStyles.search_bar())
        # Bouton Ajouter
        self.btn_add.setStyleSheet(ConsultationStyles.button_primary())
        self.btn_add.setIcon(qta.icon("fa5s.plus-square", color=c['text_inverse']))
        # Boutons ronds (notification, export, import)
        round_btn_style = ConsultationStyles.button_secondary()
        for btn, ico in [(self.btn_notification, "fa5s.bell"), (self.btn_export, "fa5s.file-export"), (self.btn_import, "fa5s.file-import")]:
            btn.setStyleSheet(round_btn_style)
            btn.setIcon(qta.icon(ico, color=c['primary']))
        # Cartes statistiques
        for card, key in [(self.card_jour, 'primary'), (self.card_session, 'success'), (self.card_attente, 'warning')]:
            color = c[key]
            card.setStyleSheet(ConsultationStyles.stat_card_style(color))
            card._icon_lbl.setPixmap(qta.icon(card._icon_name, color=color).pixmap(QSize(20, 20)))
            card._title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_secondary']}; font-size:11px; border:none;")
            card.value_label.setStyleSheet(f"font-size:28px; font-weight:bold; color:{color}; border:none;")
        # Cadres arrondis (table + graphe)
        for frame in [self.frame_table, self.frame_graph]:
            frame.setStyleSheet(ConsultationStyles.card())
            frame._icon_lbl.setPixmap(qta.icon(frame._icon_name, color=c['primary']).pixmap(QSize(16, 16)))
            frame._title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_primary']}; font-size:12px; border:none;")
            frame._separator.setStyleSheet(f"background:{c['border_light']}; border:none;")
        # Tableau + scrollbar
        self.table.setStyleSheet(ConsultationStyles.table())
        self.table.verticalScrollBar().setStyleSheet(ConsultationStyles.scrollbar())

    def _setup_top_bar(self):
        hbox = QHBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(" Rechercher une consultation...")
        self.search_bar.setFixedHeight(45)
        self.search_bar.textChanged.connect(self._filtrer_consultations)

        self.btn_add = QPushButton(qta.icon("fa5s.plus-square", color="white"), " Ajouter")
        self.btn_add.setFixedSize(120, 45)
        self.btn_add.clicked.connect(self._ouvrir_formulaire)

        c = theme_manager.colors()
        self.btn_notification = QPushButton(qta.icon("fa5s.bell", color=c['primary']), "")
        self.btn_notification.setFixedSize(45, 45)
        self.btn_notification.setToolTip("Notifications")
        self.btn_notification.clicked.connect(self._basculer_stats)

        self.btn_export = QPushButton(qta.icon("fa5s.file-export", color=c['primary']), "")
        self.btn_export.setFixedSize(45, 45)
        self.btn_export.setToolTip("Exporter")

        self.btn_import = QPushButton(qta.icon("fa5s.file-import", color=c['primary']), "")
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
    # CARDS STATISTIQUES
    # =========================================================================

    def _setup_stats_section(self):
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_jour    = self._creer_stat_card("Consultations du Jour", "0", "fa5s.calendar-day", "primary")
        self.card_session = self._creer_stat_card("Session en Cours",      "—", "fa5s.clock",        "success")
        self.card_attente = self._creer_stat_card("Patients en Attente",   "0", "fa5s.users",        "warning")

        stats_layout.addWidget(self.card_jour)
        stats_layout.addWidget(self.card_session)
        stats_layout.addWidget(self.card_attente)
        self.main_layout.addLayout(stats_layout)

    def _creer_stat_card(self, titre: str, valeur: str, icone: str, accent_key: str) -> AnimatedFrame:
        """Crée une carte statistique avec titre, icône et valeur."""
        c = theme_manager.colors()
        couleur = c.get(accent_key, accent_key)
        card = AnimatedFrame()
        card.setFixedHeight(120)
        card._icon_name = icone
        card._accent_key = accent_key
        card.setStyleSheet(ConsultationStyles.stat_card_style(couleur))

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)

        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icone, color=couleur).pixmap(QSize(20, 20)))
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        card._icon_lbl = icon_lbl
        title_lbl = QLabel(titre)
        title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_secondary']}; font-size:11px; border:none;")
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

    # =========================================================================
    # SECTION BAS : TABLE + GRAPHE
    # =========================================================================

    def _setup_bottom_section(self):
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        self.frame_table = self._creer_cadre_arrondi("Liste des Consultations", "fa5s.stethoscope")
        self._setup_table()

        self.frame_graph = self._creer_cadre_arrondi("Consultations par Mois", "fa5s.chart-line")
        self._setup_graphe()

        bottom_layout.addWidget(self.frame_table, 3)
        bottom_layout.addWidget(self.frame_graph, 2)
        self.main_layout.addLayout(bottom_layout)
        


    def _creer_cadre_arrondi(self, titre: str, icone_name: str) -> AnimatedFrame:
        """Crée un cadre arrondi avec en-tête titre + icône."""
        c = theme_manager.colors()
        frame = AnimatedFrame()
        frame._icon_name = icone_name
        frame.setStyleSheet(ConsultationStyles.card())
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

    def _setup_table(self):
        """Crée la table vide avec ses 5 colonnes."""
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Code", "Patient", "Statut Facture", "Date", "Actions"]
        )
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._apply_scrollbar_style(self.table)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 100)

        self.table.setStyleSheet(ConsultationStyles.table())
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setAlternatingRowColors(True)
        self.frame_table.layout().addWidget(self.table)

    def _apply_scrollbar_style(self, widget):
        widget.verticalScrollBar().setStyleSheet(ConsultationStyles.scrollbar())
        
    def _basculer_stats(self):
        if not self.code_session:
            return
        self.panneau_stats.actualiser(self.code_session)
        self.panneau_stats.basculer()

    def _setup_graphe(self):
        self.graphe = ConsultationAnalyseGraph(
            parent=self.frame_graph, width=8, height=6
        )
        self.frame_graph.layout().addWidget(self.graphe)

    # =========================================================================
    # CHARGEMENT DES DONNÉES (appelé depuis le dashboard)
    # =========================================================================

    def charger_consultations(self, code_session: str):
        """
        Point d'entrée principal appelé depuis le dashboard.
        Reçoit le code_session et charge toutes les données de la vue.
        """
        self.code_session = code_session
        consultations = self.ctrl.lister_consultations(self.code_session)
        self._remplir_table(consultations)
        self._mettre_a_jour_stats()       # ← ajouter
        self._mettre_a_jour_graphe()     # ← ajouter

    # =========================================================================
    # REMPLISSAGE DE LA TABLE
    # =========================================================================

    def _remplir_table(self, consultations: list):
        """Remplit la table avec la liste des consultations."""
        self.table.setRowCount(0)

        for consultation in consultations:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Colonne Code
            self.table.setItem(row, 0, QTableWidgetItem(str(consultation.code)))

            # Colonne Patient — récupéré via consultation_complete (JOIN patient)
            nom_patient = self._get_nom_patient(consultation.code)
            self.table.setItem(row, 1, QTableWidgetItem(nom_patient))

            # Colonne Statut Facture
            self.table.setItem(row, 2, QTableWidgetItem(str(consultation.statut_facture)))

            # Colonne Date
            date_val = consultation.date_consultation
            date_str = (
                date_val.strftime("%d/%m/%Y")
                if hasattr(date_val, 'strftime') else str(date_val)
            )
            self.table.setItem(row, 3, QTableWidgetItem(date_str))

            # Colonne Actions
            self._ajouter_boutons_actions(row, consultation)

    def _get_nom_patient(self, code_consultation: str) -> str:
        """
        Récupère le nom complet du patient via consultation_complete.
        Retourne '—' si introuvable.
        """
        data = self.ctrl.obtenir_consultation_complete(code_consultation)
        if not data:
            return "—"
        nom    = data.get('patient_nom',    '') or ''
        prenom = data.get('patient_prenom', '') or ''
        return f"{nom} {prenom}".strip() or "—"

    def _ajouter_boutons_actions(self, row: int, consultation):
        """Ajoute les boutons voir / modifier / supprimer sur une ligne."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        c = theme_manager.colors()
        btn_view   = QPushButton(qta.icon("fa5s.eye",       color=c['info']), "")
        btn_edit   = QPushButton(qta.icon("fa5s.edit",      color=c['primary']), "")
        btn_delete = QPushButton(qta.icon("fa5s.trash-alt", color=c['danger']), "")

        btn_style = ConsultationStyles.button_table_action()
        for btn in [btn_view, btn_edit, btn_delete]:
            btn.setFixedSize(26, 26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(btn_style)
            layout.addWidget(btn)

        btn_view.clicked.connect(self._make_handler(self._action_voir, consultation))
        btn_edit.clicked.connect(self._make_handler(self._action_modifier, consultation))
        btn_delete.clicked.connect(self._make_handler(self._action_supprimer, consultation))

        self.table.setCellWidget(row, 4, container)

    def _make_handler(self, func, consultation):
        """Évite les problèmes de closure dans les boucles."""
        def handler():
            func(consultation)
        return handler

    # =========================================================================
    # ACTIONS SUR LES CONSULTATIONS
    # =========================================================================

    def _action_voir(self, consultation):
        from .detail_consultation_modal import DetailsConsultationModal
        modal = DetailsConsultationModal(self, consultation.code, self.ctrl)
        modal.exec()

    def _action_modifier(self, consultation):
        from .consultation_form import ConsultationFormDialog
        # On récupère les infos complètes pour avoir code_visite et code_personnel
        data = self.ctrl.obtenir_par_code(consultation.code)
        if not data:
            return
        dialog = ConsultationFormDialog(
            controleur       = self.ctrl,
            code_visite      = data.code_visite,
            code_session     = self.code_session,
            code_personnel   = data.code_personnel,
            consultation_obj = data,
            parent           = self
        )
        if dialog.exec():
            self.charger_consultations(self.code_session)

    def _action_supprimer(self, consultation):
        confirm = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer la consultation {consultation.code} ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
        ok, msg = self.ctrl.supprimer_consultation(consultation.code)
        if ok:
            QMessageBox.information(self, "Succès", msg)
            self.charger_consultations(self.code_session)
        else:
            QMessageBox.critical(self, "Erreur", msg)

    def _ouvrir_formulaire(self):
        from .consultation_form import ConsultationFormDialog
        dialog = ConsultationFormDialog(
            controleur   = self.ctrl,
            code_session = self.code_session,  # pas de code_visite → combo libre
            parent       = self
        )
        if dialog.exec():
            self.charger_consultations(self.code_session)

        # =========================================================================
        # FILTRAGE
        # =========================================================================

    def _filtrer_consultations(self, texte: str):
        """Filtre la table en temps réel selon la saisie."""
        if not self.code_session:
            return
        texte = texte.strip()
        if not texte:
            self.charger_consultations(self.code_session)
        else:
            resultats = self.ctrl.rechercher_consultation(texte, self.code_session)
            self._remplir_table(resultats)

        # =========================================================================
        # FORMULAIRE (à implémenter)
        # =========================================================================

        # def _ouvrir_formulaire(self):
        #     print("Ouverture formulaire ajout consultation")
    def _mettre_a_jour_stats(self):
        if not self.code_session:
            return
        nb_jour    = self.ctrl.obtenir_consultations_aujourd_hui(self.code_session)
        nb_session = self.ctrl.obtenir_nombre_total(self.code_session)
        nb_attente = self.ctrl.obtenir_nombre_patients_en_attente(self.code_session)

        self.card_jour.value_label.setText(str(nb_jour))
        self.card_session.value_label.setText(str(nb_session))
        self.card_attente.value_label.setText(str(nb_attente))
        
    def _mettre_a_jour_graphe(self):
        if not self.code_session:
            return
        stats = self.ctrl.obtenir_nombre_par_mois(self.code_session)
        self.graphe.update_graph(stats)