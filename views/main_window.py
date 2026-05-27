from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtCore import Qt

from config import Config
from controllers.controleur_user import UserController
from controllers.controleur_visite import VisiteControleur
from controllers.controleur_permission import PermissionControleur
from views.dashboard_view import DashboardView
from views.login_view import LoginView
from views.otp_dialog import OTPDialog
from views.shared.message_box import CustomMessageBox


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Config.APP_NAME)
        self.setMinimumSize(1200, 800)
        # Enlever la barre de titre par défaut
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.ctrl = UserController()
        self.visite_ctrl = VisiteControleur()
        self.permission_ctrl = PermissionControleur()  # Contrôleur de permissions
        
        # Stocker les infos de l'utilisateur connecté
        self.current_user = None

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Charger le login au début
        self.login_page = LoginView()
        self.stack.addWidget(self.login_page)
        self.login_page.login_success.connect(self.tenter_connexion)
        
        # Afficher en plein écran dès le lancement
        self.showMaximized()



    def tenter_connexion(self, _credentials=None):
        login = self.login_page.input_login.text().strip()
        mdp   = self.login_page.input_password.text()

        res = self.ctrl.gerer_authentification(login, mdp)
        if res["status"] == "success":
            self.afficher_dashboard(res["user_info"])
        elif res["status"] == "otp_required":
            self._verifier_connexion_otp(res)
        else:
            CustomMessageBox.error(self, "Erreur de connexion", res["message"])

    def _verifier_connexion_otp(self, contexte_otp: dict):
        code_utilisateur = contexte_otp.get("user_code", "")
        email_masque     = contexte_otp.get("masked_email", "votre adresse email")

        # Afficher le dialogue OTP moderne
        dialog = OTPDialog(email_masque, parent=self)
        
        # Connecter le signal de renvoi de code
        dialog.resend_requested.connect(lambda: self._renvoyer_code_otp(code_utilisateur, email_masque))
        
        if dialog.exec() != OTPDialog.Accepted:
            CustomMessageBox.info(
                self,
                "Connexion interrompue",
                "La vérification OTP a été annulée.",
            )
            return
        
        code_otp = dialog.get_otp_code()
        if not code_otp:
            return

        res = self.ctrl.verifier_otp_connexion(code_utilisateur, code_otp)
        if res["status"] == "success":
            self.afficher_dashboard(res["user_info"])
        else:
            CustomMessageBox.error(self, "Code OTP invalide", res["message"])
    
    def _renvoyer_code_otp(self, code_utilisateur: str, email_masque: str):
        """Renvoie un nouveau code OTP à l'utilisateur"""
        # Récupérer les infos utilisateur pour régénérer l'OTP
        infos = self.ctrl.dao.rechercher_utilisateur(code_utilisateur)
        if not infos:
            CustomMessageBox.error(self, "Erreur", "Impossible de renvoyer le code.")
            return
        
        # Générer et envoyer un nouveau code OTP
        from core.vault_service import VaultService
        vault = VaultService()
        
        if not vault.est_connecte():
            CustomMessageBox.error(self, "Erreur", "Service Vault indisponible.")
            return
        
        code_otp = vault.generer_code_otp(code_utilisateur)
        if not code_otp:
            CustomMessageBox.error(self, "Erreur", "Impossible de générer un nouveau code.")
            return
        
        email = infos.get("mail", "")
        prenom = infos.get("prenom", "")
        
        if vault.envoyer_otp_par_email(email, code_otp, prenom=prenom):
            CustomMessageBox.info(
                self,
                "Code renvoyé",
                f"Un nouveau code a été envoyé à {email_masque}.",
            )
        else:
            CustomMessageBox.error(self, "Erreur", "Impossible d'envoyer le code par email.")

    # ─────────────────────────────────────────────────────────────────────────
    # Dashboard
    # ─────────────────────────────────────────────────────────────────────────

    def afficher_dashboard(self, user_info):
        # Stocker les informations de l'utilisateur connecté
        self.current_user = user_info
        
        # Création du dashboard (Sidebar) avec les infos utilisateur et le contrôleur de permissions
        self.dashboard = DashboardView(user_info, self.visite_ctrl, self.permission_ctrl)
        # Connecter le signal de déconnexion
        self.dashboard.logout_requested.connect(self.deconnecter_utilisateur)
        
        # L'affichage par défaut du Dashboard est la page Accueil (index 0).
        self.stack.addWidget(self.dashboard)
        self.stack.setCurrentWidget(self.dashboard)
        self.showMaximized()
    
    def deconnecter_utilisateur(self):
        """Déconnecte l'utilisateur et retourne à la page de connexion."""
        # Supprimer la clé TOTP de l'utilisateur dans Vault pour permettre une nouvelle connexion
        if self.current_user:
            code_utilisateur = self.current_user.get("code", "")
            if code_utilisateur:
                from core.vault_service import VaultService
                vault = VaultService()
                if vault.est_connecte():
                    # Supprimer la clé TOTP pour forcer la génération d'un nouveau code
                    vault.supprimer_cle_totp(code_utilisateur)
        
        # Réinitialiser l'utilisateur courant
        self.current_user = None
        
        # Supprimer le dashboard du stack
        if hasattr(self, 'dashboard'):
            self.stack.removeWidget(self.dashboard)
            self.dashboard.deleteLater()
            del self.dashboard
        
        # Réinitialiser les champs de connexion
        self.login_page.input_login.clear()
        self.login_page.input_password.clear()
        
        # Retourner à la page de connexion
        self.stack.setCurrentWidget(self.login_page)
        # Garder le plein écran au lieu de revenir en mode normal
        # self.showNormal()  # Ligne commentée pour garder le plein écran
        
        # Message de confirmation
        CustomMessageBox.info(
            self,
            "Déconnexion réussie",
            "Vous avez été déconnecté avec succès."
        )