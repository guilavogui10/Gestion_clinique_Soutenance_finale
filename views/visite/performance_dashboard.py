# Standard library imports
import logging
from datetime import datetime

# Third-party imports
import qtawesome as qta
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import (
    QColor, QPainter, QPen, QBrush, QLinearGradient,
    QFont, QPainterPath
)
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGridLayout, QSizePolicy, QGraphicsDropShadowEffect
)

from views.shared.theme_manager import theme_manager


# ─────────────────────────────────────────────
#  PALETTE LIGHT MEDICAL (dynamique via thème)
# ─────────────────────────────────────────────
class _TC:
    """Descripteur renvoyant la couleur du thème courant."""
    def __init__(self, key):
        self._key = key
    def __set_name__(self, owner, name):
        self._name = name
    def __get__(self, obj, objtype=None):
        return theme_manager.colors()[self._key]


class C:
    PRIMARY    = _TC('primary')
    PRIMARY_L  = _TC('primary_hover')
    SUCCESS    = _TC('success')
    WARNING    = _TC('warning')
    DANGER     = _TC('danger')
    INFO       = _TC('info')
    PURPLE     = _TC('accent')
    BG         = _TC('bg_main')
    SURFACE    = _TC('bg_card')
    BORDER     = _TC('border')
    BORDER_S   = _TC('border_light')
    TEXT_H     = _TC('text_primary')
    TEXT_B     = _TC('text_secondary')
    TEXT_M     = _TC('text_muted')
    HEADER_BG  = _TC('text_primary')


# ─────────────────────────────────────────────
#  UTILITAIRES
# ─────────────────────────────────────────────
def make_separator():
    sep = QFrame()
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background: {C.BORDER_S}; border: none;")
    return sep


