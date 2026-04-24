"""
=============================================================================
 STYLES - Facturation
=============================================================================
 Styles spécifiques au module facturation patient.
 Hérite des styles globaux via views.shared.styles.Styles
 et views.shared.theme_manager.theme_manager.

 Utilisation :
   from views.facturation.patient.styles import FacturationStyles
   self.table.setStyleSheet(FacturationStyles.table())
=============================================================================
"""

from views.shared.styles import Styles
from views.shared.theme_manager import theme_manager


class FacturationStyles:
    """Styles propres au module facturation. Étend les styles globaux."""

    # ── HÉRITAGE GLOBAL ──────────────────────────────────────────────────

    table            = Styles.table
    card             = Styles.card
    search_bar       = Styles.search_bar
    input_field      = Styles.input_field
    button_primary   = Styles.button_primary
    button_secondary = Styles.button_secondary
    button_danger    = Styles.button_danger
    dialog           = Styles.dialog
    dialog_header    = Styles.dialog_header

    # ── STYLES SPÉCIFIQUES ───────────────────────────────────────────────

    @staticmethod
    def facture_card() -> str:
        """Carte de facture."""
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
            QLabel[class="date"] {{
                font-size: 12px;
                color: {c['text_muted']};
            }}
        """

    @staticmethod
    def montant_label() -> str:
        """Affichage des montants."""
        c = theme_manager.colors()
        return f"""
            QLabel[class="montant-total"] {{
                font-size: 22px;
                font-weight: 800;
                color: {c['text_primary']};
            }}
            QLabel[class="montant-paye"] {{
                font-size: 16px;
                font-weight: 700;
                color: {c.get('success', '#10b981')};
            }}
            QLabel[class="montant-reste"] {{
                font-size: 16px;
                font-weight: 700;
                color: {c.get('danger', '#ef4444')};
            }}
            QLabel[class="devise"] {{
                font-size: 12px;
                color: {c['text_muted']};
                font-weight: 500;
            }}
        """

    @staticmethod
    def status_facture(paid: bool) -> str:
        """Badge de statut de facture (payée / impayée)."""
        c = theme_manager.colors()
        if paid:
            fg = c.get('success', '#10b981')
            bg = c.get('success_bg', '#d1fae5')
        else:
            fg = c.get('danger', '#ef4444')
            bg = c.get('danger_bg', '#fee2e2')
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
