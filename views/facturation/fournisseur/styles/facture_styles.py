"""
Styles centralisés pour le module facture_fournisseur.
Responsabilité : Définir tous les styles CSS et couleurs du module.
Pattern : Centralization of Concerns.
"""
from views.shared.theme_manager import theme_manager


class _ThemeColor:
    """Descripteur qui résout une couleur du thème à chaque accès."""
    def __init__(self, key):
        self._key = key
    def __set_name__(self, owner, name):
        self._name = name
    def __get__(self, obj, objtype=None):
        return theme_manager.colors()[self._key]


class FactureStyles:
    """Classe contenant tous les styles du module facture_fournisseur."""

    # Couleurs rétro-compatibles (résolues dynamiquement via theme_manager)
    BLANC          = _ThemeColor('bg_card')
    GRIS_CLAIR     = _ThemeColor('border_light')
    GRIS_FOND      = _ThemeColor('bg_main')
    GRIS_TEXTE     = _ThemeColor('text_muted')
    VERT_PRINCIPAL = _ThemeColor('primary')
    VERT_CLAIR     = _ThemeColor('success_bg')
    VERT_MED       = _ThemeColor('success')
    BLEU           = _ThemeColor('primary')
    BLEU_SOFT      = _ThemeColor('info')
    BLEU_CLAIR     = _ThemeColor('primary_light')
    ROUGE          = _ThemeColor('danger')
    ROUGE_SOFT     = _ThemeColor('danger')
    ROUGE_CLAIR    = _ThemeColor('danger_bg')
    ORANGE         = _ThemeColor('warning')
    ORANGE_SOFT    = _ThemeColor('warning')
    ORANGE_CLAIR   = _ThemeColor('warning_bg')
    VIOLET_SOFT    = _ThemeColor('accent')

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
    def card_produit():
        """Style pour les cards produit."""
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border-radius: 12px;
                border: 1px solid {c['border']};
            }}
        """

    @staticmethod
    def ligne_lot():
        """Style pour les lignes de lot."""
        c = theme_manager.colors()
        return f"""
            background: {c['bg_main']};
            border-radius: 8px;
            border: none;
        """

    # =========================================================================
    # STYLES DES LABELS
    # =========================================================================

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
    def label_valeur(couleur: str, taille: int = 12):
        """Style pour les valeurs affichées."""
        return f"""
            font-size: {taille}px;
            font-weight: 600;
            color: {couleur};
            border: none;
            background: transparent;
        """

    @staticmethod
    def label_badge(couleur_bg: str, couleur_text: str):
        """Style pour les badges."""
        return f"""
            background: {couleur_bg};
            color: {couleur_text};
            border-radius: 6px;
            font-size: 9px;
            font-weight: bold;
            border: none;
            padding: 2px 8px;
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
    # STYLES DES BOUTONS
    # =========================================================================

    @staticmethod
    def bouton_detail():
        """Style pour le bouton détail."""
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                background: {c['info_bg']};
                color: {c['info']};
                border-radius: 8px;
                border: none;
                font-size: 11px;
                font-weight: 600;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background: {c['info']};
                color: {c['text_inverse']};
            }}
        """

    @staticmethod
    def bouton_action(couleur_bg: str, couleur_text: str):
        """Style pour les boutons d'action."""
        return f"""
            QPushButton {{
                background: {couleur_bg};
                color: {couleur_text};
                border-radius: 8px;
                border: none;
                font-size: 11px;
                font-weight: 700;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
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
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']};
                min-height: 20px;
                border-radius: 2px;
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
        return """
            QScrollArea {
                border: none;
                background: transparent;
            }
        """

    # =========================================================================
    # STYLES DES SÉPARATEURS
    # =========================================================================

    @staticmethod
    def separateur(couleur: str = None):
        """Style pour les séparateurs."""
        c = theme_manager.colors()
        couleur = couleur or c['border']
        return f"""
            background: {couleur};
            border: none;
        """

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    @staticmethod
    def transparent():
        """Style transparent."""
        return "background: transparent; border: none;"

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
            "Liquide":   c['info'],
            "Pommade":   c['accent'],
            "Comprimé":  c['warning'],
        }

        return couleurs.get(type_normalise, c['text_primary'])

    @staticmethod
    def obtenir_couleur_statut(statut: str) -> tuple:
        """
        Retourne les couleurs (bg, text) associées à un statut.

        Args:
            statut: Statut (valide, expire, bientot)

        Returns:
            tuple: (couleur_bg, couleur_text)
        """
        c = theme_manager.colors()
        statut_normalise = statut.strip().lower()

        couleurs = {
            "valide":  (c['success_bg'], c['success']),
            "expire":  (c['danger_bg'], c['danger']),
            "bientot": (c['warning_bg'], c['warning']),
        }

        return couleurs.get(statut_normalise, (c['border'], c['text_primary']))
