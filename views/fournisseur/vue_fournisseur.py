import qtawesome as qta
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QPoint, QEasingCurve, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QHeaderView, QFrame, QLabel, QGraphicsDropShadowEffect,
    QTableWidgetItem, QFileDialog, QMessageBox
)
from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager
from views.fournisseur.styles import FournisseurStyles


class AnimatedFrame(QFrame):
    """Cadre arrondi avec effet d ombre et animation de survol."""

    def __init__(self, parent=None):   # doit rester parent=None
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


class FournisseurView(QWidget):
    """
    Vue principale pour la gestion des fournisseurs.
    Interface uniquement - logique a implementer ulterieurement.
    """

    def __init__(self, fournisseur_ctrl):
        super().__init__()
        self.ctrl = fournisseur_ctrl
        self.code_session = None
        self._actifs_cache = None
        self._actifs_cache_session = None
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)
        self._search_timer.timeout.connect(self._appliquer_filtre)
        self._init_ui()

        # Appliquer le thème initial et écouter les changements
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def apply_theme(self):
        """Applique le thème actif à tous les composants de la vue fournisseur."""
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_main']};")
        self.search_bar.setStyleSheet(FournisseurStyles.search_bar())
        self.status_combo.setStyleSheet(FournisseurStyles.input_field())
        self.btn_add.setStyleSheet(FournisseurStyles.button_primary())
        self.btn_add.setIcon(qta.icon("fa5s.plus-square", color=c['text_inverse']))
        round_btn = FournisseurStyles.button_secondary()
        for btn, ico in [(self.btn_notification, "fa5s.bell"), (self.btn_export, "fa5s.file-export"), (self.btn_import, "fa5s.file-import")]:
            btn.setStyleSheet(round_btn)
            btn.setIcon(qta.icon(ico, color=c['primary']))
        for card, key in [(self.card_total, 'primary'), (self.card_actifs, 'success'), (self.card_inactifs, 'warning')]:
            color = c[key]
            card.setStyleSheet(FournisseurStyles.stat_card_style(color))
            card._icon_lbl.setPixmap(qta.icon(card._icon_name, color=color).pixmap(QSize(20, 20)))
            card._title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_secondary']}; font-size:11px; border:none;")
            card.value_label.setStyleSheet(f"font-size:28px; font-weight:bold; color:{color}; border:none;")
        self.frame_table.setStyleSheet(FournisseurStyles.card())
        self.frame_table._icon_lbl.setPixmap(qta.icon(self.frame_table._icon_name, color=c['primary']).pixmap(QSize(16, 16)))
        self.frame_table._title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_primary']}; font-size:12px; border:none;")
        self.frame_table._separator.setStyleSheet(f"background:{c['border_light']}; border:none;")
        self.table.setStyleSheet(FournisseurStyles.table())
        self.table.verticalScrollBar().setStyleSheet(FournisseurStyles.scrollbar())

    # =========================================================================
    # CONSTRUCTION DE L INTERFACE
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
    def _setup_top_bar(self):
        hbox = QHBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(" Rechercher un fournisseur...")
        self.search_bar.setFixedHeight(45)
        self.search_bar.textChanged.connect(self._planifier_filtre)

        self.status_combo = QComboBox()
        self.status_combo.setFixedHeight(45)
        self.status_combo.addItem(qta.icon("fa5s.list", color="#64748b"), "Tous")
        self.status_combo.addItem(qta.icon("fa5s.check-circle", color="#16a34a"), "Actif")
        self.status_combo.addItem(qta.icon("fa5s.times-circle", color="#ef4444"), "Inactif")
        self.status_combo.currentIndexChanged.connect(self._appliquer_filtre)

        self.btn_add = QPushButton(qta.icon("fa5s.plus-square", color="white"), " Ajouter")
        self.btn_add.setFixedSize(120, 45)
        self.btn_add.clicked.connect(self._ouvrir_formulaire)

        self.btn_notification = QPushButton(qta.icon("fa5s.bell", color=theme_manager.colors()['primary']), "")
        self.btn_notification.setFixedSize(45, 45)
        self.btn_notification.setToolTip("Notifications")

        self.btn_export = QPushButton(qta.icon("fa5s.file-export", color=theme_manager.colors()['primary']), "")
        self.btn_export.setFixedSize(45, 45)
        self.btn_export.setToolTip("Exporter")
        self.btn_export.clicked.connect(self._exporter)

        self.btn_import = QPushButton(qta.icon("fa5s.file-import", color=theme_manager.colors()['primary']), "")
        self.btn_import.setFixedSize(45, 45)
        self.btn_import.setToolTip("Importer")
        self.btn_import.clicked.connect(self._importer)

        hbox.addWidget(self.search_bar)
        hbox.addWidget(self.btn_add)
        hbox.addWidget(self.status_combo)
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

        self.card_total = self._creer_stat_card(
            "Total Fournisseurs", "0", "fa5s.truck", "primary")
        self.card_actifs = self._creer_stat_card(
            "Fournisseurs Actifs", "0", "fa5s.check-circle", "success")
        self.card_inactifs = self._creer_stat_card(
            "Fournisseurs Inactifs", "0", "fa5s.times-circle", "warning")

        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_actifs)
        stats_layout.addWidget(self.card_inactifs)
        self.main_layout.addLayout(stats_layout)

    def _creer_stat_card(self, titre: str, valeur: str,
                         icone: str, accent_key: str) -> AnimatedFrame:
        c = theme_manager.colors()
        couleur = c.get(accent_key, accent_key)
        card = AnimatedFrame()
        card.setFixedHeight(120)
        card._icon_name = icone
        card._accent_key = accent_key
        card.setStyleSheet(FournisseurStyles.stat_card_style(couleur))

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
    # SECTION BAS : TABLE
    # =========================================================================
    def _setup_bottom_section(self):
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        self.frame_table = self._creer_cadre_arrondi(
            "Liste des Fournisseurs", "fa5s.truck")
        self._setup_table()

        bottom_layout.addWidget(self.frame_table, 1)
        self.main_layout.addLayout(bottom_layout)

    def _creer_cadre_arrondi(self, titre: str, icone_name: str) -> AnimatedFrame:
        c = theme_manager.colors()
        frame = AnimatedFrame()
        frame._icon_name = icone_name
        frame.setStyleSheet(FournisseurStyles.card())
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
            ["Email", "Entreprise", "Telephone", "Adresse", "Actions"]
        )
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._apply_scrollbar_style(self.table)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 130)

        self.table.setStyleSheet(FournisseurStyles.table())
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setAlternatingRowColors(True)
        self.frame_table.layout().addWidget(self.table)

    def _apply_scrollbar_style(self, widget):
        widget.verticalScrollBar().setStyleSheet(FournisseurStyles.scrollbar())

    # =========================================================================
    # DONNEES / ACTIONS
    # =========================================================================
    def charger_fournisseurs(self, code_session: str = None):
        self.code_session = code_session
        self._actifs_cache = None
        self._actifs_cache_session = None
        fournisseurs = self.ctrl.get_all_fournisseurs()
        self._remplir_table(fournisseurs)
        self._mettre_a_jour_stats()

    def _filtrer_fournisseurs(self, texte):
        critere = texte.strip()
        try:
            if not critere:
                fournisseurs = self.ctrl.get_all_fournisseurs()
            else:
                if "@" in critere:
                    fournisseurs = self.ctrl.search_fournisseurs(critere="mail", valeur=critere)
                elif critere.isdigit():
                    fournisseurs = self.ctrl.search_fournisseurs(critere="telephone", valeur=critere)
                else:
                    fournisseurs = self.ctrl.search_fournisseurs(valeur=critere)

            fournisseurs = self._appliquer_filtre_statut(fournisseurs)
            self._remplir_table(fournisseurs)
        except Exception as e:
            print(f"Erreur lors de la recherche : {e}")

    def _planifier_filtre(self, _texte):
        self._search_timer.start()

    def _appliquer_filtre(self):
        texte = self.search_bar.text()
        self._filtrer_fournisseurs(texte)

    def _appliquer_filtre_statut(self, fournisseurs: list):
        statut = self.status_combo.currentText() if hasattr(self, "status_combo") else "Tous"
        if statut == "Tous":
            return fournisseurs

        actifs = self._get_actifs_set()
        if statut == "Actif":
            return [f for f in fournisseurs if f.get("email_fournisseur") in actifs]
        if statut == "Inactif":
            return [f for f in fournisseurs if f.get("email_fournisseur") not in actifs]
        return fournisseurs

    def _get_actifs_set(self):
        if self._actifs_cache is None or self._actifs_cache_session != self.code_session:
            actifs_list = self.ctrl.get_fournisseurs_actifs(self.code_session)
            self._actifs_cache = set(actifs_list or [])
            self._actifs_cache_session = self.code_session
        return self._actifs_cache

    def _remplir_table(self, fournisseurs: list):
        self.table.setRowCount(0)
        self.table.setUpdatesEnabled(False)

        for fournisseur in fournisseurs:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(str(fournisseur.get("email_fournisseur", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(fournisseur.get("nom_entreprise", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(fournisseur.get("telephone", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(fournisseur.get("adresse", ""))))

            self._ajouter_boutons_actions(row, fournisseur)

        self.table.setUpdatesEnabled(True)

    def _mettre_a_jour_stats(self):
        stats = self.ctrl.get_fournisseur_stats(self.code_session)
        total = stats.get("total", 0)
        actifs = stats.get("actifs", 0)
        inactifs = stats.get("inactifs", 0)

        self.card_total.value_label.setText(str(total))
        self.card_actifs.value_label.setText(str(actifs))
        self.card_inactifs.value_label.setText(str(inactifs))

    def _make_handler(self, func, fournisseur):
        def handler():
            func(fournisseur)
        return handler

    def _action_voir(self, fournisseur):
        from .detail_fournisseur_modal import DetailsFournisseurModal
        dialog = DetailsFournisseurModal(self, fournisseur, self.ctrl)
        dialog.exec()

    def _action_modifier(self, fournisseur):
        from .fournisseur_form import FournisseurFormDialog
        dialog = FournisseurFormDialog(self.ctrl, fournisseur_obj=fournisseur, parent=self)
        if dialog.exec():
            self.show_message(True, "Fournisseur mis a jour.")
            self._actifs_cache = None
            self.charger_fournisseurs()

    def _action_supprimer(self, fournisseur):
        mail = fournisseur.get("email_fournisseur", "")
        if not mail:
            self.show_message(False, "Email introuvable.")
            return

        rep = QMessageBox.question(
            self,
            "Confirmation",
            f"Supprimer le fournisseur {mail} ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep == QMessageBox.Yes:
            ok, msg = self.ctrl.delete_fournisseur(mail)
            self.show_message(ok, msg)
            if ok:
                self._actifs_cache = None
                self.charger_fournisseurs()

    def _action_work(self, fournisseur):
        from .fournisseur_action_dialog import FournisseurActionDialog
        dialog = FournisseurActionDialog(self.ctrl, fournisseur, code_session=self.code_session, parent=self)
        dialog.exec()

    def _ouvrir_formulaire(self):
        from .fournisseur_form import FournisseurFormDialog
        dialog = FournisseurFormDialog(self.ctrl, parent=self)
        if dialog.exec():
            self._actifs_cache = None
            self.charger_fournisseurs()

    def _ajouter_boutons_actions(self, row: int, fournisseur):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        c = theme_manager.colors()
        btn_view = QPushButton(qta.icon("fa5s.eye", color=c['info']), "")
        btn_edit = QPushButton(qta.icon("fa5s.edit", color=c['primary']), "")
        btn_work = QPushButton(qta.icon("fa5s.briefcase", color=c['success']), "")
        btn_delete = QPushButton(qta.icon("fa5s.trash-alt", color=c['danger']), "")

        btn_style = FournisseurStyles.button_table_action()
        for btn in [btn_view, btn_edit, btn_work, btn_delete]:
            btn.setFixedSize(26, 26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(btn_style)
            layout.addWidget(btn)

        btn_view.clicked.connect(self._make_handler(self._action_voir, fournisseur))
        btn_edit.clicked.connect(self._make_handler(self._action_modifier, fournisseur))
        btn_work.clicked.connect(self._make_handler(self._action_work, fournisseur))
        btn_delete.clicked.connect(self._make_handler(self._action_supprimer, fournisseur))

        self.table.setCellWidget(row, 4, container)

    # =========================================================================
    # EXPORT / IMPORT
    # =========================================================================
    def _exporter(self):
        chemin, _ = QFileDialog.getSaveFileName(
            self, "Exporter fournisseurs", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not chemin:
            return
        if chemin.lower().endswith(".csv"):
            ok, msg = self.ctrl.exporter_fournisseurs_to_csv(chemin)
        else:
            if not chemin.lower().endswith(".xlsx"):
                chemin = chemin + ".xlsx"
            ok, msg = self.ctrl.exporter_fournisseurs_to_excel(chemin)
        self.show_message(ok, msg)

    def _importer(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Importer fournisseurs", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not chemin:
            return
        if chemin.lower().endswith(".csv"):
            ok, msg = self.ctrl.importer_fournisseurs_from_csv(chemin)
        else:
            ok, msg = self.ctrl.importer_fournisseurs_from_excel(chemin)
        self.show_message(ok, msg)
        if ok:
            self.charger_fournisseurs()

    def show_message(self, reussite, message):
        titre = "Succes" if reussite else "Information / Erreur"
        dialog = CustomMessageBox(titre, message, is_success=reussite, parent=self)
        dialog.exec()
