# Importations des classes
from data.dao_user import UserDAO
from models.modele_user import ModeleUser
import bcrypt

class UserController:
    def __init__(self):
        self.dao = UserDAO()

    def gerer_creation(self, mdp: str, role: str, id_personnel: str) -> dict:
        """
        Gère la création d'un utilisateur.
        Retourne un dictionnaire de résultat.
        """
        if not all([mdp, role, id_personnel]):
            return {"status": "error", "message": "Erreur : Tous les champs sont requis."}
            
        nouveau_code = self.dao.generer_nouveau_code()
        
        if nouveau_code:
            nouvel_utilisateur = ModeleUser(nouveau_code, mdp, role, id_personnel)
            if self.dao.enregistrer_utilisateur(nouvel_utilisateur):
                return {"status": "success", "message": f"Compte '{nouveau_code}' créé avec succès.", "code": nouveau_code}
            else:
                return {"status": "error", "message": "Échec de la création du compte."}
        else:
            return {"status": "error", "message": "Impossible de générer un nouveau code utilisateur."}

    def gerer_authentification(self, role: str, mdp: str) -> dict:
        """
        Vérifie le mot de passe en fonction du rôle.
        Si l'authentification réussit, retourne les infos de l'utilisateur.
        """
        # 1. On recherche le code de l'utilisateur en fonction du rôle
        code = self.dao.rechercher_code_par_role(role)
        
        if not code:
            # Si aucun code n'est trouvé pour ce rôle, c'est une erreur d'authentification
            return {"status": "error", "message": "Erreur : Code ou mot de passe incorrect."}
            
        # 2. On recherche toutes les informations de l'utilisateur à partir du code
        # Cette méthode a été modifiée dans le DAO pour inclure `photo_path`
        infos_utilisateur = self.dao.rechercher_utilisateur(code)
        
        if infos_utilisateur:
            # S'assurer que le mot de passe haché est bien une chaîne de caractères
            mdp_hashe_stocke = infos_utilisateur['mdp'].encode('utf-8')
            
            # 3. On vérifie si le mot de passe fourni correspond au mot de passe haché
            if bcrypt.checkpw(mdp.encode('utf-8'), mdp_hashe_stocke):
                
                # C'EST LA PARTIE QUI CHANGE
                # On prépare le dictionnaire des informations à renvoyer à l'interface
                user_info_to_return = {
                    "role": infos_utilisateur['role'],
                    "nom": infos_utilisateur['nom'],
                    "prenom": infos_utilisateur['prenom'],
                    "mail": infos_utilisateur['mail'],
                    "photo_path": infos_utilisateur['photo_path'] # On ajoute le chemin de la photo ici
                }
                
                return {"status": "success", "user_info": user_info_to_return}
            else:
                return {"status": "error", "message": "Erreur : Code ou mot de passe incorrect."}
        else:
            # Devrait pas arriver si le code a été trouvé, mais par sécurité
            return {"status": "error", "message": "Erreur : Utilisateur introuvable."}

    def gerer_recherche_utilisateur(self, code: str) -> dict:
        """
        Recherche un utilisateur et retourne ses informations complètes.
        """
        infos_utilisateur = self.dao.rechercher_utilisateur(code)
        
        if infos_utilisateur:
            # On renvoie tout sauf le mot de passe haché
            if 'mdp' in infos_utilisateur:
                del infos_utilisateur['mdp']
            return {"status": "success", "user_info": infos_utilisateur}
        else:
            return {"status": "error", "message": f"Erreur : Aucun utilisateur trouvé avec le code '{code}'."}

    def gerer_suppression(self, code: str) -> dict:
        """
        Supprime un utilisateur et retourne le résultat de l'opération.
        """
        user_existant = self.dao.rechercher_utilisateur(code)
        if user_existant:
            self.dao.supprimer_utilisateur(code)
            return {"status": "success", "message": f"L'utilisateur avec le code '{code}' a été supprimé."}
        else:
            return {"status": "error", "message": f"Erreur : Aucun utilisateur trouvé avec le code '{code}'."}