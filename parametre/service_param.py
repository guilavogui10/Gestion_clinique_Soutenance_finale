# /service_metier/cabinet_service.py

from parametre.dao_param import CabinetDAO
from parametre.model_param import Parametre
import os
import shutil

class CabinetService:
    """
    Service métier pour la gestion des paramètres du cabinet.
    Contient toute la logique métier.
    """
    
    def __init__(self):
        self.dao = CabinetDAO()
    
    def obtenir_informations_cabinet(self):
        """
        Récupère les informations du cabinet depuis la base.
        Retourne un dictionnaire ou None.
        """
        try:
            info = self.dao.get_info_cabinet()
            if info:
                return {
                    'nom_cabinet': info.get('nom_cabinet', ''),
                    'logo': info.get('logo', ''),
                    'adresse': info.get('adresse', ''),
                    'email': info.get('email', ''),
                    'telephone': info.get('telephone', ''),
                    'devise': info.get('devise', 'GNF - Franc guinéen (GNF)'),
                    'fuseau_horaire': info.get('fuseau_horaire', '(GMT) Afrique/Conakry'),
                    'format_date': info.get('format_date', 'DD/MM/YYYY'),
                    'format_heure': info.get('format_heure', '24 heures (HH:mm)'),
                    'notes': info.get('notes', ''),
                    'date_creation': info.get('date_creation', None)
                }
            return None
        except Exception as e:
            print(f"[CabinetService] Erreur obtention info: {e}")
            return None
    
    def sauvegarder_logo(self, chemin_source, nom_fichier):
        """
        Copie le fichier logo vers le répertoire de l'application.
        Retourne (nom_fichier, "") si succès, (None, message_erreur) sinon.
        """
        try:
            script_dir = os.path.dirname(__file__)
            destination_dir = os.path.join(script_dir, '..', 'connexion', 'image')
            destination_dir = os.path.abspath(destination_dir)
            
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)
            
            chemin_destination = os.path.join(destination_dir, nom_fichier)
            chemin_source_abs = os.path.abspath(chemin_source)
            chemin_destination_abs = os.path.abspath(chemin_destination)
            
            # Vérifier si la source et la destination sont le même fichier
            if chemin_source_abs == chemin_destination_abs:
                print(f"[CabinetService] Le fichier est déjà au bon endroit: {nom_fichier}")
                return nom_fichier, ""
            
            # Copier le fichier
            shutil.copy(chemin_source_abs, chemin_destination_abs)
            
            return nom_fichier, ""
        except Exception as e:
            return None, f"Erreur sauvegarde logo: {e}"
    
    def creer_informations_cabinet(self, nom_cabinet, chemin_logo, adresse, email, telephone,
                                   devise, fuseau_horaire, format_date, format_heure, notes, date_creation=None):
        """
        Crée les informations initiales du cabinet.
        Retourne (True, message) si succès, (False, message) sinon.
        """
        try:
            # Validation
            valide, msg = self._valider_donnees(nom_cabinet, adresse, email, telephone, 
                                               devise, fuseau_horaire, format_date, format_heure)
            if not valide:
                return False, msg
            
            # Gestion du logo
            if not chemin_logo:
                return False, "Le logo est obligatoire"
            
            logo_filename = os.path.basename(chemin_logo)
            nom_logo, msg_logo = self.sauvegarder_logo(chemin_logo, logo_filename)
            
            if not nom_logo:
                return False, msg_logo
            
            # Création de l'objet
            cabinet = Parametre(
                nom_cabinet=nom_cabinet,
                logo=nom_logo,
                adresse=adresse,
                email=email,
                telephone=telephone,
                devise=devise,
                fuseau_horaire=fuseau_horaire,
                format_date=format_date,
                format_heure=format_heure,
                notes=notes,
                date_creation=date_creation
            )
            
            # Insertion en base
            return self.dao.insert_info_cabinet(cabinet)
            
        except Exception as e:
            return False, f"Erreur création: {e}"
    
    def modifier_informations_cabinet(self, nom_cabinet, chemin_logo, adresse, email, telephone,
                                     devise, fuseau_horaire, format_date, format_heure, notes, date_creation=None):
        """
        Met à jour les informations du cabinet.
        Retourne (True, message) si succès, (False, message) sinon.
        """
        try:
            # Validation
            valide, msg = self._valider_donnees(nom_cabinet, adresse, email, telephone,
                                               devise, fuseau_horaire, format_date, format_heure)
            if not valide:
                return False, msg
            
            # Gestion du logo
            nom_logo = None
            if chemin_logo:
                logo_filename = os.path.basename(chemin_logo)
                nom_logo, msg_logo = self.sauvegarder_logo(chemin_logo, logo_filename)
                if not nom_logo:
                    return False, msg_logo
            else:
                # Garder l'ancien logo
                info = self.dao.get_info_cabinet()
                nom_logo = info.get('logo') if info else None
            
            # Création de l'objet
            cabinet = Parametre(
                nom_cabinet=nom_cabinet,
                logo=nom_logo,
                adresse=adresse,
                email=email,
                telephone=telephone,
                devise=devise,
                fuseau_horaire=fuseau_horaire,
                format_date=format_date,
                format_heure=format_heure,
                notes=notes,
                date_creation=date_creation
            )
            
            # Mise à jour en base
            return self.dao.update_info_cabinet(cabinet)
            
        except Exception as e:
            return False, f"Erreur modification: {e}"
    
    def _valider_donnees(self, nom_cabinet, adresse, email, telephone, devise, fuseau_horaire, format_date, format_heure):
        """
        Valide les données du cabinet.
        Retourne (True, "") si valide, (False, message) sinon.
        """
        if not nom_cabinet or len(nom_cabinet.strip()) < 3:
            return False, "Le nom du cabinet doit contenir au moins 3 caractères"
        
        if not adresse or len(adresse.strip()) < 5:
            return False, "L'adresse doit contenir au moins 5 caractères"
        
        if email and '@' not in email:
            return False, "L'email n'est pas valide"
        
        if not devise:
            return False, "Veuillez sélectionner une devise"
        
        if not fuseau_horaire:
            return False, "Veuillez sélectionner un fuseau horaire"
        
        if not format_date:
            return False, "Veuillez sélectionner un format de date"
        
        if not format_heure:
            return False, "Veuillez sélectionner un format d'heure"
        
        return True, ""
    
    def obtenir_chemin_logo_complet(self):
        """
        Retourne le chemin absolu du logo du cabinet.
        """
        try:
            info = self.dao.get_info_cabinet()
            if info and info.get('logo'):
                script_dir = os.path.dirname(__file__)
                logo_path = os.path.join(script_dir, '..', 'connexion', 'image', info['logo'])
                return os.path.abspath(logo_path)
            return None
        except Exception as e:
            print(f"[CabinetService] Erreur chemin logo: {e}")
            return None
    
    def obtenir_code_devise(self):
        """
        Retourne le code de la devise configurée (ex: 'GNF').
        """
        try:
            info = self.dao.get_info_cabinet()
            if info and info.get('devise'):
                devise_complete = info.get('devise', 'GNF - Franc guinéen (GNF)')
                # Extraire le code devise (ex: "GNF" depuis "GNF - Franc guinéen (GNF)")
                code_devise = devise_complete.split(' - ')[0] if ' - ' in devise_complete else 'GNF'
                return code_devise
            return 'GNF'
        except Exception as e:
            print(f"[CabinetService] Erreur code devise: {e}")
            return 'GNF'
    
    def formater_montant(self, montant):
        """
        Formate un montant selon la devise du cabinet.
        Retourne le montant formaté (ex: "100 000 GNF").
        """
        try:
            code_devise = self.obtenir_code_devise()
            # Formater le montant avec espaces comme séparateurs de milliers
            montant_formate = f"{int(montant):,}".replace(',', ' ')
            return f"{montant_formate} {code_devise}"
        except Exception as e:
            print(f"[CabinetService] Erreur formatage montant: {e}")
            return f"{int(montant):,}".replace(',', ' ')
