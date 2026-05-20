"""
Handler PrescriptionOperations.
Responsabilité : Opérations CRUD sur le panier prescription.
Pattern : Service Layer pour encapsuler la logique métier.

Différences vs PanierOperations :
  - creer_facture_fournisseur()    → supprimé
  - finaliser_facture()            → valider_prescription() (confirmation simple)
  - annuler_facture()              → annuler_prescription()
  - date_expiration                → jamais manipulée ici (FEFO auto dans DAO)
  - actualiser_prix_achat()        → supprimé (prix vente readonly)
  - Le modèle instancié ici        → PanierPrescriptionProduit
"""

import logging
from typing import Tuple, Dict, Any

from views.shared.message_box import CustomMessageBox


class PrescriptionOperations:
    """
    Gère les opérations CRUD sur le panier prescription.
    Encapsule la logique métier et les appels au contrôleur.
    """

    def __init__(self, prescription_ctrl):
        """
        Args:
            prescription_ctrl: PrescriptionControleur (injecté depuis le widget)
        """
        self.ctrl   = prescription_ctrl
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # AJOUTER
    # =========================================================================

    def ajouter_ligne_prescription(self, form_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valide et ajoute une ligne de prescription.

        Flux :
          1. Contrôle des champs obligatoires
          2. Conversion des types
          3. Instanciation du modèle PanierPrescriptionProduit
          4. Appel ctrl.ajouter_ligne() → vérifie stock + FEFO + insert

        Args:
            form_data: {
                'code_produit'    : str,
                'code_session'    : str,
                'code_visite'     : str,
                'code_consultation': str,
                'designation'     : str,   # peut être vide → auto-complété par DAO
                'quantite'        : int,
                'prix'            : float, # peut être 0 → auto-complété par DAO
            }

        Returns:
            Tuple[bool, str]: (succès, message)
        """
        # Lazy import pour éviter les imports circulaires
        from models.modele_panier_prescription_produit import PanierPrescriptionProduit

        try:
            # 1. Vérifications minimales côté handler
            if not form_data.get('code_produit'):
                return False, "Veuillez sélectionner un produit."

            if not form_data.get('code_acte'):
                return False, "Aucun acte médical actif pour ce patient."

            quantite = int(form_data.get('quantite', 0))
            if quantite <= 0:
                return False, "La quantité doit être supérieure à 0."

            # 2. Conversion prix (peut être 0 — DAO auto-complétera)
            try:
                prix = float(str(form_data.get('prix', '0')).replace(" ", ""))
            except (ValueError, TypeError):
                prix = 0.0

            # 3. Instanciation du modèle
            prescription = PanierPrescriptionProduit(
                code_prescription         = None,           # Généré par DAO
                designation              = form_data.get('designation', ''),
                code_produit             = form_data['code_produit'],
                quantite_prescript       = quantite,
                prix_applique            = prix,
                date_expiration          = None,           # FEFO automatique
                code_acte                = form_data['code_acte'],
                code_session             = form_data['code_session'],
            )

            # 4. Délégation au contrôleur (validation + stock + FEFO + insert)
            ok, msg = self.ctrl.ajouter_ligne(prescription)

            if ok:
                # Mettre à jour form_data avec les allocations FEFO (si multi-lots)
                allocations = getattr(prescription, 'allocations', None)
                if allocations:
                    form_data['allocations'] = []
                    for alloc in allocations:
                        form_data['allocations'].append({
                            'designation':     prescription.designation,
                            'quantite':        alloc.get('quantite', 0),
                            'prix':            prescription.prix_applique,
                            'date_expiration': alloc.get('date_expiration'),
                            'code_prescription': alloc.get('code_prescription', 'PRS_TEMP')
                        })

                    # Fallback: première allocation pour compatibilité
                    premier = form_data['allocations'][0]
                    form_data['code_prescription'] = premier.get('code_prescription', 'PRS_TEMP')
                    form_data['date_expiration']   = premier.get('date_expiration')
                    form_data['prix']              = premier.get('prix', prescription.prix_applique)
                    form_data['designation']       = premier.get('designation', prescription.designation)
                else:
                    # Mettre à jour form_data avec le code généré pour affichage
                    form_data['code_prescription'] = (
                        prescription.code_prescription or "PRS_TEMP"
                    )
                    form_data['date_expiration'] = prescription.date_expiration
                    form_data['prix']            = prescription.prix_applique
                    form_data['designation']     = prescription.designation
                return True, "Produit prescrit avec succès."
            else:
                return False, msg

        except ValueError as e:
            self.logger.error(f"Valeurs invalides: {e}", exc_info=True)
            return False, f"Valeurs invalides : {e}"
        except Exception as e:
            self.logger.error(f"Erreur ajouter_ligne_prescription: {e}", exc_info=True)
            return False, f"Erreur lors de l'ajout : {e}"

    # =========================================================================
    # SUPPRIMER
    # =========================================================================

    def supprimer_ligne_prescription(self, code_prescription: str,
                                      parent_widget) -> Tuple[bool, str]:
        """
        Supprime une ligne prescription avec confirmation utilisateur.

        Args:
            code_prescription : Code PRS de la ligne à supprimer
            parent_widget     : Widget parent pour la boîte de dialogue

        Returns:
            Tuple[bool, str]: (succès, message)
        """
        confirmed = CustomMessageBox.question(
            parent_widget,
            "Confirmation",
            "Voulez-vous supprimer ce produit de la prescription ?"
        )

        if not confirmed:
            return False, "Suppression annulée"

        ok, msg = self.ctrl.supprimer_ligne(code_prescription)

        if ok:
            return True, "Ligne supprimée de la prescription."
        return False, msg

    # =========================================================================
    # VALIDER
    # =========================================================================

    def valider_prescription(self, code_acte: str,
                              parent_widget) -> Tuple[bool, str]:
        """
        Valide la prescription en cours avec confirmation.
        Le statut_patient de la visite passe à 'Attente payement' via le DAO.

        Args:
            code_acte         : Code de l'acte médical en cours
            parent_widget     : Widget parent pour la boîte de dialogue

        Returns:
            Tuple[bool, str]: (succès, message)
        """
        if not code_acte:
            return False, "Aucun acte médical actif."

        confirmed = CustomMessageBox.confirm(
            parent_widget,
            "Confirmation",
            "Confirmer la prescription ?\n"
            "Le patient sera dirigé vers le service de paiement."
        )

        if not confirmed:
            return False, "Validation annulée"

        # La prescription est déjà enregistrée ligne par ligne.
        # Ici on finalise : passage du statut_patient à 'Attente payement'.
        ok, msg = self.ctrl.valider_prescription_visite(code_acte)
        return ok, msg

    # =========================================================================
    # ANNULER
    # =========================================================================

    def annuler_prescription(self, lignes_prescriptions: list,
                              parent_widget) -> Tuple[bool, str]:
        """
        Annule la prescription en cours : supprime toutes les lignes avec confirmation.

        Args:
            lignes_prescriptions : Liste des widgets ligne (ont un attr code_prescription)
            parent_widget        : Widget parent pour la boîte de dialogue

        Returns:
            Tuple[bool, str]: (succès, message)
        """
        if not lignes_prescriptions:
            return False, "Aucune ligne à annuler."

        confirmed = CustomMessageBox.question(
            parent_widget,
            "Confirmation",
            f"Supprimer les {len(lignes_prescriptions)} ligne(s) de la prescription ?\n"
            "Cette action est irréversible."
        )

        if not confirmed:
            return False, "Annulation annulée"

        erreurs = 0
        for ligne in lignes_prescriptions:
            if hasattr(ligne, 'code_prescription') and ligne.code_prescription:
                ok, _ = self.ctrl.supprimer_ligne(ligne.code_prescription)
                if not ok:
                    erreurs += 1

        if erreurs:
            return False, f"{erreurs} ligne(s) n'ont pas pu être supprimées."

        return True, "Prescription annulée."

    # =========================================================================
    # INFOS PRODUIT (auto-remplissage)
    # =========================================================================

    def obtenir_infos_produit(self, code_produit: str) -> Tuple[str, float]:
        """
        Retourne (designation, prix_vente_unitaire) pour auto-remplir le formulaire.

        Args:
            code_produit: Code du produit sélectionné dans le combo

        Returns:
            Tuple[str, float]: (designation, prix)
        """
        if self.ctrl:
            return self.ctrl.obtenir_infos_produit(code_produit)
        return "", 0.0
