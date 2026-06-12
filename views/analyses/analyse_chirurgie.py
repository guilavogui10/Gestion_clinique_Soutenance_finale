# """
# Analyse chirurgie:
# - Graphe 1 : nombre par mois + moyenne journaliere du nombre
# - Graphe 2  : montant par mois + moyenne journaliere du montant
# - 4 cards KPI
# - Frame bas gauche  : Top libellés de chirurgies les plus fréquents
# - Frame bas droite  : Détail hebdomadaire + récap par personnel
# """

# import calendar
# from datetime import datetime

# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout, QLabel,
#     QFrame, QGraphicsDropShadowEffect, QComboBox, QSizePolicy,
# )
# from PySide6.QtCore import QSize, Qt
# from PySide6.QtGui import QColor
# import qtawesome as qta

# from views.shared.theme_manager import theme_manager

# # ── Composants réutilisables importés depuis analyse_consultation ────────────
# # _TC, ModernTheme, KPICard, GraphFrame et BaseGraph sont partagés.
# # Les graphes (barres verticales) sont propres à chirurgie et définis ci-dessous.
# from views.analyses.analyse_consultation import (
#     _TC,
#     ModernTheme,
#     BaseGraph,
#     KPICard,
#     GraphFrame,
# )

# import numpy as np
# from scipy.interpolate import make_interp_spline
# import mplcursors
# from matplotlib.ticker import MaxNLocator, FuncFormatter


# # ============================================================================
# # Graphe 1 : Nombre de chirurgies par mois — barres verticales
# #            + courbe moyenne journalière sur axe secondaire
# # ============================================================================

# class ChirurgieNombreGraph(BaseGraph):
#     """
#     Deux barres verticales côte à côte par mois :
#       - Barre gauche (primary) : nombre total de chirurgies du mois
#       - Barre droite (blue)    : moyenne journalière du nombre
#     """

#     _BAR_WIDTH = 0.38
#     _GAP       = 0.04

#     def update_graph(self, nombre_par_mois: dict, moyenne_par_mois: dict):
#         self.axes.clear()
#         self._setup_style()

#         x     = np.arange(len(self.MONTH_LABELS))
#         y_nb  = np.array([nombre_par_mois.get(m, 0)  for m in self.MONTH_LABELS], dtype=float)
#         y_avg = np.array([moyenne_par_mois.get(m, 0) for m in self.MONTH_LABELS], dtype=float)

#         w    = self._BAR_WIDTH
#         half = w / 2 + self._GAP / 2

#         x_nb  = x - half
#         x_avg = x + half

#         primary_color = self.theme.COLORS["primary"]
#         blue_color    = self.theme.COLORS["blue"]

#         # ── Barres nombre total ───────────────────────────────────────────────
#         bars_nb = self.axes.bar(
#             x_nb, y_nb, width=w,
#             color=primary_color, alpha=0.80, zorder=3,
#             label="Chirurgies / mois", linewidth=0,
#         )

#         # ── Barres moyenne journalière ────────────────────────────────────────
#         bars_avg = self.axes.bar(
#             x_avg, y_avg, width=w,
#             color=blue_color, alpha=0.65, zorder=3,
#             label="Moyenne / jour", linewidth=0,
#         )

#         # ── Labels au-dessus des barres non nulles ────────────────────────────
#         for bar, val in zip(bars_nb, y_nb):
#             if val > 0:
#                 self.axes.text(
#                     bar.get_x() + bar.get_width() / 2, bar.get_height(),
#                     f"{int(val)}",
#                     ha="center", va="bottom",
#                     fontsize=6, fontweight="600", color=primary_color,
#                 )

#         for bar, val in zip(bars_avg, y_avg):
#             if val > 0:
#                 txt = f"{val:.1f}" if val != int(val) else f"{int(val)}"
#                 self.axes.text(
#                     bar.get_x() + bar.get_width() / 2, bar.get_height(),
#                     txt,
#                     ha="center", va="bottom",
#                     fontsize=6, fontweight="600", color=blue_color,
#                 )

