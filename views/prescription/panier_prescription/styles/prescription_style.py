"""
Styles CSS centralisés pour le widget prescription.
Architecture : Séparation des préoccupations (Separation of Concerns).
Palette médicale — bleu marine professionnel.
"""
from views.shared.theme_manager import theme_manager


class _ThemeColor:
    def __init__(self, key): self._key = key
    def __set_name__(self, owner, name): self._name = name
    def __get__(self, obj, objtype=None): return theme_manager.colors()[self._key]


class PrescriptionStyles:
    """Classe contenant tous les styles CSS du widget prescription."""

    BLEU_PRINCIPAL = _ThemeColor('primary')
    ROUGE          = _ThemeColor('danger')

    # -------------------------------------------------------------------------
    # Combos
    # -------------------------------------------------------------------------

    @staticmethod
    def combo_produit() -> str:
        """Style pour le combo produit."""
        c = theme_manager.colors()
        return f"""
            QComboBox {{
                border-radius: 10px;
                border: 2px solid {c['border_light']};
                padding-left: 10px;
                background: {c['bg_input']};
                font-size: 12px;
                color: {c['text_primary']};
            }}
            QComboBox:focus {{ border: 2px solid {c['primary']}; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
            QComboBox QAbstractItemView {{
                border-radius: 8px;
                border: 1px solid {c['border']};
                selection-background-color: {c['primary']}20;
            }}
        """

    # -------------------------------------------------------------------------
    # Champs de saisie
    # -------------------------------------------------------------------------

    @staticmethod
    def input_readonly() -> str:
        """Style pour les champs en lecture seule (auto-remplis)."""
        c = theme_manager.colors()
        return (
            f"border-radius: 8px; border: 1px solid {c['border']};"
            f"padding-left: 12px; background: {c['bg_input']}; font-size: 12px; color: {c['text_muted']};"
        )

    @staticmethod
    def input_normal() -> str:
        """Style pour les champs normaux."""
        c = theme_manager.colors()
        return (
            f"border-radius: 8px; border: 1px solid {c['border']};"
            f"padding-left: 12px; background: {c['bg_card']}; font-size: 12px;"
        )

    @staticmethod
    def input_valide() -> str:
        """Style pour les champs valides (vert)."""
        c = theme_manager.colors()
        return (
            f"border-radius: 8px; border: 2px solid {c['success']};"
            f"padding-left: 12px; background: {c['success_bg']}; font-size: 12px;"
        )

    @staticmethod
    def input_invalide() -> str:
        """Style pour les champs invalides (rouge)."""
        c = theme_manager.colors()
        return (
            f"border-radius: 8px; border: 2px solid {c['danger']};"
            f"padding-left: 12px; background: {c['danger_bg']}; font-size: 12px;"
        )

    # -------------------------------------------------------------------------
    # Carte patient (info-display readonly)
    # -------------------------------------------------------------------------

    @staticmethod
    def patient_card() -> str:
        """Style pour la carte d'information patient."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {c['bg_main']},
                    stop:1 {c['bg_input']}
                );
                border-radius: 10px;
                border: 1.5px solid {c['primary']};
            }}
        """

    # -------------------------------------------------------------------------
    # Boutons
    # -------------------------------------------------------------------------

    @staticmethod
    def btn_prescrire_modern() -> str:
        """Style moderne pour le bouton 'Prescrire ce produit'."""
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                background: {c['primary']};
                color: {c['text_inverse']};
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
                border: none;
                padding: 8px 20px;
            }}
            QPushButton:hover {{ background: {c['primary_hover']}; }}
            QPushButton:pressed  {{ background-color: {c['primary_hover']}; }}
            QPushButton:disabled {{
                background: {c['border']};
                color: {c['text_muted']};
            }}
        """

    @staticmethod
    def btn_valider() -> str:
        """Style pour le bouton valider la prescription."""
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {c['success']};
                border: 2px solid {c['success']};
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {c['success_bg']};
            }}
            QPushButton:pressed {{
                background-color: {c['success']};
                color: {c['text_inverse']};
            }}
            QPushButton:disabled {{
                background-color: transparent;
                border-color: {c['border']};
                color: {c['text_muted']};
            }}
        """

    @staticmethod
    def btn_annuler() -> str:
        """Style pour le bouton annuler."""
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {c['danger']};
                border: 2px solid {c['danger']};
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {c['danger_bg']};
            }}
            QPushButton:pressed {{
                background-color: {c['danger']};
                color: {c['text_inverse']};
            }}
        """

    # -------------------------------------------------------------------------
    # Scrollbar
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # Ligne prescription
    # -------------------------------------------------------------------------

    @staticmethod
    def ligne_prescription() -> str:
        """Style de base pour une ligne du panier prescription."""
        c = theme_manager.colors()
        return f"""
            background: {c['bg_main']}; border-radius: 10px;
            border: 1px solid {c['border']};
        """