"""
Examens table avec recherche, filtres et pagination
"""
from math import ceil

import qtawesome as qta
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QMessageBox
)

from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox


class ExamensTable(QWidget):
    view_clicked = Signal(object)
    edit_clicked = Signal(object)
    delete_clicked = Signal(object)
    new_clicked = Signal()

    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.code_session = None
        self.current_page = 1
        self.items_per_page = 5
        self.total_items = 0
        self.all_examens = []
        self.filtered_examens = []

        # Debounce timer pour la recherche serveur
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(350)
        self._search_timer.timeout.connect(self._executer_recherche)

        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.container = QFrame()
        self.container.setObjectName("ExamensTableCard")
        self.container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        self.search_mode = QComboBox()
        self.search_mode.setObjectName("StatusFilter")
        self.search_mode.setFixedHeight(40)
        self.search_mode.setMinimumWidth(140)
        self.search_mode.addItems(["Tous champs", "Par code", "Par n° acte", "Par libellé"])
        self.search_mode.currentTextChanged.connect(self._on_search_mode_changed)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Rechercher...")
        self.search_input.setFixedHeight(40)
        self.search_input.addAction(
            qta.icon("fa5s.search", color=theme_manager.colors()["text_muted"]),
            QLineEdit.LeadingPosition,
        )
        self.search_input.textChanged.connect(self._on_search_text_changed)

        self.status_filter = QComboBox()
        self.status_filter.setObjectName("StatusFilter")
        self.status_filter.setFixedHeight(40)
        self.status_filter.setMinimumWidth(170)
        self.status_filter.addItems(["Tous les statuts", "attente payement", "payee", "non payee"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)

        self.btn_new = QPushButton("Nouvel Examen")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_new.setFixedHeight(40)
        self.btn_new.setMinimumWidth(160)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setIcon(qta.icon("fa5s.plus", color="white"))
        self.btn_new.clicked.connect(self.new_clicked.emit)

        toolbar_layout.addWidget(self.search_mode)
        toolbar_layout.addWidget(self.search_input, 1)
        toolbar_layout.addWidget(self.status_filter)
        toolbar_layout.addWidget(self.btn_new)
        container_layout.addLayout(toolbar_layout)

        self.table = QTableWidget(0, 8)
        self.table.setObjectName("ExamenTable")
        self.table.setHorizontalHeaderLabels(
            [
                "Code",
                "Date examen",
                "Patient",
                "Libellé examen",
                "Personnel médical",
                "Frais (GNF)",
                "Statut facture",
                "Actions",
            ]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        self.table.setMouseTracking(True)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setMinimumHeight(372)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 220)
        self.table.setColumnWidth(4, 200)
        self.table.setColumnWidth(7, 132)

        container_layout.addWidget(self.table)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 4, 0, 0)
        footer_layout.setSpacing(8)

        self.btn_prev = QPushButton()
        self.btn_prev.setObjectName("PaginationButton")
        self.btn_prev.setFixedSize(28, 28)
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.setIcon(qta.icon("fa5s.chevron-left", color=theme_manager.colors()["text_secondary"]))
        self.btn_prev.clicked.connect(self.prev_page)

        self.btn_next = QPushButton()
        self.btn_next.setObjectName("PaginationButton")
        self.btn_next.setFixedSize(28, 28)
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setIcon(qta.icon("fa5s.chevron-right", color=theme_manager.colors()["text_secondary"]))
        self.btn_next.clicked.connect(self.next_page)

        self.pages_widget = QWidget()
        self.pages_layout = QHBoxLayout(self.pages_widget)
        self.pages_layout.setContentsMargins(0, 0, 0, 0)
        self.pages_layout.setSpacing(5)

        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_prev)
        footer_layout.addWidget(self.pages_widget)
        footer_layout.addWidget(self.btn_next)
        footer_layout.addStretch()

        container_layout.addLayout(footer_layout)
        outer_layout.addWidget(self.container)

    def apply_theme(self):
        c = theme_manager.colors()

        self.container.setStyleSheet(
            f"""
            QFrame#ExamensTableCard {{
                background: white;
                border: none;
            }}
            QLineEdit#SearchInput {{
                background: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 0 14px;
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QLineEdit#SearchInput:focus {{
                border: 1px solid {c['primary']};
                background: {c['bg_card']};
            }}
            QComboBox#StatusFilter {{
                background: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 0 12px;
                color: {c['text_primary']};
                font-size: 13px;
                min-width: 160px;
            }}
            QComboBox#StatusFilter::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox#StatusFilter QAbstractItemView {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                selection-background-color: {c['primary_light']};
                selection-color: {c['primary']};
                color: {c['text_primary']};
            }}
            QPushButton#PrimaryButton {{
                background: {c['primary']};
                color: {c['text_inverse']};
                border: none;
                border-radius: 10px;
                padding: 0 16px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton#PrimaryButton:hover {{
                background: {c['primary_hover']};
            }}
            QTableWidget#ExamenTable {{
                background: white;
                border: none;
                gridline-color: {c['table_gridline']};
                color: {c['text_primary']};
                selection-background-color: {c['table_selection']};
            }}
            QTableWidget#ExamenTable::item {{
                padding: 0px;
                border-bottom: 1px solid {c['border_light']};
            }}
            QHeaderView::section {{
                background: {c['table_header_bg']};
                color: {c['text_secondary']};
                border: none;
                border-bottom: 1px solid {c['border_light']};
                padding: 10px 10px;
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton#PaginationButton {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 6px;
            }}
            QPushButton#PaginationButton:hover {{
                background: {c['hover']};
                border-color: {c['primary']};
            }}
            QPushButton#PaginationButton:disabled {{
                background: {c['bg_main']};
                border-color: {c['border_light']};
            }}
            """
        )

        self.btn_prev.setIcon(qta.icon("fa5s.chevron-left", color=c["text_secondary"]))
        self.btn_next.setIcon(qta.icon("fa5s.chevron-right", color=c["text_secondary"]))
        self._refresh_pagination_buttons()

    def load_examens(self, examens, code_session: str):
        self.code_session = code_session
        self.all_examens = list(examens or [])
        self.filtered_examens = list(self.all_examens)
        self.current_page = 1
        self.apply_filters()

    def _on_search_mode_changed(self):
        mode = self.search_mode.currentText()
        hints = {
            "Tous champs": "Rechercher (code, patient, libellé...)",
            "Par code": "Ex: EXA-2026-001",
            "Par n° acte": "Ex: ACT-2026-001",
            "Par libellé": "Ex: Bilan sanguin",
        }
        self.search_input.setPlaceholderText(hints.get(mode, "Rechercher..."))
        self.search_input.clear()
        self._search_timer.stop()
        # Réinitialiser sur la liste complète
        self.filtered_examens = list(self.all_examens)
        self.total_items = len(self.filtered_examens)
        self.current_page = 1
        self.update_table()
        self._refresh_pagination_buttons()

    def _on_search_text_changed(self):
        mode = self.search_mode.currentText()
        if mode == "Tous champs":
            # Filtrage local immédiat
            self._search_timer.stop()
            self.apply_filters()
        else:
            # Recherche serveur avec debounce 350ms
            self._search_timer.start()

    def _executer_recherche(self):
        query = self.search_input.text().strip()
        mode = self.search_mode.currentText()

        if not query:
            self.filtered_examens = list(self.all_examens)
            self.total_items = len(self.filtered_examens)
            self.current_page = 1
            self.update_table()
            self._refresh_pagination_buttons()
            return

        if not self.code_session:
            return

        resultats = []
        try:
            if mode == "Par code":
                examen = self.ctrl.obtenir_par_code(query)
                resultats = [examen] if examen else []
            elif mode == "Par n° acte":
                examen = self.ctrl.obtenir_par_acte(query)
                resultats = [examen] if examen else []
            elif mode == "Par libellé":
                resultats = self.ctrl.rechercher_par_libelle(self.code_session, query) or []
        except Exception:
            resultats = []

        # Appliquer en plus le filtre statut si actif
        status_filter = self.status_filter.currentText()
        if status_filter != "Tous les statuts":
            resultats = [
                ex for ex in resultats
                if (ex.statut_facture or "").lower() == status_filter.lower()
            ]

        self.filtered_examens = resultats
        self.total_items = len(resultats)
        self.current_page = 1
        self.update_table()
        self._refresh_pagination_buttons()

    def apply_filters(self):
        query = self.search_input.text().strip().lower()
        status_filter = self.status_filter.currentText()

        filtered = []
        for examen in self.all_examens:
            if status_filter != "Tous les statuts":
                if (examen.statut_facture or "").lower() != status_filter.lower():
                    continue
            if query and not self._matches_query(examen, query):
                continue
            filtered.append(examen)

        self.filtered_examens = filtered
        self.total_items = len(filtered)
        max_page = self.total_pages()
        self.current_page = min(max(self.current_page, 1), max_page)
        self.update_table()
        self._refresh_pagination_buttons()

    def update_table(self):
        self.table.setRowCount(0)

        if self.total_items == 0:
            return

        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, self.total_items)
        page_examens = self.filtered_examens[start_idx:end_idx]

        for examen in page_examens:
            self._add_examen_row(examen)

    def total_pages(self):
        if self.total_items <= 0:
            return 1
        return max(1, ceil(self.total_items / self.items_per_page))

    def _matches_query(self, examen, query):
        values = [
            examen.code or "",
            examen.libelle_examen or "",
            examen.conclusion_medicale or "",
            str(examen.date_examen or ""),
            examen.statut_facture or "",
            getattr(examen, 'patient_nom', "") or "",
            getattr(examen, 'patient_prenom', "") or "",
            getattr(examen, 'patient_telephone', "") or "",
            getattr(examen, 'personnel_nom', "") or "",
            getattr(examen, 'personnel_prenom', "") or "",
        ]
        haystack = " ".join(str(v).lower() for v in values if v)
        return query in haystack

    def _add_examen_row(self, examen):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 66)

        date_str = (
            examen.date_examen.strftime("%d/%m/%Y %H:%M")
            if hasattr(examen.date_examen, "strftime")
            else str(examen.date_examen or "-")
        )

        patient_name  = f"{getattr(examen, 'patient_nom', '') or ''} {getattr(examen, 'patient_prenom', '') or ''}".strip()
        patient_phone = getattr(examen, 'patient_telephone', "") or ""
        pn            = getattr(examen, 'personnel_nom', "") or ""
        pp            = getattr(examen, 'personnel_prenom', "") or ""
        personnel_nom  = f"Dr. {pn} {pp}".strip() if pn else ""
        personnel_role = getattr(examen, 'personnel_fonction', "") or "Personnel médical"

        self.table.setCellWidget(
            row, 0,
            self._build_double_line_widget(
                examen.code or "-", "",
                primary_color=theme_manager.colors()["primary"],
                primary_weight=700,
            ),
        )
        self.table.setCellWidget(row, 1, self._build_double_line_widget(date_str, ""))
        self.table.setCellWidget(
            row, 2,
            self._build_double_line_widget(
                patient_name or "Patient inconnu",
                patient_phone,
                secondary_icon="fa5s.phone-alt",
            ),
        )
        self.table.setCellWidget(
            row, 3,
            self._build_double_line_widget(examen.libelle_examen or "-", ""),
        )
        self.table.setCellWidget(
            row, 4,
            self._build_double_line_widget(personnel_nom or "Dr. -", personnel_role),
        )
        self.table.setCellWidget(row, 5, self._build_amount_widget(examen.frais_examen))
        self.table.setCellWidget(row, 6, self._create_status_badge(examen.statut_facture))
        self.table.setCellWidget(row, 7, self._create_actions_buttons(examen))

    def _build_double_line_widget(
        self,
        primary_text,
        secondary_text,
        primary_color=None,
        primary_weight=600,
        secondary_icon=None,
    ):
        c = theme_manager.colors()

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)

        primary = QLabel(primary_text)
        primary.setWordWrap(True)
        primary.setStyleSheet(
            f"color: {primary_color or c['text_primary']}; font-size: 12px; font-weight: {primary_weight};"
        )
        layout.addWidget(primary)

        if secondary_text:
            secondary_row = QHBoxLayout()
            secondary_row.setContentsMargins(0, 0, 0, 0)
            secondary_row.setSpacing(6)

            if secondary_icon:
                icon_label = QLabel()
                icon_label.setPixmap(
                    qta.icon(secondary_icon, color=c["text_muted"]).pixmap(12, 12)
                )
                secondary_row.addWidget(icon_label, 0, Qt.AlignTop)

            secondary = QLabel(secondary_text)
            secondary.setWordWrap(True)
            secondary.setStyleSheet(
                f"color: {c['text_secondary']}; font-size: 11px; font-weight: 500;"
            )
            secondary_row.addWidget(secondary)
            secondary_row.addStretch()
            layout.addLayout(secondary_row)
        else:
            layout.addStretch()

        return container

    def _create_status_badge(self, statut):
        c = theme_manager.colors()
        statut = (statut or "").lower()
        if "payée" in statut or statut == "payee":
            color, bg = c.get("success", "#27ae60"), c.get("success_bg", "#27ae6020")
            label_text = "Payée"
        elif "attente" in statut:
            color, bg = c.get("warning", "#f39c12"), c.get("warning_bg", "#f39c1220")
            label_text = "Attente"
        else:
            color, bg = c.get("text_muted", "#888"), c.get("bg_main", "#f5f5f5")
            label_text = statut.capitalize() or "-"

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 0, 10, 0)
        badge = QLabel(label_text)
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedHeight(26)
        badge.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: {color};
                border: 1px solid {color}55;
                border-radius: 8px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 10px;
            }}
        """)
        layout.addWidget(badge)
        return widget

    def _build_amount_widget(self, amount):
        c = theme_manager.colors()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)

        label = QLabel(self._format_money(amount))
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 12px; font-weight: 600;"
        )
        layout.addWidget(label)
        return widget

    def _create_actions_buttons(self, examen):
        c = theme_manager.colors()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        actions = [
            ("fa5s.eye", c["primary"], c["primary_light"], "view"),
            ("fa5s.pen", c["secondary"], c["info_bg"], "edit"),
            ("fa5s.trash", c["danger"], c["danger_bg"], "delete"),
        ]

        for icon_name, icon_color, bg_color, action_name in actions:
            btn = QPushButton()
            btn.setFixedSize(30, 30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(qta.icon(icon_name, color=icon_color))
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: {bg_color};
                    border: 1px solid {c['border_light']};
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    border-color: {icon_color};
                    background: {c['bg_card']};
                }}
                """
            )
            if action_name == "view":
                btn.clicked.connect(lambda checked=False, ex=examen: self.view_clicked.emit(ex))
            elif action_name == "edit":
                btn.clicked.connect(lambda checked=False, ex=examen: self.edit_clicked.emit(ex))
            elif action_name == "delete":
                btn.clicked.connect(lambda checked=False, ex=examen: self._confirm_delete(ex))
            layout.addWidget(btn)

        return widget

    def _confirm_delete(self, examen):
        """Confirme et supprime un examen"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment supprimer l'examen {examen.code} ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.delete_clicked.emit(examen)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self._clear_layout(child_layout)

    def _refresh_pagination_buttons(self):
        c = theme_manager.colors()
        self._clear_layout(self.pages_layout)

        total_pages = self.total_pages()
        self.btn_prev.setEnabled(self.current_page > 1 and self.total_items > 0)
        self.btn_next.setEnabled(self.current_page < total_pages and self.total_items > 0)

        # Afficher seulement 3 boutons de page
        pages_to_show = []
        if total_pages <= 3:
            pages_to_show = list(range(1, total_pages + 1))
        else:
            if self.current_page == 1:
                pages_to_show = [1, 2, 3]
            elif self.current_page == total_pages:
                pages_to_show = [total_pages - 2, total_pages - 1, total_pages]
            else:
                pages_to_show = [self.current_page - 1, self.current_page, self.current_page + 1]

        for value in pages_to_show:
            btn = QPushButton(str(value))
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.PointingHandCursor)
            is_active = value == self.current_page and self.total_items > 0
            btn.setStyleSheet(self._page_button_style(is_active))
            btn.clicked.connect(lambda checked=False, page=value: self.go_to_page(page))
            self.pages_layout.addWidget(btn)

    def _page_button_style(self, active):
        c = theme_manager.colors()
        if active:
            return f"""
                QPushButton {{
                    background: {c['primary']};
                    color: {c['text_inverse']};
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 700;
                }}
            """
        return f"""
            QPushButton {{
                background: {c['bg_card']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {c['primary']};
                background: {c['hover']};
            }}
        """

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_table()
            self._refresh_pagination_buttons()

    def next_page(self):
        total_pages = self.total_pages()
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_table()
            self._refresh_pagination_buttons()

    def go_to_page(self, page):
        self.current_page = page
        self.update_table()
        self._refresh_pagination_buttons()

    def _format_money(self, value):
        try:
            return f"{float(value or 0):,.0f}".replace(",", " ")
        except Exception:
            return "0"