#         # ── Tooltips (scatter invisible, juste pour mplcursors) ───────────────
#         sc_nb = self.axes.scatter(
#             x_nb, y_nb,
#             color=self.theme.COLORS["surface"], edgecolor=primary_color,
#             s=28, zorder=10, linewidth=1.5, alpha=0.0,
#         )
#         sc_avg = self.axes.scatter(
#             x_avg, y_avg,
#             color=self.theme.COLORS["surface"], edgecolor=blue_color,
#             s=28, zorder=10, linewidth=1.5, alpha=0.0,
#         )
#         cur_nb  = mplcursors.cursor(sc_nb,  hover=True)
#         cur_avg = mplcursors.cursor(sc_avg, hover=True)
#         cur_nb.connect( "add", lambda sel: self._on_hover(sel, "Chirurgies"))
#         cur_avg.connect("add", lambda sel: self._on_hover(sel, "Moyenne / jour"))
#         self.cursors.extend([cur_nb, cur_avg])

#         # ── Axe X centré sur le groupe de deux barres ─────────────────────────
#         self.axes.set_xticks(x)
#         self.axes.set_xticklabels(self.MONTH_LABELS, rotation=0)
#         self.axes.set_xlim(-0.6, len(self.MONTH_LABELS) - 0.4)

#         self._set_ylim_counts(y_nb.tolist(), y_avg.tolist())
#         self.axes.set_ylabel(
#             "Nombre", color=self.theme.COLORS["subtext"],
#             fontsize=10, fontweight="500",
#         )

#         self.axes.legend(loc="upper left", fontsize=7, framealpha=0)
#         self._style_legend()
#         self._finalize()


# # ============================================================================
# # Graphe 2 : Montant des chirurgies par mois — barres verticales
# #            + courbe moyenne journalière sur le même axe
# # ============================================================================

# class ChirurgieMontantGraph(BaseGraph):
#     """
#     Deux barres verticales côte à côte par mois :
#       - Barre gauche (accent)  : montant total des chirurgies du mois
#       - Barre droite (warning) : moyenne journalière du montant
#     """

#     _BAR_WIDTH = 0.38
#     _GAP       = 0.04

#     def update_graph(self, montant_par_mois: dict, moyenne_par_mois: dict):
#         self.axes.clear()
#         self._setup_style()

#         x     = np.arange(len(self.MONTH_LABELS))
#         y_tot = np.array([montant_par_mois.get(m, 0)  for m in self.MONTH_LABELS], dtype=float)
#         y_avg = np.array([moyenne_par_mois.get(m, 0)  for m in self.MONTH_LABELS], dtype=float)

#         w    = self._BAR_WIDTH
#         half = w / 2 + self._GAP / 2

#         x_tot = x - half
#         x_avg = x + half

#         accent_color  = self.theme.COLORS["accent"]
#         warning_color = self.theme.COLORS["warning"]

#         # ── Barres montant total ──────────────────────────────────────────────
#         bars_tot = self.axes.bar(
#             x_tot, y_tot, width=w,
#             color=accent_color, alpha=0.80, zorder=3,
#             label="Montant total", linewidth=0,
#         )

#         # ── Barres moyenne journalière ────────────────────────────────────────
#         bars_avg = self.axes.bar(
#             x_avg, y_avg, width=w,
#             color=warning_color, alpha=0.65, zorder=3,
#             label="Moyenne / jour", linewidth=0,
#         )

#         # ── Labels au-dessus des barres non nulles ────────────────────────────
#         fmt = lambda v: f"{int(v):,}".replace(",", " ")

#         for bar, val in zip(bars_tot, y_tot):
#             if val > 0:
#                 self.axes.text(
#                     bar.get_x() + bar.get_width() / 2, bar.get_height(),
#                     fmt(val),
#                     ha="center", va="bottom",
#                     fontsize=5, fontweight="600", color=accent_color,
#                 )

#         for bar, val in zip(bars_avg, y_avg):
#             if val > 0:
#                 self.axes.text(
#                     bar.get_x() + bar.get_width() / 2, bar.get_height(),
#                     fmt(val),
#                     ha="center", va="bottom",
#                     fontsize=5, fontweight="600", color=warning_color,
#                 )

#         # ── Tooltips (scatter invisible, juste pour mplcursors) ───────────────
#         sc_tot = self.axes.scatter(
#             x_tot, y_tot,
#             color=self.theme.COLORS["surface"], edgecolor=accent_color,
#             s=28, zorder=10, linewidth=1.5, alpha=0.0,
#         )
#         sc_avg = self.axes.scatter(
#             x_avg, y_avg,
#             color=self.theme.COLORS["surface"], edgecolor=warning_color,
#             s=28, zorder=10, linewidth=1.5, alpha=0.0,
#         )
#         cur_tot = mplcursors.cursor(sc_tot, hover=True)
#         cur_avg = mplcursors.cursor(sc_avg, hover=True)
#         cur_tot.connect("add", lambda sel: self._on_hover(sel, "Montant total"))
#         cur_avg.connect("add", lambda sel: self._on_hover(sel, "Moyenne / jour"))
#         self.cursors.extend([cur_tot, cur_avg])

