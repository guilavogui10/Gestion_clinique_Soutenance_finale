"""
Analyse consultation:
- Graphe 1: nombre par mois + moyenne journaliere du nombre
- Graphe 2: montant par mois + moyenne journaliere du montant
- 4 cards KPI
"""

import calendar
from datetime import datetime
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, FuncFormatter
from matplotlib.patches import Wedge, Circle

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGraphicsDropShadowEffect, QGridLayout, QComboBox, QSizePolicy,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDateEdit, QTabWidget
)
from PySide6.QtCore import QSize, Qt, QDate, QTimer
from PySide6.QtGui import QColor
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class _TC:
    """Descripteur de couleur thématique pour graphiques."""
    def __init__(self, key):
        self._key = key
    def __set_name__(self, owner, name):
        self._name = name
    def __get__(self, obj, objtype=None):
        return theme_manager.colors()[self._key]


class ModernTheme:
    primary    = _TC('primary')
    success    = _TC('success')
    warning    = _TC('warning')
    danger     = _TC('danger')
    info       = _TC('info')
    accent     = _TC('accent')
    blue       = _TC('info')
    text       = _TC('text_primary')
    subtext    = _TC('text_secondary')
    surface    = _TC('bg_card')
    border     = _TC('border')

    @property
    def COLORS(self):
        return {
            "primary":  self.primary,
            "success":  self.success,
            "warning":  self.warning,
            "danger":   self.danger,
            "info":     self.info,
            "accent":   self.accent,
            "blue":     self.blue,
            "text":     self.text,
            "subtext":  self.subtext,
            "surface":  self.surface,
            "border":   self.border,
        }


class BaseGraph(FigureCanvas):
    MONTH_LABELS = [
        "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
        "Juil", "Août", "Sep", "Oct", "Nov", "Déc",
    ]

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.theme = ModernTheme()
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor("none")
        self.hover_text = self.fig.text(0.5, 0.96, '', ha='center', va='top', fontsize=10, fontweight='bold')
        super().__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet("background: transparent;")
        self.scatters = []
        self._setup_style()
        self.mpl_connect("motion_notify_event", self._on_hover)
        self.mpl_connect("axes_leave_event", lambda e: self._clear_hover_text())
        self.mpl_connect("figure_leave_event", lambda e: self._clear_hover_text())

    def _setup_style(self):
        for spine in self.axes.spines.values():
            spine.set_visible(False)
        self.axes.grid(
            True, axis="y", linestyle="--", alpha=0.3,
            color=self.theme.COLORS["border"], linewidth=0.8,
        )
        self.axes.tick_params(
            colors=self.theme.COLORS["subtext"], labelsize=9, length=0, pad=8
        )
        if hasattr(self, 'hover_text'):
            self.hover_text.set_text('')
        self.fig.subplots_adjust(left=0.1, right=0.9, top=0.85, bottom=0.15)

    def _draw_linear_curve(self, x, y, color, label, linestyle="-", alpha=0.9, axis=None):
        target_ax = axis if axis else self.axes
        if len(y) < 2 or float(np.sum(y)) == 0.0:
            return
        target_ax.plot(
            x, y, color=color, linewidth=2.0,
            linestyle=linestyle, label=label, alpha=alpha, antialiased=True, zorder=5
        )

    def _format_value(self, val: float, fmt: str) -> str:
        if fmt == "count":
            return f"{int(round(val))} consult."
        elif fmt == "money":
            if val >= 1_000_000:
                return f"{val / 1_000_000:.2f}M GNF"
            return f"{int(round(val)):,} GNF".replace(",", " ")
        elif fmt == "average_count":
            return f"moy. {val:.1f} / jour"
        elif fmt == "average_money":
            if val >= 1_000_000:
                return f"moy. {val / 1_000_000:.2f}M GNF/j"
            return f"moy. {int(round(val)):,} GNF/j".replace(",", " ")
        else:
            return f"{int(round(val)):,}".replace(",", " ")

    def _draw_points(self, x, y, color, tooltip_label, fmt="count", axis=None):
        target_ax = axis if axis else self.axes
        sc = target_ax.scatter(
            x, y,
            color=color,
            edgecolor=self.theme.COLORS["surface"],
            s=50, zorder=10, linewidth=1.5, alpha=1.0,
        )
        self.scatters.append({'scatter': sc, 'label': tooltip_label, 'x': x, 'y': y, 'fmt': fmt})

    def _on_hover(self, event):
        if not event.inaxes:
            self._clear_hover_text()
            return
        found = False
        for item in self.scatters:
            cont, ind = item['scatter'].contains(event)
            if cont:
                idx = ind["ind"][0]
                value = item['y'][idx]
                label = item['label']
                fmt = item['fmt']
                month = self.MONTH_LABELS[idx] if 0 <= idx < len(self.MONTH_LABELS) else ""
                val_txt = self._format_value(value, fmt)
                txt = f"{label} en {month} : {val_txt}" if month else f"{label} : {val_txt}"
                if self.hover_text.get_text() != txt:
                    self.hover_text.set_text(txt)
                    self.hover_text.set_color(self.theme.COLORS["text"])
                    self.fig.canvas.draw_idle()
                found = True
                break
        if not found and self.hover_text.get_text() != '':
            self._clear_hover_text()

    def _clear_hover_text(self):
        self.hover_text.set_text('')
        self.fig.canvas.draw_idle()

    def _set_x_axis(self, x):
        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.MONTH_LABELS, rotation=0)

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
        upper = float(nice * magnitude)
        return max(upper, float(min_upper))

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

    def _style_legend(self, ax=None):
        target = ax or self.axes
        leg = target.get_legend()
        if leg is None:
            return
        leg.get_frame().set_facecolor("none")
        leg.get_frame().set_edgecolor("none")
        leg.get_frame().set_alpha(0)
        for txt in leg.get_texts():
            txt.set_color(self.theme.COLORS["subtext"])
            txt.set_fontsize(7)
            txt.set_fontweight("600")


class ConsultationNombreGraph(BaseGraph):
    def update_graph(self, nombre_par_mois: dict, moyenne_par_mois: dict):
        if hasattr(self, "avg_axis") and self.avg_axis is not None:
            try:
                self.avg_axis.remove()
            except Exception:
                pass
            self.avg_axis = None

        self.axes.clear()
        self.scatters.clear()
        self._setup_style()

        x = np.arange(len(self.MONTH_LABELS))
        y_nb = np.array([nombre_par_mois.get(m, 0) for m in self.MONTH_LABELS], dtype=float)
        y_avg = np.array([moyenne_par_mois.get(m, 0) for m in self.MONTH_LABELS], dtype=float)

        self._draw_linear_curve(x, y_nb, self.theme.COLORS["primary"], "Nombre consultations")
        self._draw_points(x, y_nb, self.theme.COLORS["primary"], "Consultations", "count")

        self.avg_axis = self.axes.twinx()
        for spine_name, spine in self.avg_axis.spines.items():
            spine.set_visible(spine_name == "right")
        self.avg_axis.spines["right"].set_color(self.theme.COLORS["border"])
        self.avg_axis.spines["right"].set_linewidth(0.8)
        self.avg_axis.grid(False)
        self.avg_axis.tick_params(
            colors=self.theme.COLORS["blue"], labelsize=8, length=0, pad=6
        )
        self.avg_axis.set_ylabel(
            "Moyenne / jour", color=self.theme.COLORS["blue"], fontsize=9, fontweight="500"
        )

        self._draw_linear_curve(x, y_avg, self.theme.COLORS["blue"], "Moyenne journaliere", linestyle="--", axis=self.avg_axis)
        self._draw_points(x, y_avg, self.theme.COLORS["blue"], "Moy. journalière", "average_count", axis=self.avg_axis)

        self._set_x_axis(x)
        self._set_ylim_counts(y_nb.tolist())

        avg_vals = [float(v) for v in y_avg.tolist() if v > 0]
        avg_max = max(avg_vals) if avg_vals else 0.0
        avg_upper = self._nice_upper_bound(avg_max * 1.15, min_upper=1.0)
        self.avg_axis.set_ylim(0, avg_upper)
        self.avg_axis.yaxis.set_major_locator(MaxNLocator(nbins=5))

        self.axes.set_ylabel(
            "Consultations", color=self.theme.COLORS["subtext"], fontsize=10, fontweight="500"
        )
        h1, l1 = self.axes.get_legend_handles_labels()
        h2, l2 = self.avg_axis.get_legend_handles_labels()
        self.axes.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=7, framealpha=0)
        self._style_legend()
        self._finalize()


class ConsultationMontantGraph(BaseGraph):
    def update_graph(self, montant_par_mois: dict, moyenne_par_mois: dict):
        self.axes.clear()
        self.scatters.clear()
        self._setup_style()

        x = np.arange(len(self.MONTH_LABELS))
        y_tot = np.array([montant_par_mois.get(m, 0) for m in self.MONTH_LABELS], dtype=float)
        y_avg = np.array([moyenne_par_mois.get(m, 0) for m in self.MONTH_LABELS], dtype=float)

        self._draw_linear_curve(x, y_tot, self.theme.COLORS["accent"], "Montant total")
        self._draw_points(x, y_tot, self.theme.COLORS["accent"], "Montant total", "money")

        self._draw_linear_curve(
            x, y_avg, self.theme.COLORS["warning"], "Moy. journalière", linestyle="--"
        )
        self._draw_points(x, y_avg, self.theme.COLORS["warning"], "Moy. journalière", "average_money")

        self._set_x_axis(x)
        self._set_ylim_amounts(y_tot.tolist(), y_avg.tolist())
        self.axes.set_ylabel(
            "Montant (GNF)", color=self.theme.COLORS["subtext"], fontsize=10, fontweight="500"
        )
        self.axes.yaxis.set_visible(False)
        self.axes.legend(loc="upper left", fontsize=7, framealpha=0)
        self._style_legend()
        self._finalize()


class SemiCircleGauge(FigureCanvas):
    def __init__(self, label: str, parent=None, width=1.9, height=1.9, dpi=100):
        self.label = label
        self.theme = ModernTheme()
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor("none")
        super().__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet("background: transparent;")
        self.update_value(0.0)

    def _color_for_percent(self, percent: float) -> str:
        c = theme_manager.colors()
        if percent < 35:
            return c['danger']
        if percent < 70:
            return c['warning']
        return c['success']

    def update_value(self, percent):
        try:
            p = float(percent)
        except Exception:
            p = 0.0

        # Compatibilite: accepte aussi les ratios 0..1
        if 0 < p <= 1:
            p = p * 100.0
        p = max(0.0, min(100.0, p))

        color = self._color_for_percent(p)

        self.axes.clear()
        self.axes.set_facecolor("none")
        self.axes.axis("off")

        # Cercle de fond (piste)
        self.axes.add_patch(
            Wedge((0, 0), 1.0, 0, 360, width=0.24, facecolor=theme_manager.color('border'), edgecolor="none")
        )

        # Cercle valeur (progression)
        angle = 360.0 * (p / 100.0)
        start_angle = 90.0
        end_angle = start_angle + angle
        if p > 0:
            self.axes.add_patch(
                Wedge((0, 0), 1.0, start_angle, end_angle, width=0.24, facecolor=color, edgecolor="none")
            )

            # Petit marqueur circulaire sur l'extremite du pourcentage
            theta = np.deg2rad(end_angle)
            marker_x = 0.88 * np.cos(theta)
            marker_y = 0.88 * np.sin(theta)
            self.axes.add_patch(Circle((marker_x, marker_y), 0.09, facecolor=color, edgecolor=theme_manager.color('text_inverse'), linewidth=1.0))

        self.axes.text(
            0, 0.02, f"{p:.0f}%",
            ha="center", va="center",
            fontsize=12, fontweight="bold", color=self.theme.COLORS["subtext"],
        )
        self.axes.text(
            0, -1.18, self.label,
            ha="center", va="center",
            fontsize=9, color=self.theme.COLORS["subtext"],
        )

        self.axes.set_xlim(-1.25, 1.25)
        self.axes.set_ylim(-1.28, 1.2)
        self.draw()


