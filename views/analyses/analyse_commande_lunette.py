# """
# Analyse commandes lunettes:
# - Graphe 1 : nombre de commandes par mois (barres verticales) + moyenne journaliere
# - Graphe 2 : montant des commandes par mois (barres verticales) + moyenne journaliere
# - 4 cards KPI
# - 3 jauges : taux livraison, taux recouvrement, ponctualite livraison
# - Panneau detail hebdomadaire
# """

# import calendar
# from datetime import datetime
# import numpy as np
# from scipy.interpolate import make_interp_spline
# import mplcursors
# from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.figure import Figure
# from matplotlib.ticker import MaxNLocator, FuncFormatter
# from matplotlib.patches import Wedge, Circle

# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout, QLabel,
#     QFrame, QGraphicsDropShadowEffect, QComboBox, QSizePolicy
# )
# from PySide6.QtCore import QSize, Qt
# from PySide6.QtGui import QColor
# import qtawesome as qta
# from views.shared.theme_manager import theme_manager


# # =============================================================================
# # DESCRIPTEUR COULEUR THEMATIQUE
# # =============================================================================

# class _TC:
#     """Descripteur de couleur thématique pour graphiques."""
#     def __init__(self, key):
#         self._key = key

#     def __set_name__(self, owner, name):
#         self._name = name

#     def __get__(self, obj, objtype=None):
#         return theme_manager.colors()[self._key]


# # =============================================================================
# # THEME
# # =============================================================================

# class ModernTheme:
#     primary = _TC('primary')
#     success = _TC('success')
#     warning = _TC('warning')
#     danger  = _TC('danger')
#     info    = _TC('info')
#     accent  = _TC('accent')
#     blue    = _TC('info')
#     text    = _TC('text_primary')
#     subtext = _TC('text_secondary')
#     surface = _TC('bg_card')
#     border  = _TC('border')

#     @property
#     def COLORS(self):
#         return {
#             "primary": self.primary,
#             "success": self.success,
#             "warning": self.warning,
#             "danger":  self.danger,
#             "info":    self.info,
#             "accent":  self.accent,
#             "blue":    self.blue,
#             "text":    self.text,
#             "subtext": self.subtext,
#             "surface": self.surface,
#             "border":  self.border,
#         }


# # =============================================================================
# # GRAPHE DE BASE
# # =============================================================================

# class BaseGraph(FigureCanvas):
#     MONTH_LABELS = [
#         "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
#         "Juil", "Août", "Sep", "Oct", "Nov", "Déc",
#     ]

#     def __init__(self, parent=None, width=5, height=4, dpi=100):
#         self.theme = ModernTheme()
#         self.fig   = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
#         self.axes  = self.fig.add_subplot(111)
#         self.axes.set_facecolor("none")
#         super().__init__(self.fig)
#         self.setParent(parent)
#         self.setStyleSheet("background: transparent;")
#         self.cursors     = []
#         self._annotations = []
#         self._setup_style()
#         self.mpl_connect("figure_leave_event", self._on_figure_leave)

#     def _on_figure_leave(self, event):
#         for ann in self._annotations:
#             try:
#                 ann.set_visible(False)
#             except Exception:
#                 pass
#         self.draw_idle()

#     def _setup_style(self):
#         for spine in self.axes.spines.values():
#             spine.set_visible(False)
#         self.axes.grid(
#             True, axis="y", linestyle="-", alpha=0.1,
#             color=self.theme.COLORS["border"], linewidth=0.8,
#         )
#         self.axes.tick_params(
#             colors=self.theme.COLORS["subtext"], labelsize=9, length=0, pad=8
#         )
#         self.fig.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.15)

#     # ------------------------------------------------------------------
#     # Barres verticales avec hover
#     # ------------------------------------------------------------------

#     def _draw_bars(self, x, y, color, label, alpha=0.78, width=0.55):
#         """Dessine des barres verticales avec tooltip au survol."""
#         bars = self.axes.bar(
#             x, y,
#             width=width,
#             color=color,
#             alpha=alpha,
#             label=label,
#             zorder=5,
#             linewidth=0,
#         )
#         cur = mplcursors.cursor(bars, hover=True)
#         cur.connect("add", lambda sel, lbl=label: self._on_bar_hover(sel, lbl))
#         self.cursors.append(cur)
#         return bars

#     def _on_bar_hover(self, sel, label):
#         """Tooltip adapté aux barres : utilise l'index de la barre."""
#         try:
#             idx = sel.index
#         except AttributeError:
#             idx = int(round(sel.target[0]))
#         val = sel.target[1]
#         month = self.MONTH_LABELS[idx] if 0 <= idx < len(self.MONTH_LABELS) else ""
#         if abs(val - round(val)) < 1e-6:
#             value_txt = f"{int(round(val)):,}".replace(",", " ")
#         else:
#             value_txt = f"{val:,.2f}".replace(",", " ")
#         sel.annotation.set_text(f"{month}\n{label}: {value_txt}")
#         sel.annotation.get_bbox_patch().set(
#             fc=self.theme.COLORS["surface"],
#             ec=self.theme.COLORS["border"],
#             boxstyle="round,pad=0.5",
#             alpha=0.95, linewidth=1,
#         )
#         sel.annotation.set_color(self.theme.COLORS["text"])
#         sel.annotation.set_fontsize(9)
#         sel.annotation.set_fontweight("500")
#         sel.annotation.arrow_patch.set_visible(False)
#         if sel.annotation not in self._annotations:
#             self._annotations.append(sel.annotation)

#     # ------------------------------------------------------------------
#     # Courbe lisse (pour les moyennes sur axe secondaire)
#     # ------------------------------------------------------------------

#     def _draw_smooth_curve(self, x, y, color, label, linestyle="--", alpha=0.9, ax=None):
#         target = ax or self.axes
#         if len(y) < 2 or float(np.sum(y)) == 0.0:
#             return
#         x_s = np.linspace(x.min(), x.max(), 300)
#         y_s = np.maximum(make_interp_spline(x, y, k=min(3, len(y) - 1))(x_s), 0)
#         src_max = float(np.max(y)) if len(y) else 0.0
#         if src_max > 0:
#             y_s = np.clip(y_s, 0, src_max * 1.05)
#         target.plot(
#             x_s, y_s, color=color, linewidth=2.2,
#             linestyle=linestyle, label=label, alpha=alpha, antialiased=True,
#         )