#         # ── Axe X centré sur le groupe de deux barres ─────────────────────────
#         self.axes.set_xticks(x)
#         self.axes.set_xticklabels(self.MONTH_LABELS, rotation=0)
#         self.axes.set_xlim(-0.6, len(self.MONTH_LABELS) - 0.4)

#         self._set_ylim_amounts(y_tot.tolist(), y_avg.tolist())
#         self.axes.set_ylabel(
#             "Montant (GNF)", color=self.theme.COLORS["subtext"],
#             fontsize=10, fontweight="500",
#         )
#         self.axes.yaxis.set_major_formatter(
#             FuncFormatter(lambda v, _: f"{int(v):,}".replace(",", " "))
#         )

#         self.axes.legend(loc="upper left", fontsize=7, framealpha=0)
#         self._style_legend()
#         self._finalize()


# # ============================================================================
# # Widget : Ligne journalière — libellé « chirurgies » au lieu de «consultations»
# # ============================================================================

# class ChirurgieDayStatRow(QFrame):
#     """Ligne de statistique journalière adaptée aux chirurgies."""

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self._accent = theme_manager.color('accent')
#         self.setStyleSheet("QFrame { background: transparent; border: none; }")
#         self.setFixedHeight(16)

#         layout = QHBoxLayout(self)
#         layout.setContentsMargins(1, 0, 1, 0)
#         layout.setSpacing(3)

#         self.lbl_icon = QLabel()
#         self.lbl_icon.setFixedSize(10, 10)
#         self.lbl_icon.setAlignment(Qt.AlignCenter)

#         self.lbl_jour = QLabel("--")
#         self.lbl_jour.setStyleSheet(
#             f"color:{theme_manager.color('text_secondary')}; font-size:8px; font-weight:600; border:none;"
#         )
#         self.lbl_nombre = QLabel("0 chirurgies")
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

#     def update_values(self, jour_label: str, nombre: int, montant: float,
#                       active: bool = True):
#         self.lbl_jour.setText(jour_label)
#         plural = "s" if nombre != 1 else ""
#         self.lbl_nombre.setText(f"{int(nombre)} chirurgie{plural}")
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
#             for lbl in (self.lbl_jour, self.lbl_nombre, self.lbl_montant):
#                 lbl.setStyleSheet(
#                     f"color:{theme_manager.color('text_muted')}; font-size:8px; font-weight:600; border:none;"
#                 )


# # ============================================================================
# # Widget : Top libellés de chirurgies
# # ============================================================================

# class TopLibellesWidget(QWidget):
#     """
#     Affiche les libellés de chirurgies les plus fréquents sous forme
#     de liste colorée avec badge de comptage.
#     Remplace les jauges demi-cercle (spécifiques à la consultation).
#     """

#     _PALETTE = [
#         "#6366f1", "#f59e0b", "#10b981",
#         "#3b82f6", "#ef4444", "#8b5cf6",
#         "#ec4899", "#14b8a6",
#     ]

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setStyleSheet("background: transparent;")

#         self._root = QVBoxLayout(self)
#         self._root.setContentsMargins(4, 4, 4, 4)
#         self._root.setSpacing(4)

#         self._placeholder = QLabel("Aucune donnée disponible")
#         self._placeholder.setAlignment(Qt.AlignCenter)
#         self._placeholder.setStyleSheet(
#             f"color:{theme_manager.color('text_muted')}; font-size:10px; border:none;"
#         )
#         self._root.addStretch()
#         self._root.addWidget(self._placeholder)
#         self._root.addStretch()

#         self._item_widgets: list[QWidget] = []

#     # ------------------------------------------------------------------
#     # API publique
#     # ------------------------------------------------------------------

#     def update_data(self, top_libelles: list):
#         """
#         Accepte indifféremment :
#         - list of dict  : [{'libelle_chururgie': ..., 'nombre': ...}, ...]
#         - list of tuple : [(libelle, count), ...]
#         """
#         self._clear_items()

#         items = self._normaliser(top_libelles)
#         if not items:
#             self._placeholder.show()
#             return

#         self._placeholder.hide()
#         max_count = max(c for _, c in items) if items else 1

#         for idx, (libelle, count) in enumerate(items[:8]):
#             color = self._PALETTE[idx % len(self._PALETTE)]
#             row = self._build_row(libelle, count, max_count, color)
#             self._item_widgets.append(row)
#             # Insère avant le dernier stretch
#             self._root.insertWidget(self._root.count() - 1, row)

