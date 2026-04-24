"""
=============================================================================
 STYLES - Admin
=============================================================================
 Styles spécifiques au module administration.
 Hérite des styles globaux via views.shared.styles.Styles
 et views.shared.theme_manager.theme_manager.

 Utilisation :
   from views.admin.styles import AdminStyles
   self.table.setStyleSheet(AdminStyles.table())
=============================================================================
"""

from views.shared.styles import Styles
from views.shared.theme_manager import theme_manager


class AdminStyles:
    """Styles propres au module administration. Étend les styles globaux."""

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
    def admin_card() -> str:
        """Carte du panneau d'administration."""
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
            QLabel[class="description"] {{
                font-size: 13px;
                color: {c['text_secondary']};
            }}
            QLabel[class="count"] {{
                font-size: 22px;
                font-weight: 800;
                color: {c['primary']};
            }}
        """

    @staticmethod
    def system_info() -> str:
        """Affichage des informations système."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_main']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 12px;
            }}
            QLabel[class="info-key"] {{
                font-size: 12px;
                font-weight: 600;
                color: {c['text_secondary']};
            }}
            QLabel[class="info-value"] {{
                font-size: 13px;
                font-weight: 500;
                color: {c['text_primary']};
            }}
            QLabel[class="version"] {{
                font-size: 11px;
                color: {c['text_muted']};
            }}
            QProgressBar {{
                background-color: {c['border']};
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {c['primary']};
                border-radius: 4px;
            }}
        """
