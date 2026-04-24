"""
Composant AnimatedFrame - Cadre avec animation.
Responsabilité : Fournir un cadre avec effet d'ombre et animation au survol.
Pattern : Component, Reusability.
"""

from PySide6.QtCore import QPropertyAnimation, QPoint, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect


class AnimatedFrame(QFrame):
    """
    Cadre arrondi avec effet d'ombre et animation de survol.
    
    Fonctionnalités :
    - Ombre portée configurable
    - Animation au survol (monte de 5px)
    - Animation au départ (descend de 5px)
    
    Usage:
        >>> frame = AnimatedFrame()
        >>> frame.setStyleSheet("background: white; border-radius: 12px;")
    """
    
    def __init__(self, parent=None):
        """
        Initialise le cadre animé.
        
        Args:
            parent: Widget parent Qt
        """
        super().__init__(parent)
        self._setup_animation()
    
    def _setup_animation(self):
        """Configure l'ombre et l'animation."""
        # Ombre portée
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(0, 4)
        self.shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(self.shadow)
        
        # Animation de position
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def enterEvent(self, event):
        """
        Événement déclenché quand la souris entre dans le cadre.
        Animation : monte de 5px et augmente l'ombre.
        """
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(QPoint(self.pos().x(), self.pos().y() - 5))
        self.shadow.setBlurRadius(25)
        self.animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """
        Événement déclenché quand la souris quitte le cadre.
        Animation : descend de 5px et réduit l'ombre.
        """
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(QPoint(self.pos().x(), self.pos().y() + 5))
        self.shadow.setBlurRadius(15)
        self.animation.start()
        super().leaveEvent(event)
