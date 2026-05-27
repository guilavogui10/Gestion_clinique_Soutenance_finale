"""
Contrôleur Historique Patient
Fait le lien entre la vue et le service orchestrateur
"""
import logging
from typing import List, Dict, Optional


class HistoriquePatientControleur:
    """Contrôleur pour la gestion de l'historique patient"""
    
    def __init__(self):
        from service_metier.historique_patient_service import HistoriquePatientService
        self.service = HistoriquePatientService()
        self.logger = logging.getLogger(__name__)
    
    # =========================================================================
    # NIVEAU 1 : VISITES
    # =========================================================================
    
    def lister_visites_patient(self, code_patient: str) -> List[Dict]:
        """
        Retourne toutes les visites d'un patient
        
        Args:
            code_patient: Code du patient (ex: PAT-00000001)
            
        Returns:
            Liste de dictionnaires contenant les infos des visites
        """
        if not code_patient or not code_patient.strip():
            self.logger.warning("Code patient vide")
            return []
        
        try:
            return self.service.lister_visites_patient(code_patient.strip())
        except Exception as e:
            self.logger.error(f"Erreur lister_visites_patient: {e}")
            return []
    
    def get_visite_detail(self, code_visite: str) -> Optional[Dict]:
        """
        Retourne les détails complets d'une visite
        
        Args:
            code_visite: Code de la visite
            
        Returns:
            Dictionnaire avec les détails de la visite ou None
        """
        if not code_visite or not code_visite.strip():
            self.logger.warning("Code visite vide")
            return None
        
        try:
            return self.service.get_visite_detail(code_visite.strip())
        except Exception as e:
            self.logger.error(f"Erreur get_visite_detail: {e}")
            return None
    
    # =========================================================================
    # NIVEAU 2 : CONSULTATIONS
    # =========================================================================
    
    def lister_consultations_visite(self, code_visite: str) -> List[Dict]:
        """
        Retourne toutes les consultations d'une visite
        
        Args:
            code_visite: Code de la visite
            
        Returns:
            Liste de dictionnaires contenant les infos des consultations
        """
        if not code_visite or not code_visite.strip():
            self.logger.warning("Code visite vide")
            return []
        
        try:
            return self.service.lister_consultations_visite(code_visite.strip())
        except Exception as e:
            self.logger.error(f"Erreur lister_consultations_visite: {e}")
            return []
    
    def get_consultation_detail(self, code_consultation: str) -> Optional[Dict]:
        """
        Retourne les détails complets d'une consultation
        
        Args:
            code_consultation: Code de la consultation
            
        Returns:
            Dictionnaire avec les détails de la consultation ou None
        """
        if not code_consultation or not code_consultation.strip():
            self.logger.warning("Code consultation vide")
            return None
        
        try:
            return self.service.get_consultation_detail(code_consultation.strip())
        except Exception as e:
            self.logger.error(f"Erreur get_consultation_detail: {e}")
            return None
    
    # =========================================================================
    # NIVEAU 3 : ACTES MÉDICAUX
    # =========================================================================
    
    def lister_actes_consultation(self, code_consultation: str) -> List[Dict]:
        """
        Retourne tous les actes médicaux d'une consultation
        Inclut : examens, chirurgies, lunettes, prescriptions
        
        Args:
            code_consultation: Code de la consultation
            
        Returns:
            Liste de dictionnaires contenant les infos des actes
        """
        if not code_consultation or not code_consultation.strip():
            self.logger.warning("Code consultation vide")
            return []
        
        try:
            return self.service.lister_actes_consultation(code_consultation.strip())
        except Exception as e:
            self.logger.error(f"Erreur lister_actes_consultation: {e}")
            return []
    
    # =========================================================================
    # NIVEAU 4 : RÉSULTATS MÉDICAUX
    # =========================================================================
    
    def lister_resultats_acte(self, code_acte: str, type_acte: str) -> List[Dict]:
        """
        Retourne tous les résultats médicaux d'un acte
        
        Args:
            code_acte: Code de l'acte médical
            type_acte: Type d'acte (examen, chirurgie, etc.)
            
        Returns:
            Liste de dictionnaires contenant les infos des résultats
        """
        if not code_acte or not code_acte.strip():
            self.logger.warning("Code acte vide")
            return []
        
        try:
            return self.service.lister_resultats_acte(code_acte.strip(), type_acte)
        except Exception as e:
            self.logger.error(f"Erreur lister_resultats_acte: {e}")
            return []
    
    def compter_resultats_acte(self, code_acte: str) -> int:
        """
        Compte le nombre de résultats pour un acte
        
        Args:
            code_acte: Code de l'acte médical
            
        Returns:
            Nombre de résultats
        """
        if not code_acte or not code_acte.strip():
            return 0
        
        try:
            return self.service.compter_resultats_acte(code_acte.strip())
        except Exception as e:
            self.logger.error(f"Erreur compter_resultats_acte: {e}")
            return 0
    
    # =========================================================================
    # MÉTHODES UTILITAIRES
    # =========================================================================
    
    def get_parcours_complet_patient(self, code_patient: str) -> Dict:
        """
        Retourne le parcours médical complet d'un patient
        Structure hiérarchique complète : Visites → Consultations → Actes → Résultats
        
        Args:
            code_patient: Code du patient
            
        Returns:
            Dictionnaire avec toute la hiérarchie
        """
        if not code_patient or not code_patient.strip():
            self.logger.warning("Code patient vide")
            return {'code_patient': '', 'visites': []}
        
        try:
            return self.service.get_parcours_complet_patient(code_patient.strip())
        except Exception as e:
            self.logger.error(f"Erreur get_parcours_complet_patient: {e}")
            return {'code_patient': code_patient, 'visites': []}
    
    def valider_code_patient(self, code_patient: str) -> tuple[bool, str]:
        """
        Valide un code patient
        
        Args:
            code_patient: Code du patient à valider
            
        Returns:
            (bool, str): (valide, message)
        """
        if not code_patient or not code_patient.strip():
            return False, "Le code patient est obligatoire"
        
        if not code_patient.startswith("PAT-"):
            return False, "Le code patient doit commencer par 'PAT-'"
        
        return True, ""
    
    def valider_code_visite(self, code_visite: str) -> tuple[bool, str]:
        """
        Valide un code visite
        
        Args:
            code_visite: Code de la visite à valider
            
        Returns:
            (bool, str): (valide, message)
        """
        if not code_visite or not code_visite.strip():
            return False, "Le code visite est obligatoire"
        
        # Vérifier le format (peut varier selon votre implémentation)
        # Exemple : VIS-00000001
        
        return True, ""
    
    def valider_code_consultation(self, code_consultation: str) -> tuple[bool, str]:
        """
        Valide un code consultation
        
        Args:
            code_consultation: Code de la consultation à valider
            
        Returns:
            (bool, str): (valide, message)
        """
        if not code_consultation or not code_consultation.strip():
            return False, "Le code consultation est obligatoire"
        
        return True, ""
    
    def valider_code_acte(self, code_acte: str) -> tuple[bool, str]:
        """
        Valide un code acte médical
        
        Args:
            code_acte: Code de l'acte à valider
            
        Returns:
            (bool, str): (valide, message)
        """
        if not code_acte or not code_acte.strip():
            return False, "Le code acte est obligatoire"
        
        return True, ""
    
    # =========================================================================
    # MÉTHODES POUR IMPRESSION
    # =========================================================================
    
    def get_consultation_complete(self, code_consultation: str) -> Optional[Dict]:
        """
        Récupère une consultation complète pour impression
        
        Args:
            code_consultation: Code de la consultation
            
        Returns:
            Dictionnaire avec tous les détails de la consultation
        """
        if not code_consultation or not code_consultation.strip():
            self.logger.warning("Code consultation vide")
            return None
        
        try:
            return self.service.get_consultation_complete(code_consultation.strip())
        except Exception as e:
            self.logger.error(f"Erreur get_consultation_complete: {e}")
            return None
    
    def get_examen_complet(self, code_acte: str) -> Optional[Dict]:
        """
        Récupère un examen complet pour impression
        
        Args:
            code_acte: Code de l'acte examen
            
        Returns:
            Dictionnaire avec tous les détails de l'examen
        """
        if not code_acte or not code_acte.strip():
            self.logger.warning("Code acte vide")
            return None
        
        try:
            return self.service.get_examen_complet(code_acte.strip())
        except Exception as e:
            self.logger.error(f"Erreur get_examen_complet: {e}")
            return None
    
    def get_chirurgie_complete(self, code_acte: str) -> Optional[Dict]:
        """
        Récupère une chirurgie complète pour impression
        
        Args:
            code_acte: Code de l'acte chirurgie
            
        Returns:
            Dictionnaire avec tous les détails de la chirurgie
        """
        if not code_acte or not code_acte.strip():
            self.logger.warning("Code acte vide")
            return None
        
        try:
            return self.service.get_chirurgie_complete(code_acte.strip())
        except Exception as e:
            self.logger.error(f"Erreur get_chirurgie_complete: {e}")
            return None
    
    def get_lunette_complete(self, code_acte: str) -> Optional[Dict]:
        """
        Récupère une commande lunette complète pour impression
        
        Args:
            code_acte: Code de l'acte lunette
            
        Returns:
            Dictionnaire avec tous les détails de la commande
        """
        if not code_acte or not code_acte.strip():
            self.logger.warning("Code acte vide")
            return None
        
        try:
            return self.service.get_lunette_complete(code_acte.strip())
        except Exception as e:
            self.logger.error(f"Erreur get_lunette_complete: {e}")
            return None
    
    def get_prescription_complete(self, code_acte: str) -> Optional[Dict]:
        """
        Récupère une prescription complète pour impression
        
        Args:
            code_acte: Code de l'acte prescription
            
        Returns:
            Dictionnaire avec tous les détails de la prescription
        """
        if not code_acte or not code_acte.strip():
            self.logger.warning("Code acte vide")
            return None
        
        try:
            return self.service.get_prescription_complete(code_acte.strip())
        except Exception as e:
            self.logger.error(f"Erreur get_prescription_complete: {e}")
            return None
            
    def get_facture_par_visite(self, code_visite: str) -> Optional[Dict]:
        """
        Récupère la facture associée à une visite et son statut
        
        Args:
            code_visite: Code de la visite
            
        Returns:
            Dictionnaire avec les détails de la facture ou None
        """
        if not code_visite or not code_visite.strip():
            self.logger.warning("Code visite vide")
            return None
        
        try:
            return self.service.get_facture_par_visite(code_visite.strip())
        except Exception as e:
            self.logger.error(f"Erreur get_facture_par_visite: {e}")
            return None
    
    def generer_facture_pdf(self, code_facture: str, chemin_fichier: str) -> tuple[bool, str]:
        """
        Génère le PDF de facture patient avec le détail des services.
        
        Args:
            code_facture: Code de la facture
            chemin_fichier: Chemin de destination
            
        Returns:
            (succès, message)
        """
        if not code_facture or not code_facture.strip():
            return False, "Le code facture est obligatoire"
            
        try:
            return self.service.facture_service.generer_facture_pdf(code_facture.strip(), chemin_fichier)
        except Exception as e:
            self.logger.error(f"Erreur generer_facture_pdf: {e}")
            return False, f"Erreur lors de la génération de la facture: {str(e)}"
    
    def get_cabinet_info(self) -> Dict:
        """
        Récupère les informations du cabinet pour l'entête des PDF
        
        Returns:
            Dictionnaire avec nom_cabinet, adresse_cabinet, logo
        """
        try:
            return self.service.get_cabinet_info()
        except Exception as e:
            self.logger.error(f"Erreur get_cabinet_info: {e}")
            return {}
