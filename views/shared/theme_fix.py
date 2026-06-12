"""
=============================================================================
 CORRECTIF THÈME - Forcer les Couleurs sur Tous les Widgets
=============================================================================
 Fonctions utilitaires pour éliminer les couleurs hardcodées (noir, blanc)
 et forcer l'application du thème sur tous les widgets.
=============================================================================
"""

from PySide6.QtWidgets import QWidget, QFrame, QLabel, QLineEdit, QTextEdit, QComboBox
from PySide6.QtWidgets import QPushButton, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit
from PySide6.QtWidgets import QScrollArea, QGroupBox, QPlainTextEdit
from views.shared.theme_manager import theme_manager


def force_theme_recursive(widget: QWidget, force_bg: bool = True):
    """
    Force l'application du thème récursivement sur un widget et tous ses enfants.
    
    Args:
        widget: Le widget racine
        force_bg: Si True, force le fond bg_main sur le widget racine
    """
    if not widget:
        return
    
    c = theme_manager.colors()
    
    # Forcer le fond sur le widget racine
    if force_bg and isinstance(widget, QWidget):
        current_style = widget.styleSheet()
        # Si pas de style ou style par défaut Qt
        if not current_style or 'background' not in current_style:
            widget.setStyleSheet(f"""
                {widget.__class__.__name__} {{
                    background-color: {c['bg_main']};
                    color: {c['text_primary']};
                }}
            """)
    
    # Parcourir tous les enfants
    for child in widget.findChildren(QWidget):
        _apply_theme_to_widget(child, c)


def _apply_theme_to_widget(widget: QWidget, colors: dict):
    """Applique le thème sur un widget selon son type."""
    if not widget:
        return
    
    c = colors
    object_name = widget.objectName()
    current_style = widget.styleSheet()
    
    # Déterminer si le widget a un style personnalisé important
    has_custom = _has_custom_style(current_style)
    
    # QFrame - Vérifier le fond
    if isinstance(widget, QFrame) and not has_custom:
        # Si fond noir ou blanc hardcodé, le remplacer
        if any(x in current_style.lower() for x in ['#000', 'black', '#fff', 'white']):
            widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {c['bg_card']};
                    color: {c['text_primary']};
                }}
            """)
        # Si pas de fond du tout, en mettre un
        elif 'background' not in current_style:
            widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {c['bg_card']};
                    color: {c['text_primary']};
                }}
            """)
    
    # QLabel - Forcer la couleur texte
    elif isinstance(widget, QLabel) and not has_custom:
        # Si texte noir hardcodé
        if any(x in current_style.lower() for x in ['color:#000', 'color: #000', 'color:black']):
            widget.setStyleSheet(f"""
                QLabel {{
                    color: {c['text_primary']};
                    background: transparent;
                    border: none;
                }}
            """)
        # Si pas de style du tout
        elif not current_style or 'color' not in current_style:
            widget.setStyleSheet(f"""
                QLabel {{
                    color: {c['text_primary']};
                    background: transparent;
                    border: none;
                }}
            """)
    
    # Champs de saisie
    elif isinstance(widget, (QLineEdit, QTextEdit, QPlainTextEdit)) and not has_custom:
        readonly = widget.isReadOnly() if hasattr(widget, 'isReadOnly') else False
        bg = c['bg_input'] if not readonly else c['bg_card']
        widget.setStyleSheet(f"""
            {widget.__class__.__name__} {{
                background-color: {bg};
                color: {c['text_primary']};
                border: 1.5px solid {c['border']};
                border-radius: 8px;
                padding: 8px;
            }}
            {widget.__class__.__name__}:focus {{
                border: 2px solid {c['border_focus']};
            }}
        """)
    
    # ComboBox
    elif isinstance(widget, QComboBox) and not has_custom:
        widget.setStyleSheet(f"""
            QComboBox {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1.5px solid {c['border']};
                border-radius: 8px;
                padding: 6px 10px;
            }}
            QComboBox:focus {{
                border: 2px solid {c['border_focus']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                selection-background-color: {c['primary_light']};
                selection-color: {c['primary']};
            }}
        """)
    
    # Spinners
    elif isinstance(widget, (QSpinBox, QDoubleSpinBox)) and not has_custom:
        widget.setStyleSheet(f"""
            {widget.__class__.__name__} {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1.5px solid {c['border']};
                border-radius: 8px;
                padding: 6px;
            }}
        """)
    
    # Date/Time
    elif isinstance(widget, (QDateEdit, QTimeEdit)) and not has_custom:
        widget.setStyleSheet(f"""
            {widget.__class__.__name__} {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1.5px solid {c['border']};
                border-radius: 8px;
                padding: 6px 10px;
            }}
        """)
    
    # ScrollArea
    elif isinstance(widget, QScrollArea):
        widget.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: {c['bg_card']};
            }}
            QScrollArea > QWidget {{
                background: {c['bg_card']};
            }}
        """)


def _has_custom_style(style: str) -> bool:
    """Détecte si un style est personnalisé (ne pas écraser)."""
    if not style:
        return False
    indicators = [
        'qlineargradient', 'qradialgradient',
        'border-left:', 'border-right:', 'border-top:',
        'font-weight: bold', 'font-weight:bold',
        'border-radius: 1', 'border-radius:1'
    ]
    return any(ind in style.lower() for ind in indicators)


def fix_black_widgets(widget: QWidget):
    """
    Fonction spécifique pour corriger les widgets qui restent noirs.
    À utiliser en dernier recours.
    """
    c = theme_manager.colors()
    
    # Forcer le fond sur TOUS les QFrame sans exception
    for frame in widget.findChildren(QFrame):
        current = frame.styleSheet()
        # Si contient noir ou blanc, remplacer
        if any(x in current.lower() for x in ['#000', 'black', 'background:#fff', 'background: #fff']):
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {c['bg_card']};
                    color: {c['text_primary']};
                }}
            """)
    
    # Forcer la couleur sur TOUS les QLabel
    for label in widget.findChildren(QLabel):
        current = label.styleSheet()
        # Si texte noir ou pas de style
        if not current or any(x in current.lower() for x in ['color:#000', 'color:black', 'color: #000']):
            label.setStyleSheet(f"""
                QLabel {{
                    color: {c['text_primary']};
                    background: transparent;
                }}
            """)