#     def _draw_points(self, x, y, color, tooltip_label, ax=None):
#         target = ax or self.axes
#         sc = target.scatter(
#             x, y,
#             color=self.theme.COLORS["surface"],
#             edgecolor=color,
#             s=48, zorder=10, linewidth=2, alpha=0.95,
#         )
#         cur = mplcursors.cursor(sc, hover=True)
#         cur.connect("add", lambda sel, lbl=tooltip_label: self._on_hover(sel, lbl))
#         self.cursors.append(cur)

#     def _on_hover(self, sel, label):
#         idx = int(round(sel.target[0]))
#         val = sel.target[1]
#         month = self.MONTH_LABELS[idx] if 0 <= idx < len(self.MONTH_LABELS) else ""
#         if abs(val - round(val)) < 1e-6:
#             value_txt = f"{int(round(val)):,}".replace(",", " ")
#         else:
#             value_txt = f"{val:,.2f}".replace(",", " ")
#         sel.annotation.set_text(f"{month}\n{label}: {value_txt}")
#         sel.annotation.get_bbox_patch().set(
#             fc=self.theme.COLORS["surface"],
#             ec=self.theme.COLORS["border"],
#             boxstyle="round,pad=0.5",
#             alpha=0.95, linewidth=1,
#         )
#         sel.annotation.set_color(self.theme.COLORS["text"])
#         sel.annotation.set_fontsize(9)
#         sel.annotation.set_fontweight("500")
#         sel.annotation.arrow_patch.set_visible(False)
#         if sel.annotation not in self._annotations:
#             self._annotations.append(sel.annotation)

#     # ------------------------------------------------------------------
#     # Axes & echelles
#     # ------------------------------------------------------------------

#     def _set_x_axis(self, x):
#         self.axes.set_xticks(x)
#         self.axes.set_xticklabels(self.MONTH_LABELS, rotation=0)

#     def _nice_upper_bound(self, value: float, min_upper: float) -> float:
#         if value <= 0:
#             return float(min_upper)
#         magnitude  = 10 ** np.floor(np.log10(value))
#         normalized = value / magnitude
#         if normalized <= 1:
#             nice = 1
#         elif normalized <= 2:
#             nice = 2
#         elif normalized <= 5:
#             nice = 5
#         else:
#             nice = 10
#         return max(float(nice * magnitude), float(min_upper))

#     def _set_ylim_counts(self, *value_lists):
#         all_vals = [float(v) for lst in value_lists for v in lst if v > 0]
#         max_val  = max(all_vals) if all_vals else 0.0
#         upper    = self._nice_upper_bound(max_val * 1.20, min_upper=20.0)
#         self.axes.set_ylim(0, upper)
#         self.axes.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

#     def _set_ylim_amounts(self, *value_lists):
#         all_vals = [float(v) for lst in value_lists for v in lst if v > 0]
#         max_val  = max(all_vals) if all_vals else 0.0
#         upper    = self._nice_upper_bound(max_val * 1.20, min_upper=1000.0)
#         self.axes.set_ylim(0, upper)
#         self.axes.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

#     def _finalize(self):
#         self.fig.tight_layout()
#         self.draw()

#     def _style_legend(self, ax=None):
#         target = ax or self.axes
#         leg = target.get_legend()
#         if leg is None:
#             return
#         leg.get_frame().set_facecolor("none")
#         leg.get_frame().set_edgecolor("none")
#         leg.get_frame().set_alpha(0)
#         for txt in leg.get_texts():
#             txt.set_color(self.theme.COLORS["subtext"])
#             txt.set_fontsize(7)
#             txt.set_fontweight("600")


# # =============================================================================
# # GRAPHE 1 — NOMBRE DE COMMANDES PAR MOIS (BARRES + MOYENNE SECONDAIRE)
# # =============================================================================

# class CommandeNombreGraph(BaseGraph):

#     def update_graph(self, nombre_par_mois: dict, moyenne_par_mois: dict):
#         # Nettoie l'axe secondaire precedent si existant
#         if hasattr(self, "avg_axis") and self.avg_axis is not None:
#             try:
#                 self.avg_axis.remove()
#             except Exception:
#                 pass
#             self.avg_axis = None

#         self.axes.clear()
#         self._setup_style()

#         x     = np.arange(len(self.MONTH_LABELS))
#         y_nb  = np.array([nombre_par_mois.get(m, 0)  for m in self.MONTH_LABELS], dtype=float)
#         y_avg = np.array([moyenne_par_mois.get(m, 0)  for m in self.MONTH_LABELS], dtype=float)

#         # Barres principales (nombre de commandes)
#         self._draw_bars(x, y_nb, self.theme.COLORS["primary"], "Nb commandes")

#         # Axe secondaire pour la moyenne journaliere
#         self.avg_axis = self.axes.twinx()
#         for spine_name, spine in self.avg_axis.spines.items():
#             spine.set_visible(spine_name == "right")
#         self.avg_axis.spines["right"].set_color(self.theme.COLORS["border"])
#         self.avg_axis.spines["right"].set_linewidth(0.8)
#         self.avg_axis.grid(False)
#         self.avg_axis.tick_params(
#             colors=self.theme.COLORS["blue"], labelsize=8, length=0, pad=6
#         )
#         self.avg_axis.set_ylabel(
#             "Moyenne / jour", color=self.theme.COLORS["blue"], fontsize=9, fontweight="500"
#         )

#         if len(y_avg) >= 2 and float(np.sum(y_avg)) > 0.0:
#             self._draw_smooth_curve(
#                 x, y_avg,
#                 color=self.theme.COLORS["blue"],
#                 label="Moyenne journaliere",
#                 linestyle="--",
#                 ax=self.avg_axis,
#             )
#             self._draw_points(x, y_avg, self.theme.COLORS["blue"], "Moy. journaliere", ax=self.avg_axis)

#         self._set_x_axis(x)
#         self._set_ylim_counts(y_nb.tolist())

#         avg_vals  = [float(v) for v in y_avg.tolist() if v > 0]
#         avg_max   = max(avg_vals) if avg_vals else 0.0
#         avg_upper = self._nice_upper_bound(avg_max * 1.15, min_upper=1.0)
#         self.avg_axis.set_ylim(0, avg_upper)
#         self.avg_axis.yaxis.set_major_locator(MaxNLocator(nbins=5))

