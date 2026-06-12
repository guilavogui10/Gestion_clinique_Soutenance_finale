"""
=============================================================================
 GESTIONNAIRE DE THÈMES - Vue Centralisée
=============================================================================
 Singleton qui gère les 3 modes de couleur de l'application :
   1. CLAIR  (Light)  - Vert classique, fond blanc
   2. SOMBRE (Dark)   - Fond sombre, accents verts lumineux
   3. OCEAN  (Ocean)  - Bleu professionnel, fond bleu clair

 Utilisation :
   from views.shared.theme_manager import theme_manager
   theme_manager.set_theme("sombre")
   couleurs = theme_manager.colors()
=============================================================================
"""

from PySide6.QtCore import QObject, Signal


# ─────────────────────────────────────────────────────────────────────────────
# PALETTES DE COULEURS
# ─────────────────────────────────────────────────────────────────────────────

THEMES = {

    # ── Thème CLAIR (Medical Teal - palette login) ───────────────────────
    "clair": {
        # Couleurs principales — teal lumineux du login
        "primary":       "#3ECFCF",    # Teal vif (boutons login)
        "primary_hover": "#35B8B8",    # Teal hover
        "primary_light": "#E6FAFA",    # Teal très clair (hover sidebar)
        "secondary":     "#3D9B9B",    # Teal lien (liens login)
        "accent":        "#F59E0B",    # Ambre chaud (stat cards)
        "accent_light":  "#FEF3C7",    # Ambre pâle

        # Arrière-plans — homogènes teal très pâle
        "bg_main":       "#F4FAFA",    # Fond principal (teal très pâle)
        "bg_sidebar":    "#0d5f5a",    # Sidebar — teal profond
        "bg_card":       "#F4FAFA",    # Cartes (identique)
        "bg_header":     "#F4FAFA",    # Header (identique)
        "bg_input":      "#F8F9FA",    # Champs de saisie
        "bg_table":      "#F4FAFA",    # Tableau (identique)
        "bg_table_alt":  "#F0FAFA",    # Ligne alternée teal pâle

        # Textes — palette login
        "text_primary":  "#2C3E50",    # Texte principal (titre login)
        "text_secondary":"#7F8C8D",    # Sous-titres (sous-titre login)
        "text_inverse":  "#FFFFFF",    # Sur fond coloré
        "text_muted":    "#95A5A6",    # Légendes (placeholder login)

        # Bordures
        "border":        "#B0B8C0",    # Bordure grise visible
        "border_light":  "#D0D4D8",    # Bordure légère
        "border_focus":  "#3ECFCF",    # Focus = teal vif login

        # États interactifs
        "hover":         "#E6FAFA",
        "selected":      "#3ECFCF",
        "danger":        "#EF4444",
        "warning":       "#F59E0B",
        "success":       "#10B981",
        "info":          "#3B82F6",

        # Fonds légers pour badges
        "danger_bg":     "#FEF2F2",
        "warning_bg":    "#FFFBEB",
        "success_bg":    "#ECFDF5",
        "info_bg":       "#EFF6FF",

        # Ombres
        "shadow":        "rgba(62, 207, 207, 0.08)",
        "shadow_hover":  "rgba(62, 207, 207, 0.18)",

        # Tableau
        "table_header_bg":    "#F0FAFA",
        "table_header_border":"#3ECFCF",
        "table_selection":    "#E6FAFA",
        "table_gridline":     "#F4FAFA",

        # Texte sidebar (blanc car bg_sidebar est sombre)
        "text_sidebar":  "#FFFFFF",
        "hover_sidebar": "rgba(255,255,255,0.12)",

        # Métadonnées
        "_name":  "Clair",
        "_icon":  "fa5s.sun",
    },

    # ── Thème SOMBRE (Deep Blue-Gray + Teal lumineux) ────────────────────
    "sombre": {
        "primary":       "#2DD4BF",    # Teal lumineux
        "primary_hover": "#14B8A6",
        "primary_light": "#1A3038",
        "secondary":     "#60A5FA",    # Bleu vif
        "accent":        "#FBBF24",    # Or chaud
        "accent_light":  "#3D3520",

        "bg_main":       "#1C2330",    # Fond principal (identique aux cards pour homogénéité)
        "bg_sidebar":    "#151C24",
        "bg_card":       "#1C2430",
        "bg_header":     "#151C24",
        "bg_input":      "#243040",
        "bg_table":      "#1C2430",
        "bg_table_alt":  "#222D3A",

        "text_primary":  "#E8EDF2",
        "text_secondary":"#8899AA",
        "text_inverse":  "#FFFFFF",
        "text_muted":    "#5C6F82",

        "border":        "#2A3645",
        "border_light":  "#243040",
        "border_focus":  "#2DD4BF",

        "hover":         "#243040",
        "selected":      "#2DD4BF",
        "danger":        "#F87171",
        "warning":       "#FBBF24",
        "success":       "#34D399",
        "info":          "#60A5FA",

        "danger_bg":     "#3D1F1F",
        "warning_bg":    "#3D3520",
        "success_bg":    "#1A3D2E",
        "info_bg":       "#1A2D45",

        "shadow":        "rgba(0, 0, 0, 0.35)",
        "shadow_hover":  "rgba(0, 0, 0, 0.50)",

        "table_header_bg":    "#222D3A",
        "table_header_border":"#2DD4BF",
        "table_selection":    "#1A3038",
        "table_gridline":     "#2A3645",

        # Texte sidebar (clair car bg_sidebar est sombre)
        "text_sidebar":  "#E8EDF2",
        "hover_sidebar": "rgba(255,255,255,0.08)",

        "_name":  "Sombre",
        "_icon":  "fa5s.moon",
    },

    # ── Thème OCEAN (Tech Blue — Génie Informatique) ─────────────────────
    "ocean": {
        # Bleu électrique tech — signature génie informatique (Azure, GitHub, Bootstrap)
        "primary":       "#2563EB",    # Bleu tech vif (Tailwind blue-600)
        "primary_hover": "#1D4ED8",    # Bleu plus sombre au survol
        "primary_light": "#DBEAFE",    # Bleu très clair (hover, sélection)
        "secondary":     "#0EA5E9",    # Cyan tech (variété / liens)
        "accent":        "#7C3AED",    # Violet code (accent tech)
        "accent_light":  "#EDE9FE",    # Violet pâle

        # Arrière-plans — homogènes
        "bg_main":       "#F0F7FF",    # Fond principal (identique aux cards)
        "bg_sidebar":    "#0F1F3D",    # Sidebar navy profond
        "bg_card":       "#F0F7FF",    # Cartes
        "bg_header":     "#FFFFFF",    # Header blanc (contraste propre)
        "bg_input":      "#FAFCFF",    # Champs — quasi-blanc teinté bleu
        "bg_table":      "#F0F7FF",    # Tableau
        "bg_table_alt":  "#E5EFFF",    # Ligne alternée — bleu légèrement plus marqué

        # Textes
        "text_primary":  "#1E3A5F",    # Navy profond (lisible sur fond clair)
        "text_secondary":"#4A6080",    # Bleu-gris secondaire
        "text_inverse":  "#FFFFFF",    # Sur fond coloré
        "text_muted":    "#8BA3C0",    # Bleu pâle discret

        # Bordures
        "border":        "#C7D9F0",    # Bordure bleutée
        "border_light":  "#DDE9F8",    # Bordure légère
        "border_focus":  "#2563EB",    # Focus bleu tech

        # États interactifs
        "hover":         "#DBEAFE",    # Hover bleu clair
        "selected":      "#2563EB",
        "danger":        "#DC2626",
        "warning":       "#D97706",
        "success":       "#059669",
        "info":          "#0EA5E9",

        # Fonds légers pour badges
        "danger_bg":     "#FEF2F2",
        "warning_bg":    "#FFFBEB",
        "success_bg":    "#ECFDF5",
        "info_bg":       "#E0F2FE",

        # Ombres
        "shadow":        "rgba(37, 99, 235, 0.10)",
        "shadow_hover":  "rgba(37, 99, 235, 0.20)",

        # Tableau
        "table_header_bg":    "#E5EFFF",    # En-tête — bleu légèrement plus marqué
        "table_header_border":"#2563EB",
        "table_selection":    "#DBEAFE",
        "table_gridline":     "#D5E8FF",    # Grille bleutée visible

        # Texte sidebar (clair car bg_sidebar est navy foncé)
        "text_sidebar":  "#B8CEED",    # Bleu-blanc sur fond navy
        "hover_sidebar": "rgba(37, 99, 235, 0.20)",

        "_name":  "Océan",
        "_icon":  "fa5s.water",
    },
}