#     def apply_theme(self):
#         """Recharge les couleurs de thème sur le placeholder."""
#         self._placeholder.setStyleSheet(
#             f"color:{theme_manager.color('text_muted')}; font-size:10px; border:none;"
#         )

#     # ------------------------------------------------------------------
#     # Helpers privés
#     # ------------------------------------------------------------------

#     def _clear_items(self):
#         for w in self._item_widgets:
#             w.setParent(None)
#         self._item_widgets.clear()

#     @staticmethod
#     def _normaliser(raw: list) -> list:
#         items = []
#         for entry in (raw or []):
#             if isinstance(entry, dict):
#                 libelle = (
#                     entry.get("libelle_chururgie")
#                     or entry.get("libelle_chirurgie")
#                     or entry.get("libelle")
#                     or "Inconnu"
#                 )
#                 count = int(entry.get("nombre") or entry.get("count") or 0)
#             elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
#                 libelle, count = str(entry[0]), int(entry[1])
#             else:
#                 continue
#             items.append((str(libelle), count))
#         return items

#     def _build_row(self, libelle: str, count: int,
#                    max_count: int, color: str) -> QWidget:
#         container = QWidget()
#         container.setFixedHeight(24)
#         container.setStyleSheet("background: transparent;")

#         h = QHBoxLayout(container)
#         h.setContentsMargins(2, 2, 2, 2)
#         h.setSpacing(6)

#         # Pastille colorée
#         dot = QLabel()
#         dot.setFixedSize(8, 8)
#         dot.setStyleSheet(
#             f"background:{color}; border-radius:4px; border:none;"
#         )

#         # Libellé tronqué
#         txt = libelle[:24] + ("…" if len(libelle) > 24 else "")
#         lbl = QLabel(txt)
#         lbl.setStyleSheet(
#             f"color:{theme_manager.color('text_primary')}; "
#             f"font-size:9px; font-weight:600; border:none;"
#         )
#         lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

#         # Badge comptage
#         badge = QLabel(str(count))
#         badge.setFixedHeight(16)
#         badge.setAlignment(Qt.AlignCenter)
#         badge.setStyleSheet(
#             f"background:{color}28; color:{color}; font-size:8px; "
#             f"font-weight:700; border-radius:6px; padding:0 6px; border:none;"
#         )

#         h.addWidget(dot, 0, Qt.AlignVCenter)
#         h.addWidget(lbl, 1)
#         h.addWidget(badge, 0, Qt.AlignVCenter)

#         return container


# # ============================================================================
# # Widget : Ligne récap par personnel
# # ============================================================================

# class PersonnelStatRow(QFrame):
#     """
#     Ligne affichant le prénom/nom d'un personnel et son nombre de chirurgies.
#     Utilisée dans le panneau droit du détail hebdomadaire.
#     """

#     _PALETTE = ["#6366f1", "#f59e0b", "#10b981", "#3b82f6", "#ef4444"]

#     def __init__(self, idx: int = 0, parent=None):
#         super().__init__(parent)
#         self._color = self._PALETTE[idx % len(self._PALETTE)]
#         self.setFixedHeight(22)
#         self.setStyleSheet(
#             f"QFrame {{ background:{self._color}18; border-radius:6px; border:none; }}"
#         )

#         layout = QHBoxLayout(self)
#         layout.setContentsMargins(6, 0, 6, 0)
#         layout.setSpacing(4)

#         ico = QLabel()
#         ico.setFixedSize(12, 12)
#         ico.setPixmap(
#             qta.icon("fa5s.user-md", color=self._color).pixmap(QSize(12, 12))
#         )
#         ico.setStyleSheet("border:none; background:transparent;")

#         self.lbl_nom = QLabel("--")
#         self.lbl_nom.setStyleSheet(
#             f"color:{self._color}; font-size:9px; font-weight:700; "
#             f"border:none; background:transparent;"
#         )

#         self.lbl_count = QLabel("0 chir.")
#         self.lbl_count.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#         self.lbl_count.setStyleSheet(
#             f"color:{theme_manager.color('text_primary')}; font-size:8px; "
#             f"font-weight:600; border:none; background:transparent;"
#         )

#         layout.addWidget(ico)
#         layout.addWidget(self.lbl_nom, 1)
#         layout.addWidget(self.lbl_count)

