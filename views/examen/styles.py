"""
=============================================================================
 STYLES - Examen
=============================================================================
 Styles spécifiques au module examen.
 Hérite des styles globaux via views.shared.styles.Styles
 et views.shared.theme_manager.theme_manager.

 Utilisation :
   from views.examen.styles import ExamenStyles
   self.table.setStyleSheet(ExamenStyles.table())
=============================================================================
"""

from views.shared.styles import Styles
from views.shared.theme_manager import theme_manager


class ExamenStyles:
    """Styles propres au module examen. Étend les styles globaux."""

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
    def examen_card() -> str:
        """Carte de détail d'un examen."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 16px;
            }}
            QLabel[class="type"] {{
                font-size: 14px;
                font-weight: 700;
                color: {c['primary']};
            }}
            QLabel[class="date"] {{
                font-size: 12px;
                color: {c['text_muted']};
            }}
            QLabel[class="description"] {{
                font-size: 13px;
                color: {c['text_secondary']};
            }}
        """

    @staticmethod
    def result_panel() -> str:
        """Panneau d'affichage des résultats d'examen."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 14px;
            }}
            QLabel[class="result-title"] {{
                font-size: 15px;
                font-weight: 700;
                color: {c['text_primary']};
            }}
            QLabel[class="result-value"] {{
                font-size: 14px;
                color: {c['text_primary']};
                font-weight: 600;
            }}
            QLabel[class="result-unit"] {{
                font-size: 12px;
                color: {c['text_muted']};
            }}
            QLabel[class="result-normal"] {{
                color: {c.get('success', '#10b981')};
                font-weight: 600;
            }}
            QLabel[class="result-abnormal"] {{
                color: {c.get('danger', '#ef4444')};
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
