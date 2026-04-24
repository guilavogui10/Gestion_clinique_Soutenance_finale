"""
Palette de couleurs dynamique pour les modals de détail.
Lit les couleurs du thème courant à chaque accès.
Usage:
    from views.shared.modal_theme import MC
    # MC.BG_CARD → couleur bg_card du thème actif
"""
from views.shared.theme_manager import theme_manager


class _ThemeColor:
    def __init__(self, key):
        self._key = key
    def __set_name__(self, owner, name):
        self._name = name
    def __get__(self, obj, objtype=None):
        return theme_manager.colors()[self._key]


class MC:
    """Modal Colors — descriptors dynamiques liés au thème courant."""
    BG_CARD      = _ThemeColor('bg_card')
    BG_MAIN      = _ThemeColor('bg_main')
    BG_INPUT     = _ThemeColor('bg_input')
    BORDER       = _ThemeColor('border')
    BORDER_LIGHT = _ThemeColor('border_light')
    TEXT_PRIMARY  = _ThemeColor('text_primary')
    TEXT_SECONDARY = _ThemeColor('text_secondary')
    TEXT_MUTED    = _ThemeColor('text_muted')
    TEXT_INVERSE  = _ThemeColor('text_inverse')
    PRIMARY       = _ThemeColor('primary')
    PRIMARY_LIGHT = _ThemeColor('primary_light')
    PRIMARY_HOVER = _ThemeColor('primary_hover')
    SUCCESS       = _ThemeColor('success')
    SUCCESS_BG    = _ThemeColor('success_bg')
    DANGER        = _ThemeColor('danger')
    DANGER_BG     = _ThemeColor('danger_bg')
    WARNING       = _ThemeColor('warning')
    WARNING_BG    = _ThemeColor('warning_bg')
    INFO          = _ThemeColor('info')
    ACCENT        = _ThemeColor('accent')
    HOVER         = _ThemeColor('hover')