# Liste ordonnée pour le cycle de basculement
THEME_ORDER = ["clair", "sombre", "ocean"]


# ─────────────────────────────────────────────────────────────────────────────
# SINGLETON ThemeManager
# ─────────────────────────────────────────────────────────────────────────────

class ThemeManager(QObject):
    """
    Gestionnaire centralisé des thèmes.
    Émet `theme_changed` à chaque changement pour que toutes les vues
    puissent se mettre à jour dynamiquement.
    """

    # Signal émis avec le nom du nouveau thème ("clair", "sombre", "ocean")
    theme_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._current = "clair"

    # ── Accès au thème courant ───────────────────────────────────────────

    @property
    def current(self) -> str:
        """Nom du thème actif ('clair', 'sombre', 'ocean')."""
        return self._current

    def colors(self) -> dict:
        """Retourne le dictionnaire de couleurs du thème actif."""
        return THEMES[self._current]

    def color(self, key: str) -> str:
        """Raccourci pour obtenir une couleur spécifique du thème actif."""
        return THEMES[self._current][key]

    # ── Changement de thème ──────────────────────────────────────────────

    def set_theme(self, name: str):
        """Active un thème par son nom."""
        if name in THEMES and name != self._current:
            self._current = name
            self.theme_changed.emit(name)

    def next_theme(self):
        """Bascule vers le thème suivant dans le cycle."""
        idx = THEME_ORDER.index(self._current)
        next_idx = (idx + 1) % len(THEME_ORDER)
        self.set_theme(THEME_ORDER[next_idx])

    # ── Utilitaires ──────────────────────────────────────────────────────

    def is_dark(self) -> bool:
        """Vrai si le thème actif est sombre (pour adapter les icônes)."""
        return self._current == "sombre"

    def theme_display_name(self) -> str:
        """Nom d'affichage du thème courant."""
        return THEMES[self._current]["_name"]

    def theme_icon(self) -> str:
        """Nom de l'icône qtawesome du thème courant."""
        return THEMES[self._current]["_icon"]

    def next_theme_name(self) -> str:
        """Nom d'affichage du prochain thème (pour le bouton)."""
        idx = THEME_ORDER.index(self._current)
        next_idx = (idx + 1) % len(THEME_ORDER)
        return THEMES[THEME_ORDER[next_idx]]["_name"]

    def next_theme_icon(self) -> str:
        """Icône du prochain thème (pour le bouton)."""
        idx = THEME_ORDER.index(self._current)
        next_idx = (idx + 1) % len(THEME_ORDER)
        return THEMES[THEME_ORDER[next_idx]]["_icon"]


# ── Instance unique (Singleton) ──────────────────────────────────────────────
theme_manager = ThemeManager()
