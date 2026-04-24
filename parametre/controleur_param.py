# /controleurs/CabinetController.py

import os
import shutil # Nécessaire pour copier les fichiers
# Assurez-vous d'importer vos classes DAO et Modèle correctement
from parametre.dao_param import CabinetDAO 
from parametre.model_param import Parametre 

class CabinetController:
    """
    Contrôleur pour la gestion des informations générales du cabinet.
    """
    def __init__(self):
        # Les dépendances sont injectées
        self.cabinet_dao = CabinetDAO()
        self.Parametre = Parametre # Nom du modèle utilisé par l'utilisateur
        
    # --- LOGIQUE DE GESTION DES FICHIERS ---

    def _sauvegarder_logo(self, chemin_source_temporaire, nom_fichier_desire):
        """
        Copie le fichier logo depuis le chemin local de l'utilisateur vers
        le répertoire permanent de l'application (connexion/image/).
        Retourne le nom du fichier sauvegardé ou None en cas d'échec.
        """
        # Le script_dir est là où se trouve CabinetController.py (ex: /controleurs)
        script_dir = os.path.dirname(__file__)
        
        # Définit le chemin absolu du répertoire de destination:
        # Remonter d'un niveau (..) puis aller dans connexion/image
        destination_dir = os.path.join(script_dir, '..', 'connexion', 'image')
        
        # Assurez-vous que le répertoire de destination existe
        if not os.path.exists(destination_dir):
            try:
                os.makedirs(destination_dir)
            except Exception as e:
                return None, f"Impossible de créer le dossier de destination: {e}"

        # Crée le chemin final complet pour la copie
        chemin_destination = os.path.join(destination_dir, nom_fichier_desire)
        
        try:
            # Effectue la copie du fichier
            shutil.copy(chemin_source_temporaire, chemin_destination)
            # Retourne uniquement le nom du fichier qui sera stocké en base
            return nom_fichier_desire, "" 
        except Exception as e:
            return None, f"Erreur lors de la sauvegarde physique du logo: {e}"

    # --- MÉTHODES CRUD/Configuration ---

    def get_info(self):
        """
        Récupère et retourne les informations du cabinet (dictionnaire).
        """
        return self.cabinet_dao.get_info_cabinet()

    def create_initial_info(self, nom_cabinet, chemin_logo_source, adresse):
        """
        Gère la création initiale de l'unique ligne d'informations du cabinet.
        """
        # 1. Validation de base
        if not nom_cabinet or not adresse or not chemin_logo_source:
            return {"status": "error", "message": "Le nom, l'adresse et le logo sont obligatoires."}
        
        # 2. Gestion et sauvegarde du fichier logo
        logo_filename = os.path.basename(chemin_logo_source)
        nom_logo_sauvegarde, message_sauvegarde = self._sauvegarder_logo(chemin_logo_source, logo_filename)
        
        if not nom_logo_sauvegarde:
            return {"status": "error", "message": message_sauvegarde}
        try:
            # 3. Création de l'objet Modèle (avec le NOM du fichier sauvegardé)
            cabinet_obj = self.Parametre(
                nom_cabinet=nom_cabinet,
                logo=nom_logo_sauvegarde, # Stocke uniquement le nom du fichier
                adresse=adresse
            )
            
            # 4. Appel au DAO pour l'insertion
            success, message=  self.cabinet_dao.insert_info_cabinet(cabinet_obj)
            if success:
                return {"status": "success", "message": message}
            else:
                return {"status": "error", "message": message}
        except Exception as e:
            return {"status": "error", "message": f"Erreur contrôleur : {e}"}
            
            
    def update_info(self, nom_cabinet, chemin_logo_source, adresse):
        """
        Met à jour les informations existantes du cabinet.
        Gère le logo : si un nouveau chemin source est fourni, il est sauvegardé.
        """
        if not nom_cabinet or not adresse:
            return {"status": "error", "message": "Le nom et l'adresse ne peuvent pas être vides."}
        
        nom_logo_sauvegarde = None
        
        # 1. Gestion du logo (si un nouveau fichier a été sélectionné)
        if chemin_logo_source:
            logo_filename = os.path.basename(chemin_logo_source)
            nom_logo_sauvegarde, message_sauvegarde = self._sauvegarder_logo(chemin_logo_source, logo_filename)
            if not nom_logo_sauvegarde:
                return {"status": "error", "message": message_sauvegarde}
        else:
            # Si aucun nouveau fichier n'est sélectionné, on garde l'ancien nom de logo
            info_actuelle = self.get_info()
            nom_logo_sauvegarde = info_actuelle.get('logo') if info_actuelle else None
            
        try:
            # 2. Création de l'objet Modèle
            cabinet_obj = self.Parametre(
                nom_cabinet=nom_cabinet,
                logo=nom_logo_sauvegarde, # Le nouveau nom ou l'ancien nom
                adresse=adresse
            )
            
            # 3. Appel au DAO
            success, message = self.cabinet_dao.update_info_cabinet(cabinet_obj)
            if success:
                return {"status": "success", "message": message}
            else:
                return {"status": "error", "message": message}
        except Exception as e:
            return {"status": "error", "message": f"Erreur contrôleur : {e}"}