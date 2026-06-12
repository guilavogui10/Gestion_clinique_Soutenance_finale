"""
Graphiques statistiques pour les commandes de lunettes.
3 graphiques matplotlib organisés en ligne horizontale :
  1. Nombre de commandes par mois (courbe linéaire)
  2. Montant des commandes par mois (courbe linéaire)
  3. Revenu moyen journalier par mois (courbe linéaire)
"""
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from PySide6.QtCore    import Qt
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QSizePolicy
)
from PySide6.QtGui import QFont

from views.shared.theme_manager import theme_manager


# =============================================================================
# THÈME DYNAMIQUE
# =============================================================================

class _TC:
    def __init__(self, key):
        self._key = key
    def __get__(self, obj, objtype=None):
        return theme_manager.colors()[self._key]


class ModernTheme:
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


# =============================================================================
# BASE GRAPH
# =============================================================================

class BaseGraph(FigureCanvas):
    """Classe de base pour tous les graphiques lunette avec style moderne."""

    MONTH_LABELS = [
        'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
        'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'
    ]

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.theme = ModernTheme()
        _bg = theme_manager.colors()['bg_card']
        self.fig   = Figure(figsize=(width, height), dpi=dpi, facecolor=_bg)
        self.axes  = self.fig.add_subplot(111)
        self.axes.set_facecolor(_bg)

        self.hover_text = self.fig.text(0.5, 0.96, '', ha='center', va='top', fontsize=10, fontweight='bold')

        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._last_stats = {}
        self.setStyleSheet(f"background-color: {_bg};")

        self.fig.canvas.mpl_connect('motion_notify_event', self._on_hover)
        self.fig.canvas.mpl_connect('axes_leave_event', lambda event: self._clear_hover_text())
        self.fig.canvas.mpl_connect('figure_leave_event', lambda event: self._clear_hover_text())

        self._setup_modern_style()
        theme_manager.theme_changed.connect(self._on_theme_change)
        theme_manager.theme_changed.connect(self._on_canvas_theme_change)

    def _on_theme_change(self):
        if self._last_stats:
            self.update_graph(self._last_stats)

    def _on_canvas_theme_change(self):
        bg = theme_manager.colors()['bg_card']
        self.setStyleSheet(f"background-color: {bg};")
        self.fig.patch.set_facecolor(bg)
        self.axes.set_facecolor(bg)
        self.draw_idle()

    def _setup_modern_style(self):
        bg = theme_manager.colors()['bg_card']
        self.fig.patch.set_facecolor(bg)
        self.axes.set_facecolor(bg)

        for spine in self.axes.spines.values():
            spine.set_visible(False)
        self.axes.grid(
            True, axis="both", linestyle="--", alpha=0.3,
            color=self.theme.COLORS["border"], linewidth=0.8
        )
        self.axes.tick_params(
            colors=self.theme.COLORS["subtext"], labelsize=9, length=0, pad=8
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
                
                if 0 <= idx < len(self.MONTH_LABELS):
                    text = f"{category_name} en {self.MONTH_LABELS[idx]} : {int(value):,}"
                else:
                    text = f"{category_name} : {int(value):,}"

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
        max_val = max(values) if values else 0
        if max_val == 0:
            self.axes.set_ylim(0, 10)
        elif max_val < 10:
            self.axes.set_ylim(0, 10)
        else:
            self.axes.set_ylim(0, max_val * 1.2)
        self.axes.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

    def _finalize(self):
        self.fig.tight_layout()
        self.draw()


# =============================================================================
# GRAPHIQUE 1 — Nombre de commandes par mois
# =============================================================================

class CommandeNombreParMoisGraph(BaseGraph):
    """Courbe linéaire : nombre de commandes par mois."""

    def update_graph(self, stats: dict):
        self._last_stats = stats or {}
        self.axes.clear()
        if hasattr(self, 'scatters'):
            self.scatters.clear()
        self._setup_modern_style()

        if not stats:
            self._finalize()
            return

        values = [stats.get(m, 0) for m in self.MONTH_LABELS]
        x      = np.arange(len(self.MONTH_LABELS))
        y      = np.array(values, dtype=float)
        color  = self.theme.COLORS["primary"]

        self._create_linear_curve(x, y, color)
        self._create_data_points(x, y, color, "Commandes")

        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.MONTH_LABELS, rotation=0, fontsize=8)
        self._set_intelligent_ylim(values)
        self.axes.set_ylabel(
            "Nb commandes",
            color=self.theme.COLORS["subtext"], fontsize=9, fontweight="500"
        )
        self._finalize()


# =============================================================================
# GRAPHIQUE 2 — Montant des commandes par mois
# =============================================================================

class CommandeMontantParMoisGraph(BaseGraph):
    """Courbe linéaire : montant total des commandes par mois (GNF)."""

    def update_graph(self, stats: dict):
        self._last_stats = stats or {}
        self.axes.clear()
        if hasattr(self, 'scatters'):
            self.scatters.clear()
        self._setup_modern_style()

        if not stats:
            self._finalize()
            return

        values = [stats.get(m, 0) for m in self.MONTH_LABELS]
        x      = np.arange(len(self.MONTH_LABELS))
        y      = np.array(values, dtype=float)
        color  = self.theme.COLORS["success"]

        self._create_linear_curve(x, y, color)
        self._create_data_points(x, y, color, "Montant (GNF)")

        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.MONTH_LABELS, rotation=0, fontsize=8)
        self.axes.yaxis.set_visible(False)
        self._set_intelligent_ylim(values)
        self._finalize()


