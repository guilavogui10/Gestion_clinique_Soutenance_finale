"""
Widget MultiSegmentDonut - Graphique en camembert multi-segments.
Responsabilité : Dessiner un donut avec plusieurs segments colorés.
Pattern : Custom Widget, Painter Pattern.
"""

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush
from PySide6.QtWidgets import QWidget
from typing import List, Tuple

from views.shared.theme_manager import theme_manager


class MultiSegmentDonut(QWidget):
    """
    Widget personnalisé pour afficher un graphique en camembert multi-segments.
    
    Dessine un cercle avec plusieurs segments colorés selon les pourcentages.
    
    Structure :
        🔴 Segment 1 (ex: Expirés)
        🟠 Segment 2 (ex: Bientôt expirés)
        🟢 Segment 3 (ex: Valides)
        📊 Total au centre
    
    Usage:
        >>> segments = [
        ...     (25, "#e74c3c", "Expirés"),
        ...     (30, "#f39c12", "Bientôt"),
        ...     (45, "#27ae60", "Valides")
        ... ]
        >>> donut = MultiSegmentDonut(segments, total=4850)
    """
    
    def __init__(self, segments: List[Tuple[int, str, str]] = None, 
                 total: int = 0, taille: int = 140, parent=None):
        """
        Initialise le widget de donut multi-segments.
        
        Args:
            segments: Liste de tuples (pourcentage, couleur, label)
            total: Valeur totale à afficher au centre
            taille: Taille du widget en pixels
            parent: Widget parent Qt
        """
        super().__init__(parent)
        
        self.segments = segments or []
        self.total = total
        self.taille = taille

        self.setFixedSize(taille, taille)
        theme_manager.theme_changed.connect(self.update)
    
    def set_segments(self, segments: List[Tuple[int, str, str]], total: int = 0):
        """
        Met à jour les segments et redessine.
        
        Args:
            segments: Liste de tuples (pourcentage, couleur, label)
            total: Valeur totale à afficher au centre
        """
        self.segments = segments
        self.total = total
        self.update()  # Déclenche paintEvent
    
    def paintEvent(self, event):
        """
        Dessine le donut multi-segments.
        Appelé automatiquement par Qt lors du rafraîchissement.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dimensions
        width = self.width()
        height = self.height()
        size = min(width, height)
        
        # Rectangle pour le cercle
        margin = 10
        rect = QRect(margin, margin, size - 2*margin, size - 2*margin)
        
        # Épaisseur du donut
        pen_width = 16
        
        # Si aucun segment, afficher un cercle gris
        if not self.segments or sum(seg[0] for seg in self.segments) == 0:
            c = theme_manager.colors()
            pen_fond = QPen(QColor(c['border_light']))
            pen_fond.setWidth(pen_width)
            pen_fond.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_fond)
            painter.drawArc(rect, 0, 360 * 16)
        else:
            # Dessiner chaque segment
            start_angle = 90 * 16  # Commencer en haut (12h)
            
            for pourcentage, couleur, label in self.segments:
                if pourcentage > 0:
                    pen_segment = QPen(QColor(couleur))
                    pen_segment.setWidth(pen_width)
                    pen_segment.setCapStyle(Qt.FlatCap)
                    painter.setPen(pen_segment)
                    
                    # Calculer l'angle de balayage
                    span_angle = -int(pourcentage * 3.6 * 16)  # Négatif = sens horaire
                    
                    painter.drawArc(rect, start_angle, span_angle)
                    
                    # Mettre à jour l'angle de départ pour le prochain segment
                    start_angle += span_angle
        
        # Dessiner le total au centre
        if self.total > 0:
            c = theme_manager.colors()
            painter.setPen(QColor(c['text_primary']))  # Utiliser 'text_primary' au lieu de 'text'
            font = QFont()
            font.setPixelSize(28)
            font.setBold(True)
            painter.setFont(font)
            
            text = f"{self.total:,}".replace(',', ' ')
            painter.drawText(rect, Qt.AlignCenter, text)
