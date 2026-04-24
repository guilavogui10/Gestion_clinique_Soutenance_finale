"""
Composant ModernPriceInput - Champ de saisie de prix avec formatage automatique.
Responsabilité : Saisie intuitive de prix avec formatage des milliers et validation.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QLabel
from PySide6.QtGui import QIntValidator


class ModernPriceInput(QWidget):
    """
    Champ de saisie de prix moderne avec formatage automatique des milliers.
    Pattern : Composite Widget avec formatage en temps réel.
    """
    
    # Signal émis quand le texte change
    textChanged = Signal(str)
    
    def __init__(self, vert_principal: str = "#003f20", parent=None):
        super().__init__(parent)
        self.vert_principal = vert_principal
        self._raw_value = ""
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialise l'interface du price input."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container avec bordure arrondie
        self.setStyleSheet("""
            QWidget {
                background: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
            }
        """)
        self.setFixedHeight(44)
        
        # Icône monnaie
        icon_label = QLabel()
        icon_label.setPixmap(
            qta.icon("fa5s.coins", color=self.vert_principal).pixmap(20, 20)
        )
        icon_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                padding-left: 12px;
            }
        """)
        
        # Champ de saisie
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("0")
        self.input_field.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.input_field.setStyleSheet("""
            QLineEdit {
                font-size: 15px;
                font-weight: bold;
                color: #2c3e50;
                background: transparent;
                border: none;
                padding: 0px 10px;
            }
            QLineEdit::placeholder {
                color: #bdc3c7;
            }
        """)
        
        # Validation : seulement des chiffres
        self.input_field.textChanged.connect(self._on_text_changed)
        
        # Label devise
        currency_label = QLabel("GNF")
        currency_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: bold;
                color: {self.vert_principal};
                background: transparent;
                border: none;
                padding-right: 12px;
            }}
        """)
        
        layout.addWidget(icon_label)
        layout.addWidget(self.input_field, 1)
        layout.addWidget(currency_label)
    
    def _on_text_changed(self, text: str):
        """Callback quand le texte change - formate automatiquement."""
        # Supprimer tous les espaces pour obtenir la valeur brute
        raw_text = text.replace(" ", "")
        
        # Garder seulement les chiffres
        raw_text = ''.join(filter(str.isdigit, raw_text))
        
        if raw_text:
            # Formater avec des espaces tous les 3 chiffres
            formatted = self._format_number(raw_text)
            
            # Mettre à jour le champ sans déclencher le signal
            cursor_pos = self.input_field.cursorPosition()
            self.input_field.blockSignals(True)
            self.input_field.setText(formatted)
            self.input_field.blockSignals(False)
            
            # Ajuster la position du curseur
            # Compter les espaces avant la position du curseur
            spaces_before = formatted[:cursor_pos].count(' ')
            new_pos = min(cursor_pos + spaces_before, len(formatted))
            self.input_field.setCursorPosition(new_pos)
            
            self._raw_value = raw_text
        else:
            self._raw_value = ""
        
        # Émettre le signal avec la valeur brute
        self.textChanged.emit(self._raw_value)
    
    def _format_number(self, number_str: str) -> str:
        """Formate un nombre avec des espaces tous les 3 chiffres."""
        # Inverser la chaîne pour faciliter le formatage
        reversed_str = number_str[::-1]
        
        # Ajouter un espace tous les 3 caractères
        formatted_parts = []
        for i in range(0, len(reversed_str), 3):
            formatted_parts.append(reversed_str[i:i+3])
        
        # Rejoindre avec des espaces et inverser à nouveau
        formatted = ' '.join(formatted_parts)[::-1]
        
        return formatted
    
    # =========================================================================
    # API PUBLIQUE (Compatibilité QLineEdit)
    # =========================================================================
    
    def text(self) -> str:
        """Retourne la valeur brute (sans espaces)."""
        return self._raw_value
    
    def setText(self, text: str):
        """Définit le texte (sera formaté automatiquement)."""
        # Supprimer les espaces et garder seulement les chiffres
        raw_text = ''.join(filter(str.isdigit, text.replace(" ", "")))
        
        if raw_text:
            formatted = self._format_number(raw_text)
            self.input_field.setText(formatted)
            self._raw_value = raw_text
        else:
            self.input_field.clear()
            self._raw_value = ""
    
    def clear(self):
        """Efface le champ."""
        self.input_field.clear()
        self._raw_value = ""
    
    def setPlaceholderText(self, text: str):
        """Définit le texte placeholder."""
        self.input_field.setPlaceholderText(text)
    
    def setEnabled(self, enabled: bool):
        """Active/désactive le widget."""
        super().setEnabled(enabled)
        self.input_field.setEnabled(enabled)
        
        # Style visuel pour l'état désactivé
        if not enabled:
            self.setStyleSheet("""
                QWidget {
                    background: #f5f5f5;
                    border: 2px solid #e0e0e0;
                    border-radius: 10px;
                }
            """)
            self.input_field.setStyleSheet("""
                QLineEdit {
                    font-size: 15px;
                    font-weight: bold;
                    color: #bdc3c7;
                    background: transparent;
                    border: none;
                    padding: 0px 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background: white;
                    border: 2px solid #e0e0e0;
                    border-radius: 10px;
                }
            """)
            self.input_field.setStyleSheet("""
                QLineEdit {
                    font-size: 15px;
                    font-weight: bold;
                    color: #2c3e50;
                    background: transparent;
                    border: none;
                    padding: 0px 10px;
                }
                QLineEdit::placeholder {
                    color: #bdc3c7;
                }
            """)
    
    def setStyleSheet(self, style: str):
        """Override pour gérer les styles de validation."""
        # Extraire la couleur de bordure du style
        if "border: 2px solid #27ae60" in style:
            # Style valide (vert)
            super().setStyleSheet("""
                QWidget {
                    background: #f0f8f5;
                    border: 2px solid #27ae60;
                    border-radius: 10px;
                }
            """)
        elif "border: 2px solid #e74c3c" in style:
            # Style invalide (rouge)
            super().setStyleSheet("""
                QWidget {
                    background: #fdf2f2;
                    border: 2px solid #e74c3c;
                    border-radius: 10px;
                }
            """)
        else:
            # Style normal
            super().setStyleSheet(style)
    
    def setFocus(self):
        """Donne le focus au champ de saisie."""
        self.input_field.setFocus()
