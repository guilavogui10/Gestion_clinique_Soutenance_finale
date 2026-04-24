"""
=============================================================================
 STYLES - Prescription
=============================================================================
 Styles spécifiques au module prescription.
 Hérite des styles globaux via views.shared.styles.Styles
 et views.shared.theme_manager.theme_manager.

 Utilisation :
   from views.prescription.styles import PrescriptionStyles
   self.table.setStyleSheet(PrescriptionStyles.table())
=============================================================================
"""

from views.shared.styles import Styles
from views.shared.theme_manager import theme_manager


class PrescriptionStyles:
    """Styles propres au module prescription. Étend les styles globaux."""

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
    def prescription_card() -> str:
        """Carte de détail d'une prescription."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 16px;
            }}
            QLabel[class="title"] {{
                font-size: 15px;
                font-weight: 700;
                color: {c['text_primary']};
            }}
            QLabel[class="medecin"] {{
                font-size: 13px;
                color: {c['primary']};
                font-weight: 600;
            }}
            QLabel[class="date"] {{
                font-size: 12px;
                color: {c['text_muted']};
            }}
        """

    @staticmethod
    def ligne_item() -> str:
        """Ligne d'un élément de prescription."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_main']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 8px 12px;
                margin-bottom: 4px;
            }}
            QLabel[class="medicament"] {{
                font-size: 13px;
                font-weight: 600;
                color: {c['text_primary']};
            }}
            QLabel[class="posologie"] {{
                font-size: 12px;
                color: {c['text_secondary']};
            }}
            QLabel[class="quantite"] {{
                font-size: 13px;
                font-weight: 700;
                color: {c['primary']};
            }}
        """
