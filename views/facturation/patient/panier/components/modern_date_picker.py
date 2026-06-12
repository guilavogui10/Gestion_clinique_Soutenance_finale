"""
Composant ModernDatePicker - Sélecteur de date moderne avec calendrier popup.
Responsabilité : Sélection intuitive de date avec calendrier visuel style e-commerce.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, Signal, QDate, QSize
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QCalendarWidget,
    QVBoxLayout, QFrame
)
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QGuiApplication
from views.shared.modal_theme import MC


class ModernDatePicker(QWidget):
    """
    Sélecteur de date moderne avec calendrier popup style e-commerce.
    Pattern : Composite Widget avec popup personnalisé.
    """
    
    # Signal émis quand la date change
    dateChanged = Signal(str)  # Format: JJ/MM/AAAA
    
    def __init__(self, vert_principal: str = None, parent=None):
        super().__init__(parent)
        from views.shared.theme_manager import theme_manager
        self.vert_principal = vert_principal or theme_manager.colors()['primary']
        self._selected_date = None
        self._calendar_popup = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialise l'interface du date picker."""
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
        
        # Icône calendrier
        self.btn_calendar = QPushButton(qta.icon("fa5s.calendar-alt", color=self.vert_principal), "")
        self.btn_calendar.setFixedSize(38, 38)
        self.btn_calendar.setCursor(Qt.PointingHandCursor)
        self.btn_calendar.setStyleSheet(f"""
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
        self.btn_calendar.clicked.connect(self._show_calendar)
        
        # Label affichage date
        self.lbl_date = QLabel("Sélectionner une date...")
        self.lbl_date.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_date.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {MC.TEXT_MUTED};
                background: transparent;
                border: none;
                padding-left: 10px;
            }}
        """)
        
        # Bouton clear (X)
        self.btn_clear = QPushButton(qta.icon("fa5s.times", color=MC.DANGER), "")
        self.btn_clear.setFixedSize(30, 30)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: {MC.DANGER_BG};
            }}
            QPushButton:pressed {{
                background: {MC.DANGER_BG};
            }}
        """)
        self.btn_clear.clicked.connect(self.clear)
        self.btn_clear.setVisible(False)  # Caché par défaut
        
        layout.addWidget(self.btn_calendar)
        layout.addWidget(self.lbl_date, 1)
        layout.addWidget(self.btn_clear)
    
    def _show_calendar(self):
        """Affiche le popup calendrier."""
        if self._calendar_popup is None:
            self._create_calendar_popup()

        # Positionner le popup (privilÃ©gier sous le widget, sinon au-dessus)
        self._calendar_popup.adjustSize()
        popup_h = self._calendar_popup.sizeHint().height()

        screen = QGuiApplication.screenAt(self.mapToGlobal(self.rect().center()))
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None

        bottom_left = self.mapToGlobal(self.rect().bottomLeft())
        top_left = self.mapToGlobal(self.rect().topLeft())

        y = bottom_left.y() + 5
        if available:
            if y + popup_h > available.bottom():
                y = top_left.y() - popup_h - 5
            if y < available.top():
                y = available.top() + 5

        self._calendar_popup.move(bottom_left.x(), y)
        self._calendar_popup.show()
        self._calendar_popup.raise_()
        self._calendar_popup.activateWindow()
    
    def _create_calendar_popup(self):
        """Crée le popup calendrier stylisé."""
        from PySide6.QtWidgets import QDialog
        
        self._calendar_popup = QDialog(self, Qt.Popup | Qt.FramelessWindowHint)
        self._calendar_popup.setStyleSheet(f"""
            QDialog {{
                background: {MC.BG_CARD};
                border: 2px solid {MC.BORDER};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self._calendar_popup)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Titre
        title = QLabel("Sélectionner la date d'expiration")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: bold;
                color: {self.vert_principal};
                background: transparent;
                border: none;
                padding: 5px;
            }}
        """)
        layout.addWidget(title)
        
        # Calendrier
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QDate.currentDate())  # Pas de dates passées
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        
        # Style moderne du calendrier
        self._style_calendar()
        
        # Connexion du signal
        self.calendar.clicked.connect(self._on_date_selected)
        
        layout.addWidget(self.calendar)
        
        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        btn_today = QPushButton(qta.icon("fa5s.calendar-day", color=self.vert_principal), " Aujourd'hui")
        btn_today.setFixedHeight(36)
        btn_today.setCursor(Qt.PointingHandCursor)
        btn_today.setStyleSheet(f"""
            QPushButton {{
                background: {MC.BG_MAIN};
                border: 1px solid {MC.BORDER};
                border-radius: 8px;
                padding: 5px 15px;
                font-size: 12px;
                color: {self.vert_principal};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {MC.BORDER_LIGHT};
            }}
        """)
        btn_today.clicked.connect(self._select_today)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setFixedHeight(36)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {MC.BG_MAIN};
                border: 1px solid {MC.BORDER};
                border-radius: 8px;
                padding: 5px 15px;
                font-size: 12px;
                color: {MC.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                background: {MC.BORDER_LIGHT};
            }}
        """)
        btn_cancel.clicked.connect(self._calendar_popup.close)
        
        btn_layout.addWidget(btn_today)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
    
    def _style_calendar(self):
        """Applique un style moderne au calendrier."""
        self.calendar.setStyleSheet(f"""
            QCalendarWidget {{
                background: {MC.BG_CARD};
                border: none;
            }}
            
            /* Navigation bar */
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background: {self.vert_principal};
                border-radius: 8px;
                padding: 5px;
            }}
            
            /* Boutons navigation */
            QCalendarWidget QToolButton {{
                color: {MC.TEXT_INVERSE};
                background: transparent;
                border: none;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
                font-weight: bold;
            }}
            QCalendarWidget QToolButton:hover {{
                background: {MC.PRIMARY_HOVER};
            }}
            QCalendarWidget QToolButton:pressed {{
                background: {MC.PRIMARY_HOVER};
            }}
            
            /* Menu mois/année */
            QCalendarWidget QMenu {{
                background: {MC.BG_CARD};
                border: 1px solid {MC.BORDER};
                border-radius: 8px;
            }}
            QCalendarWidget QSpinBox {{
                background: {MC.BG_CARD};
                color: {self.vert_principal};
                border: none;
                font-weight: bold;
            }}
            
            /* En-têtes jours */
            QCalendarWidget QWidget {{
                alternate-background-color: {MC.BG_MAIN};
            }}
            
            /* Cellules */
            QCalendarWidget QAbstractItemView {{
                selection-background-color: {self.vert_principal};
                selection-color: {MC.TEXT_INVERSE};
                border: none;
                outline: none;
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                color: {MC.TEXT_PRIMARY};
                background: {MC.BG_CARD};
            }}
            QCalendarWidget QAbstractItemView:disabled {{
                color: {MC.TEXT_MUTED};
            }}
        """)
        
        # Format pour la date sélectionnée
        selected_format = QTextCharFormat()
        selected_format.setBackground(QColor(self.vert_principal))
        selected_format.setForeground(QColor(MC.TEXT_INVERSE))
        selected_format.setFontWeight(QFont.Bold)
        
        # Format pour aujourd'hui
        today_format = QTextCharFormat()
        today_format.setBackground(QColor(MC.SUCCESS_BG))
        today_format.setForeground(QColor(self.vert_principal))
        today_format.setFontWeight(QFont.Bold)
        
        self.calendar.setDateTextFormat(QDate.currentDate(), today_format)
    
    def _select_today(self):
        """Sélectionne la date d'aujourd'hui."""
        self.calendar.setSelectedDate(QDate.currentDate())
        self._on_date_selected(QDate.currentDate())
    
    def _on_date_selected(self, date: QDate):
        """Callback quand une date est sélectionnée."""
        self._selected_date = date.toString("dd/MM/yyyy")
        self.lbl_date.setText(self._selected_date)
        self.lbl_date.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: bold;
                color: {self.vert_principal};
                background: transparent;
                border: none;
                padding-left: 10px;
            }}
        """)
        
        # Afficher le bouton clear
        self.btn_clear.setVisible(True)
        
        # Émettre le signal
        self.dateChanged.emit(self._selected_date)
        
        # Fermer le popup
        if self._calendar_popup:
            self._calendar_popup.close()
    
    # =========================================================================
    # API PUBLIQUE (Compatibilité QLineEdit)
    # =========================================================================
    
    def text(self) -> str:
        """Retourne la date sélectionnée (format JJ/MM/AAAA)."""
        return self._selected_date if self._selected_date else ""
    
    def setText(self, date_str: str):
        """Définit la date (format JJ/MM/AAAA)."""
        if date_str:
            try:
                date = QDate.fromString(date_str, "dd/MM/yyyy")
                if date.isValid():
                    self._selected_date = date_str
                    self.lbl_date.setText(date_str)
                    self.lbl_date.setStyleSheet(f"""
                        QLabel {{
                            font-size: 13px;
                            font-weight: bold;
                            color: {self.vert_principal};
                            background: transparent;
                            border: none;
                            padding-left: 10px;
                        }}
                    """)
                    self.btn_clear.setVisible(True)
            except:
                pass
    
    def clear(self):
        """Efface la date sélectionnée."""
        self._selected_date = None
        self.lbl_date.setText("Sélectionner une date...")
        self.lbl_date.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {MC.TEXT_MUTED};
                background: transparent;
                border: none;
                padding-left: 10px;
            }}
        """)
        self.btn_clear.setVisible(False)
        self.dateChanged.emit("")
    
    def setEnabled(self, enabled: bool):
        """Active/désactive le widget."""
        super().setEnabled(enabled)
        self.btn_calendar.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled)
        
        if not enabled:
            self.setStyleSheet(f"""
                QWidget {{
                    background: {MC.BG_MAIN};
                    border: 2px solid {MC.BORDER};
                    border-radius: 10px;
                }}
            """)
            self.lbl_date.setStyleSheet(f"""
                QLabel {{
                    font-size: 13px;
                    color: {MC.TEXT_MUTED};
                    background: transparent;
                    border: none;
                    padding-left: 10px;
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
    
    def setPlaceholderText(self, text: str):
        """Définit le texte placeholder (compatibilité QLineEdit)."""
        if not self._selected_date:
            self.lbl_date.setText(text)
    
    def setStyleSheet(self, style: str):
        """Override pour gérer les styles de validation."""
        if f"border: 2px solid {MC.SUCCESS}" in style:
            super().setStyleSheet(f"""
                QWidget {{
                    background: {MC.SUCCESS_BG};
                    border: 2px solid {MC.SUCCESS};
                    border-radius: 10px;
                }}
            """)
        elif f"border: 2px solid {MC.DANGER}" in style:
            super().setStyleSheet(f"""
                QWidget {{
                    background: {MC.DANGER_BG};
                    border: 2px solid {MC.DANGER};
                    border-radius: 10px;
                }}
            """)
        else:
            super().setStyleSheet(style)

    def apply_theme(self):
        """Met à jour les couleurs selon le thème actif."""
        self.vert_principal = MC.PRIMARY
        # Container
        if self.isEnabled():
            super(ModernDatePicker, self).setStyleSheet(f"""
                QWidget {{
                    background: {MC.BG_CARD};
                    border: 2px solid {MC.BORDER};
                    border-radius: 10px;
                }}
            """)
        else:
            super(ModernDatePicker, self).setStyleSheet(f"""
                QWidget {{
                    background: {MC.BG_MAIN};
                    border: 2px solid {MC.BORDER};
                    border-radius: 10px;
                }}
            """)
        # Bouton calendrier
        self.btn_calendar.setIcon(qta.icon("fa5s.calendar-alt", color=MC.PRIMARY))
        self.btn_calendar.setStyleSheet(f"""
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
        # Bouton clear
        self.btn_clear.setIcon(qta.icon("fa5s.times", color=MC.DANGER))
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: {MC.DANGER_BG};
            }}
            QPushButton:pressed {{
                background: {MC.DANGER_BG};
            }}
        """)
        # Label date
        if self._selected_date:
            self.lbl_date.setStyleSheet(f"""
                QLabel {{
                    font-size: 13px;
                    font-weight: bold;
                    color: {MC.PRIMARY};
                    background: transparent;
                    border: none;
                    padding-left: 10px;
                }}
            """)
        else:
            self.lbl_date.setStyleSheet(f"""
                QLabel {{
                    font-size: 13px;
                    color: {MC.TEXT_MUTED};
                    background: transparent;
                    border: none;
                    padding-left: 10px;
                }}
            """)
        # Re-style calendar si créé
        if self._calendar_popup and hasattr(self, 'calendar'):
            self._style_calendar()
