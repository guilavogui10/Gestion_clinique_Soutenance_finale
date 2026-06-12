import numpy as np
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
        
        # Texte fixe pour le hover en haut
        self.hover_text = self.fig.text(0.5, 0.96, '', ha='center', va='top', fontsize=10, fontweight='bold')
        
        super().__init__(self.fig)
        self.setParent(parent)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_hover)
        self.fig.canvas.mpl_connect('axes_leave_event', lambda event: self._clear_hover_text())
        self.fig.canvas.mpl_connect('figure_leave_event', lambda event: self._clear_hover_text())

    def _setup_style(self):
        for spine in self.axes.spines.values():
            spine.set_visible(False)

        self.axes.grid(
            True,
            axis="both",
            linestyle="--",
            alpha=0.3,
            color=self.theme.COLORS["border"],
            linewidth=0.8,
        )
        self.axes.tick_params(colors=self.theme.COLORS["subtext"], labelsize=9, length=0, pad=8)
        
        if hasattr(self, 'hover_text'):
            self.hover_text.set_text('')
            
        self.fig.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.15)

    def _create_linear_curve(self, x, y, color, alpha=0.9):
        """Crée une courbe linéaire (lignes droites entre les points)"""
        if len(y) < 2 or float(np.sum(y)) == 0.0:
            return
            
        self.axes.plot(x, y, color=color, linewidth=2.0, alpha=alpha, antialiased=True, zorder=5)

    def _create_data_points(self, x, y, color, label):
        scatter = self.axes.scatter(
            x,
            y,
            color=color,
            edgecolor=self.theme.COLORS["surface"],
            s=50,
            zorder=10,
            linewidth=1.5,
            alpha=1.0,
        )
        
        if not hasattr(self, 'scatters'):
            self.scatters = []
        self.scatters.append({'scatter': scatter, 'label': label, 'x': x, 'y': y})

    def _on_hover(self, event):
        if not event.inaxes:
            self._clear_hover_text()
            return

        if not hasattr(self, 'scatters'):
            return

        found = False
        for item in self.scatters:
            cont, ind = item['scatter'].contains(event)
            if cont:
                idx = ind["ind"][0]
                value = item['y'][idx]
                label = item['label']
                
                month = self.month_labels[idx] if hasattr(self, 'month_labels') and 0 <= idx < len(self.month_labels) else ""
                text = f"{label} en {month} : {int(value)}" if month else f"{label} : {int(value)}"

                if self.hover_text.get_text() != text:
                    self.hover_text.set_text(text)
                    self.hover_text.set_color(self.theme.COLORS["text"])
                    self.fig.canvas.draw_idle()
                
                found = True
                break
                
        if not found and self.hover_text.get_text() != '':
            self._clear_hover_text()

    def _clear_hover_text(self):
        self.hover_text.set_text('')
        self.fig.canvas.draw_idle()

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
        if hasattr(self, 'scatters'):
            self.scatters.clear()
        self._setup_style()

        if not stats_mensuelles:
            self._finalize()
            return

        values = [stats_mensuelles.get(mois, 0) for mois in self.month_labels]
        x = np.arange(len(self.month_labels))
        y = np.array(values, dtype=float)
        color = self.theme.COLORS["accent"]

        self._create_linear_curve(x, y, color)
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
