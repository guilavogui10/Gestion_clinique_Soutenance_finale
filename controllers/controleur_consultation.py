import sys
import os
import logging
import re
from datetime import datetime
from typing import Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.dao_consultation import ConsultationDAO
from models.modele_consultation import Consultation
from parametre.dao_param import CabinetDAO


class ConsultationControleur:
    """
    ContrÃ´leur MVC pour la gestion des consultations.
    Fait le lien entre la vue et le DAO.
    Contient toute la logique mÃ©tier et la validation des donnÃ©es.
    """

    def __init__(self):
        self.dao        = ConsultationDAO()
        self.cabinetdao = CabinetDAO()
        self.logger     = logging.getLogger(__name__)
        from data.dao_visite import Visitedao
        self.dao_visite = Visitedao()

    # =========================================================================
    # MÃ‰THODES DE VALIDATION (LOGIQUE MÃ‰TIER)
    # =========================================================================

    def valider_texte(self, texte: str, nom_champ: str, min_longueur: int = 3) -> tuple:
        """Valide qu'un champ texte est non vide et sans caractÃ¨res interdits."""
        if not texte or texte.strip() == "":
            return False, f"Le champ {nom_champ} est obligatoire"

        if len(texte.strip()) < min_longueur:
            return False, f"Le {nom_champ} doit contenir au moins {min_longueur} caractÃ¨res"

        if re.search(r'[<>{}[\]\\|`~]', texte):
            return False, f"Le {nom_champ} contient des caractÃ¨res spÃ©ciaux interdits"

        return True, ""

    def valider_date(self, date_consultation) -> tuple:
        """Valide que la date de consultation est exactement celle d'aujourd'hui."""
        if not date_consultation:
            return False, "La date de consultation est obligatoire"
        try:
            if isinstance(date_consultation, str):
                date_obj = datetime.strptime(date_consultation, "%d/%m/%Y").date()
            else:
                date_obj = date_consultation.date() if hasattr(date_consultation, 'date') else date_consultation

            aujourdhui = datetime.now().date()

            if date_obj < aujourdhui:
                return False, "La date de consultation ne peut pas Ãªtre dans le passÃ©"
            if date_obj > aujourdhui:
                return False, "La date de consultation ne peut pas Ãªtre dans le futur"

            return True, ""

        except Exception:
            return False, "Format de date invalide (attendu: JJ/MM/AAAA)"

    def valider_frais(self, frais) -> tuple:
        """Valide que les frais sont un nombre positif."""
        try:
            frais_float = float(frais)
            if frais_float < 0:
                return False, "Les frais ne peuvent pas Ãªtre nÃ©gatifs"
            return True, ""
        except Exception:
            return False, "Les frais doivent Ãªtre un nombre valide"

    def valider_choix(self, valeur: str, nom_champ: str) -> tuple:
        """Valide qu'un champ boolÃ©en vaut 'Oui' ou 'Non'."""
        if valeur not in ["Oui", "Non"]:
            return False, f"Le champ {nom_champ} doit Ãªtre 'Oui' ou 'Non'"
        return True, ""

    def valider_codes_obligatoires(self, consultation: Consultation) -> tuple:
        """Valide que les codes visite, session et personnel sont renseignÃ©s."""
        if not consultation.code_visite or not consultation.code_session or not consultation.code_personnel:
            return False, "Tous les codes (visite, session, personnel) sont obligatoires"
        return True, ""

    def valider_consultation(self, consultation: Consultation) -> tuple:
        """
        Regroupe toutes les validations communes Ã  la crÃ©ation et Ã  la modification.
        Ã‰vite la duplication de code entre creer et modifier.
        """
        valide, msg = self.valider_texte(consultation.diagnostique, "diagnostique")
        if not valide:
            return False, msg

        valide, msg = self.valider_texte(consultation.resultat_consultation, "rÃ©sultat de consultation")
        if not valide:
            return False, msg

        valide, msg = self.valider_date(consultation.date_consultation)
        if not valide:
            return False, msg

        valide, msg = self.valider_frais(consultation.frais_consultation)
        if not valide:
            return False, msg

        for champ, valeur in [
            ("examen",               consultation.examen),
            ("chirurgie",            consultation.chirurgie),
            ("commande lunette",     consultation.commandelunette),
            ("prescription produit", consultation.prescription_produit)
        ]:
            valide, msg = self.valider_choix(valeur, champ)
            if not valide:
                return False, msg

        return True, ""

    def _nettoyer_consultation(self, consultation: Consultation) -> None:
        """Nettoie les champs texte (supprime les espaces superflus)."""
        consultation.diagnostique          = consultation.diagnostique.strip()
        consultation.resultat_consultation = consultation.resultat_consultation.strip()

    def _determiner_prochain_statut(self, consultation: Consultation) -> str:
        """
        DÃ©termine le prochain statut du patient selon les services prescrits.
        RÃ¨gle de prioritÃ© : Examen > Chirurgie > Pharmacie > Paiement
        """
        if consultation.examen == 'Oui':
            return "Attente examen"
        elif consultation.chirurgie == 'Oui':
            return "Attente operation"
        elif consultation.prescription_produit == 'Oui':
            return "Attente Pharmacie"
        else:
            return "Attente payement"

    # =========================================================================
    # MÃ‰THODES CRUD
    # =========================================================================

    def creer_consultation(self, consultation: Consultation) -> tuple:
        """
        Valide et crÃ©e une nouvelle consultation.
        Le DAO met automatiquement Ã  jour le statut de la visite.
        """
        valide, msg = self.valider_consultation(consultation)
        if not valide:
            return False, msg

        valide, msg = self.valider_codes_obligatoires(consultation)
        if not valide:
            return False, msg

        if self.dao.obtenir_par_visite(consultation.code_visite):
            return False, "Une consultation existe dÃ©jÃ  pour cette visite"

        self._nettoyer_consultation(consultation)

        if self.dao.ajouter(consultation):
            self.logger.info(f"Consultation {consultation.code} crÃ©Ã©e pour visite {consultation.code_visite}")
            return True, "Consultation crÃ©Ã©e avec succÃ¨s"

        return False, "Erreur lors de la crÃ©ation de la consultation"

    def modifier_consultation(self, consultation: Consultation) -> tuple:
        """
        Valide et met Ã  jour une consultation existante.
        Note: La modification d'une consultation ne change PAS le statut de la visite
        car le patient est dÃ©jÃ  dans son parcours.
        """
        valide, msg = self.valider_consultation(consultation)
        if not valide:
            return False, msg

        self._nettoyer_consultation(consultation)

        if self.dao.modifier(consultation):
            self.logger.info(f"Consultation {consultation.code} modifiÃ©e")
            return True, "Consultation modifiÃ©e avec succÃ¨s"

        return False, "Erreur lors de la modification de la consultation"

    def supprimer_consultation(self, code: str) -> tuple:
        """Supprime une consultation par son code."""
        if not code:
            return False, "Code de consultation invalide"
        if self.dao.supprimer(code):
            return True, "Consultation supprimÃ©e avec succÃ¨s"
        return False, "Erreur lors de la suppression de la consultation"

    # =========================================================================
    # MÃ‰THODES DE RÃ‰CUPÃ‰RATION
    # =========================================================================

    def obtenir_par_code(self, code: str):
        """Retourne une consultation par son code."""
        return self.dao.obtenir_par_code(code)

    def obtenir_par_visite(self, code_visite: str):
        """Retourne la consultation liÃ©e Ã  une visite."""
        return self.dao.obtenir_par_visite(code_visite)

    def lister_consultations(self, code_session: str) -> list:
        """Retourne toutes les consultations d'une session."""
        return self.dao.lister_par_session(code_session)

    def rechercher_consultation(self, critere: str, code_session: str) -> list:
        """Recherche des consultations par critÃ¨re dans une session."""
        return self.dao.rechercher_par_critere(critere, code_session)

    def obtenir_consultation_complete(self, code_consultation: str):
        """Retourne une consultation avec les infos patient et personnel."""
        return self.dao.consultation_complete(code_consultation)

    def obtenir_services_lies(self, code_consultation: str) -> dict:
        """Retourne tous les services liÃ©s Ã  une consultation."""
        return self.dao.services_lies(code_consultation)

    def obtenir_historique_patient(self, code_patient: str) -> list:
        """Retourne l'historique complet des consultations d'un patient."""
        return self.dao.historique_patient(code_patient)

    # =========================================================================
    # MÃ‰THODES PATIENTS (LISTES FILTRÃ‰ES)
    # =========================================================================

    def obtenir_patients_attente(self, code_session: str) -> list:
        """Retourne les patients en attente de consultation."""
        return self.dao.patients_en_attente(code_session)

    def obtenir_patients_examen(self, code_session: str) -> list:
        """Retourne les patients orientÃ©s vers un examen."""
        return self.dao.patients_pour_examen(code_session)

    def obtenir_patients_chirurgie(self, code_session: str) -> list:
        """Retourne les patients orientÃ©s vers une chirurgie."""
        return self.dao.patients_pour_chirurgie(code_session)

    def obtenir_patients_lunette(self, code_session: str) -> list:
        """Retourne les patients avec commande de lunettes."""
        return self.dao.patients_pour_lunette(code_session)

    def obtenir_patients_prescription(self, code_session: str) -> list:
        """Retourne les patients avec prescription de produits."""
        return self.dao.patients_pour_prescription(code_session)

    def info_cabinet(self) -> dict:
        """Retourne les informations du cabinet (nom, logo, adresse)."""
        return self.cabinetdao.get_info_cabinet()

    # =========================================================================
    # MÃ‰THODES STATISTIQUES CARDS
    # =========================================================================

    def obtenir_nombre_total(self, code_session: str) -> int:
        """Card 'Session en Cours' : nombre total de consultations de la session."""
        return self.dao.nombre_total_par_session(code_session)

    def obtenir_consultations_aujourd_hui(self, code_session: str) -> int:
        """Card 'Consultations du Jour' : nombre de consultations crÃ©Ã©es aujourd'hui."""
        return self.dao.nombre_consultations_aujourd_hui(code_session)

    def obtenir_nombre_patients_en_attente(self, code_session: str) -> int:
        """Card 'Patients en Attente' : patients avec visite mais sans consultation."""
        return self.dao.nombre_patients_en_attente(code_session)

    def obtenir_montant_aujourd_hui(self, code_session: str) -> float:
        """Card 'Montant du Jour' : montant total des consultations d'aujourd'hui."""
        return self.dao.montant_consultations_aujourd_hui(code_session)

    def obtenir_montant_session(self, code_session: str) -> float:
        """Card 'Montant Session' : montant total des consultations de la session."""
        return self.dao.montant_consultations_session(code_session)

    # =========================================================================
    # MÃ‰THODES STATISTIQUES & GRAPHES
    # =========================================================================

    def obtenir_nombre_par_mois(self, code_session: str) -> dict:
        """Retourne le nombre de consultations par mois."""
        return self.dao.nombre_par_mois(code_session)

    def obtenir_nombre_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """Retourne le nombre de consultations par jour pour un mois donne."""
        return self.dao.nombre_par_jour(code_session, annee, mois)

    def obtenir_montant_par_mois(self, code_session: str) -> dict:
        """Retourne le montant total des consultations par mois."""
        return self.dao.montant_par_mois(code_session)

    def obtenir_montant_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """Retourne le montant des consultations par jour pour un mois donne."""
        return self.dao.montant_par_jour(code_session, annee, mois)

    def obtenir_revenu_moyen_par_mois(self, code_session: str) -> dict:
        """
        Alias historique : moyenne journaliere des montants de consultations par mois
        (jours sans activite inclus).
        """
        return self.dao.moyenne_montant_journalier_mois(code_session)

    def obtenir_moyenne_montant_journalier_par_mois(self, code_session: str) -> dict:
        """Retourne la moyenne journaliere des montants de consultations par mois."""
        return self.dao.moyenne_montant_journalier_mois(code_session)

    def obtenir_moyenne_consultations_par_mois(self, code_session: str) -> dict:
        """
        Alias historique : moyenne journaliere du nombre de consultations par mois
        (jours sans activite inclus).
        """
        return self.dao.moyenne_consultations_journalieres_mois(code_session)

    def obtenir_moyenne_nombre_journalier_par_mois(self, code_session: str) -> dict:
        """Retourne la moyenne journaliere du nombre de consultations par mois."""
        return self.dao.moyenne_consultations_journalieres_mois(code_session)

    def obtenir_resume_session(self, code_session: str) -> dict:
        """Retourne un rÃ©sumÃ© complet d'une session pour le tableau de bord."""
        return self.dao.resume_session(code_session)

    def obtenir_revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        """Retourne le total des frais de consultation pour une session."""
        return self.dao.revenu_total(code_session, date_debut, date_fin)

    def obtenir_top_diagnostics(self, code_session: str, limite: int = 10) -> list:
        """Retourne les diagnostics les plus frÃ©quents pour une session."""
        return self.dao.top_diagnostics(code_session, limite)

    def obtenir_consultations_par_personnel(self, code_session: str) -> list:
        """Retourne le nombre de consultations groupÃ© par personnel."""
        return self.dao.consultations_par_personnel(code_session)

    def obtenir_taux_conversion(self, code_session: str) -> dict:
        """Retourne le taux de conversion des services complÃ©mentaires."""
        return self.dao.taux_conversion_services(code_session)

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        """RÃ©cupÃ¨re les informations du cabinet mÃ©dical."""
        try:
            info            = self.cabinetdao.get_info_cabinet() or {}
            nom_cabinet     = info.get("nom_cabinet", "Cabinet ophtalmologique")
            adresse_cabinet = info.get("adresse", "")
            logo_cabinet    = info.get("logo", None)

            final_logo = None
            if logo_cabinet:
                try:
                    base_dir   = os.path.dirname(os.path.dirname(__file__))
                    logo_path  = os.path.join(base_dir, "connexion", "image", logo_cabinet)
                    if os.path.exists(logo_path) and os.path.isfile(logo_path):
                        final_logo = os.path.abspath(logo_path)
                except Exception as e:
                    self.logger.warning(f"Erreur chemin logo: {e}")

            return {
                "nom_cabinet":      nom_cabinet,
                "adresse_cabinet":  adresse_cabinet,
                "logo_url":         final_logo
            }

        except Exception as e:
            self.logger.error(f"Erreur get_cabinet_info: {e}")
            return {
                "nom_cabinet":     "Cabinet ophtalmologique",
                "adresse_cabinet": "",
                "logo_url":        None
            }

    def lister_personnel(self) -> list:
        """Retourne la liste du personnel pour le formulaire."""
        return self.dao.lister_personnel()

    # =========================================================================
    # MÉTHODES DE RECHERCHE AVANCÉE & FILTRAGE
    # =========================================================================

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        """
        Recherche les consultations entre deux dates.
        Délègue au DAO qui retourne une liste d'objets Consultation.
        """
        try:
            return self.dao.rechercher_entre_dates(code_session, date_debut, date_fin) or []
        except Exception as e:
            self.logger.error(f"Erreur rechercher_entre_dates: {e}")
            return []

    def rechercher_par_services(self, code_session: str, examen=None, chirurgie=None, 
                               commandelunette=None, prescription=None) -> list:
        """
        Recherche les consultations par services supplémentaires.
        Chaque paramètre peut être None, "Oui", ou "Non".
        """
        try:
            return self.dao.rechercher_par_services(
                code_session, examen, chirurgie, commandelunette, prescription
            ) or []
        except Exception as e:
            self.logger.error(f"Erreur rechercher_par_services: {e}")
            return []

    def obtenir_consultations_par_patient_par_mois(self, code_session: str, code_patient: str = None) -> dict:
        """
        Retourne les consultations par patient par mois.
        Format : { "Jan": { "P001": 2, "P002": 1 }, ... } ou { "Jan": 2, ... }
        """
        try:
            return self.dao.consultations_par_patient_par_mois(code_session, code_patient) or {}
        except Exception as e:
            self.logger.error(f"Erreur obtenir_consultations_par_patient_par_mois: {e}")
            return {}

    def obtenir_nombre_par_mois_filtre(self, code_session: str, examen: str = None, 
                                       chirurgie: str = None, commandelunette: str = None, 
                                       prescription: str = None) -> dict:
        """
        Retourne le nombre de consultations par mois avec filtres sur services.
        Format : { "Jan": 5, "Fév": 3, ... }
        """
        try:
            return self.dao.nombre_par_mois_filtre(
                code_session, examen, chirurgie, commandelunette, prescription
            ) or {}
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_par_mois_filtre: {e}")
            return {}

    def obtenir_codes_patients_session(self, code_session: str) -> list:
        """
        Retourne une liste des codes patients uniques pour une session.
        Format: [{'code_patient': 'P001', 'nom': 'Dupont', 'prenom': 'Jean'}, ...]
        """
        try:
            return self.dao.codes_patients_session(code_session) or []
        except Exception as e:
            self.logger.error(f"Erreur obtenir_codes_patients_session: {e}")
            return []