# =============================================================================
# GRAPHIQUE 3 — Revenu moyen journalier par mois
# =============================================================================

class CommandeRevenuMoyenGraph(BaseGraph):
    """Courbe linéaire : revenu moyen journalier des commandes par mois."""

    def update_graph(self, stats: dict):
        self._last_stats = stats or {}
        self.axes.clear()
        if hasattr(self, 'scatters'):
            self.scatters.clear()
        self._setup_modern_style()

        if not stats:
            self._finalize()
            return

        values = [stats.get(m, 0) for m in self.MONTH_LABELS]
        x      = np.arange(len(self.MONTH_LABELS))
        y      = np.array(values, dtype=float)
        color  = self.theme.COLORS["warning"]

        self._create_linear_curve(x, y, color)
        self._create_data_points(x, y, color, "Revenu moyen")

        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.MONTH_LABELS, rotation=0, fontsize=8)
        self._set_intelligent_ylim(values)
        self.axes.set_ylabel(
            "Revenu moyen (GNF)",
            color=self.theme.COLORS["subtext"], fontsize=9, fontweight="500"
        )
        self._finalize()


# =============================================================================
# SECTION CHARTS — 3 graphiques en ligne (comme ChartsSection consultation)
# =============================================================================

class CommandeLunetteChartsSection(QWidget):
    """3 graphiques en ligne horizontale pour l'onglet Statistiques lunettes."""

    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self._init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Graphique 1 — Nombre par mois
        self.frame1 = self._create_chart_frame("Nombre de commandes par mois")
        self.graph1 = CommandeNombreParMoisGraph(self.frame1, width=6, height=4, dpi=100)
        self.frame1.layout().addWidget(self.graph1)

        # Graphique 2 — Montant par mois
        self.frame2 = self._create_chart_frame("Montant des commandes par mois (GNF)")
        self.graph2 = CommandeMontantParMoisGraph(self.frame2, width=6, height=4, dpi=100)
        self.frame2.layout().addWidget(self.graph2)

        # Graphique 3 — Revenu moyen journalier
        self.frame3 = self._create_chart_frame("Revenu moyen journalier (GNF)")
        self.graph3 = CommandeRevenuMoyenGraph(self.frame3, width=6, height=4, dpi=100)
        self.frame3.layout().addWidget(self.graph3)

        layout.addWidget(self.frame1, 1)
        layout.addWidget(self.frame2, 1)
        layout.addWidget(self.frame3, 1)

    def _create_chart_frame(self, title: str) -> QFrame:
        c = theme_manager.colors()
        frame = QFrame()
        frame.setObjectName("ChartFrame")
        frame.setStyleSheet(f"""
            QFrame#ChartFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border_light']};
                border-radius: 12px;
            }}
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(4)

        lbl = QLabel(title)
        lbl.setObjectName("ChartTitle")
        f = QFont()
        f.setPointSize(10)
        f.setBold(True)
        lbl.setFont(f)
        lbl.setStyleSheet(
            f"color: {c['text_primary']}; border: none; background: {c['bg_card']};"
        )
        lay.addWidget(lbl)
        return frame

    def update_data(self, code_session: str):
        """Met à jour les 3 graphiques depuis le contrôleur."""
        if not code_session:
            return

        try:
            self.graph1.update_graph(
                self.ctrl.obtenir_nombre_par_mois(code_session) or {}
            )
        except Exception as e:
            print(f"[LunetteCharts] graph1: {e}")
            self.graph1.update_graph({})

        try:
            self.graph2.update_graph(
                self.ctrl.obtenir_montant_par_mois(code_session) or {}
            )
        except Exception as e:
            print(f"[LunetteCharts] graph2: {e}")
            self.graph2.update_graph({})

        try:
            self.graph3.update_graph(
                self.ctrl.obtenir_revenu_moyen_par_mois(code_session) or {}
            )
        except Exception as e:
            print(f"[LunetteCharts] graph3: {e}")
            self.graph3.update_graph({})

    def apply_theme(self):
        c = theme_manager.colors()
        bg = c['bg_card']
        for frame, title in [
            (self.frame1, "Nombre de commandes par mois"),
            (self.frame2, "Montant des commandes par mois (GNF)"),
            (self.frame3, "Revenu moyen journalier (GNF)"),
        ]:
            frame.setStyleSheet(f"""
                QFrame#ChartFrame {{
                    background: {bg};
                    border: 1px solid {c['border_light']};
                    border-radius: 12px;
                }}
            """)
            lbl = frame.findChild(QLabel, "ChartTitle")
            if lbl:
                lbl.setStyleSheet(
                    f"color: {c['text_primary']}; border: none; background: {c['bg_card']};"
                )

        for graph in (self.graph1, self.graph2, self.graph3):
            graph.setStyleSheet(f"background-color: {bg};")
            graph.fig.patch.set_facecolor(bg)
            graph.axes.set_facecolor(bg)
            graph.draw_idle()


# Alias de compatibilité (ancienne API utilisée dans vue_commande_lunette)
CommandeLunetteAnalyseGraph = CommandeLunetteChartsSection
