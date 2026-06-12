"""
Composant PanierForm - Formulaire de saisie des produits MODERNE.
Responsabilité : Gestion du formulaire de saisie avec composants UI/UX modernes.
Version E-COMMERCE : Spinner quantité, Date picker, Price input formaté.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QTimer
from views.shared.theme_manager import theme_manager
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QFrame, QLabel, QComboBox, QScrollArea
)
from ..styles.panier_styles import PanierStyles
from views.shared.theme_manager import theme_manager

# Import des composants modernes
from .modern_quantity_spinner import ModernQuantitySpinner
from .modern_date_picker import ModernDatePicker
from .modern_price_input import ModernPriceInput


class _ComboDown(QComboBox):
    """QComboBox qui force la liste déroulante à s'afficher toujours en bas."""
    def showPopup(self):
        super().showPopup()
        popup = self.view().window()
        QTimer.singleShot(0, lambda: popup.move(
            self.mapToGlobal(self.rect().bottomLeft())
        ))


class PanierForm:
    """
    Gère le formulaire de saisie des produits.
    Pattern : Facade pour simplifier la création du formulaire.
    """
    
    def __init__(self, vert_principal: str):
        self.vert_principal = vert_principal
        
        # Widgets du formulaire
        self.combo_fournisseur = None
        self.combo_produit = None
        self.input_designation = None
        self.input_quantite = None
        self.input_prix = None
        self.input_date_exp = None
        self.btn_ajouter_panier = None
        self.container_panier = None
        self.layout_lignes_panier = None
        self._body_scroll = None
        self._body = None
    
    def create(self, parent_layout, appliquer_style_scrollbar_callback, show_lignes: bool = True):
        """
        Crée le formulaire complet dans un QScrollArea.
        
        Args:
            parent_layout: Layout parent où ajouter le formulaire
            appliquer_style_scrollbar_callback: Fonction pour appliquer le style scrollbar
        
        Returns:
            tuple: (container_panier, layout_lignes_panier) pour la liste des lignes
        """
        body_scroll = QScrollArea()
        body_scroll.setWidgetResizable(True)
        body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        c = theme_manager.colors()
        body_scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {c['bg_card']}; }}")
        appliquer_style_scrollbar_callback(body_scroll)

        body = QWidget()
        body.setStyleSheet(f"background: {c['bg_card']};")
        self._body_scroll = body_scroll
        self._body = body
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 8, 12, 8)
        body_layout.setSpacing(8)

        # Section Fournisseur (pleine largeur)
        self._create_fournisseur_section(body_layout)
        
        # Séparateur
        self._ajouter_separateur(body_layout, "Détail du produit")
        
        # ✅ OPTIMISATION : Produit + Désignation côte à côte
        self._create_produit_designation_row(body_layout)
        
        # ✅ OPTIMISATION : Quantité + Prix + Date côte à côte
        self._create_quantite_prix_date_row(body_layout)
        
        # Bouton Ajouter (pleine largeur, plus visible)
        self._create_bouton_ajouter(body_layout)
        
        if show_lignes:
            # Séparateur
            self._ajouter_separateur(body_layout, "Articles en cours")
            
            # Container pour la liste des lignes panier
            self.container_panier = QWidget()
            self.container_panier.setStyleSheet("background: transparent;")
            self.layout_lignes_panier = QVBoxLayout(self.container_panier)
            self.layout_lignes_panier.setContentsMargins(0, 0, 0, 0)
            self.layout_lignes_panier.setSpacing(6)
            self.layout_lignes_panier.addStretch()
            body_layout.addWidget(self.container_panier)
        else:
            self.container_panier = None
            self.layout_lignes_panier = None

        body_scroll.setWidget(body)
        parent_layout.addWidget(body_scroll, stretch=1)
        
        return self.container_panier, self.layout_lignes_panier
    
    def _create_fournisseur_section(self, layout):
        """Crée la section fournisseur."""
        lbl_four = QLabel("Fournisseur")
        lbl_four.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {theme_manager.colors()['text_muted']};"
            "text-transform: uppercase; border: none; background: transparent;"
        )
        layout.addWidget(lbl_four)

        self.combo_fournisseur = _ComboDown()
        self.combo_fournisseur.addItem(
            qta.icon("fa5s.truck", color=self.vert_principal),
            "  Sélectionner un fournisseur..."
        )
        self.combo_fournisseur.setFixedHeight(34)
        self.combo_fournisseur.setStyleSheet(PanierStyles.combo_fournisseur(self.vert_principal))
        layout.addWidget(self.combo_fournisseur)
    
    def _create_produit_designation_row(self, layout):
        """✅ Crée Produit + Désignation côte à côte pour optimiser l'espace."""
        row = QHBoxLayout()
        row.setSpacing(10)
        
        # Colonne Produit (40%)
        col_produit = QVBoxLayout()
        col_produit.setSpacing(4)
        lbl_produit = QLabel("Produit")
        lbl_produit.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {theme_manager.colors()['text_muted']};"
            "text-transform: uppercase; border: none; background: transparent;"
        )
        self.combo_produit = _ComboDown()
        self.combo_produit.addItem(
            qta.icon("fa5s.pills", color=self.vert_principal),
            "  Choisir..."
        )
        self.combo_produit.setFixedHeight(38)
        self.combo_produit.setStyleSheet(PanierStyles.combo_produit(self.vert_principal))
        col_produit.addWidget(lbl_produit)
        col_produit.addWidget(self.combo_produit)
        
        # Colonne Désignation (60%)
        col_designation = QVBoxLayout()
        col_designation.setSpacing(4)
        lbl_designation = QLabel("Désignation")
        lbl_designation.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {theme_manager.colors()['text_muted']};"
            "text-transform: uppercase; border: none; background: transparent;"
        )
        self.input_designation = QLineEdit()
        self.input_designation.setPlaceholderText("Rempli automatiquement...")
        self.input_designation.setFixedHeight(38)
        self.input_designation.setReadOnly(True)
        self.input_designation.setStyleSheet(PanierStyles.input_readonly())
        col_designation.addWidget(lbl_designation)
        col_designation.addWidget(self.input_designation)
        
        row.addLayout(col_produit, 2)
        row.addLayout(col_designation, 3)
        layout.addLayout(row)
    
    def _create_quantite_prix_date_row(self, layout):
        """✅ Crée Quantité + Prix + Date côte à côte pour optimiser l'espace."""
        row = QHBoxLayout()
        row.setSpacing(10)

        # Quantité avec Spinner moderne (25%)
        col_qte = QVBoxLayout()
        col_qte.setSpacing(4)
        lbl_qte = QLabel("Quantité")
        lbl_qte.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {theme_manager.colors()['text_muted']};"
            "text-transform: uppercase; border: none; background: transparent;"
        )
        self.input_quantite = ModernQuantitySpinner(self.vert_principal)
        self.input_quantite.setMinimum(1)
        self.input_quantite.setMaximum(9999)
        self.input_quantite.setToolTip("Utilisez les boutons +/- pour ajuster la quantité")
        col_qte.addWidget(lbl_qte)
        col_qte.addWidget(self.input_quantite)

        # Prix avec formatage automatique (35%)
        col_prix = QVBoxLayout()
        col_prix.setSpacing(4)
        lbl_prix = QLabel("Prix unitaire")
        lbl_prix.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {theme_manager.colors()['text_muted']};"
            "text-transform: uppercase; border: none; background: transparent;"
        )
        self.input_prix = ModernPriceInput(self.vert_principal)
        self.input_prix.setPlaceholderText("0")
        self.input_prix.setToolTip("Le prix sera formaté automatiquement (ex: 5 000 GNF)")
        col_prix.addWidget(lbl_prix)
        col_prix.addWidget(self.input_prix)
        
        # Date d'expiration avec calendrier moderne (40%)
        col_date = QVBoxLayout()
        col_date.setSpacing(4)
        lbl_date = QLabel("Date d'expiration")
        lbl_date.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {theme_manager.colors()['text_muted']};"
            "text-transform: uppercase; border: none; background: transparent;"
        )
        self.input_date_exp = ModernDatePicker(self.vert_principal)
        self.input_date_exp.setPlaceholderText("Sélectionner...")
        self.input_date_exp.setToolTip("Cliquez sur l'icône calendrier pour sélectionner une date")
        col_date.addWidget(lbl_date)
        col_date.addWidget(self.input_date_exp)

        row.addLayout(col_qte, 2)
        row.addLayout(col_prix, 3)
        row.addLayout(col_date, 3)
        layout.addLayout(row)
    
    def _create_bouton_ajouter(self, layout):
        """Crée le bouton ajouter au panier avec style moderne et visible."""
        layout.addSpacing(4)
        
        self.btn_ajouter_panier = QPushButton(
            qta.icon("fa5s.cart-plus", color=theme_manager.colors()['text_inverse']), "  Ajouter au Panier"
        )
        self.btn_ajouter_panier.setFixedHeight(46)
        self.btn_ajouter_panier.setCursor(Qt.PointingHandCursor)
        self.btn_ajouter_panier.setStyleSheet(PanierStyles.btn_ajouter_modern(self.vert_principal))
        self.btn_ajouter_panier.setToolTip("Ajouter ce produit au panier d'approvisionnement")
        layout.addWidget(self.btn_ajouter_panier)
        
        layout.addSpacing(6)
    
    def _ajouter_separateur(self, layout: QVBoxLayout, texte: str):
        """Ajoute un séparateur moderne avec icône."""
        sep_row = QHBoxLayout()
        sep_row.setSpacing(8)
        sep_row.setContentsMargins(0, 8, 0, 8)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon("fa5s.grip-lines", color=theme_manager.colors()['text_muted']).pixmap(12, 12)
        )
        icon_lbl.setFixedSize(12, 12)
        icon_lbl.setStyleSheet("border: none; background: transparent;")

        lbl = QLabel(texte.upper())
        lbl.setStyleSheet(
            f"font-size: 9px; font-weight: 700; color: {theme_manager.colors()['text_muted']};"
            "letter-spacing: 1px; border: none; background: transparent;"
        )
        lbl.setFixedHeight(14)

        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet(
            f"background: qlineargradient("
            f"x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 transparent, "
            f"stop:0.5 {theme_manager.colors()['border']}, "
            f"stop:1 transparent"
            f"); border: none; border-radius: 1px;"
        )

        sep_row.addWidget(icon_lbl)
        sep_row.addWidget(lbl)
        sep_row.addWidget(line, 1)
        layout.addLayout(sep_row)
    
    def activer_formulaire(self):
        """Active tous les champs du formulaire."""
        self.combo_produit.setEnabled(True)
        self.input_quantite.setEnabled(True)
        self.input_prix.setEnabled(True)
        self.input_date_exp.setEnabled(True)
        self.btn_ajouter_panier.setEnabled(True)
    
    def desactiver_formulaire(self):
        """Désactive tous les champs du formulaire."""
        self.combo_produit.setEnabled(False)
        self.input_quantite.setEnabled(False)
        self.input_prix.setEnabled(False)
        self.input_date_exp.setEnabled(False)
        self.btn_ajouter_panier.setEnabled(False)
    
    def vider_formulaire(self):
        """Vide tous les champs du formulaire."""
        self.combo_produit.setCurrentIndex(0)
        self.input_designation.clear()
        self.input_quantite.clear()
        self.input_prix.clear()
        self.input_date_exp.clear()

    def apply_theme(self, c: dict):
        """Met à jour les couleurs selon le thème actif."""
        if self._body_scroll:
            self._body_scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {c['bg_card']}; }}")
        if self._body:
            self._body.setStyleSheet(f"background: {c['bg_card']};")
        self.vert_principal = c['primary']
        if self.combo_fournisseur:
            self.combo_fournisseur.setStyleSheet(PanierStyles.combo_fournisseur(c['primary']))
        if self.combo_produit:
            self.combo_produit.setStyleSheet(PanierStyles.combo_produit(c['primary']))
        if self.input_designation:
            self.input_designation.setStyleSheet(PanierStyles.input_readonly())
        if self.btn_ajouter_panier:
            self.btn_ajouter_panier.setStyleSheet(PanierStyles.btn_ajouter_modern(c['primary']))
        if self.input_quantite and hasattr(self.input_quantite, 'apply_theme'):
            self.input_quantite.apply_theme()
        if self.input_prix and hasattr(self.input_prix, 'apply_theme'):
            self.input_prix.apply_theme()
        if self.input_date_exp and hasattr(self.input_date_exp, 'apply_theme'):
            self.input_date_exp.apply_theme()