class KPICard(QFrame):
    def __init__(self, titre: str, valeur: str, icone: str, couleur: str, unite: str = "", parent=None):
        super().__init__(parent)
        self._icone = icone
        self._couleur = couleur
        self._build(titre, valeur, icone, couleur, unite)

    def _build(self, titre, valeur, icone, couleur, unite):
        self.setMaximumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet(
            f"QFrame {{ background-color: {theme_manager.color('bg_card')}; border-radius: 12px; border: 1px solid {theme_manager.color('border')}; }}"
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(4)

        hdr = QHBoxLayout()
        self._ico = QLabel()
        self._ico.setPixmap(qta.icon(icone, color=couleur).pixmap(QSize(22, 22)))
        self._ico.setStyleSheet("border:none;")
        self._ttl = QLabel(titre)
        self._ttl.setStyleSheet(f"color:{theme_manager.color('text_secondary')}; font-size:11px; font-weight:600; border:none;")
        hdr.addWidget(self._ico)
        hdr.addSpacing(6)
        hdr.addWidget(self._ttl)
        hdr.addStretch()
        layout.addLayout(hdr)

        self._val_lbl = QLabel(valeur)
        self._val_lbl.setStyleSheet(
            f"color:{couleur}; font-size:24px; font-weight:bold; border:none;"
        )
        layout.addWidget(self._val_lbl)

        self._unite_lbl = None
        if unite:
            self._unite_lbl = QLabel(unite)
            self._unite_lbl.setStyleSheet(f"color:{theme_manager.color('text_muted')}; font-size:10px; border:none;")
            layout.addWidget(self._unite_lbl)
        layout.addStretch()

    def apply_theme(self, couleur: str = None):
        if couleur:
            self._couleur = couleur
        c = self._couleur
        self.setStyleSheet(
            f"QFrame {{ background-color: {theme_manager.color('bg_card')}; border-radius: 12px; border: 1px solid {theme_manager.color('border')}; }}"
        )
        self._ico.setPixmap(qta.icon(self._icone, color=c).pixmap(QSize(22, 22)))
        self._ttl.setStyleSheet(f"color:{theme_manager.color('text_secondary')}; font-size:11px; font-weight:600; border:none;")
        self._val_lbl.setStyleSheet(f"color:{c}; font-size:24px; font-weight:bold; border:none;")
        if self._unite_lbl:
            self._unite_lbl.setStyleSheet(f"color:{theme_manager.color('text_muted')}; font-size:10px; border:none;")

    def update_value(self, v: str):
        self._val_lbl.setText(v)


class GraphFrame(QFrame):
    def __init__(self, titre: str, icone: str, parent=None):
        super().__init__(parent)
        self._icone = icone
        self.setStyleSheet(
            f"QFrame {{ background-color: {theme_manager.color('bg_card')}; border-radius: 18px; border: 1px solid {theme_manager.color('border')}; }}"
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        hdr = QHBoxLayout()
        self._ico = QLabel()
        self._ico.setPixmap(qta.icon(icone, color=theme_manager.color('primary')).pixmap(QSize(18, 18)))
        self._ico.setStyleSheet("border:none;")
        self._ttl = QLabel(titre)
        self._ttl.setStyleSheet(f"font-weight:bold; color:{theme_manager.color('text_primary')}; font-size:13px; border:none;")
        hdr.addWidget(self._ico)
        hdr.addSpacing(6)
        hdr.addWidget(self._ttl)
        hdr.addStretch()
        root.addLayout(hdr)

        self._sep = QFrame()
        self._sep.setFixedHeight(1)
        self._sep.setStyleSheet(f"background:{theme_manager.color('border')}; border:none;")
        root.addWidget(self._sep)

        self.graph_layout = QVBoxLayout()
        self.graph_layout.setContentsMargins(0, 0, 0, 0)
        root.addLayout(self.graph_layout, 1)

    def apply_theme(self):
        self.setStyleSheet(
            f"QFrame {{ background-color: {theme_manager.color('bg_card')}; border-radius: 18px; border: 1px solid {theme_manager.color('border')}; }}"
        )
        self._ico.setPixmap(qta.icon(self._icone, color=theme_manager.color('primary')).pixmap(QSize(18, 18)))
        self._ttl.setStyleSheet(f"font-weight:bold; color:{theme_manager.color('text_primary')}; font-size:13px; border:none;")
        self._sep.setStyleSheet(f"background:{theme_manager.color('border')}; border:none;")


class DayStatRow(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._accent = theme_manager.color('accent')
        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        self.setFixedHeight(16)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 0, 1, 0)
        layout.setSpacing(3)

        self.lbl_icon = QLabel()
        self.lbl_icon.setFixedSize(10, 10)
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_jour = QLabel("--")
        self.lbl_jour.setStyleSheet(f"color:{theme_manager.color('text_secondary')}; font-size:8px; font-weight:600; border:none;")

        self.lbl_nombre = QLabel("0 consultations")
        self.lbl_nombre.setStyleSheet(f"color:{theme_manager.color('text_secondary')}; font-size:8px; font-weight:600; border:none;")

        self.lbl_montant = QLabel("0 GNF")
        self.lbl_montant.setStyleSheet(f"color:{theme_manager.color('text_primary')}; font-size:8px; font-weight:700; border:none;")

        left = QHBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(4)
        left.addWidget(self.lbl_icon)
        left.addWidget(self.lbl_jour)

        layout.addLayout(left)
        layout.addStretch()
        layout.addWidget(self.lbl_nombre)
        layout.addSpacing(3)
        layout.addWidget(self.lbl_montant)
        self.set_accent_color(self._accent)

    def set_accent_color(self, color: str):
        self._accent = color
        self.lbl_icon.setStyleSheet(
            f"background-color:{color}; border-radius:5px; border:none;"
        )
        self.lbl_icon.setPixmap(qta.icon("fa5s.calendar-day", color=theme_manager.color('text_inverse')).pixmap(QSize(6, 6)))

    def update_values(self, jour_label: str, nombre: int, montant: float, active: bool = True):
        self.lbl_jour.setText(jour_label)
        self.lbl_nombre.setText(f"{int(nombre)} consultations")
        self.lbl_montant.setText(f"{montant:,.0f} GNF".replace(",", " "))

        if active:
            self.setStyleSheet("QFrame { background: transparent; border: none; }")
            self.lbl_icon.show()
            self.lbl_jour.setStyleSheet(f"color:{theme_manager.color('text_secondary')}; font-size:8px; font-weight:600; border:none;")
            self.lbl_nombre.setStyleSheet(f"color:{theme_manager.color('text_secondary')}; font-size:8px; font-weight:600; border:none;")
            self.lbl_montant.setStyleSheet(f"color:{theme_manager.color('text_primary')}; font-size:8px; font-weight:700; border:none;")
        else:
            self.setStyleSheet("QFrame { background: transparent; border: none; }")
            self.lbl_icon.hide()
            self.lbl_jour.setStyleSheet(f"color:{theme_manager.color('text_muted')}; font-size:8px; font-weight:600; border:none;")
            self.lbl_nombre.setStyleSheet(f"color:{theme_manager.color('text_muted')}; font-size:8px; font-weight:600; border:none;")
            self.lbl_montant.setStyleSheet(f"color:{theme_manager.color('text_muted')}; font-size:8px; font-weight:700; border:none;")


class LegacyAnalyseConsultationView(QWidget):
    BLEU = _TC('info')
    VERT = _TC('success')
    VIOLET = _TC('accent')
    ORANGE = _TC('warning')

    def __init__(self, controleur, code_session: str, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.code_session = code_session
        self._build_ui()
        self.charger_donnees()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        self._build_kpi_row(root)
        self._build_graphs(root)

    def _build_kpi_row(self, parent):
        row = QHBoxLayout()
        row.setSpacing(10)
        self.card_nb_jour = KPICard(
            "Consultations du jour", "0", "fa5s.calendar-day", self.BLEU, "consultations"
        )
        self.card_nb_session = KPICard(
            "Total consultations session", "0", "fa5s.chart-line", self.VERT, "consultations"
        )
        self.card_montant_jour = KPICard(
            "Montant consultations du jour", "0", "fa5s.money-bill-wave", self.VIOLET, "GNF"
        )
        self.card_montant_session = KPICard(
            "Montant consultations session", "0", "fa5s.wallet", self.ORANGE, "GNF"
        )
        for card in (
            self.card_nb_jour,
            self.card_nb_session,
            self.card_montant_jour,
            self.card_montant_session,
        ):
            row.addWidget(card)
        parent.addLayout(row)

    def _build_graphs(self, parent):
        from views.analyses.responsive_analyses import AnalyseResponsiveGrid
        self._resp_grid = AnalyseResponsiveGrid(spacing=10)

        # Frame graphe nombre
        self.frame_nombre = GraphFrame(
            "Nombre consultations par mois + moyenne journaliere", "fa5s.chart-line"
        )
        self.graph_nombre = ConsultationNombreGraph(width=3, height=1.6)
        self.graph_nombre.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graph_nombre.setMinimumHeight(0)
        self.frame_nombre.graph_layout.addWidget(self.graph_nombre)

        # Frame graphe montant
        self.frame_montant = GraphFrame(
            "Montant consultations par mois + moyenne journaliere", "fa5s.chart-area"
        )
        self.graph_montant = ConsultationMontantGraph(width=3, height=1.6)
        self.graph_montant.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graph_montant.setMinimumHeight(0)
        self.frame_montant.graph_layout.addWidget(self.graph_montant)

        # Frame gauche bas (cercles de conversion services)
        self.frame_bas_gauche = GraphFrame(
            "Taux services (cercles)", "fa5s.tachometer-alt"
        )
        gauges_container = QWidget()
        gauges_container.setStyleSheet("background: transparent;")
        gauges_layout = QHBoxLayout(gauges_container)
        gauges_layout.setContentsMargins(0, 0, 0, 0)
        gauges_layout.setSpacing(18)
        gauges_layout.addStretch()

        self.gauge_examen = SemiCircleGauge("Examen", width=1.5, height=1.5)
        self.gauge_chirurgie = SemiCircleGauge("Chirurgie", width=1.5, height=1.5)
        self.gauge_lunette = SemiCircleGauge("Commande lunette", width=1.5, height=1.5)

        gauges_layout.addWidget(self.gauge_examen)
        gauges_layout.addWidget(self.gauge_chirurgie)
        gauges_layout.addWidget(self.gauge_lunette)
        gauges_layout.addStretch()

        self.frame_bas_gauche.graph_layout.addStretch()
        self.frame_bas_gauche.graph_layout.addWidget(gauges_container, 0, Qt.AlignCenter)
        self.frame_bas_gauche.graph_layout.addStretch()

        # Frame droite bas (détail hebdomadaire)
        self.frame_bas_droite = GraphFrame(
            "Détail hebdomadaire des consultations", "fa5s.calendar-alt"
        )
        self.frame_bas_droite.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        two_col = QHBoxLayout()
        two_col.setContentsMargins(0, 0, 0, 0)
        two_col.setSpacing(8)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(2)

        combos_row = QHBoxLayout()
        combos_row.setContentsMargins(0, 0, 0, 0)
        combos_row.setSpacing(8)

        self.combo_mois = QComboBox()
        self.combo_mois.setFixedHeight(22)
        self.combo_mois.setMinimumWidth(110)
        self.combo_mois.addItem("Choisir un mois", None)
        for libelle, num in self._mois_options():
            self.combo_mois.addItem(libelle, num)
        self.combo_mois.setCurrentIndex(0)
        self._apply_combo_mois_style()

        self.combo_semaine = QComboBox()
        self.combo_semaine.setFixedHeight(22)
        self.combo_semaine.setMinimumWidth(140)
        self.combo_semaine.addItem("Choisir une semaine", None)
        self.combo_semaine.setEnabled(False)
        self._apply_week_combo_style(None)

        combos_row.addWidget(self.combo_mois)
        combos_row.addWidget(self.combo_semaine)
        combos_row.addStretch()
        left_col.addLayout(combos_row)

        self.lbl_week_hint = QLabel("Sélectionne d'abord le mois puis la semaine")
        self.lbl_week_hint.setStyleSheet(f"color:{theme_manager.color('text_muted')}; font-size:8px; border:none;")
        left_col.addWidget(self.lbl_week_hint)

        self.days_container = QWidget()
        self.days_container.setStyleSheet("background: transparent;")
        self.days_layout = QVBoxLayout(self.days_container)
        self.days_layout.setContentsMargins(0, 0, 0, 0)
        self.days_layout.setSpacing(0)
        self.day_rows = []
        for _ in range(7):
            row_w = DayStatRow()
            self.day_rows.append(row_w)
            self.days_layout.addWidget(row_w)
        self.days_container.hide()
        left_col.addWidget(self.days_container)
        left_col.addStretch()

        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(2)

        _YEAR_DATA = [
            (2022, "fa5s.calendar",   "#6366f1", "12 450 000 GNF"),
            (2023, "fa5s.calendar",   "#f59e0b", "18 730 000 GNF"),
            (2024, "fa5s.calendar",   "#10b981", "23 100 000 GNF"),
            (2025, "fa5s.calendar",   "#3b82f6", "31 560 000 GNF"),
            (2026, "fa5s.calendar",   "#ef4444", "9 870 000 GNF"),
        ]

        self._year_amt_labels = []
        for year, icon_name, color, amount in _YEAR_DATA:
            yr_frame = QFrame()
            yr_frame.setFixedHeight(22)
            yr_frame.setStyleSheet(
                f"QFrame {{ background: {color}18; border-radius: 6px; border: none; }}"
            )
            yr_layout = QHBoxLayout(yr_frame)
            yr_layout.setContentsMargins(6, 0, 6, 0)
            yr_layout.setSpacing(4)

            ico_lbl = QLabel()
            ico_lbl.setFixedSize(12, 12)
            ico_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(QSize(12, 12)))
            ico_lbl.setStyleSheet("border:none; background:transparent;")

            yr_lbl = QLabel(str(year))
            yr_lbl.setStyleSheet(
                f"color:{color}; font-size:9px; font-weight:700; border:none; background:transparent;"
            )

            amt_lbl = QLabel(amount)
            amt_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amt_lbl.setStyleSheet(
                f"color:{theme_manager.color('text_primary')}; font-size:8px; font-weight:600; border:none; background:transparent;"
            )
            self._year_amt_labels.append(amt_lbl)

            yr_layout.addWidget(ico_lbl)
            yr_layout.addWidget(yr_lbl)
            yr_layout.addStretch()
            yr_layout.addWidget(amt_lbl)

            right_col.addWidget(yr_frame)

        right_col.addStretch()

        self._sep_v = QFrame()
        self._sep_v.setFrameShape(QFrame.VLine)
        self._sep_v.setFixedWidth(1)
        self._sep_v.setStyleSheet(f"background:{theme_manager.color('border_light')}; border:none;")

        two_col.addLayout(left_col, stretch=3)
        two_col.addWidget(self._sep_v)
        two_col.addLayout(right_col, stretch=2)

        self.frame_bas_droite.graph_layout.addLayout(two_col)

        # Grille responsive : 2 sections (graphes haut + frames bas)
        self._resp_grid.ajouter_section(
            [self.frame_nombre, self.frame_montant]
        )
        self._resp_grid.ajouter_section(
            [self.frame_bas_gauche, self.frame_bas_droite], expand_v=False
        )

        parent.addWidget(self._resp_grid, 1)

        # Brancher les interactions apres creation des widgets.
        self.combo_mois.currentIndexChanged.connect(self._on_month_changed)
        self.combo_semaine.currentIndexChanged.connect(self._on_week_combo_changed)

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

    def _mois_options(self):
        return [
            ("Janvier", 1), ("Fevrier", 2), ("Mars", 3), ("Avril", 4),
            ("Mai", 5), ("Juin", 6), ("Juillet", 7), ("Aout", 8),
            ("Septembre", 9), ("Octobre", 10), ("Novembre", 11), ("Decembre", 12),
        ]

    def _week_color(self, week_idx: int) -> str:
        colors = ["#b44cff", "#12b6c9", "#ff7a1a", "#4f67ff"]
        if 0 <= week_idx < len(colors):
            return colors[week_idx]
        return "#64748b"

    def _apply_week_combo_style(self, accent_color: str = None):
        c = theme_manager.colors()
        if not accent_color:
            self.combo_semaine.setStyleSheet(
                f"QComboBox {{ background:{c['bg_input']}; color:{c['text_muted']}; border:none; border-radius:10px; "
                f"padding:5px 10px; font-size:11px; font-weight:600; }} "
                f"QComboBox::drop-down {{ border:none; width:18px; }} "
                f"QComboBox::down-arrow {{ image:none; }} "
                f"QComboBox QAbstractItemView {{ border:1px solid {c['border_light']}; border-radius:8px; "
                f"background:{c['bg_card']}; selection-background-color:{c['hover']}; }}"
            )
            return

        self.combo_semaine.setStyleSheet(
            f"QComboBox {{ background:{accent_color}; color:{c['text_inverse']}; border:none; border-radius:10px; "
            f"padding:5px 10px; font-size:11px; font-weight:700; }} "
            f"QComboBox::drop-down {{ border:none; width:18px; }} "
            f"QComboBox::down-arrow {{ image:none; }} "
            f"QComboBox QAbstractItemView {{ border:1px solid {c['border_light']}; border-radius:8px; "
            f"background:{c['bg_card']}; selection-background-color:{c['hover']}; color:{c['text_primary']}; }}"
        )

    def _get_selected_week_index(self):
        data = self.combo_semaine.currentData()
        if data is None:
            return None
        return int(data)

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
        self._selected_month_last_day = calendar.monthrange(self._selected_year, self._selected_month)[1]

        self._stats_nombre_jour = self._call_ctrl_args(
            ["obtenir_nombre_par_jour"], self._selected_year, self._selected_month, default={}
        )
        self._stats_montant_jour = self._call_ctrl_args(
            ["obtenir_montant_par_jour"], self._selected_year, self._selected_month, default={}
        )

        for i in range(4):
            start = 1 + (i * 7)
            if start > self._selected_month_last_day:
                break
            end = min(start + 6, self._selected_month_last_day)
            self.combo_semaine.addItem(
                qta.icon("fa5s.circle", color=self._week_color(i)),
                f"Semaine {i + 1} ({start:02d}-{end:02d})",
                i
            )

    def _on_week_combo_changed(self, index: int):
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
        names = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        return names[datetime(year, month, day).weekday()]

    def _afficher_semaine(self, week_idx: int):
        start_day = 1 + (week_idx * 7)
        accent = self._week_color(week_idx)
        for offset in range(7):
            day_num = start_day + offset
            row = self.day_rows[offset]
            row.set_accent_color(accent)

            if day_num > self._selected_month_last_day:
                row.update_values("--", 0, 0.0, active=False)
                continue

            key = f"{day_num:02d}"
            nb = int(self._stats_nombre_jour.get(key, 0))
            montant = float(self._stats_montant_jour.get(key, 0.0))
            label = f"{self._weekday_fr(self._selected_year, self._selected_month, day_num)} {day_num:02d}"
            row.update_values(label, nb, montant, active=True)

    def charger_donnees(self):
        if not self.code_session:
            return
        try:
            nb_jour = self._call_ctrl(["obtenir_consultations_aujourd_hui"], default=0)
            nb_session = self._call_ctrl(
                ["obtenir_nombre_total", "obtenir_total_consultations_session"], default=0
            )
            montant_jour = self._call_ctrl(
                ["obtenir_montant_aujourd_hui", "obtenir_montant_consultations_aujourd_hui"], default=0.0
            )
            montant_session = self._call_ctrl(
                ["obtenir_montant_session", "obtenir_montant_consultations_session"], default=0.0
            )

            self.card_nb_jour.update_value(str(nb_jour))
            self.card_nb_session.update_value(str(nb_session))
            self.card_montant_jour.update_value(f"{montant_jour:,.0f}")
            self.card_montant_session.update_value(f"{montant_session:,.0f}")

            nombre_par_mois = self._call_ctrl(["obtenir_nombre_par_mois"], default={})
            moy_nb_par_mois = self._call_ctrl(
                ["obtenir_moyenne_nombre_journalier_par_mois", "obtenir_moyenne_consultations_par_mois"],
                default={},
            )
            self.graph_nombre.update_graph(nombre_par_mois, moy_nb_par_mois)

            montant_par_mois = self._call_ctrl(["obtenir_montant_par_mois"], default={})
            moy_montant_par_mois = self._call_ctrl(
                ["obtenir_moyenne_montant_journalier_par_mois", "obtenir_revenu_moyen_par_mois"],
                default={},
            )
            self.graph_montant.update_graph(montant_par_mois, moy_montant_par_mois)

            # Demi-cercles: pourcentages de consultations ayant abouti a un service
            taux_services = self._call_ctrl(["obtenir_taux_conversion"], default={})
            pct_examen = self._extraire_pourcentage(taux_services, ["examen"])
            pct_chirurgie = self._extraire_pourcentage(taux_services, ["chirurgie", "chiurgie"])
            pct_lunette = self._extraire_pourcentage(taux_services, ["lunette", "commandelunette", "commande_lunette"])

            self.gauge_examen.update_value(pct_examen)
            self.gauge_chirurgie.update_value(pct_chirurgie)
            self.gauge_lunette.update_value(pct_lunette)

            # Recharge le panneau hebdomadaire si les widgets sont presents.
            if hasattr(self, "combo_mois"):
                selected_week = self._get_selected_week_index()
                month_data = self.combo_mois.currentData()
                if month_data is None:
                    self.days_container.hide()
                    self.lbl_week_hint.show()
                else:
                    self._selected_year = datetime.now().year
                    self._selected_month = int(month_data)
                    self._selected_month_last_day = calendar.monthrange(
                        self._selected_year, self._selected_month
                    )[1]
                    self._stats_nombre_jour = self._call_ctrl_args(
                        ["obtenir_nombre_par_jour"], self._selected_year, self._selected_month, default={}
                    )
                    self._stats_montant_jour = self._call_ctrl_args(
                        ["obtenir_montant_par_jour"], self._selected_year, self._selected_month, default={}
                    )
                    if selected_week is not None:
                        self.days_container.show()
                        self.lbl_week_hint.hide()
                        self._afficher_semaine(selected_week)
                    else:
                        self.days_container.hide()
                        self.lbl_week_hint.show()
        except Exception as e:
            print(f"[AnalyseConsultationView] Erreur chargement donnees: {e}")
            import traceback
            traceback.print_exc()

    def _apply_combo_mois_style(self):
        c = theme_manager.colors()
        self.combo_mois.setStyleSheet(
            f"QComboBox {{ background:{c['bg_input']}; color:{c['text_primary']}; border:none; border-radius:10px; "
            f"padding:5px 10px; font-size:11px; font-weight:600; }} "
            f"QComboBox::drop-down {{ border:none; width:18px; }} "
            f"QComboBox::down-arrow {{ image:none; }} "
            f"QComboBox QAbstractItemView {{ border:1px solid {c['border_light']}; border-radius:8px; "
            f"background:{c['bg_card']}; selection-background-color:{c['hover']}; }}"
        )

    def apply_theme(self):
        c = theme_manager.colors()
        self.card_nb_jour.apply_theme(self.BLEU)
        self.card_nb_session.apply_theme(self.VERT)
        self.card_montant_jour.apply_theme(self.VIOLET)
        self.card_montant_session.apply_theme(self.ORANGE)
        self.frame_nombre.apply_theme()
        self.frame_montant.apply_theme()
        self.frame_bas_gauche.apply_theme()
        self.frame_bas_droite.apply_theme()
        self._apply_combo_mois_style()
        week_idx = self._get_selected_week_index()
        if week_idx is not None:
            self._apply_week_combo_style(self._week_color(int(week_idx)))
        else:
            self._apply_week_combo_style(None)
        self.lbl_week_hint.setStyleSheet(f"color:{c['text_muted']}; font-size:10px; border:none;")
        for lbl in self._year_amt_labels:
            lbl.setStyleSheet(f"color:{c['text_primary']}; font-size:10px; font-weight:600; border:none; background:transparent;")
        self._sep_v.setStyleSheet(f"background:{c['border_light']}; border:none;")
        self.charger_donnees()

    def rafraichir(self):
        self.charger_donnees()


class SidebarMenuButton(QPushButton):
    def __init__(self, label: str, icon_name: str, active: bool = False, parent=None):
        super().__init__(label, parent)
        self.icon_name = icon_name
        self._active = active
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setChecked(active)
        self.setFixedHeight(44)
        self.setIconSize(QSize(18, 18))

    def set_active(self, active: bool, shell_colors: dict):
        self._active = active
        self.setChecked(active)
        icon_color = shell_colors["sidebar_active_text"] if active else shell_colors["sidebar_text"]
        background = shell_colors["sidebar_active"] if active else "transparent"
        border = shell_colors["sidebar_active_border"] if active else "transparent"
        self.setIcon(qta.icon(self.icon_name, color=icon_color))
        self.setStyleSheet(
            f"QPushButton {{ background:{background}; color:{icon_color}; border:1px solid {border}; "
            f"border-radius:12px; padding:0 14px; text-align:left; font-size:14px; font-weight:600; }}"
            f"QPushButton:hover {{ background:{shell_colors['sidebar_hover']}; }}"
        )


class HeroStatCard(QFrame):
    def __init__(self, title: str, value: str, subtitle: str, icon_name: str, color: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._value = value
        self._subtitle = subtitle
        self._icon_name = icon_name
        self._color = color
        self._build()

    def _build(self):
        self.setMaximumHeight(70)
        self.setMinimumHeight(70)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(8)

        self.icon_holder = QLabel()
        self.icon_holder.setFixedSize(36, 36)
        self.icon_holder.setAlignment(Qt.AlignCenter)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        self.title_label = QLabel(self._title)
        self.title_label.setWordWrap(True)

        self.value_label = QLabel(self._value)
        self.subtitle_label = QLabel(self._subtitle)

        text_col.addWidget(self.title_label)
        text_col.addStretch()
        text_col.addWidget(self.value_label)
        text_col.addWidget(self.subtitle_label)
        root.addWidget(self.icon_holder, 0, Qt.AlignTop)
        root.addLayout(text_col, 1)

        self.apply_theme()

    def update_content(self, value: str, subtitle: str = None):
        self._value = value
        if subtitle is not None:
            self._subtitle = subtitle
        self.value_label.setText(self._value)
        self.subtitle_label.setText(self._subtitle)

    def apply_theme(self):
        self.setStyleSheet(
            f"QFrame {{ background:{self._color}; border:none; border-radius:12px; }}"
        )
        self.icon_holder.setStyleSheet(
            "background: rgba(255,255,255,0.92); border:none; border-radius:18px;"
        )
        self.icon_holder.setPixmap(qta.icon(self._icon_name, color=self._color).pixmap(QSize(20, 20)))
        self.title_label.setStyleSheet(
            "color:#F8FAFC; font-size:9px; font-weight:700; text-transform:uppercase; border:none;"
        )
        self.value_label.setStyleSheet(
            "color:#FFFFFF; font-size:16px; font-weight:800; border:none;"
        )
        self.subtitle_label.setStyleSheet(
            "color:#E2E8F0; font-size:9px; font-weight:600; border:none;"
        )


class DashboardSectionCard(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._build()

    def _build(self):
        self.setMinimumHeight(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 18))
        self.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        self.title_label = QLabel(self._title)
        self.separator = QFrame()
        self.separator.setFixedHeight(1)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(8)

        root.addWidget(self.title_label)
        root.addWidget(self.separator)
        root.addLayout(self.body, 1)
        self.apply_theme()

    def set_title(self, title: str):
        self._title = title
        self.title_label.setText(title)

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(
            f"QFrame {{ background:{c['bg_card']}; border:1px solid {c['border_light']}; border-radius:16px; }}"
        )
        self.title_label.setStyleSheet(
            f"color:{c['text_primary']}; font-size:13px; font-weight:700; border:none; background:transparent;"
        )
        self.separator.setStyleSheet(f"background:{c['border_light']}; border:none;")


class MonthlyConsultationBarGraph(BaseGraph):
    def update_graph(self, nombre_par_mois: dict):
        self.axes.clear()
        self._setup_style()

        x = np.arange(len(self.MONTH_LABELS))
        y = np.array([float(nombre_par_mois.get(m, 0) or 0) for m in self.MONTH_LABELS], dtype=float)
        color = "#2F7AE5"

        bars = self.axes.bar(x, y, color=color, width=0.46, alpha=0.95, zorder=3)
        self._set_x_axis(x)
        self._set_ylim_counts(y.tolist())
        self.axes.set_ylabel("Consultations", color=self.theme.COLORS["subtext"], fontsize=9)
        for rect, value in zip(bars, y):
            if value <= 0:
                continue
            self.axes.text(
                rect.get_x() + rect.get_width() / 2,
                rect.get_height() + max(0.3, self.axes.get_ylim()[1] * 0.02),
                f"{int(value)}",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="700",
                color=self.theme.COLORS["text"],
            )
        self._finalize()


class MonthlyRevenueLineGraph(BaseGraph):
    def update_graph(self, montant_par_mois: dict):
        self.axes.clear()
        self._setup_style()

        x = np.arange(len(self.MONTH_LABELS))
        y = np.array([float(montant_par_mois.get(m, 0) or 0) for m in self.MONTH_LABELS], dtype=float)
        color = "#22A447"

        self._draw_smooth_curve(x, y, color, "Montant (GNF)")
        self._draw_points(x, y, color, "Montant", "money")
        self._set_x_axis(x)
        self._set_ylim_amounts(y.tolist())
        self.axes.set_ylabel("GNF", color=self.theme.COLORS["subtext"], fontsize=9)
        self.axes.yaxis.set_major_formatter(
            FuncFormatter(lambda v, _: f"{int(v / 1000000)}M" if v >= 1000000 else f"{int(v):,}".replace(",", " "))
        )
        self.axes.legend(loc="lower center", bbox_to_anchor=(0.5, -0.25), fontsize=7, framealpha=0)
        self._style_legend()
        self._finalize()


class MonthlyAverageDualGraph(BaseGraph):
    def update_graph(self, moyenne_nb: dict, moyenne_montant: dict):
        self.axes.clear()
        self._setup_style()

        x = np.arange(len(self.MONTH_LABELS))
        y_nb      = np.array([float(moyenne_nb.get(m, 0) or 0)      for m in self.MONTH_LABELS], dtype=float)
        y_montant = np.array([float(moyenne_montant.get(m, 0) or 0)  for m in self.MONTH_LABELS], dtype=float)

        nb_scale      = max(float(np.max(y_nb)), 1.0)
        montant_scale = max(float(np.max(y_montant)), 1.0)
        y_montant_scaled = (y_montant / montant_scale) * nb_scale if montant_scale else y_montant

        color_nb      = "#2F7AE5"
        color_montant = "#FF8A00"

        self._draw_smooth_curve(x, y_nb,             color_nb,      "Moy. consultations / jour")
        self._draw_points(x, y_nb,             color_nb,      "Moy. consultations", "average_count")

        self._draw_smooth_curve(x, y_montant_scaled, color_montant, "Moy. revenus / jour", linestyle="--")
        # real_y = valeurs GNF réelles (pas normalisées) affichées dans le tooltip
        self._draw_points(x, y_montant_scaled, color_montant, "Moy. revenus", "average_money",
                          real_y=y_montant.tolist())

        self._set_x_axis(x)
        self._set_ylim_counts(y_nb.tolist() + y_montant_scaled.tolist())
        self.axes.set_ylabel("Indice moyen", color=self.theme.COLORS["subtext"], fontsize=9)
        self.axes.legend(loc="lower center", bbox_to_anchor=(0.5, -0.25), ncol=2, fontsize=7, framealpha=0)
        self._style_legend()
        self._finalize()


class DailyConsultationBarGraph(BaseGraph):
    def update_graph(self, labels: list, values: list):
        self.axes.clear()
        self._setup_style()

        if not labels:
            labels = ["--"]
            values = [0]

        self._bar_labels = labels
        x = np.arange(len(labels))
        y = np.array([float(v or 0) for v in values], dtype=float)
        bars = self.axes.bar(x, y, color="#2F7AE5", width=0.6, alpha=0.95, zorder=3)

        self.axes.set_xticks(x)
        self.axes.set_xticklabels(labels, fontsize=8)
        self._set_ylim_counts(y.tolist())
        self.axes.set_ylabel("Consultations", color=self.theme.COLORS["subtext"], fontsize=9)
        # Tous les labels sont visibles (suppression de la condition if len(labels) > 14)
        for rect, value in zip(bars, y):
            if value <= 0:
                continue
            self.axes.text(
                rect.get_x() + rect.get_width() / 2,
                rect.get_height() + max(0.2, self.axes.get_ylim()[1] * 0.02),
                f"{int(value)}",
                ha="center",
                va="bottom",
                fontsize=8,
                color=self.theme.COLORS["text"],
            )

        # Tooltips sur les barres
        cur = mplcursors.cursor(bars, hover=True)
        cur.connect("add", self._on_bar_hover)
        self.cursors.append(cur)

        self._finalize()

    def _on_bar_hover(self, sel):
        try:
            idx = int(round(sel.target[0]))
            val = float(sel.target[1])
            lbl = (self._bar_labels[idx]
                   if hasattr(self, "_bar_labels") and 0 <= idx < len(self._bar_labels)
                   else str(idx + 1))
            txt = f"Jour {lbl}  ·  {int(round(val))} consult."
            sel.annotation.set_text(txt)
            sel.annotation.get_bbox_patch().set(
                fc=self.theme.COLORS["surface"],
                ec="#2F7AE5",
                boxstyle="round,pad=0.22",
                alpha=0.96,
                linewidth=1.8,
            )
            sel.annotation.set_color(self.theme.COLORS["text"])
            sel.annotation.set_fontsize(8)
            sel.annotation.set_fontweight("700")
            sel.annotation.arrow_patch.set_visible(False)
            if sel.annotation not in self._annotations:
                self._annotations.append(sel.annotation)
        except Exception:
            pass


class ServiceDonutGraph(FigureCanvas):
    def __init__(self, parent=None, width=2.3, height=2.2, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet("background: transparent;")
        self.update_graph([])

    def update_graph(self, items: list):
        c = theme_manager.colors()
        self.axes.clear()
        self.axes.set_facecolor("none")
        self.axes.axis("equal")

        values = [max(0.0, float(item["value"])) for item in items if item.get("value") is not None]
        colors = [item["color"] for item in items if item.get("value") is not None]
        if not values or sum(values) <= 0:
            values = [100.0]
            colors = [c["border_light"]]

        self.axes.pie(
            values,
            colors=colors,
            startangle=90,
            counterclock=False,
            wedgeprops={"width": 0.55, "edgecolor": c["bg_card"], "linewidth": 1.2},
        )
        self.axes.text(0, 0.08, "Taux", ha="center", va="center", fontsize=13, fontweight="800", color=c["text_primary"])
        self.axes.text(0, -0.14, "services", ha="center", va="center", fontsize=9, color=c["text_secondary"])
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.draw()


class DiagnosticProgressRow(QFrame):
    def __init__(self, rank: int, color: str, parent=None):
        super().__init__(parent)
        self._color = color
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.rank_label = QLabel(str(rank))
        self.rank_label.setFixedSize(18, 18)
        self.rank_label.setAlignment(Qt.AlignCenter)

        self.name_label = QLabel("--")
        self.value_label = QLabel("0")

        self.bar_bg = QFrame()
        self.bar_bg.setFixedHeight(8)
        self.bar_fill = QFrame(self.bar_bg)
        self.bar_fill.setGeometry(0, 0, 0, 8)

        center = QVBoxLayout()
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(6)
        center.addWidget(self.name_label)
        center.addWidget(self.bar_bg)

        layout.addWidget(self.rank_label, 0, Qt.AlignTop)
        layout.addLayout(center, 1)
        layout.addWidget(self.value_label, 0, Qt.AlignVCenter)

        self.apply_theme()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_fill_width(getattr(self, "_ratio", 0.0))

    def _apply_fill_width(self, ratio: float):
        ratio = max(0.0, min(1.0, ratio))
        width = int(self.bar_bg.width() * ratio)
        self.bar_fill.setGeometry(0, 0, width, self.bar_bg.height())

    def update_row(self, name: str, value: float, maximum: float):
        self.name_label.setText(name)
        self.value_label.setText(f"{int(value)}")
        self._ratio = (float(value) / float(maximum)) if maximum else 0.0
        self._apply_fill_width(self._ratio)

    def apply_theme(self):
        c = theme_manager.colors()
        self.rank_label.setStyleSheet(
            f"background:{c['selected']}; color:{c['text_inverse']}; border:none; border-radius:9px; font-size:10px; font-weight:700;"
        )
        self.name_label.setStyleSheet(
            f"color:{c['text_primary']}; font-size:13px; font-weight:600; border:none;"
        )
        self.value_label.setStyleSheet(
            f"color:{c['text_primary']}; font-size:12px; font-weight:700; border:none;"
        )
        self.bar_bg.setStyleSheet(
            f"background:{c['border_light']}; border:none; border-radius:4px;"
        )
        self.bar_fill.setStyleSheet(f"background:{self._color}; border:none; border-radius:4px;")


class ServiceMiniCard(QFrame):
    def __init__(self, title: str, icon_name: str, color: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._icon_name = icon_name
        self._color = color
        self._build()

    def _build(self):
        self.setMinimumHeight(0)
        self.setMaximumHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(4)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(6)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.title_label = QLabel(self._title)

        top.addWidget(self.icon_label)
        top.addWidget(self.title_label, 1)

        self.value_label = QLabel("0")
        self.subtitle_label = QLabel("patients")
        self.button = QPushButton("Voir la liste")
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.setFixedHeight(22)

        root.addLayout(top)
        root.addStretch()
        root.addWidget(self.value_label)
        root.addWidget(self.subtitle_label)
        root.addStretch()
        root.addWidget(self.button)
        self.apply_theme()

    def update_value(self, value: int, subtitle: str = "patients"):
        self.value_label.setText(str(int(value)))
        self.subtitle_label.setText(subtitle)

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(
            f"QFrame {{ background:{c['bg_card']}; border:1px solid {self._color}66; border-radius:10px; }}"
        )
        self.icon_label.setStyleSheet(
            f"background:{self._color}18; border:none; border-radius:12px;"
        )
        self.icon_label.setPixmap(qta.icon(self._icon_name, color=self._color).pixmap(QSize(14, 14)))
        self.title_label.setStyleSheet(
            f"color:{c['text_primary']}; font-size:10px; font-weight:700; border:none;"
        )
        self.value_label.setStyleSheet(
            f"color:{self._color}; font-size:20px; font-weight:800; border:none;"
        )
        self.subtitle_label.setStyleSheet(
            f"color:{c['text_secondary']}; font-size:9px; font-weight:600; border:none;"
        )
        self.button.setStyleSheet(
            f"QPushButton {{ background:{self._color}; color:#FFFFFF; border:none; border-radius:6px; font-size:9px; font-weight:700; padding:0 6px; }}"
            f"QPushButton:hover {{ border:1px solid {self._color}; }}"
        )


class AnalyseConsultationView(QWidget):
    """Vue d'analyse consultation — 2 onglets : Statistiques et Graphes."""

    _BLEU     = _TC('info')
    _VERT     = _TC('success')
    _VIOLET   = _TC('accent')
    _ORANGE   = _TC('warning')
    _ROUGE    = _TC('danger')
    _PRIMAIRE = _TC('primary')

    _DIAG_COLORS = [
        "#2F7AE5", "#20B486", "#FF9800", "#7A44D5", "#14A7A0",
        "#EF4444", "#F97316", "#84CC16", "#06B6D4", "#8B5CF6",
    ]

    def __init__(self, controleur, code_session: str, parent=None):
        super().__init__(parent)
        self.controleur   = controleur
        self.code_session = code_session
        self._loaded: set = set()
        self._build_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    # ------------------------------------------------------------------
    # CONSTRUCTION
    # ------------------------------------------------------------------

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._main_frame = QFrame()
        self._main_frame.setObjectName("AnalyseMainFrame")
        frame_layout = QVBoxLayout(self._main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setIconSize(QSize(20, 20))
        self.tabs.currentChanged.connect(self._on_tab_changed)
        frame_layout.addWidget(self.tabs)

        self.tab_stats   = self._build_tab_stats()
        self.tab_graphes = self._build_tab_graphes()

        c = theme_manager.colors()
        self.tabs.addTab(
            self.tab_stats,
            qta.icon("fa5s.chart-bar", color=c['primary']),
            "  Statistiques"
        )
        self.tabs.addTab(
            self.tab_graphes,
            qta.icon("fa5s.chart-line", color=c['primary']),
            "  Graphes"
        )

        main_layout.addWidget(self._main_frame)

    # ── Onglet 1 : Statistiques ─────────────────────────────────────────

    def _build_tab_stats(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Ligne 1 de KPI (4 cartes)
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self.kpi_nb_jour         = KPICard("Consultations du jour",  "0", "fa5s.calendar-day",   self._BLEU,     "consultations")
        self.kpi_nb_session      = KPICard("Total session",          "0", "fa5s.chart-line",      self._VERT,     "consultations")
        self.kpi_en_attente      = KPICard("Patients en attente",    "0", "fa5s.hourglass-half",  self._ORANGE,   "patients")
        self.kpi_revenu_moy      = KPICard("Revenu moyen mensuel",   "0", "fa5s.chart-area",      self._PRIMAIRE, "GNF")
        for card in (self.kpi_nb_jour, self.kpi_nb_session, self.kpi_en_attente, self.kpi_revenu_moy):
            row1.addWidget(card)
        layout.addLayout(row1)

        # Ligne 2 de KPI (4 cartes)
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self.kpi_montant_jour    = KPICard("Montant du jour",        "0", "fa5s.money-bill-wave", self._VIOLET, "GNF")
        self.kpi_montant_session = KPICard("Montant session",        "0", "fa5s.wallet",          self._ROUGE,  "GNF")
        self.kpi_top_diag        = KPICard("Top diagnostic",         "—", "fa5s.stethoscope",     self._VERT,   "")
        self.kpi_top_personnel   = KPICard("Personnel le + actif",   "—", "fa5s.user-md",         self._BLEU,   "")
        for card in (self.kpi_montant_jour, self.kpi_montant_session, self.kpi_top_diag, self.kpi_top_personnel):
            row2.addWidget(card)
        layout.addLayout(row2)

        # Séparateur
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("AnalyseSep")
        layout.addWidget(sep)

        # Bas : Top diagnostics (gauche) + Performance personnel (droite)
        bottom = QHBoxLayout()
        bottom.setSpacing(14)

        self.frame_diag = GraphFrame("Top 10 diagnostics", "fa5s.stethoscope")
        self.diag_rows = []
        for idx, color in enumerate(self._DIAG_COLORS, start=1):
            dr = DiagnosticProgressRow(idx, color)
            self.diag_rows.append(dr)
            self.frame_diag.graph_layout.addWidget(dr)
        self.frame_diag.graph_layout.addStretch()
        bottom.addWidget(self.frame_diag, 3)

        self.frame_personnel = GraphFrame("Performance du personnel", "fa5s.user-md")
        self.table_personnel = QTableWidget(0, 5)
        self.table_personnel.setHorizontalHeaderLabels(
            ["#", "Personnel", "Consultations", "Montant total (GNF)", "Moy./consultation"]
        )
        self.table_personnel.verticalHeader().setVisible(False)
        self.table_personnel.setSelectionMode(QAbstractItemView.NoSelection)
        self.table_personnel.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_personnel.setAlternatingRowColors(True)
        h = self.table_personnel.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.frame_personnel.graph_layout.addWidget(self.table_personnel)
        bottom.addWidget(self.frame_personnel, 4)

        layout.addLayout(bottom, 1)
        return tab

    # ── Onglet 2 : Graphes ──────────────────────────────────────────────

    def _build_tab_graphes(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Rangée 1 : nombre par mois | montant par mois
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.frame_g_nombre = GraphFrame(
            "Nombre de consultations par mois + moyenne journalière", "fa5s.chart-bar"
        )
        self.graph_nombre = ConsultationNombreGraph(width=6, height=3.2)
        self.graph_nombre.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graph_nombre.setMinimumHeight(200)
        self.frame_g_nombre.graph_layout.addWidget(self.graph_nombre)
        row1.addWidget(self.frame_g_nombre, 1)

        self.frame_g_montant = GraphFrame(
            "Montant des consultations par mois + moyenne journalière", "fa5s.chart-area"
        )
        self.graph_montant = ConsultationMontantGraph(width=6, height=3.2)
        self.graph_montant.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graph_montant.setMinimumHeight(200)
        self.frame_g_montant.graph_layout.addWidget(self.graph_montant)
        row1.addWidget(self.frame_g_montant, 1)

        layout.addLayout(row1, 1)

        # Rangée 2 : consultations par jour — pleine largeur
        self.frame_g_daily = GraphFrame(
            "Consultations par jour (mois courant)", "fa5s.calendar"
        )
        self.graph_daily = DailyConsultationBarGraph(width=10, height=3.2)
        self.graph_daily.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graph_daily.setMinimumHeight(200)
        self.frame_g_daily.graph_layout.addWidget(self.graph_daily)
        layout.addWidget(self.frame_g_daily, 1)

        return tab

    # ------------------------------------------------------------------
    # CHARGEMENT DES DONNÉES
    # ------------------------------------------------------------------

    def _on_tab_changed(self, index: int):
        if index not in self._loaded:
            self._charger_onglet(index)

    def _precharger_tout(self):
        """Précharge les 2 onglets dès l'affichage pour éviter tout délai au clic."""
        self._charger_onglet(0)
        QTimer.singleShot(80, lambda: self._charger_onglet(1))

    def _charger_onglet(self, index: int):
        if not self.code_session or index in self._loaded:
            return
        try:
            if index == 0:
                self._charger_stats()
            elif index == 1:
                self._charger_graphes()
            self._loaded.add(index)
        except Exception as e:
            print(f"[AnalyseConsultationView] Erreur onglet {index}: {e}")
            import traceback; traceback.print_exc()

    def _call(self, method: str, *args, default=0):
        fn = getattr(self.controleur, method, None)
        if callable(fn):
            try:
                return fn(self.code_session, *args)
            except Exception:
                pass
        return default

    def _safe_int(self, v) -> int:
        try: return int(float(v or 0))
        except: return 0

    def _safe_float(self, v) -> float:
        try: return float(v or 0)
        except: return 0.0

    def _fmt_money(self, v) -> str:
        try: return f"{float(v):,.0f}".replace(",", " ")
        except: return "0"

    def _charger_stats(self):
        # KPI ligne 1
        self.kpi_nb_jour.update_value(str(self._safe_int(self._call("obtenir_consultations_aujourd_hui", default=0))))
        self.kpi_nb_session.update_value(str(self._safe_int(self._call("obtenir_nombre_total", default=0))))
        self.kpi_en_attente.update_value(str(self._safe_int(self._call("obtenir_nombre_patients_en_attente", default=0))))
        avg_data = self._call("obtenir_revenu_moyen_par_mois", default={}) or {}
        avg_val  = (sum(avg_data.values()) / len(avg_data)) if avg_data else 0.0
        self.kpi_revenu_moy.update_value(self._fmt_money(avg_val))

        # KPI ligne 2
        self.kpi_montant_jour.update_value(self._fmt_money(self._call("obtenir_montant_aujourd_hui", default=0.0)))
        self.kpi_montant_session.update_value(self._fmt_money(self._call("obtenir_montant_session", default=0.0)))
        diagnostics = (self._call("obtenir_top_diagnostics", 10, default=[]) or [])[:10]
        if diagnostics:
            self.kpi_top_diag.update_value(str(diagnostics[0].get("diagnostique", "—") or "—")[:22])
        else:
            self.kpi_top_diag.update_value("—")
        personnel = self._call("obtenir_consultations_par_personnel", default=[]) or []
        if personnel:
            p0  = personnel[0]
            nom = f"{p0.get('nom','') or ''} {p0.get('prenom','') or ''}".strip()
            self.kpi_top_personnel.update_value(nom[:22] if nom else "—")
        else:
            self.kpi_top_personnel.update_value("—")

        # Top diagnostics (barres)
        max_val = max([self._safe_float(r.get("nombre", 0)) for r in diagnostics], default=0.0)
        for idx, row_w in enumerate(self.diag_rows):
            if idx < len(diagnostics):
                r = diagnostics[idx]
                row_w.update_row(str(r.get("diagnostique", "--")), self._safe_float(r.get("nombre", 0)), max_val)
                row_w.show()
            else:
                row_w.update_row("--", 0, 1)
                row_w.hide()

        # Tableau personnel
        self.table_personnel.setRowCount(len(personnel))
        for i, r in enumerate(personnel):
            nom   = f"Dr. {r.get('nom','') or ''} {r.get('prenom','') or ''}".strip()
            total = self._safe_float(r.get("total_frais", 0))
            nb    = self._safe_int(r.get("nombre", 0))
            moy   = total / nb if nb else 0.0
            for j, val in enumerate([i + 1, nom, nb, self._fmt_money(total), self._fmt_money(moy)]):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                if j in (0, 2):   item.setTextAlignment(Qt.AlignCenter)
                elif j in (3, 4): item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table_personnel.setItem(i, j, item)

    def _charger_graphes(self):
        from PySide6.QtWidgets import QApplication
        nb_mois  = self._call("obtenir_nombre_par_mois",  default={}) or {}
        mnt_mois = self._call("obtenir_montant_par_mois", default={}) or {}
        moy_nb   = self._call("obtenir_moyenne_nombre_journalier_par_mois",  default={}) or {}
        moy_mnt  = self._call("obtenir_moyenne_montant_journalier_par_mois", default={}) or {}

        self.graph_nombre.update_graph(nb_mois, moy_nb)
        QApplication.processEvents()

        self.graph_montant.update_graph(mnt_mois, moy_mnt)
        QApplication.processEvents()

        now     = datetime.now()
        nb_jour = self._call("obtenir_nombre_par_jour", now.year, now.month, default={}) or {}
        ordered = sorted(nb_jour.keys(), key=lambda x: int(x))
        self.graph_daily.update_graph(ordered, [self._safe_int(nb_jour.get(d, 0)) for d in ordered])

    # ------------------------------------------------------------------
    # API PUBLIQUE
    # ------------------------------------------------------------------

    def rafraichir(self):
        self._loaded.clear()
        self.charger_donnees()

    def charger_donnees(self):
        """Charge les 2 onglets synchronement — appelé pendant la barre de progression."""
        from PySide6.QtWidgets import QApplication
        self._loaded.clear()
        try:
            self._charger_stats()
            self._loaded.add(0)
            QApplication.processEvents()
            self._charger_graphes()
            self._loaded.add(1)
        except Exception as e:
            print(f"[AnalyseConsultationView] Erreur charger_donnees: {e}")
            import traceback; traceback.print_exc()

    # ------------------------------------------------------------------
    # THÈME
    # ------------------------------------------------------------------

    def apply_theme(self):
        c = theme_manager.colors()

        self._main_frame.setStyleSheet(f"""
            QFrame#AnalyseMainFrame {{
                background: white;
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
        """)

        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {c['bg_card']};
                padding: 0px;
                margin-top: 0px;
            }}
            QTabBar {{
                background: {c['bg_card']};
                border: none;
            }}
            QTabBar::tab {{
                background: {c['bg_card']};
                color: {c['text_secondary']};
                border: none;
                border-bottom: 3px solid transparent;
                padding: 10px 20px;
                margin-right: 0px;
                font-size: 14px;
                font-weight: 600;
                min-width: 130px;
            }}
            QTabBar::tab:selected {{
                background: {c['bg_card']};
                color: {c['primary']};
                border-bottom: 3px solid {c['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                color: {c['text_primary']};
            }}
        """)

        self.tabs.setTabIcon(0, qta.icon("fa5s.chart-bar",  color=c['primary']))
        self.tabs.setTabIcon(1, qta.icon("fa5s.chart-line", color=c['primary']))

        for card, key in [
            (self.kpi_nb_jour,         'info'),
            (self.kpi_nb_session,      'success'),
            (self.kpi_en_attente,      'warning'),
            (self.kpi_revenu_moy,      'primary'),
            (self.kpi_montant_jour,    'accent'),
            (self.kpi_montant_session, 'danger'),
            (self.kpi_top_diag,        'success'),
            (self.kpi_top_personnel,   'info'),
        ]:
            card.apply_theme(theme_manager.color(key))

        for frame in (self.frame_diag, self.frame_personnel,
                      self.frame_g_nombre, self.frame_g_montant,
                      self.frame_g_daily):
            frame.apply_theme()

        for row_w in self.diag_rows:
            row_w.apply_theme()

        self._style_table(self.table_personnel, c)

        sep = self.tab_stats.findChild(QFrame, "AnalyseSep")
        if sep:
            sep.setStyleSheet(f"background:{c['border_light']}; border:none;")

    def _style_table(self, table: QTableWidget, c: dict):
        table.setStyleSheet(
            f"QTableWidget {{ background:{c['bg_card']}; alternate-background-color:{c['bg_table_alt']}; "
            f"border:none; color:{c['text_primary']}; gridline-color:{c['border_light']}; font-size:11px; }}"
            f"QHeaderView::section {{ background:{c['table_header_bg']}; color:{c['text_primary']}; "
            f"border:none; border-bottom:1px solid {c['border_light']}; padding:6px; font-size:10px; font-weight:700; }}"
            f"QTableWidget::item {{ padding:6px; border-bottom:1px solid {c['border_light']}; }}"
        )


# Ancienne classe conservée pour compatibilité
class LegacyAnalyseConsultationView_OLD(QWidget):
    KPI_COLORS = ["#1D73E8", "#2FB344", "#FF9800", "#7A44D5", "#14A7A0"]
    DIAG_COLORS = ["#2F7AE5", "#20B486", "#FF9800", "#7A44D5", "#14A7A0"]

    def __init__(self, controleur, code_session: str, parent=None):
        super().__init__(parent)
        self.controleur = controleur
        self.code_session = code_session
        self._is_loading = False
        self._build_ui()
        self._setup_clock()
        self.apply_theme()
        self.charger_donnees()
        theme_manager.theme_changed.connect(self.apply_theme)

    def _build_ui(self):
        self.setObjectName("AnalyseConsultationView")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self.content_shell = QFrame()
        shell_layout = QVBoxLayout(self.content_shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(8)

        self.top_bar = QFrame()
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        self.menu_button = QPushButton()
        self.menu_button.setFixedSize(36, 36)
        self.menu_button.setCursor(Qt.PointingHandCursor)
        self.menu_button.setIconSize(QSize(16, 16))

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(2)
        self.page_title = QLabel()
        self.page_subtitle = QLabel("Tableau de bord analytique des consultations")
        title_col.addWidget(self.page_title)
        title_col.addWidget(self.page_subtitle)

        self.date_badge = QLabel()
        self.time_badge = QLabel()
        self.session_badge = QPushButton()
        self.session_badge.setCursor(Qt.PointingHandCursor)
        self.session_badge.setFixedHeight(28)
        self.session_badge.setIconSize(QSize(12, 12))

        top_layout.addWidget(self.menu_button)
        top_layout.addLayout(title_col, 1)
        top_layout.addWidget(self.date_badge)
        top_layout.addWidget(self.time_badge)
        top_layout.addWidget(self.session_badge)
        shell_layout.addWidget(self.top_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.dashboard_surface = QFrame()
        surface_layout = QVBoxLayout(self.dashboard_surface)
        surface_layout.setContentsMargins(10, 10, 10, 10)
        surface_layout.setSpacing(8)

        cards_row = QHBoxLayout()
        cards_row.setContentsMargins(0, 0, 0, 0)
        cards_row.setSpacing(8)
        self.hero_cards = [
            HeroStatCard("Consultations jour", "0", "Aujourd'hui", "fa5s.user-md", self.KPI_COLORS[0]),
            HeroStatCard("Total session", "0", self._session_badge_text(), "fa5s.calendar-alt", self.KPI_COLORS[1]),
            HeroStatCard("En attente", "0", "Sans consultation", "fa5s.hourglass-half", self.KPI_COLORS[2]),
            HeroStatCard("Montant jour", "0", "Revenus aujourd'hui", "fa5s.money-bill-wave", self.KPI_COLORS[3]),
            HeroStatCard("Montant session", "0", "Revenus totaux", "fa5s.wallet", self.KPI_COLORS[4]),
        ]
        for card in self.hero_cards:
            cards_row.addWidget(card, 1)
        surface_layout.addLayout(cards_row)

        panel_grid = QGridLayout()
        panel_grid.setContentsMargins(0, 0, 0, 0)
        panel_grid.setHorizontalSpacing(8)
        panel_grid.setVerticalSpacing(8)
        panel_grid.setColumnStretch(0, 3)
        panel_grid.setColumnStretch(1, 2)
        panel_grid.setColumnStretch(2, 3)

        self.panel_nombre = DashboardSectionCard("Nombre de consultations par mois")
        self.graph_nombre = MonthlyConsultationBarGraph(width=4, height=2.5)
        self.graph_nombre.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graph_nombre.setMinimumHeight(200)
        self.panel_nombre.body.addWidget(self.graph_nombre)

        self.panel_montant = DashboardSectionCard("Montant des consultations par mois (GNF)")
        self.graph_montant = MonthlyRevenueLineGraph(width=4, height=2.5)
        self.graph_montant.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graph_montant.setMinimumHeight(200)
        self.panel_montant.body.addWidget(self.graph_montant)

        self.panel_moyenne = DashboardSectionCard("Moyenne journaliere (par mois)")
        self.graph_moyenne = MonthlyAverageDualGraph(width=4, height=2.5)
        self.graph_moyenne.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graph_moyenne.setMinimumHeight(200)
        self.panel_moyenne.body.addWidget(self.graph_moyenne)

        self.panel_services = DashboardSectionCard("Taux de conversion par services")
        services_layout = QHBoxLayout()
        services_layout.setContentsMargins(0, 0, 0, 0)
        services_layout.setSpacing(6)
        self.graph_services = ServiceDonutGraph(width=1.5, height=1.5)
        services_layout.addWidget(self.graph_services, 0, Qt.AlignCenter)
        legend_col = QVBoxLayout()
        legend_col.setContentsMargins(0, 0, 0, 0)
        legend_col.setSpacing(4)
        self.service_legend_rows = []
        for title, icon_name, color in [
            ("Examen", "fa5s.microscope", "#2F7AE5"),
            ("Chirurgie", "fa5s.procedures", "#20B486"),
            ("Lunette", "fa5s.glasses", "#FF9800"),
            ("Prescription", "fa5s.pills", "#7A44D5"),
        ]:
            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(6, 4, 6, 4)
            row_layout.setSpacing(4)
            icon = QLabel()
            icon.setFixedSize(20, 20)
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet(f"background:{color}18; border:none; border-radius:10px;")
            icon.setPixmap(qta.icon(icon_name, color=color).pixmap(QSize(10, 10)))
            label = QLabel(title)
            value = QLabel("0%")
            row_layout.addWidget(icon)
            row_layout.addWidget(label, 1)
            row_layout.addWidget(value)
            self.service_legend_rows.append((row, label, value, color))
            legend_col.addWidget(row)
        legend_col.addStretch()
        services_layout.addLayout(legend_col, 1)
        self.panel_services.body.addLayout(services_layout)

        self.panel_diagnostics = DashboardSectionCard("Top 5 diagnostics")
        self.diagnostic_rows = []
        for idx, color in enumerate(self.DIAG_COLORS, start=1):
            row = DiagnosticProgressRow(idx, color)
            self.diagnostic_rows.append(row)
            self.panel_diagnostics.body.addWidget(row)
        self.panel_diagnostics.body.addStretch()

        self.panel_personnel = DashboardSectionCard("Performance du personnel")
        self.table_personnel = QTableWidget(0, 5)
        self.table_personnel.setHorizontalHeaderLabels(
            ["#", "Personnel", "Consultations", "Montant total (GNF)", "Moy. / consultation"]
        )
        self.table_personnel.setMinimumHeight(0)
        self.table_personnel.setMaximumHeight(170)
        self.panel_personnel.body.addWidget(self.table_personnel)

        self.panel_attente = DashboardSectionCard("Patients en attente de consultation")
        self.table_attente = QTableWidget(0, 4)
        self.table_attente.setHorizontalHeaderLabels(["Code visite", "Patient", "Telephone", "Date visite"])
        self.table_attente.setMinimumHeight(0)
        self.table_attente.setMaximumHeight(170)
        self.btn_attente = QPushButton("Voir tous les patients en attente")
        self.btn_attente.setCursor(Qt.PointingHandCursor)
        self.btn_attente.setFixedHeight(28)
        self.panel_attente.body.addWidget(self.table_attente)
        self.panel_attente.body.addWidget(self.btn_attente)

        self.panel_services_today = DashboardSectionCard("Patients par service (aujourd'hui)")
        services_today_layout = QHBoxLayout()
        services_today_layout.setContentsMargins(0, 0, 0, 0)
        services_today_layout.setSpacing(6)
        self.service_cards = [
            ServiceMiniCard("Examen", "fa5s.microscope", "#2F7AE5"),
            ServiceMiniCard("Chirurgie", "fa5s.procedures", "#20B486"),
            ServiceMiniCard("Lunette", "fa5s.glasses", "#FF9800"),
            ServiceMiniCard("Prescription", "fa5s.pills", "#7A44D5"),
        ]
        for service_card in self.service_cards:
            services_today_layout.addWidget(service_card, 1)
        self.panel_services_today.body.addLayout(services_today_layout)

        self.panel_daily = DashboardSectionCard("Consultations par jour")
        self.graph_daily = DailyConsultationBarGraph(width=4, height=2.5)
        self.graph_daily.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graph_daily.setMinimumHeight(200)
        self.panel_daily.body.addWidget(self.graph_daily)

        panel_grid.addWidget(self.panel_nombre, 0, 0)
        panel_grid.addWidget(self.panel_montant, 0, 1)
        panel_grid.addWidget(self.panel_moyenne, 0, 2)
        panel_grid.addWidget(self.panel_services, 1, 0)
        panel_grid.addWidget(self.panel_diagnostics, 1, 1)
        panel_grid.addWidget(self.panel_personnel, 1, 2)
        panel_grid.addWidget(self.panel_attente, 2, 0)
        panel_grid.addWidget(self.panel_services_today, 2, 1)
        panel_grid.addWidget(self.panel_daily, 2, 2)
        surface_layout.addLayout(panel_grid)

        self.filters_card = QFrame()
        filters_layout = QHBoxLayout(self.filters_card)
        filters_layout.setContentsMargins(12, 10, 12, 10)
        filters_layout.setSpacing(10)

        self.filters_title = QLabel("Filtres rapides")
        self.date_debut = QDateEdit()
        self.date_fin = QDateEdit()
        self.combo_examen = QComboBox()
        self.combo_chirurgie = QComboBox()
        self.combo_lunette = QComboBox()
        self.combo_prescription = QComboBox()
        self.btn_filtrer = QPushButton("Rechercher")
        self.btn_filtrer.setCursor(Qt.PointingHandCursor)
        self.btn_filtrer.setFixedHeight(34)

        filters_layout.addWidget(self.filters_title)
        filters_layout.addStretch()
        for lbl_text, widget in [
            ("Date debut", self.date_debut),
            ("Date fin", self.date_fin),
            ("Examen", self.combo_examen),
            ("Chirurgie", self.combo_chirurgie),
            ("Lunette", self.combo_lunette),
            ("Prescription", self.combo_prescription),
        ]:
            group = QVBoxLayout()
            group.setContentsMargins(0, 0, 0, 0)
            group.setSpacing(4)
            label = QLabel(lbl_text)
            group.addWidget(label)
            group.addWidget(widget)
            filters_layout.addLayout(group)
        filters_layout.addWidget(self.btn_filtrer)
        surface_layout.addWidget(self.filters_card)

        self.scroll.setWidget(self.dashboard_surface)
        shell_layout.addWidget(self.scroll, 1)

        root.addWidget(self.content_shell, 1)

        self.section_cards = [
            self.panel_nombre,
            self.panel_montant,
            self.panel_moyenne,
            self.panel_services,
            self.panel_diagnostics,
            self.panel_personnel,
            self.panel_attente,
            self.panel_services_today,
            self.panel_daily,
        ]

        for combo in [self.combo_examen, self.combo_chirurgie, self.combo_lunette, self.combo_prescription]:
            combo.addItems(["Tous", "Oui", "Non"])

        today = QDate.currentDate()
        first_day = QDate(today.year(), today.month(), 1)
        for widget, value in [(self.date_debut, first_day), (self.date_fin, today)]:
            widget.setCalendarPopup(True)
            widget.setDisplayFormat("dd/MM/yyyy")
            widget.setDate(value)
            widget.setFixedHeight(30)

        self.btn_filtrer.clicked.connect(self._appliquer_filtres_rapides)

    def _setup_clock(self):
        self._update_header_clock()
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_header_clock)
        self._clock_timer.start(60000)

    def _shell_colors(self) -> dict:
        current = getattr(theme_manager, "current", "clair")
        if current == "sombre":
            return {
                "shell": "#0F172A",
                "sidebar": "#0B1422",
                "sidebar_text": "#CBD5E1",
                "sidebar_subtext": "#94A3B8",
                "sidebar_hover": "#12223B",
                "sidebar_active": "#1D4ED8",
                "sidebar_active_text": "#FFFFFF",
                "sidebar_active_border": "#3B82F6",
                "top_text": "#F8FAFC",
                "top_subtext": "#CBD5E1",
                "badge_bg": "#13243D",
                "badge_text": "#F8FAFC",
            }
        return {
            "shell": "#0B2852",
            "sidebar": "#082449",
            "sidebar_text": "#E2E8F0",
            "sidebar_subtext": "#B6C4D6",
            "sidebar_hover": "#113160",
            "sidebar_active": "#1D73E8",
            "sidebar_active_text": "#FFFFFF",
            "sidebar_active_border": "#3B82F6",
            "top_text": "#F8FAFC",
            "top_subtext": "#D8E5F6",
            "badge_bg": "#12325F",
            "badge_text": "#F8FAFC",
        }

    def _session_badge_text(self) -> str:
        raw = str(self.code_session or "").strip()
        if not raw:
            return "Session active"
        if raw.lower().startswith("session"):
            return raw
        return f"Session {raw}"

    def _session_title_text(self) -> str:
        return f"DASHBOARD CONSULTATION - {self._session_badge_text().upper()}"

    def _format_money(self, value) -> str:
        try:
            return f"{float(value):,.0f}".replace(",", " ")
        except Exception:
            return "0"

    def _safe_int(self, value) -> int:
        try:
            return int(float(value or 0))
        except Exception:
            return 0

    def _safe_float(self, value) -> float:
        try:
            return float(value or 0)
        except Exception:
            return 0.0

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

    def _mois_label(self, month: int) -> str:
        labels = [
            "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre",
        ]
        if 1 <= month <= 12:
            return labels[month - 1]
        return ""

    def _date_to_python(self, value):
        if hasattr(value, "toPython"):
            return value.toPython()
        if hasattr(value, "toPyDate"):
            return value.toPyDate()
        return value

    def _normalize_date(self, value):
        if value is None:
            return None
        if hasattr(value, "date"):
            try:
                return value.date()
            except Exception:
                pass
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(value, fmt).date()
                except Exception:
                    continue
        return value

    def _consultations_sur_periode(self, start_date, end_date):
        try:
            fn = getattr(self.controleur, "rechercher_entre_dates", None)
            if not callable(fn):
                return []
            return fn(self.code_session, start_date, end_date) or []
        except Exception:
            return []

    def _filtrer_consultations_localement(self, consultations: list, examen="Tous", chirurgie="Tous", lunette="Tous", prescription="Tous") -> list:
        mapping = [
            ("examen", examen),
            ("chirurgie", chirurgie),
            ("commandelunette", lunette),
            ("prescription_produit", prescription),
        ]
        result = []
        for consultation in consultations:
            keep = True
            for attr, expected in mapping:
                if expected == "Tous":
                    continue
                if getattr(consultation, attr, None) != expected:
                    keep = False
                    break
            if keep:
                result.append(consultation)
        return result

    def _service_counts_from_consultations(self, consultations: list) -> dict:
        counts = {"examen": 0, "chirurgie": 0, "lunette": 0, "prescription": 0}
        for consultation in consultations:
            if getattr(consultation, "examen", "Non") == "Oui":
                counts["examen"] += 1
            if getattr(consultation, "chirurgie", "Non") == "Oui":
                counts["chirurgie"] += 1
            if getattr(consultation, "commandelunette", "Non") == "Oui":
                counts["lunette"] += 1
            if getattr(consultation, "prescription_produit", "Non") == "Oui":
                counts["prescription"] += 1
        return counts

    def _aggregate_consultations_by_date(self, consultations: list) -> tuple:
        stats = {}
        for consultation in consultations:
            date_value = self._normalize_date(getattr(consultation, "date_consultation", None))
            if not date_value:
                continue
            key = date_value.strftime("%d")
            stats[key] = stats.get(key, 0) + 1
        ordered_keys = sorted(stats.keys(), key=lambda item: int(item))
        return ordered_keys, [stats[key] for key in ordered_keys]

    def _update_header_clock(self):
        now = datetime.now()
        month_names = [
            "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre",
        ]
        month_label = month_names[now.month - 1]
        self.date_badge.setText(f"{now.day:02d} {month_label} {now.year}")
        self.time_badge.setText(now.strftime("%H:%M"))

    def _update_service_legend(self, service_items: list):
        for (row, label, value, color), item in zip(self.service_legend_rows, service_items):
            c = theme_manager.colors()
            row.setStyleSheet(
                f"QFrame {{ background:{c['bg_table_alt']}; border:1px solid {c['border_light']}; border-radius:10px; }}"
            )
            label.setStyleSheet(
                f"color:{c['text_primary']}; font-size:12px; font-weight:600; border:none; background:transparent;"
            )
            value.setStyleSheet(
                f"color:{color}; font-size:13px; font-weight:800; border:none; background:transparent;"
            )
            value.setText(f"{item['value']:.0f}%")

    def _populate_waiting_table(self, rows: list):
        self.table_attente.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            patient = f"{row.get('nom', '')} {row.get('prenom', '')}".strip()
            values = [
                row.get("code_visite", ""),
                patient,
                row.get("telephone", ""),
                str(row.get("date_visite", "")),
            ]
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table_attente.setItem(row_idx, col_idx, item)

    def _populate_personnel_table(self, rows: list):
        self.table_personnel.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            nom_complet = f"Dr. {row.get('nom', '')} {row.get('prenom', '')}".strip()
            total_frais = self._safe_float(row.get("total_frais", 0))
            nombre = self._safe_int(row.get("nombre", 0))
            moyenne = total_frais / nombre if nombre else 0
            values = [
                row_idx + 1,
                nom_complet,
                nombre,
                self._format_money(total_frais),
                self._format_money(moyenne),
            ]
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                if col_idx in (0, 2):
                    item.setTextAlignment(Qt.AlignCenter)
                elif col_idx in (3, 4):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table_personnel.setItem(row_idx, col_idx, item)

    def _update_diagnostics(self, diagnostics: list):
        max_value = max([self._safe_float(row.get("nombre", 0)) for row in diagnostics], default=0.0)
        for idx, row_widget in enumerate(self.diagnostic_rows):
            if idx < len(diagnostics):
                row = diagnostics[idx]
                row_widget.update_row(str(row.get("diagnostique", "--")), self._safe_float(row.get("nombre", 0)), max_value)
                row_widget.show()
            else:
                row_widget.update_row("--", 0, 1)
                row_widget.hide()

    def _set_table_style(self, table: QTableWidget):
        c = theme_manager.colors()
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        table.setStyleSheet(
            f"QTableWidget {{ background:{c['bg_card']}; alternate-background-color:{c['bg_table_alt']}; "
            f"border:none; color:{c['text_primary']}; gridline-color:{c['border_light']}; font-size:11px; }}"
            f"QHeaderView::section {{ background:{c['table_header_bg']}; color:{c['text_primary']}; border:none; "
            f"border-bottom:1px solid {c['border_light']}; padding:6px; font-size:10px; font-weight:700; }}"
            f"QTableWidget::item {{ padding:6px; border-bottom:1px solid {c['border_light']}; }}"
        )

    def _style_filters(self):
        c = theme_manager.colors()
        shell = self._shell_colors()
        self.filters_card.setStyleSheet(
            f"QFrame {{ background:{c['bg_card']}; border:1px solid {c['border_light']}; border-radius:16px; }}"
        )
        self.filters_title.setStyleSheet(
            f"color:{c['text_primary']}; font-size:13px; font-weight:700; border:none;"
        )
        for label in self.filters_card.findChildren(QLabel):
            if label is self.filters_title:
                continue
            label.setStyleSheet(
                f"color:{c['text_secondary']}; font-size:11px; font-weight:600; border:none;"
            )
        combo_style = (
            f"QComboBox, QDateEdit {{ background:{c['bg_input']}; color:{c['text_primary']}; "
            f"border:1px solid {c['border']}; border-radius:9px; padding:0 10px; font-size:11px; font-weight:600; }}"
            f"QComboBox::drop-down, QDateEdit::drop-down {{ border:none; width:20px; }}"
            f"QComboBox QAbstractItemView {{ background:{c['bg_card']}; color:{c['text_primary']}; "
            f"border:1px solid {c['border_light']}; selection-background-color:{c['hover']}; }}"
        )
        for widget in [self.date_debut, self.date_fin, self.combo_examen, self.combo_chirurgie, self.combo_lunette, self.combo_prescription]:
            widget.setStyleSheet(combo_style)
        self.btn_filtrer.setStyleSheet(
            f"QPushButton {{ background:{shell['sidebar_active']}; color:#FFFFFF; border:none; border-radius:10px; "
            "padding:0 16px; font-size:12px; font-weight:700; }}"
            f"QPushButton:hover {{ background:{shell['sidebar_active_border']}; }}"
        )
        self.btn_filtrer.setIcon(qta.icon("fa5s.search", color="#FFFFFF"))

    def _appliquer_filtres_rapides(self):
        start_date = self._date_to_python(self.date_debut.date())
        end_date = self._date_to_python(self.date_fin.date())
        consultations = self._consultations_sur_periode(start_date, end_date)
        consultations = self._filtrer_consultations_localement(
            consultations,
            examen=self.combo_examen.currentText(),
            chirurgie=self.combo_chirurgie.currentText(),
            lunette=self.combo_lunette.currentText(),
            prescription=self.combo_prescription.currentText(),
        )
        service_counts = self._service_counts_from_consultations(consultations)
        self.service_cards[0].update_value(service_counts["examen"])
        self.service_cards[1].update_value(service_counts["chirurgie"])
        self.service_cards[2].update_value(service_counts["lunette"])
        self.service_cards[3].update_value(service_counts["prescription"])

        labels, values = self._aggregate_consultations_by_date(consultations)
        if labels:
            title = f"Consultations filtrees ({self.date_debut.date().toString('dd/MM')} - {self.date_fin.date().toString('dd/MM')})"
            self.panel_daily.set_title(title)
            self.graph_daily.update_graph(labels, values)
            self.panel_services_today.set_title("Patients par service (periode choisie)")
        else:
            self.panel_daily.set_title("Consultations filtrees")
            self.graph_daily.update_graph([], [])
            self.panel_services_today.set_title("Patients par service (periode choisie)")

    def charger_donnees(self):
        if not self.code_session or self._is_loading:
            return
        self._is_loading = True
        try:
            year = datetime.now().year
            month = datetime.now().month
            nombre_par_mois = self._call_ctrl(["obtenir_nombre_par_mois"], default={}) or {}
            montant_par_mois = self._call_ctrl(["obtenir_montant_par_mois"], default={}) or {}
            moyenne_nb = self._call_ctrl(
                ["obtenir_moyenne_nombre_journalier_par_mois", "obtenir_moyenne_consultations_par_mois"],
                default={},
            ) or {}
            moyenne_montant = self._call_ctrl(
                ["obtenir_moyenne_montant_journalier_par_mois", "obtenir_revenu_moyen_par_mois"],
                default={},
            ) or {}
            taux_services = self._call_ctrl(["obtenir_taux_conversion"], default={}) or {}
            diagnostics = (self._call_ctrl_args(["obtenir_top_diagnostics"], 5, default=[]) or [])[:5]
            personnel = (self._call_ctrl(["obtenir_consultations_par_personnel"], default=[]) or [])[:5]
            patients_attente = (self._call_ctrl(["obtenir_patients_attente"], default=[]) or [])[:5]
            nombre_par_jour = self._call_ctrl_args(["obtenir_nombre_par_jour"], year, month, default={}) or {}

            nb_jour = self._safe_int(self._call_ctrl(["obtenir_consultations_aujourd_hui"], default=0))
            nb_session = self._safe_int(self._call_ctrl(["obtenir_nombre_total", "obtenir_total_consultations_session"], default=0))
            patients_attente_total = self._safe_int(self._call_ctrl(["obtenir_nombre_patients_en_attente"], default=0))
            montant_jour = self._safe_float(self._call_ctrl(["obtenir_montant_aujourd_hui", "obtenir_montant_consultations_aujourd_hui"], default=0.0))
            montant_session = self._safe_float(self._call_ctrl(["obtenir_montant_session", "obtenir_montant_consultations_session"], default=0.0))

            self.hero_cards[0].update_content(str(nb_jour), "Aujourd'hui")
            self.hero_cards[1].update_content(str(nb_session), self._session_badge_text())
            self.hero_cards[2].update_content(str(patients_attente_total), "Sans consultation")
            self.hero_cards[3].update_content(self._format_money(montant_jour), "Revenus aujourd'hui")
            self.hero_cards[4].update_content(self._format_money(montant_session), "Revenus totaux")

            self.graph_nombre.update_graph(nombre_par_mois)
            self.graph_montant.update_graph(montant_par_mois)
            self.graph_moyenne.update_graph(moyenne_nb, moyenne_montant)

            service_items = [
                {"label": "Examen", "value": self._extraire_pourcentage(taux_services, ["examen"]), "color": "#2F7AE5"},
                {"label": "Chirurgie", "value": self._extraire_pourcentage(taux_services, ["chirurgie", "chiurgie"]), "color": "#20B486"},
                {"label": "Lunette", "value": self._extraire_pourcentage(taux_services, ["lunette", "commandelunette", "commande_lunette"]), "color": "#FF9800"},
                {"label": "Prescription", "value": self._extraire_pourcentage(taux_services, ["prescription", "prescription_produit"]), "color": "#7A44D5"},
            ]
            self.graph_services.update_graph(service_items)
            self._update_service_legend(service_items)

            self._update_diagnostics(diagnostics)
            self._populate_personnel_table(personnel)
            self._populate_waiting_table(patients_attente)

            today = datetime.now().date()
            consultations_today = self._consultations_sur_periode(today, today)
            service_counts = self._service_counts_from_consultations(consultations_today)
            self.panel_services_today.set_title("Patients par service (aujourd'hui)")
            self.service_cards[0].update_value(service_counts["examen"])
            self.service_cards[1].update_value(service_counts["chirurgie"])
            self.service_cards[2].update_value(service_counts["lunette"])
            self.service_cards[3].update_value(service_counts["prescription"])

            ordered_days = sorted(nombre_par_jour.keys(), key=lambda item: int(item))
            daily_labels = ordered_days
            daily_values = [self._safe_int(nombre_par_jour.get(day, 0)) for day in ordered_days]
            self.panel_daily.set_title(f"Consultations par jour ({self._mois_label(month)} {year})")
            self.graph_daily.update_graph(daily_labels, daily_values)

            self.page_title.setText(self._session_title_text())
        except Exception as e:
            print(f"[AnalyseConsultationView] Erreur chargement donnees: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._is_loading = False

    def apply_theme(self):
        c = theme_manager.colors()
        shell = self._shell_colors()

        self.setStyleSheet(f"QWidget#AnalyseConsultationView {{ background:{shell['shell']}; }}")
        self.content_shell.setStyleSheet("QFrame { background: transparent; }")
        self.top_bar.setStyleSheet("QFrame { background: transparent; border:none; }")

        self.menu_button.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.08); border:none; border-radius:10px; }"
            "QPushButton:hover { background: rgba(255,255,255,0.14); }"
        )
        self.menu_button.setIcon(qta.icon("fa5s.bars", color="#FFFFFF"))
        self.page_title.setStyleSheet(f"color:{shell['top_text']}; font-size:17px; font-weight:800; border:none;")
        self.page_subtitle.setStyleSheet(f"color:{shell['top_subtext']}; font-size:12px; font-weight:500; border:none;")

        badge_style = (
            f"background:{shell['badge_bg']}; color:{shell['badge_text']}; border:none; border-radius:10px; "
            "padding:6px 12px; font-size:12px; font-weight:700;"
        )
        self.date_badge.setStyleSheet(badge_style)
        self.time_badge.setStyleSheet(badge_style)
        self.session_badge.setStyleSheet(
            f"QPushButton {{ background:{shell['badge_bg']}; color:{shell['badge_text']}; border:1px solid rgba(255,255,255,0.10); "
            "border-radius:10px; padding:0 12px; font-size:12px; font-weight:700; }}"
        )
        self.session_badge.setText(self._session_badge_text())
        self.session_badge.setIcon(qta.icon("fa5s.chevron-down", color="#FFFFFF"))

        self.scroll.setStyleSheet("QScrollArea { background: transparent; border:none; }")
        self.dashboard_surface.setStyleSheet(
            "QFrame { background: #F7FAFF; border:none; border-radius:20px; }"
        )

        for card in self.hero_cards:
            card.apply_theme()
        for section in self.section_cards:
            section.apply_theme()
        for row_widget in self.diagnostic_rows:
            row_widget.apply_theme()
        for card in self.service_cards:
            card.apply_theme()

        self._set_table_style(self.table_personnel)
        self._set_table_style(self.table_attente)
        self.btn_attente.setStyleSheet(
            f"QPushButton {{ background:{shell['sidebar_active']}; color:#FFFFFF; border:none; border-radius:9px; font-size:12px; font-weight:700; }}"
            f"QPushButton:hover {{ background:{shell['sidebar_active_border']}; }}"
        )
        self._style_filters()
        self.page_title.setText(self._session_title_text())

    def rafraichir(self):
        self._update_header_clock()
        self.charger_donnees()
