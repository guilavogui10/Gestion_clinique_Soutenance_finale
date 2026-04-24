"""
=============================================================================
 RESPONSIVE ANALYSES — Grille adaptative pour le dossier analyses
=============================================================================
 Sous-classe de ResponsiveGridContainer avec des breakpoints ajustés
 pour les vues d'analyse (toujours au moins 2 colonnes).

 Utilisation :
   from views.analyses.responsive_analyses import AnalyseResponsiveGrid
   grid = AnalyseResponsiveGrid(spacing=10)
   grid.ajouter_section([frame1, frame2], xl_spans=[1, 1])
=============================================================================
"""

from views.shared.responsive_helper import ResponsiveGridContainer


class AnalyseResponsiveGrid(ResponsiveGridContainer):
    """
    Grille responsive pour les vues d'analyse.
    Hérite de ResponsiveGridContainer avec breakpoints ajustés :
      ≥ 900px  →  Layout XL (spans configurables)
      <  900px →  2 colonnes (jamais 1 colonne — pas de scroll)
    """

    _BP_XL = 900
    _BP_LG = 0   # Désactivé → saute directement à MD
    _BP_MD = 0   # Toujours au moins 2 colonnes

    def __init__(self, spacing=10, parent=None):
        super().__init__(spacing=spacing, parent=parent)

    def _reorganiser(self):
        """Override : seulement XL (spans) ou 2 colonnes."""
        w = self.width()
        if w <= 0:
            return
        bp = 'xl' if w >= self._BP_XL else 'md'
        if bp == self._current_bp:
            return
        self._current_bp = bp
        self._vider_grille()
        if bp == 'xl':
            self._layout_xl()
        else:
            self._layout_grille(2)

    def _layout_xl(self):
        """Override : rangée 0 (graphes) prend plus de place que rangée 1."""
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
        # Rangée 0 (graphes) stretch=3, rangée 1 (détails) stretch=2
        stretches = [3, 2]
        for r in range(len(self._sections)):
            self._grid.setRowStretch(r, stretches[r] if r < len(stretches) else 1)

    def _layout_grille(self, cols):
        """Override : en mode 2 colonnes, lignes 0 et 2 (graphes) stretch=3, lignes 1 et 3 stretch=2."""
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
        # Alternance: rangées paires (graphes) stretch=3, impaires (détails) stretch=2
        for r in range(total_rows):
            self._grid.setRowStretch(r, 3 if r % 2 == 0 else 2)
