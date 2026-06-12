"""
Styles centralisés pour le module statistiques.
Responsabilité : Définir tous les styles CSS et couleurs du module.
Pattern : Centralization of Concerns.
"""
from views.shared.theme_manager import theme_manager


class _ThemeColor:
    def __init__(self, key): self._key = key
    def __set_name__(self, owner, name): self._name = name
    def __get__(self, obj, objtype=None): return theme_manager.colors()[self._key]


class StatistiquesStyles:
    """Classe contenant tous les styles du module statistiques."""

    ROUGE            = _ThemeColor('danger')
    ORANGE           = _ThemeColor('warning')
    VERT_CLAIR       = _ThemeColor('success')
    BLEU             = _ThemeColor('primary')
    VERT_PRINCIPAL   = _ThemeColor('primary')
    COULEUR_LIQUIDE  = _ThemeColor('primary')
    COULEUR_POMMADE  = _ThemeColor('warning')
    COULEUR_COMPRIME = _ThemeColor('success')

    # =========================================================================
    # STYLES DES CARDS
    # =========================================================================

    @staticmethod
    def card_base():
        """Style de base pour toutes les cards."""
        c = theme_manager.colors()
        return f"""
            background-color: {c['bg_card']};
            border-radius: 12px;
            border: 1px solid {c['border']};
        """

    @staticmethod
    def card_stat_compact():
        """Style pour les cards statistiques compactes."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border-radius: 14px;
                border: 1px solid {c['border']};
            }}
        """

    @staticmethod
    def card_stat(hauteur: int = 80):
        """Style pour les cards statistiques simples."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border-radius: 12px;
                border: 1px solid {c['border']};
            }}
        """

    @staticmethod
    def card_donut():
        """Style pour les DonutCards."""
        c = theme_manager.colors()
        return f"""
            background-color: {c['bg_card']};
            border-radius: 12px;
            border: 1px solid {c['border']};
        """

    @staticmethod
    def ligne_stock():
        """Style pour les lignes de stock."""
        c = theme_manager.colors()
        return f"""
            background: {c['bg_card']};
            border-radius: 8px;
            border: none;
        """

    # =========================================================================
    # STYLES DES LABELS
    # =========================================================================

    @staticmethod
    def label_titre_compact(font_size: int = 10):
        """Style pour les titres de cards compactes."""
        c = theme_manager.colors()
        return f"""
            font-weight: bold;
            color: {c['text_muted']};
            font-size: {font_size}px;
            border: none;
            background: transparent;
        """

    @staticmethod
    def label_titre():
        """Style pour les titres de cards."""
        c = theme_manager.colors()
        return f"""
            font-weight: bold;
            color: {c['text_muted']};
            font-size: 11px;
            border: none;
            background: transparent;
        """

    @staticmethod
    def label_valeur(couleur: str, taille: int = 20):
        """Style pour les valeurs affichées."""
        return f"""
            font-size: {taille}px;
            font-weight: bold;
            color: {couleur};
            border: none;
            background: transparent;
        """

    @staticmethod
    def label_badge(couleur: str):
        """Style pour les badges."""
        return f"""
            background: {couleur}22;
            color: {couleur};
            border-radius: 6px;
            font-size: 9px;
            font-weight: bold;
            border: none;
        """

    @staticmethod
    def label_vide():
        """Style pour le message 'aucune donnée'."""
        c = theme_manager.colors()
        return f"""
            color: {c['text_muted']};
            font-style: italic;
            font-size: 11px;
            border: none;
            background: transparent;
            padding: 10px;
        """

    # =========================================================================
    # STYLES DES ICÔNES
    # =========================================================================

    @staticmethod
    def icone_base():
        """Style de base pour les icônes."""
        return """
            border: none;
            background: transparent;
        """

    # =========================================================================
    # STYLES DES BARRES
    # =========================================================================

    @staticmethod
    def barre_couleur(couleur: str, hauteur: int = 3):
        """Style pour les barres colorées."""
        return f"""
            background: {couleur};
            border-radius: 2px;
            border: none;
        """

    # =========================================================================
    # STYLES DES SCROLLBARS
    # =========================================================================

    @staticmethod
    def scrollbar():
        """Style pour les scrollbars."""
        c = theme_manager.colors()
        return f"""
            QScrollBar:vertical {{
                border: none;
                background: {c['bg_main']};
                width: 5px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']};
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c['text_muted']};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """

    @staticmethod
    def scroll_area():
        """Style pour les QScrollArea."""
        c = theme_manager.colors()
        return f"""
            QScrollArea {{
                border: none;
                background: {c['bg_card']};
            }}
            QScrollArea > QWidget {{
                background: {c['bg_card']};
            }}
        """

    # =========================================================================
    # STYLES DES PROGRESSBAR (DONUT)
    # =========================================================================

    @staticmethod
    def progressbar_donut(couleur: str, pourcentage: int):
        """Style pour les ProgressBar circulaires (donut)."""
        c = theme_manager.colors()
        return f"""
            QProgressBar {{
                border: 4px solid {c['border_light']};
                border-radius: 30px;
                background: transparent;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: qconicalgradient(
                    cx:0.5, cy:0.5, angle:90,
                    stop:0 {couleur},
                    stop:{pourcentage/100} {couleur},
                    stop:{pourcentage/100 + 0.01} transparent,
                    stop:1 transparent
                );
                border-radius: 26px;
            }}
        """

    @staticmethod
    def label_pourcentage(couleur: str):
        """Style pour le label de pourcentage au centre du donut."""
        return f"""
            font-weight: bold;
            font-size: 14px;
            color: {couleur};
            border: none;
            background: transparent;
        """

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    @staticmethod
    def transparent():
        """Style transparent."""
        return "background: transparent;"

    @staticmethod
    def obtenir_couleur_type(type_produit: str) -> str:
        """
        Retourne la couleur associée à un type de produit.

        Args:
            type_produit: Type de produit (Liquide, Pommade, Comprimé)

        Returns:
            str: Code couleur hexadécimal
        """
        c = theme_manager.colors()
        type_normalise = type_produit.strip().capitalize()

        couleurs = {
            "Liquide": c['info'],
            "Pommade": c['accent'],
            "Comprimé": c['warning'],
        }

        return couleurs.get(type_normalise, c['text_muted'])