#         self.axes.set_ylabel(
#             "Commandes lunettes", color=self.theme.COLORS["subtext"], fontsize=10, fontweight="500"
#         )
#         h1, l1 = self.axes.get_legend_handles_labels()
#         h2, l2 = self.avg_axis.get_legend_handles_labels()
#         self.axes.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=7, framealpha=0)
#         self._style_legend()
#         self._finalize()


# # =============================================================================
# # GRAPHE 2 — MONTANT DES COMMANDES PAR MOIS (BARRES + MOYENNE SECONDAIRE)
# # =============================================================================

# class CommandeMontantGraph(BaseGraph):

#     def update_graph(self, montant_par_mois: dict, moyenne_par_mois: dict):
#         if hasattr(self, "avg_axis") and self.avg_axis is not None:
#             try:
#                 self.avg_axis.remove()
#             except Exception:
#                 pass
#             self.avg_axis = None

#         self.axes.clear()
#         self._setup_style()

#         x     = np.arange(len(self.MONTH_LABELS))
#         y_tot = np.array([montant_par_mois.get(m, 0) for m in self.MONTH_LABELS], dtype=float)
#         y_avg = np.array([moyenne_par_mois.get(m, 0) for m in self.MONTH_LABELS], dtype=float)

#         # Barres principales (montant total)
#         self._draw_bars(x, y_tot, self.theme.COLORS["accent"], "Montant total")

#         # Axe secondaire pour la moyenne journaliere du montant
#         self.avg_axis = self.axes.twinx()
#         for spine_name, spine in self.avg_axis.spines.items():
#             spine.set_visible(spine_name == "right")
#         self.avg_axis.spines["right"].set_color(self.theme.COLORS["border"])
#         self.avg_axis.spines["right"].set_linewidth(0.8)
#         self.avg_axis.grid(False)
#         self.avg_axis.tick_params(
#             colors=self.theme.COLORS["warning"], labelsize=8, length=0, pad=6
#         )
#         self.avg_axis.set_ylabel(
#             "Moyenne / jour (GNF)", color=self.theme.COLORS["warning"], fontsize=9, fontweight="500"
#         )

#         if len(y_avg) >= 2 and float(np.sum(y_avg)) > 0.0:
#             self._draw_smooth_curve(
#                 x, y_avg,
#                 color=self.theme.COLORS["warning"],
#                 label="Moyenne journaliere",
#                 linestyle="--",
#                 ax=self.avg_axis,
#             )
#             self._draw_points(x, y_avg, self.theme.COLORS["warning"], "Moy. journaliere", ax=self.avg_axis)

#         self._set_x_axis(x)
#         self._set_ylim_amounts(y_tot.tolist())

#         avg_vals  = [float(v) for v in y_avg.tolist() if v > 0]
#         avg_max   = max(avg_vals) if avg_vals else 0.0
#         avg_upper = self._nice_upper_bound(avg_max * 1.15, min_upper=1000.0)
#         self.avg_axis.set_ylim(0, avg_upper)
#         self.avg_axis.yaxis.set_major_locator(MaxNLocator(nbins=5))
#         self.avg_axis.yaxis.set_major_formatter(
#             FuncFormatter(lambda v, _: f"{int(v):,}".replace(",", " "))
#         )

#         self.axes.set_ylabel(
#             "Montant (GNF)", color=self.theme.COLORS["subtext"], fontsize=10, fontweight="500"
#         )
#         self.axes.yaxis.set_major_formatter(
#             FuncFormatter(lambda v, _: f"{int(v):,}".replace(",", " "))
#         )
#         h1, l1 = self.axes.get_legend_handles_labels()
#         h2, l2 = self.avg_axis.get_legend_handles_labels()
#         self.axes.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=7, framealpha=0)
#         self._style_legend()
#         self._finalize()


# # =============================================================================
# # JAUGE SEMI-CIRCULAIRE (identique a analyse_consultation)
# # =============================================================================

# class SemiCircleGauge(FigureCanvas):
#     def __init__(self, label: str, parent=None, width=1.9, height=1.9, dpi=100):
#         self.label = label
#         self.theme = ModernTheme()
#         self.fig   = Figure(figsize=(width, height), dpi=dpi, facecolor="none")
#         self.axes  = self.fig.add_subplot(111)
#         self.axes.set_facecolor("none")
#         super().__init__(self.fig)
#         self.setParent(parent)
#         self.setStyleSheet("background: transparent;")
#         self.update_value(0.0)

#     def _color_for_percent(self, percent: float) -> str:
#         c = theme_manager.colors()
#         if percent < 35:
#             return c['danger']
#         if percent < 70:
#             return c['warning']
#         return c['success']

#     def update_value(self, percent):
#         try:
#             p = float(percent)
#         except Exception:
#             p = 0.0
#         if 0 < p <= 1:
#             p = p * 100.0
#         p = max(0.0, min(100.0, p))

#         color = self._color_for_percent(p)
#         self.axes.clear()
#         self.axes.set_facecolor("none")
#         self.axes.axis("off")

#         # Piste de fond
#         self.axes.add_patch(
#             Wedge((0, 0), 1.0, 0, 360, width=0.24,
#                   facecolor=theme_manager.color('border'), edgecolor="none")
#         )
#         # Arc de progression
#         angle = 360.0 * (p / 100.0)
#         if p > 0:
#             self.axes.add_patch(
#                 Wedge((0, 0), 1.0, 90.0, 90.0 + angle, width=0.24,
#                       facecolor=color, edgecolor="none")
#             )
#             theta   = np.deg2rad(90.0 + angle)
#             mx, my  = 0.88 * np.cos(theta), 0.88 * np.sin(theta)
#             self.axes.add_patch(
#                 Circle((mx, my), 0.09, facecolor=color,
#                        edgecolor=theme_manager.color('text_inverse'), linewidth=1.0)
#             )

#         self.axes.text(0, 0.02, f"{p:.0f}%",
#                        ha="center", va="center",
#                        fontsize=12, fontweight="bold",
#                        color=self.theme.COLORS["subtext"])
#         self.axes.text(0, -1.18, self.label,
#                        ha="center", va="center",
#                        fontsize=9, color=self.theme.COLORS["subtext"])
#         self.axes.set_xlim(-1.25, 1.25)
#         self.axes.set_ylim(-1.28, 1.2)
#         self.fig.tight_layout(pad=0.2)
#         self.draw()


# # =============================================================================
# # KPI CARD (identique a analyse_consultation)
# # =============================================================================

