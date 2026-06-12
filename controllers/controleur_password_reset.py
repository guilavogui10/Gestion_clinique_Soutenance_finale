from service_metier.password_reset_service import PasswordResetService

class PasswordResetController:
    def __init__(self):
        self.service = PasswordResetService()

    def initier_reinitialisation(self, email_utilisateur: str) -> dict:
        """Initie la demande de réinitialisation de mot de passe."""
        return self.service.initier_reinitialisation(email_utilisateur)

    def valider_reinitialisation(self, email_utilisateur: str, code_validation: str) -> dict:
        """Valide le code et réinitialise le mot de passe."""
        return self.service.valider_reinitialisation(email_utilisateur, code_validation)
