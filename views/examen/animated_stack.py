"""
=============================================================================
 ANIMATED STACK
=============================================================================
 Conteneur à N pages avec transition par glissement horizontal.
 Pas de QLayout interne — enfants positionnés manuellement.

 Usage :
   stack = AnimatedStack()
   stack.add_page(widget_a)   # index 0
   stack.add_page(widget_b)   # index 1
   stack.slide_to(1)          # slide vers la droite
   stack.slide_to(0)          # slide vers la gauche
=============================================================================
"""

from PySide6.QtCore import (
    Qt, QRect, QPropertyAnimation, QEasingCurve,
    QParallelAnimationGroup, QAbstractAnimation
)
from PySide6.QtWidgets import QWidget


class AnimatedStack(QWidget):
    """
    Conteneur deux pages avec animation de glissement horizontal.

    - Aller vers index > courant : nouveau panneau entre par la droite.
    - Revenir vers index < courant : nouveau panneau entre par la gauche.
    - Les clics pendant l'animation sont ignorés (self._locked).
    """

    DURATION = 380   # ms — ajuster au goût

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pages:   list[QWidget] = []
        self._current: int           = 0
        self._locked:  bool          = False
        self._group    = None        # référence gardée pour éviter le GC

    # ─── API publique ──────────────────────────────────────────────────────

    def add_page(self, widget: QWidget) -> None:
        """Ajoute une page. La première est visible, les autres hors écran."""
        widget.setParent(self)
        idx = len(self._pages)
        self._pages.append(widget)

        if idx == 0:
            widget.setGeometry(0, 0, max(self.width(), 1), max(self.height(), 1))
            widget.show()
        else:
            # Placée hors écran à droite — sera ajustée par resizeEvent aussi
            widget.setGeometry(max(self.width(), 1), 0,
                               max(self.width(), 1), max(self.height(), 1))
            widget.hide()

    def current_index(self) -> int:
        return self._current

    def slide_to(self, index: int) -> None:
        """Lance la transition vers la page `index`."""
        if index == self._current or self._locked:
            return
        if not 0 <= index < len(self._pages):
            return

        w, h      = self.width(), self.height()
        old_page  = self._pages[self._current]
        new_page  = self._pages[index]
        direction = 1 if index > self._current else -1   # +1 = vient de droite

        # Positionner la nouvelle page hors écran côté d'entrée
        new_page.setGeometry(direction * w, 0, w, h)
        new_page.show()
        new_page.raise_()

        self._locked = True

        # Ancienne page → sort du côté opposé
        anim_out = QPropertyAnimation(old_page, b"geometry")
        anim_out.setDuration(self.DURATION)
        anim_out.setStartValue(QRect(0, 0, w, h))
        anim_out.setEndValue(QRect(-direction * w, 0, w, h))
        anim_out.setEasingCurve(QEasingCurve.InOutCubic)

        # Nouvelle page → entre au centre
        anim_in = QPropertyAnimation(new_page, b"geometry")
        anim_in.setDuration(self.DURATION)
        anim_in.setStartValue(QRect(direction * w, 0, w, h))
        anim_in.setEndValue(QRect(0, 0, w, h))
        anim_in.setEasingCurve(QEasingCurve.InOutCubic)

        self._group = QParallelAnimationGroup(self)
        self._group.addAnimation(anim_out)
        self._group.addAnimation(anim_in)

        target = index
        old    = old_page

        def _on_done():
            old.hide()
            self._current = target
            self._locked  = False

        self._group.finished.connect(_on_done)
        self._group.start(QAbstractAnimation.DeleteWhenStopped)

    # ─── Redimensionnement ────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if not w or not h:
            return

        for i, page in enumerate(self._pages):
            if i == self._current:
                page.setGeometry(0, 0, w, h)
            else:
                # Garde les pages hors écran à leur position logique
                offset = w if i > self._current else -w
                page.setGeometry(offset, 0, w, h)