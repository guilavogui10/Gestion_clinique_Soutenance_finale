"""
=============================================================================
 STYLES - Fournisseur
=============================================================================
 Styles spécifiques au module fournisseur.
 Hérite des styles globaux via views.shared.styles.Styles
 et views.shared.theme_manager.theme_manager.

 Utilisation :
   from views.fournisseur.styles import FournisseurStyles
   self.table.setStyleSheet(FournisseurStyles.table())
=============================================================================
"""

from views.shared.styles import Styles
from views.shared.theme_manager import theme_manager


class FournisseurStyles:
    """Styles propres au module fournisseur. Étend les styles globaux."""

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
    def fournisseur_card() -> str:
        """Carte d'information d'un fournisseur."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 16px;
            }}
            QLabel[class="name"] {{
                font-size: 16px;
                font-weight: 700;
                color: {c['text_primary']};
            }}
            QLabel[class="contact"] {{
                font-size: 13px;
                color: {c['text_secondary']};
            }}
            QLabel[class="tel"] {{
                font-size: 13px;
                color: {c['primary']};
                font-weight: 600;
            }}
            QLabel[class="adresse"] {{
                font-size: 12px;
                color: {c['text_muted']};
            }}
        """

    @staticmethod
    def action_dialog() -> str:
        """Style du dialogue d'action fournisseur."""
        c = theme_manager.colors()
        return f"""
            QDialog {{
                background-color: {c['bg_card']};
                border-radius: 12px;
            }}
            QLabel[class="dialog-title"] {{
                font-size: 16px;
                font-weight: 700;
                color: {c['text_primary']};
                padding-bottom: 8px;
            }}
            QLineEdit, QTextEdit {{
                background-color: {c['bg_main']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                color: {c['text_primary']};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {c['primary']};
            }}
            QPushButton {{
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }}
        """

    @staticmethod
    def tab_widget() -> str:
        """Style pour le widget d'onglets."""
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
                padding: 10px 20px;
                margin-right: 0px;
                margin-bottom: 0px;
                font-size: 14px;
                font-weight: 600;
                min-width: 120px;
            }}
            QTabBar::tab:selected {{
                background: white;
                color: {c['primary']};
                border: none;
                border-bottom: 3px solid {c['primary']};
            }}
            QTabBar::tab:hover {{
                background: white;
                color: {c['text_primary']};
                border: none;
            }}
        """
