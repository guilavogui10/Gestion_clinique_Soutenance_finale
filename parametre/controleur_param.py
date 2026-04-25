# /controleurs/CabinetController.py

from parametre.service_param import CabinetService

class CabinetController:
    """
    Contrôleur pour la gestion des paramètres du cabinet.
    Fait le lien entre la vue et le service métier.
    """
    
    def __init__(self):
        self.service = CabinetService()
    
    def obtenir_informations_cabinet(self):
        """
        Récupère les informations du cabinet.
        Retourne un dictionnaire ou None.
        """
        return self.service.obtenir_informations_cabinet()
    
    def enregistrer_informations_cabinet(self, nom_cabinet, chemin_logo, adresse, email, telephone,
                                        devise, fuseau_horaire, format_date, format_heure, notes, date_creation=None):
        """
        Enregistre ou met à jour les informations du cabinet.
        Détecte automatiquement s'il faut créer ou modifier.
        Retourne un dictionnaire {"status": "success"/"error", "message": "..."}
        """
        try:
            # Vérifier si des infos existent déjà
            info_existante = self.service.obtenir_informations_cabinet()
            
            if info_existante:
                # Mise à jour
                success, message = self.service.modifier_informations_cabinet(
                    nom_cabinet, chemin_logo, adresse, email, telephone,
                    devise, fuseau_horaire, format_date, format_heure, notes, date_creation
                )
            else:
                # Création
                success, message = self.service.creer_informations_cabinet(
                    nom_cabinet, chemin_logo, adresse, email, telephone,
                    devise, fuseau_horaire, format_date, format_heure, notes, date_creation
                )
            
            return {
                "status": "success" if success else "error",
                "message": message
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur contrôleur: {e}"
            }
    
    def obtenir_chemin_logo(self):
        """
        Retourne le chemin complet du logo.
        """
        return self.service.obtenir_chemin_logo_complet()
    
    def obtenir_code_devise(self):
        """
        Retourne le code de la devise configurée (ex: 'GNF').
        """
        return self.service.obtenir_code_devise()
    
    def formater_montant(self, montant):
        """
        Formate un montant selon la devise du cabinet.
        Retourne le montant formaté (ex: "100 000 GNF").
        """
        return self.service.formater_montant(montant)