#     def update_values(self, nom: str, count: int):
#         truncated = nom[:20] + ("…" if len(nom) > 20 else "")
#         self.lbl_nom.setText(truncated)
#         plural = "s" if count != 1 else ""
#         self.lbl_count.setText(f"{count} chir.")

#     def apply_theme(self):
#         self.lbl_count.setStyleSheet(
#             f"color:{theme_manager.color('text_primary')}; font-size:8px; "
#             f"font-weight:600; border:none; background:transparent;"
#         )


# # ============================================================================
# # Vue principale : AnalyseChirurgieView
# # ============================================================================

# class AnalyseChirurgieView(QWidget):
#     BLEU   = _TC('info')
#     VERT   = _TC('success')
#     VIOLET = _TC('accent')
#     ORANGE = _TC('warning')

#     # Nombre maximum de lignes personnel affichées
#     _MAX_PERSONNEL = 5
#     # Nombre maximum de libellés affichés
#     _MAX_LIBELLES = 8

#     def __init__(self, controleur, code_session: str, parent=None):
#         super().__init__(parent)
#         self.controleur  = controleur
#         self.code_session = code_session
#         self._build_ui()
#         self.charger_donnees()
#         theme_manager.theme_changed.connect(self.apply_theme)

#     # -------------------------------------------------------------------------
#     # Construction de l'UI
#     # -------------------------------------------------------------------------

#     def _build_ui(self):
#         root = QVBoxLayout(self)
#         root.setContentsMargins(0, 0, 0, 0)
#         root.setSpacing(8)
#         self._build_kpi_row(root)
#         self._build_graphs(root)

#     def _build_kpi_row(self, parent: QVBoxLayout):
#         row = QHBoxLayout()
#         row.setSpacing(10)

#         self.card_nb_jour = KPICard(
#             "Chirurgies du jour", "0",
#             "fa5s.calendar-day", self.BLEU, "chirurgies"
#         )
#         self.card_nb_session = KPICard(
#             "Total chirurgies session", "0",
#             "fa5s.chart-line", self.VERT, "chirurgies"
#         )
#         self.card_montant_jour = KPICard(
#             "Montant chirurgies du jour", "0",
#             "fa5s.money-bill-wave", self.VIOLET, "GNF"
#         )
#         self.card_montant_session = KPICard(
#             "Montant chirurgies session", "0",
#             "fa5s.wallet", self.ORANGE, "GNF"
#         )

#         for card in (
#             self.card_nb_jour,
#             self.card_nb_session,
#             self.card_montant_jour,
#             self.card_montant_session,
#         ):
#             row.addWidget(card)

#         parent.addLayout(row)

#     def _build_graphs(self, parent: QVBoxLayout):
#         from views.analyses.responsive_analyses import AnalyseResponsiveGrid
#         self._resp_grid = AnalyseResponsiveGrid(spacing=10)

#         # ── Graphe 1 : nombre ─────────────────────────────────────────────────
#         self.frame_nombre = GraphFrame(
#             "Nombre de chirurgies par mois + moyenne journalière",
#             "fa5s.chart-line"
#         )
#         self.graph_nombre = ChirurgieNombreGraph(width=3, height=1.6)
#         self.graph_nombre.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.graph_nombre.setMinimumHeight(0)
#         self.frame_nombre.graph_layout.addWidget(self.graph_nombre)

#         # ── Graphe 2 : montant ────────────────────────────────────────────────
#         self.frame_montant = GraphFrame(
#             "Montant des chirurgies par mois + moyenne journalière",
#             "fa5s.chart-area"
#         )
#         self.graph_montant = ChirurgieMontantGraph(width=3, height=1.6)
#         self.graph_montant.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.graph_montant.setMinimumHeight(0)
#         self.frame_montant.graph_layout.addWidget(self.graph_montant)

#         # ── Frame bas gauche : top libellés ───────────────────────────────────
#         self.frame_bas_gauche = GraphFrame(
#             "Top libellés de chirurgies", "fa5s.list-ol"
#         )
#         self.top_libelles_widget = TopLibellesWidget()
#         self.top_libelles_widget.setSizePolicy(
#             QSizePolicy.Expanding, QSizePolicy.Expanding
#         )
#         self.frame_bas_gauche.graph_layout.addWidget(self.top_libelles_widget)

#         # ── Frame bas droite : détail hebdomadaire ────────────────────────────
#         self.frame_bas_droite = GraphFrame(
#             "Détail hebdomadaire des chirurgies", "fa5s.calendar-alt"
#         )
#         self.frame_bas_droite.setSizePolicy(
#             QSizePolicy.Expanding, QSizePolicy.Expanding
#         )

