import qtawesome as qta

from PySide6.QtCore    import Qt, QTimer, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea
)
from views.shared.modal_theme import MC


# =============================================================================
# PALETTE  (évaluée dynamiquement à chaque appel)
# =============================================================================
def _couleurs_mois():
    return [
        MC.INFO,       # Jan  — Bleu
        MC.SUCCESS,    # Fev  — Vert
        MC.WARNING,    # Mar  — Orange
        MC.ACCENT,     # Avr  — Violet
        MC.DANGER,     # Mai  — Rouge
        "#D4AF37",     # Juin — Or
        MC.PRIMARY,    # Juil — Vert foncé
        "#06B6D4",     # Aout — Cyan
        "#F97316",     # Sep  — Orange vif
        "#6366F1",     # Oct  — Indigo
        "#EC4899",     # Nov  — Rose
        "#14B8A6",     # Dec  — Teal
    ]


# =============================================================================
# BARRE DE PROGRESSION ANIMÉE PAR MOIS
# =============================================================================
class BarreProgressionMois(QWidget):

    def __init__(self, mois: str, valeur: int, max_valeur: int, couleur: str = None, parent=None):
        super().__init__(parent)
        self.mois        = mois
        self.valeur      = valeur
        self.max_valeur  = max(max_valeur, 1)
        self.couleur     = couleur or MC.ACCENT
        self._pct_actuel = 0.0
        self._setup_ui()
        QTimer.singleShot(400, self._demarrer_animation)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(3)

        header = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(qta.icon("fa5s.calendar", color=self.couleur).pixmap(QSize(11, 11)))

        nom = QLabel(self.mois)
        nom.setStyleSheet(
            f"color:{MC.TEXT_SECONDARY}; font-size:10px; font-weight:600; background:transparent;"
        )

        self.lbl_val = QLabel("0")
        self.lbl_val.setStyleSheet(
            f"color:{self.couleur}; font-size:14px; font-weight:700; background:transparent;"
        )
        self.lbl_val.setAlignment(Qt.AlignRight)

        header.addWidget(ic)
        header.addSpacing(4)
        header.addWidget(nom)
        header.addStretch()
        header.addWidget(self.lbl_val)
        layout.addLayout(header)

        self._piste = QFrame()
        self._piste.setFixedHeight(6)
        self._piste.setStyleSheet(f"background:{MC.BORDER}; border-radius:3px; border:none;")
        piste_inner = QHBoxLayout(self._piste)
        piste_inner.setContentsMargins(0, 0, 0, 0)
        piste_inner.setSpacing(0)

        self._fill = QFrame()
        self._fill.setFixedHeight(6)
        self._fill.setFixedWidth(0)
        self._fill.setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {self.couleur}99,stop:1 {self.couleur});"
            f"border-radius:3px; border:none;"
        )
        piste_inner.addWidget(self._fill)
        piste_inner.addStretch()
        layout.addWidget(self._piste)

    def _demarrer_animation(self):
        if self.valeur == 0:
            return
        self._timer = QTimer()
        self._timer.setInterval(14)
        self._timer.timeout.connect(self._animer)
        self._timer.start()

    def _animer(self):
        pct_cible = (self.valeur / self.max_valeur) * 100
        if self._pct_actuel >= pct_cible:
            self._pct_actuel = pct_cible
            self._timer.stop()
        self._pct_actuel = min(self._pct_actuel + 1.5, pct_cible)
        w = max(0, int((self._piste.width() - 2) * self._pct_actuel / 100))
        self._fill.setFixedWidth(w)
        val_actuelle = int((self.valeur * self._pct_actuel) / pct_cible) if pct_cible > 0 else 0
        self.lbl_val.setText(f"{val_actuelle}")


# =============================================================================
# WIDGET PRINCIPAL
# =============================================================================
class CommandeLunetteAnalyseGraph(QWidget):

    MONTH_LABELS = [
        'Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin',
        'Juil', 'Aout', 'Sep', 'Oct', 'Nov', 'Dec'
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_stats = None
        self.setStyleSheet("background:transparent; border:none;")

        from views.shared.theme_manager import theme_manager
        theme_manager.theme_changed.connect(self._on_theme_change)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)          # ← supprime tout contour
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        from views.shared.theme_manager import theme_manager
        tc = theme_manager.colors()
        scroll.setStyleSheet(
            "QScrollArea{border:none; background:transparent;}"
            f"QScrollBar:vertical{{border:none; background:{tc['bg_main']};"
            "width:4px; border-radius:2px;}"
            f"QScrollBar::handle:vertical{{background:{tc['border']}; border-radius:2px;}}"
            "QScrollBar::add-line:vertical,"
            "QScrollBar::sub-line:vertical{height:0;}"
        )

        self._contenu = QWidget()
        self._contenu.setStyleSheet("background:transparent; border:none;")
        self._contenu_layout = QVBoxLayout(self._contenu)
        self._contenu_layout.setContentsMargins(0, 2, 10, 2)
        self._contenu_layout.setSpacing(6)

        scroll.setWidget(self._contenu)
        layout.addWidget(scroll)

    def _on_theme_change(self):
        if self._last_stats is not None:
            self.update_graph(self._last_stats)

    def update_graph(self, stats_mensuelles: dict):
        self._last_stats = stats_mensuelles
        while self._contenu_layout.count():
            item = self._contenu_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not stats_mensuelles:
            lbl = QLabel("Aucune donnée disponible")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                f"color:{MC.TEXT_SECONDARY}; font-size:10px; background:transparent;")
            self._contenu_layout.addWidget(lbl)
            return

        values  = [stats_mensuelles.get(mois, 0) for mois in self.MONTH_LABELS]
        max_val = max(values) if max(values) > 0 else 1
            
        # APRÈS
        palette = _couleurs_mois()
        for i, mois in enumerate(self.MONTH_LABELS):
            valeur  = stats_mensuelles.get(mois, 0)
            couleur = palette[i]
            self._contenu_layout.addWidget(
                BarreProgressionMois(mois, valeur, max_val, couleur=couleur))

        self._contenu_layout.addStretch()