"""
controleur_patient.py
----------------------
Contrôleur MVC — Couche mince qui délègue au PatientService.

Le contrôleur ne contient AUCUNE logique métier.
Il instancie le service et redirige chaque appel de la vue vers le service.
"""

from service_metier.patient_service import PatientService
from models.model_patient import Patient


class ControleurPatient:
    """Contrôleur mince pour la gestion des patients."""

    def __init__(self):
        self.service = PatientService()
        self.patientdao = self.service.dao
        self.patient_objet = Patient

    # =========================================================================
    # VALIDATION (délégation au service)
    # =========================================================================

    def _valider_nom(self, nom):
        return self.service._valider_nom(nom)

    def _valider_prenom(self, prenom):
        return self.service._valider_prenom(prenom)

    def _valider_telephone(self, telephone):
        return self.service._valider_telephone(telephone)

    def _valider_date(self, naissance):
        return self.service._valider_date(naissance)

    def _valider_genre(self, genre):
        return self.service._valider_genre(genre)

    def _valider_profession(self, profession):
        return self.service._valider_profession(profession)

    def _valider_adresse(self, adresse):
        return self.service._valider_adresse(adresse)

    def _control_exist(self, telephone):
        return self.service._control_exist(telephone)

    # =========================================================================
    # CRUD (délégation au service)
    # =========================================================================

    def save_patient(self, patient_objet):
        return self.service.save_patient(patient_objet)

    def update_patient(self, patient_update):
        return self.service.update_patient(patient_update)

    # =========================================================================
    # RÉCUPÉRATION (délégation au service)
    # =========================================================================

    def reed_Allpatient(self):
        return self.service.reed_Allpatient()

    def reed_by_code_patient(self, code_patient):
        return self.service.reed_by_code_patient(code_patient)

    def reed_by_sexe_patient(self, sexe):
        return self.service.reed_by_sexe_patient(sexe)

    def reed_by_critere_patient(self, critere):
        return self.service.reed_by_critere_patient(critere)

    # =========================================================================
    # STATISTIQUES (délégation au service)
    # =========================================================================

    def statistique(self):
        return self.service.statistique()

    # =========================================================================
    # EXPORT / IMPORT (délégation au service)
    # =========================================================================

    def obtenir_donnees_pour_export(self):
        return self.service.obtenir_donnees_pour_export()

    def export_to_excel(self, fichier):
        return self.service.export_to_excel(fichier)

    def export_to_csv(self, fichier):
        return self.service.export_to_csv(fichier)

    def import_from_excel(self, fichier):
        return self.service.import_from_excel(fichier)

    def import_from_csv(self, chemin_fichier):
        return self.service.import_from_csv(chemin_fichier)

    # =========================================================================
    # INFORMATIONS CABINET (délégation au service)
    # =========================================================================

    def get_cabinet_info(self):
        return self.service.get_cabinet_info()

    # =========================================================================
    # GÉNÉRATION PDF (délégation au service)
    # =========================================================================

    def generer_carnet_par_code(self, code_patient, dossier_destination):
        return self.service.generer_carnet_par_code(code_patient, dossier_destination)

    def generer_liste_patients_par_genre(self, genre, dossier_destination):
        return self.service.generer_liste_patients_par_genre(genre, dossier_destination)

    def generer_liste_total_patient(self, dossier_destination):
        return self.service.generer_liste_total_patient(dossier_destination)

    def generer_rapport_patients(self):
        """Retourne le chemin du PDF temporaire pour ApercuPDFDialog."""
        return self.service.generer_rapport_patients()

    def generer_dossier_medical(self, code_patient):
        """Génère le PDF dossier médical complet pour un patient."""
        from services.pdf_patient.pdf_dossier_medical import DossierMedicalPDF
        from controllers.controleur_consultation import ConsultationControleur
        from controllers.controleur_examen import ExamenControleur
        from controllers.controleur_chururgie import ChirurgieControleur
        from controllers.controleur_lunette import CommandeLunetteControleur
        from controllers.controleur_prescription import PrescriptionControleur
        from controllers.controleur_rendez_vous import RendezVousControleur
        from controllers.controleur_historique_patient import HistoriquePatientControleur

        patient      = self.reed_by_code_patient(code_patient)
        info_cabinet = self.get_cabinet_info()

        visites       = HistoriquePatientControleur().lister_visites_patient(code_patient)       or []
        consultations = ConsultationControleur().obtenir_historique_patient(code_patient)        or []
        examens       = ExamenControleur().obtenir_historique_patient(code_patient)              or []
        chirurgies    = ChirurgieControleur().obtenir_historique_patient(code_patient)           or []
        lunettes      = CommandeLunetteControleur().obtenir_historique_patient(code_patient)     or []
        prescriptions = PrescriptionControleur().obtenir_historique_patient(code_patient)        or []
        rendez_vous   = RendezVousControleur().obtenir_historique_patient(code_patient)          or []

        return DossierMedicalPDF.generer(
            patient, visites, consultations, examens, chirurgies,
            prescriptions, lunettes, rendez_vous, info_cabinet
        )





    
        
    
    
