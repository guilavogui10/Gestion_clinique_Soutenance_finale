"""
Analyse consultation — Dashboard moderne
Thème: fond sombre dégradé, cartes glassmorphism, couleurs vives
"""

import calendar
from datetime import datetime
import numpy as np
from scipy.interpolate import make_interp_spline
import mplcursors
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, FuncFormatter
from matplotlib.patches import Wedge, Circle

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGraphicsDropShadowEffect, QGridLayout,
    QComboBox, QSizePolicy, QScrollArea
)
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPalette, QPainter, QBrush
import qtawesome as qta


# ─────────────────────────────────────────────────────────────
#  PALETTE GLOBALE
# ─────────────────────────────────────────────────────────────
class Theme:
    # Fond général
    BG_DEEP     = "#0D0B26"
    BG_CARD     = "#16133A"
    BG_CARD2    = "#1A1740"
    BG_SURFACE  = "#211E4F"

    # Accents principaux (palette inspirée finance dashboard)
    PURPLE      = "#8B5CF6"
    PURPLE_LIGHT= "#A78BFA"
    BLUE        = "#3B82F6"
    BLUE_LIGHT  = "#60A5FA"
    TEAL        = "#06B6D4"
    GREEN       = "#10B981"
    AMBER       = "#F59E0B"
    PINK        = "#EC4899"
    RED         = "#EF4444"
    INDIGO      = "#6366F1"

    # Texte
    TEXT_PRIMARY   = "#F1F5F9"
    TEXT_SECONDARY = "#94A3B8"
    TEXT_MUTED     = "#475569"

    # Bordures
    BORDER         = "#2D2A6A"
    BORDER_BRIGHT  = "#4C4899"

    # Graphes — fond transparent
    PLOT_BG        = "none"

    # Couleurs années
    YEAR_COLORS = {
        2022: "#6366F1",
        2023: "#F59E0B",
        2024: "#10B981",
        2025: "#3B82F6",
        2026: "#EC4899",
    }

    # Style QSS global (appliqué sur la vue racine)
    GLOBAL_QSS = f"""
        QWidget {{
            background-color: {BG_DEEP};
            color: {TEXT_PRIMARY};
            font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
        }}
        QComboBox {{
            background-color: {BG_SURFACE};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_BRIGHT};
            border-radius: 10px;
            padding: 5px 12px;
            font-size: 11px;
            font-weight: 600;
        }}
        QComboBox::drop-down {{ border: none; width: 16px; }}
        QComboBox::down-arrow {{ image: none; }}
        QComboBox QAbstractItemView {{
            background-color: {BG_CARD};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_BRIGHT};
            border-radius: 8px;
            selection-background-color: {BG_SURFACE};
        }}
        QScrollBar:vertical {{
            background: {BG_DEEP};
            width: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: {BORDER_BRIGHT};
            border-radius: 3px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """


def _shadow(blur=24, offset_y=6, alpha=80, color=(0, 0, 0)):
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur)
    s.setOffset(0, offset_y)
    s.setColor(QColor(*color, alpha))
    return s


def _glow(color_hex: str, blur=18, alpha=60):
    """Ombre colorée pour l'effet glow."""
    c = QColor(color_hex)
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur)
    s.setOffset(0, 0)
    s.setColor(QColor(c.red(), c.green(), c.blue(), alpha))
    return s


# ─────────────────────────────────────────────────────────────
#  CARTE GLASSMORPHISM
# ─────────────────────────────────────────────────────────────
class GlassCard(QFrame):
    """Carte à fond semi-transparent avec bordure lumineuse optionnelle."""

    def __init__(self, accent: str = None, parent=None):
        super().__init__(parent)
        border_color = accent if accent else Theme.BORDER
        self.setStyleSheet(
            f"QFrame {{"
            f"  background-color: {Theme.BG_CARD};"
            f"  border-radius: 16px;"
            f"  border: 1px solid {border_color};"
            f"}}"
        )
        self.setGraphicsEffect(_shadow(24, 6, 90))


