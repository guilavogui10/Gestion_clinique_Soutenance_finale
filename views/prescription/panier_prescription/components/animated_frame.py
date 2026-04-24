"""
Composant AnimatedFrame réutilisable.
Pattern : Composition - Composant UI réutilisable avec animation.
"""

from PySide6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect


class AnimatedFrame(QFrame):
    """
    Cadre arrondi avec effet d'ombre et animation de survol.
    Réutilisable dans toute l'application.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_animation()

    def _setup_animation(self):
        """Configure l'effet d'ombre et l'animation."""
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(0, 4)
        self.shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(self.shadow)

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

    def enterEvent(self, event):
        """Animation au survol de la souris."""
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(QPoint(self.pos().x(), self.pos().y() - 5))
        self.shadow.setBlurRadius(25)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Animation à la sortie de la souris."""
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(QPoint(self.pos().x(), self.pos().y() + 5))
        self.shadow.setBlurRadius(15)
        self.animation.start()
        super().leaveEvent(event)