#         two_col = QHBoxLayout()
#         two_col.setContentsMargins(0, 0, 0, 0)
#         two_col.setSpacing(8)

#         # ── Colonne gauche : sélecteurs + jours ───────────────────────────────
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

#         self.day_rows: list[ChirurgieDayStatRow] = []
#         for _ in range(7):
#             row_w = ChirurgieDayStatRow()
#             self.day_rows.append(row_w)
#             self.days_layout.addWidget(row_w)

#         self.days_container.hide()
#         left_col.addWidget(self.days_container)
#         left_col.addStretch()

#         # ── Colonne droite : récap par personnel ──────────────────────────────
#         right_col = QVBoxLayout()
#         right_col.setContentsMargins(0, 0, 0, 0)
#         right_col.setSpacing(4)

#         self._personnel_rows: list[PersonnelStatRow] = []
#         for i in range(self._MAX_PERSONNEL):
#             p_row = PersonnelStatRow(idx=i)
#             p_row.hide()
#             self._personnel_rows.append(p_row)
#             right_col.addWidget(p_row)

#         self._lbl_no_personnel = QLabel("Aucun personnel trouvé")
#         self._lbl_no_personnel.setAlignment(Qt.AlignCenter)
#         self._lbl_no_personnel.setStyleSheet(
#             f"color:{theme_manager.color('text_muted')}; font-size:9px; border:none;"
#         )
#         right_col.addWidget(self._lbl_no_personnel)
#         right_col.addStretch()

#         # ── Séparateur vertical ───────────────────────────────────────────────
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

#         # ── Grille responsive : 2 sections ───────────────────────────────────
#         self._resp_grid.ajouter_section(
#             [self.frame_nombre, self.frame_montant]
#         )
#         self._resp_grid.ajouter_section(
#             [self.frame_bas_gauche, self.frame_bas_droite], expand_v=False
#         )

#         parent.addWidget(self._resp_grid, 1)

#         # Branchement des signaux après construction
#         self.combo_mois.currentIndexChanged.connect(self._on_month_changed)
#         self.combo_semaine.currentIndexChanged.connect(self._on_week_combo_changed)

#     # -------------------------------------------------------------------------
#     # Helpers contrôleur
#     # -------------------------------------------------------------------------

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

#     # -------------------------------------------------------------------------
#     # Helpers UI généraux
#     # -------------------------------------------------------------------------

#     def _mois_options(self):
#         return [
#             ("Janvier", 1), ("Fevrier", 2), ("Mars", 3), ("Avril", 4),
#             ("Mai", 5), ("Juin", 6), ("Juillet", 7), ("Aout", 8),
#             ("Septembre", 9), ("Octobre", 10), ("Novembre", 11), ("Decembre", 12),
#         ]

#     def _week_color(self, week_idx: int) -> str:
#         colors = ["#b44cff", "#12b6c9", "#ff7a1a", "#4f67ff"]
#         return colors[week_idx] if 0 <= week_idx < len(colors) else "#64748b"

#     def _weekday_fr(self, year: int, month: int, day: int) -> str:
#         names = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
#         return names[datetime(year, month, day).weekday()]

#     def _get_selected_week_index(self):
#         data = self.combo_semaine.currentData()
#         return int(data) if data is not None else None

#     # -------------------------------------------------------------------------
#     # Styles combobox
#     # -------------------------------------------------------------------------

#     def _apply_combo_mois_style(self):
#         c = theme_manager.colors()
#         self.combo_mois.setStyleSheet(
#             f"QComboBox {{ background:{c['bg_input']}; color:{c['text_primary']}; "
#             f"border:none; border-radius:10px; padding:5px 10px; "
#             f"font-size:11px; font-weight:600; }} "
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
#                 f"QComboBox {{ background:{c['bg_input']}; color:{c['text_muted']}; "
#                 f"border:none; border-radius:10px; padding:5px 10px; "
#                 f"font-size:11px; font-weight:600; }} "
#                 f"QComboBox::drop-down {{ border:none; width:18px; }} "
#                 f"QComboBox::down-arrow {{ image:none; }} "
#                 f"QComboBox QAbstractItemView {{ border:1px solid {c['border_light']}; "
#                 f"border-radius:8px; background:{c['bg_card']}; "
#                 f"selection-background-color:{c['hover']}; }}"
#             )
#         else:
#             self.combo_semaine.setStyleSheet(
#                 f"QComboBox {{ background:{accent_color}; color:{c['text_inverse']}; "
#                 f"border:none; border-radius:10px; padding:5px 10px; "
#                 f"font-size:11px; font-weight:700; }} "
#                 f"QComboBox::drop-down {{ border:none; width:18px; }} "
#                 f"QComboBox::down-arrow {{ image:none; }} "
#                 f"QComboBox QAbstractItemView {{ border:1px solid {c['border_light']}; "
#                 f"border-radius:8px; background:{c['bg_card']}; "
#                 f"selection-background-color:{c['hover']}; "
#                 f"color:{c['text_primary']}; }}"
#             )