# class KPICard(QFrame):
#     def __init__(self, titre: str, valeur: str, icone: str,
#                  couleur: str, unite: str = "", parent=None):
#         super().__init__(parent)
#         self._icone   = icone
#         self._couleur = couleur
#         self._build(titre, valeur, icone, couleur, unite)

#     def _build(self, titre, valeur, icone, couleur, unite):
#         self.setMaximumHeight(80)
#         self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
#         self.setStyleSheet(
#             f"QFrame {{ background-color: {theme_manager.color('bg_card')}; "
#             f"border-radius: 12px; border: 1px solid {theme_manager.color('border')}; }}"
#         )
#         shadow = QGraphicsDropShadowEffect()
#         shadow.setBlurRadius(10)
#         shadow.setOffset(0, 2)
#         shadow.setColor(QColor(0, 0, 0, 20))
#         self.setGraphicsEffect(shadow)

#         layout = QVBoxLayout(self)
#         layout.setContentsMargins(15, 10, 15, 10)
#         layout.setSpacing(4)

#         hdr = QHBoxLayout()
#         self._ico = QLabel()
#         self._ico.setPixmap(qta.icon(icone, color=couleur).pixmap(QSize(22, 22)))
#         self._ico.setStyleSheet("border:none;")
#         self._ttl = QLabel(titre)
#         self._ttl.setStyleSheet(
#             f"color:{theme_manager.color('text_secondary')}; font-size:11px; font-weight:600; border:none;"
#         )
#         hdr.addWidget(self._ico)
#         hdr.addSpacing(6)
#         hdr.addWidget(self._ttl)
#         hdr.addStretch()
#         layout.addLayout(hdr)

#         self._val_lbl = QLabel(valeur)
#         self._val_lbl.setStyleSheet(
#             f"color:{couleur}; font-size:24px; font-weight:bold; border:none;"
#         )
#         layout.addWidget(self._val_lbl)

#         self._unite_lbl = None
#         if unite:
#             self._unite_lbl = QLabel(unite)
#             self._unite_lbl.setStyleSheet(
#                 f"color:{theme_manager.color('text_muted')}; font-size:10px; border:none;"
#             )
#             layout.addWidget(self._unite_lbl)
#         layout.addStretch()

#     def apply_theme(self, couleur: str = None):
#         if couleur:
#             self._couleur = couleur
#         c = self._couleur
#         self.setStyleSheet(
#             f"QFrame {{ background-color: {theme_manager.color('bg_card')}; "
#             f"border-radius: 12px; border: 1px solid {theme_manager.color('border')}; }}"
#         )
#         self._ico.setPixmap(qta.icon(self._icone, color=c).pixmap(QSize(22, 22)))
#         self._ttl.setStyleSheet(
#             f"color:{theme_manager.color('text_secondary')}; font-size:11px; font-weight:600; border:none;"
#         )
#         self._val_lbl.setStyleSheet(
#             f"color:{c}; font-size:24px; font-weight:bold; border:none;"
#         )
#         if self._unite_lbl:
#             self._unite_lbl.setStyleSheet(
#                 f"color:{theme_manager.color('text_muted')}; font-size:10px; border:none;"
#             )

#     def update_value(self, v: str):
#         self._val_lbl.setText(v)


# # =============================================================================
# # GRAPH FRAME (identique a analyse_consultation)
# # =============================================================================

# class GraphFrame(QFrame):
#     def __init__(self, titre: str, icone: str, parent=None):
#         super().__init__(parent)
#         self._icone = icone
#         self.setStyleSheet(
#             f"QFrame {{ background-color: {theme_manager.color('bg_card')}; "
#             f"border-radius: 18px; border: 1px solid {theme_manager.color('border')}; }}"
#         )
#         shadow = QGraphicsDropShadowEffect()
#         shadow.setBlurRadius(15)
#         shadow.setOffset(0, 4)
#         shadow.setColor(QColor(0, 0, 0, 30))
#         self.setGraphicsEffect(shadow)

#         root = QVBoxLayout(self)
#         root.setContentsMargins(12, 12, 12, 12)
#         root.setSpacing(8)

#         hdr = QHBoxLayout()
#         self._ico = QLabel()
#         self._ico.setPixmap(
#             qta.icon(icone, color=theme_manager.color('primary')).pixmap(QSize(18, 18))
#         )
#         self._ico.setStyleSheet("border:none;")
#         self._ttl = QLabel(titre)
#         self._ttl.setStyleSheet(
#             f"font-weight:bold; color:{theme_manager.color('text_primary')}; "
#             f"font-size:13px; border:none;"
#         )
#         hdr.addWidget(self._ico)
#         hdr.addSpacing(6)
#         hdr.addWidget(self._ttl)
#         hdr.addStretch()
#         root.addLayout(hdr)

#         self._sep = QFrame()
#         self._sep.setFixedHeight(1)
#         self._sep.setStyleSheet(f"background:{theme_manager.color('border')}; border:none;")
#         root.addWidget(self._sep)

#         self.graph_layout = QVBoxLayout()
#         self.graph_layout.setContentsMargins(0, 0, 0, 0)
#         root.addLayout(self.graph_layout, 1)

#     def apply_theme(self):
#         self.setStyleSheet(
#             f"QFrame {{ background-color: {theme_manager.color('bg_card')}; "
#             f"border-radius: 18px; border: 1px solid {theme_manager.color('border')}; }}"
#         )
#         self._ico.setPixmap(
#             qta.icon(self._icone, color=theme_manager.color('primary')).pixmap(QSize(18, 18))
#         )
#         self._ttl.setStyleSheet(
#             f"font-weight:bold; color:{theme_manager.color('text_primary')}; "
#             f"font-size:13px; border:none;"
#         )
#         self._sep.setStyleSheet(f"background:{theme_manager.color('border')}; border:none;")


# # =============================================================================
# # LIGNE DETAIL JOURNALIER (identique a analyse_consultation)
# # =============================================================================

# class DayStatRow(QFrame):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self._accent = theme_manager.color('accent')
#         self.setStyleSheet("QFrame { background: transparent; border: none; }")
#         self.setFixedHeight(16)
#         layout = QHBoxLayout(self)
#         layout.setContentsMargins(1, 0, 1, 0)
#         layout.setSpacing(3)

