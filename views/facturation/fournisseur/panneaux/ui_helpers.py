"""
Helpers UI partagés pour les panneaux du module facture_fournisseur.
Responsabilité : Fournir les widgets et fonctions utilitaires réutilisables.
Pattern : Utility, DRY.
"""

from typing import Optional
import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPainter, QPainterPath, QBrush
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea

from ..styles.facture_styles import FactureStyles


# =============================================================================
# FOND ARRONDI
# =============================================================================
class FondArrondi(QWidget):
    """Widget de base avec fond coloré et coins arrondis."""

    def __init__(self, rayon: int = 20,
                 couleur_fond: str = FactureStyles.BLANC,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._rayon       = rayon
        self._couleur_fond = QColor(couleur_fond)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(
            self.rect().adjusted(1, 1, -1, -1),
            self._rayon, self._rayon
        )
        painter.fillPath(path, QBrush(self._couleur_fond))
        painter.end()


# =============================================================================
# HELPERS FONCTIONS
# =============================================================================
def lbl_vide(texte: str) -> QWidget:
    """
    Crée un widget centré avec icône + message pour état vide.

    Args:
        texte: Message à afficher

    Returns:
        QWidget: Widget centré avec icône inbox et texte
    """
    w = QWidget()
    w.setStyleSheet("background:transparent;")
    lay = QVBoxLayout(w)
    lay.setAlignment(Qt.AlignCenter)
    lay.setSpacing(10)

    ic = QLabel()
    ic.setPixmap(
        qta.icon("fa5s.inbox",
                 color=FactureStyles.GRIS_CLAIR).pixmap(QSize(36, 36))
    )
    ic.setAlignment(Qt.AlignCenter)
    ic.setStyleSheet("background:transparent;")

    lbl = QLabel(texte)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        f"color:{FactureStyles.GRIS_TEXTE}; font-size:12px; "
        f"font-style:italic; background:transparent; padding:4px;"
    )

    lay.addWidget(ic)
    lay.addWidget(lbl)
    return w


def scroll_wrap(inner_widget: QWidget) -> QScrollArea:
    """
    Enveloppe un widget dans un QScrollArea sans bordure.

    Args:
        inner_widget: Widget à envelopper

    Returns:
        QScrollArea: Scroll configuré
    """
    scroll = QScrollArea()
    from views.shared.theme_manager import theme_manager
    _bg = theme_manager.colors()['bg_card']
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setStyleSheet(
        f"QScrollArea {{ border: none; background: {_bg}; }}"
        f"QScrollArea > QWidget {{ background: {_bg}; }}"
    )
    scroll.verticalScrollBar().setStyleSheet(FactureStyles.scrollbar())
    scroll.setWidget(inner_widget)
    return scroll


def separateur_h(couleur: str = FactureStyles.GRIS_CLAIR) -> QFrame:
    """
    Crée un séparateur horizontal fin.

    Args:
        couleur: Couleur du séparateur

    Returns:
        QFrame: Séparateur configuré
    """
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background:{couleur}; border:none;")
    return sep