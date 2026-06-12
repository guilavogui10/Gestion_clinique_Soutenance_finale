"""
user_service.py
---------------
Service metier - Gestion des utilisateurs.

Responsabilites :
  - Creation de comptes (generation de code, hashage mdp via bcrypt)
  - Authentification en deux etapes (mot de passe + OTP Vault)
  - Recherche et suppression d'utilisateurs
"""

import logging

import bcrypt

from core.vault_service import VaultService
from data.dao_user import UserDAO
from data.dao_otp_tentatives import OTPTentativesDAO
from models.modele_user import ModeleUser


class UserService:
    """
    Service metier pour la gestion des utilisateurs.
    Toute la logique metier (validations, authentification, hashage) est ici.
    """

    def __init__(self, dao=None):
        self.dao = dao or UserDAO()
        self.vault = VaultService()
        self.logger = logging.getLogger(__name__)
        
        # Limitation des tentatives OTP
        try:
            self.tentatives_dao = OTPTentativesDAO()
        except Exception as e:
            self.logger.error(f"Erreur initialisation tentatives: {e}")
            self.tentatives_dao = None

    def _construire_user_info(self, infos_utilisateur: dict) -> dict:
        return {
            "code": infos_utilisateur.get("code"),
            "code_personnel": infos_utilisateur.get("code_personnel"),
            "role": infos_utilisateur.get("role"),
            "nom": infos_utilisateur.get("nom"),
            "prenom": infos_utilisateur.get("prenom"),
            "mail": infos_utilisateur.get("mail"),
            "contact": infos_utilisateur.get("contact"),
            "fonction": infos_utilisateur.get("fonction"),
            "photo_path": infos_utilisateur.get("photo_path"),
            "est_responsable": infos_utilisateur.get("est_responsable", 0),
        }

    @staticmethod
    def _masquer_email(email: str) -> str:
        email = (email or "").strip()
        if "@" not in email:
            return email
        local, domaine = email.split("@", 1)
        if len(local) <= 2:
            local_masque = local[:1] + "*"
        else:
            local_masque = local[:2] + "*" * max(len(local) - 2, 1)
        return f"{local_masque}@{domaine}"

    # =========================================================================
    # CREATION
    # =========================================================================

    def gerer_creation(self, mdp: str, role: str, id_personnel: str) -> dict:
        """
        Gere la creation d'un utilisateur ou la mise à jour s'il existe déjà.

        Args:
            mdp (str): Mot de passe en clair.
            role (str): Role de l'utilisateur.
            id_personnel (str): Code du personnel associe.

        Returns:
            dict: {"status": "success"|"error", "message": ..., "code": ...}
        """
        if not all([mdp, role, id_personnel]):
            return {"status": "error", "message": "Erreur : Tous les champs sont requis."}

        # Vérifier si l'utilisateur existe déjà pour ce personnel
        user_existant = self.dao.rechercher_par_code_personnel(id_personnel)
        if user_existant:
            code_user = user_existant["code"]
            user_maj = ModeleUser(code_user, mdp, role, id_personnel)
            self.dao.modifier_utilisateur(user_maj)
            
            message = f"Le compte '{code_user}' existait déjà. Son mot de passe et son rôle ont été mis à jour."
            email = (user_existant.get("mail") or "").strip()
            if email:
                # Recréer la clé TOTP Vault au cas où
                self.vault.creer_cle_totp(code_user, account_name=email)
                
            return {
                "status": "success",
                "message": message,
                "code": code_user,
            }

        nouveau_code = self.dao.generer_nouveau_code()
        if not nouveau_code:
            return {"status": "error", "message": "Impossible de generer un nouveau code utilisateur."}

        nouvel_utilisateur = ModeleUser(nouveau_code, mdp, role, id_personnel)
        if not self.dao.enregistrer_utilisateur(nouvel_utilisateur):
            return {"status": "error", "message": "Echec de la creation du compte."}

        message = f"Compte '{nouveau_code}' cree avec succes."
        infos_utilisateur = self.dao.rechercher_utilisateur(nouveau_code) or {}
        email = (infos_utilisateur.get("mail") or "").strip()
        if email and not self.vault.creer_cle_totp(nouveau_code, account_name=email):
            message += " Cle Vault TOTP non pre-initialisee : elle sera recreee a la premiere connexion."

        return {
            "status": "success",
            "message": message,
            "code": nouveau_code,
        }

    # =========================================================================
    # AUTHENTIFICATION
    # =========================================================================

    def gerer_authentification(self, login: str, mdp: str) -> dict:
        """
        Verifie le mot de passe puis declenche la seconde etape MFA via Vault TOTP.

        Args:
            login (str): Identifiant saisi par l'utilisateur (peut correspondre à plusieurs rôles).
            mdp (str): Mot de passe saisi.

        Returns:
            dict: {"status": "otp_required"|"error", ...}
        """
        # Obtenir TOUS les utilisateurs qui correspondent au login
        utilisateurs_trouves = self.dao.rechercher_utilisateurs_par_login((login or "").strip())
        
        if not utilisateurs_trouves:
            return {"status": "error", "message": "Erreur : Utilisateur introuvable."}

        # Chercher l'utilisateur dont le mot de passe correspond
        utilisateur_valide = None
        for u in utilisateurs_trouves:
            mdp_hashe_stocke = u["mdp"].encode("utf-8")
            if bcrypt.checkpw(mdp.encode("utf-8"), mdp_hashe_stocke):
                utilisateur_valide = u
                break
        
        if not utilisateur_valide:
            return {"status": "error", "message": "Erreur : Code ou mot de passe incorrect."}

        # Utilisateur trouvé et mot de passe vérifié !
        infos_utilisateur = utilisateur_valide
        code = infos_utilisateur["code"]
        
        # VÉRIFIER LE BLOCAGE AVANT D'ENVOYER LE CODE OTP
        identifiant_otp = f"connexion_{code}"
        if self.tentatives_dao:
            if self.tentatives_dao.est_bloque(identifiant_otp):
                info = self.tentatives_dao.obtenir_info_tentative(identifiant_otp)
                minutes_restantes = info.get('minutes_restantes_blocage', 0) if info else 0
                return {
                    "status": "error",
                    "message": f"Compte bloqué suite à trop de tentatives échouées. Réessayez dans {minutes_restantes} minute(s)."
                }

        email = (infos_utilisateur.get("mail") or "").strip()
        if not email:
            return {"status": "error", "message": "Aucune adresse email n'est associee a ce compte."}

        if not self.vault.est_connecte():
            return {
                "status": "error",
                "message": "Vault est indisponible : impossible de terminer l'authentification multi-facteurs.",
            }

        # Supprimer l'ancienne clé TOTP si elle existe pour forcer la génération d'un nouveau code
        self.vault.supprimer_cle_totp(code)
        
        # Créer une nouvelle clé TOTP
        if not self.vault.creer_cle_totp(code, account_name=email):
            return {
                "status": "error",
                "message": "Impossible d'initialiser la cle TOTP Vault pour cet utilisateur.",
            }

        code_otp = self.vault.generer_code_otp(code)
        if not code_otp:
            return {
                "status": "error",
                "message": "Vault n'a pas pu generer le code OTP de connexion.",
            }

        if not self.vault.envoyer_otp_par_email(
            email,
            code_otp,
            prenom=infos_utilisateur.get("prenom", ""),
        ):
            return {
                "status": "error",
                "message": "Le code OTP n'a pas pu etre envoye par email.",
            }

        return {
            "status": "otp_required",
            "message": f"Un code de verification a ete envoye a {self._masquer_email(email)}.",
            "user_code": code,
            "masked_email": self._masquer_email(email),
        }

    def verifier_otp_connexion(self, code_utilisateur: str, code_otp: str) -> dict:
        """
        Valide le code OTP saisi apres la verification du mot de passe.
        Avec limitation des tentatives (3 max, blocage 15 minutes).
        """
        code_utilisateur = (code_utilisateur or "").strip()
        code_otp = (code_otp or "").strip()

        if not code_utilisateur or not code_otp:
            return {"status": "error", "message": "Le code de verification est obligatoire."}

        infos_utilisateur = self.dao.rechercher_utilisateur(code_utilisateur)
        if not infos_utilisateur:
            return {"status": "error", "message": "Utilisateur introuvable."}

        if not self.vault.est_connecte():
            return {
                "status": "error",
                "message": "Vault est indisponible : impossible de verifier le code OTP.",
            }
        
        # Identifiant unique pour cette connexion
        identifiant_otp = f"connexion_{code_utilisateur}"
        
        # Vérifier si bloqué
        if self.tentatives_dao:
            if self.tentatives_dao.est_bloque(identifiant_otp):
                info = self.tentatives_dao.obtenir_info_tentative(identifiant_otp)
                minutes_restantes = info.get('minutes_restantes_blocage', 0) if info else 0
                return {
                    "status": "error",
                    "message": f"Trop de tentatives échouées. Réessayez dans {minutes_restantes} minute(s)."
                }
            
            # Créer ou obtenir l'enregistrement de tentative
            self.tentatives_dao.creer_ou_obtenir_tentative(code_utilisateur, identifiant_otp)
            # Incrémenter le compteur
            self.tentatives_dao.incrementer_tentative(identifiant_otp, est_echec=False)

        # Vérifier le code OTP
        if not self.vault.verifier_code_otp(code_utilisateur, code_otp):
            # Code invalide - Incrémenter les échecs
            if self.tentatives_dao:
                self.tentatives_dao.incrementer_tentative(identifiant_otp, est_echec=True)
                
                # Vérifier le nombre de tentatives restantes
                info = self.tentatives_dao.obtenir_info_tentative(identifiant_otp)
                if info:
                    nb_echecs = info.get('nb_echecs', 0)
                    tentatives_restantes = self.tentatives_dao.MAX_TENTATIVES - nb_echecs
                    
                    if tentatives_restantes > 0:
                        return {
                            "status": "error",
                            "message": f"Code OTP invalide. {tentatives_restantes} tentative(s) restante(s)."
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"Trop de tentatives. Compte bloqué pour {self.tentatives_dao.DUREE_BLOCAGE_MINUTES} minutes."
                        }
            
            return {
                "status": "error",
                "message": "Code OTP invalide ou expire. Recommencez la connexion pour obtenir un nouveau code.",
            }
        
        # Code valide - Nettoyer
        if self.tentatives_dao:
            self.tentatives_dao.supprimer_tentative(identifiant_otp)

        return {
            "status": "success",
            "user_info": self._construire_user_info(infos_utilisateur),
        }

    # =========================================================================
    # RECHERCHE
    # =========================================================================

    def gerer_recherche_utilisateur(self, code: str) -> dict:
        """
        Recherche un utilisateur et retourne ses informations completes (sans mdp).

        Args:
            code (str): Code utilisateur.

        Returns:
            dict: {"status": "success"|"error", "user_info": {...}}
        """
        infos_utilisateur = self.dao.rechercher_utilisateur(code)

        if infos_utilisateur:
            infos_utilisateur = dict(infos_utilisateur)
            infos_utilisateur.pop("mdp", None)
            return {"status": "success", "user_info": infos_utilisateur}

        return {"status": "error", "message": f"Erreur : Aucun utilisateur trouve avec le code '{code}'."}

    # =========================================================================
    # SUPPRESSION
    # =========================================================================

    def gerer_suppression(self, code: str) -> dict:
        """
        Supprime un utilisateur apres verification d'existence.

        Args:
            code (str): Code de l'utilisateur a supprimer.

        Returns:
            dict: {"status": "success"|"error", "message": ...}
        """
        user_existant = self.dao.rechercher_utilisateur(code)
        if not user_existant:
            return {"status": "error", "message": f"Erreur : Aucun utilisateur trouve avec le code '{code}'."}

        self.dao.supprimer_utilisateur(code)
        self.vault.supprimer_cle_totp(code)
        return {"status": "success", "message": f"L'utilisateur avec le code '{code}' a ete supprime."}

    def lister_personnel_par_roles(self, roles: list) -> list:
        return self.dao.lister_personnel_par_roles(roles)

    def obtenir_roles_disponibles(self) -> list:
        """
        Retourne la liste des rôles distincts présents dans le système.
        """
        return self.dao.obtenir_roles_disponibles()