#     # -------------------------------------------------------------------------
#     # Slots : interactions sélecteurs
#     # -------------------------------------------------------------------------

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
#         self._selected_year  = datetime.now().year
#         self._selected_month = int(month_data)
#         self._selected_month_last_day = calendar.monthrange(
#             self._selected_year, self._selected_month
#         )[1]

#         self._stats_nombre_jour  = self._call_ctrl_args(
#             ["obtenir_nombre_par_jour"],
#             self._selected_year, self._selected_month, default={}
#         )
#         self._stats_montant_jour = self._call_ctrl_args(
#             ["obtenir_montant_par_jour"],
#             self._selected_year, self._selected_month, default={}
#         )

#         for i in range(4):
#             start = 1 + (i * 7)
#             if start > self._selected_month_last_day:
#                 break
#             end = min(start + 6, self._selected_month_last_day)
#             self.combo_semaine.addItem(
#                 qta.icon("fa5s.circle", color=self._week_color(i)),
#                 f"Semaine {i + 1} ({start:02d}-{end:02d})",
#                 i,
#             )

#     def _on_week_combo_changed(self, _index):
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
#             label   = (
#                 f"{self._weekday_fr(self._selected_year, self._selected_month, day_num)}"
#                 f" {day_num:02d}"
#             )
#             row.update_values(label, nb, montant, active=True)

#     # -------------------------------------------------------------------------
#     # Mise à jour du panneau personnel
#     # -------------------------------------------------------------------------

#     def _normaliser_personnel(self, raw: list) -> list:
#         """
#         Normalise la réponse de obtenir_chururgies_par_personnel.
#         Accepte : list of dict | list of tuple
#         Retourne : [(nom_affiche, count), ...]
#         """
#         result = []
#         for entry in (raw or []):
#             if isinstance(entry, dict):
#                 nom = (
#                     entry.get("nom_complet")
#                     or entry.get("personnel")
#                     or entry.get("nom")
#                     or entry.get("prenom", "")
#                     or "Inconnu"
#                 )
#                 count = int(entry.get("nombre") or entry.get("count") or 0)
#             elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
#                 nom, count = str(entry[0]), int(entry[1])
#             else:
#                 continue
#             result.append((str(nom), count))
#         return result

#     def _update_personnel_panel(self, personnel_data: list):
#         items = self._normaliser_personnel(personnel_data)[: self._MAX_PERSONNEL]

#         if not items:
#             for row in self._personnel_rows:
#                 row.hide()
#             self._lbl_no_personnel.show()
#             return

#         self._lbl_no_personnel.hide()
#         for i, p_row in enumerate(self._personnel_rows):
#             if i < len(items):
#                 nom, count = items[i]
#                 p_row.update_values(nom, count)
#                 p_row.show()
#             else:
#                 p_row.hide()

#     # -------------------------------------------------------------------------
#     # Chargement des données
#     # -------------------------------------------------------------------------

#     def charger_donnees(self):
#         if not self.code_session:
#             return
#         try:
#             # ── KPI cards ─────────────────────────────────────────────────────
#             nb_jour = self._call_ctrl(
#                 ["obtenir_chururgies_aujourd_hui"], default=0
#             )
#             nb_session = self._call_ctrl(
#                 ["obtenir_total_chururgies_session"], default=0
#             )
#             montant_jour = self._call_ctrl(
#                 ["obtenir_montant_total_aujourdhui"], default=0.0
#             )
#             montant_session = self._call_ctrl(
#                 ["obtenir_montant_total_par_session"], default=0.0
#             )

#             self.card_nb_jour.update_value(str(nb_jour))
#             self.card_nb_session.update_value(str(nb_session))
#             self.card_montant_jour.update_value(f"{montant_jour:,.0f}")
#             self.card_montant_session.update_value(f"{montant_session:,.0f}")