#         self.lbl_icon   = QLabel()
#         self.lbl_icon.setFixedSize(10, 10)
#         self.lbl_icon.setAlignment(Qt.AlignCenter)
#         self.lbl_jour   = QLabel("--")
#         self.lbl_jour.setStyleSheet(
#             f"color:{theme_manager.color('text_secondary')}; font-size:8px; font-weight:600; border:none;"
#         )
#         self.lbl_nombre = QLabel("0 commandes")
#         self.lbl_nombre.setStyleSheet(
#             f"color:{theme_manager.color('text_secondary')}; font-size:8px; font-weight:600; border:none;"
#         )
#         self.lbl_montant = QLabel("0 GNF")
#         self.lbl_montant.setStyleSheet(
#             f"color:{theme_manager.color('text_primary')}; font-size:8px; font-weight:700; border:none;"
#         )

#         left = QHBoxLayout()
#         left.setContentsMargins(0, 0, 0, 0)
#         left.setSpacing(4)
#         left.addWidget(self.lbl_icon)
#         left.addWidget(self.lbl_jour)

#         layout.addLayout(left)
#         layout.addStretch()
#         layout.addWidget(self.lbl_nombre)
#         layout.addSpacing(3)
#         layout.addWidget(self.lbl_montant)
#         self.set_accent_color(self._accent)

#     def set_accent_color(self, color: str):
#         self._accent = color
#         self.lbl_icon.setStyleSheet(
#             f"background-color:{color}; border-radius:5px; border:none;"
#         )
#         self.lbl_icon.setPixmap(
#             qta.icon("fa5s.calendar-day",
#                      color=theme_manager.color('text_inverse')).pixmap(QSize(6, 6))
#         )

#     def update_values(self, jour_label: str, nombre: int, montant: float, active: bool = True):
#         self.lbl_jour.setText(jour_label)
#         self.lbl_nombre.setText(f"{int(nombre)} commandes")
#         self.lbl_montant.setText(f"{montant:,.0f} GNF".replace(",", " "))

#         if active:
#             self.setStyleSheet("QFrame { background: transparent; border: none; }")
#             self.lbl_icon.show()
#             self.lbl_jour.setStyleSheet(
#                 f"color:{theme_manager.color('text_secondary')}; font-size:8px; font-weight:600; border:none;"
#             )
#             self.lbl_nombre.setStyleSheet(
#                 f"color:{theme_manager.color('text_secondary')}; font-size:8px; font-weight:600; border:none;"
#             )
#             self.lbl_montant.setStyleSheet(
#                 f"color:{theme_manager.color('text_primary')}; font-size:8px; font-weight:700; border:none;"
#             )
#         else:
#             self.setStyleSheet("QFrame { background: transparent; border: none; }")
#             self.lbl_icon.hide()
#             self.lbl_jour.setStyleSheet(
#                 f"color:{theme_manager.color('text_muted')}; font-size:8px; font-weight:600; border:none;"
#             )
#             self.lbl_nombre.setStyleSheet(
#                 f"color:{theme_manager.color('text_muted')}; font-size:8px; font-weight:600; border:none;"
#             )
#             self.lbl_montant.setStyleSheet(
#                 f"color:{theme_manager.color('text_muted')}; font-size:8px; font-weight:700; border:none;"
#             )


# # =============================================================================
# # VUE PRINCIPALE — ANALYSE COMMANDES LUNETTES
# # =============================================================================

# class AnalyseCommandeLunetteView(QWidget):
#     BLEU   = _TC('info')
#     VERT   = _TC('success')
#     VIOLET = _TC('accent')
#     ORANGE = _TC('warning')

#     def __init__(self, controleur, code_session: str, parent=None):
#         super().__init__(parent)
#         self.controleur   = controleur
#         self.code_session = code_session
#         self._build_ui()
#         self.charger_donnees()
#         theme_manager.theme_changed.connect(self.apply_theme)

#     # ------------------------------------------------------------------
#     # Construction de l'interface
#     # ------------------------------------------------------------------

#     def _build_ui(self):
#         root = QVBoxLayout(self)
#         root.setContentsMargins(0, 0, 0, 0)
#         root.setSpacing(8)
#         self._build_kpi_row(root)
#         self._build_graphs(root)

#     def _build_kpi_row(self, parent):
#         row = QHBoxLayout()
#         row.setSpacing(10)

#         self.card_total_session = KPICard(
#             "Total commandes session", "0",
#             "fa5s.glasses", self.BLEU, "commandes"
#         )
#         self.card_attente_livraison = KPICard(
#             "En attente de livraison", "0",
#             "fa5s.hourglass-half", self.ORANGE, "commandes"
#         )
#         self.card_montant_jour = KPICard(
#             "Montant commandes du jour", "0",
#             "fa5s.money-bill-wave", self.VIOLET, "GNF"
#         )
#         self.card_montant_session = KPICard(
#             "Montant total session", "0",
#             "fa5s.wallet", self.VERT, "GNF"
#         )
#         for card in (
#             self.card_total_session,
#             self.card_attente_livraison,
#             self.card_montant_jour,
#             self.card_montant_session,
#         ):
#             row.addWidget(card)
#         parent.addLayout(row)

#     def _build_graphs(self, parent):
#         from views.analyses.responsive_analyses import AnalyseResponsiveGrid
#         self._resp_grid = AnalyseResponsiveGrid(spacing=10)

#         # ---- Frame graphe nombre ----------------------------------------
#         self.frame_nombre = GraphFrame(
#             "Nombre commandes lunettes par mois + moyenne journaliere",
#             "fa5s.chart-bar"
#         )
#         self.graph_nombre = CommandeNombreGraph(width=3, height=1.6)
#         self.graph_nombre.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.graph_nombre.setMinimumHeight(0)
#         self.frame_nombre.graph_layout.addWidget(self.graph_nombre)

#         # ---- Frame graphe montant ----------------------------------------
#         self.frame_montant = GraphFrame(
#             "Montant commandes lunettes par mois + moyenne journaliere",
#             "fa5s.chart-area"
#         )
#         self.graph_montant = CommandeMontantGraph(width=3, height=1.6)
#         self.graph_montant.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.graph_montant.setMinimumHeight(0)
#         self.frame_montant.graph_layout.addWidget(self.graph_montant)

#         # ---- Frame bas gauche — jauges livraison / recouvrement ----------
#         self.frame_bas_gauche = GraphFrame(
#             "Taux livraison & recouvrement", "fa5s.tachometer-alt"
#         )
#         gauges_container = QWidget()
#         gauges_container.setStyleSheet("background: transparent;")
#         gauges_layout = QHBoxLayout(gauges_container)
#         gauges_layout.setContentsMargins(0, 0, 0, 0)
#         gauges_layout.setSpacing(18)
#         gauges_layout.addStretch()

