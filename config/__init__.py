"""Package de configuration du système."""

import qtawesome as qta

class Config:
    APP_NAME = "OphthalmoPro v1.0"
    PRIMARY_COLOR = "#006633"
    # --- THÈME CLAIR (Par défaut) ---
    LIGHT_THEME = {
        "sidebar_bg": "#FFFFFF",
        "content_bg": "#F4F7F6",
        "text_main": "#2C3E50",
        "accent": "#006633",
        "hover": "#E8F5E9",
        "border": "#DCDDE1"
    }

    # --- THÈME SOMBRE ---
    DARK_THEME = {
        "sidebar_bg": "#1A1A2E",
        "content_bg": "#16213E",
        "text_main": "#EAEAEA",
        "accent": "#2ECC71",
        "hover": "#0F3460",
        "border": "#252545"
    }

    # Icônes (Utilisation de FontAwesome)
    ICONS = {
        "eye": "fa5s.eye",
        "patient": "fa5s.user-injured",
        "consult": "fa5s.stethoscope",
        "exam": "fa5s.microscope",
        "stats": "fa5s.chart-line",
        "light_mode": "fa5s.sun",
        "dark_mode": "fa5s.moon",
        "logout": "fa5s.sign-out-alt"
    }
