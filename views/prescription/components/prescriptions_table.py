"""
Prescriptions table - tableau des prescriptions groupées par acte médical
"""
from math import ceil

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
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


class PrescriptionsTable(QWidget):
    view_clicked = Signal(object)
    edit_clicked = Signal(object)
    new_clicked = Signal()

    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.current_page = 1
        self.items_per_page = 5
        self.total_items = 0
        self.all_prescriptions = []
        self.filtered_prescriptions = []

        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.container = QFrame()
        self.container.setObjectName("PrescriptionsTableCard")
        self.container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Rechercher (code acte, patient...)")
        self.search_input.setFixedHeight(40)
        self.search_input.addAction(
            qta.icon("fa5s.search", color=theme_manager.colors()["text_muted"]),
            QLineEdit.LeadingPosition,
        )
        self.search_input.textChanged.connect(self.apply_filters)

        self.btn_new = QPushButton("Nouvelle prescription")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_new.setFixedHeight(40)
        self.btn_new.setMinimumWidth(185)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setIcon(qta.icon("fa5s.plus", color="white"))
        self.btn_new.clicked.connect(self.new_clicked.emit)

        toolbar_layout.addWidget(self.search_input, 1)
        toolbar_layout.addWidget(self.btn_new)
        container_layout.addLayout(toolbar_layout)

        self.table = QTableWidget(0, 6)
        self.table.setObjectName("PrescriptionTable")
        self.table.setHorizontalHeaderLabels(
            [
                "Code Acte",
                "Patient",
                "Date",
                "Nb Produits",
                "Quantité Totale",
                "Montant (GNF)",
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
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

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
            QFrame#PrescriptionsTableCard {{
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
            QTableWidget#PrescriptionTable {{
                background: white;
                border: none;
                gridline-color: {c['table_gridline']};
                color: {c['text_primary']};
                selection-background-color: {c['table_selection']};
            }}
            QTableWidget#PrescriptionTable::item {{
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

    def load_prescriptions(self, prescriptions):
        self.all_prescriptions = list(prescriptions or [])
        self.filtered_prescriptions = list(self.all_prescriptions)
        self.current_page = 1
        self.apply_filters()

    def apply_filters(self):
        query = self.search_input.text().strip().lower()

        filtered = []
        for prescription in self.all_prescriptions:
            if query and not self._matches_query(prescription, query):
                continue
            filtered.append(prescription)

        self.filtered_prescriptions = filtered
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
        page_prescriptions = self.filtered_prescriptions[start_idx:end_idx]

        for prescription in page_prescriptions:
            self._add_prescription_row(prescription)

    def total_pages(self):
        if self.total_items <= 0:
            return 1
        return max(1, ceil(self.total_items / self.items_per_page))

    def _matches_query(self, prescription, query):
        values = [
            prescription.get("code_acte", "") or "",
            prescription.get("patient_nom", "") or "",
            prescription.get("patient_prenom", "") or "",
            str(prescription.get("date_consultation", "") or ""),
        ]
        haystack = " ".join(str(value).lower() for value in values if value)
        return query in haystack

    def _add_prescription_row(self, prescription):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 66)

        date_str = (
            prescription.get("date_consultation").strftime("%d/%m/%Y %H:%M")
            if hasattr(prescription.get("date_consultation"), "strftime")
            else str(prescription.get("date_consultation", "-") or "-")
        )

        patient_name = f"{prescription.get('patient_prenom', '')} {prescription.get('patient_nom', '')}".strip()

        self.table.setCellWidget(
            row,
            0,
            self._build_double_line_widget(
                prescription.get("code_acte", "-") or "-",
                "",
                primary_color=theme_manager.colors()["primary"],
                primary_weight=700,
            ),
        )
        self.table.setCellWidget(
            row,
            1,
            self._build_double_line_widget(
                patient_name or "Patient inconnu",
                "",
            ),
        )
        self.table.setCellWidget(row, 2, self._build_double_line_widget(date_str, ""))
        self.table.setCellWidget(
            row,
            3,
            self._build_double_line_widget(
                str(prescription.get("nb_produits", "-") or "-"),
                "",
            ),
        )
        self.table.setCellWidget(
            row,
            4,
            self._build_double_line_widget(
                str(prescription.get("total_quantite", "-") or "-"),
                "",
            ),
        )
        self.table.setCellWidget(row, 5, self._build_amount_widget(prescription.get("total_montant")))

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
