"""
Composant StockTableCard - Tableau pour afficher le stock détaillé.
Responsabilité : Afficher un tableau avec colonnes et lignes alternées.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QTableWidget, QHeaderView, QLabel, QTableWidgetItem
from PySide6.QtCore import Qt
from views.shared.theme_manager import theme_manager


class StockTableCard(QFrame):
    """
    Card avec tableau pour afficher le stock détaillé par produit.
    
    Colonnes : Désignation | Type | Quantité totale | Statut principal
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface du tableau."""
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {c['border_light']};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Titre
        title_lbl = QLabel("STOCK DÉTAILLÉ PAR PRODUIT (APERÇU)")
        title_lbl.setStyleSheet(
            f"color: {c['text_primary']}; font-weight: bold; font-size: 13px; border: none; background: transparent;"
        )
        layout.addWidget(title_lbl)
        
        # Tableau
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Désignation", "Type", "Quantité totale", "Statut principal"
        ])
        
        # Configuration des colonnes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Style du tableau
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: white;
                border: none;
                gridline-color: {c['border_light']};
            }}
            QTableWidget::item {{
                padding: 8px;
                border: none;
            }}
            QTableWidget::item:alternate {{
                background: {c['bg_card']};
            }}
            QHeaderView::section {{
                background: {c['bg_card']};
                color: {c['text_primary']};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {c['border']};
                font-weight: bold;
                font-size: 11px;
            }}
        """)
        
        layout.addWidget(self.table)
    
    def charger_produits(self, produits: list):
        """
        Charge les produits dans le tableau.
        
        Args:
            produits: Liste de dict avec 'designation', 'type', 'quantite', 'statut'
        """
        from PySide6.QtGui import QColor
        
        self.table.setRowCount(0)
        
        if not produits:
            return
        
        c = theme_manager.colors()
        
        for produit in produits:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Désignation
            self.table.setItem(row, 0, QTableWidgetItem(produit.get('designation', '')))
            
            # Type
            self.table.setItem(row, 1, QTableWidgetItem(produit.get('type', '')))
            
            # Quantité
            qte_item = QTableWidgetItem(str(produit.get('quantite', 0)))
            qte_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, qte_item)
            
            # Statut avec couleur
            statut = produit.get('statut', 'Valide')
            statut_item = QTableWidgetItem(statut)
            statut_item.setTextAlignment(Qt.AlignCenter)
            
            if statut == 'Expiré' or statut == 'Rupture':
                statut_item.setForeground(QColor(c['danger']))
            elif statut == 'À expirer' or statut == 'Stock faible':
                statut_item.setForeground(QColor(c['warning']))
            else:
                statut_item.setForeground(QColor(c['success']))
            
            self.table.setItem(row, 3, statut_item)
    
    def vider(self):
        """Vide le tableau."""
        self.table.setRowCount(0)
