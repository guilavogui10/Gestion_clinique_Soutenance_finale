"""
=============================================================================
 RESPONSIVE HELPERS — Conteneurs adaptatifs pour toute l'application
=============================================================================
 Fournit des widgets qui réorganisent automatiquement leur contenu
 selon la largeur disponible, garantissant la visibilité sur tout écran
 SANS SCROLL VERTICAL.

 Classes :
   ResponsiveGridContainer  — Grille NxM qui passe de 4→3→2→1 colonnes
   ResponsiveSplitContainer — Deux panneaux côte-à-côte qui s'empilent
=============================================================================
"""

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QSizePolicy,
)
from PySide6.QtCore import QTimer, Qt


# ═════════════════════════════════════════════════════════════════════════════
# ResponsiveGridContainer
# ═════════════════════════════════════════════════════════════════════════════

class ResponsiveGridContainer(QWidget):
    """
    Conteneur grille responsive.
    Réorganise automatiquement ses widgets enfants selon la largeur
    disponible. Les lignes et colonnes reçoivent un stretch égal
    pour remplir tout l'espace sans besoin de scroll.

    Breakpoints (largeur du conteneur) :
      ≥ 1000px  →  Layout XL personnalisé (spans configurables)
      ≥  700px  →  3 colonnes
      ≥  450px  →  2 colonnes
      <  450px  →  1 colonne
    """

    _BP_XL = 1000
    _BP_LG = 700
    _BP_MD = 450

    def __init__(self, spacing=15, parent=None):
        super().__init__(parent)
        self._grid = QGridLayout(self)
        self._grid.setSpacing(spacing)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._sections = []
        self._all_widgets = []
        self._current_bp = None

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._reorganiser)

    def ajouter_section(self, widgets, xl_spans=None, expand_v=True):
        """
        Ajoute une section (rangée logique) de widgets.

        Args:
            widgets:   liste de QWidget à placer dans cette section
            xl_spans:  nb de colonnes par widget en mode XL (ex: [2, 1, 1])
            expand_v:  si True les widgets s'étirent verticalement
        """
        for w in widgets:
            v_policy = QSizePolicy.Expanding if expand_v else QSizePolicy.Preferred
            w.setSizePolicy(QSizePolicy.Expanding, v_policy)
        self._sections.append({
            'widgets': widgets,
            'xl_spans': xl_spans or [1] * len(widgets),
        })
        self._all_widgets = [w for s in self._sections for w in s['widgets']]

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._timer.start()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._reorganiser)

    def _reorganiser(self):
        w = self.width()
        if w <= 0:
            return
        if w >= self._BP_XL:
            bp = 'xl'
        elif w >= self._BP_LG:
            bp = 'lg'
        elif w >= self._BP_MD:
            bp = 'md'
        else:
            bp = 'sm'
        if bp == self._current_bp:
            return
        self._current_bp = bp
        self._vider_grille()
        if bp == 'xl':
            self._layout_xl()
        elif bp == 'lg':
            self._layout_grille(3)
        elif bp == 'md':
            self._layout_grille(2)
        else:
            self._layout_grille(1)

    def _vider_grille(self):
        """Retire tous les widgets et remet les stretch à zéro."""
        while self._grid.count():
            self._grid.takeAt(0)
        for c in range(self._grid.columnCount()):
            self._grid.setColumnStretch(c, 0)
        for r in range(self._grid.rowCount()):
            self._grid.setRowStretch(r, 0)

    def _layout_xl(self):
        """Place les widgets selon les sections avec xl_spans + stretch lignes."""
        max_cols = 1
        for row_idx, section in enumerate(self._sections):
            col = 0
            for i, widget in enumerate(section['widgets']):
                span = section['xl_spans'][i]
                self._grid.addWidget(widget, row_idx, col, 1, span)
                col += span
            max_cols = max(max_cols, col)
        for c in range(max_cols):
            self._grid.setColumnStretch(c, 1)
        for r in range(len(self._sections)):
            self._grid.setRowStretch(r, 1)

    def _layout_grille(self, cols):
        """Place tous les widgets en grille simple N colonnes + stretch lignes."""
        row, col = 0, 0
        for widget in self._all_widgets:
            self._grid.addWidget(widget, row, col, 1, 1)
            col += 1
            if col >= cols:
                col = 0
                row += 1
        total_rows = row + (1 if col > 0 else 0)
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)
        for r in range(total_rows):
            self._grid.setRowStretch(r, 1)


# ═════════════════════════════════════════════════════════════════════════════
# ResponsiveSplitContainer
# ═════════════════════════════════════════════════════════════════════════════

class ResponsiveSplitContainer(QWidget):
    """
    Conteneur à deux panneaux qui bascule automatiquement :
      ≥ breakpoint  →  côte-à-côte (horizontal) avec ratios configurables
      < breakpoint  →  empilés verticalement (ratios 1:1)

    Utilisation :
      split = ResponsiveSplitContainer(breakpoint=800)
      split.set_widgets(left_panel, right_panel, ratios=(7, 3))
    """

    def __init__(self, breakpoint=800, spacing=16, parent=None):
        super().__init__(parent)
        self._bp = breakpoint
        self._spacing = spacing
        self._w1 = None
        self._w2 = None
        self._ratios = (3, 2)
        self._current_mode = None

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(0)

        self._container = QWidget()
        self._inner_layout = None
        self._outer.addWidget(self._container)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._reorganiser)

    def set_widgets(self, w1, w2, ratios=(3, 2)):
        """Définit les deux panneaux et leurs proportions."""
        self._w1 = w1
        self._w2 = w2
        self._ratios = ratios
        self._current_mode = None
        self._reorganiser()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._timer.start()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._reorganiser)

    def _reorganiser(self):
        if not self._w1 or not self._w2:
            return
        w = self.width()
        if w <= 0:
            return
        mode = 'h' if w >= self._bp else 'v'
        if mode == self._current_mode:
            return
        self._current_mode = mode

        # Retirer les widgets de l'ancien layout
        if self._inner_layout is not None:
            self._inner_layout.removeWidget(self._w1)
            self._inner_layout.removeWidget(self._w2)
            self._w1.setParent(None)
            self._w2.setParent(None)

        self._outer.removeWidget(self._container)
        self._container.deleteLater()

        self._container = QWidget()
        if mode == 'h':
            lay = QHBoxLayout(self._container)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(self._spacing)
            lay.addWidget(self._w1, self._ratios[0])
            lay.addWidget(self._w2, self._ratios[1])
        else:
            lay = QVBoxLayout(self._container)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(self._spacing)
            lay.addWidget(self._w1, 1)
            lay.addWidget(self._w2, 1)

        self._inner_layout = lay
        self._outer.addWidget(self._container)
