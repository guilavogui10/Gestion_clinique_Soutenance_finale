"""
Patients Table - Tableau des patients avec style consultation
Double ligne, pagination, filtres avancés
"""
from math import ceil
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                                QPushButton, QTableWidget, QHeaderView, 
                                QLabel, QComboBox, QFrame, QSizePolicy, QTableWidgetItem)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class PatientsTable(QWidget):
    """Tableau des patients avec style consultation"""
    
    # Signaux
    view_clicked = Signal(object)
    edit_clicked = Signal(object)
    visit_clicked = Signal(object)
    facture_clicked = Signal(object)  # Nouveau signal
    imprimer_dossier_clicked = Signal(object)  # Nouveau signal
    new_clicked = Signal()
    row_clicked = Signal(object)  # Signal émis quand on clique sur une ligne
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.all_patients = []
        self.filtered_patients = []
        self.current_page = 1
        self.items_per_page = 5
        self.total_items = 0
        
        # Timer pour la recherche différée
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
        self.container.setObjectName("PatientsTableCard")
        self.container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)
        
        # Mode de recherche
        self.search_mode = QComboBox()
        self.search_mode.setObjectName("StatusFilter")
        self.search_mode.setFixedHeight(40)
        self.search_mode.setMinimumWidth(140)
        self.search_mode.addItems(["Tous champs", "Par code", "Par nom", "Par téléphone"])
        self.search_mode.currentTextChanged.connect(self._on_search_mode_changed)
        
        # Champ de recherche
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Rechercher (code, nom, téléphone...)")
        self.search_input.setFixedHeight(40)
        self.search_input.addAction(
            qta.icon("fa5s.search", color=theme_manager.colors()["text_muted"]),
            QLineEdit.LeadingPosition
        )
        self.search_input.textChanged.connect(self._on_search_text_changed)
        
        # Filtre par genre
        self.genre_filter = QComboBox()
        self.genre_filter.setObjectName("StatusFilter")
        self.genre_filter.setFixedHeight(40)
        self.genre_filter.setMinimumWidth(150)
        self.genre_filter.addItems(["Tous les genres", "Homme", "Femme"])
        self.genre_filter.currentTextChanged.connect(self.apply_filters)
        
        # Bouton Nouveau
        self.btn_new = QPushButton("Nouveau Patient")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_new.setFixedHeight(40)
        self.btn_new.setMinimumWidth(165)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setIcon(qta.icon("fa5s.plus", color="white"))
        self.btn_new.clicked.connect(self.new_clicked.emit)
        
        toolbar_layout.addWidget(self.search_mode)
        toolbar_layout.addWidget(self.search_input, 1)
        toolbar_layout.addWidget(self.genre_filter)
        toolbar_layout.addWidget(self.btn_new)
        container_layout.addLayout(toolbar_layout)
        
        # Tableau
        self.table = QTableWidget(0, 6)
        self.table.setObjectName("PatientTable")
        self.table.setHorizontalHeaderLabels([
            "Code Patient",
            "Nom & Prénom",
            "Contact",
            "Genre",
            "Profession",
            "Actions"
        ])
        # Aligner les en-têtes des colonnes texte à gauche —
        # obligatoire pour correspondre au contenu des cell widgets.
        # Les colonnes Genre (3) et Actions (5) restent centrées.
        for col in [0, 1, 2, 4]:
            item = self.table.horizontalHeaderItem(col)
            if item:
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Profession (col 4) : indentation supplémentaire pour correspondre
        # au left_margin=22 du cell widget et créer de l'espace après le badge Genre.
        profession_header = self.table.horizontalHeaderItem(4)
        if profession_header:
            profession_header.setData(Qt.UserRole, "indented")
        self.table.setHorizontalHeaderItem(4, self._make_indented_header("Profession", indent=12))

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
        
        # Connecter le signal de clic sur ligne
        self.table.cellClicked.connect(self._on_cell_clicked)
        
        # Configuration des colonnes
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Fixed)    # Code Patient - largeur fixe
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Nom & Prénom - extensible
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Contact - extensible
        header.setSectionResizeMode(3, QHeaderView.Fixed)    # Genre - largeur fixe
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Profession - extensible
        header.setSectionResizeMode(5, QHeaderView.Fixed)    # Actions - largeur fixe
        self.table.setColumnWidth(0, 120)  # Code Patient
        self.table.setColumnWidth(3, 100)  # Genre
        self.table.setColumnWidth(5, 130)  # Actions
        
        container_layout.addWidget(self.table)
        
        # Pagination
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
        pages_inner = QHBoxLayout(self.pages_widget)
        pages_inner.setContentsMargins(0, 0, 0, 0)
        pages_inner.setSpacing(5)
        
        self.page_buttons = []
        for i in range(1, 4):
            btn = QPushButton(str(i))
            btn.setObjectName("PageButton")
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setVisible(False)
            btn.clicked.connect(lambda checked=False, p=i: self.go_to_page(p))
            self.page_buttons.append(btn)
            pages_inner.addWidget(btn)
        
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_prev)
        footer_layout.addWidget(self.pages_widget)
        footer_layout.addWidget(self.btn_next)
        footer_layout.addStretch()
        
        container_layout.addLayout(footer_layout)
        outer_layout.addWidget(self.container)
    
    def load_patients(self, patients):
        """Charge la liste des patients"""
        self.all_patients = list(patients or [])
        self.filtered_patients = list(self.all_patients)
        self.current_page = 1
        self.apply_filters()
    
    def _on_search_mode_changed(self):
        """Change le placeholder selon le mode"""
        self.search_input.clear()
        placeholders = {
            "Tous champs": "Rechercher (code, nom, téléphone...)",
            "Par code": "Code patient (ex: PAT-00001)...",
            "Par nom": "Nom ou prénom du patient...",
            "Par téléphone": "Numéro de téléphone...",
        }
        self.search_input.setPlaceholderText(
            placeholders.get(self.search_mode.currentText(), "Rechercher...")
        )
    
    def _on_search_text_changed(self):
        """Déclenche la recherche avec délai"""
        mode = self.search_mode.currentText()
        if mode == "Tous champs":
            self._search_timer.stop()
            self.apply_filters()
        else:
            self._search_timer.start()
    
    def _executer_recherche(self):
        """Exécute la recherche selon le mode"""
        query = self.search_input.text().strip().lower()
        mode = self.search_mode.currentText()
        
        if not query:
            self.filtered_patients = list(self.all_patients)
            self.total_items = len(self.filtered_patients)
            self.current_page = 1
            self.update_table()
            return
        
        resultats = []
        if mode == "Par code":
            resultats = [p for p in self.all_patients if query in p.get_code_patient().lower()]
        elif mode == "Par nom":
            resultats = [
                p for p in self.all_patients
                if query in p.get_nom().lower() or query in p.get_prenom().lower()
            ]
        elif mode == "Par téléphone":
            resultats = [p for p in self.all_patients if query in (p.get_telephone() or "").lower()]
        
        # Appliquer le filtre genre
        genre_filter = self.genre_filter.currentText()
        if genre_filter != "Tous les genres":
            resultats = [p for p in resultats if p.get_genre() == genre_filter]
        
        self.filtered_patients = resultats
        self.total_items = len(resultats)
        self.current_page = 1
        self.update_table()
    
    def apply_filters(self):
        """Applique les filtres de recherche et genre"""
        query = self.search_input.text().strip().lower()
        genre_filter = self.genre_filter.currentText()
        
        filtered = []
        for patient in self.all_patients:
            # Filtre genre
            if genre_filter != "Tous les genres":
                if patient.get_genre() != genre_filter:
                    continue
            
            # Filtre recherche
            if query and not self._matches_query(patient, query):
                continue
            
            filtered.append(patient)
        
        self.filtered_patients = filtered
        self.total_items = len(filtered)
        max_page = self.total_pages()
        self.current_page = min(max(self.current_page, 1), max_page)
        self.update_table()
    
    def _matches_query(self, patient, query):
        """Vérifie si le patient correspond à la recherche"""
        values = [
            patient.get_code_patient() or "",
            patient.get_nom() or "",
            patient.get_prenom() or "",
            patient.get_telephone() or "",
            patient.get_genre() or "",
            patient.get_profession() or "",
            patient.get_adresse() or "",
        ]
        haystack = " ".join(str(v).lower() for v in values if v)
        return query in haystack
    
    def update_table(self):
        """Met à jour l'affichage du tableau"""
        self.table.setRowCount(0)
        if self.total_items > 0:
            start_idx = (self.current_page - 1) * self.items_per_page
            end_idx = min(start_idx + self.items_per_page, self.total_items)
            for patient in self.filtered_patients[start_idx:end_idx]:
                self._add_patient_row(patient)
        self._update_pagination()
    
    def _add_patient_row(self, patient):
        """Ajoute une ligne patient — tous les contenus via cell widgets pour
        garantir un alignement pixel-perfect avec les en-têtes."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 66)

        c = theme_manager.colors()

        # Col 0 — Code Patient
        self.table.setCellWidget(row, 0, self._build_double_line_widget(
            primary_text=patient.get_code_patient() or "—",
            secondary_text=None,
            primary_color=c["primary"],
            primary_weight=700,
        ))

        # Col 1 — Nom & Prénom + date de naissance
        nom_complet = f"{patient.get_nom()} {patient.get_prenom()}".strip()
        date_naissance = patient.get_naissance()
        date_str = (
            date_naissance.strftime("%d/%m/%Y")
            if hasattr(date_naissance, "strftime")
            else str(date_naissance or "")
        )
        self.table.setCellWidget(row, 1, self._build_double_line_widget(
            primary_text=nom_complet or "—",
            secondary_text=f"Né(e) le {date_str}" if date_str else None,
            secondary_icon="fa5s.birthday-cake",
        ))

        # Col 2 — Contact : téléphone + adresse
        tel = patient.get_telephone() or "Non renseigné"
        adr = patient.get_adresse() or ""
        self.table.setCellWidget(row, 2, self._build_double_line_widget(
            primary_text=tel,
            secondary_text=adr if adr else None,
            secondary_icon="fa5s.map-marker-alt",
        ))

        # Col 3 — Genre (Badge widget)
        self.table.setCellWidget(row, 3, self._create_genre_badge(patient.get_genre()))

        # Col 4 — Profession (marge gauche augmentée pour aérer après le badge Genre)
        self.table.setCellWidget(row, 4, self._build_double_line_widget(
            primary_text=patient.get_profession() or "Non renseignée",
            secondary_text=None,
            left_margin=22,
        ))

        # Col 5 — Actions
        self.table.setCellWidget(row, 5, self._create_actions_buttons(patient))
    
    def _make_indented_header(self, text, indent=12):
        """Crée un QTableWidgetItem d'en-tête avec indentation gauche via
        des espaces Unicode fine (thin space U+2009) pour simuler un padding-left
        sans delegate — seule méthode fiable en Qt pour décaler un en-tête.
        """
        # 1 thin space ≈ 3-4px selon la police ; on calcule le nombre approximatif
        thin_space = "\u2009"
        nb_spaces = round(indent / 3.5)
        item = QTableWidgetItem(thin_space * nb_spaces + text)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        return item

    def _build_double_line_widget(self, primary_text, secondary_text,
                                   primary_color=None, primary_weight=600,
                                   secondary_icon=None, left_margin=10):
        """Crée un widget avec deux lignes de texte centré verticalement.

        left_margin : marge gauche en pixels (défaut 10 = même que header padding).
        Augmenter cette valeur sur une colonne crée une séparation visuelle
        avec la colonne précédente sans toucher aux largeurs de colonnes.
        """
        c = theme_manager.colors()

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(left_margin, 0, 10, 0)
        layout.setSpacing(4)
        
        layout.addStretch()
        
        # Texte principal
        primary = QLabel(primary_text)
        primary.setWordWrap(True)
        primary.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        primary.setStyleSheet(
            f"color: {primary_color or c['text_primary']}; "
            f"font-size: 12px; font-weight: {primary_weight};"
        )
        layout.addWidget(primary)
        
        # Texte secondaire
        if secondary_text:
            secondary_row = QHBoxLayout()
            secondary_row.setContentsMargins(0, 0, 0, 0)
            secondary_row.setSpacing(6)
            
            if secondary_icon:
                icon_label = QLabel()
                icon_label.setPixmap(
                    qta.icon(secondary_icon, color=c["text_muted"]).pixmap(11, 11)
                )
                secondary_row.addWidget(icon_label, 0, Qt.AlignVCenter)
            
            secondary = QLabel(secondary_text)
            secondary.setWordWrap(True)
            secondary.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            secondary.setStyleSheet(
                f"color: {c['text_secondary']}; font-size: 11px; font-weight: 500;"
            )
            secondary_row.addWidget(secondary, 1)
            layout.addLayout(secondary_row)
        
        layout.addStretch()
        
        return container
    
    def _create_genre_badge(self, genre):
        """Crée un badge pour le genre centré"""
        c = theme_manager.colors()
        
        genre_colors = {
            "Homme": (c["info_bg"], c["info"]),
            "Femme": (c["danger_bg"], c["danger"]),
        }
        bg_color, text_color = genre_colors.get(genre, (c["hover"], c["text_secondary"]))
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignCenter)
        
        badge = QLabel(genre or "—")
        badge.setAlignment(Qt.AlignCenter)
        badge.setWordWrap(False)
        badge.setStyleSheet(f"""
            background: {bg_color};
            color: {text_color};
            border-radius: 12px;
            padding: 6px 14px;
            font-size: 11px;
            font-weight: 700;
        """)
        layout.addWidget(badge)
        
        return widget
    
    def _create_actions_buttons(self, patient):
        """Crée les boutons d'actions centrés"""
        c = theme_manager.colors()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)
        
        # Bouton Voir
        btn_view = QPushButton()
        btn_view.setFixedSize(32, 32)
        btn_view.setCursor(Qt.PointingHandCursor)
        btn_view.setIcon(qta.icon("fa5s.eye", color=c["primary"]))
        btn_view.setObjectName("ActionButton")
        btn_view.clicked.connect(lambda checked=False, p=patient: self.view_clicked.emit(p))
        layout.addWidget(btn_view)
        
        # Bouton Modifier
        btn_edit = QPushButton()
        btn_edit.setFixedSize(32, 32)
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setIcon(qta.icon("fa5s.pen", color=c["secondary"]))
        btn_edit.setObjectName("ActionButton")
        btn_edit.clicked.connect(lambda checked=False, p=patient: self.edit_clicked.emit(p))
        layout.addWidget(btn_edit)
        
        # Bouton Menu (remplace le bouton visite)
        btn_menu = QPushButton()
        btn_menu.setFixedSize(32, 32)
        btn_menu.setCursor(Qt.PointingHandCursor)
        btn_menu.setIcon(qta.icon("fa5s.ellipsis-v", color=c["success"]))
        btn_menu.setObjectName("ActionButton")
        btn_menu.clicked.connect(lambda checked=False, p=patient: self._show_patient_menu(p, btn_menu))
        layout.addWidget(btn_menu)
        
        return widget
    
    def _show_patient_menu(self, patient, button):
        """Affiche le menu déroulant pour un patient"""
        from PySide6.QtWidgets import QMenu
        
        c = theme_manager.colors()
        menu = QMenu(self)
        
        # Style du menu
        menu.setStyleSheet(f"""
            QMenu {{
                background: white;
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 8px 0;
            }}
            QMenu::item {{
                padding: 10px 20px;
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QMenu::item:selected {{
                background: {c['primary_light']};
                color: {c['primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {c['border_light']};
                margin: 4px 0;
            }}
        """)
        
        # Action Visite
        action_visite = menu.addAction(qta.icon("fa5s.walking", color=c['success']), "  Historique Visite")
        action_visite.triggered.connect(lambda: self.visit_clicked.emit(patient))
        
        menu.addSeparator()
        
        # Action Facture
        action_facture = menu.addAction(qta.icon("fa5s.file-invoice-dollar", color=c['warning']), "  Facture Patient")
        action_facture.triggered.connect(lambda: self.facture_clicked.emit(patient))
        
        # Action Imprimer dossier
        action_imprimer = menu.addAction(qta.icon("fa5s.print", color=c['danger']), "  Imprimer Dossier")
        action_imprimer.triggered.connect(lambda: self.imprimer_dossier_clicked.emit(patient))
        
        # Afficher le menu sous le bouton
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
    
    def total_pages(self):
        """Calcule le nombre total de pages"""
        if self.total_items <= 0:
            return 1
        return max(1, ceil(self.total_items / self.items_per_page))
    
    def _update_pagination(self):
        """Met à jour les boutons de pagination"""
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
        """Style des boutons de page"""
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
        """Page précédente"""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_table()
    
    def next_page(self):
        """Page suivante"""
        total_pages = self.total_pages()
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_table()
    
    def go_to_page(self, page):
        """Aller à une page spécifique"""
        self.current_page = page
        self.update_table()
    
    def apply_theme(self):
        """Applique le thème actuel"""
        c = theme_manager.colors()
        
        self.container.setStyleSheet(f"""
            QFrame#PatientsTableCard {{
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
            QTableWidget#PatientTable {{
                background: white;
                border: none;
                gridline-color: {c['table_gridline']};
                color: {c['text_primary']};
                selection-background-color: transparent;
            }}
            QTableWidget#PatientTable::item {{
                padding: 0px;
                border-bottom: 1px solid {c['border_light']};
            }}
            QHeaderView::section {{
                background: {c['table_header_bg']};
                color: {c['text_secondary']};
                border: none;
                border-bottom: 1px solid {c['border_light']};
                padding: 10px 10px 10px 10px;
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
            QPushButton#ActionButton {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
            }}
            QPushButton#ActionButton:hover {{
                background: {c['primary_light']};
                border: 1px solid {c['primary']};
            }}
        """)
        
        self.btn_prev.setIcon(qta.icon("fa5s.chevron-left", color=c["text_secondary"]))
        self.btn_next.setIcon(qta.icon("fa5s.chevron-right", color=c["text_secondary"]))
        self._update_pagination()
    
    def _on_cell_clicked(self, row, column):
        """Appelé quand on clique sur une cellule du tableau"""
        # Ignorer les clics sur la colonne Actions (colonne 5)
        if column == 5:
            return
        
        # Récupérer le patient de cette ligne
        if 0 <= row < len(self.filtered_patients):
            start_idx = (self.current_page - 1) * self.items_per_page
            patient_idx = start_idx + row
            if patient_idx < len(self.filtered_patients):
                patient = self.filtered_patients[patient_idx]
                self.row_clicked.emit(patient)