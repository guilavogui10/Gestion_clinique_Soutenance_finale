"""
Styles centralisés pour la vue Acte Médical.
"""
from views.shared.theme_manager import theme_manager


def get_styles():
    c = theme_manager.colors()
    return f"""
        QFrame#MainWhiteFrame {{
            background-color: {c['bg_card']};
            border-radius: 16px;
            border: 1px solid {c['border']};
        }}
        QTabWidget::pane {{
            border: none;
            background: {c['bg_card']};
        }}
        QTabBar::tab {{
            background: {c['bg_main']};
            color: {c['text_secondary']};
            padding: 10px 20px;
            border: none;
            font-size: 13px;
            font-weight: 500;
            min-width: 140px;
        }}
        QTabBar::tab:selected {{
            background: {c['bg_card']};
            color: {c['primary']};
            font-weight: bold;
            border-bottom: 2px solid {c['primary']};
        }}
        QTabBar::tab:hover {{
            background: {c['primary_light']};
            color: {c['primary']};
        }}
    """