# ─────────────────────────────────────────────────────────────
#  KPI CARD
# ─────────────────────────────────────────────────────────────
class KPICard(QFrame):
    def __init__(self, titre: str, valeur: str, icone: str,
                 couleur: str, unite: str = "", parent=None):
        super().__init__(parent)
        self._couleur = couleur
        self._build(titre, valeur, icone, couleur, unite)

    def _build(self, titre, valeur, icone, couleur, unite):
        self.setFixedHeight(110)
        # Fond dégradé simulé : bande colorée sur la gauche via border-left
        self.setStyleSheet(
            f"QFrame {{"
            f"  background-color: {Theme.BG_CARD};"
            f"  border-radius: 16px;"
            f"  border: 1px solid {Theme.BORDER};"
            f"  border-left: 4px solid {couleur};"
            f"}}"
        )
        self.setGraphicsEffect(_glow(couleur, blur=28, alpha=50))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(4)

        # En-tête
        hdr = QHBoxLayout()
        ico_bg = QFrame()
        ico_bg.setFixedSize(36, 36)
        ico_bg.setStyleSheet(
            f"QFrame {{ background-color: {couleur}22; border-radius: 10px; border: none; }}"
        )
        ico_lay = QHBoxLayout(ico_bg)
        ico_lay.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setAlignment(Qt.AlignCenter)
        ico_lbl.setPixmap(qta.icon(icone, color=couleur).pixmap(QSize(18, 18)))
        ico_lbl.setStyleSheet("border: none; background: transparent;")
        ico_lay.addWidget(ico_lbl, 0, Qt.AlignCenter)

        ttl = QLabel(titre)
        ttl.setStyleSheet(
            f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: 600; border: none;"
        )
        ttl.setWordWrap(True)
        hdr.addWidget(ico_bg)
        hdr.addSpacing(8)
        hdr.addWidget(ttl)
        hdr.addStretch()
        lay.addLayout(hdr)

        self._val_lbl = QLabel(valeur)
        self._val_lbl.setStyleSheet(
            f"color: {couleur}; font-size: 26px; font-weight: 800; border: none;"
        )
        lay.addWidget(self._val_lbl)

        if unite:
            u = QLabel(unite)
            u.setStyleSheet(
                f"color: {Theme.TEXT_MUTED}; font-size: 10px; border: none;"
            )
            lay.addWidget(u)
        lay.addStretch()

    def update_value(self, v: str):
        self._val_lbl.setText(v)


# ─────────────────────────────────────────────────────────────
#  FRAME GRAPHE
# ─────────────────────────────────────────────────────────────
class GraphFrame(QFrame):
    def __init__(self, titre: str, icone: str, accent: str = None, parent=None):
        super().__init__(parent)
        self._accent = accent or Theme.PURPLE
        self.setStyleSheet(
            f"QFrame {{"
            f"  background-color: {Theme.BG_CARD};"
            f"  border-radius: 18px;"
            f"  border: 1px solid {Theme.BORDER};"
            f"}}"
        )
        self.setGraphicsEffect(_shadow(20, 5, 100))

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(8)

        hdr = QHBoxLayout()
        ico_bg = QFrame()
        ico_bg.setFixedSize(30, 30)
        ico_bg.setStyleSheet(
            f"QFrame {{ background-color: {self._accent}25; border-radius: 8px; border: none; }}"
        )
        ico_inner = QHBoxLayout(ico_bg)
        ico_inner.setContentsMargins(0, 0, 0, 0)
        ico_lbl = QLabel()
        ico_lbl.setAlignment(Qt.AlignCenter)
        ico_lbl.setPixmap(qta.icon(icone, color=self._accent).pixmap(QSize(15, 15)))
        ico_lbl.setStyleSheet("border: none; background: transparent;")
        ico_inner.addWidget(ico_lbl, 0, Qt.AlignCenter)

        ttl = QLabel(titre)
        ttl.setStyleSheet(
            f"font-weight: 700; color: {Theme.TEXT_PRIMARY}; font-size: 12px; border: none;"
        )
        hdr.addWidget(ico_bg)
        hdr.addSpacing(8)
        hdr.addWidget(ttl)
        hdr.addStretch()
        root.addLayout(hdr)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {Theme.BORDER}; border: none;")
        root.addWidget(sep)

        self.graph_layout = QVBoxLayout()
        self.graph_layout.setContentsMargins(0, 0, 0, 0)
        root.addLayout(self.graph_layout)