#         self.gauge_livraison    = SemiCircleGauge("Taux livraison",    width=1.5, height=1.5)
#         self.gauge_recouvrement = SemiCircleGauge("Taux recouvrement", width=1.5, height=1.5)
#         self.gauge_ponctualite  = SemiCircleGauge("Ponctualité",       width=1.5, height=1.5)

#         gauges_layout.addWidget(self.gauge_livraison)
#         gauges_layout.addWidget(self.gauge_recouvrement)
#         gauges_layout.addWidget(self.gauge_ponctualite)
#         gauges_layout.addStretch()

#         self.frame_bas_gauche.graph_layout.addStretch()
#         self.frame_bas_gauche.graph_layout.addWidget(gauges_container, 0, Qt.AlignCenter)
#         self.frame_bas_gauche.graph_layout.addStretch()

#         # ---- Frame bas droite — detail hebdomadaire ----------------------
#         self.frame_bas_droite = GraphFrame(
#             "Détail hebdomadaire des commandes", "fa5s.calendar-alt"
#         )
#         self.frame_bas_droite.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

#         two_col = QHBoxLayout()
#         two_col.setContentsMargins(0, 0, 0, 0)
#         two_col.setSpacing(8)

#         # Colonne gauche : combos + jours
#         left_col = QVBoxLayout()
#         left_col.setContentsMargins(0, 0, 0, 0)
#         left_col.setSpacing(2)

#         combos_row = QHBoxLayout()
#         combos_row.setContentsMargins(0, 0, 0, 0)
#         combos_row.setSpacing(8)

#         self.combo_mois = QComboBox()
#         self.combo_mois.setFixedHeight(22)
#         self.combo_mois.setMinimumWidth(110)
#         self.combo_mois.addItem("Choisir un mois", None)
#         for libelle, num in self._mois_options():
#             self.combo_mois.addItem(libelle, num)
#         self.combo_mois.setCurrentIndex(0)
#         self._apply_combo_mois_style()

#         self.combo_semaine = QComboBox()
#         self.combo_semaine.setFixedHeight(22)
#         self.combo_semaine.setMinimumWidth(140)
#         self.combo_semaine.addItem("Choisir une semaine", None)
#         self.combo_semaine.setEnabled(False)
#         self._apply_week_combo_style(None)

#         combos_row.addWidget(self.combo_mois)
#         combos_row.addWidget(self.combo_semaine)
#         combos_row.addStretch()
#         left_col.addLayout(combos_row)

#         self.lbl_week_hint = QLabel("Sélectionne d'abord le mois puis la semaine")
#         self.lbl_week_hint.setStyleSheet(
#             f"color:{theme_manager.color('text_muted')}; font-size:8px; border:none;"
#         )
#         left_col.addWidget(self.lbl_week_hint)

#         self.days_container = QWidget()
#         self.days_container.setStyleSheet("background: transparent;")
#         self.days_layout = QVBoxLayout(self.days_container)
#         self.days_layout.setContentsMargins(0, 0, 0, 0)
#         self.days_layout.setSpacing(0)
#         self.day_rows = []
#         for _ in range(7):
#             row_w = DayStatRow()
#             self.day_rows.append(row_w)
#             self.days_layout.addWidget(row_w)
#         self.days_container.hide()
#         left_col.addWidget(self.days_container)
#         left_col.addStretch()

#         # Colonne droite : recap annuel
#         right_col = QVBoxLayout()
#         right_col.setContentsMargins(0, 0, 0, 0)
#         right_col.setSpacing(2)

#         _YEAR_DATA = [
#             (2022, "fa5s.calendar", "#6366f1", "—"),
#             (2023, "fa5s.calendar", "#f59e0b", "—"),
#             (2024, "fa5s.calendar", "#10b981", "—"),
#             (2025, "fa5s.calendar", "#3b82f6", "—"),
#             (2026, "fa5s.calendar", "#ef4444", "—"),
#         ]

#         self._year_amt_labels = []
#         for year, icon_name, color, amount in _YEAR_DATA:
#             yr_frame = QFrame()
#             yr_frame.setFixedHeight(22)
#             yr_frame.setStyleSheet(
#                 f"QFrame {{ background: {color}18; border-radius: 6px; border: none; }}"
#             )
#             yr_layout = QHBoxLayout(yr_frame)
#             yr_layout.setContentsMargins(6, 0, 6, 0)
#             yr_layout.setSpacing(4)

#             ico_lbl = QLabel()
#             ico_lbl.setFixedSize(12, 12)
#             ico_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(QSize(12, 12)))
#             ico_lbl.setStyleSheet("border:none; background:transparent;")

#             yr_lbl = QLabel(str(year))
#             yr_lbl.setStyleSheet(
#                 f"color:{color}; font-size:9px; font-weight:700; border:none; background:transparent;"
#             )

#             amt_lbl = QLabel(amount)
#             amt_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#             amt_lbl.setStyleSheet(
#                 f"color:{theme_manager.color('text_primary')}; font-size:8px; "
#                 f"font-weight:600; border:none; background:transparent;"
#             )
#             self._year_amt_labels.append(amt_lbl)

#             yr_layout.addWidget(ico_lbl)
#             yr_layout.addWidget(yr_lbl)
#             yr_layout.addStretch()
#             yr_layout.addWidget(amt_lbl)
#             right_col.addWidget(yr_frame)

#         right_col.addStretch()

#         self._sep_v = QFrame()
#         self._sep_v.setFrameShape(QFrame.VLine)
#         self._sep_v.setFixedWidth(1)
#         self._sep_v.setStyleSheet(
#             f"background:{theme_manager.color('border_light')}; border:none;"
#         )

#         two_col.addLayout(left_col, stretch=3)
#         two_col.addWidget(self._sep_v)
#         two_col.addLayout(right_col, stretch=2)

#         self.frame_bas_droite.graph_layout.addLayout(two_col)

#         # ---- Grille responsive ------------------------------------------
#         self._resp_grid.ajouter_section(
#             [self.frame_nombre, self.frame_montant]
#         )
#         self._resp_grid.ajouter_section(
#             [self.frame_bas_gauche, self.frame_bas_droite], expand_v=False
#         )
#         parent.addWidget(self._resp_grid, 1)

#         # Connexions signaux
#         self.combo_mois.currentIndexChanged.connect(self._on_month_changed)
#         self.combo_semaine.currentIndexChanged.connect(self._on_week_combo_changed)

