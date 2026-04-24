"""
Conteneur a pages avec transition horizontale.
"""

from PySide6.QtCore import (
    QRect,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QAbstractAnimation,
)
from PySide6.QtWidgets import QWidget


class AnimatedStack(QWidget):
    DURATION = 380

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pages = []
        self._current = 0
        self._locked = False
        self._group = None

    def add_page(self, widget: QWidget) -> None:
        widget.setParent(self)
        idx = len(self._pages)
        self._pages.append(widget)

        if idx == 0:
            widget.setGeometry(0, 0, max(self.width(), 1), max(self.height(), 1))
            widget.show()
        else:
            widget.setGeometry(max(self.width(), 1), 0, max(self.width(), 1), max(self.height(), 1))
            widget.hide()

    def current_index(self) -> int:
        return self._current

    def slide_to(self, index: int) -> None:
        if index == self._current or self._locked:
            return
        if not 0 <= index < len(self._pages):
            return

        w, h = self.width(), self.height()
        old_page = self._pages[self._current]
        new_page = self._pages[index]
        direction = 1 if index > self._current else -1

        new_page.setGeometry(direction * w, 0, w, h)
        new_page.show()
        new_page.raise_()

        self._locked = True

        anim_out = QPropertyAnimation(old_page, b"geometry")
        anim_out.setDuration(self.DURATION)
        anim_out.setStartValue(QRect(0, 0, w, h))
        anim_out.setEndValue(QRect(-direction * w, 0, w, h))
        anim_out.setEasingCurve(QEasingCurve.InOutCubic)

        anim_in = QPropertyAnimation(new_page, b"geometry")
        anim_in.setDuration(self.DURATION)
        anim_in.setStartValue(QRect(direction * w, 0, w, h))
        anim_in.setEndValue(QRect(0, 0, w, h))
        anim_in.setEasingCurve(QEasingCurve.InOutCubic)

        self._group = QParallelAnimationGroup(self)
        self._group.addAnimation(anim_out)
        self._group.addAnimation(anim_in)

        target = index
        old = old_page

        def _on_done():
            old.hide()
            self._current = target
            self._locked = False

        self._group.finished.connect(_on_done)
        self._group.start(QAbstractAnimation.DeleteWhenStopped)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if not w or not h:
            return

        for i, page in enumerate(self._pages):
            if i == self._current:
                page.setGeometry(0, 0, w, h)
            else:
                offset = w if i > self._current else -w
                page.setGeometry(offset, 0, w, h)