def apply_theme_to_all_children(widget: QWidget):
    """
    Version agressive - applique le thème sur TOUS les enfants sans vérification.
    Utiliser si force_theme_recursive ne fonctionne pas.
    """
    c = theme_manager.colors()
    
    # Style global pour tous les widgets
    widget.setStyleSheet(f"""
        QWidget {{
            background-color: {c['bg_main']};
            color: {c['text_primary']};
        }}
        QFrame {{
            background-color: {c['bg_card']};
            color: {c['text_primary']};
        }}
        QLabel {{
            color: {c['text_primary']};
            background: transparent;
            border: none;
        }}
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {c['bg_input']};
            color: {c['text_primary']};
            border: 1.5px solid {c['border']};
            border-radius: 8px;
            padding: 8px;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {c['border_focus']};
        }}
        QComboBox {{
            background-color: {c['bg_input']};
            color: {c['text_primary']};
            border: 1.5px solid {c['border']};
            border-radius: 8px;
            padding: 6px 10px;
        }}
        QComboBox:focus {{
            border: 2px solid {c['border_focus']};
        }}
        QComboBox QAbstractItemView {{
            background-color: {c['bg_card']};
            color: {c['text_primary']};
            selection-background-color: {c['primary_light']};
            selection-color: {c['primary']};
        }}
        QScrollArea {{
            border: none;
            background: {c['bg_card']};
        }}
        QScrollArea > QWidget {{
            background: {c['bg_card']};
        }}
        QGroupBox {{
            background-color: {c['bg_card']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
        }}
    """)
