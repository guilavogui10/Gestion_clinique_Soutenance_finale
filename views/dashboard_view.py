from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QLabel, QStackedWidget, QFrame, QSpacerItem, QSizePolicy, QButtonGroup)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
import qtawesome as qta
from config import Config
from views.shared.theme_manager import theme_manager
from views.shared.styles import Styles
from views.patient import PatientView
from views.graphiques import GrapheView
from views.visite import VisiteView
from views.rendez_vous import RendezVousView
from views.consultation import ConsultationView
from views.examen import ExamenView
from views.chirurgie import ChirurgieView
from views.lunette import CommandeLunetteView
from views.produit import GestionProduitsView
from views.facturation import FacturePatientView
from views.prescription import PrescriptionView
from views.fournisseur import FournisseurView
from views.personnel import PersonnelView
from views.admin import AdminView
from views.settings.vue_parametre import ParametreView


class DashboardView(QWidget):
    def __init__(self, user_info,visite_ctrl):
        super().__init__()
        self.user_info = user_info
        self.visite_ctrl = visite_ctrl
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
        self.btn_stats = self.create_nav_btn("Statistiques", 'fa5s.chart-pie')
        self.btn_admin = self.create_nav_btn("Administration", 'fa5s.user-shield')
        self.btn_settings = self.create_nav_btn("Paramètres", 'fa5s.cogs')

        # AJOUT AU GROUPE (Une fois qu'ils sont créés)
        self.nav_group = QButtonGroup(self)
        for btn in [self.btn_patients, self.btn_visites, self.btn_rendez_vous, self.btn_consults, self.btn_examens,
                    self.btn_chirurgies, self.btn_lunettes, self.btn_panier,
                    self.btn_prescription, self.btn_facturation, self.btn_fournisseurs,
                    self.btn_personnel, self.btn_stats,     self.btn_admin, self.btn_settings]:
            self.nav_group.addButton(btn)
            sidebar_layout.addWidget(btn, 0, Qt.AlignCenter)
        self.nav_group.setExclusive(True)
        self.btn_stats.setChecked(True)

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

        # Header
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(50)
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(15, 5, 15, 5)
        self.lbl_page_title = QLabel("Tableau de Bord")
        self.lbl_page_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.lbl_user_name = QLabel(f"Bienvenue, {self.user_info.get('nom', 'Utilisateur')}")
        self.lbl_user_name.setStyleSheet("padding: 5px 15px; background: #eee; border-radius: 15px;")
        
        header_layout.addWidget(self.lbl_page_title)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_user_name)

        # --- STACKED WIDGET ---
        self.workspace_stack = QStackedWidget()
        
        # PAGES
        self.page_stats = GrapheView() 
        self.page_patients = PatientView() 
        self.page_visites = VisiteView(self.visite_ctrl)
        self.page_rendez_vous = RendezVousView(self.rendez_vous_ctrl)
        self.page_consultation = ConsultationView(self.consultation_ctrl)
        self.page_chirurgies = ChirurgieView(self.chirurgie_ctrl)
        self.page_examens = ExamenView(self.examen_ctrl)
        self.page_lunettes = CommandeLunetteView(self.commande_lunette_ctrl)
        self.page_prescription = PrescriptionView(self.prescription_ctrl)
        self.page_settings = ParametreView()
        # Import du contrôleur produit
        from controllers.controleur_produit import ProduitControleur
        self.produit_ctrl = ProduitControleur()
        self.page_gestion_panier = GestionProduitsView(self.produit_ctrl)

        # Facturation patient
        from controllers.controleur_facture_patient import FacturePatientControleur
        from controllers.controleur_panier_facture_patient import PanierFacturePatientControleur
        self.facture_patient_ctrl = FacturePatientControleur()
        self.panier_facture_patient_ctrl = PanierFacturePatientControleur()
        self.page_facturation = FacturePatientView(
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
        
        
        self.workspace_stack.addWidget(self.page_stats)    # Index 0
        self.workspace_stack.addWidget(self.page_patients) # Index 1
        self.workspace_stack.addWidget(self.page_visites)  # Index 2
        self.workspace_stack.addWidget(self.page_rendez_vous)  # Index 3
        self.workspace_stack.addWidget(self.page_consultation)  # Index 4
        self.workspace_stack.addWidget(self.page_examens)       # Index 5
        self.workspace_stack.addWidget(self.page_chirurgies)    # Index 6
        self.workspace_stack.addWidget(self.page_lunettes)      # Index 7
        self.workspace_stack.addWidget(self.page_gestion_panier)  # Index 8
        self.workspace_stack.addWidget(self.page_prescription)  # Index 9
        self.workspace_stack.addWidget(self.page_facturation)  # Index 10
        self.workspace_stack.addWidget(self.page_fournisseurs)  # Index 11
        self.workspace_stack.addWidget(self.page_personnel)  # Index 12
        self.workspace_stack.addWidget(self.page_admin)  # Index 13
        self.workspace_stack.addWidget(self.page_settings)  # Index 14

        self.content_layout.addWidget(self.header_frame)
        self.content_layout.addWidget(self.workspace_stack)

        self.layout.addWidget(self.sidebar_container)
        self.layout.addWidget(self.content_area)
        
        self.apply_theme()

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
        self.btn_stats.clicked.connect(self.show_home)
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
        self.btn_admin.clicked.connect(self.show_admin)
        self.btn_settings.clicked.connect(self.show_settings)
        self.btn_theme.clicked.connect(self.toggle_theme)
        
        # Connecter tous les boutons pour mettre à jour les indicateurs
        for btn in [self.btn_patients, self.btn_visites, self.btn_rendez_vous, self.btn_consults, self.btn_examens,
                    self.btn_chirurgies, self.btn_lunettes, self.btn_panier,
                    self.btn_prescription, self.btn_facturation, self.btn_fournisseurs,
                    self.btn_personnel, self.btn_admin, self.btn_stats, self.btn_logout, self.btn_settings]:
            btn.clicked.connect(self._update_nav_indicators)

    def _update_nav_indicators(self):
        """Met à jour les indicateurs de ligne pour tous les boutons."""
        pass

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
        for btn in [self.btn_patients, self.btn_visites, self.btn_rendez_vous, self.btn_consults, self.btn_examens,
                    self.btn_chirurgies, self.btn_lunettes, self.btn_panier,
                    self.btn_prescription, self.btn_facturation, self.btn_fournisseurs,
                    self.btn_personnel, self.btn_admin,
                    self.btn_stats, self.btn_logout, self.btn_settings]:
            
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
        self.header_frame.setStyleSheet(
            f"QFrame {{ background-color: transparent; border: none; }}"
        )
        self.lbl_page_title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {c['text_primary']};"
        )
        self.lbl_user_name.setStyleSheet(
            f"padding: 5px 15px; background: {c['bg_card']}; "
            f"border-radius: 15px; color: {c['text_primary']}; "
            f"border: 1px solid {c['border_light']};"
        )

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

    def show_home(self):
        self.lbl_page_title.setText("Statistiques Générales")
        self.workspace_stack.setCurrentIndex(0)

    def show_patients(self):
        self.lbl_page_title.setText("Gestion des Patients")
        self.workspace_stack.setCurrentIndex(1) 
        if hasattr(self.page_patients, 'load_all_data'):
            self.page_patients.load_all_data()
            
    def show_visites(self):
        self.lbl_page_title.setText("Gestion des Visites & Workflow")
        self.workspace_stack.setCurrentIndex(2)

    def show_rendez_vous(self):
        self.lbl_page_title.setText("Gestion des Rendez-vous")
        self.workspace_stack.setCurrentIndex(3)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_rendez_vous.charger_rendez_vous(code_session)
        
    def show_examen(self):
        self.lbl_page_title.setText("Gestion des Examens")
        self.workspace_stack.setCurrentIndex(5)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_examens.charger_examens(code_session)
    
    def show_chirurgie(self):
        self.lbl_page_title.setText("Gestion des Chirurgies")
        self.workspace_stack.setCurrentIndex(6)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_chirurgies.charger_chururgies(code_session)
            
    def show_prescription(self):
        self.lbl_page_title.setText("Gestion des Prescriptions")
        self.workspace_stack.setCurrentIndex(9)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_prescription.charger_donnees(code_session)

    def show_facturation(self):
        self.lbl_page_title.setText("Facturation Patient")
        self.workspace_stack.setCurrentIndex(10)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_facturation.charger_donnees(code_session)

    def show_fournisseurs(self):
        self.lbl_page_title.setText("Gestion des Fournisseurs")
        self.workspace_stack.setCurrentIndex(11)
        if hasattr(self.page_fournisseurs, "charger_fournisseurs"):
            actif, code_session = self.visite_ctrl.verifier_session_active()
            if actif:
                self.page_fournisseurs.charger_fournisseurs(code_session)
            else:
                self.page_fournisseurs.charger_fournisseurs()

    def show_personnel(self):
        self.lbl_page_title.setText("Gestion du Personnel")
        self.workspace_stack.setCurrentIndex(12)
        if hasattr(self.page_personnel, "charger_personnels"):
            self.page_personnel.charger_personnels()
    
    def show_admin(self):
        self.lbl_page_title.setText("Panneau d'Administration")
        self.workspace_stack.setCurrentIndex(13)
            
    def show_commande_lunette(self):
        self.lbl_page_title.setText("Gestion du service lunetation")
        self.workspace_stack.setCurrentIndex(7)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_lunettes.charger_commandes(code_session)
            
    def show_pharmacie(self):
        self.lbl_page_title.setText("Gestion Produits & Stock")
        self.workspace_stack.setCurrentIndex(8)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_gestion_panier.charger_donnees(code_session)
        
        
    def show_consultation(self):
        self.lbl_page_title.setText("Gestion des Consultations")
        self.workspace_stack.setCurrentIndex(4)
        actif, code_session = self.visite_ctrl.verifier_session_active()
        if actif:
            self.page_consultation.charger_consultations(code_session)

    # show_settings est appelé par le bouton "Paramètres" dans la sidebar
    def show_settings(self):
        self.lbl_page_title.setText("Paramètres de l'Application")
        self.workspace_stack.setCurrentIndex(14)