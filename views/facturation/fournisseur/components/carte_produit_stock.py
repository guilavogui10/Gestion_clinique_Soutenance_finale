"""
Composant CarteProduitStock - Carte produit avec informations stock et bouton détail.
Responsabilité : Afficher un produit avec son stock et un bouton pour voir les détails.
Pattern : Component, Reusability.
"""

from typing import Dict, Any, Optional, Callable
import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget

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


class CarteProduitStock(QFrame):
    """
    Carte produit avec informations de stock et bouton détail.
    
    Structure :
    ┌─────────────────────────────────────┐
    │ #PRD001                    [Détail] │
    │ ─────────────────────────────────── │
    │ 📦 Paracétamol 500mg               │
    │ 💧 Liquide                          │
    │ 📊 Stock : 150 unités               │
    │ ✅ Valides : 120 | ❌ Expirés : 30 │
    └─────────────────────────────────────┘
    
    Usage:
        >>> carte = CarteProduitStock(row, ctrl, on_voir_detail)
    """
    
    def __init__(self, row: Dict[str, Any], ctrl: Any, on_voir_detail: Callable, parent: Optional[QWidget] = None):
        """
        Initialise la carte produit.
        
        Args:
            row: Dictionnaire avec les données du produit
            ctrl: Contrôleur panier
            on_voir_detail: Callback pour afficher le détail
            parent: Widget parent Qt
        """
        super().__init__(parent)
        self.ctrl = ctrl
        self.row = row
        self.on_voir_detail = on_voir_detail
        self.code_produit = row.get("code_produit") or row.get("code", "")
        
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
        code_lbl = QLabel(f"#{self.code_produit}")
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
            lambda: self.on_voir_detail(self.code_produit, self.row)
        )
        
        ligne1.addWidget(code_lbl)
        ligne1.addStretch()
        ligne1.addWidget(btn_detail)
        lay.addLayout(ligne1)
        lay.addWidget(_sep())
        
        # Ligne 2 : Libellé produit
        libelle = self.row.get("designation") or self.row.get("libelle", "Produit inconnu")
        lay.addWidget(_row_ic_val(
            "fa5s.box",
            libelle,
            _c['text_muted'], _c['text_primary'], gras=True
        ))
        
        # Ligne 3 : Type produit
        type_produit = self.row.get("type", "—")
        couleur_type = FactureStyles.obtenir_couleur_type(type_produit)
        lay.addWidget(_row_ic_val(
            "fa5s.tag",
            f"Type : {type_produit}",
            couleur_type, couleur_type
        ))
        
        # Ligne 4 : Stock total
        stock_total = self.row.get("quantite_stock") or self.row.get("stock_total", 0)
        lay.addWidget(_row_ic_val(
            "fa5s.layer-group",
            f"Stock total : {stock_total} unités",
            _c['text_muted'], _c['text_muted'], gras=True
        ))
        
        # Ligne 5 : Détail des quantités par statut
        qte_valide = self.row.get("qte_valide", 0)
        qte_a_expirer = self.row.get("qte_a_expirer", 0)
        qte_expire = self.row.get("qte_expire", 0)
        
        # Valide (toujours afficher)
        lay.addWidget(_row_ic_val(
            "fa5s.check-circle",
            f"Valide : {qte_valide} unité{'s' if qte_valide > 1 else ''}",
            _c['success'], _c['success']
        ))
        
        # À expirer (toujours afficher avec jours restants si > 0)
        jours_restants = self.row.get("jours_restants")
        texte_jours = f" (expire dans {jours_restants} jour{'s' if jours_restants > 1 else ''})" if qte_a_expirer > 0 and jours_restants is not None else ""
        lay.addWidget(_row_ic_val(
            "fa5s.exclamation-triangle",
            f"À expirer : {qte_a_expirer} unité{'s' if qte_a_expirer > 1 else ''}{texte_jours}",
            _c['warning'], _c['warning'], gras=(qte_a_expirer > 0)
        ))
        
        # Expiré (toujours afficher)
        lay.addWidget(_row_ic_val(
            "fa5s.times-circle",
            f"Expiré : {qte_expire} unité{'s' if qte_expire > 1 else ''}",
            _c['danger'], _c['danger']
        ))
