"""
Graphiques statistiques pour les commandes de lunettes.
3 graphiques matplotlib organisés en ligne horizontale :
  1. Nombre de commandes par mois (barres verticales)
  2. Montant des commandes par mois (courbe lissée)
  3. Revenu moyen journalier par mois (courbe lissée)
"""
import numpy as np
from scipy.interpolate import make_interp_spline
import mplcursors
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
        self.fig   = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
        self.axes  = self.fig.add_subplot(111)
        self.axes.set_facecolor("none")
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cursors     = []
        self._last_stats = {}
        self._setup_modern_style()
        theme_manager.theme_changed.connect(self._on_theme_change)

    def _on_theme_change(self):
        if self._last_stats:
            self.update_graph(self._last_stats)

    def _setup_modern_style(self):
        for spine in self.axes.spines.values():
            spine.set_visible(False)
        self.axes.grid(
            True, axis="y", linestyle="-", alpha=0.1,
            color=self.theme.COLORS["border"], linewidth=0.8
        )
        self.axes.tick_params(
            colors=self.theme.COLORS["subtext"], labelsize=9, length=0, pad=8
        )
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.18)

    def _create_smooth_curve(self, x, y, color, label=None, alpha=0.85):
        if len(y) < 2 or sum(y) == 0:
            return None, None
        x_smooth = np.linspace(x.min(), x.max(), 200)
        spline   = make_interp_spline(x, y, k=min(3, len(y) - 1))
        y_smooth = np.maximum(spline(x_smooth), 0)
        self.axes.plot(
            x_smooth, y_smooth,
            color=color, linewidth=2.5, alpha=alpha,
            label=label, antialiased=True
        )
        self.axes.fill_between(x_smooth, y_smooth, color=color, alpha=0.1)
        return x_smooth, y_smooth

    def _create_data_points(self, x, y, color, category_name):
        scatter = self.axes.scatter(
            x, y,
            color=self.theme.COLORS["surface"],
            edgecolor=color, s=50, zorder=10, linewidth=2, alpha=0.9
        )
        cursor = mplcursors.cursor(scatter, hover=True)
        cursor.connect("add", lambda sel: self._style_tooltip(sel, category_name))
        self.cursors.append(cursor)

    def _style_tooltip(self, sel, category_name):
        idx   = int(round(sel.target[0]))
        value = sel.target[1]
        lbl   = self.MONTH_LABELS[idx] if idx < len(self.MONTH_LABELS) else str(idx)
        sel.annotation.set_text(f"{lbl}\n{category_name}: {int(value):,}")
        sel.annotation.get_bbox_patch().set(
            fc=self.theme.COLORS["surface"], ec=self.theme.COLORS["border"],
            boxstyle="round,pad=0.5", alpha=0.95, linewidth=1
        )
        sel.annotation.set_color(self.theme.COLORS["text"])
        sel.annotation.set_fontsize(9)
        sel.annotation.arrow_patch.set_visible(False)

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
# GRAPHIQUE 1 — Nombre de commandes par mois (barres verticales)
# =============================================================================

class CommandeNombreParMoisGraph(BaseGraph):
    """Barres verticales : nombre de commandes par mois."""

    def update_graph(self, stats: dict):
        self._last_stats = stats or {}
        self.axes.clear()
        self._setup_modern_style()

        if not stats:
            self._finalize()
            return

        values = [stats.get(m, 0) for m in self.MONTH_LABELS]
        x      = np.arange(len(self.MONTH_LABELS))
        color  = self.theme.COLORS["primary"]

        bars = self.axes.bar(x, values, width=0.6, color=color,
                             edgecolor='none', alpha=0.8)
        for bar, val in zip(bars, values):
            if val > 0:
                self.axes.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.3,
                    str(int(val)),
                    ha='center', va='bottom', fontsize=8, fontweight='600',
                    color=self.theme.COLORS["text"]
                )

        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.MONTH_LABELS, rotation=0, fontsize=8)
        self.axes.set_xlim(-0.8, len(self.MONTH_LABELS) - 0.2)
        self._set_intelligent_ylim(values)
        self.axes.set_ylabel(
            "Nb commandes",
            color=self.theme.COLORS["subtext"], fontsize=9, fontweight="500"
        )
        self._finalize()


# =============================================================================
# GRAPHIQUE 2 — Montant des commandes par mois (courbe lissée)
# =============================================================================

class CommandeMontantParMoisGraph(BaseGraph):
    """Courbe lissée : montant total des commandes par mois (GNF)."""

    def update_graph(self, stats: dict):
        self._last_stats = stats or {}
        self.axes.clear()
        self._setup_modern_style()

        if not stats:
            self._finalize()
            return

        values = [stats.get(m, 0) for m in self.MONTH_LABELS]
        x      = np.arange(len(self.MONTH_LABELS))
        y      = np.array(values, dtype=float)
        color  = self.theme.COLORS["success"]

        self._create_smooth_curve(x, y, color)
        self._create_data_points(x, y, color, "Montant (GNF)")

        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.MONTH_LABELS, rotation=0, fontsize=8)
        self.axes.set_xlim(-0.8, len(self.MONTH_LABELS) - 0.2)
        self._set_intelligent_ylim(values)
        self.axes.set_ylabel(
            "Montant (GNF)",
            color=self.theme.COLORS["subtext"], fontsize=9, fontweight="500"
        )
        self._finalize()


# =============================================================================
# GRAPHIQUE 3 — Revenu moyen journalier par mois (courbe lissée)
# =============================================================================

class CommandeRevenuMoyenGraph(BaseGraph):
    """Courbe lissée : revenu moyen journalier des commandes par mois."""

    def update_graph(self, stats: dict):
        self._last_stats = stats or {}
        self.axes.clear()
        self._setup_modern_style()

        if not stats:
            self._finalize()
            return

        values = [stats.get(m, 0) for m in self.MONTH_LABELS]
        x      = np.arange(len(self.MONTH_LABELS))
        y      = np.array(values, dtype=float)
        color  = self.theme.COLORS["warning"]

        self._create_smooth_curve(x, y, color)
        self._create_data_points(x, y, color, "Moy. GNF/jour")

        self.axes.set_xticks(x)
        self.axes.set_xticklabels(self.MONTH_LABELS, rotation=0, fontsize=8)
        self.axes.set_xlim(-0.8, len(self.MONTH_LABELS) - 0.2)
        self._set_intelligent_ylim(values)
        self.axes.set_ylabel(
            "Moy. GNF/jour",
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
        self.frame3 = self._create_chart_frame("Revenu moyen journalier par mois (GNF)")
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
            f"color: {c['text_primary']}; border: none; background: transparent;"
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
        for frame, title in [
            (self.frame1, "Nombre de commandes par mois"),
            (self.frame2, "Montant des commandes par mois (GNF)"),
            (self.frame3, "Revenu moyen journalier par mois (GNF)"),
        ]:
            frame.setStyleSheet(f"""
                QFrame#ChartFrame {{
                    background: {c['bg_card']};
                    border: 1px solid {c['border_light']};
                    border-radius: 12px;
                }}
            """)
            lbl = frame.findChild(QLabel, "ChartTitle")
            if lbl:
                lbl.setStyleSheet(
                    f"color: {c['text_primary']}; border: none; background: transparent;"
                )


# Alias de compatibilité (ancienne API utilisée dans vue_commande_lunette)
CommandeLunetteAnalyseGraph = CommandeLunetteChartsSection
