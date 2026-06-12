"""
Styles CSS centralisés pour le widget panier.
Architecture : Séparation des préoccupations (Separation of Concerns).
"""
from views.shared.theme_manager import theme_manager


class _ThemeColor:
    def __init__(self, key): self._key = key
    def __set_name__(self, owner, name): self._name = name
    def __get__(self, obj, objtype=None): return theme_manager.colors()[self._key]


class PanierStyles:
    """Classe contenant tous les styles CSS du panier."""

    VERT_PRINCIPAL = _ThemeColor('primary')
    ROUGE          = _ThemeColor('danger')

    @staticmethod
    def combo_fournisseur(vert_principal: str = None) -> str:
        """Style pour le combo fournisseur."""
        c = theme_manager.colors()
        vert_principal = vert_principal or c['primary']
        return f"""
            QComboBox {{
                border-radius: 10px;
                border: 2px solid {c['border_light']};
                padding-left: 10px;
                background: {c['bg_input']};
                font-size: 12px;
                color: {c['text_primary']};
            }}
            QComboBox:focus {{ border: 2px solid {vert_principal}; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
            QComboBox QAbstractItemView {{
                border-radius: 8px;
                border: 1px solid {c['border']};
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                padding: 6px 10px;
                min-height: 26px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {c['hover']};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {c['primary_light']};
                color: {c['primary']};
            }}
        """

    @staticmethod
    def combo_produit(vert_principal: str = None) -> str:
        """Style moderne et compact pour le combo produit."""
        c = theme_manager.colors()
        vert_principal = vert_principal or c['primary']
        return f"""
            QComboBox {{
                border-radius: 10px;
                border: 1px solid {c['border']};
                padding-left: 12px;
                background: {c['bg_input']};
                font-size: 12px;
                color: {c['text_primary']};
            }}
            QComboBox:focus {{
                border: 2px solid {vert_principal};
                background: {c['bg_card']};
            }}
            QComboBox:hover {{
                border: 1px solid {c['text_muted']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
                subcontrol-origin: padding;
                subcontrol-position: center right;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                border-radius: 10px;
                border: 1px solid {c['border']};
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                outline: none;
                padding: 4px;
            }}
            QComboBox QAbstractItemView::item {{
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                padding: 6px 10px;
                min-height: 26px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {c['hover']};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {vert_principal};
                color: {c['text_inverse']};
            }}
        """

    @staticmethod
    def input_readonly() -> str:
        """Style élégant pour les champs en lecture seule."""
        c = theme_manager.colors()
        return f"""
            border-radius: 10px;
            border: 1px dashed {c['border']};
            padding-left: 14px;
            background: {c['bg_input']};
            font-size: 12px;
            color: {c['text_muted']};
            font-style: italic;
        """

    @staticmethod
    def input_normal() -> str:
        """Style pour les champs normaux."""
        c = theme_manager.colors()
        return f"""
            border-radius: 8px; border: 1px solid {c['border']};
            padding-left: 12px; background: {c['bg_card']}; font-size: 12px;
        """

    @staticmethod
    def input_valide() -> str:
        """Style pour les champs valides."""
        c = theme_manager.colors()
        return f"""
            border-radius: 8px; border: 2px solid {c['success']};
            padding-left: 12px; background: {c['success_bg']}; font-size: 12px;
        """

    @staticmethod
    def input_invalide() -> str:
        """Style pour les champs invalides."""
        c = theme_manager.colors()
        return f"""
            border-radius: 8px; border: 2px solid {c['danger']};
            padding-left: 12px; background: {c['danger_bg']}; font-size: 12px;
        """

    @staticmethod
    def btn_ajouter(vert_principal: str = None) -> str:
        """Style pour le bouton ajouter au panier."""
        c = theme_manager.colors()
        vert_principal = vert_principal or c['primary']
        return f"""
            QPushButton {{
                background-color: {vert_principal};
                color: {c['text_inverse']}; border-radius: 10px;
                font-weight: bold; font-size: 13px; border: none;
            }}
            QPushButton:hover {{ background-color: {c['primary_light']}; }}
            QPushButton:pressed {{ background-color: {c['primary']}; }}
        """

    @staticmethod
    def btn_ajouter_modern(vert_principal: str = None) -> str:
        """Style moderne pour le bouton ajouter au panier avec effet gradient et ombre."""
        c = theme_manager.colors()
        vert_principal = vert_principal or c['primary']
        return f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {vert_principal},
                    stop:1 {c['primary_light']}
                );
                color: {c['text_inverse']};
                border-radius: 14px;
                font-weight: 700;
                font-size: 14px;
                border: none;
                padding: 10px 24px;
                text-align: center;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {c['primary_light']},
                    stop:1 {vert_principal}
                );
                padding: 10px 26px;
            }}
            QPushButton:pressed {{
                background-color: {c['primary']};
                padding: 10px 24px;
            }}
            QPushButton:disabled {{
                background: {c['border']};
                color: {c['text_muted']};
            }}
        """

    @staticmethod
    def btn_finaliser() -> str:
        """Style pour le bouton finaliser."""
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                background-color: {c['primary']}; color: {c['text_inverse']};
                border-radius: 10px; font-weight: bold;
                font-size: 12px; border: none;
            }}
            QPushButton:hover {{
                background-color: {c['primary_hover']};
                color: {c['text_inverse']};
            }}
            QPushButton:pressed {{ background-color: {c['primary_hover']}; }}
            QPushButton:disabled {{
                background-color: {c['border']};
                color: {c['text_muted']};
            }}
        """

    @staticmethod
    def btn_annuler() -> str:
        """Style pour le bouton annuler."""
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                background-color: {c['bg_card']};
                color: {c['danger']};
                border: 1.5px solid {c['danger']};
                border-radius: 10px; font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {c['danger']};
                color: {c['text_inverse']};
                border-color: {c['danger']};
            }}
            QPushButton:pressed {{ background-color: {c['danger']}; }}
            QPushButton:disabled {{
                background-color: {c['border']};
                color: {c['text_muted']};
                border-color: {c['border']};
            }}
        """

    @staticmethod
    def scrollbar() -> str:
        """Style pour les scrollbars."""
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
    def ligne_panier() -> str:
        """Style pour une ligne du panier."""
        c = theme_manager.colors()
        return f"""
            background: {c['bg_card']}; border-radius: 10px;
            border: 1px solid {c['border']};
        """
