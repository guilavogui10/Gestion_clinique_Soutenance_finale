from service_metier.session_autorisation_service import SessionAutorisationService


class SessionAutorisationControleur:
    """Contrôleur pour l'autorisation DG de changement de session."""

    def __init__(self):
        self.service = SessionAutorisationService()

    def initier_autorisation(self, email: str) -> dict:
        return self.service.initier_autorisation(email)

    def verifier_autorisation(self, email: str, code: str) -> dict:
        return self.service.verifier_autorisation(email, code)
