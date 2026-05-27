"""
=============================================================================
 COMMANDES TABLE — tableau liste des commandes de lunettes
=============================================================================
 Colonnes : Code | Patient | Numéro Verre | Date Commande | Statut | Actions
=============================================================================
"""

import qtawesome as qta
from PySide6.QtCore    import Qt, QSize, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMenu
)

from views.shared.theme_manager import theme_manager
from views.lunette.styles       import LunetteStyles


class CommandesTable(QWidget):
    """Tableau des commandes de lunettes avec filtre et actions."""

    view_clicked                = Signal(object)
    edit_clicked                = Signal(object)
    new_clicked                 = Signal()
    imprimer_info_clicked       = Signal(object)
    imprimer_avec_resultat_clicked = Signal(object)
    new_resultat_clicked        = Signal(object)

    COLUMNS = [
        ("Code",          80,  QHeaderView.ResizeToContents),
        ("Patient",       200, QHeaderView.Stretch),
        ("Numéro Verre",  160, QHeaderView.Stretch),
        ("Date Commande", 120, QHeaderView.ResizeToContents),
        ("Statut",        130, QHeaderView.ResizeToContents),
        ("Actions",       132, QHeaderView.Fixed),
    ]

    def __init__(self, ctrl, parent=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.code_session = None
        self._all_commandes = []
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(350)
        self._search_timer.timeout.connect(self._executer_recherche)
        self._setup_ui()
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # CONSTRUCTION
    # =========================================================================

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # ── Barre de recherche + filtre + bouton ──────────────────────────
        bar = QHBoxLayout()
        bar.setSpacing(8)

        self._search_mode = QComboBox()
        self._search_mode.setObjectName("StatusFilter")
        self._search_mode.setFixedHeight(36)
        self._search_mode.setMinimumWidth(140)
        self._search_mode.addItems(["Tous champs", "Par code", "Par patient", "Par n\u00b0 verre"])
        self._search_mode.currentTextChanged.connect(self._on_search_mode_changed)

        self._search = QLineEdit()
        self._search.setPlaceholderText(" Rechercher par code, patient, verre\u2026")
        self._search.setFixedHeight(36)
        self._search.textChanged.connect(self._on_search_text_changed)

        self._filter_statut = QComboBox()
        self._filter_statut.setObjectName("StatusFilter")
        self._filter_statut.setFixedHeight(36)
        self._filter_statut.addItems(["Tous", "attente", "livree", "annulee"])
        self._filter_statut.currentIndexChanged.connect(self._filtrer)

        self._btn_new = QPushButton("  Nouveau")
        self._btn_new.setFixedHeight(36)
        self._btn_new.setCursor(Qt.PointingHandCursor)
        self._btn_new.clicked.connect(self.new_clicked)

        bar.addWidget(self._search_mode)
        bar.addWidget(self._search, 3)
        bar.addWidget(self._filter_statut, 1)
        bar.addWidget(self._btn_new)
        root.addLayout(bar)

        # ── Table ─────────────────────────────────────────────────────────
        self._table = QTableWidget(0, len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels([c[0] for c in self.COLUMNS])
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(42)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        header = self._table.horizontalHeader()
        for i, (_, width, mode) in enumerate(self.COLUMNS):
            header.setSectionResizeMode(i, mode)
            if mode == QHeaderView.Fixed:
                self._table.setColumnWidth(i, width)

        root.addWidget(self._table, 1)

    # =========================================================================
    # CHARGEMENT
    # =========================================================================

    def load_commandes(self, commandes: list, code_session: str = None):
        if code_session is not None:
            self.code_session = code_session
        self._all_commandes = commandes
        self._remplir(commandes)

    def _on_search_mode_changed(self):
        self._search.clear()
        mode = self._search_mode.currentText()
        placeholders = {
            "Tous champs": " Rechercher par code, patient, verre\u2026",
            "Par code":    " Code commande (ex: CLT001)\u2026",
            "Par patient": " Nom ou pr\u00e9nom du patient\u2026",
            "Par n\u00b0 verre": " Num\u00e9ro de verre\u2026",
        }
        self._search.setPlaceholderText(placeholders.get(mode, " Rechercher\u2026"))

    def _on_search_text_changed(self):
        mode = self._search_mode.currentText()
        if mode == "Tous champs":
            self._search_timer.stop()
            self._filtrer()
        else:
            self._search_timer.start()

    def _executer_recherche(self):
        query = self._search.text().strip()
        mode  = self._search_mode.currentText()

        if not query:
            self._all_commandes_filtered = list(self._all_commandes)
            self._remplir(self._all_commandes)
            return

        resultats = []
        try:
            if mode == "Par code":
                obj = self.ctrl.obtenir_par_code(query)
                resultats = [obj] if obj else []
            elif mode == "Par patient":
                q = query.lower()
                resultats = [
                    c for c in self._all_commandes
                    if q in (getattr(c, 'patient_nom', '') or '').lower()
                    or q in (getattr(c, 'patient_prenom', '') or '').lower()
                ]
            elif mode == "Par n\u00b0 verre":
                q = query.lower()
                resultats = [
                    c for c in self._all_commandes
                    if q in str(getattr(c, 'numero_verre', '') or '').lower()
                ]
        except Exception:
            resultats = []

        statut = self._filter_statut.currentText()
        if statut != "Tous":
            resultats = [c for c in resultats if getattr(c, 'statut', '') == statut]

        self._remplir(resultats)

    def _filtrer(self):
        texte   = self._search.text().strip().lower()
        statut  = self._filter_statut.currentText()
        result = []
        for c in self._all_commandes:
            nom    = getattr(c, 'patient_nom',    '') or ''
            prenom = getattr(c, 'patient_prenom', '') or ''
            verre  = str(getattr(c, 'numero_verre', '') or '')
            code   = str(c.code or '')
            if texte and texte not in (code + nom + prenom + verre).lower():
                continue
            if statut != "Tous" and getattr(c, 'statut', '') != statut:
                continue
            result.append(c)
        self._remplir(result)

    def _remplir(self, commandes: list):
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(0)

        for commande in commandes:
            row = self._table.rowCount()
            self._table.insertRow(row)

            # Code
            item = QTableWidgetItem(str(commande.code or ""))
            item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 0, item)

            # Patient
            nom = f"{getattr(commande,'patient_nom','') or ''} {getattr(commande,'patient_prenom','') or ''}".strip()
            self._table.setItem(row, 1, QTableWidgetItem(nom or "—"))

            # Numéro Verre
            self._table.setItem(row, 2, QTableWidgetItem(
                str(commande.numero_verre or "—")))

            # Date Commande
            dc = commande.date_commande
            date_str = dc.strftime("%d/%m/%Y") if hasattr(dc, "strftime") else str(dc or "—")
            item_date = QTableWidgetItem(date_str)
            item_date.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 3, item_date)

            # Statut badge
            self._table.setCellWidget(row, 4, self._make_statut_badge(
                getattr(commande, 'statut', '') or 'attente'
            ))

            # Actions
            self._table.setCellWidget(row, 5, self._make_actions(commande))

        self._table.setUpdatesEnabled(True)

    # ── Widgets cellule ───────────────────────────────────────────────────

    def _make_statut_badge(self, statut: str) -> QWidget:
        c = theme_manager.colors()
        colors_map = {
            "attente":  (c.get('warning', '#f39c12'),  c.get('warning', '#f39c12') + '22'),
            "livree":   (c.get('success', '#27ae60'),  c.get('success', '#27ae60') + '22'),
            "annulee":  (c.get('danger',  '#e74c3c'),  c.get('danger',  '#e74c3c') + '22'),
        }
        fg, bg = colors_map.get(statut, (c['text_secondary'], c['bg_main']))
        labels = {"attente": "En attente", "livree": "Livrée", "annulee": "Annulée"}
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setAlignment(Qt.AlignCenter)
        lbl = QLabel(labels.get(statut, statut))
        lbl.setStyleSheet(
            f"background:{bg}; color:{fg}; border-radius:8px;"
            f"padding:2px 8px; font-size:11px; font-weight:600;"
        )
        lay.addWidget(lbl)
        return w

    def _make_actions(self, commande) -> QWidget:
        c = theme_manager.colors()
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignCenter)

        btn_view = QPushButton(qta.icon("fa5s.eye",  color=c.get('info', '#3498db')), "")
        btn_edit = QPushButton(qta.icon("fa5s.edit", color=c.get('primary', '#2ecc71')), "")
        btn_menu = QPushButton(qta.icon("fa5s.ellipsis-v", color=c.get('text_secondary', '#666')), "")

        style = LunetteStyles.button_table_action()
        for btn in [btn_view, btn_edit, btn_menu]:
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(style)
            lay.addWidget(btn)

        btn_view.clicked.connect(lambda _, cm=commande: self.view_clicked.emit(cm))
        btn_edit.clicked.connect(lambda _, cm=commande: self.edit_clicked.emit(cm))
        btn_menu.clicked.connect(lambda _, cm=commande, b=btn_menu: self._show_commande_menu(cm, b))
        return w

    def _show_commande_menu(self, commande, button):
        c = theme_manager.colors()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {c.get('bg_card', '#ffffff')};
                border: 1px solid {c.get('border', '#e0e0e0')};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                color: {c.get('text_primary', '#222')};
            }}
            QMenu::item:selected {{
                background: {c.get('primary', '#2ecc71')}22;
                color: {c.get('primary', '#2ecc71')};
            }}
        """)

        act_imprimer = menu.addAction(
            qta.icon("fa5s.print", color=c.get('primary', '#2ecc71')),
            "Imprimer commande"
        )
        act_avec_resultat = menu.addAction(
            qta.icon("fa5s.file-medical-alt", color=c.get('info', '#3498db')),
            "Imprimer avec résultat"
        )
        menu.addSeparator()
        act_new_resultat = menu.addAction(
            qta.icon("fa5s.plus-circle", color=c.get('success', '#27ae60')),
            "Nouveau résultat"
        )

        act_imprimer.triggered.connect(lambda: self.imprimer_info_clicked.emit(commande))
        act_avec_resultat.triggered.connect(lambda: self.imprimer_avec_resultat_clicked.emit(commande))
        act_new_resultat.triggered.connect(lambda: self.new_resultat_clicked.emit(commande))

        pos = button.mapToGlobal(button.rect().bottomLeft())
        menu.exec(pos)

    # =========================================================================
    # THÈME
    # =========================================================================

    def apply_theme(self):
        c = theme_manager.colors()
        self._table.setStyleSheet(LunetteStyles.table())
        self._table.verticalScrollBar().setStyleSheet(LunetteStyles.scrollbar())
        self._search.setStyleSheet(LunetteStyles.search_bar())
        self._search_mode.setStyleSheet(LunetteStyles.input_field())
        self._filter_statut.setStyleSheet(LunetteStyles.input_field())
        self._btn_new.setStyleSheet(LunetteStyles.button_primary())
        self._btn_new.setIcon(
            qta.icon("fa5s.plus", color=c.get('text_inverse', '#ffffff'))
        )
