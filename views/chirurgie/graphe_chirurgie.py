import numpy as np
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
        
        self.hover_text = self.fig.text(0.5, 0.96, '', ha='center', va='top', fontsize=10, fontweight='bold')

        super().__init__(self.fig)
        self.setParent(parent)
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_hover)
        self.fig.canvas.mpl_connect('axes_leave_event', lambda event: self._clear_hover_text())
        self.fig.canvas.mpl_connect('figure_leave_event', lambda event: self._clear_hover_text())

    def _setup_modern_style(self):
        for spine in self.axes.spines.values():
            spine.set_visible(False)

        self.axes.grid(True, axis="both", linestyle="--", alpha=0.3,
                       color=self.theme.COLORS["border"], linewidth=0.8)

        self.axes.tick_params(
            colors=self.theme.COLORS["subtext"],
            labelsize=9,
            length=0,
            pad=8
        )
        
        if hasattr(self, 'hover_text'):
            self.hover_text.set_text('')

        self.fig.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.15)

    def _create_linear_curve(self, x, y, color, label=None, alpha=0.9):
        if len(y) < 2 or sum(y) == 0:
            return None, None

        line = self.axes.plot(
            x, y,
            color=color, linewidth=2.0, alpha=alpha,
            label=label, antialiased=True, zorder=5
        )[0]

        return line, (x, y)

    def _create_data_points(self, x, y, color, category_name):
        scatter = self.axes.scatter(
            x, y,
            color=color,
            edgecolor=self.theme.COLORS["surface"],
            s=50, zorder=10, linewidth=1.5, alpha=1.0
        )

        if not hasattr(self, 'scatters'):
            self.scatters = []
        self.scatters.append({'scatter': scatter, 'label': category_name, 'x': x, 'y': y})

        return scatter

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
                category_name = item['label']
                
                if hasattr(self, "month_labels") and 0 <= idx < len(self.month_labels):
                    text = f"{category_name} en {self.month_labels[idx]} : {int(value)}"
                else:
                    text = f"{category_name} : {int(value)}"

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


class ChirurgieAnalyseGraph(BaseGraph):
    """
    Graphique moderne pour l analyse des chirurgies par mois.
    Meme architecture que ExamenAnalyseGraph.
    """

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent, width, height, dpi)
        self.month_labels = [
            'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
            'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'
        ]
        self._last_stats = None
        theme_manager.theme_changed.connect(self._on_theme_change)

    def _on_theme_change(self):
        if self._last_stats is not None:
            self.update_graph(self._last_stats)

    def update_graph(self, stats_mensuelles: dict):
        """
        Met a jour le graphique des chirurgies.
        """
        self._last_stats = stats_mensuelles
        self.axes.clear()
        if hasattr(self, 'scatters'):
            self.scatters.clear()
        self._setup_modern_style()

        if not stats_mensuelles:
            self._finalize_plot()
            return

        values = [stats_mensuelles.get(mois, 0) for mois in self.month_labels]
        x = np.arange(len(self.month_labels))
        y = np.array(values, dtype=float)

        color = self.theme.COLORS["danger"]

        # Courbe linéaire
        self._create_linear_curve(x, y, color, alpha=0.9)

        # Points interactifs
        self._create_data_points(x, y, color, "Chirurgies")

        # Configuration des axes
        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.month_labels, rotation=0)
        self._set_intelligent_ylim(values)

        # Label axe Y
        self.axes.set_ylabel(
            "Nombre de chirurgies",
            color=self.theme.COLORS["subtext"],
            fontsize=10,
            fontweight="500"
        )

        self._finalize_plot()


class MontantChirurgiesGraph(BaseGraph):
    """
    Graphique scatter pour le montant des chirurgies par mois.
    """

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent, width, height, dpi)
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
        Met à jour le graphique du montant avec scatter.
        """
        self._last_stats = stats_mensuelles or {}
        self.axes.clear()
        if hasattr(self, 'scatters'):
            self.scatters.clear()
        self._setup_modern_style()

        if not stats_mensuelles:
            self._finalize_plot()
            return

        values = [stats_mensuelles.get(mois, 0) for mois in self.month_labels]
        x = np.arange(len(self.month_labels))
        y = np.array(values, dtype=float)

        color = self.theme.COLORS["success"]

        # Courbe linéaire
        self._create_linear_curve(x, y, color, alpha=0.9)

        # Points interactifs
        self._create_data_points(x, y, color, "Montant (GNF)")

        # Configuration des axes sans étiquettes Y
        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.month_labels, rotation=0)
        self.axes.yaxis.set_visible(False) # Masquer la barre Y
        self._set_intelligent_ylim(values)

        self._finalize_plot()


class MoyenneJournaliereChirurgiesGraph(BaseGraph):
    """
    Graphique scatter pour la moyenne journalière par mois.
    """

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent, width, height, dpi)
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
        Met à jour le graphique de la moyenne.
        """
        self._last_stats = stats_mensuelles or {}
        self.axes.clear()
        if hasattr(self, 'scatters'):
            self.scatters.clear()
        self._setup_modern_style()

        if not stats_mensuelles:
            self._finalize_plot()
            return

        values = [stats_mensuelles.get(mois, 0) for mois in self.month_labels]
        x = np.arange(len(self.month_labels))
        y = np.array(values)
        
        color = self.theme.COLORS["info"]

        # Courbe linéaire
        self._create_linear_curve(x, y, color, alpha=0.9)
        
        # Points interactifs
        self._create_data_points(x, y, color, "Revenu moyen")

        # Configuration des axes
        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.month_labels, rotation=0)
        self._set_intelligent_ylim(values)

        # Label axe Y
        self.axes.set_ylabel(
            "Revenu moyen (GNF)",
            color=self.theme.COLORS["subtext"],
            fontsize=10,
            fontweight="500"
        )

        self._finalize_plot()
