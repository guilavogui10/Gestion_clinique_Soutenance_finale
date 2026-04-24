"""
Composant LigneLotCard - Ligne de lot dans la vue détail produit.
Responsabilité : Afficher un lot avec sa date d'expiration et son statut.
Pattern : Component, List Item.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from ..styles.facture_styles import FactureStyles
from views.shared.theme_manager import theme_manager


def _fmt_date(val):
    """Formate une date."""
    if val and hasattr(val, "strftime"):
        return val.strftime("%d/%m/%Y")
    return str(val) if val else "—"


class LigneLotCard(QFrame):
    """
    Ligne représentant un lot de produit.
    
    Structure :
    ┌─────────────────────────────────────────────────┐
    │ [VALIDE] 📅 31/12/2025  |  📦 50 unités         │
    └─────────────────────────────────────────────────┘
    
    Usage:
        >>> ligne = LigneLotCard(date_exp, quantite, statut)
    """
    
    def __init__(self, date_expiration, quantite: int, statut: str = "valide", jours_restants: int = None, parent=None):
        """
        Initialise la ligne de lot.
        
        Args:
            date_expiration: Date d'expiration du lot
            quantite: Quantité dans le lot
            statut: Statut du lot (valide, expire, bientot)
            jours_restants: Nombre de jours avant expiration (optionnel)
            parent: Widget parent Qt
        """
        super().__init__(parent)
        
        self.date_expiration = date_expiration
        self.quantite = quantite
        self.statut = statut.lower()
        self.jours_restants = jours_restants
        
        self.setStyleSheet(FactureStyles.ligne_lot())
        self.setFixedHeight(36)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface de la ligne."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)
        
        _c = theme_manager.colors()
        # Badge statut
        badge = self._creer_badge()
        layout.addWidget(badge)
        
        # Icône + Date expiration
        ic_date = QLabel()
        ic_date.setPixmap(
            qta.icon("fa5s.calendar-alt", color=_c['text_muted']).pixmap(QSize(11, 11))
        )
        ic_date.setStyleSheet(FactureStyles.icone_base())
        
        date_lbl = QLabel(_fmt_date(self.date_expiration))
        date_lbl.setStyleSheet(
            f"color:{_c['text_muted']}; font-size:11px; font-weight:600;"
            f"background:transparent; border:none;"
        )
        
        layout.addWidget(ic_date)
        layout.addWidget(date_lbl)
        layout.addStretch()
        
        # Séparateur vertical
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background:{_c['border_light']}; border:none;")
        layout.addWidget(sep)
        
        # Icône + Quantité
        ic_qte = QLabel()
        ic_qte.setPixmap(
            qta.icon("fa5s.boxes", color=_c['text_muted']).pixmap(QSize(11, 11))
        )
        ic_qte.setStyleSheet(FactureStyles.icone_base())
        
        qte_lbl = QLabel(f"{self.quantite} unités")
        qte_lbl.setStyleSheet(
            f"color:{_c['text_muted']}; font-size:11px; font-weight:600;"
            f"background:transparent; border:none;"
        )
        
        layout.addWidget(ic_qte)
        layout.addWidget(qte_lbl)
        
        # Afficher les jours restants si statut = bientôt
        if self.statut == "bientot" and self.jours_restants is not None:
            layout.addSpacing(8)
            ic_clock = QLabel()
            ic_clock.setPixmap(
                qta.icon("fa5s.clock", color=_c['warning']).pixmap(QSize(11, 11))
            )
            ic_clock.setStyleSheet(FactureStyles.icone_base())
            
            jours_lbl = QLabel(f"{self.jours_restants}j")
            jours_lbl.setStyleSheet(
                f"color:{_c['warning']}; font-size:10px; font-weight:700;"
                f"background:transparent; border:none;"
            )
            
            layout.addWidget(ic_clock)
            layout.addWidget(jours_lbl)
    
    def _creer_badge(self) -> QLabel:
        """Crée le badge de statut."""
        couleur_bg, couleur_text = FactureStyles.obtenir_couleur_statut(self.statut)
        
        texte_statut = {
            "valide":  "VALIDE",
            "expire":  "EXPIRÉ",
            "bientot": "BIENTÔT"
        }.get(self.statut, "INCONNU")
        
        badge = QLabel(texte_statut)
        badge.setFixedWidth(65)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(FactureStyles.label_badge(couleur_bg, couleur_text))
        
        return badge
