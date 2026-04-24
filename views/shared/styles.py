"""
=============================================================================
 STYLES GLOBAUX - Bibliotheque QSS Dynamique (Clinique Medicale)
=============================================================================
 Fonctions QSS dynamiques liees au ThemeManager.
 Palette professionnelle clinique : teal, bleu, ambre + gammes de gris.
=============================================================================
"""

from views.shared.theme_manager import theme_manager


class Styles:

    # -- BOUTONS ----------------------------------------------------------

    @staticmethod
    def button_primary():
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
                border: none;
                border-radius: 10px;
                padding: 9px 20px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {c['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {c['primary_hover']};
                padding-top: 11px;
            }}
            QPushButton:disabled {{
                background-color: {c['border']};
                color: {c['text_muted']};
            }}
        """

    @staticmethod
    def button_secondary():
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
                padding: 9px 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {c['primary_light']};
                border-color: {c['primary']};
                color: {c['primary']};
            }}
            QPushButton:pressed {{
                background-color: {c['primary_light']};
            }}
        """

    @staticmethod
    def button_danger():
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                background-color: {c['danger']};
                color: {c['text_inverse']};
                border: none;
                border-radius: 10px;
                padding: 9px 20px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
        """

    @staticmethod
    def button_success():
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                background-color: {c['success']};
                color: {c['text_inverse']};
                border: none;
                border-radius: 10px;
                padding: 9px 20px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
        """

    @staticmethod
    def button_icon(size=36):
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                background-color: transparent;
                border: 1.5px solid {c['border']};
                border-radius: {size // 2}px;
                min-width: {size}px; max-width: {size}px;
                min-height: {size}px; max-height: {size}px;
            }}
            QPushButton:hover {{
                background-color: {c['primary_light']};
                border-color: {c['primary']};
            }}
        """

    @staticmethod
    def button_table_action():
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                border: 1px solid {c['border_light']};
                border-radius: 6px;
                background: {c['bg_card']};
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {c['primary_light']};
                border-color: {c['primary']};
            }}
        """

    # -- CHAMPS DE SAISIE -------------------------------------------------

    @staticmethod
    def input_field():
        c = theme_manager.colors()
        return f"""
            QLineEdit, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTimeEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
                padding: 9px 14px;
                font-size: 13px;
            }}
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus,
            QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {{
                border: 2px solid {c['border_focus']};
                background-color: {c['bg_card']};
            }}
            QComboBox::drop-down {{ border: none; padding-right: 10px; }}
            QComboBox QAbstractItemView {{
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                selection-background-color: {c['primary_light']};
                selection-color: {c['primary']};
                padding: 4px;
            }}
            QTextEdit, QPlainTextEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
                padding: 10px;
                font-size: 13px;
            }}
            QTextEdit:focus, QPlainTextEdit:focus {{
                border: 2px solid {c['border_focus']};
                background-color: {c['bg_card']};
            }}
        """

    @staticmethod
    def search_bar():
        c = theme_manager.colors()
        return f"""
            QLineEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1.5px solid {c['border']};
                border-radius: 12px;
                padding: 10px 16px 10px 40px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {c['border_focus']};
                background-color: {c['bg_card']};
            }}
        """

    @staticmethod
    def label_form():
        c = theme_manager.colors()
        return f"color: {c['text_secondary']}; font-size: 12px; font-weight: 600;"

    # -- TABLEAUX ---------------------------------------------------------

    @staticmethod
    def table():
        c = theme_manager.colors()
        return f"""
            QTableWidget {{
                background-color: {c['bg_table']};
                alternate-background-color: {c['bg_table_alt']};
                color: {c['text_primary']};
                border: none;
                border-radius: 10px;
                gridline-color: {c['table_gridline']};
                selection-background-color: {c['table_selection']};
                font-size: 13px;
            }}
            QTableWidget::item {{ padding: 4px; }}
            QTableWidget::item:selected {{
                background-color: {c['table_selection']};
                color: {c['text_primary']};
            }}
            QHeaderView::section {{
                background-color: {c['table_header_bg']};
                color: {c['primary']};
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid {c['table_header_border']};
                font-weight: bold;
                font-size: 12px;
            }}
            QHeaderView {{ background-color: {c['bg_table']}; }}
        """

    # -- CARTES & FRAMES --------------------------------------------------

    @staticmethod
    def card():
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border-radius: 15px;
                border: 1px solid {c['border_light']};
            }}
            QFrame > QFrame {{ background-color: transparent; border: none; border-radius: 0px; }}
            QFrame > QWidget {{ background-color: transparent; border: none; }}
            QLabel {{ background-color: transparent; border: none; }}
        """

    @staticmethod
    def stat_card_style(accent_color=""):
        c = theme_manager.colors()
        accent = accent_color or c['primary']
        return f"""
            QFrame#StatCard {{
                background-color: {c['bg_card']};
                border-radius: 16px;
                border: 1px solid {c['border_light']};
                border-left: 4px solid {accent};
            }}
            QFrame#StatCard QLabel {{ background-color: transparent; border: none; }}
        """

    @staticmethod
    def container():
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_card']};
                border-radius: 15px;
                border: 1px solid {c['border']};
            }}
        """

    # -- MENUS CONTEXTUELS ------------------------------------------------

    @staticmethod
    def menu():
        c = theme_manager.colors()
        return f"""
            QMenu {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 10px 30px 10px 20px;
                color: {c['text_primary']};
                border-radius: 6px;
            }}
            QMenu::item:selected {{
                background-color: {c['primary_light']};
                color: {c['primary']};
            }}
            QMenu::icon {{ padding-left: 10px; }}
            QMenu::separator {{
                height: 1px;
                background: {c['border_light']};
                margin: 4px 10px;
            }}
        """

    # -- SIDEBAR & NAVIGATION ---------------------------------------------

    @staticmethod
    def sidebar():
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['bg_sidebar']};
                border-right: 1px solid {c['border_light']};
            }}
        """

    @staticmethod
    def nav_button():
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                text-align: left;
                padding: 12px 20px;
                border: none;
                color: {c['text_secondary']};
                border-radius: 10px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {c['primary_light']};
                color: {c['primary']};
            }}
            QPushButton:checked {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
                font-weight: 600;
            }}
        """

    @staticmethod
    def theme_button():
        c = theme_manager.colors()
        return f"""
            QPushButton {{
                border-radius: 12px;
                border: 1.5px solid {c['border']};
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {c['primary_light']};
                border-color: {c['primary']};
                color: {c['primary']};
            }}
        """

    # -- ZONES DE CONTENU -------------------------------------------------

    @staticmethod
    def content_area():
        c = theme_manager.colors()
        return f"background-color: {c['bg_main']}; color: {c['text_primary']};"

    @staticmethod
    def header():
        c = theme_manager.colors()
        return f"background-color: {c['bg_header']}; color: {c['text_primary']};"

    @staticmethod
    def footer():
        c = theme_manager.colors()
        return f"""
            background-color: {c['primary']};
            border-radius: 14px;
            margin: 6px;
            color: {c['text_inverse']};
        """

    # -- LABELS & TEXTES --------------------------------------------------

    @staticmethod
    def title():
        c = theme_manager.colors()
        return f"color: {c['text_primary']}; font-size: 20px; font-weight: bold;"

    @staticmethod
    def subtitle():
        c = theme_manager.colors()
        return f"color: {c['text_secondary']}; font-size: 14px;"

    @staticmethod
    def label_value():
        c = theme_manager.colors()
        return f"color: {c['text_primary']}; font-size: 22px; font-weight: bold;"

    @staticmethod
    def label_caption():
        c = theme_manager.colors()
        return f"color: {c['text_muted']}; font-size: 12px;"

    # -- DIALOGUES --------------------------------------------------------

    @staticmethod
    def dialog():
        c = theme_manager.colors()
        return f"background-color: {c['bg_card']}; color: {c['text_primary']};"

    @staticmethod
    def dialog_header():
        c = theme_manager.colors()
        return f"""
            background-color: {c['primary']};
            color: {c['text_inverse']};
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            padding: 18px;
        """

    @staticmethod
    def dialog_full():
        c = theme_manager.colors()
        return f"""
            QDialog {{
                background-color: {c['bg_card']};
                color: {c['text_primary']};
            }}
            QLabel {{ color: {c['text_primary']}; background: transparent; border: none; }}
            QLineEdit, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox,
            QTimeEdit, QTextEdit, QPlainTextEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1.5px solid {c['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus,
            QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus,
            QTextEdit:focus, QPlainTextEdit:focus {{
                border: 2px solid {c['border_focus']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                selection-background-color: {c['primary_light']};
                selection-color: {c['primary']};
            }}
            QGroupBox {{
                background-color: transparent;
                border: 1px solid {c['border_light']};
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 16px;
                font-weight: 600;
                color: {c['text_secondary']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: {c['primary']};
            }}
            QCheckBox, QRadioButton {{ color: {c['text_primary']}; spacing: 8px; }}
            QCheckBox::indicator, QRadioButton::indicator {{
                width: 18px; height: 18px;
                border: 2px solid {c['border']};
                border-radius: 4px;
                background-color: {c['bg_input']};
            }}
            QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
                background-color: {c['primary']};
                border-color: {c['primary']};
            }}
            QRadioButton::indicator {{ border-radius: 9px; }}
        """

    # -- BARRE D'ACTIONS --------------------------------------------------

    @staticmethod
    def action_bar():
        c = theme_manager.colors()
        return f"""
            QFrame {{
                background-color: {c['primary']};
                border-radius: 12px;
            }}
            QPushButton {{
                background-color: transparent;
                color: {c['text_inverse']};
                border: none;
                font-weight: 600;
                padding: 0px 15px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.12);
                border-radius: 8px;
            }}
            QPushButton::menu-indicator {{ image: none; }}
        """

    # -- BADGES -----------------------------------------------------------

    @staticmethod
    def badge_success():
        c = theme_manager.colors()
        return f"""
            background-color: {c['success_bg']};
            color: {c['success']};
            border-radius: 10px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 700;
        """

    @staticmethod
    def badge_warning():
        c = theme_manager.colors()
        return f"""
            background-color: {c['warning_bg']};
            color: {c['warning']};
            border-radius: 10px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 700;
        """

    @staticmethod
    def badge_danger():
        c = theme_manager.colors()
        return f"""
            background-color: {c['danger_bg']};
            color: {c['danger']};
            border-radius: 10px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 700;
        """

    @staticmethod
    def badge_info():
        c = theme_manager.colors()
        return f"""
            background-color: {c['info_bg']};
            color: {c['info']};
            border-radius: 10px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 700;
        """

    # -- SCROLLBARS -------------------------------------------------------

    @staticmethod
    def scrollbar():
        c = theme_manager.colors()
        return f"""
            QScrollBar:vertical {{
                background: transparent; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']}; border-radius: 4px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {c['primary']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar:horizontal {{
                background: transparent; height: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {c['border']}; border-radius: 4px; min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{ background: {c['primary']}; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
        """

    # -- TABS -------------------------------------------------------------

    @staticmethod
    def tab_widget():
        c = theme_manager.colors()
        return f"""
            QTabWidget::pane {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border_light']};
                border-radius: 10px;
                padding: 8px;
            }}
            QTabBar::tab {{
                background-color: {c['bg_main']};
                color: {c['text_secondary']};
                border: none;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 500;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {c['bg_card']};
                color: {c['primary']};
                font-weight: 600;
                border-bottom: 2px solid {c['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {c['hover']};
                color: {c['text_primary']};
            }}
        """

    # -- TOOLTIP ----------------------------------------------------------

    @staticmethod
    def tooltip():
        c = theme_manager.colors()
        return f"""
            QToolTip {{
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }}
        """

    # -- MESSAGE BOX ------------------------------------------------------

    @staticmethod
    def message_box(is_success=True):
        c = theme_manager.colors()
        accent = c['success'] if is_success else c['danger']
        return {
            "frame": f"""
                QFrame {{
                    background-color: {c['bg_card']};
                    border: 2px solid {accent};
                    border-radius: 15px;
                }}
            """,
            "title": f"font-size: 18px; font-weight: bold; color: {accent};",
            "message": f"font-size: 14px; color: {c['text_primary']};",
            "button": f"""
                QPushButton {{
                    background-color: {accent};
                    color: {c['text_inverse']};
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {c['primary_hover']};
                }}
            """,
            "accent": accent,
        }

    # -- GRAPHIQUES -------------------------------------------------------

    @staticmethod
    def graph_colors():
        c = theme_manager.colors()
        return {
            "primary": c['primary'],
            "secondary": c['secondary'],
            "accent": c['accent'],
            "success": c['success'],
            "info": c['info'],
            "text": c['text_primary'],
            "text_muted": c['text_muted'],
            "grid": c['border_light'],
            "bg": c['bg_card'],
            "title": c['primary'],
            "series": [c['primary'], c['secondary'], c['accent'],
                       c['success'], c['info'], c['danger']],
        }

    # -- QSS GLOBAL -------------------------------------------------------

    @staticmethod
    def global_qss():
        c = theme_manager.colors()
        return f"""
            QWidget {{
                background-color: {c['bg_main']};
                color: {c['text_primary']};
                font-family: "Segoe UI", "Inter", sans-serif;
            }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
            QDateEdit, QTimeEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                border: 1.5px solid {c['border']};
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
            QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {{
                border: 2px solid {c['border_focus']};
            }}
            QLabel {{ background: transparent; border: none; }}
            QFrame#StatCard, QFrame#cardFrame {{
                background-color: {c['bg_card']};
                border-radius: 16px;
                border: 1px solid {c['border_light']};
            }}
            QTableWidget {{
                background-color: {c['bg_table']};
                alternate-background-color: {c['bg_table_alt']};
                border: none;
                border-radius: 10px;
                gridline-color: {c['table_gridline']};
                selection-background-color: {c['table_selection']};
                color: {c['text_primary']};
            }}
            QHeaderView::section {{
                background-color: {c['table_header_bg']};
                color: {c['primary']};
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid {c['table_header_border']};
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton#BtnAdd {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
                border-radius: 10px;
                padding: 9px 18px;
                font-weight: 600;
            }}
            QPushButton#BtnAdd:hover {{ background-color: {c['primary_hover']}; }}
            QScrollBar:vertical {{
                background: transparent; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']}; border-radius: 4px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {c['primary']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar:horizontal {{
                background: transparent; height: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {c['border']}; border-radius: 4px; min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{ background: {c['primary']}; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
            QToolTip {{
                background-color: {c['bg_card']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QMenu {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                color: {c['text_primary']};
                border-radius: 6px;
            }}
            QMenu::item:selected {{
                background-color: {c['primary_light']};
                color: {c['primary']};
            }}
            QMessageBox {{ background-color: {c['bg_card']}; }}
            QMessageBox QLabel {{ color: {c['text_primary']}; }}
            QMessageBox QPushButton {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 600;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{ background-color: {c['primary_hover']}; }}
        """
