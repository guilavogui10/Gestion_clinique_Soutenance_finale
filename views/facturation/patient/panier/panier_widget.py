"""
Widget Panier Produit - Version Refactorisée COMPLÈTE.
Architecture : MVC + Composition + Separation of Concerns.
Responsabilité : Orchestration des composants et gestion du workflow.
"""

from typing import Dict, Any, List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QLabel, QScrollArea, QWidget

# Composants UI
from .components.animated_frame import AnimatedFrame
from .components.panier_header import PanierHeader
from .components.panier_form import PanierForm
from .components.panier_footer import PanierFooter
from .components.panier_ligne_item import PanierLigneItem
from .components.modern_message_box import ModernMessageBox

# Handlers métier
from .handlers.data_loader import DataLoader
from .handlers.validation_handler import ValidationHandler
from .handlers.panier_operations import PanierOperations

# Styles
from .styles.panier_styles import PanierStyles
from views.shared.theme_manager import theme_manager


class PanierProduitWidget(AnimatedFrame):
    """
    Widget panier pour l'approvisionnement des produits.
    Version refactorisée avec architecture modulaire COMPLÈTE.
    
    Responsabilités :
    - Orchestration des composants UI
    - Gestion du workflow métier
    - Communication avec les contrôleurs MVC
    """

    def __init__(self, panier_ctrl=None, produit_ctrl=None, 
                 fournisseur_ctrl=None, facture_ctrl=None, parent=None,
                 layout_mode: str = "stacked"):
        super().__init__(parent)
        
        print("[PanierWidget] Initialisation version refactorisée")
        
        # Injection des contrôleurs (Architecture MVC)
        self.panier_ctrl = panier_ctrl
        self.produit_ctrl = produit_ctrl
        self.fournisseur_ctrl = fournisseur_ctrl
        self.facture_ctrl = facture_ctrl
        self.layout_mode = layout_mode
        
        # État du panier
        self.code_session = None
        self.code_facture_four = None
        self.lignes_panier = []
        
        # Initialisation des composants UI
        _c = theme_manager.colors()
        self.header_component = PanierHeader(_c['primary'])
        self.form_component = PanierForm(_c['primary'])
        self.footer_component = PanierFooter(_c['primary'])
        self.ligne_item_factory = PanierLigneItem(
            _c['primary'], 
            _c['danger']
        )
        
        # Initialisation des handlers métier
        self.data_loader = DataLoader(_c['primary'])
        self.validation_handler = ValidationHandler(panier_ctrl)
        self.operations = PanierOperations(panier_ctrl, facture_ctrl)
        
        # Construction de l'interface
        self._init_ui()
        self._connecter_signaux()
        
        # Thème dynamique
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def apply_theme(self):
        """Applique le thème actif au widget et ses sous-composants."""
        _c = theme_manager.colors()
        self.setStyleSheet(
            f"background-color: {_c['bg_card']}; border-radius: 18px;"
            f" border: 1px solid {_c['border']};"
        )
        self.header_component.apply_theme(_c)
        self.footer_component.apply_theme(_c)
        self.form_component.apply_theme(_c)
        self.ligne_item_factory.vert_principal = _c['primary']
        self.ligne_item_factory.rouge = _c['danger']
    
    def _init_ui(self):
        """Initialisation de l'interface utilisateur."""
        c = theme_manager.colors()
        self.setStyleSheet(
            f"background-color: {c['bg_card']}; border-radius: 18px;"
            f" border: 1px solid {c['border']};"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header avec badge
        self.badge_panier = self.header_component.create(layout)

        if self.layout_mode == "split":
            # Layout e-commerce : formulaire à gauche, panier à droite
            body_layout = QHBoxLayout()
            body_layout.setContentsMargins(10, 8, 10, 10)
            body_layout.setSpacing(12)

            # Colonne gauche : formulaire (scrollable) sans lignes
            left_frame = QFrame()
            left_frame.setStyleSheet("background: transparent; border: none;")
            left_layout = QVBoxLayout(left_frame)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(0)
            self.form_component.create(
                left_layout,
                self._appliquer_style_scrollbar,
                show_lignes=False
            )

            # Colonne droite : liste des lignes + footer
            right_frame = QFrame()
            right_frame.setStyleSheet("background: transparent; border: none;")
            right_layout = QVBoxLayout(right_frame)
            right_layout.setContentsMargins(0, 0, 0, 0)
            right_layout.setSpacing(8)

            # Titre panier
            title_row = QHBoxLayout()
            lbl = QLabel("Articles ajoutés")
            lbl.setStyleSheet(
                f"font-weight: bold; color: {theme_manager.colors()['primary']}; font-size: 12px;"
            )
            title_row.addWidget(lbl)
            title_row.addStretch()
            right_layout.addLayout(title_row)

            # Liste scrollable des lignes
            scroll_panier = QScrollArea()
            scroll_panier.setWidgetResizable(True)
            scroll_panier.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_panier.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            self._appliquer_style_scrollbar(scroll_panier)

            self.container_panier = QWidget()
            self.container_panier.setStyleSheet("background: transparent;")
            self.layout_lignes_panier = QVBoxLayout(self.container_panier)
            self.layout_lignes_panier.setContentsMargins(0, 0, 0, 0)
            self.layout_lignes_panier.setSpacing(6)
            self.layout_lignes_panier.addStretch()
            scroll_panier.setWidget(self.container_panier)
            right_layout.addWidget(scroll_panier, 1)

            # Footer avec total et boutons
            self.lbl_total_facture, self.btn_finaliser, self.btn_annuler_facture = \
                self.footer_component.create(right_layout)

            body_layout.addWidget(left_frame, 2)
            body_layout.addWidget(right_frame, 3)
            layout.addLayout(body_layout)
        else:
            # Layout classique empilé
            self.container_panier, self.layout_lignes_panier = self.form_component.create(
                layout,
                self._appliquer_style_scrollbar
            )

            # Footer avec total et boutons
            self.lbl_total_facture, self.btn_finaliser, self.btn_annuler_facture = \
                self.footer_component.create(layout)

        # Exposition des widgets du formulaire pour accès externe
        self.combo_fournisseur = self.form_component.combo_fournisseur
        self.combo_produit = self.form_component.combo_produit
        self.input_designation = self.form_component.input_designation
        self.input_quantite = self.form_component.input_quantite
        self.input_prix = self.form_component.input_prix
        self.input_date_exp = self.form_component.input_date_exp
        self.btn_ajouter_panier = self.form_component.btn_ajouter_panier
    
    def _connecter_signaux(self):
        """Connecte tous les signaux pour la validation en temps réel."""
        # Création automatique de la facture à la sélection du fournisseur
        self.combo_fournisseur.currentIndexChanged.connect(self._on_fournisseur_change)
        
        # Auto-remplissage de la désignation quand un produit est sélectionné
        self.combo_produit.currentIndexChanged.connect(self._on_produit_change)
        
        # Validation en temps réel des champs
        self.input_quantite.valueChanged.connect(
            lambda value: self.validation_handler.valider_quantite(self.input_quantite, str(value))
        )
        self.input_prix.textChanged.connect(
            lambda text: self.validation_handler.valider_prix(self.input_prix, text)
        )
        self.input_date_exp.dateChanged.connect(
            lambda text: self.validation_handler.valider_date(self.input_date_exp, text)
        )
        
        # Ajout au panier
        self.btn_ajouter_panier.clicked.connect(self._ajouter_au_panier)
        
        # Finalisation et annulation
        self.btn_finaliser.clicked.connect(self._finaliser_facture)
        self.btn_annuler_facture.clicked.connect(self._annuler_panier)
    
    def charger_donnees(self, code_session: str) -> None:
        """Charge les données nécessaires au panier."""
        print(f"[PanierWidget] charger_donnees appelé avec session={code_session}")
        self.code_session = code_session
        
        if self.fournisseur_ctrl:
            self.data_loader.charger_fournisseurs(
                self.fournisseur_ctrl, 
                self.combo_fournisseur, 
                code_session
            )
        
        if self.produit_ctrl:
            self.data_loader.charger_produits(
                self.produit_ctrl, 
                self.combo_produit
            )
    
    def _on_fournisseur_change(self, index: int) -> None:
        """Crée automatiquement la facture fournisseur dès la sélection."""
        code_fournisseur = self.combo_fournisseur.currentData()
        
        if not code_fournisseur or not self.facture_ctrl:
            self.code_facture_four = None
            self.form_component.desactiver_formulaire()
            return
        
        ok, result = self.operations.creer_facture_fournisseur(
            code_fournisseur, 
            self.code_session
        )
        
        if ok:
            self.code_facture_four = result
            self.form_component.activer_formulaire()
            self._afficher_message("Succès", f"Facture {result} créée", True)
        else:
            self._afficher_message("Erreur", result, False)
            self.form_component.desactiver_formulaire()
    
    def _on_produit_change(self, index: int) -> None:
        """Auto-remplissage de la désignation ET du prix."""
        code_produit = self.combo_produit.currentData()
        if code_produit:
            designation = self.operations.obtenir_designation_produit(code_produit)
            self.input_designation.setText(designation)
            self.input_designation.setStyleSheet(PanierStyles.input_valide())
            
            prix_achat = self.operations.obtenir_prix_achat_produit(code_produit)
            if prix_achat > 0:
                self.input_prix.blockSignals(True)
                self.input_prix.clear()
                self.input_prix.setText(str(int(prix_achat)) if prix_achat == int(prix_achat) else str(prix_achat))
                self.input_prix.blockSignals(False)
                self.input_prix.setStyleSheet(PanierStyles.input_valide())
        else:
            self.input_designation.clear()
            self.input_designation.setStyleSheet(PanierStyles.input_readonly())
            self.input_prix.clear()
    
    def _ajouter_au_panier(self) -> None:
        """Ajoute un produit au panier avec validation complète."""
        if not self.code_facture_four:
            self._afficher_message("Attention", "Veuillez sélectionner un fournisseur d'abord", False)
            return
        
        form_data = {
            'code_produit': self.combo_produit.currentData(),
            'code_facture_four': self.code_facture_four,
            'code_session': self.code_session,
            'designation': self.input_designation.text().strip(),
            'quantite': self.input_quantite.text().strip(),
            'prix': self.input_prix.text().strip(),
            'date_expiration': self.input_date_exp.text().strip()
        }
        
        ok, msg = self.operations.ajouter_ligne_panier(form_data)
        
        if ok:
            self._ajouter_ligne_visuelle(form_data)
            self.form_component.vider_formulaire()
            self._recalculer_total()
            self._afficher_message("Succès", msg, True)
        else:
            self._afficher_message("Erreur", msg, False)
    
    def _ajouter_ligne_visuelle(self, form_data: Dict[str, Any]) -> None:
        """Ajoute une ligne visuelle dans le panier."""
        ligne_widget = self.ligne_item_factory.create(
            form_data['designation'],
            int(form_data['quantite']),
            float(form_data['prix']),
            form_data['date_expiration'],
            form_data.get('code_panier_four', 'PFF_TEMP'),
            self._supprimer_ligne
        )
        
        self.lignes_panier.append(ligne_widget)
        
        count = self.layout_lignes_panier.count()
        self.layout_lignes_panier.insertWidget(count - 1, ligne_widget)
        
        self.badge_panier.setText(str(len(self.lignes_panier)))
    
    def _supprimer_ligne(self, ligne_widget: Any) -> None:
        """Supprime une ligne du panier (BDD + visuel)."""
        if not hasattr(ligne_widget, 'code_panier'):
            return
        
        ok, msg = self.operations.supprimer_ligne_panier(ligne_widget.code_panier, self)
        
        if ok:
            self.lignes_panier.remove(ligne_widget)
            ligne_widget.deleteLater()
            
            self.badge_panier.setText(str(len(self.lignes_panier)))
            self._recalculer_total()
            self._afficher_message("Succès", msg, True)
        else:
            if msg != "Suppression annulée":
                self._afficher_message("Erreur", msg, False)
    
    def _recalculer_total(self) -> None:
        """Recalcule et affiche le total du panier."""
        total = 0.0
        for ligne in self.lignes_panier:
            if hasattr(ligne, 'quantite') and hasattr(ligne, 'prix'):
                total += ligne.quantite * ligne.prix
        
        self.footer_component.update_total(total)
    
    def _finaliser_facture(self) -> None:
        """Finalise la facture et affiche le panneau de paiement."""
        print("[PanierWidget] _finaliser_facture appelé")
        
        if not self.lignes_panier:
            self._afficher_message("Attention", "Le panier est vide", False)
            return
        
        if not self.code_facture_four:
            self._afficher_message("Erreur", "Aucune facture en cours", False)
            return
        
        print(f"[PanierWidget] Finalisation facture {self.code_facture_four}")
        
        ok, msg = self.operations.finaliser_facture(
            self.code_facture_four,
            self.combo_fournisseur.currentData(),
            self.code_session,
            self
        )
        
        print(f"[PanierWidget] Résultat finalisation: ok={ok}, msg={msg}")
        
        if ok and msg == "SHOW_PAYMENT_PANEL":
            print("[PanierWidget] Recherche du parent GestionProduitsView...")
            # Trouver le parent GestionProduitsView (peut être plusieurs niveaux au-dessus)
            parent = self.parent()
            while parent:
                print(f"[PanierWidget] Vérification parent: {type(parent).__name__}")
                if hasattr(parent, 'show_payment_panel'):
                    print("[PanierWidget] Parent avec show_payment_panel trouvé, appel...")
                    parent.show_payment_panel()
                    return
                parent = parent.parent()
            
            print("[PanierWidget] ERREUR: Aucun parent avec show_payment_panel trouvé")
            self._afficher_message("Erreur", "Impossible d'afficher le panneau de paiement", False)
        elif not ok:
            if msg != "Finalisation annulée":
                self._afficher_message("Erreur", msg, False)
    
    def _annuler_panier(self) -> None:
        """Annule le panier en cours avec confirmation."""
        if not self.lignes_panier and not self.code_facture_four:
            return
        
        ok, msg = self.operations.annuler_facture(self.code_facture_four, self)
        
        if ok:
            self._reinitialiser_complet()
            self._afficher_message("Succès", msg, True)
        else:
            if msg != "Annulation annulée":
                self._afficher_message("Erreur", msg, False)
    
    def _reinitialiser_complet(self) -> None:
        """Réinitialise complètement le widget."""
        for ligne in self.lignes_panier:
            ligne.deleteLater()
        
        self.lignes_panier.clear()
        self.code_facture_four = None
        
        self.combo_fournisseur.setCurrentIndex(0)
        self.badge_panier.setText("0")
        self.footer_component.update_total(0)
        self.form_component.vider_formulaire()
        self.form_component.desactiver_formulaire()
    
    def _appliquer_style_scrollbar(self, widget: Any) -> None:
        """Applique le style personnalisé aux scrollbars."""
        widget.verticalScrollBar().setStyleSheet(PanierStyles.scrollbar())
    
    def _afficher_message(self, titre: str, message: str, succes: bool) -> None:
        """Affiche un message à l'utilisateur."""
        if succes:
            ModernMessageBox.success(self, titre, message, theme_manager.colors()['primary'])
        else:
            ModernMessageBox.error(self, titre, message, theme_manager.colors()['primary'])
