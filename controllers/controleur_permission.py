"""
controleur_permission.py
------------------------
Contrôleur pour la gestion des permissions et autorisations.

Responsabilités:
- Coordination entre les vues et le service de permissions
- Vérification des droits d'accès
- Gestion des demandes d'autorisation OTP
- Validation des codes OTP
"""

import logging
from typing import Dict, Tuple, Optional

from service_metier.permission_service import PermissionService


class PermissionControleur:
    """
    Contrôleur pour la gestion des permissions.
    Fait le pont entre les vues et le service métier.
    """
    
    def __init__(self):
        """Initialise le contrôleur avec le service de permissions."""
        self.service = PermissionService()
        self.logger = logging.getLogger(__name__)
    
    # =========================================================================
    # VÉRIFICATION DES PERMISSIONS
    # =========================================================================
    
    def verifier_permission(
        self,
        code_utilisateur: str,
        role: str,
        est_responsable: bool,
        action: str
    ) -> Dict[str, any]:
        """
        Vérifie si un utilisateur a la permission d'effectuer une action.
        
        Args:
            code_utilisateur: Code de l'utilisateur
            role: Rôle/fonction de l'utilisateur
            est_responsable: True si l'utilisateur est responsable
            action: Action à vérifier (lecture, modification, suppression, etc.)
        
        Returns:
            Dict avec:
                - "autorise": bool
                - "message": str (raison du refus si non autorisé)
        """
        try:
            autorise, message = self.service.verifier_permission(
                code_utilisateur, role, est_responsable, action
            )
            
            return {
                "autorise": autorise,
                "message": message or ""
            }
            
        except Exception as e:
            self.logger.error(f"Erreur verifier_permission: {e}")
            return {
                "autorise": False,
                "message": "Erreur lors de la vérification des permissions."
            }
    
    def peut_effectuer_action(
        self,
        code_utilisateur: str,
        role: str,
        est_responsable: bool,
        action: str
    ) -> bool:
        """
        Vérifie rapidement si une action est autorisée.
        
        Returns:
            True si autorisé, False sinon
        """
        try:
            return self.service.peut_effectuer_action(
                code_utilisateur, role, est_responsable, action
            )
        except Exception as e:
            self.logger.error(f"Erreur peut_effectuer_action: {e}")
            return False
    
    # =========================================================================
    # GESTION DES AUTORISATIONS OTP
    # =========================================================================
    
    def demander_autorisation(
        self,
        code_utilisateur: str,
        role: str,
        action: str,
        contexte: str = "",
        est_responsable: bool = False
    ) -> Dict[str, any]:
        """
        Génère un code OTP et l'envoie au responsable pour autoriser une action.
        
        Args:
            code_utilisateur: Code de l'utilisateur demandeur
            role: Rôle/fonction de l'utilisateur
            action: Action demandée (modification, suppression)
            contexte: Description du contexte (ex: "Modification examen #123")
            est_responsable: True si l'utilisateur est responsable
        
        Returns:
            Dict avec:
                - "status": "success" ou "error"
                - "message": str
                - "email_masque": str (si success)
        """
        try:
            succes, message, email_masque = self.service.demander_autorisation_otp(
                code_utilisateur, role, action, contexte, est_responsable
            )
            
            if succes:
                return {
                    "status": "success",
                    "message": message,
                    "email_masque": email_masque
                }
            else:
                return {
                    "status": "error",
                    "message": message
                }
                
        except Exception as e:
            self.logger.error(f"Erreur demander_autorisation: {e}")
            return {
                "status": "error",
                "message": "Erreur lors de la demande d'autorisation."
            }
    
    def valider_autorisation(
        self,
        code_utilisateur: str,
        action: str,
        contexte: str,
        code_saisi: str
    ) -> Dict[str, any]:
        """
        Valide le code OTP saisi pour autoriser une action.
        
        Args:
            code_utilisateur: Code de l'utilisateur demandeur
            action: Action demandée
            contexte: Contexte de la demande
            code_saisi: Code OTP saisi
        
        Returns:
            Dict avec:
                - "status": "success" ou "error"
                - "message": str
        """
        try:
            valide, message = self.service.valider_autorisation_otp(
                code_utilisateur, action, contexte, code_saisi
            )
            
            return {
                "status": "success" if valide else "error",
                "message": message
            }
            
        except Exception as e:
            self.logger.error(f"Erreur valider_autorisation: {e}")
            return {
                "status": "error",
                "message": "Erreur lors de la validation du code."
            }
    
    # =========================================================================
    # VÉRIFICATION D'ACCÈS AUX INTERFACES
    # =========================================================================
    
    def peut_acceder_interface(self, role: str, interface: str) -> bool:
        """
        Vérifie si un rôle peut accéder à une interface donnée.
        
        Args:
            role: Rôle/fonction de l'utilisateur
            interface: Nom de l'interface (ex: "Examens", "Consultations")
        
        Returns:
            True si accès autorisé, False sinon
        """
        try:
            return self.service.peut_acceder_interface(role, interface)
        except Exception as e:
            self.logger.error(f"Erreur peut_acceder_interface: {e}")
            return False
    
    # =========================================================================
    # CONSTANTES D'ACTIONS (pour faciliter l'utilisation)
    # =========================================================================
    
    @property
    def ACTION_LECTURE(self) -> str:
        return PermissionService.ACTION_LECTURE
    
    @property
    def ACTION_IMPRESSION(self) -> str:
        return PermissionService.ACTION_IMPRESSION
    
    @property
    def ACTION_CREATION(self) -> str:
        return PermissionService.ACTION_CREATION
    
    @property
    def ACTION_MODIFICATION(self) -> str:
        return PermissionService.ACTION_MODIFICATION
    
    @property
    def ACTION_SUPPRESSION(self) -> str:
        return PermissionService.ACTION_SUPPRESSION
    
    @property
    def ACTION_CONSULTATION(self) -> str:
        return PermissionService.ACTION_CONSULTATION
    
    # =========================================================================
    # GESTION DES REFUS ET HISTORIQUE
    # =========================================================================
    
    def refuser_autorisation(
        self,
        code_utilisateur: str,
        action: str,
        contexte: str,
        code_autorisateur: str,
        raison: str = "Refusé par le responsable"
    ) -> Dict[str, any]:
        """
        Permet au responsable de refuser explicitement une demande.
        
        Returns:
            Dict avec status et message
        """
        try:
            succes, message = self.service.refuser_autorisation(
                code_utilisateur, action, contexte, code_autorisateur, raison
            )
            return {
                "status": "success" if succes else "error",
                "message": message
            }
        except Exception as e:
            self.logger.error(f"Erreur refuser_autorisation: {e}")
            return {
                "status": "error",
                "message": "Erreur lors du refus de l'autorisation."
            }
    
    def obtenir_demandes_en_attente(self, code_autorisateur: str) -> Dict[str, any]:
        """
        Récupère les demandes en attente pour un autorisateur.
        
        Returns:
            Dict avec status et liste des demandes
        """
        try:
            demandes = self.service.obtenir_demandes_en_attente(code_autorisateur)
            return {
                "status": "success",
                "demandes": demandes,
                "count": len(demandes)
            }
        except Exception as e:
            self.logger.error(f"Erreur obtenir_demandes_en_attente: {e}")
            return {
                "status": "error",
                "message": "Erreur lors de la récupération des demandes.",
                "demandes": []
            }
    
    def obtenir_historique_utilisateur(
        self,
        code_utilisateur: str,
        limite: int = 50
    ) -> Dict[str, any]:
        """
        Récupère l'historique des demandes d'un utilisateur.
        
        Returns:
            Dict avec status et historique
        """
        try:
            historique = self.service.obtenir_historique_utilisateur(
                code_utilisateur, limite
            )
            return {
                "status": "success",
                "historique": historique,
                "count": len(historique)
            }
        except Exception as e:
            self.logger.error(f"Erreur obtenir_historique_utilisateur: {e}")
            return {
                "status": "error",
                "message": "Erreur lors de la récupération de l'historique.",
                "historique": []
            }