# ─────────────────────────────────────────────────────────────
#  BASE GRAPH (fond sombre)
# ─────────────────────────────────────────────────────────────
class BaseGraph(FigureCanvas):
    MONTH_LABELS = [
        "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
        "Juil", "Août", "Sep", "Oct", "Nov", "Déc",
    ]

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor("none")
        super().__init__(self.fig)
        self.setParent(parent)
        # Fond transparent pour s'intégrer à la carte sombre
        self.setStyleSheet("background: transparent;")
        self.fig.patch.set_alpha(0)
        self.cursors = []
        self._setup_style()

    def _setup_style(self):
        for spine in self.axes.spines.values():
            spine.set_visible(False)
        # Grille subtile sur fond sombre
        self.axes.grid(
            True, axis="y", linestyle="-", alpha=0.07,
            color="#8B9AC8", linewidth=0.7,
        )
        self.axes.tick_params(
            colors=Theme.TEXT_SECONDARY, labelsize=9, length=0, pad=8
        )
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.15)

    def _draw_smooth_curve(self, x, y, color, label, linestyle="-", alpha=0.95):
        if len(y) < 2 or float(np.sum(y)) == 0.0:
            return
        x_s = np.linspace(x.min(), x.max(), 300)
        y_s = np.maximum(make_interp_spline(x, y, k=min(3, len(y) - 1))(x_s), 0)
        source_max = float(np.max(y)) if len(y) else 0.0
        if source_max > 0:
            y_s = np.clip(y_s, 0, source_max * 1.05)

        self.axes.plot(
            x_s, y_s, color=color, linewidth=2.8,
            linestyle=linestyle, label=label, alpha=alpha, antialiased=True,
        )
        if linestyle == "-":
            self.axes.fill_between(x_s, y_s, color=color, alpha=0.12, antialiased=True)

    def _draw_points(self, x, y, color, tooltip_label):
        sc = self.axes.scatter(
            x, y,
            color=Theme.BG_CARD,
            edgecolor=color,
            s=55, zorder=10, linewidth=2.2, alpha=0.95,
        )
        cur = mplcursors.cursor(sc, hover=True)
        cur.connect("add", lambda sel, lbl=tooltip_label: self._on_hover(sel, lbl))
        self.cursors.append(cur)

    def _on_hover(self, sel, label):
        idx = int(round(sel.target[0]))
        val = sel.target[1]
        month = self.MONTH_LABELS[idx] if 0 <= idx < len(self.MONTH_LABELS) else ""
        if abs(val - round(val)) < 1e-6:
            value_txt = f"{int(round(val)):,}".replace(",", " ")
        else:
            value_txt = f"{val:,.2f}".replace(",", " ")
        sel.annotation.set_text(f"{month}\n{label}: {value_txt}")
        sel.annotation.get_bbox_patch().set(
            fc="#1A1740", ec="#4C4899",
            boxstyle="round,pad=0.5", alpha=0.96, linewidth=1,
        )
        sel.annotation.set_color(Theme.TEXT_PRIMARY)
        sel.annotation.set_fontsize(9)
        sel.annotation.set_fontweight("600")
        sel.annotation.arrow_patch.set_visible(False)

    def _set_x_axis(self, x):
        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.MONTH_LABELS, rotation=0, color=Theme.TEXT_SECONDARY)

    def _nice_upper_bound(self, value: float, min_upper: float) -> float:
        if value <= 0:
            return float(min_upper)
        magnitude = 10 ** np.floor(np.log10(value))
        normalized = value / magnitude
        if normalized <= 1:
            nice = 1
        elif normalized <= 2:
            nice = 2
        elif normalized <= 5:
            nice = 5
        else:
            nice = 10
        return max(float(nice * magnitude), float(min_upper))

    def _set_ylim_counts(self, *value_lists):
        all_vals = [float(v) for lst in value_lists for v in lst if v > 0]
        max_val = max(all_vals) if all_vals else 0.0
        upper = self._nice_upper_bound(max_val * 1.15, min_upper=20.0)
        self.axes.set_ylim(0, upper)
        self.axes.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

    def _set_ylim_amounts(self, *value_lists):
        all_vals = [float(v) for lst in value_lists for v in lst if v > 0]
        max_val = max(all_vals) if all_vals else 0.0
        upper = self._nice_upper_bound(max_val * 1.15, min_upper=1000.0)
        self.axes.set_ylim(0, upper)
        self.axes.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

    def _finalize(self):
        self.fig.tight_layout()
        self.draw()


# ─────────────────────────────────────────────────────────────
#  GRAPHE NOMBRE
# ─────────────────────────────────────────────────────────────
class ConsultationNombreGraph(BaseGraph):
    def update_graph(self, nombre_par_mois: dict, moyenne_par_mois: dict):
        if hasattr(self, "avg_axis") and self.avg_axis is not None:
            try:
                self.avg_axis.remove()
            except Exception:
                pass
            self.avg_axis = None

        self.axes.clear()
        self._setup_style()

        x = np.arange(len(self.MONTH_LABELS))
        y_nb  = np.array([nombre_par_mois.get(m, 0)  for m in self.MONTH_LABELS], dtype=float)
        y_avg = np.array([moyenne_par_mois.get(m, 0)  for m in self.MONTH_LABELS], dtype=float)

        self._draw_smooth_curve(x, y_nb, Theme.PURPLE, "Nombre consultations")
        self._draw_points(x, y_nb, Theme.PURPLE, "Nombre consultations")

        self.avg_axis = self.axes.twinx()
        for sn, sp in self.avg_axis.spines.items():
            sp.set_visible(sn == "right")
        self.avg_axis.spines["right"].set_color(Theme.BORDER_BRIGHT)
        self.avg_axis.spines["right"].set_linewidth(0.8)
        self.avg_axis.grid(False)
        self.avg_axis.tick_params(colors=Theme.TEAL, labelsize=8, length=0, pad=6)
        self.avg_axis.set_ylabel(
            "Moyenne / jour", color=Theme.TEAL, fontsize=9, fontweight="600"
        )

        if len(y_avg) >= 2 and float(np.sum(y_avg)) > 0.0:
            x_s = np.linspace(x.min(), x.max(), 300)
            y_s = np.maximum(
                make_interp_spline(x, y_avg, k=min(3, len(y_avg) - 1))(x_s), 0
            )
            src_max = float(np.max(y_avg))
            if src_max > 0:
                y_s = np.clip(y_s, 0, src_max * 1.05)
            self.avg_axis.plot(
                x_s, y_s, color=Theme.TEAL, linewidth=2.2,
                linestyle="--", label="Moyenne journalière", alpha=0.95, antialiased=True,
            )
            sc_avg = self.avg_axis.scatter(
                x, y_avg, color=Theme.BG_CARD, edgecolor=Theme.TEAL,
                s=48, zorder=10, linewidth=2, alpha=0.95,
            )
            cur_avg = mplcursors.cursor(sc_avg, hover=True)
            cur_avg.connect("add", lambda sel: self._on_hover(sel, "Moyenne journalière"))
            self.cursors.append(cur_avg)

        self._set_x_axis(x)
        self._set_ylim_counts(y_nb.tolist())

        avg_vals = [float(v) for v in y_avg.tolist() if v > 0]
        avg_max  = max(avg_vals) if avg_vals else 0.0
        avg_upper = self._nice_upper_bound(avg_max * 1.15, min_upper=1.0)
        self.avg_axis.set_ylim(0, avg_upper)
        self.avg_axis.yaxis.set_major_locator(MaxNLocator(nbins=5))

        self.axes.set_ylabel(
            "Consultations", color=Theme.TEXT_SECONDARY, fontsize=10, fontweight="600"
        )
        h1, l1 = self.axes.get_legend_handles_labels()
        h2, l2 = self.avg_axis.get_legend_handles_labels()
        leg = self.axes.legend(
            h1 + h2, l1 + l2, loc="upper left", fontsize=9, framealpha=0.85,
            facecolor=Theme.BG_CARD, edgecolor=Theme.BORDER_BRIGHT,
        )
        for txt in leg.get_texts():
            txt.set_color(Theme.TEXT_PRIMARY)
        self._finalize()


