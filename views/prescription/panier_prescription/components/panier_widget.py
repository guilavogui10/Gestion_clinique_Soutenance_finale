"""
Composant Panier de Prescription - tableau avec total en bas.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView
)
from views.shared.theme_manager import theme_manager


class PanierPrescriptionWidget(QWidget):
    """
    Widget panier de prescription - tableau avec colonnes et total en bas.
    """

    ligne_supprimee_signal = Signal(str)  # émet code_prescription

    def __init__(self, prescription_ctrl=None, parent=None):
        super().__init__(parent)
        self.prescription_ctrl = prescription_ctrl
        self.lignes = []
        self.setObjectName("PanierWidget")
        self._init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Titre avec icône
        self._create_header(layout)

        # Tableau
        self._create_table(layout)

        # Total en bas
        self._create_total_footer(layout)

    def _create_header(self, layout):
        """Titre du panier avec icône"""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon("fa5s.shopping-basket", color=theme_manager.colors()['primary']).pixmap(20, 20)
        )
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        self._header_icon_lbl = icon_lbl

        title_lbl = QLabel("Panier de Prescription")
        title_lbl.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {theme_manager.colors()['text_primary']};
            border: none;
            background: transparent;
        """)
        self._header_title_lbl = title_lbl

        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        layout.addLayout(header_layout)

    def _create_table(self, layout):
        """Crée le tableau des produits"""
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Code Produit", "Désignation", "Quantité\nPrescrite", "Prix Appliqué", ""
        ])
        
        # Style du tableau
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {theme_manager.colors()['bg_table']};
                border: 1px solid {theme_manager.colors()['border']};
                border-radius: 8px;
                gridline-color: {theme_manager.colors()['border_light']};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {theme_manager.colors()['border_light']};
            }}
            QHeaderView::section {{
                background: {theme_manager.colors()['table_header_bg']};
                color: {theme_manager.colors()['text_primary']};
                font-weight: bold;
                font-size: 11px;
                padding: 10px;
                border: none;
                border-bottom: 2px solid {theme_manager.colors()['primary']};
            }}
        """)

        # Configuration des colonnes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 50)

        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.table, 1)

    def _create_total_footer(self, layout):
        """Crée le footer avec le total"""
        footer_frame = QFrame()
        footer_frame.setStyleSheet(f"""
            QFrame {{
                background: {theme_manager.colors()['bg_card']};
                border: 1px solid {theme_manager.colors()['border']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        self._footer_frame = footer_frame
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(12, 8, 12, 8)
        footer_layout.setSpacing(10)

        # Icône panier en vert
        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon("fa5s.shopping-cart", color=theme_manager.colors()['success']).pixmap(20, 20)
        )
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        self._footer_icon_lbl = icon_lbl

        # Texte total
        total_text = QLabel("Total:")
        total_text.setStyleSheet(f"""
            font-size: 13px;
            font-weight: bold;
            color: {theme_manager.colors()['text_primary']};
            border: none;
            background: transparent;
        """)
        self._footer_total_text = total_text

        # Montant total
        self.lbl_total = QLabel("0 GNF")
        self.lbl_total.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {theme_manager.colors()['success']};
            border: none;
            background: transparent;
        """)

        footer_layout.addWidget(icon_lbl)
        footer_layout.addWidget(total_text)
        footer_layout.addStretch()
        footer_layout.addWidget(self.lbl_total)

        layout.addWidget(footer_frame)

    def apply_theme(self):
        """Met à jour tous les styles avec le thème courant."""
        c = theme_manager.colors()
        self.setStyleSheet(f"QWidget#PanierWidget {{ background: {c['bg_card']}; border-radius: 12px; }}")

        if hasattr(self, '_header_icon_lbl'):
            self._header_icon_lbl.setPixmap(
                qta.icon("fa5s.shopping-basket", color=c['primary']).pixmap(20, 20)
            )
        if hasattr(self, '_header_title_lbl'):
            self._header_title_lbl.setStyleSheet(
                f"font-size: 16px; font-weight: bold; color: {c['text_primary']}; border: none; background: transparent;"
            )

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {c['bg_table']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                gridline-color: {c['border_light']};
                color: {c['text_primary']};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {c['border_light']};
            }}
            QHeaderView::section {{
                background: {c['table_header_bg']};
                color: {c['text_primary']};
                font-weight: bold;
                font-size: 11px;
                padding: 10px;
                border: none;
                border-bottom: 2px solid {c['primary']};
            }}
        """)

        if hasattr(self, '_footer_frame'):
            self._footer_frame.setStyleSheet(f"""
                QFrame {{
                    background: {c['bg_card']};
                    border: 1px solid {c['border']};
                    border-radius: 8px;
                    padding: 8px;
                }}
            """)
        if hasattr(self, '_footer_icon_lbl'):
            self._footer_icon_lbl.setPixmap(
                qta.icon("fa5s.shopping-cart", color=c['success']).pixmap(20, 20)
            )
        if hasattr(self, '_footer_total_text'):
            self._footer_total_text.setStyleSheet(
                f"font-size: 13px; font-weight: bold; color: {c['text_primary']}; border: none; background: transparent;"
            )
        self.lbl_total.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {c['success']}; border: none; background: transparent;"
        )

    def ajouter_ligne(self, form_data: dict):
        """Ajoute une ligne au tableau"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Code Produit
        code_item = QTableWidgetItem(str(form_data.get('code_produit', '')))
        code_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, code_item)

        # Désignation
        designation_item = QTableWidgetItem(str(form_data.get('designation', '')))
        self.table.setItem(row, 1, designation_item)

        # Quantité
        quantite_item = QTableWidgetItem(str(form_data.get('quantite', '')))
        quantite_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 2, quantite_item)

        # Prix
        prix = form_data.get('prix', 0)
        prix_str = f"{float(prix):.0f} GNF" if prix else "0 GNF"
        prix_item = QTableWidgetItem(prix_str)
        prix_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 3, prix_item)

        # Bouton supprimer
        btn_delete = QPushButton()
        btn_delete.setIcon(qta.icon("fa5s.times", color=theme_manager.colors()['danger']))
        btn_delete.setFixedSize(32, 32)
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {theme_manager.colors()['danger_bg']};
            }}
        """)
        btn_delete.clicked.connect(
            lambda: self._supprimer_ligne(row, form_data.get('code_prescription'))
        )
        self.table.setCellWidget(row, 4, btn_delete)

        # Stocker les données
        self.lignes.append(form_data)

    def _supprimer_ligne(self, row: int, code_prescription: str):
        """Supprime une ligne du tableau"""
        self.ligne_supprimee_signal.emit(code_prescription)

    def vider_panier(self):
        """Vide tout le panier"""
        self.table.setRowCount(0)
        self.lignes.clear()
        self.update_total(0)

    def update_total(self, total: float):
        """Met à jour le total"""
        self.lbl_total.setText(f"{total:.0f} GNF")

    def recharger_lignes(self, lignes_data: list):
        """Recharge toutes les lignes"""
        self.vider_panier()
        for ligne_data in lignes_data:
            self.ajouter_ligne(ligne_data)
