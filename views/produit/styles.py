"""
=============================================================================
 STYLES - Produit
=============================================================================
 Styles spécifiques au module produit (stock, panier).
 Hérite des styles globaux via views.shared.styles.Styles
 et views.shared.theme_manager.theme_manager.

 Utilisation :
   from views.produit.styles import ProduitStyles
   self.table.setStyleSheet(ProduitStyles.table())
=============================================================================
"""

from views.shared.styles import Styles
from views.shared.theme_manager import theme_manager


class ProduitStyles:
    """Styles propres au module produit. Étend les styles globaux."""

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
    def stock_card() -> str:
        """Carte de niveau de stock."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 14px;
            }}
            QLabel[class="produit-nom"] {{
                font-size: 14px;
                font-weight: 700;
                color: {c['text_primary']};
            }}
            QLabel[class="quantite"] {{
                font-size: 20px;
                font-weight: 800;
                color: {c['primary']};
            }}
            QLabel[class="unite"] {{
                font-size: 12px;
                color: {c['text_muted']};
            }}
            QLabel[class="prix"] {{
                font-size: 13px;
                font-weight: 600;
                color: {c['text_primary']};
            }}
        """

    @staticmethod
    def stock_alert(level: str) -> str:
        """Badge d'alerte de stock (normal, faible, rupture)."""
        c = theme_manager.colors()
        colors_map = {
            "normal":  (c.get('success', '#10b981'), c.get('success_bg', '#d1fae5')),
            "faible":  (c.get('warning', '#f59e0b'), c.get('warning_bg', '#fef3c7')),
            "rupture": (c.get('danger', '#ef4444'),  c.get('danger_bg', '#fee2e2')),
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
            }}
        """

    @staticmethod
    def panier_item() -> str:
        """Ligne d'article dans le panier."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_main']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 8px 12px;
                margin-bottom: 4px;
            }}
            QLabel[class="nom"] {{
                font-size: 13px;
                font-weight: 600;
                color: {c['text_primary']};
            }}
            QLabel[class="qte"] {{
                font-size: 13px;
                color: {c['text_secondary']};
            }}
            QLabel[class="total"] {{
                font-size: 14px;
                font-weight: 700;
                color: {c['primary']};
            }}
            QSpinBox {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 13px;
                color: {c['text_primary']};
            }}
        """
