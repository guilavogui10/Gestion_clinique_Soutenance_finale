"""
=============================================================================
 MIXIN THÈME - Application Automatique et Récursive
=============================================================================
 Mixin pour automatiser l'application du thème sur tous les widgets.
 Résout le problème des widgets avec couleurs fixes (noir, blanc).
=============================================================================
"""

from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton
from PySide6.QtWidgets import QTableWidget, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit
from PySide6.QtWidgets import QFrame, QGroupBox, QCheckBox, QRadioButton, QPlainTextEdit
from views.shared.theme_manager import theme_manager


class ThemeAwareMixin:
    """
    Mixin qui automatise l'application du thème.
    Usage : class MyWidget(ThemeAwareMixin, QWidget):
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Connexion automatique au changement de thème
        theme_manager.theme_changed.connect(self._auto_apply_theme)
        # Application initiale
        self._auto_apply_theme()
    
    def _auto_apply_theme(self):
        """Applique le thème automatiquement et récursivement."""
        # 1. Appeler la méthode apply_theme si elle existe
        if hasattr(self, 'apply_theme') and callable(self.apply_theme):
            try:
                self.apply_theme()
            except Exception:
                pass
        
        # 2. Forcer les styles de base sur les widgets enfants
        self._apply_theme_recursive(self)
    
    def _apply_theme_recursive(self, widget):
        """Applique le thème récursivement sur tous les enfants."""
        if not widget:
            return
        
        c = theme_manager.colors()
        
        # Appliquer les styles de base selon le type de widget
        self._apply_base_style(widget, c)
        
        # Parcourir tous les enfants
        for child in widget.findChildren(QWidget):
            # Si l'enfant a sa propre méthode apply_theme, l'appeler
            if hasattr(child, 'apply_theme') and callable(child.apply_theme):
                try:
                    child.apply_theme()
                except Exception:
                    pass
            else:
                # Sinon appliquer le style de base
                self._apply_base_style(child, c)
    
    def _apply_base_style(self, widget, colors):
        """Applique un style de base selon le type de widget."""
        if not widget:
            return
        
        # Ne pas écraser si le widget a un objectName spécifique (styles personnalisés)
        object_name = widget.objectName()
        
        # Labels - forcer la couleur de texte
        if isinstance(widget, QLabel):
            current = widget.styleSheet()
            # Ne forcer que si pas de style personnalisé évident
            if 'color:' not in current or '#000' in current or 'black' in current.lower():
                widget.setStyleSheet(f"""
                    QLabel {{
                        color: {colors['text_primary']};
                        background: transparent;
                        border: none;
                    }}
                """)
        
        # Champs de saisie
        elif isinstance(widget, (QLineEdit, QTextEdit, QPlainTextEdit)):
            if not current_has_complex_style(widget):
                widget.setStyleSheet(f"""
                    {widget.__class__.__name__} {{
                        background-color: {colors['bg_input']};
                        color: {colors['text_primary']};
                        border: 1.5px solid {colors['border']};
                        border-radius: 8px;
                        padding: 8px;
                    }}
                    {widget.__class__.__name__}:focus {{
                        border: 2px solid {colors['border_focus']};
                        background-color: {colors['bg_card']};
                    }}
                """)
        
        # ComboBox
        elif isinstance(widget, QComboBox):
            if not current_has_complex_style(widget):
                widget.setStyleSheet(f"""
                    QComboBox {{
                        background-color: {colors['bg_input']};
                        color: {colors['text_primary']};
                        border: 1.5px solid {colors['border']};
                        border-radius: 8px;
                        padding: 6px 10px;
                    }}
                    QComboBox:focus {{
                        border: 2px solid {colors['border_focus']};
                    }}
                    QComboBox::drop-down {{
                        border: none;
                    }}
                    QComboBox QAbstractItemView {{
                        background-color: {colors['bg_card']};
                        color: {colors['text_primary']};
                        selection-background-color: {colors['primary_light']};
                        selection-color: {colors['primary']};
                    }}
                """)
        
        # Spinners
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            if not current_has_complex_style(widget):
                widget.setStyleSheet(f"""
                    {widget.__class__.__name__} {{
                        background-color: {colors['bg_input']};
                        color: {colors['text_primary']};
                        border: 1.5px solid {colors['border']};
                        border-radius: 8px;
                        padding: 6px;
                    }}
                """)
        
        # Date/Time
        elif isinstance(widget, (QDateEdit, QTimeEdit)):
            if not current_has_complex_style(widget):
                widget.setStyleSheet(f"""
                    {widget.__class__.__name__} {{
                        background-color: {colors['bg_input']};
                        color: {colors['text_primary']};
                        border: 1.5px solid {colors['border']};
                        border-radius: 8px;
                        padding: 6px 10px;
                    }}
                """)
        
        # Frames - forcer le fond
        elif isinstance(widget, (QFrame, QGroupBox)):
            current = widget.styleSheet()
            # Seulement si pas de style ou fond noir/blanc fixe
            if not current or 'background' not in current or any(x in current for x in ['#000', 'black', '#fff', 'white']):
                if not object_name or 'card' in object_name.lower():
                    widget.setStyleSheet(f"""
                        {widget.__class__.__name__} {{
                            background-color: {colors['bg_card']};
                            color: {colors['text_primary']};
                        }}
                    """)
        
        # Tables
        elif isinstance(widget, QTableWidget):
            widget.setStyleSheet(f"""
                QTableWidget {{
                    background-color: {colors['bg_table']};
                    alternate-background-color: {colors['bg_table_alt']};
                    color: {colors['text_primary']};
                    gridline-color: {colors['table_gridline']};
                    selection-background-color: {colors['table_selection']};
                }}
                QHeaderView::section {{
                    background-color: {colors['table_header_bg']};
                    color: {colors['primary']};
                    border-bottom: 2px solid {colors['table_header_border']};
                }}
            """)


def current_has_complex_style(widget):
    """Vérifie si un widget a un style complexe personnalisé."""
    style = widget.styleSheet()
    if not style:
        return False
    # Indicateurs de style complexe
    indicators = ['qlineargradient', 'qradialgradient', 'font-weight:', 'border-left:', 'border-right:']
    return any(ind in style.lower() for ind in indicators)


def force_theme_on_widget(widget):
    """
    Fonction utilitaire pour forcer l'application du thème sur un widget externe.
    Usage: force_theme_on_widget(mon_widget)
    """
    c = theme_manager.colors()
    
    # Appliquer le fond principal
    widget.setStyleSheet(f"""
        QWidget {{
            background-color: {c['bg_main']};
            color: {c['text_primary']};
        }}
        QLabel {{
            color: {c['text_primary']};
            background: transparent;
        }}
        QFrame {{
            background-color: {c['bg_card']};
            color: {c['text_primary']};
        }}
    """)
    
    # Propager récursivement
    for child in widget.findChildren(QWidget):
        if hasattr(child, 'apply_theme'):
            child.apply_theme()
