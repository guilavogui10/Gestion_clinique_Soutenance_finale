"""
=============================================================================
 STYLES - Patient
=============================================================================
 Styles spécifiques au module patient.
 Hérite des styles globaux via views.shared.styles.Styles
 et views.shared.theme_manager.theme_manager.

 Utilisation :
   from views.patient.styles import PatientStyles
   self.table.setStyleSheet(PatientStyles.table())
=============================================================================
"""

from views.shared.styles import Styles
from views.shared.theme_manager import theme_manager


class PatientStyles:
    """Styles propres au module patient. Étend les styles globaux."""

    # ── HÉRITAGE GLOBAL ──────────────────────────────────────────────────

    table            = Styles.table
    card             = Styles.card
    search_bar       = Styles.search_bar
    input_field      = Styles.input_field
    button_primary   = Styles.button_primary
    button_secondary = Styles.button_secondary
    button_danger    = Styles.button_danger
    button_table_action = Styles.button_table_action
    dialog           = Styles.dialog
    dialog_header    = Styles.dialog_header
    dialog_full      = Styles.dialog_full
    action_bar       = Styles.action_bar
    menu             = Styles.menu
    scrollbar        = Styles.scrollbar
    stat_card_style  = Styles.stat_card_style

    # ── STYLES SPÉCIFIQUES ───────────────────────────────────────────────

    @staticmethod
    def action_bar() -> str:
        """Barre d'actions avec boutons (voir, modifier, ajouter visite)."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 8px 12px;
            }}
            QPushButton {{
                background-color: {c['primary']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {c['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {c['primary_hover']};
            }}
            QPushButton[class="secondary"] {{
                background-color: transparent;
                color: {c['primary']};
                border: 1px solid {c['primary']};
            }}
            QPushButton[class="secondary"]:hover {{
                background-color: {c['primary']};
                color: #ffffff;
            }}
        """

    @staticmethod
    def patient_info_card() -> str:
        """Carte de détail d'un patient."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 16px;
            }}
            QLabel[class="name"] {{
                font-size: 18px;
                font-weight: 700;
                color: {c['text_primary']};
            }}
            QLabel[class="info"] {{
                font-size: 13px;
                color: {c['text_secondary']};
            }}
            QLabel[class="id"] {{
                font-size: 12px;
                color: {c['primary']};
                font-weight: 600;
            }}
        """
    
    @staticmethod
    def tab_widget() -> str:
        """Style pour le QTabWidget."""
        c = theme_manager.colors()
        return f"""
            QTabWidget::pane {{
                border: none;
                background: white;
                padding: 0px;
                margin-top: 0px;
            }}
            QTabBar {{
                background: white;
                border: none;
            }}
            QTabBar::tab {{
                background: white;
                color: {c['text_secondary']};
                border: none;
                border-bottom: 3px solid transparent;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                min-width: 120px;
            }}
            QTabBar::tab:selected {{
                background: white;
                color: {c['primary']};
                border-bottom: 3px solid {c['primary']};
            }}
            QTabBar::tab:hover {{
                background: white;
                color: {c['text_primary']};
            }}
        """