# ─────────────────────────────────────────────────────────────
#  GRAPHE MONTANT
# ─────────────────────────────────────────────────────────────
class ConsultationMontantGraph(BaseGraph):
    def update_graph(self, montant_par_mois: dict, moyenne_par_mois: dict):
        self.axes.clear()
        self._setup_style()

        x     = np.arange(len(self.MONTH_LABELS))
        y_tot = np.array([montant_par_mois.get(m, 0)  for m in self.MONTH_LABELS], dtype=float)
        y_avg = np.array([moyenne_par_mois.get(m, 0)  for m in self.MONTH_LABELS], dtype=float)

        self._draw_smooth_curve(x, y_tot, Theme.BLUE,  "Montant total")
        self._draw_points(x, y_tot, Theme.BLUE,  "Montant total")
        self._draw_smooth_curve(x, y_avg, Theme.AMBER, "Moyenne journalière", linestyle="--")
        self._draw_points(x, y_avg, Theme.AMBER, "Moyenne journalière")

        self._set_x_axis(x)
        self._set_ylim_amounts(y_tot.tolist(), y_avg.tolist())
        self.axes.set_ylabel(
            "Montant (GNF)", color=Theme.TEXT_SECONDARY, fontsize=10, fontweight="600"
        )
        self.axes.yaxis.set_major_formatter(
            FuncFormatter(lambda v, _: f"{int(v):,}".replace(",", " "))
        )
        leg = self.axes.legend(
            loc="upper left", fontsize=9, framealpha=0.85,
            facecolor=Theme.BG_CARD, edgecolor=Theme.BORDER_BRIGHT,
        )
        for txt in leg.get_texts():
            txt.set_color(Theme.TEXT_PRIMARY)
        self._finalize()


# ─────────────────────────────────────────────────────────────
#  SEMI-CIRCLE GAUGE (fond sombre)
# ─────────────────────────────────────────────────────────────
class SemiCircleGauge(FigureCanvas):
    def __init__(self, label: str, parent=None, width=2.0, height=2.0, dpi=100):
        self.label = label
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor("none")
        super().__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet("background: transparent;")
        self.fig.patch.set_alpha(0)
        self.update_value(0.0)

    def _color_for_percent(self, p: float) -> str:
        if p < 35:
            return Theme.RED
        if p < 70:
            return Theme.AMBER
        return Theme.GREEN

    def update_value(self, percent):
        try:
            p = float(percent)
        except Exception:
            p = 0.0
        if 0 < p <= 1:
            p *= 100.0
        p = max(0.0, min(100.0, p))
        color = self._color_for_percent(p)

        self.axes.clear()
        self.axes.set_facecolor("none")
        self.axes.axis("off")

        # Piste fond sombre
        self.axes.add_patch(
            Wedge((0, 0), 1.0, 0, 360, width=0.26, facecolor="#2D2A6A", edgecolor="none")
        )
        if p > 0:
            angle = 360.0 * (p / 100.0)
            self.axes.add_patch(
                Wedge((0, 0), 1.0, 90, 90 + angle, width=0.26, facecolor=color, edgecolor="none")
            )
            theta = np.deg2rad(90 + angle)
            mx, my = 0.87 * np.cos(theta), 0.87 * np.sin(theta)
            self.axes.add_patch(
                Circle((mx, my), 0.10, facecolor=color, edgecolor="#16133A", linewidth=1.5)
            )

        self.axes.text(0, 0.04, f"{p:.0f}%",
            ha="center", va="center",
            fontsize=13, fontweight="800", color=Theme.TEXT_PRIMARY)
        self.axes.text(0, -1.22, self.label,
            ha="center", va="center",
            fontsize=9, color=Theme.TEXT_SECONDARY)

        self.axes.set_xlim(-1.28, 1.28)
        self.axes.set_ylim(-1.32, 1.22)
        self.fig.tight_layout(pad=0.2)
        self.draw()


