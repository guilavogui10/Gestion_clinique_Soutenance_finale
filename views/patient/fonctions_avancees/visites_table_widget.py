"""
Widget tableau des visites d'un patient
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                                QTableWidgetItem, QPushButton, QLabel, QHeaderView,
                                QFrame, QLineEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class VisitesTableWidget(QWidget):
    """Tableau affichant les visites d'un patient"""
    
    # Signaux
    visite_clicked = Signal(dict)  # Émet la visite sélectionnée
    
    def __init__(self, controleur_visite, parent=None):
        super().__init__(parent)
        self.controleur = controleur_visite
        self.visites = []
        self._init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Barre de recherche
        search_bar = self._create_search_bar()
        layout.addWidget(search_bar)
        
        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Code Visite", "Date", "Motif", "Statut", "Session", "Action"
        ])
        
        # Configuration du tableau (identique au tableau patients)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        self.table.setMouseTracking(True)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        
        # Ajuster les colonnes (même logique que le tableau patients)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)         # Code Visite
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(2, QHeaderView.Stretch)       # Motif
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Statut
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Session
        header.setSectionResizeMode(5, QHeaderView.Fixed)         # Action
        self.table.setColumnWidth(0, 120)  # Code Visite
        self.table.setColumnWidth(5, 130)  # Action
        
        layout.addWidget(self.table)
        
        self.apply_theme()
    
    def _create_search_bar(self):
        """Crée la barre de recherche"""
        frame = QFrame()
        frame.setObjectName("SearchBar")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Label
        label = QLabel("Visites du patient")
        label.setObjectName("SearchLabel")
        layout.addWidget(label)
        
        layout.addStretch()
        
        # Champ de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher une visite...")
        self.search_input.setFixedWidth(250)
        self.search_input.setFixedHeight(36)
        self.search_input.textChanged.connect(self._filter_table)
        layout.addWidget(self.search_input)
        
        return frame
    
    def charger_visites(self, code_patient):
        """Charge les visites d'un patient"""
        try:
            # Récupérer les visites depuis le contrôleur
            self.visites = self.controleur.lister_visites_patient(code_patient)
            self._populate_table()
            
            # Afficher un message si aucune visite
            if not self.visites or len(self.visites) == 0:
                from views.shared.message_box import CustomMessageBox
                CustomMessageBox(
                    "Information",
                    f"Aucune visite trouvée pour ce patient.\n\n"
                    f"Le patient n'a pas encore effectué de visite.",
                    is_success=False,
                    parent=self
                ).exec()
        except Exception as e:
            from views.shared.message_box import CustomMessageBox
            print(f"Erreur chargement visites: {e}")
            self.visites = []
            self.table.setRowCount(0)
            CustomMessageBox(
                "Erreur",
                f"Erreur lors du chargement des visites:\n{str(e)}",
                is_success=False,
                parent=self
            ).exec()
    
    def _populate_table(self):
        """Remplit le tableau avec les visites"""
        self.table.setRowCount(0)
        
        for visite in self.visites:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 66)  # Même hauteur que le tableau patients
            
            # Code visite
            self.table.setItem(row, 0, QTableWidgetItem(visite.get('code_visite', 'N/A')))
            
            # Date
            date_visite = visite.get('date_visite') or visite.get('date')
            if date_visite and hasattr(date_visite, 'strftime'):
                date_visite = date_visite.strftime('%d/%m/%Y %H:%M')
            elif date_visite:
                date_visite = str(date_visite)
            else:
                date_visite = 'N/A'
            self.table.setItem(row, 1, QTableWidgetItem(date_visite))
            
            # Motif (type_visite)
            motif = visite.get('type_visite') or visite.get('motif', 'N/A')
            self.table.setItem(row, 2, QTableWidgetItem(motif))
            
            # Statut
            statut = visite.get('statut_visite') or visite.get('statut', 'N/A')
            item_statut = QTableWidgetItem(statut)
            c = theme_manager.colors()
            if statut.lower() in ['terminée', 'terminee']:
                item_statut.setForeground(QColor(c['success']))
            elif statut.lower() in ['en cours', 'en_cours']:
                item_statut.setForeground(QColor(c['info']))
            self.table.setItem(row, 3, item_statut)
            
            # Session
            session = visite.get('code_session') or visite.get('nom_session', 'N/A')
            self.table.setItem(row, 4, QTableWidgetItem(session))
            
            # Bouton Voir Info - Utiliser setCellWidget comme dans le tableau patients
            self.table.setCellWidget(row, 5, self._create_action_button(visite))
    
    def _create_action_button(self, visite):
        """Crée le bouton d'action centré (même style que le tableau patients)"""
        c = theme_manager.colors()
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)
        
        btn_voir = QPushButton("  Voir Info")
        btn_voir.setIcon(qta.icon("fa5s.eye", color="white"))
        btn_voir.setObjectName("BtnVoir")
        btn_voir.setCursor(Qt.PointingHandCursor)
        btn_voir.setFixedSize(100, 32)
        btn_voir.clicked.connect(lambda checked, v=visite: self.visite_clicked.emit(v))
        
        layout.addWidget(btn_voir)
        
        return widget
    
    def _filter_table(self, text):
        """Filtre le tableau selon le texte de recherche"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount() - 1):  # Exclure la colonne Action
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
    
    def apply_theme(self):
        """Applique le thème (identique au tableau patients)"""
        c = theme_manager.colors()

        # Repopuler les lignes pour rafraîchir les cell-widgets (boutons colorés)
        if self.visites:
            self._populate_table()

        self.setStyleSheet(f"""
            QFrame#SearchBar {{
                background: {c['bg_card']};
                border: 1.5px solid {c['border_light']};
                border-radius: 10px;
            }}
            
            QLabel#SearchLabel {{
                font-size: 15px;
                font-weight: 600;
                color: {c['text_primary']};
                background: transparent;
                border: none;
            }}
            
            QLineEdit {{
                background: {c['bg_input']};
                border: 1.5px solid {c['border']};
                border-radius: 8px;
                padding: 0 12px;
                font-size: 12px;
                color: {c['text_primary']};
            }}
            
            QLineEdit:focus {{
                border-color: {c['primary']};
                background: {c['bg_card']};
            }}
            
            QTableWidget {{
                background: {c['bg_table']};
                border: 1.5px solid {c['border_light']};
                border-radius: 10px;
                gridline-color: transparent;
                color: {c['text_primary']};
                selection-background-color: transparent;
            }}
            
            QTableWidget::item {{
                padding: 8px;
                border: none;
                border-bottom: 1px solid {c['border_light']};
            }}
            
            QTableWidget::item:selected {{
                background: {c['primary']}20;
                color: {c['text_primary']};
            }}
            
            QHeaderView::section {{
                background: {c['table_header_bg']};
                color: {c['text_secondary']};
                padding: 10px;
                border: none;
                border-bottom: 1px solid {c['border_light']};
                font-weight: 700;
                font-size: 11px;
            }}
            
            QPushButton#BtnVoir {{
                background: {c['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            
            QPushButton#BtnVoir:hover {{
                background: {c['primary_hover']};
            }}
        """)
