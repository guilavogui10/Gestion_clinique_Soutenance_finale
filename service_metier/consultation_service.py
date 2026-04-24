"""
consultation_service.py
------------------------
Service métier — Gestion des consultations.

Responsabilités :
  - Validation des données de consultation
  - CRUD : création, modification, suppression
  - Détermination du prochain statut patient (workflow)
  - Récupération (par code, visite, session, historique patient)
  - Listes filtrées de patients (attente, examen, chirurgie, etc.)
  - Statistiques (cards, graphiques mensuels/journaliers, revenus)
  - Recherche avancée (dates, services, par patient)
  - Informations cabinet
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, Optional

from data.dao_consultation import ConsultationDAO
from models.modele_consultation import Consultation
from parametre.dao_param import CabinetDAO


class ConsultationService:
    """
    Service métier pour la gestion des consultations.
    Contient la validation, le CRUD, le workflow patient et les statistiques.
    """

    def __init__(self, dao=None, cabinet_dao=None):
        self.dao = dao or ConsultationDAO()
        self.cabinet_dao = cabinet_dao or CabinetDAO()
        self.logger = logging.getLogger(__name__)
        from data.dao_visite import Visitedao
        self.dao_visite = Visitedao()

    # =========================================================================
    # MÉTHODES DE VALIDATION (LOGIQUE MÉTIER)
    # =========================================================================

    def valider_texte(self, texte: str, nom_champ: str, min_longueur: int = 3) -> tuple:
        """Valide qu'un champ texte est non vide et sans caractères interdits."""
        if not texte or texte.strip() == "":
            return False, f"Le champ {nom_champ} est obligatoire"
        if len(texte.strip()) < min_longueur:
            return False, f"Le {nom_champ} doit contenir au moins {min_longueur} caractères"
        if re.search(r'[<>{}[\]\\|`~]', texte):
            return False, f"Le {nom_champ} contient des caractères spéciaux interdits"
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
                return False, "La date de consultation ne peut pas être dans le passé"
            if date_obj > aujourdhui:
                return False, "La date de consultation ne peut pas être dans le futur"
            return True, ""
        except Exception:
            return False, "Format de date invalide (attendu: JJ/MM/AAAA)"

    def valider_frais(self, frais) -> tuple:
        """Valide que les frais sont un nombre positif."""
        try:
            frais_float = float(frais)
            if frais_float < 0:
                return False, "Les frais ne peuvent pas être négatifs"
            return True, ""
        except Exception:
            return False, "Les frais doivent être un nombre valide"

    def valider_choix(self, valeur: str, nom_champ: str) -> tuple:
        """Valide qu'un champ booléen vaut 'Oui' ou 'Non'."""
        if valeur not in ["Oui", "Non"]:
            return False, f"Le champ {nom_champ} doit être 'Oui' ou 'Non'"
        return True, ""

    def valider_codes_obligatoires(self, consultation: Consultation) -> tuple:
        """Valide que les codes visite, session et personnel sont renseignés."""
        if not consultation.code_visite or not consultation.code_session or not consultation.code_personnel:
            return False, "Tous les codes (visite, session, personnel) sont obligatoires"
        return True, ""

    def valider_consultation(self, consultation: Consultation) -> tuple:
        """Regroupe toutes les validations communes à la création et modification."""
        valide, msg = self.valider_texte(consultation.diagnostique, "diagnostique")
        if not valide:
            return False, msg
        valide, msg = self.valider_texte(consultation.resultat_consultation, "résultat de consultation")
        if not valide:
            return False, msg
        valide, msg = self.valider_date(consultation.date_consultation)
        if not valide:
            return False, msg
        valide, msg = self.valider_frais(consultation.frais_consultation)
        if not valide:
            return False, msg
        for champ, valeur in [
            ("examen", consultation.examen),
            ("chirurgie", consultation.chirurgie),
            ("commande lunette", consultation.commandelunette),
            ("prescription produit", consultation.prescription_produit)
        ]:
            valide, msg = self.valider_choix(valeur, champ)
            if not valide:
                return False, msg
        return True, ""

    def _nettoyer_consultation(self, consultation: Consultation) -> None:
        """Nettoie les champs texte (supprime les espaces superflus)."""
        consultation.diagnostique = consultation.diagnostique.strip()
        consultation.resultat_consultation = consultation.resultat_consultation.strip()

    def _determiner_prochain_statut(self, consultation: Consultation) -> str:
        """
        Détermine le prochain statut du patient selon les services prescrits.
        Règle de priorité : Examen > Chirurgie > Pharmacie > Paiement
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
    # MÉTHODES CRUD
    # =========================================================================

    def creer_consultation(self, consultation: Consultation) -> tuple:
        """Valide et crée une nouvelle consultation."""
        valide, msg = self.valider_consultation(consultation)
        if not valide:
            return False, msg
        valide, msg = self.valider_codes_obligatoires(consultation)
        if not valide:
            return False, msg
        if self.dao.obtenir_par_visite(consultation.code_visite):
            return False, "Une consultation existe déjà pour cette visite"
        self._nettoyer_consultation(consultation)
        if self.dao.ajouter(consultation):
            self.logger.info(f"Consultation {consultation.code} créée pour visite {consultation.code_visite}")
            return True, "Consultation créée avec succès"
        return False, "Erreur lors de la création de la consultation"

    def modifier_consultation(self, consultation: Consultation) -> tuple:
        """Valide et met à jour une consultation existante."""
        valide, msg = self.valider_consultation(consultation)
        if not valide:
            return False, msg
        self._nettoyer_consultation(consultation)
        if self.dao.modifier(consultation):
            self.logger.info(f"Consultation {consultation.code} modifiée")
            return True, "Consultation modifiée avec succès"
        return False, "Erreur lors de la modification de la consultation"

    def supprimer_consultation(self, code: str) -> tuple:
        """Supprime une consultation par son code."""
        if not code:
            return False, "Code de consultation invalide"
        if self.dao.supprimer(code):
            return True, "Consultation supprimée avec succès"
        return False, "Erreur lors de la suppression de la consultation"

    # =========================================================================
    # MÉTHODES DE RÉCUPÉRATION
    # =========================================================================

    def obtenir_par_code(self, code: str):
        return self.dao.obtenir_par_code(code)

    def obtenir_par_visite(self, code_visite: str):
        return self.dao.obtenir_par_visite(code_visite)

    def lister_consultations(self, code_session: str) -> list:
        return self.dao.lister_par_session(code_session)

    def rechercher_consultation(self, critere: str, code_session: str) -> list:
        return self.dao.rechercher_par_critere(critere, code_session)

    def obtenir_consultation_complete(self, code_consultation: str):
        return self.dao.consultation_complete(code_consultation)

    def obtenir_services_lies(self, code_consultation: str) -> dict:
        return self.dao.services_lies(code_consultation)

    def obtenir_historique_patient(self, code_patient: str) -> list:
        return self.dao.historique_patient(code_patient)

    # =========================================================================
    # MÉTHODES PATIENTS (LISTES FILTRÉES)
    # =========================================================================

    def obtenir_patients_attente(self, code_session: str) -> list:
        return self.dao.patients_en_attente(code_session)

    def obtenir_patients_examen(self, code_session: str) -> list:
        return self.dao.patients_pour_examen(code_session)

    def obtenir_patients_chirurgie(self, code_session: str) -> list:
        return self.dao.patients_pour_chirurgie(code_session)

    def obtenir_patients_lunette(self, code_session: str) -> list:
        return self.dao.patients_pour_lunette(code_session)

    def obtenir_patients_prescription(self, code_session: str) -> list:
        return self.dao.patients_pour_prescription(code_session)

    def info_cabinet(self) -> dict:
        return self.cabinet_dao.get_info_cabinet()

    # =========================================================================
    # MÉTHODES STATISTIQUES CARDS
    # =========================================================================

    def obtenir_nombre_total(self, code_session: str) -> int:
        return self.dao.nombre_total_par_session(code_session)

    def obtenir_consultations_aujourd_hui(self, code_session: str) -> int:
        return self.dao.nombre_consultations_aujourd_hui(code_session)

    def obtenir_nombre_patients_en_attente(self, code_session: str) -> int:
        return self.dao.nombre_patients_en_attente(code_session)

    def obtenir_montant_aujourd_hui(self, code_session: str) -> float:
        return self.dao.montant_consultations_aujourd_hui(code_session)

    def obtenir_montant_session(self, code_session: str) -> float:
        return self.dao.montant_consultations_session(code_session)

    # =========================================================================
    # MÉTHODES STATISTIQUES & GRAPHES
    # =========================================================================

    def obtenir_nombre_par_mois(self, code_session: str) -> dict:
        return self.dao.nombre_par_mois(code_session)

    def obtenir_nombre_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        return self.dao.nombre_par_jour(code_session, annee, mois)

    def obtenir_montant_par_mois(self, code_session: str) -> dict:
        return self.dao.montant_par_mois(code_session)

    def obtenir_montant_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        return self.dao.montant_par_jour(code_session, annee, mois)

    def obtenir_revenu_moyen_par_mois(self, code_session: str) -> dict:
        return self.dao.moyenne_montant_journalier_mois(code_session)

    def obtenir_moyenne_montant_journalier_par_mois(self, code_session: str) -> dict:
        return self.dao.moyenne_montant_journalier_mois(code_session)

    def obtenir_moyenne_consultations_par_mois(self, code_session: str) -> dict:
        return self.dao.moyenne_consultations_journalieres_mois(code_session)

    def obtenir_moyenne_nombre_journalier_par_mois(self, code_session: str) -> dict:
        return self.dao.moyenne_consultations_journalieres_mois(code_session)

    def obtenir_resume_session(self, code_session: str) -> dict:
        return self.dao.resume_session(code_session)

    def obtenir_revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        return self.dao.revenu_total(code_session, date_debut, date_fin)

    def obtenir_top_diagnostics(self, code_session: str, limite: int = 10) -> list:
        return self.dao.top_diagnostics(code_session, limite)

    def obtenir_consultations_par_personnel(self, code_session: str) -> list:
        return self.dao.consultations_par_personnel(code_session)

    def obtenir_taux_conversion(self, code_session: str) -> dict:
        return self.dao.taux_conversion_services(code_session)

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        """Récupère les informations du cabinet médical."""
        try:
            info = self.cabinet_dao.get_info_cabinet() or {}
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
                "logo_url": final_logo
            }
        except Exception as e:
            self.logger.error(f"Erreur get_cabinet_info: {e}")
            return {"nom_cabinet": "Cabinet ophtalmologique", "adresse_cabinet": "", "logo_url": None}

    def lister_personnel(self) -> list:
        """Retourne la liste du personnel pour le formulaire."""
        return self.dao.lister_personnel()

    # =========================================================================
    # MÉTHODES DE RECHERCHE AVANCÉE & FILTRAGE
    # =========================================================================

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        try:
            return self.dao.rechercher_entre_dates(code_session, date_debut, date_fin) or []
        except Exception as e:
            self.logger.error(f"Erreur rechercher_entre_dates: {e}")
            return []

    def rechercher_par_services(self, code_session: str, examen=None, chirurgie=None,
                               commandelunette=None, prescription=None) -> list:
        try:
            return self.dao.rechercher_par_services(
                code_session, examen, chirurgie, commandelunette, prescription
            ) or []
        except Exception as e:
            self.logger.error(f"Erreur rechercher_par_services: {e}")
            return []

    def obtenir_consultations_par_patient_par_mois(self, code_session: str, code_patient: str = None) -> dict:
        try:
            return self.dao.consultations_par_patient_par_mois(code_session, code_patient) or {}
        except Exception as e:
            self.logger.error(f"Erreur obtenir_consultations_par_patient_par_mois: {e}")
            return {}

    def obtenir_nombre_par_mois_filtre(self, code_session: str, examen: str = None,
                                       chirurgie: str = None, commandelunette: str = None,
                                       prescription: str = None) -> dict:
        try:
            return self.dao.nombre_par_mois_filtre(
                code_session, examen, chirurgie, commandelunette, prescription
            ) or {}
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_par_mois_filtre: {e}")
            return {}

    def obtenir_codes_patients_session(self, code_session: str) -> list:
        try:
            return self.dao.codes_patients_session(code_session) or []
        except Exception as e:
            self.logger.error(f"Erreur obtenir_codes_patients_session: {e}")
            return []
