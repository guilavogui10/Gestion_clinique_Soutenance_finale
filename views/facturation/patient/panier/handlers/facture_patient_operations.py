"""
Operations metier pour facture patient.
Responsabilite : generation facture, CRUD lignes, paiement, annulation.
"""

from __future__ import annotations

import logging
from typing import Tuple, Dict, Any

from views.shared.message_box import CustomMessageBox
from views.shared.theme_manager import theme_manager
from ..components.facture_patient_invoice_dialog import FacturePatientInvoiceDialog
from models.modele_panier_facture import PanierFacture


class FacturePatientOperations:
    """Service layer pour la facture patient."""

    def __init__(self, facture_ctrl, panier_ctrl, couleur=None):
        self.facture_ctrl = facture_ctrl
        self.panier_ctrl = panier_ctrl
        self._couleur = couleur

    @property
    def couleur(self):
        return self._couleur or theme_manager.colors()['primary']
        self.logger = logging.getLogger(__name__)

    def generer_facture(self, code_visite: str, telephone: str = "",
                        creer_panier: bool = True) -> Tuple[bool, str, str]:
        if not self.facture_ctrl:
            return False, "Controleur facture non initialise", ""
        return self.facture_ctrl.generer_facture(code_visite, telephone, creer_panier)

    def ajouter_ligne(self, code_facture: str, data: Dict) -> Tuple[bool, str, str]:
        if not self.panier_ctrl:
            return False, "Controleur panier non initialise", ""
        panier = PanierFacture(
            code_paniere="",
            designation=data.get("designation", ""),
            numero_reference=data.get("description", ""),
            quantite_facture=int(data.get("quantite", 1)),
            prix_applique=float(data.get("prix", 0)),
            code_facture=code_facture
        )
        ok, msg = self.panier_ctrl.ajouter_ligne(panier)
        if ok:
            # Recalculer montant facture
            if self.facture_ctrl:
                self.facture_ctrl.recalculer_montant_facture(code_facture)
            return True, msg, panier.get_code_paniere()
        return False, msg, ""

    def modifier_ligne(self, code_facture: str, code_paniere: str, data: Dict) -> Tuple[bool, str]:
        if not self.panier_ctrl:
            return False, "Controleur panier non initialise"
        panier = PanierFacture(
            code_paniere=code_paniere,
            designation=data.get("designation", ""),
            numero_reference=data.get("description", ""),
            quantite_facture=int(data.get("quantite", 1)),
            prix_applique=float(data.get("prix", 0)),
            code_facture=code_facture
        )
        ok, msg = self.panier_ctrl.modifier_ligne(panier)
        if ok and self.facture_ctrl:
            self.facture_ctrl.recalculer_montant_facture(code_facture)
        return ok, msg

    def supprimer_ligne(self, code_paniere: str, parent_widget) -> Tuple[bool, str]:
        if not self.panier_ctrl:
            return False, "Controleur panier non initialise"
        confirmed = CustomMessageBox.question(
            parent_widget,
            "Confirmation",
            "Supprimer cette ligne du panier ?",
            self.couleur
        )
        if not confirmed:
            return False, "Suppression annulee"
        ok, msg = self.panier_ctrl.supprimer_ligne(code_paniere)
        if ok and self.facture_ctrl:
            # On ne connait pas directement code_facture ici
            # -> La vue peut relancer un recalcul si besoin
            pass
        return ok, msg

    def annuler_facture(self, code_facture: str, parent_widget) -> Tuple[bool, str]:
        if not self.facture_ctrl:
            return False, "Controleur facture non initialise"
        confirmed = CustomMessageBox.question(
            parent_widget,
            "Confirmation",
            "Annuler cette facture ? Les lignes seront effacees et la facture restera en attente.",
            self.couleur
        )
        if not confirmed:
            return False, "Annulation annulee"
        return self.facture_ctrl.reinitialiser_facture(code_facture)

    def encaisser_facture(self, code_facture: str, parent_widget,
                          patient_info: Dict[str, Any] = None) -> Tuple[bool, str]:
        if not self.facture_ctrl:
            return False, "Controleur facture non initialise"
        facture = self.facture_ctrl.obtenir_par_code(code_facture)
        lignes = []
        total = 0.0
        cabinet_info = {}
        try:
            cabinet_info = self.facture_ctrl.get_cabinet_info() if self.facture_ctrl else {}
        except Exception:
            cabinet_info = {}
        if self.panier_ctrl:
            lignes = self.panier_ctrl.lister_par_facture(code_facture) or []
            total = sum(
                getattr(l, "get_quantite_facture", lambda: 1)() *
                getattr(l, "get_prix_applique", lambda: 0.0)()
                for l in lignes
            )
        dialog = FacturePatientInvoiceDialog(
            parent_widget,
            facture=facture,
            patient_info=patient_info or {},
            lignes=lignes,
            total=total,
            cabinet_info=cabinet_info,
            pdf_exporter=(
                lambda path: self.facture_ctrl.generer_facture_pdf(code_facture, path)
            ) if self.facture_ctrl else None
        )
        if dialog.exec() != FacturePatientInvoiceDialog.Accepted:
            return False, "Paiement annule"
        data = dialog.get_data()
        return self.facture_ctrl.enregistrer_paiement(
            code_facture, data.get("mode_paiement", ""), data.get("telephone", "")
        )

    def encaisser_facture_direct(self, code_facture: str, mode_paiement: str, telephone: str) -> Tuple[bool, str]:
        if not self.facture_ctrl:
            return False, "Controleur facture non initialise"
        return self.facture_ctrl.enregistrer_paiement(code_facture, mode_paiement, telephone)
