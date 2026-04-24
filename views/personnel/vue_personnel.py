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
from views.personnel.styles import PersonnelStyles


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


class PersonnelView(QWidget):
    def __init__(self, personnel_ctrl):
        super().__init__()
        self.ctrl = personnel_ctrl
        self._personnels_cache = []
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)
        self._search_timer.timeout.connect(self._appliquer_filtre)
        self._init_ui()

        # Appliquer le thème initial et écouter les changements
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def apply_theme(self):
        """Applique le thème actif à tous les composants de la vue personnel."""
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_main']};")
        self.search_bar.setStyleSheet(PersonnelStyles.search_bar())
        self.status_combo.setStyleSheet(PersonnelStyles.input_field())
        self.btn_add.setStyleSheet(PersonnelStyles.button_primary())
        self.btn_add.setIcon(qta.icon("fa5s.plus-square", color=c['text_inverse']))
        round_btn = PersonnelStyles.button_secondary()
        for btn, ico in [(self.btn_pdf, "fa5s.file-pdf"), (self.btn_export, "fa5s.file-export"), (self.btn_import, "fa5s.file-import")]:
            btn.setStyleSheet(round_btn)
            btn.setIcon(qta.icon(ico, color=c['primary']))
        for card, key in [(self.card_total, 'primary'), (self.card_avec_photo, 'success'), (self.card_sans_photo, 'warning')]:
            color = c[key]
            card.setStyleSheet(PersonnelStyles.stat_card_style(color))
            card._icon_lbl.setPixmap(qta.icon(card._icon_name, color=color).pixmap(QSize(20, 20)))
            card._title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_secondary']}; font-size:11px; border:none;")
            card.value_label.setStyleSheet(f"font-size:28px; font-weight:bold; color:{color}; border:none;")
        self.frame_table.setStyleSheet(PersonnelStyles.card())
        self.frame_table._icon_lbl.setPixmap(qta.icon(self.frame_table._icon_name, color=c['primary']).pixmap(QSize(16, 16)))
        self.frame_table._title_lbl.setStyleSheet(f"font-weight:bold; color:{c['text_primary']}; font-size:12px; border:none;")
        self.frame_table._separator.setStyleSheet(f"background:{c['border_light']}; border:none;")
        self.table.setStyleSheet(PersonnelStyles.table())
        self.table.verticalScrollBar().setStyleSheet(PersonnelStyles.scrollbar())

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        self._setup_top_bar()
        self._setup_stats_section()
        self._setup_bottom_section()

    def _setup_top_bar(self):
        hbox = QHBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(" Rechercher un personnel...")
        self.search_bar.setFixedHeight(45)
        self.search_bar.textChanged.connect(self._planifier_filtre)

        self.status_combo = QComboBox()
        self.status_combo.setFixedHeight(45)
        self.status_combo.addItem(qta.icon("fa5s.list", color="#64748b"), "Tous")
        self.status_combo.addItem(qta.icon("fa5s.image", color="#16a34a"), "Avec photo")
        self.status_combo.addItem(qta.icon("fa5s.user-circle", color="#ef4444"), "Sans photo")
        self.status_combo.currentIndexChanged.connect(self._appliquer_filtre)

        self.btn_add = QPushButton(qta.icon("fa5s.plus-square", color="white"), " Ajouter")
        self.btn_add.setFixedSize(120, 45)
        self.btn_add.clicked.connect(self._ouvrir_formulaire)

        self.btn_pdf = QPushButton(qta.icon("fa5s.file-pdf", color=theme_manager.colors()['primary']), "")
        self.btn_pdf.setFixedSize(45, 45)
        self.btn_pdf.setToolTip("Exporter la liste en PDF")
        self.btn_pdf.clicked.connect(self._exporter_pdf)

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
        hbox.addWidget(self.btn_pdf)
        hbox.addWidget(self.btn_export)
        hbox.addWidget(self.btn_import)
        self.main_layout.addLayout(hbox)

    def _setup_stats_section(self):
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_total = self._creer_stat_card(
            "Total Personnel", "0", "fa5s.users", "primary")
        self.card_avec_photo = self._creer_stat_card(
            "Avec Photo", "0", "fa5s.image", "success")
        self.card_sans_photo = self._creer_stat_card(
            "Sans Photo", "0", "fa5s.user-circle", "warning")

        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_avec_photo)
        stats_layout.addWidget(self.card_sans_photo)
        self.main_layout.addLayout(stats_layout)

    def _creer_stat_card(self, titre: str, valeur: str,
                         icone: str, accent_key: str) -> AnimatedFrame:
        c = theme_manager.colors()
        couleur = c.get(accent_key, accent_key)
        card = AnimatedFrame()
        card.setFixedHeight(120)
        card._icon_name = icone
        card._accent_key = accent_key
        card.setStyleSheet(PersonnelStyles.stat_card_style(couleur))

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

    def _setup_bottom_section(self):
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        self.frame_table = self._creer_cadre_arrondi(
            "Liste du Personnel", "fa5s.users")
        self._setup_table()

        bottom_layout.addWidget(self.frame_table, 1)
        self.main_layout.addLayout(bottom_layout)

    def _creer_cadre_arrondi(self, titre: str, icone_name: str) -> AnimatedFrame:
        c = theme_manager.colors()
        frame = AnimatedFrame()
        frame._icon_name = icone_name
        frame.setStyleSheet(PersonnelStyles.card())
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

        title_lbl = QLabel(titre)
        title_lbl.setStyleSheet(
            "font-weight: bold; color: #333; font-size: 12px; border: none;"
        )
        header.addWidget(icon_lbl)
        header.addSpacing(6)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #f0f0f0; border: none;")
        layout.addWidget(sep)

        return frame

    def _setup_table(self):
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Code", "Nom complet", "Fonction", "Contact", "Email", "Actions"]
        )
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._apply_scrollbar_style(self.table)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 130)

        self.table.setStyleSheet(PersonnelStyles.table())
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setAlternatingRowColors(True)
        self.frame_table.layout().addWidget(self.table)

    def _apply_scrollbar_style(self, widget):
        widget.verticalScrollBar().setStyleSheet(PersonnelStyles.scrollbar())

    def charger_personnels(self, _code_session: str = None):
        self._personnels_cache = self.ctrl.get_all_personnels()
        self._appliquer_filtre()
        self._mettre_a_jour_stats()

    def _planifier_filtre(self, _texte):
        self._search_timer.start()

    def _appliquer_filtre(self):
        personnels = list(self._personnels_cache or self.ctrl.get_all_personnels())
        texte = self.search_bar.text().strip().lower()
        if texte:
            personnels = [
                p for p in personnels
                if texte in " ".join([
                    str(p.get("code", "")),
                    str(p.get("nom", "")),
                    str(p.get("prenom", "")),
                    str(p.get("fonction", "")),
                    str(p.get("contact", "")),
                    str(p.get("mail", "")),
                    str(p.get("adresse", "")),
                ]).lower()
            ]
        personnels = self._appliquer_filtre_statut(personnels)
        self._remplir_table(personnels)

    def _appliquer_filtre_statut(self, personnels: list):
        statut = self.status_combo.currentText() if hasattr(self, "status_combo") else "Tous"
        if statut == "Tous":
            return personnels
        if statut == "Avec photo":
            return [p for p in personnels if p.get("photo_path")]
        if statut == "Sans photo":
            return [p for p in personnels if not p.get("photo_path")]
        return personnels

    def _remplir_table(self, personnels: list):
        self.table.setRowCount(0)
        self.table.setUpdatesEnabled(False)

        for personnel in personnels:
            row = self.table.rowCount()
            self.table.insertRow(row)

            nom_complet = f"{personnel.get('nom', '')} {personnel.get('prenom', '')}".strip()
            self.table.setItem(row, 0, QTableWidgetItem(str(personnel.get("code", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(nom_complet))
            self.table.setItem(row, 2, QTableWidgetItem(str(personnel.get("fonction", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(personnel.get("contact", ""))))
            self.table.setItem(row, 4, QTableWidgetItem(str(personnel.get("mail", ""))))

            self._ajouter_boutons_actions(row, personnel)

        self.table.setUpdatesEnabled(True)

    def _mettre_a_jour_stats(self):
        stats = self.ctrl.get_personnel_stats()
        self.card_total.value_label.setText(str(stats.get("total", 0)))
        self.card_avec_photo.value_label.setText(str(stats.get("avec_photo", 0)))
        self.card_sans_photo.value_label.setText(str(stats.get("sans_photo", 0)))

    def _make_handler(self, func, personnel):
        def handler():
            func(personnel)
        return handler

    def _action_voir(self, personnel):
        from .detail_personnel_modal import DetailsPersonnelModal
        dialog = DetailsPersonnelModal(self, personnel, self.ctrl)
        dialog.exec()

    def _action_modifier(self, personnel):
        from .personnel_form import PersonnelFormDialog
        dialog = PersonnelFormDialog(self.ctrl, personnel_obj=personnel, parent=self)
        if dialog.exec():
            self.show_message(True, "Personnel mis a jour.")
            self.charger_personnels()

    def _action_supprimer(self, personnel):
        mail = personnel.get("mail", "")
        if not mail:
            self.show_message(False, "Email introuvable.")
            return

        rep = QMessageBox.question(
            self,
            "Confirmation",
            f"Supprimer le personnel {mail} ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep == QMessageBox.Yes:
            ok, msg = self.ctrl.delete_personnel(mail)
            self.show_message(ok, msg)
            if ok:
                self.charger_personnels()

    def _action_carte(self, personnel):
        code = personnel.get("code", "")
        if not code:
            self.show_message(False, "Code personnel introuvable.")
            return
        chemin, _ = QFileDialog.getSaveFileName(
            self, "Generer carte membre", f"carte_{code}.pdf", "PDF Files (*.pdf)"
        )
        if not chemin:
            return
        ok, msg = self.ctrl.generer_carte_membre_pdf(code, chemin)
        self.show_message(ok, msg)

    def _ouvrir_formulaire(self):
        from .personnel_form import PersonnelFormDialog
        dialog = PersonnelFormDialog(self.ctrl, parent=self)
        if dialog.exec():
            self.charger_personnels()

    def _ajouter_boutons_actions(self, row: int, personnel):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        c = theme_manager.colors()
        btn_view = QPushButton(qta.icon("fa5s.eye", color=c['info']), "")
        btn_edit = QPushButton(qta.icon("fa5s.edit", color=c['primary']), "")
        btn_card = QPushButton(qta.icon("fa5s.id-card", color=c['success']), "")
        btn_delete = QPushButton(qta.icon("fa5s.trash-alt", color=c['danger']), "")

        btn_style = PersonnelStyles.button_table_action()
        for btn in [btn_view, btn_edit, btn_card, btn_delete]:
            btn.setFixedSize(26, 26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(btn_style)
            layout.addWidget(btn)

        btn_view.clicked.connect(self._make_handler(self._action_voir, personnel))
        btn_edit.clicked.connect(self._make_handler(self._action_modifier, personnel))
        btn_card.clicked.connect(self._make_handler(self._action_carte, personnel))
        btn_delete.clicked.connect(self._make_handler(self._action_supprimer, personnel))

        self.table.setCellWidget(row, 5, container)

    def _exporter_pdf(self):
        chemin, _ = QFileDialog.getSaveFileName(
            self, "Exporter la liste du personnel", "", "PDF Files (*.pdf)"
        )
        if not chemin:
            return
        ok, msg = self.ctrl.generer_liste_pdf(chemin)
        self.show_message(ok, msg)

    def _exporter(self):
        chemin, _ = QFileDialog.getSaveFileName(
            self, "Exporter personnel", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not chemin:
            return
        if chemin.lower().endswith(".csv"):
            ok, msg = self.ctrl.export_to_csv(chemin)
        else:
            if not chemin.lower().endswith(".xlsx"):
                chemin = chemin + ".xlsx"
            ok, msg = self.ctrl.export_to_excel(chemin)
        self.show_message(ok, msg)

    def _importer(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Importer personnel", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not chemin:
            return
        if chemin.lower().endswith(".csv"):
            ok, msg = self.ctrl.import_from_csv(chemin)
        else:
            ok, msg = self.ctrl.import_from_excel(chemin)
        self.show_message(ok, msg)
        if ok:
            self.charger_personnels()

    def show_message(self, reussite, message):
        titre = "Succes" if reussite else "Information / Erreur"
        dialog = CustomMessageBox(titre, message, is_success=reussite, parent=self)
        dialog.exec()
