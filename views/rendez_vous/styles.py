"""
Styles specifiques au module rendez-vous.
"""

from views.shared.styles import Styles
from views.shared.theme_manager import theme_manager


class RendezVousStyles:
    table = Styles.table
    card = Styles.card
    search_bar = Styles.search_bar
    input_field = Styles.input_field
    button_primary = Styles.button_primary
    button_secondary = Styles.button_secondary
    button_danger = Styles.button_danger
    button_table_action = Styles.button_table_action
    dialog = Styles.dialog
    dialog_header = Styles.dialog_header
    dialog_full = Styles.dialog_full
    action_bar = Styles.action_bar
    menu = Styles.menu
    scrollbar = Styles.scrollbar
    stat_card_style = Styles.stat_card_style

    @staticmethod
    def status_badge(statut: str) -> str:
        c = theme_manager.colors()
        statut = str(statut or "").strip().lower()
        palette = {
            "attente": (c["warning"], c["warning_bg"]),
            "confirme": (c["success"], c["success_bg"]),
            "en_cours": (c["info"], c["info_bg"]),
            "termine": (c["primary"], c["primary_light"]),
            "annule": (c["danger"], c["danger_bg"]),
            "absent": ("#B7791F", "#FEF3C7"),
            "reporte": ("#DB2777", "#FCE7F3"),
        }
        fg, bg = palette.get(statut, (c["text_secondary"], c["bg_input"]))
        return f"""
            QLabel {{
                color: {fg};
                background: {bg};
                border: 1px solid {fg}55;
                border-radius: 10px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 700;
            }}
        """
