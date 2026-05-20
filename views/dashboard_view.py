from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QLabel, QStackedWidget, QFrame, QSpacerItem, QSizePolicy, QButtonGroup, QMenu)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QPixmap
import qtawesome as qta
from config import Config
from views.shared.theme_manager import theme_manager
from views.shared.styles import Styles
from views.shared.message_box import CustomMessageBox
from views.home import AccueilView
from views.patient import VuePatient
from views.graphiques import GrapheView
from views.visite import VisiteView
from views.rendez_vous import RendezVousView
from views.consultation import ConsultationView
from views.examen import ExamenView
from views.chirurgie import ChirurgieView
from views.lunette import CommandeLunetteView
from views.produit import GestionProduitsView
from views.facturation import FacturationView
from views.prescription import PrescriptionView
from views.fournisseur import FournisseurView
from views.personnel import PersonnelView
from views.admin import AdminView
from views.settings.vue_parametre import ParametreView
from views.acte_medical import VueActeMedical
from views.resultat_medical.vue_resultat_medical import VueResultatMedical


class DashboardView(QWidget):
    logout_requested = Signal()  # Signal pour demander la déconnexion
    
    def __init__(self, user_info, visite_ctrl, permission_ctrl=None):
        super().__init__()
        # Enlever la barre de titre par défaut
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        self.user_info = user_info
        self.visite_ctrl = visite_ctrl
        self.permission_ctrl = permission_ctrl  # Contrôleur de permissions
        
        # Extraire les infos utilisateur pour les permissions
        self.code_utilisateur = user_info.get("code", "")
        self.role = user_info.get("role", "")
        self.est_responsable = bool(user_info.get("est_responsable", 0))
        from controllers.controleur_consultation import ConsultationControleur
        from controllers.controleur_rendez_vous import RendezVousControleur
        from controllers.controleur_examen import ExamenControleur
        from controllers.controleur_chururgie import ChirurgieControleur  
        from controllers.controleur_lunette import CommandeLunetteControleur  
        from controllers.controleur_prescription import PrescriptionControleur  
        self.rendez_vous_ctrl = RendezVousControleur()
        self.examen_ctrl = ExamenControleur()
        self.consultation_ctrl = ConsultationControleur()
        self.chirurgie_ctrl = ChirurgieControleur()
        self.commande_lunette_ctrl = CommandeLunetteControleur()
        self.prescription_ctrl = PrescriptionControleur()
        
        self.init_ui()
        self.setup_navigation()
        
        # Écouter les changements de thème pour mise à jour dynamique
        theme_manager.theme_changed.connect(self.apply_theme)

    def init_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # 1. SIDEBAR avec scroll
        self.sidebar_container = QFrame()
        self.sidebar_container.setObjectName("sidebar_container")
        self.sidebar_container.setFixedWidth(100)
        container_layout = QVBoxLayout(self.sidebar_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Scroll area pour la sidebar
        from PySide6.QtWidgets import QScrollArea
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.sidebar_scroll.setFrameShape(QFrame.NoFrame)
        
        self.sidebar = QFrame()
        self.sidebar.setObjectName("main_sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 15, 12, 15)
        sidebar_layout.setSpacing(10)

        # Logo OEIL (compact)
        self.logo_icon = QLabel()
        self.logo_icon.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.logo_icon)

        # Bouton de basculement de thème (icône seulement)
        self.btn_theme = QPushButton()
        self.btn_theme.setFixedSize(76, 40)
        sidebar_layout.addWidget(self.btn_theme, 0, Qt.AlignCenter)
        sidebar_layout.addSpacing(4)

        # Navigation (CRÉATION DES BOUTONS)
        self.btn_accueil = self.create_nav_btn("Accueil", 'fa5s.home')
        self.btn_patients = self.create_nav_btn("Patients", 'fa5s.user-injured')
        self.btn_rendez_vous = self.create_nav_btn("Rendez-vous", 'fa5s.calendar-check')
        self.btn_consults = self.create_nav_btn("Consultations", 'fa5s.stethoscope')
        self.btn_visites= self.create_nav_btn("visite", 'fa5s.walking')
        self.btn_examens = self.create_nav_btn("Examens", 'fa5s.microscope')
        self.btn_chirurgies = self.create_nav_btn("Chirurgies", 'fa5s.procedures')
        self.btn_lunettes = self.create_nav_btn("Lunettes", 'fa5s.glasses')
        self.btn_panier = self.create_nav_btn("Pharmacie", 'fa5s.pills')
        self.btn_prescription = self.create_nav_btn("Prescriptions", 'fa5s.prescription')
        self.btn_facturation = self.create_nav_btn("Facturation", 'fa5s.file-invoice-dollar')
        self.btn_fournisseurs = self.create_nav_btn("Fournisseurs", 'fa5s.truck')
        self.btn_personnel = self.create_nav_btn("Personnel", 'fa5s.user-md')
        self.btn_actes = self.create_nav_btn("Actes", 'fa5s.file-medical-alt')
        self.btn_resultats = self.create_nav_btn("Résultats", 'fa5s.file-image')
        self.btn_admin = self.create_nav_btn("Administration", 'fa5s.user-shield')
        self.btn_settings = self.create_nav_btn("Paramètres", 'fa5s.cogs')

        # AJOUT AU GROUPE (Une fois qu'ils sont créés)
        self.nav_group = QButtonGroup(self)
        for btn in [self.btn_accueil, self.btn_patients, self.btn_visites, self.btn_rendez_vous, self.btn_consults, self.btn_examens,
                    self.btn_chirurgies, self.btn_lunettes, self.btn_panier,
                    self.btn_prescription, self.btn_facturation, self.btn_fournisseurs,
                    self.btn_personnel, self.btn_actes, self.btn_resultats, self.btn_admin, self.btn_settings]:
            self.nav_group.addButton(btn)
            sidebar_layout.addWidget(btn, 0, Qt.AlignCenter)
        self.nav_group.setExclusive(True)
        self.btn_accueil.setChecked(True)  # Accueil sélectionné par défaut

        # --- FRAME DE BAS DE SIDEBAR (compact) ---
        sidebar_layout.addStretch() 

        self.footer_frame = QFrame()
        self.footer_frame.setFixedHeight(60)
        self.footer_frame.setObjectName("FooterFrame")
        footer_layout = QVBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(4, 4, 4, 4)
        footer_layout.setSpacing(2)
        
        self.lbl_version = QLabel("v1.0.2")
        self.lbl_version.setAlignment(Qt.AlignCenter)
        self.lbl_version.setStyleSheet("font-size: 8px; color: gray;")

        footer_layout.addWidget(self.lbl_version)
        sidebar_layout.addWidget(self.footer_frame)

        self.btn_logout = self.create_nav_btn("Déconnexion", 'fa5s.sign-out-alt')
        sidebar_layout.addWidget(self.btn_logout, 0, Qt.AlignCenter)
        
        # Ajouter la sidebar au scroll
        self.sidebar_scroll.setWidget(self.sidebar)
        container_layout.addWidget(self.sidebar_scroll)

        # 2. CONTENT AREA
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # Header avec navigation horizontale
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(70)
        self.header_frame.setObjectName("main_header")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(20)
        
        # Logo + Nom (gauche)
        logo_container = QWidget()
        logo_container.setObjectName("logo_container")
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(40, 0, 0, 0)
        logo_layout.setSpacing(12)
        
        self.logo_icon_header = QLabel()
        self.logo_icon_header.setFixedSize(50, 50)
        self.logo_icon_header.setAlignment(Qt.AlignCenter)
        self.logo_icon_header.setObjectName("logo_icon_header")
        logo_layout.addWidget(self.logo_icon_header)
        
        logo_text_container = QWidget()
        logo_text_container.setObjectName("logo_text_container")
        logo_text_layout = QVBoxLayout(logo_text_container)
        logo_text_layout.setContentsMargins(0, 0, 0, 0)
        logo_text_layout.setSpacing(0)
        
        self.lbl_app_name = QLabel("VisionCare")
        self.lbl_app_name.setObjectName("app_name")
        logo_text_layout.addWidget(self.lbl_app_name)
        
        self.lbl_app_subtitle = QLabel("Clinique Ophtalmologique")
        self.lbl_app_subtitle.setObjectName("app_subtitle")
        logo_text_layout.addWidget(self.lbl_app_subtitle)
        
        logo_layout.addWidget(logo_text_container)
        header_layout.addWidget(logo_container)
        
        header_layout.addSpacing(30)
        
        # Menu de navigation horizontal (centre)
        nav_container = QWidget()
        nav_container.setObjectName("nav_container")
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(5)
        
        self.btn_nav_accueil = self.create_header_nav_btn("Accueil", 'fa5s.home')
        self.btn_nav_apropos = self.create_header_nav_btn("À propos", 'fa5s.info-circle')
        self.btn_nav_services = self.create_header_nav_btn("Services", 'fa5s.concierge-bell')
        self.btn_nav_equipe = self.create_header_nav_btn("Équipe", 'fa5s.users')
        self.btn_nav_rdv = self.create_header_nav_btn("Rendez-vous", 'fa5s.calendar-check')
        self.btn_nav_contact = self.create_header_nav_btn("Contact", 'fa5s.envelope')
        
        nav_layout.addWidget(self.btn_nav_accueil)
        nav_layout.addWidget(self.btn_nav_apropos)
        nav_layout.addWidget(self.btn_nav_services)
        nav_layout.addWidget(self.btn_nav_equipe)
        nav_layout.addWidget(self.btn_nav_rdv)
        nav_layout.addWidget(self.btn_nav_contact)
        
        header_layout.addWidget(nav_container)
        header_layout.addStretch()
        
        # Bouton Login (droite)
        login_container = QWidget()
        login_container.setObjectName("login_container")
        login_layout = QHBoxLayout(login_container)
        login_layout.setContentsMargins(0, 0, 40, 0)
        
        self.btn_login = QPushButton()
        self.btn_login.setIcon(qta.icon('fa5s.user', color='white'))
        self.btn_login.setIconSize(QSize(16, 16))
        self.btn_login.setText("  Login")
        self.btn_login.setFixedHeight(40)
        self.btn_login.setMinimumWidth(100)
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setObjectName("btn_login")
        self.btn_login.clicked.connect(self._show_login_menu)
        login_layout.addWidget(self.btn_login)
        
        header_layout.addWidget(login_container)

        # --- STACKED WIDGET ---
        self.workspace_stack = QStackedWidget()
        
        # PAGES
        self.page_accueil = AccueilView()  # Index 0 - Page d'accueil
        # Connecter le signal de navigation de la page d'accueil
        self.page_accueil.navigate_to.connect(self._handle_accueil_navigation)
        from controllers.controleur_patient import ControleurPatient
        self.patient_ctrl = ControleurPatient()
        self.page_patients = VuePatient(self.patient_ctrl)  # Index 1
        self.page_visites = VisiteView(self.visite_ctrl)  # Index 2
        self.page_rendez_vous = RendezVousView(self.rendez_vous_ctrl)  # Index 3
        self.page_consultation = ConsultationView(self.consultation_ctrl, self.permission_ctrl, self.user_info)  # Index 4
        self.page_examens = ExamenView(self.examen_ctrl, self.permission_ctrl, self.user_info)  # Index 5
        self.page_chirurgies = ChirurgieView(self.chirurgie_ctrl, self.permission_ctrl, self.user_info)  # Index 6
        self.page_lunettes = CommandeLunetteView(self.commande_lunette_ctrl)  # Index 7
        self.page_prescription = PrescriptionView(self.prescription_ctrl, self.permission_ctrl, self.user_info)  # Index 8
        self.page_settings = ParametreView()
        # Import du contrôleur produit
        from controllers.controleur_produit import ProduitControleur
        self.produit_ctrl = ProduitControleur()
        self.page_gestion_panier = GestionProduitsView(self.produit_ctrl)

        # Facturation avec onglets
        from controllers.controleur_facture_patient import FacturePatientControleur
        from controllers.controleur_panier_facture_patient import PanierFacturePatientControleur
        self.facture_patient_ctrl = FacturePatientControleur()
        self.panier_facture_patient_ctrl = PanierFacturePatientControleur()
        self.page_facturation = FacturationView(
            self.facture_patient_ctrl, self.panier_facture_patient_ctrl
        )
        
        # Fournisseurs
        from controllers.controleur_fournisseur import FournisseurControleur
        self.fournisseur_ctrl = FournisseurControleur()
        self.page_fournisseurs = FournisseurView(self.fournisseur_ctrl)

        # Paramètres
        self.page_settings = ParametreView()
        
        # Personnel
        from controllers.controleur_personnel import ControllerPersonnel
        self.personnel_ctrl = ControllerPersonnel()
        self.page_personnel = PersonnelView(self.personnel_ctrl)
        
        # Administration
        self.page_admin = AdminView(self.visite_ctrl)

        # Actes médicaux
        from controllers.controleur_acte_medicale import ActeMedicalControleur
        self.acte_medical_ctrl = ActeMedicalControleur()
        self.page_actes = VueActeMedical(self.acte_medical_ctrl)

        # Résultats médicaux
        from controllers.controleur_resultat_medical import ResultatMedicalControleur
        self.resultat_ctrl = ResultatMedicalControleur()
        self.page_resultats = VueResultatMedical(self.resultat_ctrl, self.permission_ctrl, self.user_info)

        self.workspace_stack.addWidget(self.page_accueil)  # Index 0 - ACCUEIL
        self.workspace_stack.addWidget(self.page_patients)  # Index 1
        self.workspace_stack.addWidget(self.page_visites)  # Index 2
        self.workspace_stack.addWidget(self.page_rendez_vous)  # Index 3
        self.workspace_stack.addWidget(self.page_consultation)  # Index 4
        self.workspace_stack.addWidget(self.page_examens)  # Index 5
        self.workspace_stack.addWidget(self.page_chirurgies)  # Index 6
        self.workspace_stack.addWidget(self.page_lunettes)  # Index 7
        self.workspace_stack.addWidget(self.page_gestion_panier)  # Index 8
        self.workspace_stack.addWidget(self.page_prescription)  # Index 9
        self.workspace_stack.addWidget(self.page_facturation)  # Index 10
        self.workspace_stack.addWidget(self.page_fournisseurs)  # Index 11
        self.workspace_stack.addWidget(self.page_personnel)  # Index 12
        self.workspace_stack.addWidget(self.page_admin)  # Index 13
        self.workspace_stack.addWidget(self.page_settings)  # Index 14
        self.workspace_stack.addWidget(self.page_actes)  # Index 15
        self.workspace_stack.addWidget(self.page_resultats)  # Index 16

        self.content_layout.addWidget(self.header_frame)
        self.content_layout.addWidget(self.workspace_stack)

        self.layout.addWidget(self.sidebar_container)
        self.layout.addWidget(self.content_area)
        
        self.apply_theme()

    def create_header_nav_btn(self, text, icon_name):
        """Crée un bouton de navigation pour le header horizontal avec icône."""
        btn = QPushButton()
        btn.setFixedHeight(40)
        btn.setMinimumWidth(120)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setObjectName("header_nav_btn")
        btn.setProperty("nav_text", text)
        btn.setProperty("nav_icon", icon_name)
        
        # Layout horizontal pour icône + texte
        layout = QHBoxLayout(btn)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)
        
        # Icône
        icon_label = QLabel()
        icon_label.setObjectName("nav_icon_label")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(16, 16)
        layout.addWidget(icon_label)
        
        # Texte
        text_label = QLabel(text)
        text_label.setObjectName("nav_text_label")
        text_label.setWordWrap(False)
        layout.addWidget(text_label)
        
        return btn
    
    def create_nav_btn(self, text, icon_name):
        """Crée un bouton de navigation compact dans la sidebar (icône + texte vertical)."""
        c = theme_manager.colors()
        btn = QPushButton()
        btn.setProperty("icon_name", icon_name)
        btn.setProperty("text_label", text)
        btn.setCheckable(True)
        btn.setFixedSize(76, 56)
        btn.setCursor(Qt.PointingHandCursor)
        
        # Layout vertical pour icône + texte
        layout = QVBoxLayout(btn)
        layout.setContentsMargins(5, 6, 5, 6)
        layout.setSpacing(4)
        
        # Texte en haut
        label_text = QLabel(text)
        label_text.setAlignment(Qt.AlignCenter)
        label_text.setWordWrap(True)
        label_text.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 9px; font-weight: 600; "
            "border: none; background: transparent;"
        )
        label_text.setObjectName("btn_text_label")
        
        # Icône au milieu
        label_icon = QLabel()
        label_icon.setPixmap(qta.icon(icon_name, color=c['primary']).pixmap(QSize(24, 24)))
        label_icon.setAlignment(Qt.AlignCenter)
        label_icon.setStyleSheet("border: none; background: transparent;")
        label_icon.setObjectName("btn_icon_label")
        
        layout.addWidget(label_text)
        layout.addWidget(label_icon)
        layout.addStretch()
        
        return btn

    def setup_navigation(self):
        self.btn_accueil.clicked.connect(self.show_home)
        self.btn_patients.clicked.connect(self.show_patients)
        self.btn_visites.clicked.connect(self.show_visites)
        self.btn_rendez_vous.clicked.connect(self.show_rendez_vous)
        self.btn_consults.clicked.connect(self.show_consultation)
        self.btn_examens.clicked.connect(self.show_examen)
        self.btn_chirurgies.clicked.connect(self.show_chirurgie)
        self.btn_lunettes.clicked.connect(self.show_commande_lunette)
        self.btn_panier.clicked.connect(self.show_pharmacie)
        self.btn_prescription.clicked.connect(self.show_prescription)
        self.btn_facturation.clicked.connect(self.show_facturation)
        self.btn_fournisseurs.clicked.connect(self.show_fournisseurs)
        self.btn_personnel.clicked.connect(self.show_personnel)
        self.btn_actes.clicked.connect(self.show_actes)
        self.btn_resultats.clicked.connect(self.show_resultats)
        self.btn_admin.clicked.connect(self.show_admin)
        self.btn_settings.clicked.connect(self.show_settings)
        self.btn_theme.clicked.connect(self.toggle_theme)
        
        # Boutons du header
        self.btn_nav_accueil.clicked.connect(self.show_home)
        self.btn_nav_apropos.clicked.connect(self.show_settings)
        self.btn_nav_services.clicked.connect(self._show_header_services_menu)
        self.btn_nav_equipe.clicked.connect(self.show_personnel)
        self.btn_nav_rdv.clicked.connect(self.show_rendez_vous)
        self.btn_nav_contact.clicked.connect(self.show_settings)
        
        # Connecter tous les boutons pour mettre à jour les indicateurs
        for btn in [self.btn_accueil, self.btn_patients, self.btn_visites, self.btn_rendez_vous, self.btn_consults, self.btn_examens,
                    self.btn_chirurgies, self.btn_lunettes, self.btn_panier,
                    self.btn_prescription, self.btn_facturation, self.btn_fournisseurs,
                    self.btn_personnel, self.btn_actes, self.btn_resultats, self.btn_admin, self.btn_logout, self.btn_settings]:
            btn.clicked.connect(self._update_nav_indicators)

    def _update_nav_indicators(self):
        """Met à jour les indicateurs de ligne pour tous les boutons."""
        pass
    
    def _show_header_services_menu(self):
        """Affiche le menu déroulant des services depuis le header."""
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self)
        menu.setObjectName("header_services_menu")
        
        # Définir les services avec icônes
        services = [
            ('fa5s.stethoscope', 'Consultation', '#3B82F6', self.show_consultation),
            ('fa5s.microscope', 'Examens', '#10B981', self.show_examen),
            ('fa5s.procedures', 'Chirurgie', '#8B5CF6', self.show_chirurgie),
            ('fa5s.glasses', 'Lunettes', '#F59E0B', self.show_commande_lunette),
            ('fa5s.pills', 'Pharmacie', '#EF4444', self.show_pharmacie),
            ('fa5s.calendar-check', 'Rendez-vous', '#06B6D4', self.show_rendez_vous),
        ]
        
        # Créer les actions du menu
        for icon_name, service_name, color, nav_method in services:
            action = menu.addAction(
                qta.icon(icon_name, color=color),
                f"  {service_name}"
            )
            action.triggered.connect(nav_method)
        
        # Appliquer le style au menu
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 0;
            }
            QMenu::item {
                padding: 10px 20px;
                color: #1F2937;
                font-size: 13px;
                font-weight: 500;
            }
            QMenu::item:selected {
                background-color: #EFF6FF;
                color: #3B82F6;
            }
            QMenu::icon {
                padding-left: 10px;
            }
        """)
        
        # Afficher le menu sous le bouton
        menu.exec(self.btn_nav_services.mapToGlobal(self.btn_nav_services.rect().bottomLeft()))
    
    def _show_login_menu(self):
        """Affiche le menu déroulant du bouton Login."""
        menu = QMenu(self)
        menu.setObjectName("login_menu")
        
        # Action Déconnexion
        action_logout = menu.addAction(
            qta.icon('fa5s.sign-out-alt', color='#EF4444'),
            "  Déconnexion"
        )
        action_logout.triggered.connect(self._confirmer_deconnexion)
        
        # Action Créer compte
        action_create = menu.addAction(
            qta.icon('fa5s.user-plus', color='#3B82F6'),
            "  Créer compte"
        )
        action_create.triggered.connect(self._creer_compte)
        
        # Appliquer le style au menu
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 0;
            }
            QMenu::item {
                padding: 10px 20px;
                color: #1F2937;
                font-size: 13px;
                font-weight: 500;
            }
            QMenu::item:selected {
                background-color: #EFF6FF;
                color: #3B82F6;
            }
            QMenu::icon {
                padding-left: 10px;
            }
        """)
        
        # Afficher le menu sous le bouton
        menu.exec(self.btn_login.mapToGlobal(self.btn_login.rect().bottomLeft()))
    
    def _confirmer_deconnexion(self):
        """Demande confirmation avant de déconnecter."""
        reponse = CustomMessageBox.confirm(
            self,
            "Confirmation de déconnexion",
            "Voulez-vous vraiment vous déconnecter ?"
        )
        
        if reponse:
            self.logout_requested.emit()
    
    def _creer_compte(self):
        """Ouvre l'interface de création de compte (Administration)."""
        self.show_admin()

    def toggle_theme(self):
        """Bascule vers le thème suivant (Clair → Sombre → Océan → Clair)."""
        theme_manager.next_theme()

    def apply_theme(self):
        """
        Applique le thème actif à tout le dashboard.
        Appelé automatiquement quand le ThemeManager émet theme_changed.
        """
        c = theme_manager.colors()

        # ── Logo (compact) ──
        icon_color = c['primary']
        self.logo_icon.setPixmap(
            qta.icon('fa5s.eye', color=icon_color).pixmap(QSize(50, 50))
        )

        # ── Sidebar container ──
        self.sidebar_container.setStyleSheet(f"""
            QFrame#sidebar_container {{
                background-color: {c['bg_card']};
                border-radius: 15px;
                border: 1px solid {c['border']};
            }}
        """)
        
        # ── Scroll area de la sidebar ──
        self.sidebar_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                border-radius: 3px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border_light']};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c['primary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
        # ── Sidebar ──
        self.sidebar.setStyleSheet(f"""
            QFrame#main_sidebar {{
                background-color: transparent;
                border: none;
            }}
        """)

        # ── Bouton thème (icône seulement) ──
        next_icon = theme_manager.next_theme_icon()
        self.btn_theme.setText("")
        self.btn_theme.setIcon(qta.icon(next_icon, color=c['primary']))
        self.btn_theme.setIconSize(QSize(24, 24))
        self.btn_theme.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {c['hover']};
            }}
        """)

        # ── Navigation (style compact avec ligne indicatrice) ──
        for btn in [self.btn_accueil, self.btn_patients, self.btn_visites, self.btn_rendez_vous, self.btn_consults, self.btn_examens,
                    self.btn_chirurgies, self.btn_lunettes, self.btn_panier,
                    self.btn_prescription, self.btn_facturation, self.btn_fournisseurs,
                    self.btn_personnel, self.btn_actes, self.btn_resultats, self.btn_admin,
                    self.btn_logout, self.btn_settings]:
            
            is_checked = btn.isChecked()
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                }}
                QPushButton:checked {{
                    background-color: {c['hover']};
                    border-left: 3px solid {c['primary']};
                }}
                QPushButton:hover {{
                    background-color: {c['hover']};
                }}
                QPushButton QLabel {{
                    color: {c['text_primary']};
                    background: transparent;
                    border: none;
                }}
            """)
            
            # Mettre à jour l'icône
            icon_label = btn.findChild(QLabel, "btn_icon_label")
            if icon_label:
                icon_color = c['primary']
                icon_label.setPixmap(
                    qta.icon(btn.property("icon_name") or 'fa5s.circle', color=icon_color).pixmap(QSize(24, 24))
                )
            
            # Mettre à jour le texte
            text_label = btn.findChild(QLabel, "btn_text_label")
            if text_label:
                text_color = c['text_primary']
                text_label.setStyleSheet(
                    f"color: {text_color}; font-size: 9px; font-weight: 600; "
                    "border: none; background: transparent;"
                )

        # ── Zone de contenu ──
        self.content_area.setStyleSheet(Styles.content_area())
        
        # ── Header ──
        self.header_frame.setStyleSheet(f"""
            QFrame#main_header {{
                background-color: white;
                border: none;
                border-bottom: 1px solid #E5E7EB;
            }}
            QWidget#logo_container, QWidget#logo_text_container, 
            QWidget#nav_container, QWidget#login_container {{
                background-color: transparent;
                border: none;
            }}
            QLabel#logo_icon_header {{
                background-color: transparent;
                border: none;
            }}
        """)
        
        # Logo header
        self.logo_icon_header.setPixmap(
            qta.icon('fa5s.eye', color='#3B82F6').pixmap(QSize(50, 50))
        )
        
        self.lbl_app_name.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #1F2937; background: transparent; border: none; font-family: 'Yu Gothic UI', 'Segoe UI', Arial, sans-serif;"
        )
        self.lbl_app_subtitle.setStyleSheet(
            "font-size: 11px; color: #6B7280; background: transparent; border: none; font-family: 'Yu Gothic UI', 'Segoe UI', Arial, sans-serif;"
        )
        
        # Boutons de navigation header
        for btn in [self.btn_nav_accueil, self.btn_nav_apropos, self.btn_nav_services, 
                    self.btn_nav_equipe, self.btn_nav_rdv, self.btn_nav_contact]:
            btn.setStyleSheet(f"""
                QPushButton#header_nav_btn {{
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 12px;
                }}
                QPushButton#header_nav_btn:hover {{
                    background-color: transparent;
                }}
                QLabel#nav_text_label {{
                    color: #6B7280;
                    font-size: 14px;
                    font-weight: 700;
                    background: transparent;
                    border: none;
                    font-family: 'Yu Gothic UI', 'Segoe UI', Arial, sans-serif;
                }}
                QPushButton#header_nav_btn:hover QLabel#nav_text_label {{
                    color: #3B82F6;
                }}
                QLabel#nav_icon_label {{
                    background: transparent;
                    border: none;
                }}
            """)
            
            # Mettre à jour l'icône en bleu gras
            icon_label = btn.findChild(QLabel, "nav_icon_label")
            if icon_label:
                icon_label.setPixmap(
                    qta.icon(btn.property("nav_icon"), color='#3B82F6').pixmap(QSize(16, 16))
                )
        
        # Bouton Login
        self.btn_login.setStyleSheet(f"""
            QPushButton#btn_login {{
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 20px;
            }}
            QPushButton#btn_login:hover {{
                background-color: #2563EB;
            }}
        """)

        # ── Footer sidebar ──
        self.footer_frame.setStyleSheet(Styles.footer())
        self.lbl_version.setStyleSheet(
            f"font-size: 8px; color: {c['text_muted']};"
        )

        # ── Appliquer le QSS global au QApplication ──
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet(Styles.global_qss())

        # ── Propager le thème à toutes les pages enfants ──
        for i in range(self.workspace_stack.count()):
            page = self.workspace_stack.widget(i)
            if hasattr(page, 'apply_theme'):
                try:
                    page.apply_theme()
                except Exception:
                    pass

    def _verifier_acces_interface(self, nom_interface: str) -> bool:
        """
        Vérifie si l'utilisateur peut accéder à une interface.
        Affiche un message d'erreur si l'accès est refusé.
        
        Returns:
            True si accès autorisé, False sinon
        """
        # Si pas de contrôleur de permissions, autoriser tout (mode dégradé)
        if not self.permission_ctrl:
            return True
        
        # DG et Admin ont accès à tout
        if self.role in ["Directeur Général", "Administrateur"]:
            return True
        
        # Vérifier l'accès selon le rôle
        if not self.permission_ctrl.peut_acceder_interface(self.role, nom_interface):
            CustomMessageBox.warning(
                self,
                "Accès refusé",
                f"Votre rôle '{self.role}' ne vous permet pas d'accéder à l'interface '{nom_interface}'."
            )
            return False
        
        return True
    
    def show_home(self):
        self.workspace_stack.setCurrentIndex(0)
    
    def _handle_accueil_navigation(self, page_name: str):
        """Gère la navigation depuis la page d'accueil."""
        navigation_map = {
            "Rendez-vous": self.show_rendez_vous,
            "Consultations": self.show_consultation,
            "Examens": self.show_examen,
            "Chirurgies": self.show_chirurgie,
            "Lunettes": self.show_commande_lunette,
            "Pharmacie": self.show_pharmacie
        }
        
        nav_method = navigation_map.get(page_name)
        if nav_method:
            nav_method()
    
    def show_patients(self):
        # Vérifier l'accès à l'interface Patients
        if not self._verifier_acces_interface("Patients"):
            return
        
        self.workspace_stack.setCurrentIndex(1) 
        if hasattr(self.page_patients, 'charger_donnees'):
            self.page_patients.charger_donnees()
            
    def show_visites(self):
        # Vérifier l'accès à l'interface Visites
        if not self._verifier_acces_interface("Visites"):
            return
        
        self.workspace_stack.setCurrentIndex(2)

    def show_rendez_vous(self):
        # Vérifier l'accès à l'interface Rendez-vous
        if not self._verifier_acces_interface("Rendez-vous"):
            return
        
        self.workspace_stack.setCurrentIndex(3)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_rendez_vous.charger_rendez_vous(code_session)
        
    def show_examen(self):
        # Vérifier l'accès à l'interface Examens
        if not self._verifier_acces_interface("Examens"):
            return
        
        self.workspace_stack.setCurrentIndex(5)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_examens.charger_examens(code_session)
    
    def show_chirurgie(self):
        # Vérifier l'accès à l'interface Chirurgies
        if not self._verifier_acces_interface("Chirurgies"):
            return
        
        self.workspace_stack.setCurrentIndex(6)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_chirurgies.charger_chururgies(code_session)
            
    def show_prescription(self):
        # Vérifier l'accès à l'interface Prescriptions
        if not self._verifier_acces_interface("Prescriptions"):
            return
        
        self.workspace_stack.setCurrentIndex(9)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_prescription.charger_donnees(code_session)

    def show_facturation(self):
        # Vérifier l'accès à l'interface Facturation
        if not self._verifier_acces_interface("Facturation"):
            return
        
        self.workspace_stack.setCurrentIndex(10)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_facturation.charger_donnees(code_session)

    def show_fournisseurs(self):
        # Vérifier l'accès à l'interface Fournisseurs
        if not self._verifier_acces_interface("Fournisseurs"):
            return
        
        self.workspace_stack.setCurrentIndex(11)
        if hasattr(self.page_fournisseurs, "charger_fournisseurs"):
            actif, code_session = self.visite_ctrl.verifier_session_active()
            if actif:
                self.page_fournisseurs.charger_fournisseurs(code_session)
            else:
                self.page_fournisseurs.charger_fournisseurs()

    def show_personnel(self):
        # Vérifier l'accès à l'interface Personnel
        if not self._verifier_acces_interface("Personnel"):
            return
        
        self.workspace_stack.setCurrentIndex(12)
        if hasattr(self.page_personnel, "charger_personnels"):
            self.page_personnel.charger_personnels()
    
    def show_admin(self):
        self.workspace_stack.setCurrentIndex(13)
            
    def show_commande_lunette(self):
        # Vérifier l'accès à l'interface Lunettes
        if not self._verifier_acces_interface("Lunettes"):
            return
        
        self.workspace_stack.setCurrentIndex(7)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_lunettes.charger_commandes(code_session)
            
    def show_pharmacie(self):
        # Vérifier l'accès à l'interface Pharmacie
        if not self._verifier_acces_interface("Pharmacie"):
            return
        
        self.workspace_stack.setCurrentIndex(8)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_gestion_panier.charger_donnees(code_session)
        
        
    def show_consultation(self):
        # Vérifier l'accès à l'interface Consultations
        if not self._verifier_acces_interface("Consultations"):
            return
        
        self.workspace_stack.setCurrentIndex(4)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_consultation.charger_consultations(code_session)

    # show_settings est appelé par le bouton "Paramètres" dans la sidebar
    def show_settings(self):
        self.workspace_stack.setCurrentIndex(14)

    def show_actes(self):
        self.workspace_stack.setCurrentIndex(15)

    def show_resultats(self):
        self.workspace_stack.setCurrentIndex(16)
        if hasattr(self.page_actes, "load_data"):
            self.page_actes.load_data()