"""
Handler PanierOperations - Opérations CRUD sur le panier.
Responsabilité : Gestion des opérations métier (ajouter, supprimer, finaliser).
Pattern : Service Layer pour encapsuler la logique métier.
"""

import logging
from typing import Tuple, Dict, Any
from datetime import datetime
from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt
from views.shared.message_box import CustomMessageBox
from ..components.payment_slide_panel import PaymentSlidePanel


class PanierOperations:
    """
    Gère les opérations CRUD sur le panier.
    Encapsule la logique métier et les appels aux contrôleurs.
    """
    
    def __init__(self, panier_ctrl, facture_ctrl):
        """
        Initialise le handler avec les contrôleurs nécessaires.
        
        Args:
            panier_ctrl: Contrôleur du panier
            facture_ctrl: Contrôleur des factures fournisseur
        """
        self.panier_ctrl = panier_ctrl
        self.facture_ctrl = facture_ctrl
        self.logger = logging.getLogger(__name__)
    
    def creer_facture_fournisseur(self, code_fournisseur: str, code_session: str) -> Tuple[bool, str]:
        """
        Crée une nouvelle facture fournisseur.
        
        Args:
            code_fournisseur: Code du fournisseur sélectionné
            code_session: Code de la session active
        
        Returns:
            tuple: (succès, code_facture ou message d'erreur)
        """
        from models.modele_factureFournisseur import FactureFournisseur
        
        facture = FactureFournisseur(
            code_facture_four="",  # Généré par le DAO
            code_fournisseur=code_fournisseur,
            code_session=code_session,
            date_facture_four=datetime.now(),
            montant_total=0,  # Sera recalculé automatiquement
            mode_payement="",  # Rempli à la finalisation
            telephone=""  # Rempli à la finalisation
        )
        
        return self.facture_ctrl.creer_facture(facture)
    
    def ajouter_ligne_panier(self, form_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Ajoute une ligne au panier.
        
        Args:
            form_data: Dictionnaire contenant les données du formulaire
                {
                    'code_produit': str,
                    'code_facture_four': str,
                    'code_session': str,
                    'designation': str,
                    'quantite': int,
                    'prix': float,
                    'date_expiration': str
                }
        
        Returns:
            Tuple[bool, str]: (succès, message)
        """
        from models.modele_panier_fourni import PanierFactureFourni
        
        try:
            # Validation des données
            if not form_data.get('code_produit'):
                return False, "Veuillez sélectionner un produit"
            
            if not form_data.get('quantite'):
                return False, "Veuillez saisir la quantité"
            
            if not form_data.get('prix'):
                return False, "Veuillez saisir le prix unitaire"
            
            if not form_data.get('date_expiration'):
                return False, "Veuillez saisir la date d'expiration"
            
            # Conversion des types
            quantite = int(form_data['quantite'])
            prix = float(str(form_data['prix']).replace(" ", ""))
            
            # Conversion de la date DD/MM/YYYY vers YYYY-MM-DD (format MySQL)
            date_str = form_data['date_expiration']
            try:
                # Si la date est au format DD/MM/YYYY
                if '/' in date_str:
                    date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                    date_mysql = date_obj.strftime("%Y-%m-%d")
                else:
                    # Si déjà au format YYYY-MM-DD, valider quand même
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    date_mysql = date_str
            except ValueError as e:
                self.logger.error(f"Format de date invalide: {date_str} - {e}")
                return False, f"Format de date invalide (attendu: JJ/MM/AAAA)"
            
            # Création de l'objet panier
            panier = PanierFactureFourni(
                code_panier_four="",  # Généré par le DAO
                code_produit=form_data['code_produit'],
                code_facture_four=form_data['code_facture_four'],
                code_session=form_data['code_session'],
                designation=form_data['designation'],
                quantite_four=quantite,
                prix_unitaire=prix,
                date_expiration=date_mysql  # Format MySQL
            )
            
            # Appel du contrôleur
            ok, msg = self.panier_ctrl.ajouter_ligne(panier)
            
            if ok:
                # ✅ NOUVEAU : Mettre à jour le prix d'achat du produit si différent
                code_produit = form_data['code_produit']
                prix_saisi = prix
                
                # Récupérer le prix actuel du catalogue
                prix_catalogue = self.obtenir_prix_achat_produit(code_produit)
                
                # Si le prix saisi est différent du prix catalogue, mettre à jour
                if prix_catalogue > 0 and abs(prix_saisi - prix_catalogue) > 0.01:  # Tolérance de 0.01
                    ok_maj, msg_maj = self.actualiser_prix_achat_produit(code_produit, prix_saisi)
                    if ok_maj:
                        self.logger.info(f"Prix achat produit {code_produit} mis à jour: {prix_catalogue} → {prix_saisi}")
                    else:
                        self.logger.warning(f"Échec mise à jour prix produit {code_produit}: {msg_maj}")
                
                # Récupérer le code généré
                form_data['code_panier_four'] = panier.code_panier_four or "PFF_TEMP"
                return True, "Produit ajouté au panier"
            else:
                return False, msg
                
        except ValueError as e:
            self.logger.error(f"Valeurs invalides lors de l'ajout: {e}", exc_info=True)
            return False, f"Valeurs invalides: {e}"
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout au panier: {e}", exc_info=True)
            return False, f"Erreur lors de l'ajout: {e}"
    
    def supprimer_ligne_panier(self, code_panier: str, parent_widget) -> Tuple[bool, str]:
        """
        Supprime une ligne du panier avec confirmation.
        
        Args:
            code_panier: Code de la ligne à supprimer
            parent_widget: Widget parent pour la boîte de dialogue
        
        Returns:
            tuple: (succès, message)
        """
        # Confirmation utilisateur avec dialogue moderne
        confirmed = CustomMessageBox.question(
            parent_widget,
            "Confirmation",
            "Voulez-vous vraiment supprimer cette ligne du panier ?"
        )
        
        if not confirmed:
            return False, "Suppression annulée"
        
        # Suppression en BDD
        ok, msg = self.panier_ctrl.supprimer_ligne(code_panier)
        
        if ok:
            return True, "Ligne supprimée du panier"
        else:
            return False, msg
    
    def finaliser_facture(self, code_facture_four: str, code_fournisseur: str, 
                         code_session: str, parent_widget) -> Tuple[bool, str]:
        """
        Finalise la facture avec panneau de paiement glissant.
        
        Args:
            code_facture_four: Code de la facture à finaliser
            code_fournisseur: Code du fournisseur
            code_session: Code de la session
            parent_widget: Widget parent pour le panneau
        
        Returns:
            tuple: (succès, message)
        """
        # Récupérer les données de la facture
        facture_data = self.facture_ctrl.obtenir_par_code(code_facture_four)
        if not facture_data:
            return False, "Facture introuvable"
        
        # Récupérer les produits du panier
        produits_data = self.panier_ctrl.lister_par_facture(code_facture_four)
        if not produits_data:
            return False, "Aucun produit dans le panier"
        
        # Récupérer les infos fournisseur
        from controllers.controleur_fournisseur import FournisseurControleur
        fournisseur_ctrl = FournisseurControleur()
        fournisseur_data = fournisseur_ctrl.obtenir_par_code(code_fournisseur)
        
        # Stocker les données pour le panneau
        parent_widget._payment_facture_data = facture_data
        parent_widget._payment_produits_data = produits_data
        parent_widget._payment_fournisseur_data = fournisseur_data
        parent_widget._payment_code_facture = code_facture_four
        parent_widget._payment_code_fournisseur = code_fournisseur
        parent_widget._payment_code_session = code_session
        
        # Retourner succès pour que le panier se ferme
        return True, "SHOW_PAYMENT_PANEL"
    
    def annuler_facture(self, code_facture_four: str, parent_widget) -> Tuple[bool, str]:
        """
        Annule la facture en cours avec confirmation.
        
        Args:
            code_facture_four: Code de la facture à annuler
            parent_widget: Widget parent pour la boîte de dialogue
        
        Returns:
            tuple: (succès, message)
        """
        # Confirmation avec dialogue moderne
        confirmed = CustomMessageBox.question(
            parent_widget,
            "Confirmation",
            "Voulez-vous vraiment annuler cette facture ?\nToutes les lignes seront supprimées."
        )
        
        if not confirmed:
            return False, "Annulation annulée"
        
        # Suppression de la facture (cascade sur les lignes)
        ok, msg = self.facture_ctrl.supprimer_facture(code_facture_four)
        
        if ok:
            return True, "Facture annulée"
        else:
            return False, msg
    
    def obtenir_designation_produit(self, code_produit: str) -> str:
        """
        Obtient la désignation d'un produit.
        
        Args:
            code_produit: Code du produit
        
        Returns:
            str: Désignation du produit
        """
        if self.panier_ctrl:
            return self.panier_ctrl.obtenir_designation_produit(code_produit)
        return ""
    
    def obtenir_prix_achat_produit(self, code_produit: str) -> float:
        """
        Obtient le prix d'achat unitaire d'un produit.
        Utilise pour auto-remplir le champ prix dans le panier.
        
        Args:
            code_produit: Code du produit
        
        Returns:
            float: Prix d'achat unitaire ou 0.0
        """
        if self.panier_ctrl:
            return self.panier_ctrl.obtenir_prix_achat_produit(code_produit)
        return 0.0
    
    def actualiser_prix_achat_produit(self, code_produit: str, nouveau_prix: float) -> Tuple[bool, str]:
        """
        Met a jour le prix d'achat d'un produit apres validation du panier.
        Appele uniquement si le prix fournisseur est different du prix catalogue.
        
        Args:
            code_produit: Code du produit
            nouveau_prix: Nouveau prix d'achat unitaire
        
        Returns:
            Tuple[bool, str]: (succes, message)
        """
        if self.panier_ctrl:
            return self.panier_ctrl.actualiser_prix_achat_produit(code_produit, nouveau_prix)
        return False, "Contrôleur panier non initialisé"
