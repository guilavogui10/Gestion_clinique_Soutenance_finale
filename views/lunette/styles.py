"""
=============================================================================
 STYLES - Lunette
=============================================================================
 Styles spécifiques au module lunette (commandes optiques).
 Hérite des styles globaux via views.shared.styles.Styles
 et views.shared.theme_manager.theme_manager.

 Utilisation :
   from views.lunette.styles import LunetteStyles
   self.table.setStyleSheet(LunetteStyles.table())
=============================================================================
"""

from views.shared.styles import Styles
from views.shared.theme_manager import theme_manager


class LunetteStyles:
    """Styles propres au module lunette. Étend les styles globaux."""

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
    def commande_card() -> str:
        """Carte de commande optique."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 16px;
            }}
            QLabel[class="ref"] {{
                font-size: 14px;
                font-weight: 700;
                color: {c['primary']};
            }}
            QLabel[class="patient"] {{
                font-size: 14px;
                font-weight: 600;
                color: {c['text_primary']};
            }}
            QLabel[class="detail"] {{
                font-size: 13px;
                color: {c['text_secondary']};
            }}
            QLabel[class="prix"] {{
                font-size: 15px;
                font-weight: 700;
                color: {c['text_primary']};
            }}
        """

    @staticmethod
    def livraison_badge(status: str) -> str:
        """Badge de statut de livraison (en_attente, en_cours, livree, annulee)."""
        c = theme_manager.colors()
        colors_map = {
            "en_attente": (c.get('warning', '#f59e0b'), c.get('warning_bg', '#fef3c7')),
            "en_cours":   (c.get('info', '#3b82f6'),    c.get('info_bg', '#dbeafe')),
            "livree":     (c.get('success', '#10b981'), c.get('success_bg', '#d1fae5')),
            "annulee":    (c.get('danger', '#ef4444'),  c.get('danger_bg', '#fee2e2')),
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
