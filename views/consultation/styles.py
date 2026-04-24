"""
=============================================================================
 STYLES - Consultation
=============================================================================
 Styles spécifiques au module consultation.
 Hérite des styles globaux via views.shared.styles.Styles
 et views.shared.theme_manager.theme_manager.

 Utilisation :
   from views.consultation.styles import ConsultationStyles
   self.table.setStyleSheet(ConsultationStyles.table())
=============================================================================
"""

from views.shared.styles import Styles
from views.shared.theme_manager import theme_manager


class ConsultationStyles:
    """Styles propres au module consultation. Étend les styles globaux."""

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
    def consultation_card() -> str:
        """Carte de détail d'une consultation."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 16px;
            }}
            QLabel[class="title"] {{
                font-size: 16px;
                font-weight: 700;
                color: {c['text_primary']};
            }}
            QLabel[class="date"] {{
                font-size: 12px;
                color: {c['text_muted']};
            }}
            QLabel[class="motif"] {{
                font-size: 13px;
                color: {c['text_secondary']};
                padding: 4px 0;
            }}
            QTextEdit {{
                background-color: {c['bg_main']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                color: {c['text_primary']};
            }}
        """

    @staticmethod
    def stat_panel() -> str:
        """Panneau de statistiques."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 14px;
            }}
            QLabel[class="stat-value"] {{
                font-size: 24px;
                font-weight: 800;
                color: {c['primary']};
            }}
            QLabel[class="stat-label"] {{
                font-size: 12px;
                color: {c['text_secondary']};
                font-weight: 500;
            }}
            QLabel[class="stat-change"] {{
                font-size: 11px;
                color: {c.get('success', '#10b981')};
                font-weight: 600;
            }}
        """
