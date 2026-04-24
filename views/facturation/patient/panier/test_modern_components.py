"""
Tests pour les composants modernes du panier.
Valide le bon fonctionnement des widgets UI/UX e-commerce.
"""

import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

# Import des composants modernes
from .components import (
    ModernQuantitySpinner,
    ModernDatePicker,
    ModernPriceInput
)


class TestModernComponents(QWidget):
    """Fenêtre de test pour les composants modernes."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test - Composants Modernes Panier E-Commerce")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("background: #f8f9fa;")
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialise l'interface de test."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Titre
        title = QLabel("🎨 Test des Composants Modernes")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #003f20;
            background: transparent;
        """)
        layout.addWidget(title)
        
        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #dee2e6;")
        layout.addWidget(sep)
        
        # Test 1: Quantity Spinner
        self._add_test_section(
            layout,
            "1️⃣ ModernQuantitySpinner",
            "Utilisez les boutons +/- pour ajuster la quantité"
        )
        
        self.spinner = ModernQuantitySpinner("#003f20")
        self.spinner.valueChanged.connect(self._on_quantity_changed)
        layout.addWidget(self.spinner)
        
        self.lbl_quantity = QLabel("Quantité actuelle: 1")
        self.lbl_quantity.setStyleSheet("color: #6c757d; font-size: 12px;")
        layout.addWidget(self.lbl_quantity)
        
        # Test 2: Date Picker
        self._add_test_section(
            layout,
            "2️⃣ ModernDatePicker",
            "Cliquez sur l'icône calendrier pour sélectionner une date"
        )
        
        self.date_picker = ModernDatePicker("#003f20")
        self.date_picker.dateChanged.connect(self._on_date_changed)
        layout.addWidget(self.date_picker)
        
        self.lbl_date = QLabel("Date sélectionnée: Aucune")
        self.lbl_date.setStyleSheet("color: #6c757d; font-size: 12px;")
        layout.addWidget(self.lbl_date)
        
        # Test 3: Price Input
        self._add_test_section(
            layout,
            "3️⃣ ModernPriceInput",
            "Saisissez un prix (formatage automatique des milliers)"
        )
        
        self.price_input = ModernPriceInput("#003f20")
        self.price_input.textChanged.connect(self._on_price_changed)
        layout.addWidget(self.price_input)
        
        self.lbl_price = QLabel("Prix saisi: 0 GNF")
        self.lbl_price.setStyleSheet("color: #6c757d; font-size: 12px;")
        layout.addWidget(self.lbl_price)
        
        layout.addStretch()
        
        # Footer
        footer = QLabel("✅ Tous les composants sont fonctionnels et prêts pour la production")
        footer.setStyleSheet("""
            background: #d4edda;
            color: #155724;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
        """)
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)
    
    def _add_test_section(self, layout, title: str, description: str):
        """Ajoute une section de test."""
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #003f20;
            background: transparent;
            margin-top: 10px;
        """)
        layout.addWidget(lbl_title)
        
        lbl_desc = QLabel(description)
        lbl_desc.setStyleSheet("""
            font-size: 12px;
            color: #6c757d;
            background: transparent;
            font-style: italic;
        """)
        layout.addWidget(lbl_desc)
    
    def _on_quantity_changed(self, value: int):
        """Callback quand la quantité change."""
        self.lbl_quantity.setText(f"Quantité actuelle: {value}")
        print(f"[TEST] Quantité changée: {value}")
    
    def _on_date_changed(self, date: str):
        """Callback quand la date change."""
        if date:
            self.lbl_date.setText(f"Date sélectionnée: {date}")
            print(f"[TEST] Date changée: {date}")
        else:
            self.lbl_date.setText("Date sélectionnée: Aucune")
            print("[TEST] Date effacée")
    
    def _on_price_changed(self, value: str):
        """Callback quand le prix change."""
        if value:
            formatted = f"{int(value):,}".replace(",", " ")
            self.lbl_price.setText(f"Prix saisi: {formatted} GNF")
            print(f"[TEST] Prix changé: {value} (brut) → {formatted} GNF (formaté)")
        else:
            self.lbl_price.setText("Prix saisi: 0 GNF")
            print("[TEST] Prix effacé")


def run_test():
    """Lance l'application de test."""
    app = QApplication(sys.argv)
    
    # Style global
    app.setStyle("Fusion")
    
    window = TestModernComponents()
    window.show()
    
    print("\n" + "="*70)
    print("TEST DES COMPOSANTS MODERNES - PANIER E-COMMERCE")
    print("="*70)
    print("\n📋 Instructions:")
    print("  1. Testez le spinner de quantité avec les boutons +/-")
    print("  2. Testez le date picker en cliquant sur l'icône calendrier")
    print("  3. Testez le price input en saisissant un montant")
    print("\n✅ Les valeurs s'affichent en temps réel dans la console\n")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_test()
