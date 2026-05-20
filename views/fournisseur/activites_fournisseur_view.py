"""
Vue activités fournisseur - affichage intégré dans l'onglet
"""
import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit
)
from views.shared.theme_manager import theme_manager


class ActivitesFournisseurView(QWidget):
    """
    Vue pour afficher les activités d'un fournisseur sélectionné.
    Affiche les statistiques et la liste des produits fournis.
    """

    def __init__(self, controleur, code_session: str, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.code_session = code_session
        self.fournisseur_actuel = None
        
        self._init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 12, 20, 12)
        main_layout.setSpacing(12)

        # Header avec sélection fournisseur
        self._setup_header(main_layout)

        # Stats cards
        self._setup_stats_cards(main_layout)

        # Table produits
        self._setup_table(main_layout)

        # Info dernière commande
        self._setup_last_order_info(main_layout)

    def _setup_header(self, parent_layout):
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)

        # Icône + titre
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(24, 24)
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        self._header_icon = icon_lbl

        title_lbl = QLabel("Activités du fournisseur")
        title_lbl.setObjectName("HeaderTitle")
        self._header_title = title_lbl

        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        # Combo sélection fournisseur
        self.combo_fournisseur = QComboBox()
        self.combo_fournisseur.setObjectName("FournisseurCombo")
        self.combo_fournisseur.setFixedHeight(40)
        self.combo_fournisseur.setMinimumWidth(300)
        self.combo_fournisseur.addItem("-- Sélectionner un fournisseur --", None)
        self.combo_fournisseur.currentIndexChanged.connect(self._on_fournisseur_changed)
        header_layout.addWidget(self.combo_fournisseur)

        parent_layout.addWidget(header_frame)

    def _setup_stats_cards(self, parent_layout):
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_produits = self._create_stat_card("Produits", "0", "fa5s.boxes")
        self.card_quantite = self._create_stat_card("Quantité totale", "0", "fa5s.balance-scale")
        self.card_derniere = self._create_stat_card("Dernière quantité", "0", "fa5s.history")

        stats_layout.addWidget(self.card_produits)
        stats_layout.addWidget(self.card_quantite)
        stats_layout.addWidget(self.card_derniere)

        parent_layout.addLayout(stats_layout)

    def _create_stat_card(self, title, value, icon_name):
        c = theme_manager.colors()
        card = QFrame()
        card.setObjectName("StatCard")
        card.setFixedHeight(100)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Header avec icône
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(18, 18)
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        
        title_lbl = QLabel(title)
        title_lbl.setObjectName("StatTitle")
        
        header.addWidget(icon_lbl)
        header.addSpacing(6)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        # Valeur
        value_lbl = QLabel(value)
        value_lbl.setObjectName("StatValue")
        value_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_lbl)
        layout.addStretch()

        # Stocker les références
        card._icon_lbl = icon_lbl
        card._icon_name = icon_name
        card._value_lbl = value_lbl

        return card

    def _setup_table(self, parent_layout):
        table_frame = QFrame()
        table_frame.setObjectName("TableFrame")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(16, 12, 16, 12)
        table_layout.setSpacing(8)

        # Titre table
        title_layout = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(qta.icon("fa5s.list", color=theme_manager.colors()["primary"]).pixmap(16, 16))
        icon.setStyleSheet("border: none; background: transparent;")
        title = QLabel("Liste des produits fournis")
        title.setObjectName("TableTitle")
        title_layout.addWidget(icon)
        title_layout.addSpacing(6)
        title_layout.addWidget(title)
        title_layout.addStretch()
        table_layout.addLayout(title_layout)

        # Table
        self.table = QTableWidget(0, 2)
        self.table.setObjectName("ProductsTable")
        self.table.setHorizontalHeaderLabels(["Produit", "Quantité"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setMinimumHeight(300)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        table_layout.addWidget(self.table)
        parent_layout.addWidget(table_frame, 1)

    def _setup_last_order_info(self, parent_layout):
        self.info_frame = QFrame()
        self.info_frame.setObjectName("InfoFrame")
        info_layout = QHBoxLayout(self.info_frame)
        info_layout.setContentsMargins(16, 12, 16, 12)
        info_layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(18, 18)
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        self._info_icon = icon_lbl

        self.info_label = QLabel("Sélectionnez un fournisseur pour voir ses activités")
        self.info_label.setObjectName("InfoLabel")
        self.info_label.setWordWrap(True)

        info_layout.addWidget(icon_lbl)
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()

        parent_layout.addWidget(self.info_frame)

    def charger_fournisseurs(self):
        """Charge la liste des fournisseurs dans le combo"""
        self.combo_fournisseur.blockSignals(True)
        self.combo_fournisseur.clear()
        self.combo_fournisseur.addItem("-- Sélectionner un fournisseur --", None)

        fournisseurs = self.ctrl.get_all_fournisseurs()
        for f in fournisseurs:
            email = f.get("email_fournisseur", "")
            nom = f.get("nom_entreprise", "")
            display = f"{nom} ({email})" if nom else email
            self.combo_fournisseur.addItem(display, f)

        self.combo_fournisseur.blockSignals(False)

    def _on_fournisseur_changed(self, index):
        """Appelé quand un fournisseur est sélectionné"""
        fournisseur = self.combo_fournisseur.currentData()
        if fournisseur:
            self.afficher_activites(fournisseur)
        else:
            self._clear_display()

    def afficher_activites(self, fournisseur):
        """Affiche les activités d'un fournisseur"""
        self.fournisseur_actuel = fournisseur
        email = fournisseur.get("email_fournisseur", "")

        # Récupérer les stats
        stats = self.ctrl.get_stats_fournisseur_detail(email, self.code_session)

        # Mettre à jour les cartes
        self.card_produits._value_lbl.setText(str(stats.get("nb_produits", 0)))
        self.card_quantite._value_lbl.setText(str(stats.get("quantite_totale", 0)))
        
        dernier = stats.get("dernier_mouvement")
        last_qty = stats.get("dernier_quantite", 0)
        if dernier and (last_qty is None or last_qty == 0):
            last_qty = dernier.get("quantite_four", last_qty)
        self.card_derniere._value_lbl.setText(str(last_qty))

        # Remplir la table
        self.table.setRowCount(0)
        produits = stats.get("produits", [])
        for prod in produits:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(prod.get("nom", prod.get("code_produit", "")))))
            self.table.setItem(row, 1, QTableWidgetItem(str(prod.get("quantite", 0))))

        # Info dernière commande
        if dernier:
            text = (
                f"Dernier produit: {dernier.get('code_produit', '')}  |  "
                f"Quantité: {dernier.get('quantite_four', last_qty)}  |  "
                f"Date: {dernier.get('date_facture_four', '')}"
            )
        else:
            text = "Aucun mouvement enregistré pour ce fournisseur."
        
        self.info_label.setText(text)

    def _clear_display(self):
        """Réinitialise l'affichage"""
        self.fournisseur_actuel = None
        self.card_produits._value_lbl.setText("0")
        self.card_quantite._value_lbl.setText("0")
        self.card_derniere._value_lbl.setText("0")
        self.table.setRowCount(0)
        self.info_label.setText("Sélectionnez un fournisseur pour voir ses activités")

    def apply_theme(self):
        c = theme_manager.colors()

        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_main']};
            }}
            QFrame#HeaderFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}
            QLabel#HeaderTitle {{
                font-size: 15px;
                font-weight: 700;
                color: {c['text_primary']};
                border: none;
                background: transparent;
            }}
            QComboBox#FournisseurCombo {{
                background: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 0 12px;
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QComboBox#FournisseurCombo::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox#FournisseurCombo QAbstractItemView {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                selection-background-color: {c['primary_light']};
                selection-color: {c['primary']};
                color: {c['text_primary']};
            }}
            QFrame#StatCard {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}
            QLabel#StatTitle {{
                font-size: 11px;
                color: {c['text_secondary']};
                border: none;
                background: transparent;
            }}
            QLabel#StatValue {{
                font-size: 22px;
                font-weight: bold;
                color: {c['primary']};
                border: none;
                background: transparent;
            }}
            QFrame#TableFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}
            QLabel#TableTitle {{
                font-size: 13px;
                font-weight: 700;
                color: {c['text_primary']};
                border: none;
                background: transparent;
            }}
            QTableWidget#ProductsTable {{
                background: white;
                border: none;
                gridline-color: {c['table_gridline']};
                color: {c['text_primary']};
            }}
            QTableWidget#ProductsTable::item {{
                padding: 8px;
                border-bottom: 1px solid {c['border_light']};
            }}
            QHeaderView::section {{
                background: {c['table_header_bg']};
                color: {c['text_secondary']};
                border: none;
                border-bottom: 1px solid {c['border_light']};
                padding: 10px;
                font-size: 11px;
                font-weight: 700;
            }}
            QFrame#InfoFrame {{
                background: {c['success_bg']};
                border: 1px solid {c['border_light']};
                border-radius: 10px;
            }}
            QLabel#InfoLabel {{
                color: {c['primary']};
                font-weight: 600;
                font-size: 12px;
                border: none;
                background: transparent;
            }}
        """)

        # Mettre à jour les icônes
        if hasattr(self, '_header_icon'):
            self._header_icon.setPixmap(qta.icon("fa5s.briefcase", color=c["primary"]).pixmap(24, 24))
        
        if hasattr(self, 'card_produits'):
            for card in [self.card_produits, self.card_quantite, self.card_derniere]:
                card._icon_lbl.setPixmap(qta.icon(card._icon_name, color=c["primary"]).pixmap(18, 18))
        
        if hasattr(self, '_info_icon'):
            self._info_icon.setPixmap(qta.icon("fa5s.info-circle", color=c["primary"]).pixmap(18, 18))