# ─────────────────────────────────────────────
#  CARTE KPI
# ─────────────────────────────────────────────
class KpiCard(QFrame):
    def __init__(self, titre, valeur, sous_texte, icone, couleur, parent=None):
        super().__init__(parent)
        self._build(titre, valeur, sous_texte, icone, couleur)
        sh = QGraphicsDropShadowEffect(self)
        sh.setBlurRadius(12)
        sh.setOffset(0, 4)
        c = QColor(couleur)
        c.setAlpha(45)
        sh.setColor(c)
        self.setGraphicsEffect(sh)

    def _build(self, titre, valeur, sous_texte, icone, couleur):
        self.setFixedHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            KpiCard {{
                background: {C.SURFACE};
                border-radius: 14px;
                border-left: 4px solid {couleur};
                border-top: 1px solid {C.BORDER};
                border-right: 1px solid {C.BORDER};
                border-bottom: 1px solid {C.BORDER};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Cercle icône
        circle = QFrame()
        circle.setFixedSize(44, 44)
        circle.setStyleSheet(f"""
            QFrame {{
                background: {couleur}15;
                border-radius: 22px;
                border: 1px solid {couleur}30;
            }}
        """)
        cl = QHBoxLayout(circle)
        cl.setContentsMargins(0, 0, 0, 0)
        ic = QLabel()
        ic.setPixmap(qta.icon(icone, color=couleur).pixmap(20, 20))
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet("border: none; background: transparent;")
        cl.addWidget(ic, alignment=Qt.AlignCenter)

        # Textes
        col = QVBoxLayout()
        col.setSpacing(2)
        self.val_lbl = QLabel(str(valeur))
        self.val_lbl.setStyleSheet(f"""
            font-size: 24px; font-weight: 900; color: {couleur};
            border: none; background: transparent;
        """)
        t_lbl = QLabel(titre.upper())
        t_lbl.setStyleSheet(f"""
            font-size: 9px; font-weight: 700; letter-spacing: 1px;
            color: {C.TEXT_B}; border: none; background: transparent;
        """)
        self.sub_lbl = QLabel(sous_texte)
        self.sub_lbl.setStyleSheet(f"font-size: 9px; color: {C.TEXT_M}; border: none; background: transparent;")
        col.addWidget(self.val_lbl)
        col.addWidget(t_lbl)
        col.addWidget(self.sub_lbl)

        layout.addWidget(circle)
        layout.addLayout(col)
        layout.addStretch()

    def update_value(self, valeur, sous_texte=None):
        self.val_lbl.setText(str(valeur))
        if sous_texte is not None:
            self.sub_lbl.setText(sous_texte)


# ─────────────────────────────────────────────
#  BARRE DE STATUT
# ─────────────────────────────────────────────
class StatutBar(QWidget):
    def __init__(self, label, count, max_count, color, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(10)

        lbl = QLabel(label)
        lbl.setFixedWidth(175)
        lbl.setStyleSheet(f"font-size: 11px; color: {C.TEXT_B}; font-weight: 500; border: none; background: transparent;")

        bar_bg = QFrame()
        bar_bg.setFixedHeight(7)
        bar_bg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bar_bg.setStyleSheet(f"background: {C.BORDER_S}; border-radius: 4px; border: none;")

        pct = (count / max_count) if max_count > 0 else 0
        bar_fill = QFrame(bar_bg)
        bar_fill.setFixedHeight(7)
        bar_fill.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {color}, stop:1 {color}88);
            border-radius: 4px; border: none;
        """)

        count_lbl = QLabel(str(count))
        count_lbl.setFixedWidth(28)
        count_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        count_lbl.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {color}; border: none; background: transparent;")

        layout.addWidget(lbl)
        layout.addWidget(bar_bg, 1)
        layout.addWidget(count_lbl)

        def _resize():
            bar_fill.setFixedWidth(max(6, int(bar_bg.width() * pct)))
        QTimer.singleShot(80, _resize)


# ─────────────────────────────────────────────
#  SPARKLINE
# ─────────────────────────────────────────────
class SparklineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background: transparent; border: none;")

    def set_data(self, flux_list: list):
        self._data = flux_list or []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Fond arrondi léger
        bg = QPainterPath()
        bg.addRoundedRect(QRectF(0, 0, w, h - 22), 10, 10)
        painter.fillPath(bg, QBrush(QColor(C.BG)))

        if not self._data or len(self._data) < 2:
            painter.setPen(QPen(QColor(C.TEXT_M)))
            f = QFont()
            f.setPointSize(9)
            painter.setFont(f)
            painter.drawText(0, 0, w, h - 22, Qt.AlignCenter, "Aucune donnée disponible")
            return

        px, py = 18, 14
        values = [d.get("total", 0) for d in self._data]
        jours  = [d.get("jour", "")  for d in self._data]
        max_v  = max(values) if max(values) > 0 else 1
        n      = len(values)

        def xp(i): return px + i * (w - 2 * px) / (n - 1)
        def yp(v): return py + (1 - v / max_v) * (h - 2 * py - 26)

        # Lignes de grille
        painter.setPen(QPen(QColor(C.BORDER), 1, Qt.DotLine))
        for lvl in [0.25, 0.5, 0.75]:
            yg = py + (1 - lvl) * (h - 2 * py - 26)
            painter.drawLine(int(px), int(yg), int(w - px), int(yg))

        # Remplissage dégradé
        path_fill = QPainterPath()
        path_fill.moveTo(xp(0), h - py - 26)
        for i, v in enumerate(values):
            path_fill.lineTo(xp(i), yp(v))
        path_fill.lineTo(xp(n - 1), h - py - 26)
        path_fill.closeSubpath()
        primary_c = QColor(C.PRIMARY)
        grad = QLinearGradient(0, 0, 0, h)
        primary_c.setAlpha(80)
        grad.setColorAt(0.0, primary_c)
        primary_c.setAlpha(15)
        grad.setColorAt(0.7, primary_c)
        primary_c.setAlpha(0)
        grad.setColorAt(1.0, primary_c)
        painter.fillPath(path_fill, QBrush(grad))

        # Ligne principale
        painter.setPen(QPen(QColor(C.PRIMARY), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        path_line = QPainterPath()
        path_line.moveTo(xp(0), yp(values[0]))
        for i in range(1, n):
            path_line.lineTo(xp(i), yp(values[i]))
        painter.drawPath(path_line)

        # Points
        for i, v in enumerate(values):
            painter.setBrush(QBrush(QColor(C.PRIMARY)))
            painter.setPen(QPen(QColor(C.SURFACE), 2))
            painter.drawEllipse(QPointF(xp(i), yp(v)), 4, 4)

        # Labels jours
        painter.setPen(QPen(QColor(C.TEXT_M)))
        f = QFont()
        f.setPointSize(8)
        painter.setFont(f)
        for i, jour in enumerate(jours):
            painter.drawText(int(xp(i)) - 16, h - 20, 32, 18, Qt.AlignCenter, jour[:3])


# ─────────────────────────────────────────────
#  DIALOG PRINCIPAL — STYLE FLOTTANT
# ─────────────────────────────────────────────
class PerformanceDashboard(QDialog):
    """
    Tableau de bord performance — carte flottante détachée.
    Usage: PerformanceDashboard(controleur=ctrl, parent=self).exec()
    """

    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl   = controleur
        self.logger = logging.getLogger(__name__)
        self._kpi_cards = {}

        # Couleurs calculées au moment de l'ouverture (pas à l'import)
        self._kpi_config = [
            ("Durée Moy.",      "fa5s.clock",          C.INFO,    "duree_moyenne",   "min / visite"),
            ("Attente Max",     "fa5s.hourglass-half",  C.WARNING, "attente_max",     "minutes"),
            ("Visites Actives", "fa5s.user-clock",      C.PRIMARY, "visites_actives", "en cours"),
            ("Tendance",        "fa5s.chart-line",      C.SUCCESS, "tendance",        "vs session préc."),
            ("Efficacité",      "fa5s.tachometer-alt",  C.SUCCESS, "efficacite",      "% objectif"),
            ("Satisfaction",    "fa5s.smile",           C.INFO,    "satisfaction",    "score / 100"),
        ]
        self._statut_colors = {
            "Attente consultation": C.INFO,
            "Attente examen":       C.WARNING,
            "Attente operation":    C.DANGER,
            "Attente payement":     C.SUCCESS,
            "Attente Pharmacie":    C.PURPLE,
            "Libéré":               C.SUCCESS,
        }

        # ── Style flottant comme DetailsVisiteModal ──
        self.setWindowTitle("Performance Session")
        self.setMinimumSize(1000, 660)
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        # Ombre externe
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(15)
        shadow.setColor(QColor(0, 0, 0, 80))

        # Conteneur principal blanc arrondi
        self.main_container = QFrame(self)
        self.main_container.setGraphicsEffect(shadow)
        self.main_container.setStyleSheet(f"""
            QFrame {{
                background-color: {C.SURFACE};
                border-radius: 22px;
                border: 1px solid {C.BORDER};
            }}
        """)

        root = QVBoxLayout(self.main_container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_body())
        root.addWidget(self._build_footer())

        # Wrapper avec marges pour laisser respirer l'ombre
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(25, 25, 25, 25)
        wrapper.addWidget(self.main_container)

    # ── HEADER sombre comme DetailsVisiteModal ─────────────────────────
    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setFixedHeight(72)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {C.HEADER_BG};
                border-top-left-radius: 22px;
                border-top-right-radius: 22px;
                border: none;
            }}
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(26, 0, 26, 0)

        # Icône + titres
        ic = QLabel()
        ic.setPixmap(qta.icon("fa5s.tachometer-alt", color=C.SUCCESS).pixmap(22, 22))
        ic.setStyleSheet("border: none; background: transparent;")

        title = QLabel("Performance Session")
        title.setStyleSheet(f"font-size: 16px; font-weight: 900; color: {C.BG}; border: none; background: transparent;")

        sub = QLabel("Analyse en temps réel · Session active")
        sub.setStyleSheet(f"font-size: 10px; color: {C.TEXT_M}; border: none; background: transparent;")

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title_col.addWidget(title)
        title_col.addWidget(sub)

        self.last_update = QLabel("")
        self.last_update.setStyleSheet(f"font-size: 10px; color: {C.TEXT_M}; border: none; background: transparent;")

        btn_refresh = QPushButton(qta.icon("fa5s.sync-alt", color=C.HEADER_BG), " Actualiser")
        btn_refresh.setFixedHeight(34)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: {C.SUCCESS}; color: {C.HEADER_BG};
                border: none; border-radius: 10px;
                font-size: 11px; font-weight: 800; padding: 0 16px;
            }}
            QPushButton:hover {{ background: {C.SUCCESS}; opacity: 0.85; }}
        """)
        btn_refresh.clicked.connect(self.refresh)

        btn_close = QPushButton(qta.icon("fa5s.times", color=C.TEXT_M), "")
        btn_close.setFixedSize(34, 34)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: {C.HEADER_BG}; border: 1px solid {C.BORDER};
                border-radius: 10px;
            }}
            QPushButton:hover {{ background: {C.DANGER}22; border-color: {C.DANGER}; }}
        """)
        btn_close.clicked.connect(self.accept)

        layout.addWidget(ic)
        layout.addSpacing(10)
        layout.addLayout(title_col)
        layout.addStretch()
        layout.addWidget(self.last_update)
        layout.addSpacing(14)
        layout.addWidget(btn_refresh)
        layout.addSpacing(8)
        layout.addWidget(btn_close)
        return header

    # ── BODY : KPIs + Bilan + Flux ─────────────────────────────────────
    def _build_body(self) -> QWidget:
        body = QWidget()
        body.setStyleSheet(f"background: {C.SURFACE}; border: none;")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        layout.addWidget(self._build_kpi_row())
        layout.addWidget(make_separator())

        row2 = QHBoxLayout()
        row2.setSpacing(16)
        row2.addWidget(self._build_bilan_frame(), 55)
        row2.addWidget(self._build_flux_frame(), 45)
        layout.addLayout(row2)

        return body

    def _build_kpi_row(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(12)
        for i, (titre, icone, couleur, cle, sous) in enumerate(self._kpi_config):
            card = KpiCard(titre, "—", sous, icone, couleur)
            self._kpi_cards[cle] = card
            grid.addWidget(card, 0, i)
        return container

    def _card_frame(self) -> QFrame:
        """Cadre blanc arrondi avec ombre légère."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {C.SURFACE};
                border-radius: 14px;
                border: 1px solid {C.BORDER};
            }}
        """)
        sh = QGraphicsDropShadowEffect(frame)
        sh.setBlurRadius(16)
        sh.setOffset(0, 4)
        sh.setColor(QColor(0, 0, 0, 18))
        frame.setGraphicsEffect(sh)
        return frame

    def _build_bilan_frame(self) -> QFrame:
        frame = self._card_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(qta.icon("fa5s.tasks", color=C.PRIMARY).pixmap(15, 15))
        ic.setStyleSheet("border: none; background: transparent;")
        title = QLabel("Bilan par Service")
        title.setStyleSheet(f"font-weight: 800; font-size: 13px; color: {C.TEXT_H}; border: none; background: transparent;")
        self.moy_lbl = QLabel("")
        self.moy_lbl.setStyleSheet(f"font-size: 11px; color: {C.PRIMARY}; font-weight: 700; border: none; background: transparent;")
        header.addWidget(ic)
        header.addSpacing(6)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.moy_lbl)
        layout.addLayout(header)
        layout.addWidget(make_separator())

        self.bilan_layout = QVBoxLayout()
        self.bilan_layout.setSpacing(10)
        layout.addLayout(self.bilan_layout)
        layout.addStretch()
        return frame

    def _build_flux_frame(self) -> QFrame:
        frame = self._card_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(qta.icon("fa5s.chart-area", color=C.PRIMARY).pixmap(15, 15))
        ic.setStyleSheet("border: none; background: transparent;")
        title = QLabel("Flux Hebdomadaire")
        title.setStyleSheet(f"font-weight: 800; font-size: 13px; color: {C.TEXT_H}; border: none; background: transparent;")
        header.addWidget(ic)
        header.addSpacing(6)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        layout.addWidget(make_separator())

        self.sparkline = SparklineWidget()
        layout.addWidget(self.sparkline, 1)
        return frame

    # ── FOOTER ─────────────────────────────────────────────────────────
    def _build_footer(self) -> QFrame:
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet(f"""
            QFrame {{
                background: {C.BG};
                border-bottom-left-radius: 22px;
                border-bottom-right-radius: 22px;
                border-top: 1px solid {C.BORDER};
                border-left: none; border-right: none; border-bottom: none;
            }}
        """)
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(26, 0, 26, 0)

        info = QLabel("Données calculées en temps réel sur la session active")
        info.setStyleSheet(f"font-size: 10px; color: {C.TEXT_M}; border: none; background: transparent;")

        btn_close2 = QPushButton("Fermer")
        btn_close2.setCursor(Qt.PointingHandCursor)
        btn_close2.setFixedHeight(34)
        btn_close2.setStyleSheet(f"""
            QPushButton {{
                background: {C.SURFACE}; color: {C.TEXT_B};
                border: 1px solid {C.BORDER}; border-radius: 9px;
                font-weight: 600; padding: 0 20px; font-size: 11px;
            }}
            QPushButton:hover {{ background: {C.BG}; border-color: {C.TEXT_M}; }}
        """)
        btn_close2.clicked.connect(self.accept)

        layout.addWidget(info)
        layout.addStretch()
        layout.addWidget(btn_close2)
        return footer

    # ── Rafraîchissement ───────────────────────────────────────────────
    def refresh(self):
        try:
            self._refresh_kpis()
            self._refresh_bilan()
            self._refresh_flux()
            self.last_update.setText(f"Mis à jour · {datetime.now().strftime('%H:%M')}")
        except Exception as e:
            self.logger.error(f"Erreur refresh PerformanceDashboard: {e}")

    def _refresh_kpis(self):
        stats = self.ctrl.obtenir_statistiques_performance()
        for cle, card in self._kpi_cards.items():
            val = stats.get(cle, "—")
            if cle in ("duree_moyenne", "attente_max") and isinstance(val, (int, float)):
                card.update_value(f"{val}")
            elif cle == "efficacite" and isinstance(val, (int, float)):
                card.update_value(f"{val}%")
            else:
                card.update_value(str(val))

    def _refresh_bilan(self):
        bilan   = self.ctrl.obtenir_bilan_performance_session()
        moyenne = bilan.get("moyenne_globale", 0)
        details = bilan.get("details_par_statut", [])
        self.moy_lbl.setText(f"Moy. · {moyenne} min")

        while self.bilan_layout.count():
            item = self.bilan_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not details:
            vide = QLabel("Aucune donnée disponible")
            vide.setStyleSheet(f"color: {C.TEXT_M}; font-size: 11px; border: none;")
            vide.setAlignment(Qt.AlignCenter)
            self.bilan_layout.addWidget(vide)
            return

        max_count = max((d.get("nombre", 1) for d in details), default=1)
        for d in details:
            statut = d.get("statut") or "Inconnu"
            count  = d.get("nombre", 0)
            color  = self._statut_colors.get(statut, C.INFO)
            self.bilan_layout.addWidget(StatutBar(statut, count, max_count, color))

    def _refresh_flux(self):
        self.sparkline.set_data(self.ctrl.obtenir_analyse_flux_hebdomadaire())