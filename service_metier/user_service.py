"""
user_service.py
----------------
Service métier — Gestion des utilisateurs.

Responsabilités :
  - Création de comptes (génération de code, hashage mdp via bcrypt)
  - Authentification (vérification role + mot de passe)
  - Recherche et suppression d'utilisateurs
"""

import logging
import bcrypt

from data.dao_user import UserDAO
from models.modele_user import ModeleUser


class UserService:
    """
    Service métier pour la gestion des utilisateurs.
    Toute la logique métier (validations, authentification, hashage) est ici.
    """

    def __init__(self, dao=None):
        self.dao = dao or UserDAO()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # CRÉATION
    # =========================================================================

    def gerer_creation(self, mdp: str, role: str, id_personnel: str) -> dict:
        """
        Gère la création d'un utilisateur.

        Args:
            mdp (str): Mot de passe en clair.
            role (str): Rôle de l'utilisateur.
            id_personnel (str): Code du personnel associé.

        Returns:
            dict: {"status": "success"|"error", "message": ..., "code": ...}
        """
        if not all([mdp, role, id_personnel]):
            return {"status": "error", "message": "Erreur : Tous les champs sont requis."}

        nouveau_code = self.dao.generer_nouveau_code()

        if nouveau_code:
            nouvel_utilisateur = ModeleUser(nouveau_code, mdp, role, id_personnel)
            if self.dao.enregistrer_utilisateur(nouvel_utilisateur):
                return {
                    "status": "success",
                    "message": f"Compte '{nouveau_code}' créé avec succès.",
                    "code": nouveau_code
                }
            else:
                return {"status": "error", "message": "Échec de la création du compte."}
        else:
            return {"status": "error", "message": "Impossible de générer un nouveau code utilisateur."}

    # =========================================================================
    # AUTHENTIFICATION
    # =========================================================================

    def gerer_authentification(self, role: str, mdp: str) -> dict:
        """
        Vérifie le mot de passe en fonction du rôle.
        Si l'authentification réussit, retourne les infos de l'utilisateur.

        Args:
            role (str): Rôle saisi par l'utilisateur.
            mdp (str): Mot de passe saisi.

        Returns:
            dict: {"status": "success"|"error", "user_info": {...}} ou {"message": ...}
        """
        # 1. Recherche du code utilisateur par rôle
        code = self.dao.rechercher_code_par_role(role)

        if not code:
            return {"status": "error", "message": "Erreur : Code ou mot de passe incorrect."}

        # 2. Recherche des informations complètes de l'utilisateur
        infos_utilisateur = self.dao.rechercher_utilisateur(code)

        if infos_utilisateur:
            # Vérification bcrypt du mot de passe
            mdp_hashe_stocke = infos_utilisateur['mdp'].encode('utf-8')

            if bcrypt.checkpw(mdp.encode('utf-8'), mdp_hashe_stocke):
                # Préparation du dictionnaire de retour (sans le mdp hashé)
                user_info_to_return = {
                    "role": infos_utilisateur['role'],
                    "nom": infos_utilisateur['nom'],
                    "prenom": infos_utilisateur['prenom'],
                    "mail": infos_utilisateur['mail'],
                    "photo_path": infos_utilisateur['photo_path']
                }
                return {"status": "success", "user_info": user_info_to_return}
            else:
                return {"status": "error", "message": "Erreur : Code ou mot de passe incorrect."}
        else:
            return {"status": "error", "message": "Erreur : Utilisateur introuvable."}

    # =========================================================================
    # RECHERCHE
    # =========================================================================

    def gerer_recherche_utilisateur(self, code: str) -> dict:
        """
        Recherche un utilisateur et retourne ses informations complètes (sans mdp).

        Args:
            code (str): Code utilisateur.

        Returns:
            dict: {"status": "success"|"error", "user_info": {...}}
        """
        infos_utilisateur = self.dao.rechercher_utilisateur(code)

        if infos_utilisateur:
            # Suppression du mot de passe hashé avant retour
            if 'mdp' in infos_utilisateur:
                del infos_utilisateur['mdp']
            return {"status": "success", "user_info": infos_utilisateur}
        else:
            return {"status": "error", "message": f"Erreur : Aucun utilisateur trouvé avec le code '{code}'."}

    # =========================================================================
    # SUPPRESSION
    # =========================================================================

    def gerer_suppression(self, code: str) -> dict:
        """
        Supprime un utilisateur après vérification d'existence.

        Args:
            code (str): Code de l'utilisateur à supprimer.

        Returns:
            dict: {"status": "success"|"error", "message": ...}
        """
        user_existant = self.dao.rechercher_utilisateur(code)
        if user_existant:
            self.dao.supprimer_utilisateur(code)
            return {"status": "success", "message": f"L'utilisateur avec le code '{code}' a été supprimé."}
        else:
            return {"status": "error", "message": f"Erreur : Aucun utilisateur trouvé avec le code '{code}'."}
