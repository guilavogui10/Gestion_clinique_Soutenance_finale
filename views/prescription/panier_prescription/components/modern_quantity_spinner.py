"""
Composant ModernQuantitySpinner - Sélecteur de quantité moderne style e-commerce.
Responsabilité : Sélection intuitive de quantité avec boutons +/- et animations.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtGui import QFont
from views.shared.theme_manager import theme_manager


class ModernQuantitySpinner(QWidget):
    """
    Sélecteur de quantité moderne avec boutons +/- style e-commerce.
    Pattern : Composite Widget avec signaux personnalisés.
    """
    
    # Signal émis quand la quantité change
    valueChanged = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 1
        self._min_value = 1
        self._max_value = 9999
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialise l'interface du spinner."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container avec bordure arrondie
        _c = theme_manager.colors()
        self.setStyleSheet(f"""
            QWidget {{
                background: {_c['bg_input']};
                border: 2px solid {_c['border']};
                border-radius: 10px;
            }}
        """)
        self.setFixedHeight(44)
        self.setMinimumWidth(140)
        
        # Bouton Moins (-)
        self.btn_minus = self._create_button("fa5s.minus", theme_manager.colors()['danger'])
        self.btn_minus.clicked.connect(self._decrement)
        
        # Label affichage valeur
        self.lbl_value = QLabel(str(self._value))
        self.lbl_value.setAlignment(Qt.AlignCenter)
        _c = theme_manager.colors()
        self.lbl_value.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {_c['text_primary']};
                background: transparent;
                border: none;
                padding: 0px 15px;
            }}
        """)
        self.lbl_value.setMinimumWidth(50)
        
        # Bouton Plus (+)
        self.btn_plus = self._create_button("fa5s.plus", theme_manager.colors()['primary'])
        self.btn_plus.clicked.connect(self._increment)
        
        layout.addWidget(self.btn_minus)
        layout.addWidget(self.lbl_value, 1)
        layout.addWidget(self.btn_plus)
    
    def _create_button(self, icon_name: str, color: str) -> QPushButton:
        """Crée un bouton stylisé avec icône."""
        btn = QPushButton(qta.icon(icon_name, color=color), "")
        btn.setFixedSize(44, 44)
        btn.setCursor(Qt.PointingHandCursor)
        _c = theme_manager.colors()
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background: {_c['hover']};
            }}
            QPushButton:pressed {{
                background: {_c['border_light']};
            }}
        """)
        return btn
    
    def _increment(self):
        """Incrémente la valeur avec animation."""
        if self._value < self._max_value:
            self._value += 1
            self._update_display()
            self.valueChanged.emit(self._value)
            self._animate_value()
    
    def _decrement(self):
        """Décrémente la valeur avec animation."""
        if self._value > self._min_value:
            self._value -= 1
            self._update_display()
            self.valueChanged.emit(self._value)
            self._animate_value()
    
    def _update_display(self):
        """Met à jour l'affichage de la valeur."""
        self.lbl_value.setText(str(self._value))
        
        # Désactiver le bouton moins si valeur minimale
        self.btn_minus.setEnabled(self._value > self._min_value)
        
        # Désactiver le bouton plus si valeur maximale
        self.btn_plus.setEnabled(self._value < self._max_value)
    
    def _animate_value(self):
        """Animation subtile lors du changement de valeur."""
        # Animation de scale (zoom léger)
        font = self.lbl_value.font()
        original_size = font.pointSize()
        
        # Augmenter temporairement la taille
        font.setPointSize(original_size + 2)
        self.lbl_value.setFont(font)
        
        # Revenir à la taille normale après 100ms
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self._reset_font_size(original_size))
    
    def _reset_font_size(self, size: int):
        """Réinitialise la taille de la police."""
        font = self.lbl_value.font()
        font.setPointSize(size)
        self.lbl_value.setFont(font)
    
    # =========================================================================
    # API PUBLIQUE
    # =========================================================================
    
    def value(self) -> int:
        """Retourne la valeur actuelle."""
        return self._value
    
    def setValue(self, value: int):
        """Définit la valeur."""
        if self._min_value <= value <= self._max_value:
            self._value = value
            self._update_display()
    
    def setMinimum(self, min_value: int):
        """Définit la valeur minimale."""
        self._min_value = min_value
        if self._value < min_value:
            self.setValue(min_value)
    
    def setMaximum(self, max_value: int):
        """Définit la valeur maximale."""
        self._max_value = max_value
        if self._value > max_value:
            self.setValue(max_value)
    
    def clear(self):
        """Réinitialise à la valeur minimale."""
        self.setValue(self._min_value)
    
    def text(self) -> str:
        """Retourne la valeur sous forme de texte (compatibilité QLineEdit)."""
        return str(self._value)
    
    def setEnabled(self, enabled: bool):
        """Active/désactive le widget."""
        super().setEnabled(enabled)
        self.btn_minus.setEnabled(enabled and self._value > self._min_value)
        self.btn_plus.setEnabled(enabled and self._value < self._max_value)
        
        # Style visuel pour l'état désactivé
        _c = theme_manager.colors()
        if not enabled:
            super().setStyleSheet(f"""
                QWidget {{
                    background: {_c['bg_input']};
                    border: 2px solid {_c['border']};
                    border-radius: 10px;
                }}
            """)
            self.lbl_value.setStyleSheet(f"""
                QLabel {{
                    font-size: 16px;
                    font-weight: bold;
                    color: {_c['text_muted']};
                    background: transparent;
                    border: none;
                    padding: 0px 15px;
                }}
            """)
        else:
            super().setStyleSheet(f"""
                QWidget {{
                    background: {_c['bg_input']};
                    border: 2px solid {_c['border']};
                    border-radius: 10px;
                }}
            """)
            self.lbl_value.setStyleSheet(f"""
                QLabel {{
                    font-size: 16px;
                    font-weight: bold;
                    color: {_c['text_primary']};
                    background: transparent;
                    border: none;
                    padding: 0px 15px;
                }}
            """)
