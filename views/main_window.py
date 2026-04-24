from PySide6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from views.login_view import LoginView
from views.dashboard_view import DashboardView
from views.graphiques import GrapheView
from controllers.controleur_user import UserController
# 1. N'oublie pas l'import en haut du fichier
from controllers.controleur_visite import VisiteControleur
from config import Config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Config.APP_NAME)
        self.setMinimumSize(1200, 800)
        self.ctrl = UserController()
        self.visite_ctrl = VisiteControleur() # <-- C'est cette ligne qui manque
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Charger le login au début
        self.login_page = LoginView()
        self.stack.addWidget(self.login_page)
        self.login_page.btn_login.clicked.connect(self.tenter_connexion)

    def tenter_connexion(self):
        role = self.login_page.combo_role.currentText()
        mdp = self.login_page.input_password.text()
        
        res = self.ctrl.gerer_authentification(role, mdp)
        if res["status"] == "success":
            self.afficher_dashboard(res["user_info"])
        else:
            QMessageBox.warning(self, "Erreur", res["message"])

    def afficher_dashboard(self, user_info):
        # Création du dashboard (Sidebar)
        self.dashboard = DashboardView(user_info, self.visite_ctrl)
        # Remplacement du contenu par les graphes
        self.graphes = GrapheView()
        self.dashboard.workspace_stack.addWidget(self.graphes)
        self.dashboard.workspace_stack.setCurrentWidget(self.graphes)
        
        self.stack.addWidget(self.dashboard)
        self.stack.setCurrentWidget(self.dashboard)
        self.showMaximized()