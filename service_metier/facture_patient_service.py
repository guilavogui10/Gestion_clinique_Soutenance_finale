"""
facture_patient_service.py
---------------------------
Service métier — Gestion des factures patient.

Responsabilités :
  - Validation des données (code_visite, code_facture, mode_paiement, téléphone)
  - Actions métier : génération, recalcul, paiement, annulation, réinitialisation, suppression
  - Récupération : par code, visite, session, attente, recherche, services visite
  - Statistiques cards : factures du jour, en attente, total session
  - Statistiques revenus : total, résumé financier, par mois, par mode paiement
  - Génération PDF
  - Informations cabinet
"""

import os
import logging
import re
from typing import Dict, Optional, List, Tuple

from data.dao_facture_patient import FacturePatientDAO
from models.modele_facture_patient import FacturePatient
from parametre.dao_param import CabinetDAO
from services.pdf_patient.facture_pdf import FacturePatientPDFService


class FacturePatientService:
    """
    Service métier pour la gestion des factures patient.
    Contient la validation, les actions métier, la récupération, les statistiques et le PDF.
    """

    # =========================================================================
    # CONSTANTES MÉTIER
    # =========================================================================

    MODES_PAIEMENT_VALIDES = ["Especes", "Espèces", "Mobile Money", "Orange Money", "Carte bancaire"]

    def __init__(self, dao=None, cabinet_dao=None):
        self.dao = dao or FacturePatientDAO()
        self.cabinetdao = cabinet_dao or CabinetDAO()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # MÉTHODES DE VALIDATION
    # =========================================================================

    def valider_code_visite(self, code_visite: str) -> Tuple[bool, str]:
        """Valide que le code visite est renseigné."""
        if not code_visite or code_visite.strip() == "":
            return False, "Le code visite est obligatoire"
        return True, ""

    def valider_code_facture(self, code_facture: str) -> Tuple[bool, str]:
        """Valide que le code facture est renseigné."""
        if not code_facture or code_facture.strip() == "":
            return False, "Le code facture est obligatoire"
        return True, ""

    def valider_mode_paiement(self, mode_payement: str) -> Tuple[bool, str]:
        """Valide que le mode de paiement est l'un des modes autorisés."""
        if not mode_payement or mode_payement.strip() == "":
            return False, "Le mode de paiement est obligatoire"
        if mode_payement not in self.MODES_PAIEMENT_VALIDES:
            return False, f"Mode de paiement invalide. Valeurs acceptees : {', '.join(self.MODES_PAIEMENT_VALIDES)}"
        return True, ""

    def valider_telephone(self, telephone: str, mode_payement: str) -> Tuple[bool, str]:
        """
        Valide le numéro de téléphone.
        Obligatoire uniquement si le mode de paiement est 'Mobile Money' ou 'Orange Money'.
        """
        if mode_payement in ["Mobile Money", "Orange Money"]:
            if not telephone or telephone.strip() == "":
                return False, f"Le numero de telephone est obligatoire pour un paiement {mode_payement}"
            if not re.match(r'^\+?[0-9]{8,15}$', telephone.strip()):
                return False, "Le numero de telephone est invalide"
        return True, ""

    # =========================================================================
    # ACTIONS MÉTIER
    # =========================================================================

    def generer_facture(self, code_visite: str, telephone: str = "",
                        creer_panier: bool = True) -> Tuple[bool, str, Optional[str]]:
        """
        Déclenche la génération automatique de la facture et de ses lignes panier.

        Args:
            code_visite (str): Code de la visite à facturer.
            telephone (str): Contact optionnel (Mobile Money).
            creer_panier (bool): Créer les lignes panier automatiquement.

        Returns:
            Tuple(bool, str, str|None): (succès, message, code_facture)
        """
        valide, msg = self.valider_code_visite(code_visite)
        if not valide:
            return False, msg, None

        succes, message, code_facture = self.dao.generer_facture(
            code_visite, telephone.strip(), creer_panier
        )

        if succes:
            self.logger.info(f"Facture {code_facture} generee pour la visite {code_visite}")
        else:
            self.logger.warning(f"Echec generation facture pour visite {code_visite} : {message}")

        return succes, message, code_facture

    def recalculer_montant_facture(self, code_facture: str) -> Tuple[bool, str]:
        """Recalcule le montant total d'une facture à partir des lignes panier."""
        valide, msg = self.valider_code_facture(code_facture)
        if not valide:
            return False, msg
        ok = self.dao.recalculer_montant_facture(code_facture)
        return (ok, "Montant facture mis a jour" if ok else "Erreur recalcul montant")

    def enregistrer_paiement(self, code_facture: str,
                              mode_payement: str,
                              telephone: str = "") -> Tuple[bool, str]:
        """
        Valide les données puis enregistre le paiement d'une facture.

        Args:
            code_facture (str): Code de la facture à solder.
            mode_payement (str): 'Especes' | 'Mobile Money' | 'Carte bancaire'.
            telephone (str): Numéro pour confirmation (Mobile Money).

        Returns:
            Tuple(bool, str): (succès, message)
        """
        valide, msg = self.valider_code_facture(code_facture)
        if not valide:
            return False, msg

        valide, msg = self.valider_mode_paiement(mode_payement)
        if not valide:
            return False, msg

        valide, msg = self.valider_telephone(telephone, mode_payement)
        if not valide:
            return False, msg

        succes, message = self.dao.enregistrer_paiement(code_facture, mode_payement, telephone.strip())

        if succes:
            self.logger.info(f"Paiement enregistre pour facture {code_facture} - mode : {mode_payement}")
        else:
            self.logger.warning(f"Echec paiement facture {code_facture} : {message}")

        return succes, message

    def annuler_facture(self, code_facture: str) -> Tuple[bool, str]:
        """Annule une facture en attente de paiement."""
        valide, msg = self.valider_code_facture(code_facture)
        if not valide:
            return False, msg

        succes, message = self.dao.annuler_facture(code_facture)

        if succes:
            self.logger.info(f"Facture {code_facture} annulee")
        else:
            self.logger.warning(f"Echec annulation facture {code_facture} : {message}")

        return succes, message

    def reinitialiser_facture(self, code_facture: str) -> Tuple[bool, str]:
        """Réinitialise une facture non payée et supprime toutes les lignes panier."""
        valide, msg = self.valider_code_facture(code_facture)
        if not valide:
            return False, msg

        succes, message = self.dao.reinitialiser_facture(code_facture)

        if succes:
            self.logger.info(f"Facture {code_facture} reinitialisee")
        else:
            self.logger.warning(f"Echec reinitialisation facture {code_facture} : {message}")

        return succes, message

    def supprimer_facture(self, code_facture: str) -> Tuple[bool, str]:
        """Supprime une facture non payée et toutes ses lignes."""
        valide, msg = self.valider_code_facture(code_facture)
        if not valide:
            return False, msg

        succes, message = self.dao.supprimer_facture(code_facture)

        if succes:
            self.logger.info(f"Facture {code_facture} supprimee")
        else:
            self.logger.warning(f"Echec suppression facture {code_facture} : {message}")

        return succes, message

    # =========================================================================
    # RÉCUPÉRATION
    # =========================================================================

    def obtenir_par_code(self, code_facture: str) -> Optional[FacturePatient]:
        """Retourne une facture par son code."""
        return self.dao.obtenir_par_code(code_facture)

    def obtenir_par_visite(self, code_visite: str) -> Optional[FacturePatient]:
        """Retourne la facture active d'une visite."""
        return self.dao.obtenir_par_visite(code_visite)

    def lister_par_session(self, code_session: str) -> List[FacturePatient]:
        """Retourne toutes les factures d'une session avec infos patient."""
        return self.dao.lister_par_session(code_session)

    def lister_en_attente(self, code_session: str) -> List[FacturePatient]:
        """Retourne les factures non soldées de la session (file d'attente caisse)."""
        return self.dao.lister_en_attente(code_session)

    def rechercher(self, critere: str, code_session: str) -> List[FacturePatient]:
        """Recherche des factures par code, nom, prénom ou téléphone."""
        return self.dao.rechercher_par_critere(critere, code_session)

    def obtenir_patients_en_attente(self, code_session: str) -> List[Dict]:
        """Retourne les patients en attente de paiement sans facture générée."""
        return self.dao.patients_en_attente_paiement(code_session)

    def lister_services_visite(self, code_visite: str) -> List[Dict]:
        """Retourne les services liés à une visite (consultation, examen, chirurgie, lunettes, pharmacie)."""
        valide, msg = self.valider_code_visite(code_visite)
        if not valide:
            self.logger.warning(f"Code visite invalide: {msg}")
            return []
        return self.dao.lister_services_visite(code_visite) or []

    # =========================================================================
    # STATISTIQUES — CARDS
    # =========================================================================

    def obtenir_nombre_factures_aujourd_hui(self, code_session: str) -> int:
        """Card 'Factures du Jour'."""
        try:
            return self.dao.nombre_factures_aujourd_hui(code_session) or 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_factures_aujourd_hui: {e}")
            return 0

    def obtenir_nombre_en_attente(self, code_session: str) -> int:
        """Card 'En Attente'."""
        try:
            return self.dao.nombre_en_attente(code_session) or 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_en_attente: {e}")
            return 0

    def obtenir_nombre_total_session(self, code_session: str) -> int:
        """Card 'Total Session'."""
        try:
            return self.dao.nombre_total_par_session(code_session) or 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_total_par_session: {e}")
            return 0

    # =========================================================================
    # STATISTIQUES — REVENUS
    # =========================================================================

    def obtenir_revenu_total(self, code_session: str,
                              date_debut: str = None,
                              date_fin: str = None) -> float:
        """Chiffre d'affaires total des factures payées."""
        try:
            return self.dao.revenu_total(code_session, date_debut, date_fin) or 0.0
        except Exception as e:
            self.logger.error(f"Erreur revenu_total: {e}")
            return 0.0

    def obtenir_resume_financier(self, code_session: str) -> Dict:
        """Synthèse financière complète pour le dashboard."""
        try:
            return self.dao.resume_financier(code_session)
        except Exception as e:
            self.logger.error(f"Erreur resume_financier: {e}")
            return self._resume_vide()

    def obtenir_revenu_par_mois(self, code_session: str) -> Dict:
        """Revenus mensuels pour graphique."""
        try:
            return self.dao.revenu_par_mois(code_session)
        except Exception as e:
            self.logger.error(f"Erreur revenu_par_mois: {e}")
            return {}

    def obtenir_repartition_par_mode_paiement(self, code_session: str) -> List[Dict]:
        """Répartition des paiements par mode pour graphique camembert."""
        try:
            return self.dao.repartition_par_mode_paiement(code_session)
        except Exception as e:
            self.logger.error(f"Erreur repartition_par_mode_paiement: {e}")
            return []

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        """Récupère les informations du cabinet médical."""
        try:
            info = self.cabinetdao.get_info_cabinet() or {}
            nom_cabinet = info.get("nom_cabinet", "Cabinet ophtalmologique")
            adresse_cabinet = info.get("adresse", "")
            logo_cabinet = info.get("logo", None)

            final_logo = None
            if logo_cabinet:
                try:
                    base_dir = os.path.dirname(os.path.dirname(__file__))
                    logo_path = os.path.join(base_dir, "connexion", "image", logo_cabinet)
                    if os.path.exists(logo_path) and os.path.isfile(logo_path):
                        final_logo = os.path.abspath(logo_path)
                except Exception as e:
                    self.logger.warning(f"Erreur chemin logo: {e}")

            return {
                "nom_cabinet": nom_cabinet,
                "adresse_cabinet": adresse_cabinet,
                "logo_url": final_logo,
            }
        except Exception as e:
            self.logger.error(f"Erreur get_cabinet_info: {e}")
            return {
                "nom_cabinet": "Cabinet ophtalmologique",
                "adresse_cabinet": "",
                "logo_url": None,
            }

    # =========================================================================
    # PDF FACTURE PATIENT
    # =========================================================================

    def generer_facture_pdf(self, code_facture: str, chemin_fichier: str) -> Tuple[bool, str]:
        """
        Génère le PDF de facture patient avec le détail des services.

        Args:
            code_facture (str): Code facture.
            chemin_fichier (str): Chemin de sortie PDF.

        Returns:
            Tuple(bool, str): (succès, message)
        """
        valide, msg = self.valider_code_facture(code_facture)
        if not valide:
            return False, msg

        details = self.dao.details_facture_pdf(code_facture)
        if not details:
            return False, "Aucune donnée trouvée pour cette facture."

        info_cabinet = self.get_cabinet_info()
        try:
            FacturePatientPDFService.generer_facture_pdf(details, info_cabinet, chemin_fichier)
            return True, "PDF généré avec succès."
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du PDF de la facture: {e}")
            return False, f"Erreur génération PDF : {e}"

    # =========================================================================
    # RAPPORTS PDF LISTE FACTURES
    # =========================================================================

    def generer_rapport_pdf_par_date(self, code_session: str) -> str:
        """Génère un PDF de toutes les factures de la session groupées par date."""
        from services.pdf_rapports.rapport_facture_patient import RapportFacturePatientPDF
        factures = self.dao.lister_par_session(code_session) or []
        info_cabinet = self.get_cabinet_info()
        return RapportFacturePatientPDF.generer_pdf_par_date(
            [self._facture_to_dict(f) for f in factures], info_cabinet
        )

    def generer_rapport_pdf_date_precise(self, code_session: str, date_cible) -> str:
        """Génère un PDF des factures de la session pour une date précise."""
        from services.pdf_rapports.rapport_facture_patient import RapportFacturePatientPDF
        factures = self.dao.lister_par_session(code_session) or []
        info_cabinet = self.get_cabinet_info()
        return RapportFacturePatientPDF.generer_pdf_date_precise(
            [self._facture_to_dict(f) for f in factures], date_cible, info_cabinet
        )

    @staticmethod
    def _facture_to_dict(f) -> dict:
        """Convertit un objet FacturePatient (attributs privés) en dict pour les rapports PDF."""
        return {
            'code_facture':   f.get_code_facture(),
            'montant_total':  f.get_montant_total(),
            'mode_payement':  f.get_mode_payement(),
            'statut_facture': f.get_statut_facture(),
            'date_facture':   f.get_date_facture(),
            'nom_patient':    getattr(f, 'nom_patient',    ''),
            'prenom_patient': getattr(f, 'prenom_patient', ''),
        }

    # =========================================================================
    # MÉTHODES PRIVÉES
    # =========================================================================

    @staticmethod
    def _resume_vide() -> Dict:
        """Retourne un dictionnaire résumé vide (cas d'erreur)."""
        return {
            "total_encaisse": 0.0,
            "total_en_attente": 0.0,
            "nombre_payees": 0,
            "nombre_en_attente": 0,
            "taux_recouvrement": 0.0,
        }
