import logging
from typing import Dict, Optional, List, Tuple

from models.modele_facture_patient import FacturePatient
from service_metier.facture_patient_service import FacturePatientService


class FacturePatientControleur:
    """
    Controleur MVC pour la gestion des factures patient.
    Délègue toute la logique métier au service FacturePatientService.
    """

    # =========================================================================
    # CONSTANTES METIER
    # =========================================================================

    MODES_PAIEMENT_VALIDES = ["Especes", "Mobile Money", "Carte bancaire"]

    def __init__(self):
        self.service = FacturePatientService()
        self.logger  = logging.getLogger(__name__)

    # =========================================================================
    # VALIDATION (pour compatibilite si appelees depuis la vue)
    # =========================================================================

    def valider_code_visite(self, code_visite: str) -> Tuple[bool, str]:
        return self.service.valider_code_visite(code_visite)

    def valider_code_facture(self, code_facture: str) -> Tuple[bool, str]:
        return self.service.valider_code_facture(code_facture)

    def valider_mode_paiement(self, mode_payement: str) -> Tuple[bool, str]:
        return self.service.valider_mode_paiement(mode_payement)

    def valider_telephone(self, telephone: str, mode_payement: str) -> Tuple[bool, str]:
        return self.service.valider_telephone(telephone, mode_payement)

    # =========================================================================
    # ACTIONS METIER
    # =========================================================================

    def generer_facture(self, code_visite: str, telephone: str = "",
                        creer_panier: bool = True) -> Tuple[bool, str, Optional[str]]:
        """Genere la facture pour une visite."""
        return self.service.generer_facture(code_visite, telephone, creer_panier)

    def recalculer_montant_facture(self, code_facture: str) -> Tuple[bool, str]:
        """Recalcule le montant total d'une facture a partir des lignes panier."""
        return self.service.recalculer_montant_facture(code_facture)

    def enregistrer_paiement(self, code_facture: str,
                              mode_payement: str,
                              telephone: str = "") -> Tuple[bool, str]:
        """Enregistre le paiement d'une facture."""
        return self.service.enregistrer_paiement(code_facture, mode_payement, telephone)

    def annuler_facture(self, code_facture: str) -> Tuple[bool, str]:
        """Annule une facture en attente de paiement."""
        return self.service.annuler_facture(code_facture)

    def reinitialiser_facture(self, code_facture: str) -> Tuple[bool, str]:
        """Reinitialise une facture non payee (supprime les lignes panier)."""
        return self.service.reinitialiser_facture(code_facture)

    def supprimer_facture(self, code_facture: str) -> Tuple[bool, str]:
        """Supprime une facture non payee et toutes ses lignes."""
        return self.service.supprimer_facture(code_facture)

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code_facture: str) -> Optional[FacturePatient]:
        """Retourne une facture par son code."""
        return self.service.obtenir_par_code(code_facture)

    def obtenir_par_visite(self, code_visite: str) -> Optional[FacturePatient]:
        """Retourne la facture active d'une visite."""
        return self.service.obtenir_par_visite(code_visite)

    def lister_par_session(self, code_session: str) -> List[FacturePatient]:
        """Retourne toutes les factures d'une session avec infos patient."""
        return self.service.lister_par_session(code_session)

    def lister_en_attente(self, code_session: str) -> List[FacturePatient]:
        """Retourne les factures non soldees de la session."""
        return self.service.lister_en_attente(code_session)

    def rechercher(self, critere: str, code_session: str) -> List[FacturePatient]:
        """Recherche des factures par code, nom, prenom ou telephone."""
        return self.service.rechercher(critere, code_session)

    def obtenir_patients_en_attente(self, code_session: str) -> List[Dict]:
        """Retourne les patients en attente de paiement sans facture generee."""
        return self.service.obtenir_patients_en_attente(code_session)

    def lister_services_visite(self, code_visite: str) -> List[Dict]:
        """Retourne les services lies a une visite."""
        return self.service.lister_services_visite(code_visite)

    # =========================================================================
    # METHODES STATISTIQUES — CARDS
    # =========================================================================

    def obtenir_nombre_factures_aujourd_hui(self, code_session: str) -> int:
        """Card Factures du Jour."""
        return self.service.obtenir_nombre_factures_aujourd_hui(code_session)

    def obtenir_nombre_en_attente(self, code_session: str) -> int:
        """Card En Attente."""
        return self.service.obtenir_nombre_en_attente(code_session)

    def obtenir_nombre_total_session(self, code_session: str) -> int:
        """Card Total Session."""
        return self.service.obtenir_nombre_total_session(code_session)

    # =========================================================================
    # METHODES STATISTIQUES — REVENUS
    # =========================================================================

    def obtenir_revenu_total(self, code_session: str,
                              date_debut: str = None,
                              date_fin: str = None) -> float:
        """Chiffre d'affaires total des factures payees."""
        return self.service.obtenir_revenu_total(code_session, date_debut, date_fin)

    def obtenir_resume_financier(self, code_session: str) -> Dict:
        """Synthese financiere complete pour le dashboard."""
        return self.service.obtenir_resume_financier(code_session)

    def obtenir_revenu_par_mois(self, code_session: str) -> Dict:
        """Revenus mensuels pour graphique."""
        return self.service.obtenir_revenu_par_mois(code_session)

    def obtenir_repartition_par_mode_paiement(self, code_session: str) -> List[Dict]:
        """Repartition des paiements par mode pour graphique camembert."""
        return self.service.obtenir_repartition_par_mode_paiement(code_session)

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self) -> Dict:
        """Recupere les informations du cabinet medical."""
        return self.service.get_cabinet_info()

    # =========================================================================
    # PDF FACTURE PATIENT
    # =========================================================================

    def generer_facture_pdf(self, code_facture: str, chemin_fichier: str) -> Tuple[bool, str]:
        """Genere le PDF de facture patient avec le detail des services."""
        return self.service.generer_facture_pdf(code_facture, chemin_fichier)

    # =========================================================================
    # RAPPORTS PDF LISTE FACTURES
    # =========================================================================

    def generer_rapport_pdf_par_date(self, code_session: str) -> str:
        """Genere un PDF rapport de toutes les factures groupees par date."""
        return self.service.generer_rapport_pdf_par_date(code_session)

    def generer_rapport_pdf_date_precise(self, code_session: str, date_cible) -> str:
        """Genere un PDF rapport des factures pour une date precise."""
        return self.service.generer_rapport_pdf_date_precise(code_session, date_cible)


