import qtawesome as qta
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QPoint, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QHeaderView, QFrame, QLabel, QGraphicsDropShadowEffect,
    QTableWidgetItem
)
from views.shared.theme_manager import theme_manager
from views.lunette.styles import LunetteStyles


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


class CommandeLunetteView(QWidget):
    """
    Vue principale pour la gestion des commandes de lunettes.
    Interface uniquement — logique à implémenter ultérieurement.
    """

    def __init__(self,commande_lunette_ctrl):
        super().__init__()
        self.ctrl = commande_lunette_ctrl
        self.code_session = None
        self._init_ui()
        from .panneaux import PanneauAlertesLivraison
        self.panneau_alertes = PanneauAlertesLivraison(self, self.ctrl)
        from .panneaux import PanneauSuiviLivraisons
        # Dans __init__ après _init_ui() :
        self.panneau_suivi = PanneauSuiviLivraisons(self, self.ctrl)

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
        """Applique le thème actif à tous les composants de la vue lunettes."""
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_main']};")
        self.search_bar.setStyleSheet(LunetteStyles.search_bar())
        self.btn_add.setStyleSheet(LunetteStyles.button_primary())
        self.btn_add.setIcon(qta.icon("fa5s.plus-square", color=c['text_inverse']))
        round_btn = LunetteStyles.button_secondary()
        for btn, ico in [(self.btn_notification, "fa5s.bell"), (self.btn_suivi, "fa5s.shipping-fast"), (self.btn_export, "fa5s.file-export"), (self.btn_import, "fa5s.file-import")]:
            btn.setStyleSheet(round_btn)
            btn.setIcon(qta.icon(ico, color=c['primary']))
        for card, key in [(self.card_livraison, 'primary'), (self.card_session, 'success'), (self.card_attente, 'warning')]:
            color = c[key]
            card.setStyleSheet(LunetteStyles.stat_card_style(color))
            card._icon_lbl.setPixmap(qta.icon(card._icon_name, color=color).pixmap(QSize(20, 20)))
            card._title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_secondary']}; font-size:11px; border:none;")
            card.value_label.setStyleSheet(f"font-size:28px; font-weight:bold; color:{color}; border:none;")
        for frame in [self.frame_table, self.frame_graph]:
            frame.setStyleSheet(LunetteStyles.card())
            frame._icon_lbl.setPixmap(qta.icon(frame._icon_name, color=c['primary']).pixmap(QSize(16, 16)))
            frame._title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_primary']}; font-size:12px; border:none;")
            frame._separator.setStyleSheet(f"background:{c['border_light']}; border:none;")
        self.table.setStyleSheet(LunetteStyles.table())
        self.table.verticalScrollBar().setStyleSheet(LunetteStyles.scrollbar())

    def _setup_top_bar(self):
        hbox = QHBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(" Rechercher une commande de lunettes...")
        self.search_bar.setFixedHeight(45)

        self.btn_add = QPushButton(qta.icon("fa5s.plus-square", color="white"), " Ajouter")
        self.btn_add.setFixedSize(120, 45)
        self.btn_add.clicked.connect(self._ouvrir_formulaire)

        c = theme_manager.colors()
        self.btn_notification = QPushButton(qta.icon("fa5s.bell", color=c['primary']), "")
        self.btn_notification.setFixedSize(45, 45)
        self.btn_notification.setToolTip("Notifications commandes")
        self.btn_notification.clicked.connect(self._ouvrir_alertes)
        
        self.btn_suivi = QPushButton(qta.icon("fa5s.shipping-fast", color=c['primary']), "")
        self.btn_suivi.setFixedSize(45, 45)
        self.btn_suivi.setToolTip("Suivi des livraisons")
        self.btn_suivi.clicked.connect(self._ouvrir_suivi)

        self.btn_export = QPushButton(qta.icon("fa5s.file-export", color=c['primary']), "")
        self.btn_export.setFixedSize(45, 45)
        self.btn_export.setToolTip("Exporter les commandes")

        self.btn_import = QPushButton(qta.icon("fa5s.file-import", color=c['primary']), "")
        self.btn_import.setFixedSize(45, 45)
        self.btn_import.setToolTip("Importer des commandes")
        
        

        hbox.addWidget(self.search_bar)
        hbox.addWidget(self.btn_add)
        hbox.addSpacing(10)
        hbox.addWidget(self.btn_notification)
        hbox.addWidget(self.btn_suivi)
        hbox.addWidget(self.btn_export)
        hbox.addWidget(self.btn_import)
        self.main_layout.addLayout(hbox)

    # =========================================================================
    # CARDS STATISTIQUES
    # =========================================================================

    def _setup_stats_section(self):
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_livraison = self._creer_stat_card(
            "Attente de Livraisons",              "0", "fa5s.truck",         "primary")
        self.card_session   = self._creer_stat_card(
            "Commandes Lunettes Total Session",   "0", "fa5s.glasses",       "success")
        self.card_attente   = self._creer_stat_card(
            "Commandes en Attente",               "0", "fa5s.clipboard-list","warning")

        stats_layout.addWidget(self.card_livraison)
        stats_layout.addWidget(self.card_session)
        stats_layout.addWidget(self.card_attente)
        self.main_layout.addLayout(stats_layout)

    def _creer_stat_card(self, titre: str, valeur: str,
                         icone: str, accent_key: str) -> AnimatedFrame:
        c = theme_manager.colors()
        couleur = c.get(accent_key, accent_key)
        card = AnimatedFrame()
        card.setFixedHeight(120)
        card._icon_name = icone
        card._accent_key = accent_key
        card.setStyleSheet(LunetteStyles.stat_card_style(couleur))

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

        self.frame_table = self._creer_cadre_arrondi(
            "Liste des Commandes de Lunettes", "fa5s.glasses")
        self._setup_table()

        self.frame_graph = self._creer_cadre_arrondi(
            "Commandes par Mois", "fa5s.chart-bar")
        self._setup_graphe()

        bottom_layout.addWidget(self.frame_table, 3)
        bottom_layout.addWidget(self.frame_graph, 2)
        self.main_layout.addLayout(bottom_layout)

    def _creer_cadre_arrondi(self, titre: str, icone_name: str) -> AnimatedFrame:
        c = theme_manager.colors()
        frame = AnimatedFrame()
        frame._icon_name = icone_name
        frame.setStyleSheet(LunetteStyles.card())
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
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Code", "Patient", "Numéro Verre Prescrit", "Date Commande", "Actions"]
        )
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._apply_scrollbar_style(self.table)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Fixed)

        self.table.setColumnWidth(4, 100)

        self.table.setStyleSheet(LunetteStyles.table())
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setAlternatingRowColors(True)
        self.frame_table.layout().addWidget(self.table)

    def _apply_scrollbar_style(self, widget):
        widget.verticalScrollBar().setStyleSheet(LunetteStyles.scrollbar())

    def _setup_graphe(self):
        from .graphiques import CommandeLunetteAnalyseGraph
        self.graphe = CommandeLunetteAnalyseGraph(parent=self.frame_graph)
        self.frame_graph.layout().addWidget(self.graphe)

    def charger_commandes(self, code_session: str):
        """
        Appelée depuis le dashboard lors du clic sur 'Lunettes'.
        Reçoit le code_session et charge toutes les données.
        """
        self.code_session = code_session
        commandes = self.ctrl.lister_commandes(self.code_session)
        self._remplir_table(commandes)
        self._mettre_a_jour_stats()
        self._mettre_a_jour_graphe()
        
    def _filtrer_commandes(self, texte: str):
        """
        Appelée à chaque fois que l'utilisateur tape une lettre.
        """
        critere = texte.strip()
        try:
            if not critere:
                commandes = self.ctrl.lister_commandes(self.code_session)
            else:
                commandes = self.ctrl.rechercher_commande(critere, self.code_session)
            self._remplir_table(commandes)
        except Exception as e:
            print(f"Erreur lors de la recherche : {e}")
            
    def _action_voir(self, commande):
        from .modals import DetailsCommandeLunetteModal
        modal = DetailsCommandeLunetteModal(self, commande.code, self.ctrl)
        modal.exec()
        
    def _ouvrir_alertes(self):
        if self.code_session:
            self.panneau_alertes.actualiser(self.code_session)
            self.panneau_alertes.basculer()
            
    def _remplir_table(self, commandes: list):
        """Remplit la table avec la liste des commandes de lunettes."""
        self.table.setRowCount(0)
        self.table.setUpdatesEnabled(False)

        for commande in commandes:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # 1. Code
            self.table.setItem(row, 0, QTableWidgetItem(str(commande.code)))

            # 2. Patient
            nom    = getattr(commande, 'patient_nom',    "")
            prenom = getattr(commande, 'patient_prenom', "")
            nom_complet = f"{nom} {prenom}".strip() or "Patient inconnu"
            self.table.setItem(row, 1, QTableWidgetItem(nom_complet))

            # 3. Numéro Verre Prescrit
            self.table.setItem(row, 2, QTableWidgetItem(
                str(commande.numero_verre or "—")))

            # 4. Date Livraison
            date_val = commande.date_livraison
            if date_val and hasattr(date_val, "strftime"):
                date_str = date_val.strftime("%d/%m/%Y")
            elif date_val:
                date_str = str(date_val)
            else:
                date_str = "—"
            self.table.setItem(row, 3, QTableWidgetItem(date_str))

            # 5. Actions
            self._ajouter_boutons_actions(row, commande)

        self.table.setUpdatesEnabled(True)
        
    def _ajouter_boutons_actions(self, row: int, commande):
        """Ajoute les boutons voir / modifier / supprimer sur une ligne."""
        container = QWidget()
        layout    = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        c = theme_manager.colors()
        btn_view   = QPushButton(qta.icon("fa5s.eye",       color=c['info']), "")
        btn_edit   = QPushButton(qta.icon("fa5s.edit",      color=c['primary']), "")
        btn_delete = QPushButton(qta.icon("fa5s.trash-alt", color=c['danger']), "")

        btn_style = LunetteStyles.button_table_action()
        for btn in [btn_view, btn_edit, btn_delete]:
            btn.setFixedSize(26, 26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(btn_style)
            layout.addWidget(btn)

        # Connexions — logique à brancher plus tard
        btn_view.clicked.connect(self._make_handler(self._action_voir, commande))
        btn_edit.clicked.connect(self._make_handler(self._action_modifier, commande))
        # btn_delete.clicked.connect(self._make_handler(self._action_supprimer, commande))
        
        self.table.setCellWidget(row, 4, container)
        
    def _make_handler(self, func, commande):
        """Évite les problèmes de closure dans les boucles."""
        def handler():
            func(commande)
        return handler
    
    def _ouvrir_formulaire(self):
        from .commande_lunette_form import CommandeLunetteFormDialog
        dialog = CommandeLunetteFormDialog(
            controleur   = self.ctrl,
            code_session = self.code_session,
            parent       = self
        )
        if dialog.exec():
            self.charger_commandes(self.code_session)
            
    def _ouvrir_suivi(self):
        if self.code_session:
            self.panneau_suivi.actualiser(self.code_session)
            self.panneau_suivi.basculer()
            
    def _action_modifier(self, commande):
        """Ouvre le formulaire en mode édition avec les données de la commande lunette."""
        from .commande_lunette_form import CommandeLunetteFormDialog
        
        dialog = CommandeLunetteFormDialog(
            controleur    = self.ctrl,
            code_session  = self.code_session,
            commande_obj = commande,
            parent        = self
        )
        
        if dialog.exec():
            self.charger_commandes(self.code_session)

    def _mettre_a_jour_stats(self):
        """Met à jour les trois cards statistiques depuis le contrôleur."""
        if not self.code_session:
            return

        nb_livraison = self.ctrl.obtenir_commandes_en_attente_livraison(self.code_session)
        nb_session   = self.ctrl.obtenir_total_commandes_session(self.code_session)
        nb_attente   = self.ctrl.obtenir_commandes_en_attente(self.code_session)

        self.card_livraison.value_label.setText(str(nb_livraison))
        self.card_session.value_label.setText(str(nb_session))
        self.card_attente.value_label.setText(str(nb_attente))

    def _mettre_a_jour_graphe(self):
        """Met à jour le graphique des commandes par mois."""
        if not self.code_session:
            return

        try:
            stats_mensuelles = self.ctrl.obtenir_commandes_par_mois(self.code_session)
            self.graphe.update_graph(stats_mensuelles)
        except Exception as e:
            print(f"Erreur lors de la mise à jour du graphique : {e}")