"""
Consultations table inspired by the target mockup.
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
)

from views.shared.theme_manager import theme_manager


class ConsultationsTable(QWidget):
    view_clicked = Signal(object)
    edit_clicked = Signal(object)
    delete_clicked = Signal(object)
    new_clicked = Signal()
    imprimer_info_clicked = Signal(object)
    imprimer_avec_resultat_clicked = Signal(object)
    new_resultat_clicked = Signal(object)

    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.code_session = None
        self.current_page = 1
        self.items_per_page = 5
        self.total_items = 0
        self.all_consultations = []
        self.filtered_consultations = []
        self.consultation_details = {}
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
        self.container.setObjectName("ConsultationsTableCard")
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
        self.search_mode.addItems(["Tous champs", "Par code", "Par patient", "Par diagnostic"])
        self.search_mode.currentTextChanged.connect(self._on_search_mode_changed)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Rechercher (code, patient, diagnostic...)")
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
        self.status_filter.addItems(["Tous les statuts", "Facturee", "Non facturee", "En attente"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)

        self.btn_new = QPushButton("Nouvelle consultation")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_new.setFixedHeight(40)
        self.btn_new.setMinimumWidth(185)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setIcon(qta.icon("fa5s.plus", color="white"))
        self.btn_new.clicked.connect(self.new_clicked.emit)

        toolbar_layout.addWidget(self.search_mode)
        toolbar_layout.addWidget(self.search_input, 1)
        toolbar_layout.addWidget(self.status_filter)
        toolbar_layout.addWidget(self.btn_new)
        container_layout.addLayout(toolbar_layout)

        self.table = QTableWidget(0, 8)
        self.table.setObjectName("ConsultationTable")
        self.table.setHorizontalHeaderLabels(
            [
                "Code",
                "Date consultation",
                "Patient",
                "Diagnostic",
                "Personnel medical",
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
        self.table.setColumnWidth(2, 220)
        self.table.setColumnWidth(3, 240)
        self.table.setColumnWidth(4, 220)
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
        _pages_inner = QHBoxLayout(self.pages_widget)
        _pages_inner.setContentsMargins(0, 0, 0, 0)
        _pages_inner.setSpacing(5)

        self.page_buttons = []
        for i in range(1, 4):
            btn = QPushButton(str(i))
            btn.setObjectName("PageButton")
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setVisible(False)
            btn.clicked.connect(lambda checked=False, p=i: self.go_to_page(p))
            self.page_buttons.append(btn)
            _pages_inner.addWidget(btn)

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
            QFrame#ConsultationsTableCard {{
                background: {c['bg_card']};
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
            QTableWidget#ConsultationTable {{
                background: {c['bg_table']};
                border: none;
                gridline-color: {c['table_gridline']};
                color: {c['text_primary']};
                selection-background-color: {c['table_selection']};
            }}
            QTableWidget#ConsultationTable::item {{
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
        self._update_pagination()
        if self.filtered_consultations:
            self.update_table()

    def load_consultations(self, consultations, code_session: str = None):
        if code_session is not None:
            self.code_session = code_session
        self.all_consultations = list(consultations or [])
        self.filtered_consultations = list(self.all_consultations)
        self.consultation_details.clear()
        self.current_page = 1
        self.apply_filters()

    def _on_search_mode_changed(self):
        self.search_input.clear()
        placeholders = {
            "Tous champs":    "Rechercher (code, patient, diagnostic...)",
            "Par code":       "Code consultation (ex: CSL001)...",
            "Par patient":    "Nom ou prénom du patient...",
            "Par diagnostic": "Terme du diagnostic...",
        }
        self.search_input.setPlaceholderText(
            placeholders.get(self.search_mode.currentText(), "Rechercher...")
        )

    def _on_search_text_changed(self):
        mode = self.search_mode.currentText()
        if mode == "Tous champs":
            self._search_timer.stop()
            self.apply_filters()
        else:
            self._search_timer.start()

    def _executer_recherche(self):
        query = self.search_input.text().strip()
        mode  = self.search_mode.currentText()

        if not query:
            self.filtered_consultations = list(self.all_consultations)
            self.total_items = len(self.filtered_consultations)
            self.current_page = 1
            self.update_table()
            return

        resultats = []
        try:
            if mode == "Par code":
                obj = self.ctrl.obtenir_par_code(query)
                resultats = [obj] if obj else []
            elif mode == "Par patient":
                q = query.lower()
                details = [
                    (c, self._get_detail(c)) for c in self.all_consultations
                ]
                resultats = [
                    c for c, d in details
                    if q in (d.get("patient_nom", "") or "").lower()
                    or q in (d.get("patient_prenom", "") or "").lower()
                ]
            elif mode == "Par diagnostic":
                q = query.lower()
                resultats = [
                    c for c in self.all_consultations
                    if q in (getattr(c, "diagnostique", "") or "").lower()
                ]
        except Exception:
            resultats = []

        status_filter = self.status_filter.currentText()
        if status_filter != "Tous les statuts":
            resultats = [
                c for c in resultats
                if self._normalize_status(c.statut_facture) == status_filter
            ]

        self.filtered_consultations = resultats
        self.total_items = len(resultats)
        self.current_page = 1
        self.update_table()

    def apply_filters(self):
        query = self.search_input.text().strip().lower()
        status_filter = self.status_filter.currentText()

        filtered = []
        for consultation in self.all_consultations:
            if status_filter != "Tous les statuts":
                if self._normalize_status(consultation.statut_facture) != status_filter:
                    continue
            if query and not self._matches_query(consultation, query):
                continue
            filtered.append(consultation)

        self.filtered_consultations = filtered
        self.total_items = len(filtered)
        max_page = self.total_pages()
        self.current_page = min(max(self.current_page, 1), max_page)
        self.update_table()

    def update_table(self):
        self.table.setRowCount(0)
        if self.total_items > 0:
            start_idx = (self.current_page - 1) * self.items_per_page
            end_idx = min(start_idx + self.items_per_page, self.total_items)
            for consultation in self.filtered_consultations[start_idx:end_idx]:
                self._add_consultation_row(consultation)
        self._update_pagination()

    def total_pages(self):
        if self.total_items <= 0:
            return 1
        return max(1, ceil(self.total_items / self.items_per_page))

    def _matches_query(self, consultation, query):
        detail = self._get_detail(consultation)
        values = [
            consultation.code or "",
            consultation.diagnostique or "",
            str(consultation.date_consultation or ""),
            self._normalize_status(consultation.statut_facture),
        ]
        if detail:
            values.extend(
                [
                    detail.get("patient_nom", ""),
                    detail.get("patient_prenom", ""),
                    detail.get("patient_telephone", ""),
                    detail.get("personnel_nom", ""),
                    detail.get("personnel_prenom", ""),
                    detail.get("personnel_fonction", ""),
                ]
            )
        haystack = " ".join(str(value).lower() for value in values if value)
        return query in haystack

    def _get_detail(self, consultation):
        if consultation.code not in self.consultation_details:
            self.consultation_details[consultation.code] = (
                self.ctrl.obtenir_consultation_complete(consultation.code) or {}
            )
        return self.consultation_details[consultation.code]

    def _add_consultation_row(self, consultation):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 66)

        detail = self._get_detail(consultation)
        date_str = (
            consultation.date_consultation.strftime("%d/%m/%Y %H:%M")
            if hasattr(consultation.date_consultation, "strftime")
            else str(consultation.date_consultation or "-")
        )

        patient_name = f"{detail.get('patient_nom', '')} {detail.get('patient_prenom', '')}".strip()
        patient_phone = detail.get("patient_telephone", "") or "Telephone indisponible"
        doctor_name = f"Dr. {detail.get('personnel_nom', '')} {detail.get('personnel_prenom', '')}".strip()
        doctor_role = detail.get("personnel_fonction", "") or "Personnel medical"

        self.table.setCellWidget(
            row,
            0,
            self._build_double_line_widget(
                consultation.code or "-",
                "",
                primary_color=theme_manager.colors()["primary"],
                primary_weight=700,
            ),
        )
        self.table.setCellWidget(row, 1, self._build_double_line_widget(date_str, ""))
        self.table.setCellWidget(
            row,
            2,
            self._build_double_line_widget(
                patient_name or "Patient inconnu",
                patient_phone,
                secondary_icon="fa5s.phone-alt",
            ),
        )
        self.table.setCellWidget(
            row,
            3,
            self._build_double_line_widget(
                consultation.diagnostique or "-",
                "",
            ),
        )
        self.table.setCellWidget(
            row,
            4,
            self._build_double_line_widget(doctor_name or "Dr. -", doctor_role),
        )
        self.table.setCellWidget(row, 5, self._build_amount_widget(consultation.frais_consultation))
        self.table.setCellWidget(row, 6, self._create_status_badge(consultation.statut_facture))
        self.table.setCellWidget(row, 7, self._create_actions_buttons(consultation))

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

    def _create_status_badge(self, status):
        c = theme_manager.colors()
        normalized = self._normalize_status(status)

        status_colors = {
            "Facturee": (c["success_bg"], c["success"]),
            "Non facturee": (c["warning_bg"], c["warning"]),
            "En attente": (c["info_bg"], c["info"]),
        }
        bg_color, text_color = status_colors.get(normalized, (c["hover"], c["text_secondary"]))

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        badge = QLabel(normalized)
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedHeight(30)
        badge.setStyleSheet(
            f"""
            background: {bg_color};
            color: {text_color};
            border-radius: 8px;
            padding: 0 12px;
            font-size: 11px;
            font-weight: 700;
            """
        )
        layout.addWidget(badge)
        return widget

    def _create_actions_buttons(self, consultation):
        c = theme_manager.colors()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        actions = [
            ("fa5s.eye", c["primary"], c["primary_light"], "view"),
            ("fa5s.pen", c["secondary"], c["info_bg"], "edit"),
            ("fa5s.ellipsis-v", c["text_secondary"], c["hover"], "menu"),
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
                btn.clicked.connect(lambda checked=False, cons=consultation: self.view_clicked.emit(cons))
            elif action_name == "edit":
                btn.clicked.connect(lambda checked=False, cons=consultation: self.edit_clicked.emit(cons))
            elif action_name == "menu":
                btn.clicked.connect(lambda checked=False, cons=consultation, b=btn: self._show_consultation_menu(cons, b))
            layout.addWidget(btn)

        return widget

    def _show_consultation_menu(self, consultation, button):
        """Affiche le menu popover pour une consultation."""
        from PySide6.QtWidgets import QMenu
        c = theme_manager.colors()

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 6px 0;
            }}
            QMenu::item {{
                padding: 10px 20px;
                color: {c['text_primary']};
                font-size: 13px;
                font-weight: 500;
            }}
            QMenu::item:selected {{
                background: {c['primary_light']};
                color: {c['primary']};
                border-radius: 4px;
            }}
            QMenu::separator {{
                height: 1px;
                background: {c['border_light']};
                margin: 4px 8px;
            }}
        """)

        action_info = menu.addAction(
            qta.icon("fa5s.print", color=c['primary']),
            "  Imprimer informations"
        )
        action_info.triggered.connect(lambda: self.imprimer_info_clicked.emit(consultation))

        menu.addSeparator()

        action_avec_resultat = menu.addAction(
            qta.icon("fa5s.file-medical-alt", color=c['success']),
            "  Imprimer avec résultat"
        )
        action_avec_resultat.triggered.connect(lambda: self.imprimer_avec_resultat_clicked.emit(consultation))

        menu.addSeparator()

        action_new_resultat = menu.addAction(
            qta.icon("fa5s.plus-circle", color=c['secondary']),
            "  Nouveau résultat"
        )
        action_new_resultat.triggered.connect(lambda: self.new_resultat_clicked.emit(consultation))

        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def _update_pagination(self):
        total_pages = self.total_pages()
        self.btn_prev.setEnabled(self.current_page > 1 and self.total_items > 0)
        self.btn_next.setEnabled(self.current_page < total_pages and self.total_items > 0)

        if total_pages <= 3:
            pages_to_show = list(range(1, total_pages + 1))
        elif self.current_page == 1:
            pages_to_show = [1, 2, 3]
        elif self.current_page == total_pages:
            pages_to_show = [total_pages - 2, total_pages - 1, total_pages]
        else:
            pages_to_show = [self.current_page - 1, self.current_page, self.current_page + 1]

        for i, btn in enumerate(self.page_buttons):
            if i < len(pages_to_show):
                page_num = pages_to_show[i]
                btn.setText(str(page_num))
                btn.setVisible(True)
                try:
                    btn.clicked.disconnect()
                except RuntimeError:
                    pass
                p = page_num
                btn.clicked.connect(lambda checked=False, _p=p: self.go_to_page(_p))
                btn.setStyleSheet(self._page_button_style(page_num == self.current_page and self.total_items > 0))
            else:
                btn.setVisible(False)

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

    def next_page(self):
        total_pages = self.total_pages()
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_table()

    def go_to_page(self, page):
        self.current_page = page
        self.update_table()

    def _normalize_status(self, status):
        raw = (status or "").strip().lower()
        if "non" in raw and "fact" in raw:
            return "Non facturee"
        if "fact" in raw and "non" not in raw and "attente" not in raw:
            return "Facturee"
        if "attente" in raw or "pay" in raw:
            return "En attente"
        if raw == "":
            return "En attente"
        return status

    def _format_money(self, value):
        try:
            return f"{float(value or 0):,.0f}".replace(",", " ")
        except Exception:
            return "0"
