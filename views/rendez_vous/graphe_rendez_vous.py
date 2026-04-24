import numpy as np
from scipy.interpolate import make_interp_spline
import mplcursors
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from views.shared.theme_manager import theme_manager


class _TC:
    def __init__(self, key):
        self._key = key

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, objtype=None):
        return theme_manager.colors()[self._key]


class ModernTheme:
    primary = _TC("primary")
    success = _TC("success")
    warning = _TC("warning")
    danger = _TC("danger")
    info = _TC("info")
    accent = _TC("accent")
    text = _TC("text_primary")
    subtext = _TC("text_secondary")
    background = _TC("bg_main")
    surface = _TC("bg_card")
    border = _TC("border")

    @property
    def COLORS(self):
        return {
            "primary": self.primary,
            "success": self.success,
            "warning": self.warning,
            "danger": self.danger,
            "info": self.info,
            "accent": self.accent,
            "text": self.text,
            "subtext": self.subtext,
            "background": self.background,
            "surface": self.surface,
            "border": self.border,
        }


class BaseGraph(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.theme = ModernTheme()
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor("none")
        super().__init__(self.fig)
        self.setParent(parent)
        self.cursors = []
        self._setup_style()

    def _setup_style(self):
        for spine in self.axes.spines.values():
            spine.set_visible(False)

        self.axes.grid(
            True,
            axis="y",
            linestyle="-",
            alpha=0.1,
            color=self.theme.COLORS["border"],
            linewidth=0.8,
        )
        self.axes.tick_params(colors=self.theme.COLORS["subtext"], labelsize=9, length=0, pad=8)
        self.fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)

    def _create_smooth_curve(self, x, y, color):
        if len(y) < 2 or float(np.sum(y)) == 0.0:
            return
        x_smooth = np.linspace(x.min(), x.max(), 200)
        spline = make_interp_spline(x, y, k=min(3, len(y) - 1))
        y_smooth = np.maximum(spline(x_smooth), 0)
        source_max = float(np.max(y)) if len(y) else 0.0
        if source_max > 0:
            y_smooth = np.clip(y_smooth, 0, source_max * 1.05)
        self.axes.plot(x_smooth, y_smooth, color=color, linewidth=2.5, alpha=0.9, antialiased=True)
        self.axes.fill_between(x_smooth, y_smooth, color=color, alpha=0.1, antialiased=True)

    def _create_data_points(self, x, y, color, label):
        scatter = self.axes.scatter(
            x,
            y,
            color=self.theme.COLORS["surface"],
            edgecolor=color,
            s=50,
            zorder=10,
            linewidth=2,
            alpha=0.9,
        )
        cursor = mplcursors.cursor(scatter, hover=True)
        cursor.connect("add", lambda sel: self._style_tooltip(sel, label))
        self.cursors.append(cursor)

    def _style_tooltip(self, sel, label):
        idx = int(round(sel.target[0]))
        value = int(sel.target[1])
        month = self.month_labels[idx] if 0 <= idx < len(self.month_labels) else ""
        sel.annotation.set_text(f"{month}\n{label}: {value}")
        sel.annotation.get_bbox_patch().set(
            fc=self.theme.COLORS["surface"],
            ec=self.theme.COLORS["border"],
            boxstyle="round,pad=0.5",
            alpha=0.95,
            linewidth=1,
        )
        sel.annotation.set_color(self.theme.COLORS["text"])
        sel.annotation.set_fontsize(9)
        sel.annotation.set_fontweight("500")
        sel.annotation.arrow_patch.set_visible(False)

    def _set_ylim(self, values):
        max_val = max(values) if values else 0
        upper = 10 if max_val < 10 else max_val * 1.2
        self.axes.set_ylim(0, upper)
        self.axes.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

    def _finalize(self):
        self.fig.tight_layout()
        self.draw()


class RendezVousAnalyseGraph(BaseGraph):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent, width, height, dpi)
        self.month_labels = [
            "Jan", "Fev", "Mar", "Avr", "Mai", "Juin",
            "Juil", "Aout", "Sep", "Oct", "Nov", "Dec",
        ]

    def update_graph(self, stats_mensuelles: dict):
        self.axes.clear()
        self._setup_style()

        if not stats_mensuelles:
            self._finalize()
            return

        values = [stats_mensuelles.get(mois, 0) for mois in self.month_labels]
        x = np.arange(len(self.month_labels))
        y = np.array(values, dtype=float)
        color = self.theme.COLORS["accent"]

        self._create_smooth_curve(x, y, color)
        self._create_data_points(x, y, color, "Rendez-vous")

        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.month_labels, rotation=0)
        self._set_ylim(values)
        self.axes.set_ylabel(
            "Nombre de rendez-vous",
            color=self.theme.COLORS["subtext"],
            fontsize=10,
            fontweight="500",
        )
        self._finalize()
