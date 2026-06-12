"""
=============================================================================
 STYLES - Visite
=============================================================================
 Styles spécifiques au module visite.
 Hérite des styles globaux via views.shared.styles.Styles
 et views.shared.theme_manager.theme_manager.

 Utilisation :
   from views.visite.styles import VisiteStyles
   self.table.setStyleSheet(VisiteStyles.table())
=============================================================================
"""

from views.shared.styles import Styles
from views.shared.theme_manager import theme_manager


class VisiteStyles:
    """Styles propres au module visite. Étend les styles globaux."""

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
    def workflow_step(active: bool = False) -> str:
        """Carte d'étape du workflow (active ou inactive)."""
        c = theme_manager.colors()
        bg = c['primary'] if active else c['bg_card']
        text = c['text_inverse'] if active else c['text_primary']
        border = c['primary'] if active else c['border']
        return f"""
            QFrame {{
                background-color: {bg};
                border: 2px solid {border};
                border-radius: 10px;
                padding: 12px;
            }}
            QLabel {{
                color: {text};
                font-size: 13px;
            }}
            QLabel[class="title"] {{
                font-size: 15px;
                font-weight: 700;
                color: {text};
            }}
            QLabel[class="step-number"] {{
                font-size: 20px;
                font-weight: 800;
                color: {text};
            }}
        """

    @staticmethod
    def notification_panel() -> str:
        """Panneau de notifications."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 12px;
            }}
            QLabel[class="notif-title"] {{
                font-size: 14px;
                font-weight: 700;
                color: {c['text_primary']};
            }}
            QLabel[class="notif-message"] {{
                font-size: 12px;
                color: {c['text_secondary']};
            }}
            QLabel[class="notif-time"] {{
                font-size: 11px;
                color: {c['text_muted']};
            }}
        """

    @staticmethod
    def status_badge(status: str) -> str:
        """Badge de statut visite (en_attente, en_cours, terminee)."""
        c = theme_manager.colors()
        colors_map = {
            "en_attente": (c.get('warning', '#f59e0b'), c.get('warning_bg', '#fef3c7')),
            "en_cours":   (c.get('info', '#3b82f6'),    c.get('info_bg', '#dbeafe')),
            "terminee":   (c.get('success', '#10b981'),  c.get('success_bg', '#d1fae5')),
        }
        fg, bg = colors_map.get(status, (c['text_secondary'], c['bg_card']))
        return f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border-radius: 10px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 700;
            }}
        """

    @staticmethod
    def tab_widget() -> str:
        """Style pour le widget d'onglets."""
        c = theme_manager.colors()
        return f"""
            QTabWidget::pane {{
                border: none;
                background: {c['bg_card']};
                padding: 0px;
                margin-top: 0px;
            }}
            QTabBar {{
                background: {c['bg_card']};
                border: none;
            }}
            QTabBar::tab {{
                background: {c['bg_card']};
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
                background: {c['bg_card']};
                color: {c['primary']};
                border: none;
                border-bottom: 3px solid {c['primary']};
            }}
            QTabBar::tab:hover {{
                background: {c['hover']};
                color: {c['text_primary']};
                border: none;
            }}
        """
