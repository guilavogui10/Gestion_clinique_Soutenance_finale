"""
Composant CarteFacture - Carte facture fournisseur avec informations et bouton détail.
Responsabilité : Afficher une facture avec ses informations clés et un bouton pour voir les détails.
Pattern : Component, Reusability.
"""

from typing import Dict, Any, Optional, Callable
import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from ..styles.facture_styles import FactureStyles
from views.shared.theme_manager import theme_manager


def _sep(couleur: str = None) -> QFrame:
    """Crée un séparateur horizontal.
    
    Args:
        couleur: Couleur du séparateur
    
    Returns:
        QFrame: Séparateur configuré
    """
    couleur = couleur or theme_manager.colors()['border_light']
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{couleur}; border:none;")
    return f


def _row_ic_val(icone_name: str, valeur: Any, couleur_ic: str = None, 
                couleur_val: str = None, gras: bool = False):
    """Crée une ligne icône + valeur.
    
    Args:
        icone_name: Nom de l'icône FontAwesome
        valeur: Valeur à afficher
        couleur_ic: Couleur de l'icône
        couleur_val: Couleur de la valeur
        gras: Si True, texte en gras
    
    Returns:
        QWidget: Widget configuré
    """
    from PySide6.QtWidgets import QWidget
    _c = theme_manager.colors()
    couleur_ic = couleur_ic or _c['text_muted']
    couleur_val = couleur_val or _c['text_muted']
    w = QWidget()
    w.setStyleSheet("background:transparent;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(5)
    
    ic = QLabel()
    ic.setPixmap(qta.icon(icone_name, color=couleur_ic).pixmap(QSize(11, 11)))
    ic.setStyleSheet(FactureStyles.icone_base())
    
    lbl = QLabel(str(valeur) if valeur else "—")
    poids = "700" if gras else "400"
    lbl.setStyleSheet(
        f"color:{couleur_val}; font-size:11px; font-weight:{poids};"
        f"background:transparent; border:none;"
    )
    lbl.setWordWrap(True)
    
    lay.addWidget(ic)
    lay.addWidget(lbl)
    lay.addStretch()
    return w


class CarteFacture(QFrame):
    """
    Carte facture fournisseur avec informations et bouton détail.
    
    Structure :
    ┌─────────────────────────────────────┐
    │ #FCF001                    [Détail] │
    │ ─────────────────────────────────── │
    │ 🏢 Fournisseur ABC                  │
    │ 📅 Date : 15/01/2024                │
    │ 💰 Montant : 150 000 GNF            │
    │ 💳 Mode : Espèces                   │
    └─────────────────────────────────────┘
    
    Usage:
        >>> carte = CarteFacture(row, on_voir_detail)
    """
    
    def __init__(self, row: Dict[str, Any], on_voir_detail: Callable, parent: Optional[QFrame] = None):
        """
        Initialise la carte facture.
        
        Args:
            row: Dictionnaire avec les données de la facture
            on_voir_detail: Callback pour afficher le détail
            parent: Widget parent Qt
        """
        super().__init__(parent)
        self.row = row
        self.on_voir_detail = on_voir_detail
        self.code_facture = row.get("code_facture_four", "")
        
        self.setStyleSheet(FactureStyles.card_produit())
        self.setSizePolicy(
            self.sizePolicy().Policy.Expanding,
            self.sizePolicy().Policy.Fixed
        )
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configure l'interface de la carte."""
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)
        
        # Ligne 1 : Code + Bouton détail
        ligne1 = QHBoxLayout()
        
        _c = theme_manager.colors()
        code_lbl = QLabel(f"#{self.code_facture}")
        code_lbl.setStyleSheet(
            f"color:{_c['primary']}; font-size:12px; font-weight:700;"
            f"background:transparent; border:none;"
        )
        
        btn_detail = QPushButton(
            qta.icon("fa5s.eye", color=_c['info']), "  Détail"
        )
        btn_detail.setFixedHeight(28)
        btn_detail.setCursor(Qt.PointingHandCursor)
        btn_detail.setStyleSheet(FactureStyles.bouton_detail())
        btn_detail.clicked.connect(
            lambda: self.on_voir_detail(self.code_facture, self.row)
        )
        
        ligne1.addWidget(code_lbl)
        ligne1.addStretch()
        ligne1.addWidget(btn_detail)
        lay.addLayout(ligne1)
        lay.addWidget(_sep())
        
        # Ligne 2 : Fournisseur
        fournisseur_nom = self.row.get("fournisseur_nom", "Fournisseur inconnu")
        fournisseur_prenom = self.row.get("fournisseur_prenom", "")
        fournisseur_complet = f"{fournisseur_nom} {fournisseur_prenom}".strip()
        
        lay.addWidget(_row_ic_val(
            "fa5s.truck",
            fournisseur_complet,
            _c['text_muted'], _c['text_primary'], gras=True
        ))
        
        # Ligne 3 : Date
        from datetime import datetime
        date_facture = self.row.get("date_facture_four")
        if isinstance(date_facture, datetime):
            date_str = date_facture.strftime("%d/%m/%Y")
        else:
            date_str = str(date_facture) if date_facture else "—"
        
        lay.addWidget(_row_ic_val(
            "fa5s.calendar-alt",
            f"Date : {date_str}",
            _c['text_muted'], _c['text_muted']
        ))
        
        # Ligne 4 : Montant
        montant = self.row.get("montant_total", 0)
        montant_format = f"{int(montant):,}".replace(",", " ") + " GNF"
        
        lay.addWidget(_row_ic_val(
            "fa5s.coins",
            f"Montant : {montant_format}",
            _c['primary'], _c['primary'], gras=True
        ))
        
        # Ligne 5 : Mode de paiement
        mode_paiement = self.row.get("mode_payement", "—")
        couleur_mode = _c['info'] if mode_paiement and mode_paiement != "—" else _c['text_muted']
        
        lay.addWidget(_row_ic_val(
            "fa5s.credit-card",
            f"Mode : {mode_paiement.capitalize() if mode_paiement else '—'}",
            couleur_mode, couleur_mode
        ))
