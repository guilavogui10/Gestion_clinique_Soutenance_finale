import sys
import os
import logging
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service_metier.acte_medicale_service import ActeMedicalService
from service_metier.file_attente_service import FileAttenteService
from service_metier.parcours_patient_service import ParcoursPatientService
from service_metier.resultat_medical_service import ResultatMedicalService
from data.dao_acte_medicale import StatutActe, ChoixPatient, TypeActe
from models.model_acte_medicale import ActeMedical


class ActeMedicalControleur:
    """
    Contrôleur MVC — point d'entrée unique pour la gestion des actes médicaux.
    Délègue :
      - prescription / workflow d'état  → ActeMedicalService
      - file d'attente / passages       → FileAttenteService
      - parcours / analytics            → ParcoursPatientService
    """

    def __init__(self):
        self.service_acte     = ActeMedicalService()
        self.service_file     = FileAttenteService()
        self.service_parcours = ParcoursPatientService()
        self.service_resultat = ResultatMedicalService()
        self.logger           = logging.getLogger(__name__)

    # =========================================================================
    # SECTION 1 — CRUD (ActeMedicalService)
    # =========================================================================

    def creer_acte(self, acte: ActeMedical) -> tuple:
        """Crée un acte médical via le service (validation incluse)."""
        return self.service_acte.creer_acte(acte)

    def creer_acte_intelligent(self, code_consultation: str,
                                type_acte: str,
                                decision_medicale: str,
                                source_acte: str = "consultation") -> tuple:
        """
        Crée un acte médical via la factory du service.
        Retourne (acte_objet, message) ou (None, message_erreur).
        """
        return self.service_acte.creer_acte_intelligent(
            code_consultation=code_consultation,
            type_acte=type_acte,
            decision_medicale=decision_medicale,
            source_acte=source_acte,
        )

    def creer_actes_depuis_recommandations(self, code_consultation: str,
                                            recommandations: list) -> tuple:
        """
        Crée plusieurs actes depuis une liste de recommandations médicales.
        Format : [{"type_acte": "examen", "decision_medicale": "..."}, ...]
        Retourne (liste_actes, message).
        """
        return self.service_acte.creer_actes_depuis_recommandations(
            code_consultation, recommandations
        )

    def modifier_acte(self, acte: ActeMedical) -> tuple:
        """Met à jour un acte existant."""
        return self.service_acte.modifier_acte(acte)

    def supprimer_acte(self, id_acte: int) -> tuple:
        """Supprime un acte (refusé si en cours)."""
        return self.service_acte.supprimer_acte(id_acte)

    def lier_acte_parent(self, id_acte_child: int, id_acte_parent: int) -> tuple:
        """Chaîne deux actes (parent → enfant)."""
        return self.service_acte.lier_acte_parent(id_acte_child, id_acte_parent)

    # =========================================================================
    # SECTION 2 — RÉCUPÉRATION
    # =========================================================================

    def obtenir_acte(self, code_acte: str) -> Optional[ActeMedical]:
        """Retourne un acte médical par son code."""
        return self.service_acte.obtenir_par_id(code_acte)

    def lister_par_consultation(self, code_consultation: str) -> list:
        """Retourne tous les actes d'une consultation."""
        return self.service_acte.lister_par_consultation(code_consultation)

    def lister_par_type(self, type_acte: str) -> list:
        """Retourne tous les actes d'un type donné."""
        return self.service_acte.lister_par_type(type_acte)

    def lister_par_statut(self, statut: str) -> list:
        """Retourne tous les actes d'un statut donné."""
        return self.service_acte.lister_par_statut(statut)

    def lister_tous(self, limit: int = 1000) -> list:
        """Retourne tous les actes (limités pour la performance)."""
        return self.service_acte.lister_tous(limit)

    # =========================================================================
    # SECTION 3 — WORKFLOW / TRANSITIONS D'ÉTATS (ActeMedicalService)
    # =========================================================================

    def passer_en_cours(self, code_acte: str) -> tuple:
        """Démarre l'exécution d'un acte."""
        return self.service_acte.passer_en_cours(code_acte)

    def terminer_acte(self, code_acte: str, raison: str = None) -> tuple:
        """Clôture un acte en cours."""
        return self.service_acte.terminer_acte(code_acte, raison)

    def refuser_acte(self, code_acte: str, raison: str = None) -> tuple:
        """Refuse un acte avec une raison."""
        return self.service_acte.refuser_acte(code_acte, raison)

    def planifier_acte(self, code_acte: str) -> tuple:
        """Place un acte en statut planifie."""
        return self.service_acte.planifier_acte(code_acte)

    # =========================================================================
    # SECTION 4 — CHOIX PATIENT (ActeMedicalService)
    # =========================================================================

    def enregistrer_choix_patient(self, code_acte: str, choix: str) -> tuple:
        """Enregistre le choix du patient et déclenche la cascade workflow."""
        return self.service_acte.enregistrer_choix_patient(code_acte, choix)

    def patient_choisit_maintenant(self, code_acte: str) -> tuple:
        return self.service_acte.patient_choisit_maintenant(code_acte)

    def patient_choisit_plus_tard(self, code_acte: str) -> tuple:
        return self.service_acte.patient_choisit_plus_tard(code_acte)

    def patient_choisit_ailleurs(self, code_acte: str, raison: str = None) -> tuple:
        return self.service_acte.patient_choisit_ailleurs(code_acte, raison)

    def planifier_rendez_vous(self, code_acte: str, date_rdv) -> tuple:
        """Planifie un RDV (stub — délègue au service si implémenté)."""
        return self.service_acte.planifier_rendez_vous(code_acte, date_rdv)

    # =========================================================================
    # SECTION 5 — FILE D'ATTENTE (FileAttenteService)
    # =========================================================================

    def entrer_en_file(self, code_acte: str, code_visite: str) -> tuple:
        """Place un acte en file d'attente d'exécution."""
        return self.service_file.entrer_en_file(code_acte, code_visite)

    def lier_visite_origine(self, code_acte: str, code_visite: str) -> tuple:
        """Enregistre la visite de prescription (role=origine)."""
        return self.service_file.lier_visite_origine(code_acte, code_visite)

    def demarrer_passage(self, id_acte_visite: int) -> tuple:
        """Démarre le passage d'un patient (acte_visite + acte_medical)."""
        return self.service_file.demarrer_passage(id_acte_visite)
    
    def demarrer_passage_par_code_acte(self, code_acte: int) -> tuple:
        """Démarre le passage d'un patient en utilisant le code_acte."""
        return self.service_file.demarrer_passage_par_code_acte(code_acte)

    def terminer_passage(self, id_acte_visite: int, raison: str = None) -> tuple:
        """Termine le passage d'un patient (acte_visite + acte_medical)."""
        return self.service_file.terminer_passage(id_acte_visite, raison)
    
    def terminer_passage_par_code_acte(self, code_acte: int, raison: str = None) -> tuple:
        """Termine le passage d'un patient en utilisant le code_acte."""
        return self.service_file.terminer_passage_par_code_acte(code_acte, raison)

    def obtenir_code_consultation_par_acte(self, code_acte: str) -> str | None:
        """Retourne le code_consultation associé à un code_acte."""
        acte = self.service_acte.obtenir_par_id(code_acte)
        return acte.code_consultation if acte else None

    def obtenir_code_visite_par_consultation(self, code_consultation: str) -> str | None:
        """Retourne le code_visite associé à une consultation."""
        return self.service_acte.obtenir_code_visite_par_consultation(code_consultation)

    def valider_sejour_patient(self, code_visite: str) -> tuple:
        """Passe le patient en 'Attente payement' (fin de séance, décision médecin)."""
        return self.service_file.valider_sejour_patient(code_visite)

    def enregistrer_controle(self, code_acte: str, code_session: str) -> tuple:
        """
        Enregistre l'arrivée d'un patient en visite de contrôle pour un acte.
        Crée une nouvelle visite + acte_visite(role='controle').
        Le patient va directement au service, sans passer par la consultation.
        """
        return self.service_file.enregistrer_controle(code_acte, code_session)

    def obtenir_file_attente(self, type_acte: str = None) -> list:
        """Retourne la file d'attente globale ou filtrée par service."""
        return self.service_file.obtenir_file_attente(type_acte)

    def obtenir_prochain_patient(self, type_acte: str = None):
        """Retourne le prochain passage à traiter."""
        return self.service_file.obtenir_prochain_patient(type_acte)

    def obtenir_en_cours(self, type_acte: str = None) -> list:
        """Retourne tous les passages en cours d'exécution."""
        return self.service_file.obtenir_en_cours(type_acte)

    def obtenir_taille_file(self, type_acte: str = None) -> dict:
        """Retourne le nombre de patients en attente."""
        return self.service_file.obtenir_taille_file(type_acte)

    def obtenir_passages(self, code_acte: str) -> list:
        """Retourne tous les passages (acte_visite) enregistrés pour un acte médical."""
        return self.service_parcours.dao_visite.get_visites_par_acte(code_acte)

    def obtenir_file_attente_enrichie(self, type_acte: str = None) -> list:
        """
        File d'attente (statut_passage=en_attente) avec données acte_medical jointes.
        Retourne des dicts : id_acte_visite, code_acte, code_visite, date_entree,
        statut_passage, type_acte, decision_medicale, code_consultation.
        """
        return self.service_file.obtenir_file_attente_enrichie(type_acte)

    def obtenir_en_cours_enrichi(self, type_acte: str = None) -> list:
        """Passages en cours avec données acte_medical jointes — dicts."""
        return self.service_file.obtenir_en_cours_enrichi(type_acte)

    def get_suivi_file_attente(self) -> list:
        """Retourne tous les patients actifs pour le suivi temps réel de la file d'attente."""
        return self.service_file.obtenir_suivi_actifs()

    def detecter_attentes_longues(self, seuil_minutes: int = 60) -> list:
        """Retourne les passages en attente depuis plus de seuil_minutes."""
        return self.service_file.detecter_attentes_longues(seuil_minutes)

    def rapport_alerte_service(self, type_acte: str) -> dict:
        """Rapport synthétique d'un service : taille file, en cours, alertes."""
        return self.service_file.rapport_alerte_service(type_acte)

    def transferer_acte(self, code_acte: str,
                         code_visite_cible: str,
                         nouveau_type_acte: str) -> tuple:
        """Transfère un acte vers un autre service."""
        return self.service_file.transferer_acte(code_acte, code_visite_cible, nouveau_type_acte)

    # =========================================================================
    # SECTION 6 — PARCOURS ET ANALYTICS (ParcoursPatientService)
    # =========================================================================

    def obtenir_parcours(self, code_consultation: str) -> list:
        """Retourne le parcours ordonné d'une consultation avec durées."""
        return self.service_parcours.obtenir_parcours(code_consultation)

    def obtenir_etat_global(self, code_consultation: str) -> dict:
        """Vue synthétique d'une consultation : actes par statut, durée totale."""
        return self.service_parcours.obtenir_etat_global(code_consultation)

    def obtenir_durees_acte(self, code_acte: str) -> dict:
        """Retourne les durées (attente / exécution / totale) pour un acte."""
        return self.service_parcours.obtenir_durees_acte(code_acte)

    def obtenir_durees_passage(self, id_acte_visite: int) -> dict:
        """Retourne les durées d'un passage spécifique."""
        return self.service_parcours.obtenir_durees_passage(id_acte_visite)

    def dashboard_global(self) -> dict:
        """KPIs globaux : files d'attente, passages en cours, actes par statut."""
        return self.service_parcours.dashboard_global()

    def detecter_anomalies(self) -> dict:
        """Détecte les incohérences de parcours et retourne un score de santé."""
        return self.service_parcours.detecter_anomalies()

    # =========================================================================
    # SECTION 7 — RENDEZ-VOUS (ActeMedicalService + RendezVousDAO)
    # =========================================================================

    def planifier_rendez_vous(self, code_acte: str, date_rdv,
                               code_personnel: str = None,
                               code_session: str = None) -> tuple:
        """Planifie un RDV pour un acte avec choix_patient='plus_tard'."""
        return self.service_acte.planifier_rendez_vous(
            code_acte, date_rdv, code_personnel, code_session
        )

    # =========================================================================
    # SECTION 8 — RÉSULTATS MÉDICAUX (ResultatMedicalService)
    # =========================================================================

    def enregistrer_resultat(self, type_source: str, type_fichier: str,
                              chemin_fichier: str,
                              code_acte_medical: str = None,
                              code_consultation: str = None,
                              description: str = None,
                              niveau_confidentialite: str = "moyen") -> tuple:
        """Enregistre un fichier résultat lié à un acte ou une consultation."""
        return self.service_resultat.enregistrer_resultat(
            type_source, type_fichier, chemin_fichier,
            code_acte_medical, code_consultation, description, niveau_confidentialite
        )

    def modifier_resultat(self, id_resultat: str,
                           description: str = None,
                           niveau_confidentialite: str = None) -> tuple:
        """Met à jour description et/ou niveau de confidentialité d'un résultat."""
        return self.service_resultat.modifier_resultat(
            id_resultat, description, niveau_confidentialite
        )

    def supprimer_resultat(self, id_resultat: str) -> tuple:
        """Supprime un résultat médical."""
        return self.service_resultat.supprimer_resultat(id_resultat)

    def obtenir_resultat(self, id_resultat: str):
        """Retourne un résultat par son id."""
        return self.service_resultat.obtenir_resultat(id_resultat)

    def lister_resultats_par_acte(self, code_acte_medical: str) -> list:
        """Retourne tous les résultats liés à un acte médical."""
        return self.service_resultat.lister_par_acte(code_acte_medical)

    def lister_resultats_par_consultation(self, code_consultation: str) -> list:
        """Retourne tous les résultats liés à une consultation."""
        return self.service_resultat.lister_par_consultation(code_consultation)

    def source_a_des_resultats(self, code_acte_medical: str = None, code_consultation: str = None) -> bool:
        """Vérifie si un acte ou une consultation possède au moins un résultat."""
        return self.service_resultat.source_a_des_resultats(code_acte_medical, code_consultation)

    def resume_resultats_acte(self, code_acte_medical: str) -> dict:
        """Résumé des résultats d'un acte médical groupés par type de fichier."""
        return self.service_resultat.resume_par_acte(code_acte_medical)

    def resume_resultats_consultation(self, code_consultation: str) -> dict:
        """Résumé des résultats d'une consultation groupés par type de fichier."""
        return self.service_resultat.resume_par_consultation(code_consultation)

    # =========================================================================
    # SECTION 9 — DONNÉES FORMULAIRE (listes déroulantes)
    # =========================================================================

    def lister_consultations_form(self) -> list:
        """Retourne les consultations actives pour les dropdowns du formulaire."""
        return self.service_acte.lister_consultations_form()

    def lister_sessions_form(self) -> list:
        """Retourne les sessions disponibles pour les dropdowns du formulaire."""
        return self.service_acte.lister_sessions_form()

    def lister_personnel_form(self, roles: list = None) -> list:
        """Retourne le personnel pour les dropdowns, filtré par rôles si fournis."""
        return self.service_acte.lister_personnel_form(roles)

    # =========================================================================
    # SECTION VISITE / CONSULTATION (délégation via services)
    # =========================================================================

    def demarrer_consultation(self, code_visite: str) -> tuple:
        """Démarre une consultation liée à une visite."""
        from service_metier.visite_service import VisiteService
        return VisiteService().demarrer_consultation(code_visite)

    def obtenir_consultation_par_visite(self, code_visite: str):
        """Retourne le code_consultation actif pour une visite, ou None."""
        from service_metier.consultation_service import ConsultationService
        consultation = ConsultationService().obtenir_par_visite(code_visite)
        if not consultation:
            return None
        return consultation.code if hasattr(consultation, 'code') else consultation.get('code')

    # =========================================================================
    # EXPORT / IMPORT ACTES
    # =========================================================================

    def obtenir_donnees_export(self, type_acte: str) -> list:
        from service_metier.acte_import_export_service import obtenir_donnees_export
        return obtenir_donnees_export(type_acte)

    def export_examens_excel(self, chemin: str) -> tuple:
        from service_metier.acte_import_export_service import export_examens_excel
        return export_examens_excel(chemin)

    def export_examens_csv(self, chemin: str) -> tuple:
        from service_metier.acte_import_export_service import export_examens_csv
        return export_examens_csv(chemin)

    def export_chirurgies_excel(self, chemin: str) -> tuple:
        from service_metier.acte_import_export_service import export_chirurgies_excel
        return export_chirurgies_excel(chemin)

    def export_chirurgies_csv(self, chemin: str) -> tuple:
        from service_metier.acte_import_export_service import export_chirurgies_csv
        return export_chirurgies_csv(chemin)

    def export_lunettes_excel(self, chemin: str) -> tuple:
        from service_metier.acte_import_export_service import export_lunettes_excel
        return export_lunettes_excel(chemin)

    def export_lunettes_csv(self, chemin: str) -> tuple:
        from service_metier.acte_import_export_service import export_lunettes_csv
        return export_lunettes_csv(chemin)

    def export_prescriptions_excel(self, chemin: str) -> tuple:
        from service_metier.acte_import_export_service import export_prescriptions_excel
        return export_prescriptions_excel(chemin)

    def export_prescriptions_csv(self, chemin: str) -> tuple:
        from service_metier.acte_import_export_service import export_prescriptions_csv
        return export_prescriptions_csv(chemin)

    def import_examens(self, chemin: str, format_fichier: str) -> tuple:
        from service_metier.acte_import_export_service import import_examens
        return import_examens(chemin, format_fichier)

    def import_chirurgies(self, chemin: str, format_fichier: str) -> tuple:
        from service_metier.acte_import_export_service import import_chirurgies
        return import_chirurgies(chemin, format_fichier)

    def import_lunettes(self, chemin: str, format_fichier: str) -> tuple:
        from service_metier.acte_import_export_service import import_lunettes
        return import_lunettes(chemin, format_fichier)

    def import_prescriptions(self, chemin: str, format_fichier: str) -> tuple:
        from service_metier.acte_import_export_service import import_prescriptions
        return import_prescriptions(chemin, format_fichier)
