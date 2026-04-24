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

    # ── Thème CLAIR (Teal Medical - professionnel clinique) ──────────────
    "clair": {
        # Couleurs principales — teal médical + bleu secondaire
        "primary":       "#0F7B6C",    # Teal profond (accent principal)
        "primary_hover": "#0A5F53",    # Teal foncé au survol
        "primary_light": "#E6F5F2",    # Teal très clair (hover sidebar)
        "secondary":     "#3B82F6",    # Bleu (variété / liens)
        "accent":        "#F59E0B",    # Ambre chaud (highlights / stat cards)
        "accent_light":  "#FEF3C7",    # Ambre pâle

        # Arrière-plans — nuances de gris-vert très doux
        "bg_main":       "#F0F4F3",    # Fond principal
        "bg_sidebar":    "#FFFFFF",    # Sidebar
        "bg_card":       "#FFFFFF",    # Cartes
        "bg_header":     "#FFFFFF",    # Header
        "bg_input":      "#FAFBFC",    # Champs de saisie
        "bg_table":      "#FFFFFF",    # Tableau
        "bg_table_alt":  "#F7FAF9",    # Ligne alternée

        # Textes — gamme du sombre au clair
        "text_primary":  "#1A2E35",    # Texte principal (sombre)
        "text_secondary":"#5F7A84",    # Sous-titres
        "text_inverse":  "#FFFFFF",    # Sur fond coloré
        "text_muted":    "#94A3B8",    # Légendes discrètes

        # Bordures
        "border":        "#D8E2E0",
        "border_light":  "#E8EDEC",
        "border_focus":  "#0F7B6C",

        # États interactifs
        "hover":         "#EFF5F4",
        "selected":      "#0F7B6C",
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
        "shadow":        "rgba(15, 123, 108, 0.08)",
        "shadow_hover":  "rgba(15, 123, 108, 0.15)",

        # Tableau
        "table_header_bg":    "#F8FAF9",
        "table_header_border":"#0F7B6C",
        "table_selection":    "#E6F5F2",
        "table_gridline":     "#F0F4F3",

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

        "bg_main":       "#0F1419",
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

        "_name":  "Sombre",
        "_icon":  "fa5s.moon",
    },

    # ── Thème OCEAN (Bleu Royal médical) ─────────────────────────────────
    "ocean": {
        "primary":       "#1D6FD6",    # Bleu royal
        "primary_hover": "#1557B0",
        "primary_light": "#EBF4FF",
        "secondary":     "#0EA5E9",    # Bleu ciel
        "accent":        "#8B5CF6",    # Violet doux
        "accent_light":  "#F0EBFF",

        "bg_main":       "#EFF5FB",
        "bg_sidebar":    "#FFFFFF",
        "bg_card":       "#FFFFFF",
        "bg_header":     "#FFFFFF",
        "bg_input":      "#F8FAFD",
        "bg_table":      "#FFFFFF",
        "bg_table_alt":  "#F5F9FD",

        "text_primary":  "#1A2744",
        "text_secondary":"#4A6284",
        "text_inverse":  "#FFFFFF",
        "text_muted":    "#8FA3BF",

        "border":        "#D2E3F3",
        "border_light":  "#E3EDF7",
        "border_focus":  "#1D6FD6",

        "hover":         "#E3EEFB",
        "selected":      "#1D6FD6",
        "danger":        "#DC2626",
        "warning":       "#F59E0B",
        "success":       "#059669",
        "info":          "#0284C7",

        "danger_bg":     "#FEF2F2",
        "warning_bg":    "#FFFBEB",
        "success_bg":    "#ECFDF5",
        "info_bg":       "#E0F2FE",

        "shadow":        "rgba(29, 111, 214, 0.08)",
        "shadow_hover":  "rgba(29, 111, 214, 0.15)",

        "table_header_bg":    "#F5F9FD",
        "table_header_border":"#1D6FD6",
        "table_selection":    "#EBF4FF",
        "table_gridline":     "#EDF2F7",

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
