"""
Table des actes médicaux avec pagination, filtres et actions.
"""
from math import ceil
import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QSizePolicy, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QHeaderView,
)
from views.shared.theme_manager import theme_manager


# Badges colorés par statut
STATUT_COLORS = {
    "en_attente": ("#F59E0B", "#FFFBEB"),
    "planifie":   ("#3B82F6", "#EFF6FF"),
    "en_cours":   ("#8B5CF6", "#F5F3FF"),
    "termine":    ("#10B981", "#ECFDF5"),
    "refuse":     ("#EF4444", "#FEF2F2"),
}

TYPE_LABELS = {
    "examen":       "Examen",
    "chirurgie":    "Chirurgie",
    "lunette":      "Lunette",
    "prescription": "Prescription",
}


def _badge(text: str, fg: str, bg: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setFixedHeight(24)
    lbl.setStyleSheet(
        f"background:{bg}; color:{fg}; border-radius:10px;"
        f"padding: 0 8px; font-size:11px; font-weight:600;"
    )
    return lbl


class ActesTable(QWidget):
    view_clicked   = Signal(object)   # acte row dict
    edit_clicked   = Signal(object)
    delete_clicked = Signal(object)
    choix_clicked  = Signal(object)   # enregistrer choix patient
    new_clicked    = Signal()

    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.current_page = 1
        self.items_per_page = 8
        self.all_actes = []
        self.filtered_actes = []
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    # =========================================================================
    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.container = QFrame()
        self.container.setObjectName("ActesTableCard")
        self.container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)

        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(16, 12, 16, 0)
        toolbar.setSpacing(8)

        title_lbl = QLabel("Actes médicaux")
        title_lbl.setObjectName("TableTitle")
        toolbar.addWidget(title_lbl)
        toolbar.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher…")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._filter)
        toolbar.addWidget(self.search_input)

        self.filter_type = QComboBox()
        self.filter_type.addItems(["Tous les types", "examen", "chirurgie", "lunette", "prescription"])
        self.filter_type.currentTextChanged.connect(self._filter)
        toolbar.addWidget(self.filter_type)

        self.filter_statut = QComboBox()
        self.filter_statut.addItems(["Tous les statuts", "en_attente", "planifie", "en_cours", "termine", "refuse"])
        self.filter_statut.currentTextChanged.connect(self._filter)
        toolbar.addWidget(self.filter_statut)

        self.btn_new = QPushButton(" Nouvel acte")
        self.btn_new.setObjectName("BtnNewActe")
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.clicked.connect(self.new_clicked.emit)
        toolbar.addWidget(self.btn_new)

        container_layout.addLayout(toolbar)

        # ── Table ─────────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Consultation", "Type", "Décision médicale",
            "Choix patient", "Statut", "Date création", "Actions"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        container_layout.addWidget(self.table)

        # ── Pagination ────────────────────────────────────────────────────────
        pagination_layout = QHBoxLayout()
        pagination_layout.setContentsMargins(16, 4, 16, 12)
        self.lbl_count = QLabel("0 résultats")
        self.lbl_count.setObjectName("PaginationCount")
        pagination_layout.addWidget(self.lbl_count)
        pagination_layout.addStretch()

        self.btn_prev = QPushButton()
        self.btn_prev.setFixedSize(30, 30)
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.clicked.connect(self._prev_page)
        pagination_layout.addWidget(self.btn_prev)

        self.lbl_page = QLabel("1 / 1")
        self.lbl_page.setObjectName("PaginationPage")
        pagination_layout.addWidget(self.lbl_page)

        self.btn_next = QPushButton()
        self.btn_next.setFixedSize(30, 30)
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.clicked.connect(self._next_page)
        pagination_layout.addWidget(self.btn_next)

        container_layout.addLayout(pagination_layout)
        outer.addWidget(self.container)

    # =========================================================================
    def load_actes(self, actes: list):
        self.all_actes = actes
        self._filter()

    def _filter(self):
        text   = self.search_input.text().lower()
        ftype  = self.filter_type.currentText()
        fstat  = self.filter_statut.currentText()

        result = []
        for a in self.all_actes:
            if text and text not in str(a.get("decision_medicale", "")).lower() \
                    and text not in str(a.get("code_consultation", "")).lower() \
                    and text not in str(a.get("id_acte", "")).lower():
                continue
            if ftype != "Tous les types" and a.get("type_acte") != ftype:
                continue
            if fstat != "Tous les statuts" and a.get("statut_acte") != fstat:
                continue
            result.append(a)

        self.filtered_actes = result
        self.current_page = 1
        self._render_page()

    def _render_page(self):
        c = theme_manager.colors()
        total = len(self.filtered_actes)
        total_pages = max(1, ceil(total / self.items_per_page))
        self.current_page = max(1, min(self.current_page, total_pages))

        start = (self.current_page - 1) * self.items_per_page
        page_data = self.filtered_actes[start: start + self.items_per_page]

        self.table.setRowCount(len(page_data))
        for row, acte in enumerate(page_data):
            self.table.setRowHeight(row, 48)
            self._set_cell(row, 0, str(acte.get("id_acte", "")))
            self._set_cell(row, 1, str(acte.get("code_consultation", "")))

            # Type badge
            type_acte = acte.get("type_acte", "")
            type_label = TYPE_LABELS.get(type_acte, type_acte)
            type_widget = QWidget()
            type_layout = QHBoxLayout(type_widget)
            type_layout.setContentsMargins(4, 0, 4, 0)
            type_layout.setAlignment(Qt.AlignCenter)
            type_layout.addWidget(_badge(type_label, c['primary'], c['primary_light']))
            self.table.setCellWidget(row, 2, type_widget)

            # Décision médicale (tronquée)
            decision = str(acte.get("decision_medicale", ""))
            self._set_cell(row, 3, decision[:60] + "…" if len(decision) > 60 else decision)

            # Choix patient
            choix = acte.get("choix_patient") or "—"
            choix_colors = {
                "maintenant": (c['success'],         c['success_bg']),
                "plus_tard":  (c['info'],             c['info_bg']),
                "ailleurs":   (c['danger'],           c['danger_bg']),
            }
            cw = QWidget()
            cl = QHBoxLayout(cw)
            cl.setContentsMargins(4, 0, 4, 0)
            cl.setAlignment(Qt.AlignCenter)
            fc, bc = choix_colors.get(choix, (c['text_secondary'], c['bg_main']))
            cl.addWidget(_badge(choix, fc, bc))
            self.table.setCellWidget(row, 4, cw)

            # Statut badge
            statut = acte.get("statut_acte", "")
            fc2, bc2 = STATUT_COLORS.get(statut, (c['text_secondary'], c['bg_main']))
            sw = QWidget()
            sl = QHBoxLayout(sw)
            sl.setContentsMargins(4, 0, 4, 0)
            sl.setAlignment(Qt.AlignCenter)
            sl.addWidget(_badge(statut, fc2, bc2))
            self.table.setCellWidget(row, 5, sw)

            # Date création
            date_cr = acte.get("date_creation", "")
            if hasattr(date_cr, "strftime"):
                date_cr = date_cr.strftime("%d/%m/%Y %H:%M")
            self._set_cell(row, 6, str(date_cr))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)
            actions_layout.setAlignment(Qt.AlignCenter)

            btn_view = QPushButton()
            btn_view.setFixedSize(28, 28)
            btn_view.setIcon(qta.icon("fa5s.eye", color=c['info']))
            btn_view.setToolTip("Voir détails")
            btn_view.setCursor(Qt.PointingHandCursor)
            btn_view.setStyleSheet(f"QPushButton{{background:{c['info_bg']};border-radius:6px;border:none;}} QPushButton:hover{{background:{c['hover']};}}")
            btn_view.clicked.connect(lambda _, a=acte: self.view_clicked.emit(a))

            btn_choix = QPushButton()
            btn_choix.setFixedSize(28, 28)
            btn_choix.setIcon(qta.icon("fa5s.user-check", color=c['success']))
            btn_choix.setToolTip("Enregistrer choix patient")
            btn_choix.setCursor(Qt.PointingHandCursor)
            btn_choix.setStyleSheet(f"QPushButton{{background:{c['success_bg']};border-radius:6px;border:none;}} QPushButton:hover{{background:{c['hover']};}}")
            btn_choix.clicked.connect(lambda _, a=acte: self.choix_clicked.emit(a))

            btn_edit = QPushButton()
            btn_edit.setFixedSize(28, 28)
            btn_edit.setIcon(qta.icon("fa5s.edit", color=c['warning']))
            btn_edit.setToolTip("Modifier")
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setStyleSheet(f"QPushButton{{background:{c['warning_bg']};border-radius:6px;border:none;}} QPushButton:hover{{background:{c['hover']};}}")
            btn_edit.clicked.connect(lambda _, a=acte: self.edit_clicked.emit(a))

            btn_del = QPushButton()
            btn_del.setFixedSize(28, 28)
            btn_del.setIcon(qta.icon("fa5s.trash-alt", color=c['danger']))
            btn_del.setToolTip("Supprimer")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet(f"QPushButton{{background:{c['danger_bg']};border-radius:6px;border:none;}} QPushButton:hover{{background:{c['hover']};}}")
            btn_del.clicked.connect(lambda _, a=acte: self.delete_clicked.emit(a))

            for btn in (btn_view, btn_choix, btn_edit, btn_del):
                actions_layout.addWidget(btn)

            self.table.setCellWidget(row, 7, actions_widget)

        self.lbl_count.setText(f"{total} résultat{'s' if total > 1 else ''}")
        self.lbl_page.setText(f"{self.current_page} / {total_pages}")
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < total_pages)

    def _set_cell(self, row, col, text):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.table.setItem(row, col, item)

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_page()

    def _next_page(self):
        total_pages = max(1, ceil(len(self.filtered_actes) / self.items_per_page))
        if self.current_page < total_pages:
            self.current_page += 1
            self._render_page()

    # =========================================================================
    def apply_theme(self):
        c = theme_manager.colors()
        self.container.setStyleSheet(f"""
            QFrame#ActesTableCard {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
            QLabel#TableTitle {{
                font-size: 15px; font-weight: bold; color: {c['text_primary']};
            }}
            QTableWidget {{
                background: {c['bg_table']};
                alternate-background-color: {c['bg_table_alt']};
                border: none;
                gridline-color: {c['table_gridline']};
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QHeaderView::section {{
                background: {c['table_header_bg']};
                color: {c['text_secondary']};
                font-size: 12px; font-weight: 600;
                padding: 8px 12px;
                border: none;
                border-bottom: 2px solid {c['table_header_border']};
            }}
            QLineEdit {{
                padding: 7px 10px;
                border: 1px solid {c['border']};
                border-radius: 8px;
                background: {c['bg_input']};
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 2px solid {c['border_focus']}; }}
            QComboBox {{
                padding: 7px 10px;
                border: 1px solid {c['border']};
                border-radius: 8px;
                background: {c['bg_input']};
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QPushButton#BtnNewActe {{
                background: {c['primary']};
                color: {c['text_inverse']};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
                border: none;
            }}
            QPushButton#BtnNewActe:hover {{
                background: {c['primary_hover']};
            }}
            QLabel#PaginationCount, QLabel#PaginationPage {{
                color: {c['text_secondary']};
                font-size: 12px;
            }}
        """)
        self.btn_prev.setIcon(qta.icon("fa5s.chevron-left", color=c["primary"]))
        self.btn_next.setIcon(qta.icon("fa5s.chevron-right", color=c["primary"]))
        self.btn_new.setIcon(qta.icon("fa5s.plus", color=c['text_inverse']))
        self.btn_prev.setStyleSheet(f"QPushButton{{background:{c['bg_main']};border:1px solid {c['border']};border-radius:6px;}} QPushButton:hover{{background:{c['primary_light']};}}")
        self.btn_next.setStyleSheet(f"QPushButton{{background:{c['bg_main']};border:1px solid {c['border']};border-radius:6px;}} QPushButton:hover{{background:{c['primary_light']};}}")
