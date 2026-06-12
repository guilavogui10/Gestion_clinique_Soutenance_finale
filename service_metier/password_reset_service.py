import string
import random
import logging

from data.dao_user import UserDAO
from core.vault_service import VaultService
from models.modele_user import ModeleUser

class PasswordResetService:
    def __init__(self):
        self.dao_user = UserDAO()
        self.vault = VaultService()
        self.logger = logging.getLogger(__name__)

    def _generer_mot_de_passe(self, longueur=8):
        """Génère un mot de passe aléatoire de 8 caractères."""
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choice(caracteres) for _ in range(longueur))

    def _trouver_utilisateur_par_email(self, email):
        """Trouve un utilisateur complet à partir de son e-mail."""
        utilisateurs = self.dao_user.rechercher_utilisateurs_par_login(email)
        if not utilisateurs:
            return None
        
        # Filtrer pour s'assurer que c'est bien l'e-mail correspondant (au cas où login correspond à un autre champ)
        for u in utilisateurs:
            if u.get("mail") == email:
                return u
        
        return utilisateurs[0] if utilisateurs else None

    def _trouver_directeur_general(self):
        """Recherche le Directeur Général pour obtenir son e-mail."""
        roles_possibles = ["Directeur général", "Directeur General", "Admin", "Administrateur"]
        
        for role in roles_possibles:
            utilisateurs = self.dao_user.rechercher_utilisateurs_par_login(role)
            for u in utilisateurs:
                if u.get("role", "").lower() == role.lower() and u.get("mail"):
                    return u
        return None

    def initier_reinitialisation(self, email_utilisateur: str) -> dict:
        """Initie la demande de réinitialisation de mot de passe."""
        email_utilisateur = (email_utilisateur or "").strip()
        if not email_utilisateur:
            return {"status": "error", "message": "L'adresse e-mail est requise."}

        # 1. Vérifier si l'utilisateur existe
        utilisateur = self._trouver_utilisateur_par_email(email_utilisateur)
        if not utilisateur:
            return {"status": "error", "message": "Aucun compte associé à cet e-mail."}

        code_utilisateur = utilisateur.get("code")

        # 2. Trouver le DG
        dg = self._trouver_directeur_general()
        if not dg:
            return {"status": "error", "message": "Impossible de trouver un administrateur ou Directeur Général pour autoriser la demande."}

        email_dg = dg.get("mail")

        if not self.vault.est_connecte():
            return {"status": "error", "message": "Le service de sécurité (Vault) est indisponible."}

        # 3. Créer une clé TOTP spécifique pour cette demande de réinitialisation
        identifiant_reset = f"reset_{code_utilisateur}"
        
        # Supprimer l'ancienne au cas où
        self.vault.supprimer_cle_totp(identifiant_reset)
        
        # Période de 24h (86400 secondes) pour laisser le temps au DG de transmettre le code
        if not self.vault.creer_cle_totp(identifiant_reset, account_name=f"Reset {email_utilisateur}", period=86400):
            return {"status": "error", "message": "Erreur lors de la génération de la clé d'autorisation."}

        # 4. Générer le code
        code_validation = self.vault.generer_code_otp(identifiant_reset)
        if not code_validation:
            return {"status": "error", "message": "Impossible de générer le code d'autorisation."}

        # 5. Envoyer le code au DG
        if not self.vault.envoyer_email_reset_mdp(email_dg, code_validation, utilisateur):
            return {"status": "error", "message": "Impossible d'envoyer l'e-mail d'autorisation au Directeur Général."}

        return {
            "status": "success", 
            "message": "La demande a été envoyée au Directeur Général. Demandez-lui le code d'autorisation.",
            "email_dg_masque": self._masquer_email(email_dg)
        }

    def valider_reinitialisation(self, email_utilisateur: str, code_validation: str) -> dict:
        """Valide le code et réinitialise le mot de passe."""
        email_utilisateur = (email_utilisateur or "").strip()
        code_validation = (code_validation or "").strip()

        if not email_utilisateur or not code_validation:
            return {"status": "error", "message": "L'e-mail et le code sont requis."}

        utilisateur = self._trouver_utilisateur_par_email(email_utilisateur)
        if not utilisateur:
            return {"status": "error", "message": "Utilisateur introuvable."}

        code_utilisateur = utilisateur.get("code")
        identifiant_reset = f"reset_{code_utilisateur}"

        if not self.vault.est_connecte():
            return {"status": "error", "message": "Le service de sécurité est indisponible."}

        # 1. Vérifier le code
        if not self.vault.verifier_code_otp(identifiant_reset, code_validation):
            return {"status": "error", "message": "Le code d'autorisation est invalide ou a expiré."}

        # Le code est valide ! On peut supprimer la clé de réinitialisation
        self.vault.supprimer_cle_totp(identifiant_reset)

        # 2. Générer un nouveau mot de passe
        nouveau_mdp = self._generer_mot_de_passe()

        # 3. Mettre à jour l'utilisateur
        # On utilise le modèle pour s'assurer que le mdp est hashé par la DAO
        user_modifie = ModeleUser(
            code_utilisateur, 
            nouveau_mdp, 
            utilisateur.get("role"), 
            utilisateur.get("code_personnel")
        )
        self.dao_user.modifier_utilisateur(user_modifie)

        # 4. Réinitialiser la clé TOTP de connexion pour qu'il soit forcé d'en regénérer une à la connexion
        self.vault.supprimer_cle_totp(code_utilisateur)
        self.vault.creer_cle_totp(code_utilisateur, account_name=email_utilisateur)

        # 5. Envoyer le nouveau mot de passe
        if not self.vault.envoyer_nouveau_mdp(email_utilisateur, nouveau_mdp, prenom=utilisateur.get("prenom", "")):
            return {
                "status": "warning", 
                "message": f"Mot de passe réinitialisé, mais l'e-mail n'a pas pu être envoyé. Le nouveau mot de passe est : {nouveau_mdp}"
            }

        return {
            "status": "success",
            "message": "Le mot de passe a été réinitialisé avec succès et envoyé à votre adresse e-mail."
        }

    def _masquer_email(self, email: str) -> str:
        email = (email or "").strip()
        if "@" not in email:
            return email
        local, domaine = email.split("@", 1)
        if len(local) <= 2:
            local_masque = local[:1] + "*"
        else:
            local_masque = local[:2] + "*" * max(len(local) - 2, 1)
        return f"{local_masque}@{domaine}"
