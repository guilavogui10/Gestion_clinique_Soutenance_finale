"""
Styles centralises pour la facture patient.
Objectif : UI moderne proche de la maquette.
"""
from views.shared.theme_manager import theme_manager


class _ThemeColor:
    def __init__(self, key): self._key = key
    def __set_name__(self, owner, name): self._name = name
    def __get__(self, obj, objtype=None): return theme_manager.colors()[self._key]


class FacturePatientStyles:
    """Styles CSS et palette de couleurs."""

    BLEU_PRINCIPAL = _ThemeColor('primary')
    ROUGE          = _ThemeColor('danger')

    @staticmethod
    def card() -> str:
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background: {c['bg_card']};
                border-radius: 14px;
                border: 1px solid {c['border']};
            }}
        """

    @staticmethod
    def section_title(color: str = None) -> str:
        c = theme_manager.colors()
        color = color or c['text_primary']
        return (
            "font-size: 12px; font-weight: bold; text-transform: uppercase; "
            f"color: {color}; border: none; background: transparent;"
        )

    @staticmethod
    def search_input() -> str:
        c = theme_manager.colors()
        return f"""
            QLineEdit {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding-left: 12px;
                font-size: 12px;
            }}
            QLineEdit:focus {{ border: 2px solid {c['info']}; }}
            QComboBox {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding-left: 10px;
                font-size: 12px;
            }}
            QComboBox:focus {{ border: 2px solid {c['info']}; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
            QComboBox QAbstractItemView {{ border-radius: 8px; }}
        """

    @staticmethod
    def btn_add(bleu: str = None) -> str:
        c = theme_manager.colors()
        bleu = bleu or c['info']
        return f"""
            QPushButton {{
                background: {bleu};
                color: {c['text_inverse']};
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: {c['primary']}; }}
        """

    @staticmethod
    def btn_pay() -> str:
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {c['info']}, stop:1 {c['primary']}
                );
                color: {c['text_inverse']};
                border-radius: 14px;
                font-weight: bold;
                font-size: 12px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{ background: {c['primary']}; }}
        """

    @staticmethod
    def btn_cancel() -> str:
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                background: {c['bg_card']};
                color: {c['danger']};
                border: 1px solid {c['danger']};
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: {c['danger_bg']}; }}
        """

    @staticmethod
    def table_header() -> str:
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background: {c['bg_card']};
                border-radius: 10px;
                border: 1px solid {c['border']};
            }}
            QLabel {{
                color: {c['text_primary']};
                font-weight: bold;
                font-size: 10px;
                border: none;
                background: transparent;
            }}
        """

    @staticmethod
    def row_item() -> str:
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background: {c['bg_card']};
                border-radius: 10px;
                border: 1px solid {c['border']};
            }}
            QFrame:hover {{
                border: 1px solid {c['border']};
                background: {c['hover']};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """

    @staticmethod
    def scrollbar() -> str:
        c = theme_manager.colors()
        return f"""
            QScrollBar:vertical {{
                border: none; background: {c['bg_main']};
                width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']}; min-height: 20px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {c['text_muted']}; }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0px; }}
        """

    @staticmethod
    def badge_urgent() -> str:
        c = theme_manager.colors()
        return f"""
            QLabel {{
                background: {c['danger_bg']};
                color: {c['danger']};
                border-radius: 8px;
                padding: 2px 6px;
                font-size: 9px;
                font-weight: bold;
            }}
        """
