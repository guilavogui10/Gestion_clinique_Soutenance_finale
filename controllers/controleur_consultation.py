import sys
import os
import logging
from typing import Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.modele_consultation import Consultation
from service_metier.consultation_service import ConsultationService


class ConsultationControleur:

    def __init__(self):
        self.service = ConsultationService()
        self.logger  = logging.getLogger(__name__)

    # === VALIDATION ===

    def valider_texte(self, texte, nom_champ, min_longueur=3):
        return self.service.valider_texte(texte, nom_champ, min_longueur)

    def valider_date(self, date_consultation):
        return self.service.valider_date(date_consultation)

    def valider_frais(self, frais):
        return self.service.valider_frais(frais)

    def valider_choix(self, valeur, nom_champ):
        return self.service.valider_choix(valeur, nom_champ)

    def valider_codes_obligatoires(self, consultation):
        return self.service.valider_codes_obligatoires(consultation)

    def valider_consultation(self, consultation):
        return self.service.valider_consultation(consultation)

    # === CRUD ===

    def creer_consultation(self, consultation):
        return self.service.creer_consultation(consultation)

    def modifier_consultation(self, consultation):
        return self.service.modifier_consultation(consultation)

    def supprimer_consultation(self, code):
        return self.service.supprimer_consultation(code)

    # === RECUPERATION ===

    def obtenir_par_code(self, code):
        return self.service.obtenir_par_code(code)

    def obtenir_par_visite(self, code_visite):
        return self.service.obtenir_par_visite(code_visite)

    def lister_consultations(self, code_session):
        return self.service.lister_consultations(code_session)

    def lister_toutes(self):
        return self.service.lister_toutes()

    def rechercher_consultation(self, critere, code_session):
        return self.service.rechercher_consultation(critere, code_session)

    def obtenir_consultation_complete(self, code_consultation):
        return self.service.obtenir_consultation_complete(code_consultation)

    def obtenir_services_lies(self, code_consultation):
        return self.service.obtenir_services_lies(code_consultation)

    def obtenir_historique_patient(self, code_patient):
        return self.service.obtenir_historique_patient(code_patient)

    # === PATIENTS ===

    def obtenir_patients_attente(self, code_session):
        return self.service.obtenir_patients_attente(code_session)

    def obtenir_patients_examen(self, code_session):
        return self.service.obtenir_patients_examen(code_session)

    def obtenir_patients_chirurgie(self, code_session):
        return self.service.obtenir_patients_chirurgie(code_session)

    def obtenir_patients_lunette(self, code_session):
        return self.service.obtenir_patients_lunette(code_session)

    def obtenir_patients_prescription(self, code_session):
        return self.service.obtenir_patients_prescription(code_session)

    def info_cabinet(self):
        return self.service.info_cabinet()

    # === STATISTIQUES CARDS ===

    def obtenir_nombre_total(self, code_session):
        return self.service.obtenir_nombre_total(code_session)

    def obtenir_consultations_aujourd_hui(self, code_session):
        return self.service.obtenir_consultations_aujourd_hui(code_session)

    def obtenir_nombre_patients_en_attente(self, code_session):
        return self.service.obtenir_nombre_patients_en_attente(code_session)

    def obtenir_montant_aujourd_hui(self, code_session):
        return self.service.obtenir_montant_aujourd_hui(code_session)

    def obtenir_montant_session(self, code_session):
        return self.service.obtenir_montant_session(code_session)

    # === STATISTIQUES GRAPHES ===

    def obtenir_nombre_par_mois(self, code_session):
        return self.service.obtenir_nombre_par_mois(code_session)

    def obtenir_nombre_par_jour(self, code_session, annee=None, mois=None):
        return self.service.obtenir_nombre_par_jour(code_session, annee, mois)

    def obtenir_montant_par_mois(self, code_session):
        return self.service.obtenir_montant_par_mois(code_session)

    def obtenir_montant_par_jour(self, code_session, annee=None, mois=None):
        return self.service.obtenir_montant_par_jour(code_session, annee, mois)

    def obtenir_revenu_moyen_par_mois(self, code_session):
        return self.service.obtenir_revenu_moyen_par_mois(code_session)

    def obtenir_moyenne_montant_journalier_par_mois(self, code_session):
        return self.service.obtenir_moyenne_montant_journalier_par_mois(code_session)

    def obtenir_moyenne_consultations_par_mois(self, code_session):
        return self.service.obtenir_moyenne_consultations_par_mois(code_session)

    def obtenir_moyenne_nombre_journalier_par_mois(self, code_session):
        return self.service.obtenir_moyenne_nombre_journalier_par_mois(code_session)

    def obtenir_moyenne_journaliere_par_mois(self, code_session):
        return self.service.obtenir_moyenne_journaliere_par_mois(code_session)

    def obtenir_resume_session(self, code_session):
        return self.service.obtenir_resume_session(code_session)

    def obtenir_revenu_total(self, code_session, date_debut=None, date_fin=None):
        return self.service.obtenir_revenu_total(code_session, date_debut, date_fin)

    def obtenir_top_diagnostics(self, code_session, limite=10):
        return self.service.obtenir_top_diagnostics(code_session, limite)

    def obtenir_consultations_par_personnel(self, code_session):
        return self.service.obtenir_consultations_par_personnel(code_session)

    def obtenir_taux_conversion(self, code_session):
        return self.service.obtenir_taux_conversion(code_session)

    # === CABINET ===

    def get_cabinet_info(self):
        return self.service.get_cabinet_info()

    def lister_personnel(self):
        return self.service.lister_personnel()

    # === RECHERCHE AVANCEE ===

    def rechercher_entre_dates(self, code_session, date_debut, date_fin):
        return self.service.rechercher_entre_dates(code_session, date_debut, date_fin)

    def rechercher_par_services(self, code_session, examen=None, chirurgie=None,
                                commandelunette=None, prescription=None):
        return self.service.rechercher_par_services(
            code_session, examen, chirurgie, commandelunette, prescription
        )

    def obtenir_consultations_par_patient_par_mois(self, code_session, code_patient=None):
        return self.service.obtenir_consultations_par_patient_par_mois(code_session, code_patient)

    def obtenir_nombre_par_mois_filtre(self, code_session, examen=None,
                                       chirurgie=None, commandelunette=None, prescription=None):
        return self.service.obtenir_nombre_par_mois_filtre(
            code_session, examen, chirurgie, commandelunette, prescription
        )

    def obtenir_codes_patients_session(self, code_session):
        return self.service.obtenir_codes_patients_session(code_session)
