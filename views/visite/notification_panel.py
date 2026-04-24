# Standard library imports
import logging
from datetime import datetime

# Third-party imports
import qtawesome as qta
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QGraphicsDropShadowEffect,
    QSizePolicy
)

from views.shared.theme_manager import theme_manager


# ─────────────────────────────────────────────
#  PALETTE (dynamique via thème)
# ─────────────────────────────────────────────
class AlertColors:
    """Couleurs des alertes — sémantiques, adaptées au thème courant."""

    @staticmethod
    def _c():
        return theme_manager.colors()

    @classmethod
    def _make(cls, bg_key, border_key, dot_key, text_key):
        c = cls._c()
        return {"bg": c[bg_key], "border": c[border_key], "dot": c[dot_key], "text": c[text_key], "icon": c[dot_key]}

    @classmethod
    def get(cls, severite: str) -> dict:
        c = cls._c()
        severity_map = {
            "critique": {"bg": c['danger_bg'],  "border": c['danger'],  "dot": c['danger'],  "text": c['danger'],  "icon": c['danger']},
            "elevee":   {"bg": c['warning_bg'], "border": c['warning'], "dot": c['warning'], "text": c['warning'], "icon": c['warning']},
            "moyenne":  {"bg": c['warning_bg'], "border": c['warning'], "dot": c['warning'], "text": c['warning'], "icon": c['warning']},
            "faible":   {"bg": c['success_bg'], "border": c['success'], "dot": c['success'], "text": c['success'], "icon": c['success']},
        }
        return severity_map.get(severite.lower(), severity_map["faible"])


SEVERITY_LABELS = {
    "critique": "CRITIQUE", "elevee": "ÉLEVÉE",
    "moyenne": "MOYENNE",   "faible": "FAIBLE",
}

SEVERITY_ICONS = {
    "critique": "fa5s.radiation-alt",
    "elevee":   "fa5s.exclamation-circle",
    "moyenne":  "fa5s.exclamation-triangle",
    "faible":   "fa5s.info-circle",
}


