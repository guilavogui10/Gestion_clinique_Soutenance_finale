"""
Widget CircularProgress - Graphe circulaire de progression (donut chart).
Responsabilité : Dessiner un cercle de progression avec QPainter.
Pattern : Custom Widget, Painter Pattern.
"""

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import QWidget

from views.shared.theme_manager import theme_manager


class CircularProgress(QWidget):
    """
    Widget personnalisé pour afficher un graphe circulaire de progression.
    
    Dessine un cercle avec une partie colorée selon le pourcentage.
    
    Structure :
        ⭕ Cercle gris (fond)
        🔵 Arc coloré (progression)
        📊 Pourcentage au centre
    
    Usage:
        >>> progress = CircularProgress(50, "#3498db")
        >>> progress.set_value(75)
    """
    
    def __init__(self, pourcentage: int = 0, couleur: str = "#3498db", 
                 taille: int = 60, parent=None):
        """
        Initialise le widget de progression circulaire.
        
        Args:
            pourcentage: Pourcentage initial (0-100)
            couleur: Couleur hexadécimale de la progression
            taille: Taille du widget en pixels
            parent: Widget parent Qt
        """
        super().__init__(parent)
        
        self.pourcentage = pourcentage
        self.couleur = QColor(couleur)
        self.taille = taille
        
        self.setFixedSize(taille, taille)
    
    def set_value(self, pourcentage: int):
        """
        Met à jour le pourcentage et redessine.
        
        Args:
            pourcentage: Nouveau pourcentage (0-100)
        """
        self.pourcentage = max(0, min(100, pourcentage))
        self.update()  # Déclenche paintEvent
    
    def set_color(self, couleur: str):
        """
        Change la couleur de la progression.
        
        Args:
            couleur: Nouvelle couleur hexadécimale
        """
        self.couleur = QColor(couleur)
        self.update()
    
    def paintEvent(self, event):
        """
        Dessine le cercle de progression.
        Appelé automatiquement par Qt lors du rafraîchissement.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dimensions
        width = self.width()
        height = self.height()
        size = min(width, height)
        
        # Rectangle pour le cercle
        rect = QRect(5, 5, size - 10, size - 10)
        
        # 1. Dessiner le cercle de fond
        c = theme_manager.colors()
        pen_fond = QPen(QColor(c['border_light']))
        pen_fond.setWidth(8)
        pen_fond.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_fond)
        painter.drawArc(rect, 0, 360 * 16)  # 360° complet
        
        # 2. Dessiner l'arc de progression (couleur)
        if self.pourcentage > 0:
            pen_progress = QPen(self.couleur)
            pen_progress.setWidth(8)
            pen_progress.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_progress)
            
            # Angle de départ : 90° (haut du cercle)
            # Angle de balayage : pourcentage * 3.6 (360° / 100)
            start_angle = 90 * 16  # Qt utilise 1/16ème de degré
            span_angle = -int(self.pourcentage * 3.6 * 16)  # Négatif = sens horaire
            
            painter.drawArc(rect, start_angle, span_angle)
        
        # 3. Dessiner le pourcentage au centre
        painter.setPen(self.couleur)
        font = QFont()
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)
        
        text = f"{self.pourcentage}%"
        painter.drawText(rect, Qt.AlignCenter, text)
