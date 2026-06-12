# Importations des classes
from service_metier.user_service import UserService

class UserController:
    def __init__(self):
        self.service = UserService()

    def gerer_creation(self, mdp: str, role: str, id_personnel: str) -> dict:
        return self.service.gerer_creation(mdp, role, id_personnel)

    def gerer_authentification(self, login: str, mdp: str) -> dict:
        return self.service.gerer_authentification(login, mdp)

    def verifier_otp_connexion(self, code_utilisateur: str, code_otp: str) -> dict:
        return self.service.verifier_otp_connexion(code_utilisateur, code_otp)

    def gerer_recherche_utilisateur(self, code: str) -> dict:
        return self.service.gerer_recherche_utilisateur(code)

    def rechercher_par_code_personnel(self, code_personnel: str) -> dict | None:
        """
        Recherche un utilisateur via son code personnel lié.
        Permet d'identifier un utilisateur précis parmi ceux du même rôle.
        """
        return self.service.dao.rechercher_par_code_personnel(code_personnel)

    def gerer_suppression(self, code: str) -> dict:
        return self.service.gerer_suppression(code)

    def obtenir_roles_disponibles(self) -> list:
        """
        Récupère la liste des rôles disponibles dans le système.
        Respect du principe MVC : Vue -> Contrôleur -> Service -> DAO
        """
        return self.service.obtenir_roles_disponibles()