# ─────────────────────────────────────────────
#  CARTE ALERTE
# ─────────────────────────────────────────────
class AlertCard(QFrame):
    def __init__(self, alerte: dict, parent=None):
        super().__init__(parent)
        self._build(alerte)

    def _build(self, alerte: dict):
        severite  = alerte.get("severite", "faible")
        code      = alerte.get("code_visite", "—")
        temps     = alerte.get("temps_attente", 0)
        statut    = alerte.get("statut") or "Accueil"
        palette   = AlertColors.get(severite)
        label_sev = SEVERITY_LABELS.get(severite, severite.upper())
        icon_name = SEVERITY_ICONS.get(severite, "fa5s.info-circle")
        icon_color = palette['icon']

        self.setStyleSheet(f"""
            AlertCard {{
                background-color: {palette['bg']};
                border: 1px solid {palette['border']};
                border-left: 4px solid {palette['dot']};
                border-radius: 10px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        # En-tête
        header = QHBoxLayout()
        header.setSpacing(8)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(16, 16))
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        code_lbl = QLabel(f"Visite  {code.upper()}")
        code_lbl.setStyleSheet(f"font-weight: 700; font-size: 12px; color: {palette['text']}; border: none; background: transparent;")
        badge = QLabel(label_sev)
        badge.setStyleSheet(f"""
            background-color: {palette['dot']}; color: {theme_manager.colors()['text_inverse']};
            font-size: 9px; font-weight: 800;
            padding: 2px 7px; border-radius: 8px; border: none;
        """)
        header.addWidget(icon_lbl)
        header.addWidget(code_lbl)
        header.addStretch()
        header.addWidget(badge)
        layout.addLayout(header)

        # Corps
        body = QHBoxLayout()
        body.setSpacing(16)
        body.addLayout(self._info_block("fa5s.map-marker-alt", theme_manager.colors()['text_secondary'], "Service", statut, palette))
        body.addLayout(self._info_block("fa5s.hourglass-half", palette['dot'], "Attente", f"{temps} min", palette))
        body.addStretch()
        layout.addLayout(body)

    @staticmethod
    def _info_block(icon_name, icon_color, label_txt, value_txt, palette):
        col = QHBoxLayout()
        col.setSpacing(5)
        ic = QLabel()
        ic.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(11, 11))
        ic.setStyleSheet("border: none; background: transparent;")
        inner = QVBoxLayout()
        inner.setSpacing(0)
        lbl = QLabel(label_txt)
        lbl.setStyleSheet(f"font-size: 9px; color: {theme_manager.colors()['text_muted']}; font-weight: 500; border: none; background: transparent;")
        val = QLabel(value_txt)
        val.setStyleSheet(f"font-size: 11px; color: {palette['text']}; font-weight: 700; border: none; background: transparent;")
        inner.addWidget(lbl)
        inner.addWidget(val)
        col.addWidget(ic)
        col.addLayout(inner)
        return col


# ─────────────────────────────────────────────
#  PANNEAU FLOTTANT
# ─────────────────────────────────────────────
class NotificationPanel(QWidget):
    """
    Panneau latéral glissant depuis la droite — style carte flottante détachée.
    Usage:
        panel = NotificationPanel(controleur=ctrl, parent=main_window)
        panel.toggle()
    """

    PANEL_WIDTH   = 360
    ANIM_DURATION = 350

    def __init__(self, controleur, parent: QWidget = None):
        super().__init__(parent)
        self.ctrl    = controleur
        self.logger  = logging.getLogger(__name__)
        self._opened = False
        self._alertes: list = []

        # ── Style flottant ──
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._setup_geometry()
        self._build_card()
        self._setup_animation()
        self._setup_auto_refresh()

        # Réagir aux changements de thème
        theme_manager.theme_changed.connect(self._apply_theme)

    # ── Géométrie ──────────────────────────────────────────────────────
    def _setup_geometry(self):
        parent = self.parent()
        if parent:
            h = parent.height()
            y = 60
            self.setGeometry(parent.width(), y, self.PANEL_WIDTH + 30, h - y)

    # ── Carte flottante principale ─────────────────────────────────────
    def _build_card(self):
        # Ombre externe portée
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(35)
        shadow.setXOffset(-10)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 70))

        # Conteneur blanc arrondi
        c = theme_manager.colors()
        self.card = QFrame(self)
        self.card.setGraphicsEffect(shadow)
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_card']};
                border-radius: 20px;
                border: 1px solid {c['border']};
            }}
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        card_layout.addWidget(self._build_header())
        card_layout.addWidget(self._build_scroll_area())
        card_layout.addWidget(self._build_footer())

        # Wrapper avec marge gauche pour laisser respirer l'ombre
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(15, 10, 10, 10)
        wrapper.addWidget(self.card)

    # ── Header sombre ──────────────────────────────────────────────────
    def _build_header(self) -> QFrame:
        c = theme_manager.colors()
        self._header = QFrame()
        self._header.setFixedHeight(62)
        self._header.setStyleSheet(f"""
            QFrame {{
                background-color: {c['primary']};
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border: none;
            }}
        """)
        layout = QHBoxLayout(self._header)
        layout.setContentsMargins(18, 0, 18, 0)

        self._bell = QLabel()
        self._bell.setPixmap(qta.icon("fa5s.bell", color=c['text_inverse']).pixmap(18, 18))
        self._bell.setStyleSheet("border: none; background: transparent;")

        self._title = QLabel("Alertes Patients")
        self._title.setStyleSheet(f"color: {c['text_inverse']}; font-weight: 700; font-size: 14px; border: none; background: transparent;")

        self.badge_count = QLabel("0")
        self.badge_count.setFixedSize(24, 24)
        self.badge_count.setAlignment(Qt.AlignCenter)
        self.badge_count.setStyleSheet(f"""
            background-color: {c['danger']}; color: {c['text_inverse']};
            font-size: 10px; font-weight: 800;
            border-radius: 12px; border: none;
        """)

        self._btn_close_header = QPushButton(qta.icon("fa5s.times", color=c['text_muted']), "")
        self._btn_close_header.setFixedSize(30, 30)
        self._btn_close_header.setStyleSheet(f"""
            QPushButton {{ border: none; background: {c['primary_hover']}; border-radius: 8px; }}
            QPushButton:hover {{ background: {c['danger']}22; }}
        """)
        self._btn_close_header.setCursor(Qt.PointingHandCursor)
        self._btn_close_header.clicked.connect(self.close_panel)

        layout.addWidget(self._bell)
        layout.addSpacing(8)
        layout.addWidget(self._title)
        layout.addStretch()
        layout.addWidget(self.badge_count)
        layout.addSpacing(8)
        layout.addWidget(self._btn_close_header)
        return self._header

    # ── Zone scrollable ────────────────────────────────────────────────
    def _build_scroll_area(self) -> QScrollArea:
        c = theme_manager.colors()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {c['bg_main']}; }}
            QScrollBar:vertical {{
                border: none; background: {c['bg_main']};
                width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 3px; }}
            QScrollBar::handle:vertical:hover {{ background: {c['text_muted']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(f"background: {c['bg_main']};")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(14, 14, 14, 14)
        self.content_layout.setSpacing(8)
        self.content_layout.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.content_widget)
        return self.scroll

    # ── Footer ─────────────────────────────────────────────────────────
    def _build_footer(self) -> QFrame:
        c = theme_manager.colors()
        self._footer = QFrame()
        self._footer.setFixedHeight(54)
        self._footer.setStyleSheet(f"""
            QFrame {{
                background: {c['bg_card']};
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
                border-top: 1px solid {c['border_light']};
                border-left: none; border-right: none; border-bottom: none;
            }}
        """)
        layout = QHBoxLayout(self._footer)
        layout.setContentsMargins(18, 0, 18, 0)

        self.last_update_lbl = QLabel("Dernière mise à jour : —")
        self.last_update_lbl.setStyleSheet(f"color: {c['text_muted']}; font-size: 10px; border: none; background: transparent;")

        self._btn_refresh = QPushButton(qta.icon("fa5s.sync-alt", color=c['primary']), " Actualiser")
        self._btn_refresh.setFixedHeight(32)
        self._btn_refresh.setCursor(Qt.PointingHandCursor)
        self._btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: {c['success_bg']}; color: {c['primary']};
                border: 1px solid {c['success']}; border-radius: 8px;
                font-size: 11px; font-weight: 600; padding: 0 12px;
            }}
            QPushButton:hover {{ background: {c['primary_light']}; }}
        """)
        self._btn_refresh.clicked.connect(self.refresh)

        layout.addWidget(self.last_update_lbl)
        layout.addStretch()
        layout.addWidget(self._btn_refresh)
        return self._footer

    # ── Animation ──────────────────────────────────────────────────────
    def _setup_animation(self):
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(self.ANIM_DURATION)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def _setup_auto_refresh(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(60_000)

    # ── Thème dynamique ────────────────────────────────────────────────
    def _apply_theme(self):
        c = theme_manager.colors()
        # Card
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_card']};
                border-radius: 20px;
                border: 1px solid {c['border']};
            }}
        """)
        # Header
        self._header.setStyleSheet(f"""
            QFrame {{
                background-color: {c['primary']};
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border: none;
            }}
        """)
        self._bell.setPixmap(qta.icon("fa5s.bell", color=c['text_inverse']).pixmap(18, 18))
        self._title.setStyleSheet(f"color: {c['text_inverse']}; font-weight: 700; font-size: 14px; border: none; background: transparent;")
        self.badge_count.setStyleSheet(f"""
            background-color: {c['danger']}; color: {c['text_inverse']};
            font-size: 10px; font-weight: 800;
            border-radius: 12px; border: none;
        """)
        self._btn_close_header.setIcon(qta.icon("fa5s.times", color=c['text_muted']))
        self._btn_close_header.setStyleSheet(f"""
            QPushButton {{ border: none; background: {c['primary_hover']}; border-radius: 8px; }}
            QPushButton:hover {{ background: {c['danger']}22; }}
        """)
        # Scroll area
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {c['bg_main']}; }}
            QScrollBar:vertical {{
                border: none; background: {c['bg_main']};
                width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 3px; }}
            QScrollBar::handle:vertical:hover {{ background: {c['text_muted']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        self.content_widget.setStyleSheet(f"background: {c['bg_main']};")
        # Footer
        self._footer.setStyleSheet(f"""
            QFrame {{
                background: {c['bg_card']};
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
                border-top: 1px solid {c['border_light']};
                border-left: none; border-right: none; border-bottom: none;
            }}
        """)
        self.last_update_lbl.setStyleSheet(f"color: {c['text_muted']}; font-size: 10px; border: none; background: transparent;")
        self._btn_refresh.setIcon(qta.icon("fa5s.sync-alt", color=c['primary']))
        self._btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: {c['success_bg']}; color: {c['primary']};
                border: 1px solid {c['success']}; border-radius: 8px;
                font-size: 11px; font-weight: 600; padding: 0 12px;
            }}
            QPushButton:hover {{ background: {c['primary_light']}; }}
        """)
        # Re-rendu des alertes avec nouvelles couleurs
        self._render_alertes()

    def toggle(self):
        if self._opened:
            self.close_panel()
        else:
            self.open_panel()

    def open_panel(self):
        if not self._opened:
            self.refresh()
            parent = self.parent()
            if parent:
                h = parent.height()
                y = 60
                self.setGeometry(parent.width(), y, self.PANEL_WIDTH + 30, h - y)
            self.raise_()
            self.show()

            start = self.pos()
            end = QPoint(start.x() - self.PANEL_WIDTH - 30, start.y())
            self._anim.setStartValue(start)
            self._anim.setEndValue(end)
            self._anim.start()
            self._opened = True

    def close_panel(self):
        if self._opened:
            start = self.pos()
            end = QPoint(start.x() + self.PANEL_WIDTH + 30, start.y())
            self._anim.setStartValue(start)
            self._anim.setEndValue(end)
            self._anim.finished.connect(self._on_close_finished)
            self._anim.start()
            self._opened = False

    def _on_close_finished(self):
        self.hide()
        try:
            self._anim.finished.disconnect(self._on_close_finished)
        except RuntimeError:
            pass

    # ── Logique ────────────────────────────────────────────────────────
    def refresh(self):
        try:
            codes_actifs = self.ctrl.obtenir_visites_surveillance_active()
            self._alertes = self.ctrl.verifier_alertes_temps_attente(codes_actifs, seuil_minutes=20)
            self._render_alertes()
            self._update_badge(len(self._alertes))
            self.last_update_lbl.setText(f"Mis à jour à {datetime.now().strftime('%H:%M')}")
        except Exception as e:
            self.logger.error(f"Erreur refresh NotificationPanel: {e}")

    def _render_alertes(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._alertes:
            self._render_empty_state()
            return

        ordre = {"critique": 0, "elevee": 1, "moyenne": 2, "faible": 3}
        alertes_triees = sorted(
            self._alertes,
            key=lambda a: ordre.get(a.get("severite", "faible"), 3)
        )

        section_lbl = QLabel(f"{len(alertes_triees)} alerte(s) active(s)")
        section_lbl.setStyleSheet(f"color: {theme_manager.colors()['text_secondary']}; font-size: 11px; font-weight: 600; padding: 4px 0; border: none; background: transparent;")
        self.content_layout.addWidget(section_lbl)

        for alerte in alertes_triees:
            self.content_layout.addWidget(AlertCard(alerte))

    def _render_empty_state(self):
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        v = QVBoxLayout(container)
        v.setAlignment(Qt.AlignCenter)
        v.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("fa5s.check-circle", color=theme_manager.colors()['success']).pixmap(48, 48))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("border: none; background: transparent;")

        msg = QLabel("Aucune alerte active")
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet(f"color: {theme_manager.colors()['text_secondary']}; font-size: 13px; font-weight: 600; border: none; background: transparent;")

        sub = QLabel("Tous les patients sont dans les d\u00e9lais")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color: {theme_manager.colors()['text_muted']}; font-size: 11px; border: none; background: transparent;")

        v.addWidget(icon_lbl)
        v.addWidget(msg)
        v.addWidget(sub)
        self.content_layout.addWidget(container)

    def _update_badge(self, count: int):
        self.badge_count.setText(str(count))
        self.badge_count.setVisible(count > 0)

    def get_alert_count(self) -> int:
        return len(self._alertes)

    def cleanup(self):
        self._timer.stop()