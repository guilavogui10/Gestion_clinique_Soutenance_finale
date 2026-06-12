import logging

from data.dao_user import UserDAO
from core.vault_service import VaultService


class SessionAutorisationService:
    """
    Vérifie que l'utilisateur est Directeur Général, génère un OTP
    et l'envoie par email pour autoriser le changement de session de visualisation.
    """

    ROLES_DG = {"directeur général", "directeur general", "admin", "administrateur"}
    IDENTIFIANT_PREFIX = "session_auth_"
    PERIODE_OTP = 300  # 5 minutes

    def __init__(self):
        self.dao_user = UserDAO()
        self.vault = VaultService()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # API PUBLIQUE
    # =========================================================================

    def initier_autorisation(self, email: str) -> dict:
        """
        Étape 1 : vérifie que l'email appartient au DG,
        génère un OTP 5 min et l'envoie par email.
        Retourne {status, message} ou {status, message, email_masque}.
        """
        email = (email or "").strip()
        if not email:
            return {"status": "error", "message": "L'adresse e-mail est requise."}

        utilisateur = self._trouver_par_email(email)
        if not utilisateur:
            return {"status": "error", "message": "Aucun compte associé à cet e-mail."}

        role = (utilisateur.get("role") or "").strip().lower()
        if role not in self.ROLES_DG:
            return {
                "status": "error",
                "message": "Seul le Directeur Général peut modifier la session de visualisation."
            }

        if not self.vault.est_connecte():
            return {"status": "error", "message": "Le service de sécurité (Vault) est indisponible."}

        code_user = utilisateur.get("code")
        identifiant = f"{self.IDENTIFIANT_PREFIX}{code_user}"
        prenom = utilisateur.get("prenom") or utilisateur.get("nom") or ""

        self.vault.supprimer_cle_totp(identifiant)
        if not self.vault.creer_cle_totp(
            identifiant,
            account_name=f"SessionAuth {email}",
            period=self.PERIODE_OTP
        ):
            return {"status": "error", "message": "Erreur lors de la génération de la clé d'autorisation."}

        code_otp = self.vault.generer_code_otp(identifiant)
        if not code_otp:
            return {"status": "error", "message": "Impossible de générer le code d'autorisation."}

        if not self.vault.envoyer_otp_par_email(email, code_otp, prenom):
            return {"status": "error", "message": "Impossible d'envoyer le code d'autorisation par e-mail."}

        return {
            "status": "success",
            "message": "Code envoyé. Vous avez 5 minutes pour l'utiliser.",
            "email_masque": self._masquer_email(email),
        }

    def verifier_autorisation(self, email: str, code: str) -> dict:
        """
        Étape 2 : vérifie le code OTP saisi par le DG.
        Retourne {status: "success"} ou {status: "error", message}.
        """
        email = (email or "").strip()
        code  = (code  or "").strip()

        if not email or not code:
            return {"status": "error", "message": "L'e-mail et le code sont requis."}

        utilisateur = self._trouver_par_email(email)
        if not utilisateur:
            return {"status": "error", "message": "Utilisateur introuvable."}

        if not self.vault.est_connecte():
            return {"status": "error", "message": "Le service de sécurité est indisponible."}

        code_user  = utilisateur.get("code")
        identifiant = f"{self.IDENTIFIANT_PREFIX}{code_user}"

        if not self.vault.verifier_code_otp(identifiant, code):
            return {"status": "error", "message": "Code invalide ou expiré."}

        self.vault.supprimer_cle_totp(identifiant)
        return {"status": "success"}

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _trouver_par_email(self, email: str) -> dict | None:
        utilisateurs = self.dao_user.rechercher_utilisateurs_par_login(email)
        if not utilisateurs:
            return None
        for u in utilisateurs:
            if u.get("mail") == email:
                return u
        return utilisateurs[0] if utilisateurs else None

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
