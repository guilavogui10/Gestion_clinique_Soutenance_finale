"""
Onglet Graphes — Vue globale admin.
4 graphes multi-services avec courbes lissées :
  1. Nombre par mois          (top gauche)
  2. Montant par mois         (top centre)
  3. Moyenne journalière      (top droite)
  4. Nombre par jour          (bas, pleine largeur)
"""
from datetime import datetime

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QSizePolicy, QComboBox
)
from views.shared.theme_manager import theme_manager


# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

MOIS_LABELS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
               "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]

SERVICES = [
    ("Consultation", "#3B82F6"),
    ("Examen",       "#10B981"),
    ("Chirurgie",    "#EF4444"),
    ("Lunette",      "#8B5CF6"),
    ("Prescription", "#F97316"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Frame graphe générique
# ─────────────────────────────────────────────────────────────────────────────

class GraphFrame(QFrame):
    """Conteneur avec titre + canvas matplotlib + légende horizontale."""

    def __init__(self, title: str, icon: str, figsize=(5, 2.8), parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._build(title, icon, figsize)
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def _build(self, title: str, icon: str, figsize):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 6)
        lay.setSpacing(4)

        # En-tête
        hdr = QHBoxLayout()
        hdr.setSpacing(6)
        self._ico = QLabel()
        self._ico.setFixedSize(16, 16)
        self._ico.setAlignment(Qt.AlignCenter)
        self._title = QLabel(title)
        hdr.addWidget(self._ico)
        hdr.addWidget(self._title)
        hdr.addStretch()
        lay.addLayout(hdr)

        # Séparateur
        self._sep = QFrame()
        self._sep.setFixedHeight(1)
        lay.addWidget(self._sep)

        # Canvas matplotlib
        self._fig = Figure(figsize=figsize, dpi=90, facecolor="none")
        self._ax  = self._fig.add_subplot(111)
        self._ax.set_facecolor("none")
        self._canvas = FigureCanvas(self._fig)
        self._canvas.setStyleSheet("background:transparent;")
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay.addWidget(self._canvas, 1)

        self.hover_text = self._fig.text(0.5, 0.95, '', ha='center', va='top', fontweight='bold')
        self._canvas.mpl_connect('motion_notify_event', self._on_hover)
        self._canvas.mpl_connect('axes_leave_event', lambda e: self._clear_hover_text())
        self._canvas.mpl_connect('figure_leave_event', lambda e: self._clear_hover_text())
        self.scatters = []

        # Légende colorée
        self._legend_row = QHBoxLayout()
        self._legend_row.setContentsMargins(0, 0, 0, 0)
        self._legend_row.setSpacing(10)
        self._legend_row.addStretch()
        lay.addLayout(self._legend_row)

        self._icon_name = icon

    def set_legend(self, items: list):
        """items = [(label, color), ...]"""
        while self._legend_row.count() > 1:
            item = self._legend_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for label, color in items:
            dot = QLabel("●")
            dot.setStyleSheet(f"color:{color}; font-size:10px; border:none;")
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"color:{theme_manager.colors()['text_secondary']}; font-size:9px; border:none;"
            )
            self._legend_row.insertWidget(self._legend_row.count() - 1, dot)
            self._legend_row.insertWidget(self._legend_row.count() - 1, lbl)

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QFrame {{
                background:{c['bg_card']};
                border:1px solid {c['border']};
                border-radius:12px;
            }}
        """)
        self._ico.setPixmap(
            qta.icon(self._icon_name, color=c['primary']).pixmap(QSize(12, 12))
        )
        self._title.setStyleSheet(
            f"color:{c['text_primary']}; font-size:11px; font-weight:700; border:none;"
        )
        self._sep.setStyleSheet(f"background:{c['border_light']}; border:none;")

    @property
    def ax(self):
        return self._ax

    @property
    def fig(self):
        return self._fig

    def draw(self):
        self._canvas.draw()

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
                x_labels = item.get('x_labels')
                
                if value >= 1000:
                    val_str = f"{int(value):,} ".replace(",", " ").strip()
                elif value == int(value):
                    val_str = str(int(value))
                else:
                    val_str = f"{value:.2f}"

                if x_labels and 0 <= idx < len(x_labels):
                    x_val = x_labels[idx]
                    text = f"{label} en {x_val} : {val_str}"
                else:
                    text = f"{label} : {val_str}"
                
                if self.hover_text.get_text() != text:
                    self.hover_text.set_text(text)
                    self.hover_text.set_color(theme_manager.colors()['text_primary'])
                    self.fig.canvas.draw_idle()
                
                found = True
                break
                
        if not found and self.hover_text.get_text() != '':
            self._clear_hover_text()

    def _clear_hover_text(self):
        self.hover_text.set_text('')
        self.fig.canvas.draw_idle()


# ─────────────────────────────────────────────────────────────────────────────
# Fonctions de dessin
# ─────────────────────────────────────────────────────────────────────────────

def _setup_ax(gf, c: dict):
    ax = gf.ax
    ax.clear()
    gf.scatters = []
    ax.set_facecolor("none")
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.yaxis.set_visible(False)
    ax.tick_params(colors=c['text_secondary'], labelsize=7, length=0, pad=5)


def _linear_curve(gf, x, y, color, label, alpha=0.9, x_labels=None):
    """Trace une courbe linéaire pure avec scatter."""
    ax = gf.ax
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(y) < 2 or float(np.sum(y)) == 0:
        return
    
    ax.plot(x, y, color=color, linewidth=2.0, label=label, alpha=alpha, antialiased=True)
    scatter = ax.scatter(x, y, color="white", edgecolors=color,
                         s=35, zorder=10, linewidth=1.5, alpha=1.0)
    
    gf.scatters.append({
        'scatter': scatter,
        'label': label,
        'x': x,
        'y': y,
        'x_labels': x_labels
    })


def _finalise(gf, x_ticks, x_labels, c: dict):
    ax = gf.ax
    fig = gf.fig
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_labels, fontsize=7, color=c['text_secondary'])
    
    all_lines = ax.get_lines()
    all_y = [pt for line in all_lines for pt in line.get_ydata()]
    max_v = max(all_y) if all_y else 10
    if max_v <= 0:
        max_v = 10
    ax.set_ylim(0, max_v * 1.25)
    fig.subplots_adjust(left=0.05, right=0.95, top=0.88, bottom=0.22)


# ─────────────────────────────────────────────────────────────────────────────
# Widget principal
# ─────────────────────────────────────────────────────────────────────────────

class AdminGraphesTab(QWidget):

    def __init__(self, consultation_ctrl, examen_ctrl, chirurgie_ctrl,
                 lunette_ctrl, parent=None):
        super().__init__(parent)
        self.ctrl_c = consultation_ctrl
        self.ctrl_e = examen_ctrl
        self.ctrl_ch = chirurgie_ctrl
        self.ctrl_l  = lunette_ctrl
        self.code_session = None

        # Prescription
        try:
            from controllers.controleur_prescription import PrescriptionControleur
            self.ctrl_p = PrescriptionControleur()
        except Exception:
            self.ctrl_p = None

        self._build_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    # ─────────────────────────────────────────────────────────────────
    # Construction UI
    # ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 4, 10, 6)
        root.setSpacing(6)

        # ── Barre top : mois selector + actualiser ────────────────────
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)

        lbl_mois = QLabel("Mois (graphe par jour) :")
        lbl_mois.setObjectName("GrapTopLabel")
        self._combo_mois = QComboBox()
        self._combo_mois.setFixedHeight(24)
        self._combo_mois.setMinimumWidth(120)
        self._combo_mois.setObjectName("GraphCombo")
        now = datetime.now()
        for i, m in enumerate(MOIS_LABELS, start=1):
            self._combo_mois.addItem(m, i)
        self._combo_mois.setCurrentIndex(now.month - 1)
        self._combo_mois.currentIndexChanged.connect(self._on_mois_changed)

        self._btn_refresh = QPushButton("  Actualiser")
        self._btn_refresh.setFixedHeight(24)
        self._btn_refresh.setCursor(Qt.PointingHandCursor)
        self._btn_refresh.setObjectName("AdminRefreshBtn")
        self._btn_refresh.clicked.connect(self.charger_donnees)

        top.addWidget(lbl_mois)
        top.addWidget(self._combo_mois)
        top.addStretch()
        top.addWidget(self._btn_refresh)
        root.addLayout(top)

        # ── Ligne du haut : 3 graphes ─────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.gf_nombre  = GraphFrame("Nombre par mois",         "fa5s.chart-bar")
        self.gf_montant = GraphFrame("Montant par mois (GNF)",  "fa5s.chart-area")
        self.gf_moyenne = GraphFrame("Moyenne journalière/mois","fa5s.chart-line")

        top_row.addWidget(self.gf_nombre)
        top_row.addWidget(self.gf_montant)
        top_row.addWidget(self.gf_moyenne)
        root.addLayout(top_row, 1)

        # ── Bas : 1 graphe pleine largeur ─────────────────────────────
        self.gf_jour = GraphFrame("Nombre par jour", "fa5s.calendar-day",
                                  figsize=(10, 2.4))
        root.addWidget(self.gf_jour, 1)

        # Légendes initiales
        self._set_legends()

    def _set_legends(self):
        for gf in (self.gf_nombre, self.gf_montant, self.gf_moyenne, self.gf_jour):
            gf.set_legend(SERVICES)

    # ─────────────────────────────────────────────────────────────────
    # Chargement synchrone
    # ─────────────────────────────────────────────────────────────────

    def charger_donnees(self, code_session: str = None):
        if code_session:
            self.code_session = code_session
        if not self.code_session:
            return
        try:
            self._dessiner_nombre_par_mois()
            self._dessiner_montant_par_mois()
            self._dessiner_moyenne_par_mois()
            self._dessiner_nombre_par_jour()
        except Exception as e:
            print(f"[AdminGraphesTab] Erreur: {e}")
            import traceback; traceback.print_exc()

    def _on_mois_changed(self):
        if self.code_session:
            self._dessiner_nombre_par_jour()

    # ─────────────────────────────────────────────────────────────────
    # Utilitaires
    # ─────────────────────────────────────────────────────────────────

    def _safe(self, fn, *args, default=None):
        try:
            return fn(*args) or (default if default is not None else {})
        except Exception:
            return default if default is not None else {}

    # Clés sans accent utilisées dans l'ancien DAO prescription
    _PRESC_NORM = {"Fév": "Fev", "Août": "Aout", "Déc": "Dec"}

    def _mois_vals(self, data: dict) -> list:
        return [float(data.get(m, 0) or 0) for m in MOIS_LABELS]

    def _mois_vals_presc(self, data: dict) -> list:
        """Comme _mois_vals mais tolère les clés sans accent (ancien DAO)."""
        result = []
        for m in MOIS_LABELS:
            val = data.get(m, data.get(self._PRESC_NORM.get(m, m), 0))
            result.append(float(val or 0))
        return result

    def _day_vals(self, data: dict, nb_days: int) -> tuple:
        labels = [f"{d:02d}" for d in range(1, nb_days + 1)]
        values = [float(data.get(f"{d:02d}", data.get(str(d), 0)) or 0)
                  for d in range(1, nb_days + 1)]
        return labels, values

    # ─────────────────────────────────────────────────────────────────
    # Graphe 1 — Nombre par mois
    # ─────────────────────────────────────────────────────────────────

    def _dessiner_nombre_par_mois(self):
        c   = theme_manager.colors()
        _setup_ax(self.gf_nombre, c)
        s   = self.code_session
        x   = np.arange(12)

        datasets = [
            (self._mois_vals(self._safe(self.ctrl_c.obtenir_nombre_par_mois, s)),
             SERVICES[0][1], SERVICES[0][0]),
            (self._mois_vals(self._safe(self.ctrl_e.obtenir_nombre_par_mois, s)),
             SERVICES[1][1], SERVICES[1][0]),
            (self._mois_vals(self._safe(self.ctrl_ch.obtenir_nombre_par_mois, s)),
             SERVICES[2][1], SERVICES[2][0]),
            (self._mois_vals(self._safe(self.ctrl_l.obtenir_nombre_par_mois, s)),
             SERVICES[3][1], SERVICES[3][0]),
        ]
        if self.ctrl_p:
            # _mois_vals_presc tolère les clés sans accent de l'ancien DAO
            datasets.append((
                self._mois_vals_presc(self._safe(self.ctrl_p.obtenir_prescriptions_par_mois, s)),
                SERVICES[4][1], SERVICES[4][0]
            ))

        for vals, color, label in datasets:
            _linear_curve(self.gf_nombre, x, vals, color, label, x_labels=MOIS_LABELS)

        _finalise(self.gf_nombre, x, MOIS_LABELS, c)
        self.gf_nombre.draw()

    # ─────────────────────────────────────────────────────────────────
    # Graphe 2 — Montant par mois
    # ─────────────────────────────────────────────────────────────────

    def _dessiner_montant_par_mois(self):
        c   = theme_manager.colors()
        _setup_ax(self.gf_montant, c)
        s   = self.code_session
        x   = np.arange(12)

        datasets = [
            (self._mois_vals(self._safe(self.ctrl_c.obtenir_montant_par_mois, s)),
             SERVICES[0][1], SERVICES[0][0]),
            (self._mois_vals(self._safe(self.ctrl_e.obtenir_montant_par_mois, s)),
             SERVICES[1][1], SERVICES[1][0]),
            (self._mois_vals(self._safe(self.ctrl_ch.obtenir_montant_par_mois, s)),
             SERVICES[2][1], SERVICES[2][0]),
            (self._mois_vals(self._safe(self.ctrl_l.obtenir_montant_par_mois, s)),
             SERVICES[3][1], SERVICES[3][0]),
        ]
        if self.ctrl_p:
            datasets.append((
                self._mois_vals(self._safe(self.ctrl_p.obtenir_montant_par_mois, s)),
                SERVICES[4][1], SERVICES[4][0]
            ))

        for vals, color, label in datasets:
            _linear_curve(self.gf_montant, x, vals, color, label, x_labels=MOIS_LABELS)

        _finalise(self.gf_montant, x, MOIS_LABELS, c)
        self.gf_montant.draw()

    # ─────────────────────────────────────────────────────────────────
    # Graphe 3 — Moyenne journalière par mois
    # ─────────────────────────────────────────────────────────────────

    def _dessiner_moyenne_par_mois(self):
        c   = theme_manager.colors()
        _setup_ax(self.gf_moyenne, c)
        s   = self.code_session
        x   = np.arange(12)

        datasets = [
            (self._mois_vals(self._safe(
                self.ctrl_c.obtenir_moyenne_nombre_journalier_par_mois, s)),
             SERVICES[0][1], SERVICES[0][0]),
            (self._mois_vals(self._safe(
                self.ctrl_e.obtenir_moyenne_nombre_journalier_par_mois, s)),
             SERVICES[1][1], SERVICES[1][0]),
            (self._mois_vals(self._safe(
                self.ctrl_ch.obtenir_moyenne_nombre_journalier_par_mois, s)),
             SERVICES[2][1], SERVICES[2][0]),
            (self._mois_vals(self._safe(
                self.ctrl_l.obtenir_moyenne_nombre_journalier_par_mois, s)),
             SERVICES[3][1], SERVICES[3][0]),
        ]
        if self.ctrl_p:
            datasets.append((
                self._mois_vals(self._safe(
                    self.ctrl_p.obtenir_moyenne_nombre_journalier_par_mois, s)),
                SERVICES[4][1], SERVICES[4][0]
            ))

        for vals, color, label in datasets:
            _linear_curve(self.gf_moyenne, x, vals, color, label, x_labels=MOIS_LABELS)

        _finalise(self.gf_moyenne, x, MOIS_LABELS, c)
        self.gf_moyenne.draw()

    # ─────────────────────────────────────────────────────────────────
    # Graphe 4 — Nombre par jour (mois sélectionné)
    # ─────────────────────────────────────────────────────────────────

    def _dessiner_nombre_par_jour(self):
        import calendar
        c    = theme_manager.colors()
        _setup_ax(self.gf_jour, c)
        ax   = self.gf_jour.ax
        s    = self.code_session
        now  = datetime.now()
        year = now.year
        mois = self._combo_mois.currentData() or now.month
        nb_days = calendar.monthrange(year, mois)[1]
        x = np.arange(1, nb_days + 1)

        datasets = [
            (self._safe(self.ctrl_c.obtenir_nombre_par_jour,  s, year, mois),
             SERVICES[0][1], SERVICES[0][0]),
            (self._safe(self.ctrl_e.obtenir_nombre_par_jour,  s, year, mois),
             SERVICES[1][1], SERVICES[1][0]),
            (self._safe(self.ctrl_ch.obtenir_nombre_par_jour, s, year, mois),
             SERVICES[2][1], SERVICES[2][0]),
            (self._safe(self.ctrl_l.obtenir_nombre_par_jour,  s, year, mois),
             SERVICES[3][1], SERVICES[3][0]),
        ]
        if self.ctrl_p:
            datasets.append((
                self._safe(self.ctrl_p.obtenir_nombre_par_jour, s, year, mois),
                SERVICES[4][1], SERVICES[4][0]
            ))

        x_ticks = list(range(1, nb_days + 1))
        full_x_labels = [str(d) for d in x_ticks]

        for data, color, label in datasets:
            _, vals = self._day_vals(data, nb_days)
            _linear_curve(self.gf_jour, x, np.array(vals, dtype=float), color, label, x_labels=full_x_labels)

        # Tous les labels sont visibles (suppression de la condition if nb_days > 15)
        x_labels = full_x_labels

        month_name = MOIS_LABELS[mois - 1]
        ax.set_title(f"{month_name} {year}",
                     fontsize=9, color=c['text_secondary'], pad=4)
        _finalise(self.gf_jour, x_ticks, x_labels, c)
        self.gf_jour.fig.subplots_adjust(left=0.03, right=0.98, top=0.88, bottom=0.18)
        self.gf_jour.draw()

    # ─────────────────────────────────────────────────────────────────
    # Thème
    # ─────────────────────────────────────────────────────────────────

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background:{c['bg_main']};")
        self.findChild(QLabel, "GrapTopLabel")

        for w in self.findChildren(QLabel):
            if w.objectName() == "GrapTopLabel":
                w.setStyleSheet(
                    f"color:{c['text_secondary']}; font-size:11px; font-weight:600; border:none;"
                )

        self._combo_mois.setStyleSheet(f"""
            QComboBox#GraphCombo {{
                background:{c['bg_input']}; color:{c['text_primary']};
                border:1px solid {c['border']}; border-radius:6px;
                padding:0 8px; font-size:11px; font-weight:600;
            }}
            QComboBox#GraphCombo::drop-down {{ border:none; width:16px; }}
            QComboBox#GraphCombo QAbstractItemView {{
                background:{c['bg_card']}; color:{c['text_primary']};
                border:1px solid {c['border_light']};
                selection-background-color:{c['hover']};
            }}
        """)
        self._btn_refresh.setIcon(qta.icon("fa5s.sync-alt", color=c['primary']))
        self._btn_refresh.setStyleSheet(f"""
            QPushButton#AdminRefreshBtn {{
                background:{c['primary_light']}; color:{c['primary']};
                border:1px solid {c['primary']}; border-radius:6px;
                padding:0 10px; font-size:11px; font-weight:700;
            }}
            QPushButton#AdminRefreshBtn:hover {{
                background:{c['primary']}; color:{c['text_inverse']};
            }}
        """)
        # Redessiner avec les nouvelles couleurs de thème
        if self.code_session:
            self.charger_donnees()
