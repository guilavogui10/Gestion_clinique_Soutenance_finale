import numpy as np
from scipy.interpolate import make_interp_spline
import mplcursors
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
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
    """Theme moderne pour les graphiques avec palette coherente."""

    primary    = _TC('primary')
    success    = _TC('success')
    warning    = _TC('warning')
    danger     = _TC('danger')
    info       = _TC('info')
    accent     = _TC('accent')
    text       = _TC('text_primary')
    subtext    = _TC('text_secondary')
    background = _TC('bg_main')
    surface    = _TC('bg_card')
    border     = _TC('border')

    @property
    def COLORS(self):
        return {
            "primary":    self.primary,
            "success":    self.success,
            "warning":    self.warning,
            "danger":     self.danger,
            "info":       self.info,
            "accent":     self.accent,
            "text":       self.text,
            "subtext":    self.subtext,
            "background": self.background,
            "surface":    self.surface,
            "border":     self.border,
        }


class BaseGraph(FigureCanvas):
    """Classe de base pour tous les graphiques avec style moderne."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.theme = ModernTheme()
        self.fig   = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
        self.axes  = self.fig.add_subplot(111)
        self.axes.set_facecolor("none")

        super().__init__(self.fig)
        self.setParent(parent)
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cursors = []
        self._setup_modern_style()

    def _setup_modern_style(self):
        for spine in self.axes.spines.values():
            spine.set_visible(False)

        self.axes.grid(True, axis="y", linestyle="-", alpha=0.1,
                       color=self.theme.COLORS["border"], linewidth=0.8)

        self.axes.tick_params(
            colors=self.theme.COLORS["subtext"],
            labelsize=9,
            length=0,
            pad=8
        )

        self.fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)

    def _create_smooth_curve(self, x, y, color, label=None, alpha=0.8):
        if len(y) < 2 or sum(y) == 0:
            return None, None

        x_smooth = np.linspace(x.min(), x.max(), 200)
        spline   = make_interp_spline(x, y, k=min(3, len(y) - 1))
        y_smooth = np.maximum(spline(x_smooth), 0)

        line = self.axes.plot(
            x_smooth, y_smooth,
            color=color, linewidth=2.5, alpha=alpha,
            label=label, antialiased=True
        )[0]

        self.axes.fill_between(x_smooth, y_smooth, color=color, alpha=0.1, antialiased=True)

        return line, (x_smooth, y_smooth)

    def _create_data_points(self, x, y, color, category_name):
        scatter = self.axes.scatter(
            x, y,
            color=self.theme.COLORS["surface"],
            edgecolor=color,
            s=50, zorder=10, linewidth=2, alpha=0.9
        )

        cursor = mplcursors.cursor(scatter, hover=True)
        cursor.connect("add", lambda sel: self._style_tooltip(sel, category_name))
        self.cursors.append(cursor)

        return scatter

    def _style_tooltip(self, sel, category_name):
        idx   = int(round(sel.target[0]))
        value = int(sel.target[1])

        if hasattr(self, "month_labels") and idx < len(self.month_labels):
            text = f"{self.month_labels[idx]}\n{category_name}: {value}"
        else:
            text = f"{category_name}: {value}"

        sel.annotation.set_text(text)
        sel.annotation.get_bbox_patch().set(
            fc=self.theme.COLORS["surface"],
            ec=self.theme.COLORS["border"],
            boxstyle="round,pad=0.5",
            alpha=0.95,
            linewidth=1
        )
        sel.annotation.set_color(self.theme.COLORS["text"])
        sel.annotation.set_fontsize(9)
        sel.annotation.set_fontweight("500")
        sel.annotation.arrow_patch.set_visible(False)

    def _set_intelligent_ylim(self, values):
        if not values:
            self.axes.set_ylim(0, 10)
            return

        max_val = max(values)
        if max_val == 0:
            self.axes.set_ylim(0, 10)
        elif max_val < 10:
            self.axes.set_ylim(0, 10)
        else:
            self.axes.set_ylim(0, max_val * 1.2)

        self.axes.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

    def _finalize_plot(self):
        self.fig.tight_layout()
        self.draw()


class ConsultationAnalyseGraph(BaseGraph):
    """
    Graphique moderne pour l analyse des consultations par mois.
    Meme architecture que VisiteAnalyseGraph.
    
    Usage dans ConsultationView :
        self.graphe = ConsultationAnalyseGraph(parent=self.frame_graph)
        self.graphe.update_graph(self.ctrl.obtenir_nombre_par_mois(code_session))
    """

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent, width, height, dpi)
        # APRÈS — identique aux clés du DAO
        self.month_labels = [
            'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
            'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'
        ]
        self._last_stats = {}
        theme_manager.theme_changed.connect(self._on_theme_change)

    def _on_theme_change(self):
        if self._last_stats:
            self.update_graph(self._last_stats)

    def update_graph(self, stats_mensuelles: dict):
        """
        Met a jour le graphique des consultations.

        Parametre :
            stats_mensuelles (dict) : resultat de ctrl.obtenir_nombre_par_mois()
            Exemple : {"Jan": 5, "Fev": 12, "Mar": 0, ..., "Dec": 3}
        """
        print("[DEBUG] stats reçues:", stats_mensuelles)  # ← à retirer après test
        self._last_stats = stats_mensuelles or {}
        self.axes.clear()
        self._setup_modern_style()

        if not stats_mensuelles:
            self._finalize_plot()
            return

        values = [stats_mensuelles.get(mois, 0) for mois in self.month_labels]
        print("[DEBUG] values extraites:", values)         # ← à retirer après test
        x = np.arange(len(self.month_labels))
        y = np.array(values, dtype=float)

        color = self.theme.COLORS["primary"]

        # Courbe lissee + zone de remplissage
        self._create_smooth_curve(x, y, color, alpha=0.9)

        # Points interactifs avec tooltip au survol
        self._create_data_points(x, y, color, "Consultations")

        # Configuration des axes
        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.month_labels, rotation=0)
        self._set_intelligent_ylim(values)

        # Label axe Y
        self.axes.set_ylabel(
            "Nombre de consultations",
            color=self.theme.COLORS["subtext"],
            fontsize=10,
            fontweight="500"
        )

        self._finalize_plot()