#     # ------------------------------------------------------------------
#     # Helpers controleur
#     # ------------------------------------------------------------------

#     def _call_ctrl(self, method_names, default=0):
#         for name in method_names:
#             fn = getattr(self.controleur, name, None)
#             if callable(fn):
#                 return fn(self.code_session)
#         return default

#     def _call_ctrl_args(self, method_names, *args, default=0):
#         for name in method_names:
#             fn = getattr(self.controleur, name, None)
#             if callable(fn):
#                 return fn(self.code_session, *args)
#         return default

#     def _extraire_float(self, data: dict, keys, default=0.0) -> float:
#         if not isinstance(data, dict):
#             return float(default)
#         for key in keys:
#             if key in data and data[key] is not None:
#                 try:
#                     return float(data[key])
#                 except Exception:
#                     return float(default)
#         return float(default)

#     # ------------------------------------------------------------------
#     # Combos mois / semaine
#     # ------------------------------------------------------------------

#     def _mois_options(self):
#         return [
#             ("Janvier", 1),  ("Fevrier", 2),   ("Mars", 3),      ("Avril", 4),
#             ("Mai", 5),      ("Juin", 6),       ("Juillet", 7),   ("Aout", 8),
#             ("Septembre", 9),("Octobre", 10),   ("Novembre", 11), ("Decembre", 12),
#         ]

#     def _week_color(self, week_idx: int) -> str:
#         colors = ["#b44cff", "#12b6c9", "#ff7a1a", "#4f67ff"]
#         return colors[week_idx] if 0 <= week_idx < len(colors) else "#64748b"

#     def _apply_combo_mois_style(self):
#         c = theme_manager.colors()
#         self.combo_mois.setStyleSheet(
#             f"QComboBox {{ background:{c['bg_input']}; color:{c['text_primary']}; border:none; "
#             f"border-radius:10px; padding:5px 10px; font-size:11px; font-weight:600; }} "
#             f"QComboBox::drop-down {{ border:none; width:18px; }} "
#             f"QComboBox::down-arrow {{ image:none; }} "
#             f"QComboBox QAbstractItemView {{ border:1px solid {c['border_light']}; "
#             f"border-radius:8px; background:{c['bg_card']}; "
#             f"selection-background-color:{c['hover']}; }}"
#         )

#     def _apply_week_combo_style(self, accent_color: str = None):
#         c = theme_manager.colors()
#         if not accent_color:
#             self.combo_semaine.setStyleSheet(
#                 f"QComboBox {{ background:{c['bg_input']}; color:{c['text_muted']}; border:none; "
#                 f"border-radius:10px; padding:5px 10px; font-size:11px; font-weight:600; }} "
#                 f"QComboBox::drop-down {{ border:none; width:18px; }} "
#                 f"QComboBox::down-arrow {{ image:none; }} "
#                 f"QComboBox QAbstractItemView {{ border:1px solid {c['border_light']}; "
#                 f"border-radius:8px; background:{c['bg_card']}; "
#                 f"selection-background-color:{c['hover']}; }}"
#             )
#             return
#         self.combo_semaine.setStyleSheet(
#             f"QComboBox {{ background:{accent_color}; color:{c['text_inverse']}; border:none; "
#             f"border-radius:10px; padding:5px 10px; font-size:11px; font-weight:700; }} "
#             f"QComboBox::drop-down {{ border:none; width:18px; }} "
#             f"QComboBox::down-arrow {{ image:none; }} "
#             f"QComboBox QAbstractItemView {{ border:1px solid {c['border_light']}; "
#             f"border-radius:8px; background:{c['bg_card']}; "
#             f"selection-background-color:{c['hover']}; color:{c['text_primary']}; }}"
#         )

#     def _get_selected_week_index(self):
#         data = self.combo_semaine.currentData()
#         return int(data) if data is not None else None

#     def _on_month_changed(self, _index):
#         month_data = self.combo_mois.currentData()
#         self.days_container.hide()
#         self.lbl_week_hint.show()
#         self._apply_week_combo_style(None)

#         self.combo_semaine.blockSignals(True)
#         self.combo_semaine.clear()
#         self.combo_semaine.addItem("Choisir une semaine", None)
#         self.combo_semaine.blockSignals(False)

#         if month_data is None:
#             self.combo_semaine.setEnabled(False)
#             return

#         self.combo_semaine.setEnabled(True)
#         self._selected_year           = datetime.now().year
#         self._selected_month          = int(month_data)
#         self._selected_month_last_day = calendar.monthrange(
#             self._selected_year, self._selected_month
#         )[1]

#         self._stats_nombre_jour  = self._call_ctrl_args(
#             ["obtenir_nombre_par_jour"],  self._selected_year, self._selected_month, default={}
#         )
#         self._stats_montant_jour = self._call_ctrl_args(
#             ["obtenir_montant_par_jour"], self._selected_year, self._selected_month, default={}
#         )

#         for i in range(4):
#             start = 1 + (i * 7)
#             if start > self._selected_month_last_day:
#                 break
#             end = min(start + 6, self._selected_month_last_day)
#             self.combo_semaine.addItem(
#                 qta.icon("fa5s.circle", color=self._week_color(i)),
#                 f"Semaine {i + 1} ({start:02d}-{end:02d})",
#                 i
#             )

#     def _on_week_combo_changed(self, index: int):
#         week_idx = self.combo_semaine.currentData()
#         if week_idx is None:
#             self.days_container.hide()
#             self.lbl_week_hint.show()
#             self._apply_week_combo_style(None)
#             return
#         self._apply_week_combo_style(self._week_color(int(week_idx)))
#         self.lbl_week_hint.hide()
#         self.days_container.show()
#         self._afficher_semaine(int(week_idx))

#     def _weekday_fr(self, year: int, month: int, day: int) -> str:
#         names = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
#         return names[datetime(year, month, day).weekday()]

#     def _afficher_semaine(self, week_idx: int):
#         start_day = 1 + (week_idx * 7)
#         accent    = self._week_color(week_idx)
#         for offset in range(7):
#             day_num = start_day + offset
#             row     = self.day_rows[offset]
#             row.set_accent_color(accent)

#             if day_num > self._selected_month_last_day:
#                 row.update_values("--", 0, 0.0, active=False)
#                 continue

