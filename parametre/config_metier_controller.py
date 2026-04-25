# /parametre/config_metier_controller.py

from parametre.config_metier_manager import ConfigMetierManager
from parametre.controleur_param import CabinetController
from typing import Dict, Any, Optional, Tuple

class ConfigMetierController:
    """
    Contrôleur pour la configuration métier.
    Valide les données avant de les envoyer au service (manager).
    Expose les méthodes aux vues et autres services.
    """
    
    def __init__(self):
        self.manager = ConfigMetierManager()
        self.cabinet_controller = CabinetController()
    
    # ========== TYPES DE VISITE ==========
    
    def obtenir_types_visite(self) -> Dict[str, Dict[str, Any]]:
        """Retourne tous les types de visite."""
        try:
            return self.manager.get_types_visite()
        except Exception as e:
            print(f"[ConfigMetierController] Erreur obtention types visite: {e}")
            return {}
    
    def obtenir_tarif_visite(self, type_visite: str) -> Tuple[bool, Optional[float], str]:
        """
        Retourne le tarif d'un type de visite.
        Returns: (succès, tarif, message)
        """
        try:
            if not type_visite or not type_visite.strip():
                return False, None, "Le type de visite ne peut pas être vide"
            
            tarif = self.manager.get_tarif_visite(type_visite)
            if tarif is None:
                return False, None, f"Type de visite '{type_visite}' introuvable"
            
            return True, tarif, "Tarif récupéré avec succès"
        except Exception as e:
            return False, None, f"Erreur: {e}"
    
    def ajouter_type_visite(self, nom: str, tarif: float, description: str = "", actif: bool = True) -> Tuple[bool, str]:
        """
        Ajoute un nouveau type de visite après validation.
        Returns: (succès, message)
        """
        try:
            # Validation
            if not nom or not nom.strip():
                return False, "Le nom du type de visite est obligatoire"
            
            if tarif < 0:
                return False, "Le tarif ne peut pas être négatif"
            
            # Vérifier si le type existe déjà
            types_existants = self.manager.get_types_visite()
            if nom in types_existants:
                return False, f"Le type de visite '{nom}' existe déjà"
            
            # Ajouter via le manager
            success = self.manager.ajouter_type_visite(nom, tarif, description, actif)
            
            if success:
                return True, f"Type de visite '{nom}' ajouté avec succès"
            else:
                return False, "Erreur lors de l'ajout du type de visite"
                
        except Exception as e:
            return False, f"Erreur: {e}"
    
    def modifier_type_visite(self, nom: str, tarif: float, description: str = "", actif: bool = True) -> Tuple[bool, str]:
        """
        Modifie un type de visite existant après validation.
        Returns: (succès, message)
        """
        try:
            # Validation
            if not nom or not nom.strip():
                return False, "Le nom du type de visite est obligatoire"
            
            if tarif < 0:
                return False, "Le tarif ne peut pas être négatif"
            
            # Vérifier si le type existe
            types_existants = self.manager.get_types_visite()
            if nom not in types_existants:
                return False, f"Le type de visite '{nom}' n'existe pas"
            
            # Modifier via le manager
            success = self.manager.modifier_type_visite(nom, tarif, description, actif)
            
            if success:
                return True, f"Type de visite '{nom}' modifié avec succès"
            else:
                return False, "Erreur lors de la modification du type de visite"
                
        except Exception as e:
            return False, f"Erreur: {e}"
    
    def supprimer_type_visite(self, nom: str) -> Tuple[bool, str]:
        """
        Supprime un type de visite après validation.
        Returns: (succès, message)
        """
        try:
            if not nom or not nom.strip():
                return False, "Le nom du type de visite est obligatoire"
            
            # Vérifier si le type existe
            types_existants = self.manager.get_types_visite()
            if nom not in types_existants:
                return False, f"Le type de visite '{nom}' n'existe pas"
            
            # Supprimer via le manager
            success = self.manager.supprimer_type_visite(nom)
            
            if success:
                return True, f"Type de visite '{nom}' supprimé avec succès"
            else:
                return False, "Erreur lors de la suppression du type de visite"
                
        except Exception as e:
            return False, f"Erreur: {e}"
    
    # ========== DURÉES SERVICES ==========
    
    def obtenir_durees_services(self) -> Dict[str, Dict[str, Any]]:
        """Retourne toutes les durées des services."""
        try:
            return self.manager.get_durees_services()
        except Exception as e:
            print(f"[ConfigMetierController] Erreur obtention durées services: {e}")
            return {}
    
    def obtenir_duree_service(self, type_service: str) -> Tuple[bool, Optional[Tuple[int, int]], str]:
        """
        Retourne les durées (normale, maximale) d'un service.
        Returns: (succès, (duree_normale, duree_maximale), message)
        """
        try:
            if not type_service or not type_service.strip():
                return False, None, "Le type de service ne peut pas être vide"
            
            durees = self.manager.get_duree_service(type_service)
            if durees is None:
                return False, None, f"Type de service '{type_service}' introuvable"
            
            return True, durees, "Durées récupérées avec succès"
        except Exception as e:
            return False, None, f"Erreur: {e}"
    
    def modifier_duree_service(self, type_service: str, duree_normale: int, duree_maximale: int, description: str = "") -> Tuple[bool, str]:
        """
        Modifie les durées d'un service après validation.
        Returns: (succès, message)
        """
        try:
            # Validation
            if not type_service or not type_service.strip():
                return False, "Le type de service est obligatoire"
            
            if duree_normale <= 0:
                return False, "La durée normale doit être supérieure à 0"
            
            if duree_maximale <= 0:
                return False, "La durée maximale doit être supérieure à 0"
            
            if duree_normale > duree_maximale:
                return False, "La durée normale ne peut pas être supérieure à la durée maximale"
            
            if duree_normale > 240:
                return False, "La durée normale ne peut pas dépasser 240 minutes (4 heures)"
            
            if duree_maximale > 480:
                return False, "La durée maximale ne peut pas dépasser 480 minutes (8 heures)"
            
            # Vérifier si le service existe
            services_existants = self.manager.get_durees_services()
            if type_service not in services_existants:
                return False, f"Le type de service '{type_service}' n'existe pas"
            
            # Modifier via le manager
            success = self.manager.modifier_duree_service(type_service, duree_normale, duree_maximale, description)
            
            if success:
                return True, f"Durées du service '{type_service}' modifiées avec succès"
            else:
                return False, "Erreur lors de la modification des durées"
                
        except Exception as e:
            return False, f"Erreur: {e}"
    
    # ========== DURÉE PARCOURS PATIENT ==========
    
    def obtenir_duree_parcours_patient(self) -> Dict[str, Any]:
        """Retourne les durées du parcours patient complet."""
        try:
            return self.manager.get_duree_parcours_patient()
        except Exception as e:
            print(f"[ConfigMetierController] Erreur obtention durée parcours: {e}")
            return {}
    
    def obtenir_duree_totale_parcours(self) -> Tuple[int, int]:
        """
        Retourne les durées totales du parcours patient.
        Returns: (duree_normale, duree_maximale)
        """
        try:
            return self.manager.get_duree_totale_parcours()
        except Exception as e:
            print(f"[ConfigMetierController] Erreur: {e}")
            return (90, 180)
    
    def modifier_duree_parcours_patient(self, duree_normale: int, duree_maximale: int, description: str = "") -> Tuple[bool, str]:
        """
        Modifie les durées du parcours patient après validation.
        Returns: (succès, message)
        """
        try:
            # Validation
            if duree_normale <= 0:
                return False, "La durée normale doit être supérieure à 0"
            
            if duree_maximale <= 0:
                return False, "La durée maximale doit être supérieure à 0"
            
            if duree_normale > duree_maximale:
                return False, "La durée normale ne peut pas être supérieure à la durée maximale"
            
            if duree_normale < 30:
                return False, "La durée normale ne peut pas être inférieure à 30 minutes"
            
            if duree_maximale > 720:
                return False, "La durée maximale ne peut pas dépasser 720 minutes (12 heures)"
            
            # Modifier via le manager
            success = self.manager.modifier_duree_parcours_patient(duree_normale, duree_maximale, description)
            
            if success:
                return True, "Durées du parcours patient modifiées avec succès"
            else:
                return False, "Erreur lors de la modification des durées du parcours"
                
        except Exception as e:
            return False, f"Erreur: {e}"
    
    # ========== FORMATAGE ==========
    
    def formater_montant(self, montant: float) -> str:
        """
        Formate un montant selon la devise du cabinet.
        Returns: Montant formaté (ex: "100 000 GNF")
        """
        try:
            return self.cabinet_controller.formater_montant(montant)
        except Exception as e:
            print(f"[ConfigMetierController] Erreur formatage: {e}")
            return f"{int(montant):,}".replace(',', ' ')
    
    def obtenir_tarif_visite_formate(self, type_visite: str) -> Tuple[bool, Optional[str], str]:
        """
        Retourne le tarif formaté d'un type de visite.
        Returns: (succès, tarif_formaté, message)
        """
        success, tarif, message = self.obtenir_tarif_visite(type_visite)
        if success and tarif is not None:
            tarif_formate = self.formater_montant(tarif)
            return True, tarif_formate, message
        return success, None, message
    
    def obtenir_types_visite_formates(self) -> Dict[str, Dict[str, Any]]:
        """
        Retourne tous les types de visite avec tarifs formatés.
        """
        try:
            types = self.obtenir_types_visite()
            types_formates = {}
            
            for nom, info in types.items():
                types_formates[nom] = {
                    'tarif': info.get('tarif', 0),
                    'tarif_formate': self.formater_montant(info.get('tarif', 0)),
                    'description': info.get('description', ''),
                    'actif': info.get('actif', True)
                }
            
            return types_formates
        except Exception as e:
            print(f"[ConfigMetierController] Erreur formatage types: {e}")
            return {}
    
    # ========== UTILITAIRES ==========
    
    def rafraichir_configuration(self) -> bool:
        """Force le rechargement de la configuration."""
        try:
            self.manager.rafraichir()
            return True
        except Exception as e:
            print(f"[ConfigMetierController] Erreur rafraîchissement: {e}")
            return False


# Instance singleton globale pour utilisation dans l'application
config_metier_controller = ConfigMetierController()
