# /parametre/config_metier_manager.py

import json
import os
from typing import Dict, Any, Optional, Tuple

class ConfigMetierManager:
    """
    Gestionnaire de configuration métier.
    Permet de lire et modifier les paramètres métier stockés dans config_metier.json
    """
    
    _instance = None
    _config_cache = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigMetierManager, cls).__new__(cls)
            cls._instance._init_config_path()
        return cls._instance
    
    def _init_config_path(self):
        """Initialise le chemin du fichier de configuration."""
        self.config_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.config_dir, 'config_metier.json')
    
    def charger_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis le fichier JSON."""
        if self._config_cache is None:
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
            except FileNotFoundError:
                print(f"[ConfigMetierManager] Fichier non trouvé: {self.config_file}")
                self._config_cache = self._get_config_defaut()
                self.sauvegarder_config(self._config_cache)
            except json.JSONDecodeError as e:
                print(f"[ConfigMetierManager] Erreur JSON: {e}")
                self._config_cache = self._get_config_defaut()
        
        return self._config_cache
    
    def sauvegarder_config(self, config: Dict[str, Any]) -> bool:
        """Sauvegarde la configuration dans le fichier JSON."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self._config_cache = config
            return True
        except Exception as e:
            print(f"[ConfigMetierManager] Erreur sauvegarde: {e}")
            return False
    
    def rafraichir(self):
        """Force le rechargement de la configuration."""
        self._config_cache = None
        return self.charger_config()
    
    # ========== TYPES DE VISITE ==========
    
    def get_types_visite(self) -> Dict[str, Dict[str, Any]]:
        """Retourne tous les types de visite."""
        config = self.charger_config()
        return config.get('types_visite', {})
    
    def get_tarif_visite(self, type_visite: str) -> Optional[float]:
        """Retourne le tarif d'un type de visite."""
        types = self.get_types_visite()
        if type_visite in types:
            return types[type_visite].get('tarif', 0)
        return None
    
    def ajouter_type_visite(self, nom: str, tarif: float, description: str = "", actif: bool = True) -> bool:
        """Ajoute un nouveau type de visite."""
        config = self.charger_config()
        config['types_visite'][nom] = {
            'tarif': tarif,
            'description': description,
            'actif': actif
        }
        return self.sauvegarder_config(config)
    
    def modifier_type_visite(self, nom: str, tarif: float, description: str = "", actif: bool = True) -> bool:
        """Modifie un type de visite existant."""
        config = self.charger_config()
        if nom in config['types_visite']:
            config['types_visite'][nom] = {
                'tarif': tarif,
                'description': description,
                'actif': actif
            }
            return self.sauvegarder_config(config)
        return False
    
    def supprimer_type_visite(self, nom: str) -> bool:
        """Supprime un type de visite."""
        config = self.charger_config()
        if nom in config['types_visite']:
            del config['types_visite'][nom]
            return self.sauvegarder_config(config)
        return False
    
    # ========== DURÉES SERVICES ==========
    
    def get_durees_services(self) -> Dict[str, Dict[str, Any]]:
        """Retourne toutes les durées des services."""
        config = self.charger_config()
        return config.get('durees_services', {})
    
    def get_duree_service(self, type_service: str) -> Optional[Tuple[int, int]]:
        """
        Retourne les durées (normale, maximale) d'un service.
        Returns: (duree_normale, duree_maximale) ou None
        """
        durees = self.get_durees_services()
        if type_service in durees:
            service = durees[type_service]
            return (
                service.get('duree_normale_minutes', 0),
                service.get('duree_maximale_minutes', 0)
            )
        return None
    
    def modifier_duree_service(self, type_service: str, duree_normale: int, duree_maximale: int, description: str = "") -> bool:
        """Modifie les durées d'un service."""
        config = self.charger_config()
        if type_service in config['durees_services']:
            config['durees_services'][type_service] = {
                'duree_normale_minutes': duree_normale,
                'duree_maximale_minutes': duree_maximale,
                'description': description
            }
            return self.sauvegarder_config(config)
        return False
    
    # ========== DURÉE PARCOURS PATIENT ==========
    
    def get_duree_parcours_patient(self) -> Dict[str, Any]:
        """Retourne les durées du parcours patient complet."""
        config = self.charger_config()
        return config.get('duree_parcours_patient', {})
    
    def get_duree_totale_parcours(self) -> Tuple[int, int]:
        """
        Retourne les durées totales du parcours patient.
        Returns: (duree_normale, duree_maximale)
        """
        parcours = self.get_duree_parcours_patient()
        return (
            parcours.get('duree_normale_totale_minutes', 90),
            parcours.get('duree_maximale_totale_minutes', 180)
        )
    
    def modifier_duree_parcours_patient(self, duree_normale: int, duree_maximale: int, description: str = "") -> bool:
        """Modifie les durées du parcours patient."""
        config = self.charger_config()
        config['duree_parcours_patient'] = {
            'duree_normale_totale_minutes': duree_normale,
            'duree_maximale_totale_minutes': duree_maximale,
            'description': description
        }
        return self.sauvegarder_config(config)
    
    # ========== CONFIGURATION PAR DÉFAUT ==========
    
    def _get_config_defaut(self) -> Dict[str, Any]:
        """Retourne la configuration par défaut."""
        return {
            "types_visite": {
                "Contrôle": {"tarif": 0, "description": "Visite de contrôle gratuite", "actif": True},
                "VIP": {"tarif": 100000, "description": "Visite VIP avec service premium", "actif": True},
                "RDV": {"tarif": 80000, "description": "Visite sur rendez-vous", "actif": True},
                "Urgence": {"tarif": 120000, "description": "Visite d'urgence", "actif": True}
            },
            "durees_services": {
                "consultation": {
                    "duree_normale_minutes": 30,
                    "duree_maximale_minutes": 60,
                    "description": "Durée pour une consultation"
                },
                "examen": {
                    "duree_normale_minutes": 20,
                    "duree_maximale_minutes": 45,
                    "description": "Durée pour un examen ophtalmologique"
                },
                "autre": {
                    "duree_normale_minutes": 15,
                    "duree_maximale_minutes": 30,
                    "description": "Durée pour autres services"
                }
            },
            "duree_parcours_patient": {
                "duree_normale_totale_minutes": 90,
                "duree_maximale_totale_minutes": 180,
                "description": "Durée totale du parcours patient de la création de visite jusqu'à la libération"
            }
        }


# Instance singleton globale
config_metier = ConfigMetierManager()
