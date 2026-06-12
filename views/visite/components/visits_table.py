"""
Visits Table - Table principale des visites prioritaires
Avec recherche, filtres, badges de priorité/statut, pagination
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class VisitsTable(QWidget):
    """Table des visites avec recherche et filtres"""

    view_clicked = Signal(object)
    edit_clicked = Signal(object)

    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.current_page = 1
        self.items_per_page = 5
        self.total_items = 0
        self.all_visits = []
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Barre de recherche + filtres + bouton
        search_bar = QHBoxLayout()
        search_bar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher (nom, prénom...)")
        self.search_input.setFixedHeight(40)
        self.search_input.setObjectName("SearchInput")
        self.search_input.textChanged.connect(self.on_search)

        self.status_filter = QComboBox()
        self.status_filter.setObjectName("StatusFilter")
        self.status_filter.setFixedHeight(40)
        self.status_filter.setMinimumWidth(180)
        self.status_filter.addItems([
            "Tous les statuts",
            "Attente consultation",
            "Attente rendez-vous",
            "En consultation",
            "Examen en cours",
            "Accueil"
        ])
        self.status_filter.currentTextChanged.connect(self.on_filter_change)

        self.btn_new_visit = QPushButton("  Nouvelle visite")
        self.btn_new_visit.setObjectName("NewVisitButton")
        self.btn_new_visit.setIcon(qta.icon("fa5s.plus-circle", color="white"))
        self.btn_new_visit.setFixedHeight(40)
        self.btn_new_visit.setMinimumWidth(160)
        self.btn_new_visit.setCursor(Qt.PointingHandCursor)

        search_bar.addWidget(self.search_input, 3)
        search_bar.addWidget(self.status_filter, 1)
        search_bar.addWidget(self.btn_new_visit)

        layout.addLayout(search_bar)

        # Table : 7 colonnes
        self.table = QTableWidget(0, 7)
        self.table.setObjectName("VisitsTable")
        self.table.setHorizontalHeaderLabels([
            "Priorité", "Patient", "Type de visite",
            "Statut patient", "Durée", "Heure", "Actions"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Priorité
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Patient
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Type
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Statut
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Durée
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Heure
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Actions

        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        layout.addWidget(self.table)

        # Footer : Pagination compacte
        footer = QHBoxLayout()
        footer.setSpacing(8)
        footer.setContentsMargins(0, 4, 0, 0)

        c = theme_manager.colors()

        self.btn_prev = QPushButton()
        self.btn_prev.setIcon(qta.icon("fa5s.chevron-left", color=c['text_primary']))
        self.btn_prev.setObjectName("PaginationButton")
        self.btn_prev.setFixedSize(28, 28)
        self.btn_prev.clicked.connect(self.prev_page)

        self.page_buttons = []
        for i in range(1, 4):
            btn = QPushButton(str(i))
            btn.setObjectName("PageButton")
            btn.setFixedSize(28, 28)
            btn.setProperty("page", i)
            btn.clicked.connect(lambda checked, p=i: self.go_to_page(p))
            self.page_buttons.append(btn)

        self.btn_next = QPushButton()
        self.btn_next.setIcon(qta.icon("fa5s.chevron-right", color=c['text_primary']))
        self.btn_next.setObjectName("PaginationButton")
        self.btn_next.setFixedSize(28, 28)
        self.btn_next.clicked.connect(self.next_page)

        footer.addStretch()
        footer.addWidget(self.btn_prev)
        for btn in self.page_buttons:
            footer.addWidget(btn)
        footer.addWidget(self.btn_next)
        footer.addStretch()

        layout.addLayout(footer)

    # ── Données ──────────────────────────────────────────────────────────────

    def load_visits(self, visits):
        self._all_visits_original = list(visits)
        self.all_visits = list(visits)
        self.total_items = len(visits)
        self.current_page = 1
        self.update_table()

    def update_table(self):
        self.table.setRowCount(0)

        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, self.total_items)
        page_visits = self.all_visits[start_idx:end_idx]

        for visit in page_visits:
            self._add_visit_row(visit)

        self._update_pagination()

    def _add_visit_row(self, visit):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 60)

        # Col 0 — Priorité
        self.table.setCellWidget(row, 0, self._create_priority_badge(visit.get_urgent()))

        # Col 1 — Patient (nom + téléphone sur deux lignes)
        nom = f"{getattr(visit, 'nom_patient', '')} {getattr(visit, 'prenom_patient', '')}".strip()
        tel = getattr(visit, 'tel_patient', '')
        patient_text = f"{nom}\n{tel}" if tel else nom
        patient_item = QTableWidgetItem(patient_text)
        patient_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setItem(row, 1, patient_item)

        # Col 2 — Type de visite
        type_item = QTableWidgetItem(visit.get_type_visite())
        type_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.table.setItem(row, 2, type_item)

        # Col 3 — Statut patient
        self.table.setCellWidget(row, 3, self._create_status_badge(visit.get_statut_patient()))

        # Col 4 — Durée : valeur brute uniquement (ex. "45 min" ou "1h 10min")
        duree = self.ctrl.obtenir_temps_ecoule(visit.get_code_visite())
        duree_item = QTableWidgetItem(duree)
        duree_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        c = theme_manager.colors()
        # Rouge si dépasse 1h, orange sinon
        duree_item.setForeground(
            QColor(c['danger']) if "h" in duree else QColor(c['warning'])
        )
        self.table.setItem(row, 4, duree_item)

        # Col 5 — Heure
        heure = (visit.get_date_visite().strftime("%H:%M")
                 if hasattr(visit.get_date_visite(), 'strftime') else "—")
        heure_item = QTableWidgetItem(heure)
        heure_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.table.setItem(row, 5, heure_item)

        # Col 6 — Actions
        self.table.setCellWidget(row, 6, self._create_actions_buttons(visit))

    # ── Widgets cellules ─────────────────────────────────────────────────────

    def _create_priority_badge(self, urgent):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignCenter)

        c = theme_manager.colors()
        if urgent == "Oui":
            icon_label = QLabel()
            icon_label.setPixmap(qta.icon("fa5s.exclamation-circle", color=c['danger']).pixmap(20, 20))
            icon_label.setToolTip("URGENT")
            layout.addWidget(icon_label)
        else:
            icon_label = QLabel()
            icon_label.setPixmap(qta.icon("fa5s.star", color=c['warning']).pixmap(20, 20))
            icon_label.setToolTip("Normal")
            layout.addWidget(icon_label)

        return widget

    def _create_status_badge(self, status):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignCenter)

        c = theme_manager.colors()
        status_colors = {
            'Attente consultation':  (c['warning'],   c['warning_bg']),
            'Attente rendez-vous':   (c['warning'],   c['warning_bg']),
            'En consultation':       (c['info'],      c['info_bg']),
            'Examen en cours':       (c['accent'],    c['accent_light']),
            'Accueil':               (c['success'],   c['success_bg']),
        }
        text_color, bg_color = status_colors.get(status, (c['text_secondary'], c['hover']))

        badge = QLabel(status or "—")
        badge.setAlignment(Qt.AlignCenter)
        badge.setWordWrap(False)
        badge.setStyleSheet(f"""
            background: {bg_color};
            color: {text_color};
            border-radius: 12px;
            padding: 6px 14px;
            font-size: 11px;
            font-weight: 600;
        """)
        layout.addWidget(badge)
        return widget

    def _create_actions_buttons(self, visit):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        c = theme_manager.colors()

        btn_view = QPushButton()
        btn_view.setIcon(qta.icon("fa5s.eye", color=c['info']))
        btn_view.setFixedSize(32, 32)
        btn_view.setObjectName("ActionButton")
        btn_view.setCursor(Qt.PointingHandCursor)
        btn_view.setToolTip("Voir les détails")
        btn_view.clicked.connect(lambda: self.view_clicked.emit(visit))

        btn_menu = QPushButton()
        btn_menu.setIcon(qta.icon("fa5s.ellipsis-v", color=c['text_secondary']))
        btn_menu.setFixedSize(32, 32)
        btn_menu.setObjectName("ActionButton")
        btn_menu.setCursor(Qt.PointingHandCursor)
        btn_menu.setToolTip("Plus d'options")

        layout.addWidget(btn_view)
        layout.addWidget(btn_menu)
        return widget

    # ── Pagination ───────────────────────────────────────────────────────────

    def _update_pagination(self):
        for i, btn in enumerate(self.page_buttons, 1):
            btn.setProperty("active", i == self.current_page)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _apply_filters(self):
        """Applique la recherche et le filtre statut sur la liste originale."""
        if not hasattr(self, '_all_visits_original'):
            return
        text = self.search_input.text().strip().lower()
        status = self.status_filter.currentText()

        result = self._all_visits_original

        if text:
            result = [
                v for v in result
                if text in f"{getattr(v, 'nom_patient', '')} {getattr(v, 'prenom_patient', '')}".lower()
                or text in getattr(v, 'tel_patient', '').lower()
            ]

        if status != "Tous les statuts":
            result = [v for v in result if v.get_statut_patient() == status]

        self.all_visits = result
        self.total_items = len(result)
        self.current_page = 1
        self.update_table()

    def on_search(self, text):
        self._apply_filters()

    def on_filter_change(self, status):
        self._apply_filters()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_table()

    def next_page(self):
        total_pages = (self.total_items + self.items_per_page - 1) // self.items_per_page
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_table()

    def go_to_page(self, page):
        self.current_page = page
        self.update_table()

    # ── Thème ────────────────────────────────────────────────────────────────

    def apply_theme(self):
        c = theme_manager.colors()
        # Rafraîchir les cell-widgets existants avec les nouvelles couleurs
        if self.all_visits:
            self.update_table()
        self.setStyleSheet(f"""
            QLineEdit#SearchInput {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 0 15px;
                font-size: 13px;
                color: {c['text_primary']};
            }}
            QLineEdit#SearchInput:focus {{
                border: 2px solid {c['primary']};
            }}
            QComboBox#StatusFilter {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 0 15px;
                color: {c['text_primary']};
            }}
            QPushButton#NewVisitButton {{
                background: {c['primary']};
                color: {c['text_inverse']};
                border: none;
                border-radius: 10px;
                font-weight: 700;
                font-size: 13px;
            }}
            QPushButton#NewVisitButton:hover {{
                background: {c['primary_hover']};
            }}
            QLabel#SectionTitle {{
                color: {c['text_primary']};
                background: transparent;
                border: none;
            }}
            QTableWidget#VisitsTable {{
                background: {c['bg_table']};
                border: none;
                gridline-color: {c['border_light']};
            }}
            QTableWidget#VisitsTable::item {{
                padding: 8px;
                color: {c['text_primary']};
            }}
            QTableWidget#VisitsTable::item:selected {{
                background: {c['primary_light']};
            }}
            QHeaderView::section {{
                background: {c['bg_main']};
                color: {c['text_secondary']};
                font-weight: 700;
                font-size: 11px;
                padding: 10px;
                border: none;
                border-bottom: 2px solid {c['border']};
            }}
            QPushButton#ActionButton {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
            }}
            QPushButton#ActionButton:hover {{
                background: {c['primary_light']};
                border: 1px solid {c['primary']};
            }}
            QLabel#InfoLabel {{
                color: {c['text_muted']};
                font-size: 12px;
                background: transparent;
                border: none;
            }}
            QPushButton#PaginationButton, QPushButton#PageButton {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                color: {c['text_primary']};
                font-weight: 600;
            }}
            QPushButton#PageButton[active="true"] {{
                background: {c['primary']};
                color: {c['text_inverse']};
                border: 1px solid {c['primary']};
            }}
            QPushButton#PaginationButton:hover, QPushButton#PageButton:hover {{
                background: {c['primary_light']};
            }}
            QLabel#DotsLabel {{
                color: {c['text_muted']};
                background: transparent;
                border: none;
            }}
        """)