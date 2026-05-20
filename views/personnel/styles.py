"""
=============================================================================
 STYLES - Personnel
=============================================================================
 Styles spécifiques au module personnel.
 Hérite des styles globaux via views.shared.styles.Styles
 et views.shared.theme_manager.theme_manager.

 Utilisation :
   from views.personnel.styles import PersonnelStyles
   self.table.setStyleSheet(PersonnelStyles.table())
=============================================================================
"""

from views.shared.styles import Styles
from views.shared.theme_manager import theme_manager


class PersonnelStyles:
    """Styles propres au module personnel. Étend les styles globaux."""

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
    def personnel_card() -> str:
        """Carte d'information d'un membre du personnel."""
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
            QLabel[class="poste"] {{
                font-size: 13px;
                color: {c['text_secondary']};
            }}
            QLabel[class="service"] {{
                font-size: 13px;
                color: {c['primary']};
                font-weight: 600;
            }}
            QLabel[class="contact"] {{
                font-size: 12px;
                color: {c['text_muted']};
            }}
        """

    @staticmethod
    def role_badge(role: str) -> str:
        """Badge de rôle du personnel (admin, medecin, infirmier, pharmacien, autre)."""
        c = theme_manager.colors()
        colors_map = {
            "admin":      (c.get('danger', '#ef4444'),  c.get('danger_bg', '#fee2e2')),
            "medecin":    (c.get('info', '#3b82f6'),    c.get('info_bg', '#dbeafe')),
            "infirmier":  (c.get('success', '#10b981'), c.get('success_bg', '#d1fae5')),
            "pharmacien": (c.get('warning', '#f59e0b'), c.get('warning_bg', '#fef3c7')),
        }
        fg, bg = colors_map.get(role, (c['text_secondary'], c['bg_card']))
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