#             key     = f"{day_num:02d}"
#             nb      = int(self._stats_nombre_jour.get(key, 0))
#             montant = float(self._stats_montant_jour.get(key, 0.0))
#             label   = f"{self._weekday_fr(self._selected_year, self._selected_month, day_num)} {day_num:02d}"
#             row.update_values(label, nb, montant, active=True)

#     # ------------------------------------------------------------------
#     # Chargement des donnees
#     # ------------------------------------------------------------------

#     def charger_donnees(self):
#         if not self.code_session:
#             return
#         try:
#             # KPI cards
#             total_session       = self._call_ctrl(["obtenir_total_commandes_session"],          default=0)
#             attente_livraison   = self._call_ctrl(["obtenir_commandes_en_attente_livraison"],   default=0)
#             montant_jour        = self._call_ctrl(["obtenir_montant_total_aujourdhui"],         default=0.0)
#             montant_session     = self._call_ctrl(["obtenir_montant_total_par_session"],        default=0.0)

#             self.card_total_session.update_value(str(total_session))
#             self.card_attente_livraison.update_value(str(attente_livraison))
#             self.card_montant_jour.update_value(f"{montant_jour:,.0f}")
#             self.card_montant_session.update_value(f"{montant_session:,.0f}")

#             # Graphes
#             nombre_par_mois  = self._call_ctrl(["obtenir_nombre_par_mois"],                         default={})
#             moy_nb_par_mois  = self._call_ctrl(["obtenir_moyenne_nombre_journalier_par_mois"],      default={})
#             montant_par_mois = self._call_ctrl(["obtenir_montant_par_mois"],                        default={})
#             moy_mnt_par_mois = self._call_ctrl(
#                 ["obtenir_moyenne_montant_journalier_par_mois",
#                  "obtenir_moyenne_montant_journlier_par_mois"],
#                 default={}
#             )

#             self.graph_nombre.update_graph(nombre_par_mois,  moy_nb_par_mois)
#             self.graph_montant.update_graph(montant_par_mois, moy_mnt_par_mois)

#             # Jauges livraison / recouvrement / ponctualite
#             delai_data  = self._call_ctrl(["obtenir_delai_moyen_livraison"],          default={})
#             revenu_data = self._call_ctrl(["obtenir_revenu_recouvre_vs_en_attente"],  default={})

#             nb_livrees      = int(self._extraire_float(delai_data,  ["nombre_livrees"]))
#             total_commandes = int(total_session) if total_session else 0
#             revenu_total    = self._extraire_float(revenu_data, ["total"])
#             revenu_recouvre = self._extraire_float(revenu_data, ["recouvre"])

#             # Taux livraison = livrees / total * 100
#             pct_livraison = (nb_livrees / total_commandes * 100.0) if total_commandes > 0 else 0.0

#             # Taux recouvrement = recouvre / total_montant * 100
#             pct_recouvrement = (revenu_recouvre / revenu_total * 100.0) if revenu_total > 0 else 0.0

#             # Ponctualite = (livrees - en_retard) / livrees * 100
#             # On estime en_retard depuis la liste (attente depassee) vs livrees effectuees
#             en_retard_list  = self._call_ctrl(["obtenir_commandes_en_retard"], default=[])
#             nb_en_retard    = len(en_retard_list) if isinstance(en_retard_list, list) else 0
#             base_ponctualite = max(nb_livrees, nb_en_retard)
#             pct_ponctualite = (
#                 (nb_livrees - nb_en_retard) / base_ponctualite * 100.0
#                 if base_ponctualite > 0 else 0.0
#             )
#             pct_ponctualite = max(0.0, min(100.0, pct_ponctualite))

#             self.gauge_livraison.update_value(pct_livraison)
#             self.gauge_recouvrement.update_value(pct_recouvrement)
#             self.gauge_ponctualite.update_value(pct_ponctualite)

#             # Recharge le panneau hebdomadaire si un mois est selectionne
#             if hasattr(self, "combo_mois"):
#                 selected_week = self._get_selected_week_index()
#                 month_data    = self.combo_mois.currentData()
#                 if month_data is None:
#                     self.days_container.hide()
#                     self.lbl_week_hint.show()
#                 else:
#                     self._selected_year           = datetime.now().year
#                     self._selected_month          = int(month_data)
#                     self._selected_month_last_day = calendar.monthrange(
#                         self._selected_year, self._selected_month
#                     )[1]
#                     self._stats_nombre_jour  = self._call_ctrl_args(
#                         ["obtenir_nombre_par_jour"],  self._selected_year,
#                         self._selected_month, default={}
#                     )
#                     self._stats_montant_jour = self._call_ctrl_args(
#                         ["obtenir_montant_par_jour"], self._selected_year,
#                         self._selected_month, default={}
#                     )
#                     if selected_week is not None:
#                         self.days_container.show()
#                         self.lbl_week_hint.hide()
#                         self._afficher_semaine(selected_week)
#                     else:
#                         self.days_container.hide()
#                         self.lbl_week_hint.show()

#         except Exception as e:
#             print(f"[AnalyseCommandeLunetteView] Erreur chargement données: {e}")
#             import traceback
#             traceback.print_exc()

#     # ------------------------------------------------------------------
#     # Theme dynamique
#     # ------------------------------------------------------------------

#     def apply_theme(self):
#         c = theme_manager.colors()
#         self.card_total_session.apply_theme(self.BLEU)
#         self.card_attente_livraison.apply_theme(self.ORANGE)
#         self.card_montant_jour.apply_theme(self.VIOLET)
#         self.card_montant_session.apply_theme(self.VERT)
#         self.frame_nombre.apply_theme()
#         self.frame_montant.apply_theme()
#         self.frame_bas_gauche.apply_theme()
#         self.frame_bas_droite.apply_theme()
#         self._apply_combo_mois_style()
#         week_idx = self._get_selected_week_index()
#         if week_idx is not None:
#             self._apply_week_combo_style(self._week_color(int(week_idx)))
#         else:
#             self._apply_week_combo_style(None)
#         self.lbl_week_hint.setStyleSheet(
#             f"color:{c['text_muted']}; font-size:10px; border:none;"
#         )
#         for lbl in self._year_amt_labels:
#             lbl.setStyleSheet(
#                 f"color:{c['text_primary']}; font-size:10px; font-weight:600; "
#                 f"border:none; background:transparent;"
#             )
#         self._sep_v.setStyleSheet(f"background:{c['border_light']}; border:none;")
#         self.charger_donnees()

#     def rafraichir(self):
#         self.charger_donnees()