# ─────────────────────────────────────────────────────────────
#  LIGNE JOUR (hebdomadaire)
# ─────────────────────────────────────────────────────────────
class DayStatRow(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._accent = Theme.PURPLE
        self.setStyleSheet("QFrame { background: transparent; border: none; }")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 3, 2, 3)
        layout.setSpacing(8)

        self.lbl_icon = QLabel()
        self.lbl_icon.setFixedSize(22, 22)
        self.lbl_icon.setAlignment(Qt.AlignCenter)

        self.lbl_jour   = QLabel("--")
        self.lbl_nombre = QLabel("0 consultations")
        self.lbl_montant = QLabel("0 GNF")

        left = QHBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(7)
        left.addWidget(self.lbl_icon)
        left.addWidget(self.lbl_jour)

        layout.addLayout(left)
        layout.addStretch()
        layout.addWidget(self.lbl_nombre)
        layout.addSpacing(6)
        layout.addWidget(self.lbl_montant)
        self._apply_styles(active=True)

    def _apply_styles(self, active: bool):
        if active:
            c_jour    = Theme.TEXT_PRIMARY
            c_nombre  = Theme.TEXT_SECONDARY
            c_montant = Theme.TEXT_PRIMARY
        else:
            c_jour = c_nombre = c_montant = Theme.TEXT_MUTED

        self.lbl_jour.setStyleSheet(
            f"color:{c_jour}; font-size:11px; font-weight:700; border:none;")
        self.lbl_nombre.setStyleSheet(
            f"color:{c_nombre}; font-size:11px; font-weight:600; border:none;")
        self.lbl_montant.setStyleSheet(
            f"color:{c_montant}; font-size:11px; font-weight:700; border:none;")

    def set_accent_color(self, color: str):
        self._accent = color
        self.lbl_icon.setStyleSheet(
            f"background-color:{color}33; border-radius:11px; border: 1px solid {color}66;"
        )
        self.lbl_icon.setPixmap(
            qta.icon("fa5s.calendar-day", color=color).pixmap(QSize(12, 12))
        )

    def update_values(self, jour_label: str, nombre: int, montant: float, active: bool = True):
        self.lbl_jour.setText(jour_label)
        self.lbl_nombre.setText(f"{int(nombre)} consult.")
        self.lbl_montant.setText(f"{montant:,.0f} GNF".replace(",", " "))
        self._apply_styles(active)
        if active:
            self.lbl_icon.show()
        else:
            self.lbl_icon.hide()


