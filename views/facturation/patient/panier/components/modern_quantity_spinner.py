"""
Composant ModernQuantitySpinner - Sélecteur de quantité moderne style e-commerce.
Responsabilité : Sélection intuitive de quantité avec boutons +/- et animations.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtGui import QFont
from views.shared.modal_theme import MC


class ModernQuantitySpinner(QWidget):
    """
    Sélecteur de quantité moderne avec boutons +/- style e-commerce.
    Pattern : Composite Widget avec signaux personnalisés.
    """
    
    # Signal émis quand la quantité change
    valueChanged = Signal(int)
    
    def __init__(self, vert_principal: str = None, parent=None):
        super().__init__(parent)
        from views.shared.theme_manager import theme_manager
        self.vert_principal = vert_principal or theme_manager.colors()['primary']
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
        self.setStyleSheet(f"""
            QWidget {{
                background: {MC.BG_CARD};
                border: 2px solid {MC.BORDER};
                border-radius: 10px;
            }}
        """)
        self.setFixedHeight(38)
        self.setMinimumWidth(130)
        
        # Bouton Moins (-)
        self.btn_minus = self._create_button("fa5s.minus", MC.DANGER)
        self.btn_minus.clicked.connect(self._decrement)
        
        # Label affichage valeur
        self.lbl_value = QLabel(str(self._value))
        self.lbl_value.setAlignment(Qt.AlignCenter)
        self.lbl_value.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {MC.TEXT_PRIMARY};
                background: transparent;
                border: none;
                padding: 0px 12px;
            }}
        """)
        self.lbl_value.setMinimumWidth(50)
        
        # Bouton Plus (+)
        self.btn_plus = self._create_button("fa5s.plus", self.vert_principal)
        self.btn_plus.clicked.connect(self._increment)
        
        layout.addWidget(self.btn_minus)
        layout.addWidget(self.lbl_value, 1)
        layout.addWidget(self.btn_plus)
    
    def _create_button(self, icon_name: str, color: str) -> QPushButton:
        """Crée un bouton stylisé avec icône."""
        btn = QPushButton(qta.icon(icon_name, color=color), "")
        btn.setFixedSize(38, 38)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background: {MC.BG_MAIN};
            }}
            QPushButton:pressed {{
                background: {MC.BORDER_LIGHT};
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
        
        # Vérifier que la taille est valide (> 0)
        if original_size <= 0:
            original_size = 14  # Taille par défaut
        
        # Augmenter temporairement la taille
        font.setPointSize(original_size + 2)
        self.lbl_value.setFont(font)
        
        # Revenir à la taille normale après 100ms
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self._reset_font_size(original_size))
    
    def _reset_font_size(self, size: int):
        """Réinitialise la taille de la police."""
        if size > 0:
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
        if not enabled:
            self.setStyleSheet(f"""
                QWidget {{
                    background: {MC.BG_MAIN};
                    border: 2px solid {MC.BORDER};
                    border-radius: 10px;
                }}
            """)
            self.lbl_value.setStyleSheet(f"""
                QLabel {{
                    font-size: 14px;
                    font-weight: bold;
                    color: {MC.TEXT_MUTED};
                    background: transparent;
                    border: none;
                    padding: 0px 12px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QWidget {{
                    background: {MC.BG_CARD};
                    border: 2px solid {MC.BORDER};
                    border-radius: 10px;
                }}
            """)
            self.lbl_value.setStyleSheet(f"""
                QLabel {{
                    font-size: 14px;
                    font-weight: bold;
                    color: {MC.TEXT_PRIMARY};
                    background: transparent;
                    border: none;
                    padding: 0px 12px;
                }}
            """)

    def apply_theme(self):
        """Met à jour les couleurs selon le thème actif."""
        self.vert_principal = MC.PRIMARY
        # Container
        if self.isEnabled():
            super(ModernQuantitySpinner, self).setStyleSheet(f"""
                QWidget {{
                    background: {MC.BG_CARD};
                    border: 2px solid {MC.BORDER};
                    border-radius: 10px;
                }}
            """)
        else:
            super(ModernQuantitySpinner, self).setStyleSheet(f"""
                QWidget {{
                    background: {MC.BG_MAIN};
                    border: 2px solid {MC.BORDER};
                    border-radius: 10px;
                }}
            """)
        # Boutons
        self.btn_minus.setIcon(qta.icon("fa5s.minus", color=MC.DANGER))
        self.btn_minus.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background: {MC.BG_MAIN};
            }}
            QPushButton:pressed {{
                background: {MC.BORDER_LIGHT};
            }}
        """)
        self.btn_plus.setIcon(qta.icon("fa5s.plus", color=MC.PRIMARY))
        self.btn_plus.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background: {MC.BG_MAIN};
            }}
            QPushButton:pressed {{
                background: {MC.BORDER_LIGHT};
            }}
        """)
        # Label
        txt_color = MC.TEXT_PRIMARY if self.isEnabled() else MC.TEXT_MUTED
        self.lbl_value.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {txt_color};
                background: transparent;
                border: none;
                padding: 0px 12px;
            }}
        """)
