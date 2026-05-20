"""
Contrôleur pour les statistiques financières.
Fait le pont entre la vue et le service métier.
"""

import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service_metier.statistiques_financieres_service import StatistiquesFinancieresService


class StatistiquesFinancieresControleur:
    """
    Contrôleur pour les statistiques financières.
    Délègue toutes les opérations au service métier.
    """
    
    def __init__(self):
        self.service = StatistiquesFinancieresService()
        self.logger = logging.getLogger(__name__)
    
    # =========================================================================
    # MÉTHODES KPI CARDS - MONTANTS PAR SERVICE
    # =========================================================================
    
    def obtenir_montant_consultations(self, code_session: str) -> float:
        """Retourne le montant total des consultations pour la session."""
        return self.service.obtenir_montant_consultations(code_session)
    
    def obtenir_montant_examens(self, code_session: str) -> float:
        """Retourne le montant total des examens pour la session."""
        return self.service.obtenir_montant_examens(code_session)
    
    def obtenir_montant_chirurgies(self, code_session: str) -> float:
        """Retourne le montant total des chirurgies pour la session."""
        return self.service.obtenir_montant_chirurgies(code_session)
    
    def obtenir_montant_lunettes(self, code_session: str) -> float:
        """Retourne le montant total des commandes de lunettes pour la session."""
        return self.service.obtenir_montant_lunettes(code_session)
    
    def obtenir_montant_prescriptions(self, code_session: str) -> float:
        """Retourne le montant total des prescriptions pour la session."""
        return self.service.obtenir_montant_prescriptions(code_session)
    
    def obtenir_montant_paiements_fournisseurs(self, code_session: str) -> float:
        """Retourne le montant total des paiements fournisseurs pour la session."""
        return self.service.obtenir_montant_paiements_fournisseurs(code_session)
    
    # =========================================================================
    # MÉTHODES COMPTABILITÉ JOURNALIÈRE
    # =========================================================================
    
    def obtenir_statistiques_journalieres(self, code_session: str) -> dict:
        """
        Retourne les statistiques de la journée en cours.
        Utilise les méthodes 'aujourd_hui' de chaque service.
        """
        return self.service.obtenir_statistiques_journalieres(code_session)
    
    # =========================================================================
    # MÉTHODES AGRÉGÉES - TOTAUX
    # =========================================================================
    
    def obtenir_total_encaissements(self, code_session: str) -> float:
        """
        Retourne le total des encaissements (revenus) pour la session.
        Somme : consultations + examens + chirurgies + lunettes + prescriptions
        """
        return self.service.obtenir_total_encaissements(code_session)
    
    def obtenir_total_decaissements(self, code_session: str) -> float:
        """
        Retourne le total des décaissements (dépenses) pour la session.
        Actuellement : paiements fournisseurs
        """
        return self.service.obtenir_total_decaissements(code_session)
    
    def obtenir_solde_net(self, code_session: str) -> float:
        """
        Retourne le solde net pour la session.
        Solde = Encaissements - Décaissements
        """
        return self.service.obtenir_solde_net(code_session)
    
    # =========================================================================
    # MÉTHODES TABLEAUX
    # =========================================================================
    
    def obtenir_valeur_stock_par_type(self, code_session: str) -> list:
        """
        Retourne la valeur du stock par type de produit.
        
        Returns:
            Liste de dicts : [{'type': 'Montures', 'valeur': 12450000, 'pourcentage': 35.6}, ...]
        """
        return self.service.obtenir_valeur_stock_par_type(code_session)
    
    def obtenir_transactions_recentes(self, code_session: str, limite: int = 10) -> list:
        """
        Retourne les transactions récentes (encaissements et décaissements).
        
        Returns:
            Liste de dicts avec date, description, catégorie, montant, type, méthode
        """
        return self.service.obtenir_transactions_recentes(code_session, limite)
    
    # =========================================================================
    # MÉTHODES STATISTIQUES COMPLÈTES
    # =========================================================================
    
    def obtenir_statistiques_completes(self, code_session: str) -> dict:
        """
        Retourne toutes les statistiques financières pour le dashboard.
        
        Returns:
            Dict contenant :
            - montants par service (consultations, examens, chirurgies, lunettes, prescriptions, fournisseurs)
            - totaux (encaissements, décaissements, solde)
            - métadonnées (code_session, date_generation)
        """
        return self.service.obtenir_statistiques_completes(code_session)
    
    def calculer_variation_mois_precedent(self, code_session: str, service: str) -> tuple:
        """
        Calcule la variation en pourcentage par rapport au mois précédent.
        
        Args:
            code_session: Code de la session
            service: 'consultations', 'examens', 'chirurgies', 'lunettes', 'prescriptions'
        
        Returns:
            tuple: (pourcentage, est_positif)
        """
        return self.service.calculer_variation_mois_precedent(code_session, service)
