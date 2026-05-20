"""
Service Historique Patient
Orchestrateur centralisant les appels aux différents services :
- Visite
- Consultation
- Acte Médical
- Examen
- Chirurgie
- Lunette
- Prescription
- Résultat Médical
"""
import logging
from typing import List, Dict, Optional


class HistoriquePatientService:
    """Service orchestrateur pour l'historique complet d'un patient"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Import des services nécessaires
        from service_metier.visite_service import VisiteService
        from service_metier.consultation_service import ConsultationService
        from service_metier.acte_medicale_service import ActeMedicalService
        from service_metier.examen_service import ExamenService
        from service_metier.chirurgie_service import ChirurgieService
        from service_metier.lunette_service import CommandeLunetteService
        from service_metier.prescription_service import PrescriptionService
        from service_metier.resultat_medical_service import ResultatMedicalService
        
        # Initialiser les services
        self.visite_service = VisiteService()
        self.consultation_service = ConsultationService()
        self.acte_service = ActeMedicalService()
        self.examen_service = ExamenService()
        self.chirurgie_service = ChirurgieService()
        self.lunette_service = CommandeLunetteService()
        self.prescription_service = PrescriptionService()
        self.resultat_service = ResultatMedicalService()
    
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
        try:
            visites = self.visite_service.lister_visites_par_patient(code_patient)
            
            # Convertir en liste de dictionnaires
            result = []
            for visite in visites:
                if hasattr(visite, 'to_dict'):
                    result.append(visite.to_dict())
                elif isinstance(visite, dict):
                    result.append(visite)
                else:
                    result.append({
                        'code_visite': getattr(visite, 'code_visite', 'N/A'),
                        'date_visite': getattr(visite, 'date_visite', None),
                        'type_visite': getattr(visite, 'type_visite', 'N/A'),
                        'statut_visite': getattr(visite, 'statut_visite', 'N/A'),
                        'statut_patient': getattr(visite, 'statut_patient', 'N/A'),
                        'code_patient': getattr(visite, 'code_patient', 'N/A'),
                        'code_session': getattr(visite, 'code_session', 'N/A'),
                        'urgent': getattr(visite, 'urgent', 'Non'),
                    })
            
            self.logger.info(f"Visites trouvées pour {code_patient}: {len(result)}")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur lister_visites_patient: {e}")
            return []
    
    def get_visite_detail(self, code_visite: str) -> Optional[Dict]:
        """
        Retourne les détails complets d'une visite
        
        Args:
            code_visite: Code de la visite
            
        Returns:
            Dictionnaire avec les détails de la visite
        """
        try:
            visite = self.visite_service.obtenir_visite(code_visite)
            if visite:
                if hasattr(visite, 'to_dict'):
                    return visite.to_dict()
                return visite
            return None
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
        try:
            consultations = self.consultation_service.lister_consultations_par_visite(code_visite)
            
            # Convertir en liste de dictionnaires
            result = []
            for consultation in consultations:
                if hasattr(consultation, 'to_dict'):
                    result.append(consultation.to_dict())
                elif isinstance(consultation, dict):
                    result.append(consultation)
                else:
                    result.append({
                        'code': getattr(consultation, 'code', 'N/A'),
                        'date_consultation': getattr(consultation, 'date_consultation', None),
                        'diagnostique': getattr(consultation, 'diagnostique', 'N/A'),
                        'frais_consultation': getattr(consultation, 'frais_consultation', 0),
                        'statut_facture': getattr(consultation, 'statut_facture', 'N/A'),
                        'code_visite': getattr(consultation, 'code_visite', 'N/A'),
                        'code_personnel': getattr(consultation, 'code_personnel', 'N/A'),
                    })
            
            self.logger.info(f"Consultations trouvées pour visite {code_visite}: {len(result)}")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur lister_consultations_visite: {e}")
            return []
    
    def get_consultation_detail(self, code_consultation: str) -> Optional[Dict]:
        """
        Retourne les détails complets d'une consultation
        
        Args:
            code_consultation: Code de la consultation
            
        Returns:
            Dictionnaire avec les détails de la consultation
        """
        try:
            consultation = self.consultation_service.obtenir_consultation(code_consultation)
            if consultation:
                if hasattr(consultation, 'to_dict'):
                    return consultation.to_dict()
                return consultation
            return None
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
        try:
            # Récupérer tous les actes médicaux de la consultation
            actes = self.acte_service.lister_actes_par_consultation(code_consultation)
            
            result = []
            for acte in actes:
                acte_dict = {}
                
                if hasattr(acte, 'to_dict'):
                    acte_dict = acte.to_dict()
                elif isinstance(acte, dict):
                    acte_dict = acte.copy()
                else:
                    acte_dict = {
                        'code_acte': getattr(acte, 'code_acte', 'N/A'),
                        'type_acte': getattr(acte, 'type_acte', 'N/A'),
                        'decision_medicale': getattr(acte, 'decision_medicale', 'N/A'),
                        'statut_acte': getattr(acte, 'statut_acte', 'N/A'),
                        'code_consultation': getattr(acte, 'code_consultation', 'N/A'),
                    }
                
                # Enrichir avec les détails selon le type d'acte
                type_acte = acte_dict.get('type_acte', '').lower()
                code_acte = acte_dict.get('code_acte')
                
                if type_acte == 'examen':
                    details = self._get_examen_details(code_acte)
                    if details:
                        acte_dict.update({
                            'libelle': details.get('libelle_examen', 'N/A'),
                            'frais': details.get('frais_examen', 0),
                            'date': details.get('date_examen'),
                            'conclusion': details.get('conclusion_medicale', 'N/A'),
                        })
                
                elif type_acte == 'chirurgie':
                    details = self._get_chirurgie_details(code_acte)
                    if details:
                        acte_dict.update({
                            'libelle': details.get('libelle_chururgie', 'N/A'),
                            'frais': details.get('frais_chururgie', 0),
                            'date': details.get('date_chururgie'),
                            'compte_rendu': details.get('compte_rendu_operatoire', 'N/A'),
                        })
                
                elif type_acte == 'lunette':
                    details = self._get_lunette_details(code_acte)
                    if details:
                        acte_dict.update({
                            'libelle': f"Commande lunette - {details.get('type_verre', 'N/A')}",
                            'frais': details.get('prix_total', 0),
                            'date': details.get('date_commande'),
                            'statut_commande': details.get('statut_commande', 'N/A'),
                        })
                
                elif type_acte == 'prescription':
                    details = self._get_prescription_details(code_acte)
                    if details:
                        acte_dict.update({
                            'libelle': 'Prescription médicale',
                            'date': details.get('date_prescription'),
                            'nb_produits': len(details.get('produits', [])),
                        })
                
                result.append(acte_dict)
            
            self.logger.info(f"Actes trouvés pour consultation {code_consultation}: {len(result)}")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur lister_actes_consultation: {e}")
            return []
    
    def _get_examen_details(self, code_acte: str) -> Optional[Dict]:
        """Récupère les détails d'un examen"""
        try:
            examen = self.examen_service.obtenir_examen_par_acte(code_acte)
            if examen:
                if hasattr(examen, 'to_dict'):
                    return examen.to_dict()
                return examen
            return None
        except Exception as e:
            self.logger.error(f"Erreur _get_examen_details: {e}")
            return None
    
    def _get_chirurgie_details(self, code_acte: str) -> Optional[Dict]:
        """Récupère les détails d'une chirurgie"""
        try:
            chirurgie = self.chirurgie_service.obtenir_chirurgie_par_acte(code_acte)
            if chirurgie:
                if hasattr(chirurgie, 'to_dict'):
                    return chirurgie.to_dict()
                return chirurgie
            return None
        except Exception as e:
            self.logger.error(f"Erreur _get_chirurgie_details: {e}")
            return None
    
    def _get_lunette_details(self, code_acte: str) -> Optional[Dict]:
        """Récupère les détails d'une commande lunette"""
        try:
            lunette = self.lunette_service.obtenir_lunette_par_acte(code_acte)
            if lunette:
                if hasattr(lunette, 'to_dict'):
                    return lunette.to_dict()
                return lunette
            return None
        except Exception as e:
            self.logger.error(f"Erreur _get_lunette_details: {e}")
            return None
    
    def _get_prescription_details(self, code_acte: str) -> Optional[Dict]:
        """Récupère les détails d'une prescription"""
        try:
            prescription = self.prescription_service.obtenir_prescription_par_acte(code_acte)
            if prescription:
                if hasattr(prescription, 'to_dict'):
                    return prescription.to_dict()
                return prescription
            return None
        except Exception as e:
            self.logger.error(f"Erreur _get_prescription_details: {e}")
            return None
    
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
        try:
            resultats = self.resultat_service.lister_par_acte(code_acte)
            
            # Convertir en liste de dictionnaires
            result = []
            for resultat in resultats:
                if hasattr(resultat, 'to_dict'):
                    result.append(resultat.to_dict())
                elif isinstance(resultat, dict):
                    result.append(resultat)
                else:
                    result.append({
                        'id_resultat': getattr(resultat, 'id_resultat', 'N/A'),
                        'type_source': getattr(resultat, 'type_source', 'N/A'),
                        'type_fichier': getattr(resultat, 'type_fichier', 'N/A'),
                        'description': getattr(resultat, 'description', 'N/A'),
                        'date_upload': getattr(resultat, 'date_upload', None),
                        'niveau_confidentialite': getattr(resultat, 'niveau_confidentialite', 'N/A'),
                    })
            
            self.logger.info(f"Résultats trouvés pour acte {code_acte}: {len(result)}")
            return result
            
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
        try:
            resultats = self.lister_resultats_acte(code_acte, '')
            return len(resultats)
        except Exception as e:
            self.logger.error(f"Erreur compter_resultats_acte: {e}")
            return 0
    
    # =========================================================================
    # MÉTHODES UTILITAIRES
    # =========================================================================
    
    def get_consultation_complete(self, code_consultation: str) -> Optional[Dict]:
        """Récupère une consultation complète avec tous ses détails pour impression"""
        try:
            return self.consultation_service.obtenir_consultation_complete(code_consultation)
        except Exception as e:
            self.logger.error(f"Erreur get_consultation_complete: {e}")
            return None
    
    def get_examen_complet(self, code_acte: str) -> Optional[Dict]:
        """Récupère un examen complet pour impression"""
        try:
            examen = self.examen_service.obtenir_par_acte(code_acte)
            if examen and hasattr(examen, 'code'):
                return self.examen_service.obtenir_examen_complet(examen.code)
            return None
        except Exception as e:
            self.logger.error(f"Erreur get_examen_complet: {e}")
            return None
    
    def get_chirurgie_complete(self, code_acte: str) -> Optional[Dict]:
        """Récupère une chirurgie complète pour impression"""
        try:
            chirurgie = self.chirurgie_service.obtenir_par_acte(code_acte)
            if chirurgie and hasattr(chirurgie, 'code'):
                return self.chirurgie_service.obtenir_chururgie_complete(chirurgie.code)
            return None
        except Exception as e:
            self.logger.error(f"Erreur get_chirurgie_complete: {e}")
            return None
    
    def get_lunette_complete(self, code_acte: str) -> Optional[Dict]:
        """Récupère une commande lunette complète pour impression"""
        try:
            lunette = self.lunette_service.obtenir_par_acte(code_acte)
            if lunette and hasattr(lunette, 'code'):
                return self.lunette_service.obtenir_commande_complete(lunette.code)
            return None
        except Exception as e:
            self.logger.error(f"Erreur get_lunette_complete: {e}")
            return None
    
    def get_prescription_complete(self, code_acte: str) -> Optional[Dict]:
        """Récupère une prescription complète pour impression"""
        try:
            # La prescription utilise directement le code_acte
            return self.prescription_service.obtenir_prescription_complete(code_acte)
        except Exception as e:
            self.logger.error(f"Erreur get_prescription_complete: {e}")
            return None
    
    def get_cabinet_info(self) -> Dict:
        """Récupère les informations du cabinet pour l'entête des PDF"""
        try:
            from parametre.config_cabinet import config_cabinet
            import os
            
            nom_cabinet = config_cabinet.get_nom_cabinet()
            adresse_cabinet = config_cabinet.get_adresse()
            logo_cabinet = config_cabinet.get_logo()
            
            final_logo = None
            if logo_cabinet:
                # Construire le chemin complet vers le logo
                script = os.path.dirname(__file__)
                path = os.path.join(script, "..", "connexion", "image", logo_cabinet)
                if os.path.exists(path):
                    final_logo = path
            
            return {
                'nom_cabinet': nom_cabinet,
                'adresse_cabinet': adresse_cabinet,
                'logo': final_logo
            }
        except Exception as e:
            self.logger.error(f"Erreur get_cabinet_info: {e}")
            return {}
    
    def get_parcours_complet_patient(self, code_patient: str) -> Dict:
        """
        Retourne le parcours médical complet d'un patient
        Structure hiérarchique complète
        
        Args:
            code_patient: Code du patient
            
        Returns:
            Dictionnaire avec toute la hiérarchie
        """
        try:
            parcours = {
                'code_patient': code_patient,
                'visites': []
            }
            
            # Récupérer toutes les visites
            visites = self.lister_visites_patient(code_patient)
            
            for visite in visites:
                visite_data = {
                    **visite,
                    'consultations': []
                }
                
                # Récupérer les consultations de cette visite
                consultations = self.lister_consultations_visite(visite['code_visite'])
                
                for consultation in consultations:
                    consultation_data = {
                        **consultation,
                        'actes': []
                    }
                    
                    # Récupérer les actes de cette consultation
                    actes = self.lister_actes_consultation(consultation['code'])
                    
                    for acte in actes:
                        acte_data = {
                            **acte,
                            'resultats': []
                        }
                        
                        # Récupérer les résultats de cet acte
                        resultats = self.lister_resultats_acte(
                            acte['code_acte'], 
                            acte['type_acte']
                        )
                        acte_data['resultats'] = resultats
                        
                        consultation_data['actes'].append(acte_data)
                    
                    visite_data['consultations'].append(consultation_data)
                
                parcours['visites'].append(visite_data)
            
            return parcours
            
        except Exception as e:
            self.logger.error(f"Erreur get_parcours_complet_patient: {e}")
            return {'code_patient': code_patient, 'visites': []}
