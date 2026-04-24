"""
=============================================================================
 STYLES - Chirurgie
=============================================================================
 Styles spécifiques au module chirurgie.
 Hérite des styles globaux via views.shared.styles.Styles
 et views.shared.theme_manager.theme_manager.

 Utilisation :
   from views.chirurgie.styles import ChirurgieStyles
   self.table.setStyleSheet(ChirurgieStyles.table())
=============================================================================
"""

from views.shared.styles import Styles
from views.shared.theme_manager import theme_manager


class ChirurgieStyles:
    """Styles propres au module chirurgie. Étend les styles globaux."""

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
    def chirurgie_card() -> str:
        """Carte de détail d'une chirurgie."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 16px;
            }}
            QLabel[class="operation"] {{
                font-size: 16px;
                font-weight: 700;
                color: {c['text_primary']};
            }}
            QLabel[class="chirurgien"] {{
                font-size: 13px;
                color: {c['primary']};
                font-weight: 600;
            }}
            QLabel[class="date"] {{
                font-size: 12px;
                color: {c['text_muted']};
            }}
            QLabel[class="notes"] {{
                font-size: 13px;
                color: {c['text_secondary']};
            }}
        """

    @staticmethod
    def urgency_badge(level: str) -> str:
        """Badge d'urgence chirurgicale (haute, moyenne, basse)."""
        c = theme_manager.colors()
        colors_map = {
            "haute":   (c.get('danger', '#ef4444'),  c.get('danger_bg', '#fee2e2')),
            "moyenne": (c.get('warning', '#f59e0b'), c.get('warning_bg', '#fef3c7')),
            "basse":   (c.get('success', '#10b981'), c.get('success_bg', '#d1fae5')),
        }
        fg, bg = colors_map.get(level, (c['text_secondary'], c['bg_card']))
        return f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border-radius: 10px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
            }}
        """