# ─────────────────────────────────────────────────────────────
#  VUE PRINCIPALE
# ─────────────────────────────────────────────────────────────
class AnalyseConsultationView(QWidget):

    def __init__(self, controleur, code_session: str, parent=None):
        super().__init__(parent)
        self.controleur   = controleur
        self.code_session = code_session
        # Appliquer le thème global
        self.setStyleSheet(Theme.GLOBAL_QSS)
        self._build_ui()
        self.charger_donnees()

    # ── Construction ──────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)
        self._build_kpi_row(root)
        self._build_graphs(root)

    def _build_kpi_row(self, parent):
        row = QHBoxLayout()
        row.setSpacing(14)
        self.card_nb_jour = KPICard(
            "Consultations du jour", "0",
            "fa5s.calendar-day", Theme.BLUE, "consultations")
        self.card_nb_session = KPICard(
            "Total consultations session", "0",
            "fa5s.chart-line", Theme.PURPLE, "consultations")
        self.card_montant_jour = KPICard(
            "Montant du jour", "0",
            "fa5s.money-bill-wave", Theme.TEAL, "GNF")
        self.card_montant_session = KPICard(
            "Montant session", "0",
            "fa5s.wallet", Theme.AMBER, "GNF")
        for card in (
            self.card_nb_jour, self.card_nb_session,
            self.card_montant_jour, self.card_montant_session,
        ):
            row.addWidget(card)
        parent.addLayout(row)

    def _build_graphs(self, parent):
        grid = QGridLayout()
        grid.setSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        # ── Graphe 1 : nombre
        self.frame_nombre = GraphFrame(
            "Nombre consultations par mois + moyenne journalière",
            "fa5s.chart-line", Theme.PURPLE)
        self.frame_nombre.setMinimumHeight(260)
        self.graph_nombre = ConsultationNombreGraph(width=5.2, height=3.1)
        self.frame_nombre.graph_layout.addWidget(self.graph_nombre)
        grid.addWidget(self.frame_nombre, 0, 0)

        # ── Graphe 2 : montant
        self.frame_montant = GraphFrame(
            "Montant consultations par mois + moyenne journalière",
            "fa5s.chart-area", Theme.BLUE)
        self.frame_montant.setMinimumHeight(260)
        self.graph_montant = ConsultationMontantGraph(width=5.2, height=3.1)
        self.frame_montant.graph_layout.addWidget(self.graph_montant)
        grid.addWidget(self.frame_montant, 0, 1)

        # ── Frame 3 : jauges
        self.frame_bas_gauche = GraphFrame(
            "Taux de conversion par service", "fa5s.tachometer-alt", Theme.GREEN)
        self.frame_bas_gauche.setMinimumHeight(230)

        gauges_container = QWidget()
        gauges_container.setStyleSheet("background: transparent;")
        gl = QHBoxLayout(gauges_container)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.setSpacing(16)
        gl.addStretch()

        self.gauge_examen    = SemiCircleGauge("Examen",           width=2.0, height=2.0)
        self.gauge_chirurgie = SemiCircleGauge("Chirurgie",         width=2.0, height=2.0)
        self.gauge_lunette   = SemiCircleGauge("Commande lunette",  width=2.0, height=2.0)

        for g in (self.gauge_examen, self.gauge_chirurgie, self.gauge_lunette):
            gl.addWidget(g)
        gl.addStretch()

        self.frame_bas_gauche.graph_layout.addStretch()
        self.frame_bas_gauche.graph_layout.addWidget(gauges_container, 0, Qt.AlignCenter)
        self.frame_bas_gauche.graph_layout.addStretch()
        grid.addWidget(self.frame_bas_gauche, 1, 0)

        # ── Frame 4 : détail hebdo — 2 colonnes ──────────────
        self.frame_bas_droite = GraphFrame(
            "Détail hebdomadaire des consultations",
            "fa5s.calendar-alt", Theme.AMBER)
        self.frame_bas_droite.setMinimumHeight(230)
        self.frame_bas_droite.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        two_col = QHBoxLayout()
        two_col.setContentsMargins(0, 4, 0, 0)
        two_col.setSpacing(12)

        # — Colonne gauche —
        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(6)

        combos_row = QHBoxLayout()
        combos_row.setContentsMargins(0, 0, 0, 0)
        combos_row.setSpacing(8)

        self.combo_mois = QComboBox()
        self.combo_mois.setFixedHeight(30)
        self.combo_mois.setMinimumWidth(130)
        self.combo_mois.addItem("Choisir un mois", None)
        for libelle, num in self._mois_options():
            self.combo_mois.addItem(libelle, num)
        self.combo_mois.setCurrentIndex(0)

        self.combo_semaine = QComboBox()
        self.combo_semaine.setFixedHeight(30)
        self.combo_semaine.setMinimumWidth(170)
        self.combo_semaine.addItem("Choisir une semaine", None)
        self.combo_semaine.setEnabled(False)

        combos_row.addWidget(self.combo_mois)
        combos_row.addWidget(self.combo_semaine)
        combos_row.addStretch()
        left_col.addLayout(combos_row)

        self.lbl_week_hint = QLabel("Sélectionne d'abord le mois puis la semaine")
        self.lbl_week_hint.setStyleSheet(
            f"color:{Theme.TEXT_MUTED}; font-size:10px; border:none;")
        left_col.addWidget(self.lbl_week_hint)

        self.days_container = QWidget()
        self.days_container.setStyleSheet("background: transparent;")
        self.days_layout = QVBoxLayout(self.days_container)
        self.days_layout.setContentsMargins(0, 2, 0, 0)
        self.days_layout.setSpacing(3)
        self.day_rows = []
        for _ in range(7):
            row_w = DayStatRow()
            self.day_rows.append(row_w)
            self.days_layout.addWidget(row_w)
        self.days_container.hide()
        left_col.addWidget(self.days_container)
        left_col.addStretch()

        # — Séparateur —
        sep_v = QFrame()
        sep_v.setFrameShape(QFrame.VLine)
        sep_v.setFixedWidth(1)
        sep_v.setStyleSheet(f"background:{Theme.BORDER}; border:none;")

        # — Colonne droite : résumé par année —
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(7)

        # Titre colonne
        yr_title = QLabel("Récapitulatif annuel")
        yr_title.setStyleSheet(
            f"color:{Theme.TEXT_SECONDARY}; font-size:10px; font-weight:700; "
            f"letter-spacing:1px; border:none;"
        )
        right_col.addWidget(yr_title)

        _YEAR_DATA = [
            (2022, "fa5s.chart-bar",     Theme.YEAR_COLORS[2022], "12 450 000 GNF"),
            (2023, "fa5s.chart-bar",     Theme.YEAR_COLORS[2023], "18 730 000 GNF"),
            (2024, "fa5s.chart-bar",     Theme.YEAR_COLORS[2024], "23 100 000 GNF"),
            (2025, "fa5s.chart-bar",     Theme.YEAR_COLORS[2025], "31 560 000 GNF"),
            (2026, "fa5s.chart-bar",     Theme.YEAR_COLORS[2026], "9 870 000 GNF"),
        ]

        for year, icon_name, color, amount in _YEAR_DATA:
            yr_frame = QFrame()
            yr_frame.setFixedHeight(36)
            yr_frame.setStyleSheet(
                f"QFrame {{ background: {color}18; border-radius: 10px; "
                f"border: 1px solid {color}40; }}"
            )
            yr_lay = QHBoxLayout(yr_frame)
            yr_lay.setContentsMargins(8, 0, 10, 0)
            yr_lay.setSpacing(7)

            # Icône
            ico_lbl = QLabel()
            ico_lbl.setFixedSize(18, 18)
            ico_lbl.setAlignment(Qt.AlignCenter)
            ico_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(QSize(14, 14)))
            ico_lbl.setStyleSheet("border:none; background:transparent;")

            # Année
            yr_lbl = QLabel(str(year))
            yr_lbl.setStyleSheet(
                f"color:{color}; font-size:12px; font-weight:800; "
                f"border:none; background:transparent;"
            )

            # Montant
            amt_lbl = QLabel(amount)
            amt_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amt_lbl.setStyleSheet(
                f"color:{Theme.TEXT_PRIMARY}; font-size:10px; font-weight:600; "
                f"border:none; background:transparent;"
            )

            yr_lay.addWidget(ico_lbl)
            yr_lay.addWidget(yr_lbl)
            yr_lay.addStretch()
            yr_lay.addWidget(amt_lbl)
            right_col.addWidget(yr_frame)

        right_col.addStretch()

        two_col.addLayout(left_col, stretch=3)
        two_col.addWidget(sep_v)
        two_col.addLayout(right_col, stretch=2)

        self.frame_bas_droite.graph_layout.addLayout(two_col)
        grid.addWidget(self.frame_bas_droite, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        parent.addLayout(grid)

        self.frame_bas_gauche.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.frame_bas_droite.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.combo_mois.currentIndexChanged.connect(self._on_month_changed)
        self.combo_semaine.currentIndexChanged.connect(self._on_week_combo_changed)

    # ── Helpers contrôleur ───────────────────────────────────
    def _call_ctrl(self, method_names, default=0):
        for name in method_names:
            fn = getattr(self.controleur, name, None)
            if callable(fn):
                return fn(self.code_session)
        return default

    def _call_ctrl_args(self, method_names, *args, default=0):
        for name in method_names:
            fn = getattr(self.controleur, name, None)
            if callable(fn):
                return fn(self.code_session, *args)
        return default

    def _extraire_pourcentage(self, data: dict, keys, default=0.0) -> float:
        if not isinstance(data, dict):
            return float(default)
        for key in keys:
            if key in data and data[key] is not None:
                try:
                    return float(data[key])
                except Exception:
                    return float(default)
        return float(default)

    # ── Options mois / semaines ───────────────────────────────
    def _mois_options(self):
        return [
            ("Janvier", 1), ("Février", 2), ("Mars", 3), ("Avril", 4),
            ("Mai", 5), ("Juin", 6), ("Juillet", 7), ("Août", 8),
            ("Septembre", 9), ("Octobre", 10), ("Novembre", 11), ("Décembre", 12),
        ]

    def _week_color(self, week_idx: int) -> str:
        colors = [Theme.PURPLE, Theme.TEAL, Theme.AMBER, Theme.BLUE]
        return colors[week_idx % len(colors)]

    def _apply_week_combo_style(self, accent_color: str = None):
        if not accent_color:
            self.combo_semaine.setStyleSheet(
                f"QComboBox {{ background: {Theme.BG_SURFACE}; color: {Theme.TEXT_SECONDARY}; "
                f"border: 1px solid {Theme.BORDER}; border-radius: 10px; "
                f"padding: 5px 12px; font-size: 11px; font-weight: 600; }} "
                f"QComboBox::drop-down {{ border: none; width: 16px; }} "
                f"QComboBox::down-arrow {{ image: none; }} "
                f"QComboBox QAbstractItemView {{ background: {Theme.BG_CARD}; "
                f"color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_BRIGHT}; "
                f"border-radius: 8px; selection-background-color: {Theme.BG_SURFACE}; }}"
            )
        else:
            self.combo_semaine.setStyleSheet(
                f"QComboBox {{ background: {accent_color}; color: white; "
                f"border: none; border-radius: 10px; "
                f"padding: 5px 12px; font-size: 11px; font-weight: 700; }} "
                f"QComboBox::drop-down {{ border: none; width: 16px; }} "
                f"QComboBox::down-arrow {{ image: none; }} "
                f"QComboBox QAbstractItemView {{ background: {Theme.BG_CARD}; "
                f"color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_BRIGHT}; "
                f"border-radius: 8px; selection-background-color: {Theme.BG_SURFACE}; }}"
            )

    def _get_selected_week_index(self):
        data = self.combo_semaine.currentData()
        return int(data) if data is not None else None

    # ── Slots combos ─────────────────────────────────────────
    def _on_month_changed(self, _index):
        month_data = self.combo_mois.currentData()
        self.days_container.hide()
        self.lbl_week_hint.show()
        self._apply_week_combo_style(None)

        self.combo_semaine.blockSignals(True)
        self.combo_semaine.clear()
        self.combo_semaine.addItem("Choisir une semaine", None)
        self.combo_semaine.blockSignals(False)

        if month_data is None:
            self.combo_semaine.setEnabled(False)
            return

        self.combo_semaine.setEnabled(True)
        self._selected_year = datetime.now().year
        self._selected_month = int(month_data)
        self._selected_month_last_day = calendar.monthrange(
            self._selected_year, self._selected_month)[1]

        self._stats_nombre_jour = self._call_ctrl_args(
            ["obtenir_nombre_par_jour"],
            self._selected_year, self._selected_month, default={})
        self._stats_montant_jour = self._call_ctrl_args(
            ["obtenir_montant_par_jour"],
            self._selected_year, self._selected_month, default={})

        for i in range(4):
            start = 1 + (i * 7)
            if start > self._selected_month_last_day:
                break
            end = min(start + 6, self._selected_month_last_day)
            self.combo_semaine.addItem(
                qta.icon("fa5s.circle", color=self._week_color(i)),
                f"Semaine {i + 1}  ({start:02d}–{end:02d})",
                i,
            )

    def _on_week_combo_changed(self, _index):
        week_idx = self.combo_semaine.currentData()
        if week_idx is None:
            self.days_container.hide()
            self.lbl_week_hint.show()
            self._apply_week_combo_style(None)
            return
        self._apply_week_combo_style(self._week_color(int(week_idx)))
        self.lbl_week_hint.hide()
        self.days_container.show()
        self._afficher_semaine(int(week_idx))

    def _weekday_fr(self, year: int, month: int, day: int) -> str:
        return ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"][
            datetime(year, month, day).weekday()
        ]

    def _afficher_semaine(self, week_idx: int):
        start_day = 1 + (week_idx * 7)
        accent    = self._week_color(week_idx)
        for offset in range(7):
            day_num = start_day + offset
            row     = self.day_rows[offset]
            row.set_accent_color(accent)
            if day_num > self._selected_month_last_day:
                row.update_values("--", 0, 0.0, active=False)
                continue
            key     = f"{day_num:02d}"
            nb      = int(self._stats_nombre_jour.get(key, 0))
            montant = float(self._stats_montant_jour.get(key, 0.0))
            label   = f"{self._weekday_fr(self._selected_year, self._selected_month, day_num)} {day_num:02d}"
            row.update_values(label, nb, montant, active=True)

    # ── Chargement données ────────────────────────────────────
    def charger_donnees(self):
        if not self.code_session:
            return
        try:
            nb_jour        = self._call_ctrl(["obtenir_consultations_aujourd_hui"], default=0)
            nb_session     = self._call_ctrl(
                ["obtenir_nombre_total", "obtenir_total_consultations_session"], default=0)
            montant_jour   = self._call_ctrl(
                ["obtenir_montant_aujourd_hui", "obtenir_montant_consultations_aujourd_hui"], default=0.0)
            montant_session = self._call_ctrl(
                ["obtenir_montant_session", "obtenir_montant_consultations_session"], default=0.0)

            self.card_nb_jour.update_value(str(nb_jour))
            self.card_nb_session.update_value(str(nb_session))
            self.card_montant_jour.update_value(f"{montant_jour:,.0f}".replace(",", " "))
            self.card_montant_session.update_value(f"{montant_session:,.0f}".replace(",", " "))

            nombre_par_mois  = self._call_ctrl(["obtenir_nombre_par_mois"], default={})
            moy_nb_par_mois  = self._call_ctrl(
                ["obtenir_moyenne_nombre_journalier_par_mois",
                 "obtenir_moyenne_consultations_par_mois"], default={})
            self.graph_nombre.update_graph(nombre_par_mois, moy_nb_par_mois)

            montant_par_mois     = self._call_ctrl(["obtenir_montant_par_mois"], default={})
            moy_montant_par_mois = self._call_ctrl(
                ["obtenir_moyenne_montant_journalier_par_mois",
                 "obtenir_revenu_moyen_par_mois"], default={})
            self.graph_montant.update_graph(montant_par_mois, moy_montant_par_mois)

            taux_services  = self._call_ctrl(["obtenir_taux_conversion"], default={})
            pct_examen     = self._extraire_pourcentage(taux_services, ["examen"])
            pct_chirurgie  = self._extraire_pourcentage(taux_services, ["chirurgie", "chiurgie"])
            pct_lunette    = self._extraire_pourcentage(
                taux_services, ["lunette", "commandelunette", "commande_lunette"])
            self.gauge_examen.update_value(pct_examen)
            self.gauge_chirurgie.update_value(pct_chirurgie)
            self.gauge_lunette.update_value(pct_lunette)

            if hasattr(self, "combo_mois"):
                selected_week = self._get_selected_week_index()
                month_data    = self.combo_mois.currentData()
                if month_data is None:
                    self.days_container.hide()
                    self.lbl_week_hint.show()
                else:
                    self._selected_year = datetime.now().year
                    self._selected_month = int(month_data)
                    self._selected_month_last_day = calendar.monthrange(
                        self._selected_year, self._selected_month)[1]
                    self._stats_nombre_jour = self._call_ctrl_args(
                        ["obtenir_nombre_par_jour"],
                        self._selected_year, self._selected_month, default={})
                    self._stats_montant_jour = self._call_ctrl_args(
                        ["obtenir_montant_par_jour"],
                        self._selected_year, self._selected_month, default={})
                    if selected_week is not None:
                        self.days_container.show()
                        self.lbl_week_hint.hide()
                        self._afficher_semaine(selected_week)
                    else:
                        self.days_container.hide()
                        self.lbl_week_hint.show()

        except Exception as e:
            print(f"[AnalyseConsultationView] Erreur chargement données: {e}")
            import traceback; traceback.print_exc()

    def rafraichir(self):
        self.charger_donnees()