#             # ── Graphe nombre ─────────────────────────────────────────────────
#             nombre_par_mois = self._call_ctrl(
#                 ["obtenir_nombre_par_mois", "obtenir_chururgies_par_mois"], default={}
#             )
#             moy_nb_par_mois = self._call_ctrl(
#                 [
#                     "obtenir_moyenne_nombre_journalier_par_mois",
#                     "obtenir_moyenne_chirurgie_par_mois",
#                 ],
#                 default={},
#             )
#             self.graph_nombre.update_graph(nombre_par_mois, moy_nb_par_mois)

#             # ── Graphe montant ────────────────────────────────────────────────
#             montant_par_mois = self._call_ctrl(
#                 ["obtenir_montant_par_mois"], default={}
#             )
#             moy_montant_par_mois = self._call_ctrl(
#                 [
#                     "obtenir_moyenne_montant_journalier_par_mois",
#                     "obtenir_revenu_moyen_par_mois",
#                 ],
#                 default={},
#             )
#             self.graph_montant.update_graph(montant_par_mois, moy_montant_par_mois)

#             # ── Top libellés ──────────────────────────────────────────────────
#             top_libelles = self._call_ctrl(
#                 ["obtenir_top_libelles"], default=[]
#             )
#             self.top_libelles_widget.update_data(top_libelles)

#             # ── Récap personnel ───────────────────────────────────────────────
#             personnel_data = self._call_ctrl(
#                 ["obtenir_chururgies_par_personnel"], default=[]
#             )
#             self._update_personnel_panel(personnel_data)

#             # ── Recharge panneau hebdomadaire si déjà sélectionné ─────────────
#             if hasattr(self, "combo_mois"):
#                 selected_week = self._get_selected_week_index()
#                 month_data    = self.combo_mois.currentData()

#                 if month_data is None:
#                     self.days_container.hide()
#                     self.lbl_week_hint.show()
#                 else:
#                     self._selected_year  = datetime.now().year
#                     self._selected_month = int(month_data)
#                     self._selected_month_last_day = calendar.monthrange(
#                         self._selected_year, self._selected_month
#                     )[1]
#                     self._stats_nombre_jour = self._call_ctrl_args(
#                         ["obtenir_nombre_par_jour"],
#                         self._selected_year, self._selected_month, default={}
#                     )
#                     self._stats_montant_jour = self._call_ctrl_args(
#                         ["obtenir_montant_par_jour"],
#                         self._selected_year, self._selected_month, default={}
#                     )
#                     if selected_week is not None:
#                         self.days_container.show()
#                         self.lbl_week_hint.hide()
#                         self._afficher_semaine(selected_week)
#                     else:
#                         self.days_container.hide()
#                         self.lbl_week_hint.show()

#         except Exception as e:
#             print(f"[AnalyseChirurgieView] Erreur chargement données: {e}")
#             import traceback
#             traceback.print_exc()

#     # -------------------------------------------------------------------------
#     # Thème
#     # -------------------------------------------------------------------------

#     def apply_theme(self):
#         c = theme_manager.colors()

#         # KPI cards
#         self.card_nb_jour.apply_theme(self.BLEU)
#         self.card_nb_session.apply_theme(self.VERT)
#         self.card_montant_jour.apply_theme(self.VIOLET)
#         self.card_montant_session.apply_theme(self.ORANGE)

#         # Frames graphes
#         self.frame_nombre.apply_theme()
#         self.frame_montant.apply_theme()
#         self.frame_bas_gauche.apply_theme()
#         self.frame_bas_droite.apply_theme()

#         # Top libellés
#         self.top_libelles_widget.apply_theme()

#         # Personnel
#         for p_row in self._personnel_rows:
#             p_row.apply_theme()
#         self._lbl_no_personnel.setStyleSheet(
#             f"color:{c['text_muted']}; font-size:9px; border:none;"
#         )

#         # Combobox
#         self._apply_combo_mois_style()
#         week_idx = self._get_selected_week_index()
#         if week_idx is not None:
#             self._apply_week_combo_style(self._week_color(int(week_idx)))
#         else:
#             self._apply_week_combo_style(None)

#         # Hints et séparateurs
#         self.lbl_week_hint.setStyleSheet(
#             f"color:{c['text_muted']}; font-size:8px; border:none;"
#         )
#         self._sep_v.setStyleSheet(
#             f"background:{c['border_light']}; border:none;"
#         )

#         # Rechargement pour que les graphes prennent les nouvelles couleurs
#         self.charger_donnees()

#     def rafraichir(self):
#         """Point d'entrée externe pour forcer un rechargement complet."""
#         self.charger_donnees()