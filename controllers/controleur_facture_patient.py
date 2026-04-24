import sys
import os
import logging
import re
from typing import Dict, Optional, List, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.dao_facture_patient import FacturePatientDAO
from models.modele_facture_patient import FacturePatient
from parametre.dao_param import CabinetDAO
from services.facture_patient_pdf_service import FacturePatientPDFService


class FacturePatientControleur:
    """
    Controleur MVC pour la gestion des factures patient.
    Fait le lien entre la vue et le DAO.
    Contient toute la logique metier et la validation des donnees.
    """

    # =========================================================================
    # CONSTANTES METIER
    # =========================================================================

    MODES_PAIEMENT_VALIDES = ["Especes", "Mobile Money", "Carte bancaire"]

    def __init__(self):
        self.dao        = FacturePatientDAO()
        self.cabinetdao = CabinetDAO()
        self.logger     = logging.getLogger(__name__)

    # =========================================================================
    # METHODES DE VALIDATION (LOGIQUE METIER)
    # =========================================================================

    def valider_code_visite(self, code_visite: str) -> Tuple[bool, str]:
        """Valide que le code visite est renseigne."""
        if not code_visite or code_visite.strip() == "":
            return False, "Le code visite est obligatoire"
        return True, ""

    def valider_code_facture(self, code_facture: str) -> Tuple[bool, str]:
        """Valide que le code facture est renseigne."""
        if not code_facture or code_facture.strip() == "":
            return False, "Le code facture est obligatoire"
        return True, ""

    def valider_mode_paiement(self, mode_payement: str) -> Tuple[bool, str]:
        """Valide que le mode de paiement est l'un des modes autorises."""
        if not mode_payement or mode_payement.strip() == "":
            return False, "Le mode de paiement est obligatoire"
        if mode_payement not in self.MODES_PAIEMENT_VALIDES:
            return False, f"Mode de paiement invalide. Valeurs acceptees : {', '.join(self.MODES_PAIEMENT_VALIDES)}"
        return True, ""

    def valider_telephone(self, telephone: str, mode_payement: str) -> Tuple[bool, str]:
        """
        Valide le numero de telephone.
        Obligatoire uniquement si le mode de paiement est 'Mobile Money'.
        """
        if mode_payement == "Mobile Money":
            if not telephone or telephone.strip() == "":
                return False, "Le numero de telephone est obligatoire pour un paiement Mobile Money"
            if not re.match(r'^\+?[0-9]{8,15}$', telephone.strip()):
                return False, "Le numero de telephone est invalide"
        return True, ""

    # =========================================================================
    # METHODES ACTIONS METIER
    # =========================================================================

    def generer_facture(self, code_visite: str, telephone: str = "",
                        creer_panier: bool = True) -> Tuple[bool, str, Optional[str]]:
        """
        Declenche la generation automatique de la facture et de ses lignes panier.
        Valide le code visite avant de deleger au DAO.

        Args:
            code_visite (str): Code de la visite a facturer.
            telephone   (str): Contact optionnel (Mobile Money).

        Returns:
            Tuple(bool, str, str|None): (succes, message, code_facture)
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
        """
        Recalcule le montant total d'une facture a partir des lignes panier.
        """
        valide, msg = self.valider_code_facture(code_facture)
        if not valide:
            return False, msg
        ok = self.dao.recalculer_montant_facture(code_facture)
        return (ok, "Montant facture mis a jour" if ok else "Erreur recalcul montant")

    def enregistrer_paiement(self, code_facture: str,
                              mode_payement: str,
                              telephone: str = "") -> Tuple[bool, str]:
        """
        Valide les donnees puis enregistre le paiement d'une facture.
        Solde la facture et libere le patient.

        Args:
            code_facture  (str): Code de la facture a solder.
            mode_payement (str): 'Especes' | 'Mobile Money' | 'Carte bancaire'.
            telephone     (str): Numero pour confirmation (Mobile Money).

        Returns:
            Tuple(bool, str): (succes, message)
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
        """
        Annule une facture en attente de paiement.
        Une facture deja payee ne peut pas etre annulee.

        Args:
            code_facture (str): Code de la facture a annuler.

        Returns:
            Tuple(bool, str): (succes, message)
        """
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
        """
        Reinitialise une facture non payee (garde statut Attente payement)
        et supprime toutes les lignes panier.

        Args:
            code_facture (str): Code de la facture a reinitialiser.

        Returns:
            Tuple(bool, str): (succes, message)
        """
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
        """
        Supprime une facture non payee et toutes ses lignes.
        Utilise pour abandonner une facture et remettre la visite en attente.

        Args:
            code_facture (str): Code de la facture a supprimer.

        Returns:
            Tuple(bool, str): (succes, message)
        """
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
    # METHODES DE RECUPERATION
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
        """Retourne les factures non soldees de la session (file d'attente caisse)."""
        return self.dao.lister_en_attente(code_session)

    def rechercher(self, critere: str, code_session: str) -> List[FacturePatient]:
        """Recherche des factures par code, nom, prenom ou telephone."""
        return self.dao.rechercher_par_critere(critere, code_session)

    def obtenir_patients_en_attente(self, code_session: str) -> List[Dict]:
        """
        Retourne les patients en attente de paiement sans facture generee.
        Utilise pour declencher la generation depuis la vue caisse.
        """
        return self.dao.patients_en_attente_paiement(code_session)

    def lister_services_visite(self, code_visite: str) -> List[Dict]:
        """
        Retourne les services lies a une visite (consultation, examen, chirurgie,
        lunettes, pharmacie agrégée).

        Args:
            code_visite (str): Code visite

        Returns:
            list[dict]
        """
        valide, msg = self.valider_code_visite(code_visite)
        if not valide:
            self.logger.warning(f"Code visite invalide: {msg}")
            return []
        return self.dao.lister_services_visite(code_visite) or []

    # =========================================================================
    # METHODES STATISTIQUES — CARDS
    # =========================================================================

    def obtenir_nombre_factures_aujourd_hui(self, code_session: str) -> int:
        """Card 'Factures du Jour' : nombre de factures creees aujourd'hui."""
        try:
            return self.dao.nombre_factures_aujourd_hui(code_session) or 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_factures_aujourd_hui: {e}")
            return 0

    def obtenir_nombre_en_attente(self, code_session: str) -> int:
        """Card 'En Attente' : nombre de factures non soldees."""
        try:
            return self.dao.nombre_en_attente(code_session) or 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_en_attente: {e}")
            return 0

    def obtenir_nombre_total_session(self, code_session: str) -> int:
        """Card 'Total Session' : nombre total de factures de la session."""
        try:
            return self.dao.nombre_total_par_session(code_session) or 0
        except Exception as e:
            self.logger.error(f"Erreur nombre_total_par_session: {e}")
            return 0

    # =========================================================================
    # METHODES STATISTIQUES — REVENUS
    # =========================================================================

    def obtenir_revenu_total(self, code_session: str,
                              date_debut: str = None,
                              date_fin: str = None) -> float:
        """
        Chiffre d'affaires total des factures payees.
        Filtre date optionnel au format 'YYYY-MM-DD'.
        """
        try:
            return self.dao.revenu_total(code_session, date_debut, date_fin) or 0.0
        except Exception as e:
            self.logger.error(f"Erreur revenu_total: {e}")
            return 0.0

    def obtenir_resume_financier(self, code_session: str) -> Dict:
        """
        Synthese financiere complete pour le dashboard.
        Retourne : total_encaisse, total_en_attente, nombre_payees,
                   nombre_en_attente, taux_recouvrement.
        """
        try:
            return self.dao.resume_financier(code_session)
        except Exception as e:
            self.logger.error(f"Erreur resume_financier: {e}")
            return self._resume_vide()

    def obtenir_revenu_par_mois(self, code_session: str) -> Dict:
        """
        Revenus mensuels pour graphique.
        Format : {'Jan': 0.0, 'Fev': 0.0, ..., 'Dec': 0.0}
        """
        try:
            return self.dao.revenu_par_mois(code_session)
        except Exception as e:
            self.logger.error(f"Erreur revenu_par_mois: {e}")
            return {}

    def obtenir_repartition_par_mode_paiement(self, code_session: str) -> List[Dict]:
        """
        Repartition des paiements par mode pour graphique camembert.
        Retourne : [{'Mode_payement', 'nombre', 'total'}, ...]
        """
        try:
            return self.dao.repartition_par_mode_paiement(code_session)
        except Exception as e:
            self.logger.error(f"Erreur repartition_par_mode_paiement: {e}")
            return []

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        """Recupere les informations du cabinet medical."""
        try:
            info            = self.cabinetdao.get_info_cabinet() or {}
            nom_cabinet     = info.get("nom_cabinet", "Cabinet ophtalmologique")
            adresse_cabinet = info.get("adresse", "")
            logo_cabinet    = info.get("logo", None)

            final_logo = None
            if logo_cabinet:
                try:
                    base_dir  = os.path.dirname(os.path.dirname(__file__))
                    logo_path = os.path.join(base_dir, "connexion", "image", logo_cabinet)
                    if os.path.exists(logo_path) and os.path.isfile(logo_path):
                        final_logo = os.path.abspath(logo_path)
                except Exception as e:
                    self.logger.warning(f"Erreur chemin logo: {e}")

            return {
                "nom_cabinet":     nom_cabinet,
                "adresse_cabinet": adresse_cabinet,
                "logo_url":        final_logo,
            }

        except Exception as e:
            self.logger.error(f"Erreur get_cabinet_info: {e}")
            return {
                "nom_cabinet":     "Cabinet ophtalmologique",
                "adresse_cabinet": "",
                "logo_url":        None,
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

        return FacturePatientPDFService.generer_facture_pdf(
            self, chemin_fichier, details
        )

    # =========================================================================
    # METHODES PRIVEES
    # =========================================================================

    @staticmethod
    def _resume_vide() -> Dict:
        """Retourne un dictionnaire resume vide (cas d'erreur)."""
        return {
            "total_encaisse":    0.0,
            "total_en_attente":  0.0,
            "nombre_payees":     0,
            "nombre_en_attente": 0,
            "taux_recouvrement": 0.0,
        }
