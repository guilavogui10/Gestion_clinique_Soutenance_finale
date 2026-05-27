from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QStackedWidget, QFrame, QButtonGroup, QMenu,
                             QProgressBar, QApplication)
from PySide6.QtCore import Qt, QSize, Signal, QTimer
import qtawesome as qta
from views.shared.theme_manager import theme_manager
from views.shared.styles import Styles
from views.shared.message_box import CustomMessageBox


class DashboardView(QWidget):
    logout_requested = Signal()

    def __init__(self, user_info, visite_ctrl, permission_ctrl=None):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.user_info = user_info
        self.visite_ctrl = visite_ctrl
        self.permission_ctrl = permission_ctrl

        self.code_utilisateur = user_info.get("code", "")
        self.role = user_info.get("role", "")
        self.est_responsable = bool(user_info.get("est_responsable", 0))

        # Cache lazy: {clé: widget} — rempli à la première navigation
        self._pages = {}
        # Cache lazy: {nom: controleur} — créé uniquement si la page est ouverte
        self._ctrls = {}

        # Animation de la barre de progression
        self._page_cible   = None   # page à afficher quand barre=100% ET données prêtes
        self._prog_valeur  = 0      # valeur courante 0→100
        self._data_prete   = False  # True quand SQL + factory sont terminés
        self._anim_timer   = QTimer(self)
        self._anim_timer.setSingleShot(False)
        self._anim_timer.timeout.connect(self._tick_animation)

        self.init_ui()
        self.setup_navigation()
        theme_manager.theme_changed.connect(self.apply_theme)

    # ═══════════════════════════════════════════════════════════════
    # LAZY CONTROLLERS — un contrôleur est créé une seule fois,
    # uniquement quand sa vue est demandée pour la première fois.
    # ═══════════════════════════════════════════════════════════════

    def _ctrl(self, nom: str):
        if nom not in self._ctrls:
            if nom == "patient":
                from controllers.controleur_patient import ControleurPatient
                self._ctrls[nom] = ControleurPatient()
            elif nom == "rendez_vous":
                from controllers.controleur_rendez_vous import RendezVousControleur
                self._ctrls[nom] = RendezVousControleur()
            elif nom == "examen":
                from controllers.controleur_examen import ExamenControleur
                self._ctrls[nom] = ExamenControleur()
            elif nom == "consultation":
                from controllers.controleur_consultation import ConsultationControleur
                self._ctrls[nom] = ConsultationControleur()
            elif nom == "chirurgie":
                from controllers.controleur_chururgie import ChirurgieControleur
                self._ctrls[nom] = ChirurgieControleur()
            elif nom == "lunette":
                from controllers.controleur_lunette import CommandeLunetteControleur
                self._ctrls[nom] = CommandeLunetteControleur()
            elif nom == "prescription":
                from controllers.controleur_prescription import PrescriptionControleur
                self._ctrls[nom] = PrescriptionControleur()
            elif nom == "produit":
                from controllers.controleur_produit import ProduitControleur
                self._ctrls[nom] = ProduitControleur()
            elif nom == "facture_patient":
                from controllers.controleur_facture_patient import FacturePatientControleur
                self._ctrls[nom] = FacturePatientControleur()
            elif nom == "panier_facture_patient":
                from controllers.controleur_panier_facture_patient import PanierFacturePatientControleur
                self._ctrls[nom] = PanierFacturePatientControleur()
            elif nom == "fournisseur":
                from controllers.controleur_fournisseur import FournisseurControleur
                self._ctrls[nom] = FournisseurControleur()
            elif nom == "personnel":
                from controllers.controleur_personnel import ControllerPersonnel
                self._ctrls[nom] = ControllerPersonnel()
            elif nom == "acte_medical":
                from controllers.controleur_acte_medicale import ActeMedicalControleur
                self._ctrls[nom] = ActeMedicalControleur()
            elif nom == "resultat":
                from controllers.controleur_resultat_medical import ResultatMedicalControleur
                self._ctrls[nom] = ResultatMedicalControleur()
        return self._ctrls[nom]

    # ═══════════════════════════════════════════════════════════════
    # LAZY PAGES — moteur central du lazy loading.
    # La vue n'est instanciée qu'au premier clic sur le bouton nav.
    # ═══════════════════════════════════════════════════════════════

    def _page(self, cle: str, factory):
        """Retourne la page du cache ou l'instancie via factory (1 seule fois)."""
        if cle not in self._pages:
            widget = factory()
            self._pages[cle] = widget
            self.workspace_stack.addWidget(widget)
            if hasattr(widget, 'apply_theme'):
                try:
                    widget.apply_theme()
                except Exception:
                    pass
        return self._pages[cle]

    # — Factories (import + instanciation déplacés ici) —

    def _factory_accueil(self):
        from views.home import AccueilView
        page = AccueilView()
        page.navigate_to.connect(self._handle_accueil_navigation)
        return page

    def _factory_patients(self):
        from views.patient import VuePatient
        return VuePatient(self._ctrl("patient"))

    def _factory_visites(self):
        from views.visite import VisiteView
        return VisiteView(self.visite_ctrl)

    def _factory_rendez_vous(self):
        from views.rendez_vous import RendezVousView
        return RendezVousView(self._ctrl("rendez_vous"))

    def _factory_consultation(self):
        from views.consultation import ConsultationView
        return ConsultationView(self._ctrl("consultation"), self.permission_ctrl, self.user_info)

    def _factory_examens(self):
        from views.examen import ExamenView
        return ExamenView(self._ctrl("examen"), self.permission_ctrl, self.user_info)

    def _factory_chirurgies(self):
        from views.chirurgie import ChirurgieView
        return ChirurgieView(self._ctrl("chirurgie"), self.permission_ctrl, self.user_info)

    def _factory_lunettes(self):
        from views.lunette import CommandeLunetteView
        return CommandeLunetteView(self._ctrl("lunette"))

    def _factory_pharmacie(self):
        from views.produit import GestionProduitsView
        return GestionProduitsView(self._ctrl("produit"))

    def _factory_prescription(self):
        from views.prescription import PrescriptionView
        return PrescriptionView(self._ctrl("prescription"), self.permission_ctrl, self.user_info)

    def _factory_facturation(self):
        from views.facturation import FacturationView
        return FacturationView(self._ctrl("facture_patient"), self._ctrl("panier_facture_patient"))

    def _factory_fournisseurs(self):
        from views.fournisseur import FournisseurView
        return FournisseurView(self._ctrl("fournisseur"))

    def _factory_personnel(self):
        from views.personnel import PersonnelView
        return PersonnelView(self._ctrl("personnel"))

    def _factory_admin(self):
        from views.admin import AdminView
        return AdminView(self.visite_ctrl)

    def _factory_settings(self):
        from views.settings.vue_parametre import ParametreView
        return ParametreView()

    def _factory_actes(self):
        from views.acte_medical import VueActeMedical
        return VueActeMedical(self._ctrl("acte_medical"))

    def _factory_resultats(self):
        from views.resultat_medical.vue_resultat_medical import VueResultatMedical
        return VueResultatMedical(self._ctrl("resultat"), self.permission_ctrl, self.user_info)

    # ═══════════════════════════════════════════════════════════════
    # INIT UI
    # ═══════════════════════════════════════════════════════════════

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

        self.logo_icon = QLabel()
        self.logo_icon.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.logo_icon)

        self.btn_theme = QPushButton()
        self.btn_theme.setFixedSize(76, 40)
        sidebar_layout.addWidget(self.btn_theme, 0, Qt.AlignCenter)
        sidebar_layout.addSpacing(4)

        self.btn_accueil = self.create_nav_btn("Accueil", 'fa5s.home')
        self.btn_patients = self.create_nav_btn("Patients", 'fa5s.user-injured')
        self.btn_rendez_vous = self.create_nav_btn("Rendez-vous", 'fa5s.calendar-check')
        self.btn_consults = self.create_nav_btn("Consultations", 'fa5s.stethoscope')
        self.btn_visites = self.create_nav_btn("visite", 'fa5s.walking')
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

        self.nav_group = QButtonGroup(self)
        for btn in [self.btn_accueil, self.btn_patients, self.btn_visites, self.btn_rendez_vous,
                    self.btn_consults, self.btn_examens, self.btn_chirurgies, self.btn_lunettes,
                    self.btn_panier, self.btn_prescription, self.btn_facturation,
                    self.btn_fournisseurs, self.btn_personnel, self.btn_actes, self.btn_resultats,
                    self.btn_admin, self.btn_settings]:
            self.nav_group.addButton(btn)
            sidebar_layout.addWidget(btn, 0, Qt.AlignCenter)
        self.nav_group.setExclusive(True)
        self.btn_accueil.setChecked(True)

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

        self.sidebar_scroll.setWidget(self.sidebar)
        container_layout.addWidget(self.sidebar_scroll)

        # 2. CONTENT AREA
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(70)
        self.header_frame.setObjectName("main_header")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(20)

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

        self.lbl_app_name = QLabel("CSOM")
        self.lbl_app_name.setObjectName("app_name")
        logo_text_layout.addWidget(self.lbl_app_name)

        self.lbl_app_subtitle = QLabel("Clinique Ophtalmologique")
        self.lbl_app_subtitle.setObjectName("app_subtitle")
        logo_text_layout.addWidget(self.lbl_app_subtitle)

        logo_layout.addWidget(logo_text_container)
        header_layout.addWidget(logo_container)
        header_layout.addSpacing(30)

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

        # ── BARRE DE CHARGEMENT DÉTERMINÉE (0 → 100%) ──────────────
        # Cachée par défaut, affichée lors de chaque navigation.
        # La page cible ne s'affiche qu'après que la barre atteint 100%.
        self.loading_bar_container = QWidget()
        self.loading_bar_container.setFixedHeight(80)
        self.loading_bar_container.setVisible(False)
        self.loading_bar_container.setStyleSheet(
            "background-color: #EFF6FF; border-bottom: 2px solid #93C5FD;"
        )
        lbc_layout = QVBoxLayout(self.loading_bar_container)
        lbc_layout.setContentsMargins(30, 12, 30, 12)
        lbc_layout.setSpacing(8)

        # Ligne texte + pourcentage
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        self.loading_label = QLabel("Chargement...")
        self.loading_label.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #1D4ED8; "
            "background: transparent; border: none;"
        )
        self.loading_pct = QLabel("0 %")
        self.loading_pct.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #1D4ED8; "
            "background: transparent; border: none;"
        )
        top_row.addWidget(self.loading_label)
        top_row.addStretch()
        top_row.addWidget(self.loading_pct)
        lbc_layout.addLayout(top_row)

        # Barre de progression DÉTERMINÉE — agrandie
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 100)
        self.loading_bar.setValue(0)
        self.loading_bar.setFixedHeight(16)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setStyleSheet("""
            QProgressBar {
                background-color: #BFDBFE;
                border: none;
                border-radius: 8px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563EB, stop:1 #60A5FA
                );
                border-radius: 8px;
            }
        """)
        lbc_layout.addWidget(self.loading_bar)

        # STACK — vide au démarrage, peuplé en lazy loading
        self.workspace_stack = QStackedWidget()

        # Seule la page d'accueil est chargée immédiatement (visible au login)
        accueil = self._page("accueil", self._factory_accueil)
        self.workspace_stack.setCurrentWidget(accueil)

        self.content_layout.addWidget(self.header_frame)
        self.content_layout.addWidget(self.loading_bar_container)
        self.content_layout.addWidget(self.workspace_stack)

        self.layout.addWidget(self.sidebar_container)
        self.layout.addWidget(self.content_area)

        self.apply_theme()

    # ═══════════════════════════════════════════════════════════════
    # MOTEUR DE CHARGEMENT — style « site web »
    #
    # Phase 1 — INDÉTERMINÉE : barre pulse (Qt gère l'animation)
    #   pendant que factory() + charger_fn() s'exécutent.
    #   Si le thread principal est brièvement bloqué, la barre
    #   s'arrête puis reprend — comportement attendu, moins agressif
    #   qu'une barre déterminée bloquée à 2 %.
    #
    # Phase 2 — COMPLÉTION RAPIDE : dès la fin du chargement, la
    #   barre passe en mode déterminé et file vers 100 % en ~300 ms,
    #   puis la page s'affiche et la barre disparaît.
    # ═══════════════════════════════════════════════════════════════

    # 100 paliers × 30 ms = 3 000 ms d'animation totale
    _ANIM_INTERVAL_MS = 30

    def _naviguer(self, cle: str, factory, nom: str, charger_fn=None):
        """Lance la barre puis déclenche le chargement réel après 80 ms."""
        # Arrêter toute animation précédente
        self._anim_timer.stop()

        # Réinitialiser l'état
        self._prog_valeur = 0
        self._data_prete  = False
        self._page_cible  = None

        # Afficher la barre à 0 % IMMÉDIATEMENT
        self.loading_label.setText(f"Chargement de {nom}...")
        self.loading_pct.setText("0 %")
        self.loading_bar.setValue(0)
        self.loading_bar_container.setVisible(True)
        QApplication.processEvents()   # force le rendu → barre visible dès le clic

        # Démarrer l'animation de la barre
        self._anim_timer.start(self._ANIM_INTERVAL_MS)

        # Déclencher le chargement réel après 80 ms (2-3 ticks)
        # → la barre a déjà rendu quelques % avant que le SQL ne bloque
        QTimer.singleShot(80, lambda: self._executer_chargement(cle, factory, charger_fn))

    def _executer_chargement(self, cle: str, factory, charger_fn):
        """Crée la page + charge les données SQL (peut bloquer brièvement)."""
        try:
            page = self._page(cle, factory)
            if charger_fn:
                charger_fn(page)
            self._page_cible = page
        except Exception:
            pass
        finally:
            self._data_prete = True
            # Si la barre est déjà à 100 %, afficher la page maintenant
            if self._prog_valeur >= 100:
                self._finaliser_navigation()

    def _tick_animation(self):
        """Incrémente la barre toutes les 30 ms.
        À 100 % : affiche la page si données prêtes, sinon attend."""
        self._prog_valeur += 1
        self.loading_bar.setValue(self._prog_valeur)
        self.loading_pct.setText(f"{self._prog_valeur} %")

        if self._prog_valeur >= 100:
            self._anim_timer.stop()
            if self._data_prete:
                self._finaliser_navigation()
            # Sinon : barre reste à 100 %, on attend _executer_chargement()

    def _finaliser_navigation(self):
        """Cache la barre et révèle la page — appelé quand barre=100% ET données prêtes."""
        self.loading_bar_container.setVisible(False)
        if self._page_cible is not None:
            self.workspace_stack.setCurrentWidget(self._page_cible)
            self._page_cible = None

    # ═══════════════════════════════════════════════════════════════
    # HELPERS UI
    # ═══════════════════════════════════════════════════════════════

    def create_header_nav_btn(self, text, icon_name):
        btn = QPushButton()
        btn.setFixedHeight(40)
        btn.setMinimumWidth(120)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setObjectName("header_nav_btn")
        btn.setProperty("nav_text", text)
        btn.setProperty("nav_icon", icon_name)

        layout = QHBoxLayout(btn)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        icon_label = QLabel()
        icon_label.setObjectName("nav_icon_label")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(16, 16)
        layout.addWidget(icon_label)

        text_label = QLabel(text)
        text_label.setObjectName("nav_text_label")
        text_label.setWordWrap(False)
        layout.addWidget(text_label)

        return btn

    def create_nav_btn(self, text, icon_name):
        c = theme_manager.colors()
        btn = QPushButton()
        btn.setProperty("icon_name", icon_name)
        btn.setProperty("text_label", text)
        btn.setCheckable(True)
        btn.setFixedSize(76, 56)
        btn.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(btn)
        layout.setContentsMargins(5, 6, 5, 6)
        layout.setSpacing(4)

        label_text = QLabel(text)
        label_text.setAlignment(Qt.AlignCenter)
        label_text.setWordWrap(True)
        label_text.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 9px; font-weight: 600; "
            "border: none; background: transparent;"
        )
        label_text.setObjectName("btn_text_label")

        label_icon = QLabel()
        label_icon.setPixmap(qta.icon(icon_name, color=c['primary']).pixmap(QSize(24, 24)))
        label_icon.setAlignment(Qt.AlignCenter)
        label_icon.setStyleSheet("border: none; background: transparent;")
        label_icon.setObjectName("btn_icon_label")

        layout.addWidget(label_text)
        layout.addWidget(label_icon)
        layout.addStretch()

        return btn

    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════

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
        self.btn_logout.clicked.connect(self._confirmer_deconnexion)

        self.btn_nav_accueil.clicked.connect(self.show_home)
        self.btn_nav_apropos.clicked.connect(self.show_settings)
        self.btn_nav_services.clicked.connect(self._show_header_services_menu)
        self.btn_nav_equipe.clicked.connect(self.show_personnel)
        self.btn_nav_rdv.clicked.connect(self.show_rendez_vous)
        self.btn_nav_contact.clicked.connect(self.show_settings)

        for btn in [self.btn_accueil, self.btn_patients, self.btn_visites, self.btn_rendez_vous,
                    self.btn_consults, self.btn_examens, self.btn_chirurgies, self.btn_lunettes,
                    self.btn_panier, self.btn_prescription, self.btn_facturation,
                    self.btn_fournisseurs, self.btn_personnel, self.btn_actes, self.btn_resultats,
                    self.btn_admin, self.btn_logout, self.btn_settings]:
            btn.clicked.connect(self._update_nav_indicators)

    def _update_nav_indicators(self):
        pass

    def _show_header_services_menu(self):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setObjectName("header_services_menu")

        services = [
            ('fa5s.stethoscope', 'Consultation', '#3B82F6', self.show_consultation),
            ('fa5s.microscope', 'Examens', '#10B981', self.show_examen),
            ('fa5s.procedures', 'Chirurgie', '#8B5CF6', self.show_chirurgie),
            ('fa5s.glasses', 'Lunettes', '#F59E0B', self.show_commande_lunette),
            ('fa5s.pills', 'Pharmacie', '#EF4444', self.show_pharmacie),
            ('fa5s.calendar-check', 'Rendez-vous', '#06B6D4', self.show_rendez_vous),
        ]

        for icon_name, service_name, color, nav_method in services:
            action = menu.addAction(qta.icon(icon_name, color=color), f"  {service_name}")
            action.triggered.connect(nav_method)

        menu.setStyleSheet("""
            QMenu { background-color: white; border: 1px solid #E5E7EB; border-radius: 8px; padding: 8px 0; }
            QMenu::item { padding: 10px 20px; color: #1F2937; font-size: 13px; font-weight: 500; }
            QMenu::item:selected { background-color: #EFF6FF; color: #3B82F6; }
            QMenu::icon { padding-left: 10px; }
        """)
        menu.exec(self.btn_nav_services.mapToGlobal(self.btn_nav_services.rect().bottomLeft()))

    def _show_login_menu(self):
        menu = QMenu(self)
        menu.setObjectName("login_menu")

        action_logout = menu.addAction(qta.icon('fa5s.sign-out-alt', color='#EF4444'), "  Déconnexion")
        action_logout.triggered.connect(self._confirmer_deconnexion)

        action_create = menu.addAction(qta.icon('fa5s.user-plus', color='#3B82F6'), "  Créer compte")
        action_create.triggered.connect(self._creer_compte)

        menu.setStyleSheet("""
            QMenu { background-color: white; border: 1px solid #E5E7EB; border-radius: 8px; padding: 8px 0; }
            QMenu::item { padding: 10px 20px; color: #1F2937; font-size: 13px; font-weight: 500; }
            QMenu::item:selected { background-color: #EFF6FF; color: #3B82F6; }
            QMenu::icon { padding-left: 10px; }
        """)
        menu.exec(self.btn_login.mapToGlobal(self.btn_login.rect().bottomLeft()))

    def _confirmer_deconnexion(self):
        reponse = CustomMessageBox.confirm(
            self,
            "Confirmation de déconnexion",
            "Voulez-vous vraiment vous déconnecter ?"
        )
        if reponse:
            self.logout_requested.emit()

    def _creer_compte(self):
        self.show_admin()

    # ═══════════════════════════════════════════════════════════════
    # THEME
    # ═══════════════════════════════════════════════════════════════

    def toggle_theme(self):
        theme_manager.next_theme()

    def apply_theme(self):
        c = theme_manager.colors()

        self.logo_icon.setPixmap(qta.icon('fa5s.eye', color=c['primary']).pixmap(QSize(50, 50)))

        self.sidebar_container.setStyleSheet(f"""
            QFrame#sidebar_container {{
                background-color: {c['bg_card']};
                border-radius: 15px;
                border: 1px solid {c['border']};
            }}
        """)

        self.sidebar_scroll.setStyleSheet(f"""
            QScrollArea {{ background-color: transparent; border: none; }}
            QScrollBar:vertical {{ background: transparent; width: 6px; border-radius: 3px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: {c['border_light']}; border-radius: 3px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background: {c['primary']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        """)

        self.sidebar.setStyleSheet("QFrame#main_sidebar { background-color: transparent; border: none; }")

        next_icon = theme_manager.next_theme_icon()
        self.btn_theme.setText("")
        self.btn_theme.setIcon(qta.icon(next_icon, color=c['primary']))
        self.btn_theme.setIconSize(QSize(24, 24))
        self.btn_theme.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: none; border-radius: 10px; }}
            QPushButton:hover {{ background-color: {c['hover']}; }}
        """)

        for btn in [self.btn_accueil, self.btn_patients, self.btn_visites, self.btn_rendez_vous,
                    self.btn_consults, self.btn_examens, self.btn_chirurgies, self.btn_lunettes,
                    self.btn_panier, self.btn_prescription, self.btn_facturation,
                    self.btn_fournisseurs, self.btn_personnel, self.btn_actes, self.btn_resultats,
                    self.btn_admin, self.btn_logout, self.btn_settings]:
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: transparent; border: none; border-radius: 4px; }}
                QPushButton:checked {{ background-color: {c['hover']}; border-left: 3px solid {c['primary']}; }}
                QPushButton:hover {{ background-color: {c['hover']}; }}
                QPushButton QLabel {{ color: {c['text_primary']}; background: transparent; border: none; }}
            """)

            icon_label = btn.findChild(QLabel, "btn_icon_label")
            if icon_label:
                icon_label.setPixmap(
                    qta.icon(btn.property("icon_name") or 'fa5s.circle', color=c['primary']).pixmap(QSize(24, 24))
                )

            text_label = btn.findChild(QLabel, "btn_text_label")
            if text_label:
                text_label.setStyleSheet(
                    f"color: {c['text_primary']}; font-size: 9px; font-weight: 600; "
                    "border: none; background: transparent;"
                )

        self.content_area.setStyleSheet(Styles.content_area())

        self.header_frame.setStyleSheet(f"""
            QFrame#main_header {{ background-color: white; border: none; border-bottom: 1px solid #E5E7EB; }}
            QWidget#logo_container, QWidget#logo_text_container,
            QWidget#nav_container, QWidget#login_container {{ background-color: transparent; border: none; }}
            QLabel#logo_icon_header {{ background-color: transparent; border: none; }}
        """)

        self.logo_icon_header.setPixmap(qta.icon('fa5s.eye', color='#3B82F6').pixmap(QSize(50, 50)))
        self.lbl_app_name.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #1F2937; background: transparent; border: none; "
            "font-family: 'Yu Gothic UI', 'Segoe UI', Arial, sans-serif;"
        )
        self.lbl_app_subtitle.setStyleSheet(
            "font-size: 11px; color: #6B7280; background: transparent; border: none; "
            "font-family: 'Yu Gothic UI', 'Segoe UI', Arial, sans-serif;"
        )

        for btn in [self.btn_nav_accueil, self.btn_nav_apropos, self.btn_nav_services,
                    self.btn_nav_equipe, self.btn_nav_rdv, self.btn_nav_contact]:
            btn.setStyleSheet(f"""
                QPushButton#header_nav_btn {{ background-color: transparent; border: none; border-radius: 6px; padding: 8px 12px; }}
                QPushButton#header_nav_btn:hover {{ background-color: transparent; }}
                QLabel#nav_text_label {{ color: #6B7280; font-size: 14px; font-weight: 700; background: transparent; border: none; font-family: 'Yu Gothic UI', 'Segoe UI', Arial, sans-serif; }}
                QPushButton#header_nav_btn:hover QLabel#nav_text_label {{ color: #3B82F6; }}
                QLabel#nav_icon_label {{ background: transparent; border: none; }}
            """)
            icon_label = btn.findChild(QLabel, "nav_icon_label")
            if icon_label:
                icon_label.setPixmap(
                    qta.icon(btn.property("nav_icon"), color='#3B82F6').pixmap(QSize(16, 16))
                )

        self.btn_login.setStyleSheet("""
            QPushButton#btn_login { background-color: #3B82F6; color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; padding: 0 20px; }
            QPushButton#btn_login:hover { background-color: #2563EB; }
        """)

        self.footer_frame.setStyleSheet(Styles.footer())
        self.lbl_version.setStyleSheet(f"font-size: 8px; color: {c['text_muted']};")

        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet(Styles.global_qss())

        # Propager uniquement aux pages déjà chargées (lazy)
        for page in self._pages.values():
            if hasattr(page, 'apply_theme'):
                try:
                    page.apply_theme()
                except Exception:
                    pass

    # ═══════════════════════════════════════════════════════════════
    # CONTRÔLE D'ACCÈS
    # ═══════════════════════════════════════════════════════════════

    def _verifier_acces_interface(self, nom_interface: str) -> bool:
        if not self.permission_ctrl:
            return True
        if self.role in ["Directeur Général", "Administrateur"]:
            return True
        if not self.permission_ctrl.peut_acceder_interface(self.role, nom_interface):
            CustomMessageBox.warning(
                self,
                "Accès refusé",
                f"Votre rôle '{self.role}' ne vous permet pas d'accéder à l'interface '{nom_interface}'."
            )
            return False
        return True

    # ═══════════════════════════════════════════════════════════════
    # MÉTHODES DE NAVIGATION — chaque show_xxx() charge la page
    # en lazy loading au premier appel, puis navigue vers elle.
    # ═══════════════════════════════════════════════════════════════

    def show_home(self):
        # Accueil sans barre (toujours déjà chargé)
        page = self._page("accueil", self._factory_accueil)
        self.workspace_stack.setCurrentWidget(page)

    def _handle_accueil_navigation(self, page_name: str):
        navigation_map = {
            "Rendez-vous": self.show_rendez_vous,
            "Consultations": self.show_consultation,
            "Examens": self.show_examen,
            "Chirurgies": self.show_chirurgie,
            "Lunettes": self.show_commande_lunette,
            "Pharmacie": self.show_pharmacie,
        }
        nav_method = navigation_map.get(page_name)
        if nav_method:
            nav_method()

    def show_patients(self):
        if not self._verifier_acces_interface("Patients"):
            return
        def _charger(p):
            if hasattr(p, 'charger_donnees'):
                p.charger_donnees()
        self._naviguer("patients", self._factory_patients, "Patients", _charger)

    def show_visites(self):
        if not self._verifier_acces_interface("Visites"):
            return
        self._naviguer("visites", self._factory_visites, "Visites")

    def show_rendez_vous(self):
        if not self._verifier_acces_interface("Rendez-vous"):
            return
        def _charger(p):
            actif, code_session = self.visite_ctrl.verifier_session_active()
            if actif:
                p.charger_rendez_vous(code_session)
        self._naviguer("rendez_vous", self._factory_rendez_vous, "Rendez-vous", _charger)

    def show_examen(self):
        if not self._verifier_acces_interface("Examens"):
            return
        def _charger(p):
            actif, code_session = self.visite_ctrl.verifier_session_active()
            if actif:
                p.charger_examens(code_session)
        self._naviguer("examens", self._factory_examens, "Examens", _charger)

    def show_chirurgie(self):
        if not self._verifier_acces_interface("Chirurgies"):
            return
        def _charger(p):
            actif, code_session = self.visite_ctrl.verifier_session_active()
            if actif:
                p.charger_chururgies(code_session)
        self._naviguer("chirurgies", self._factory_chirurgies, "Chirurgies", _charger)

    def show_prescription(self):
        if not self._verifier_acces_interface("Prescriptions"):
            return
        def _charger(p):
            actif, code_session = self.visite_ctrl.verifier_session_active()
            if actif:
                p.charger_donnees(code_session)
        self._naviguer("prescription", self._factory_prescription, "Prescriptions", _charger)

    def show_facturation(self):
        if not self._verifier_acces_interface("Facturation"):
            return
        def _charger(p):
            actif, code_session = self.visite_ctrl.verifier_session_active()
            if actif:
                p.charger_donnees(code_session)
        self._naviguer("facturation", self._factory_facturation, "Facturation", _charger)

    def show_fournisseurs(self):
        if not self._verifier_acces_interface("Fournisseurs"):
            return
        def _charger(p):
            if hasattr(p, "charger_fournisseurs"):
                actif, code_session = self.visite_ctrl.verifier_session_active()
                if actif:
                    p.charger_fournisseurs(code_session)
                else:
                    p.charger_fournisseurs()
        self._naviguer("fournisseurs", self._factory_fournisseurs, "Fournisseurs", _charger)

    def show_personnel(self):
        if not self._verifier_acces_interface("Personnel"):
            return
        def _charger(p):
            if hasattr(p, "charger_personnels"):
                p.charger_personnels()
        self._naviguer("personnel", self._factory_personnel, "Personnel", _charger)

    def show_admin(self):
        self._naviguer("admin", self._factory_admin, "Administration")

    def show_commande_lunette(self):
        if not self._verifier_acces_interface("Lunettes"):
            return
        def _charger(p):
            actif, code_session = self.visite_ctrl.verifier_session_active()
            if actif:
                p.charger_commandes(code_session)
        self._naviguer("lunettes", self._factory_lunettes, "Lunettes", _charger)

    def show_pharmacie(self):
        if not self._verifier_acces_interface("Pharmacie"):
            return
        def _charger(p):
            actif, code_session = self.visite_ctrl.verifier_session_active()
            if actif:
                p.charger_donnees(code_session)
        self._naviguer("pharmacie", self._factory_pharmacie, "Pharmacie", _charger)

    def show_consultation(self):
        if not self._verifier_acces_interface("Consultations"):
            return
        def _charger(p):
            actif, code_session = self.visite_ctrl.verifier_session_active()
            if actif:
                p.charger_consultations(code_session)
        self._naviguer("consultation", self._factory_consultation, "Consultations", _charger)

    def show_settings(self):
        self._naviguer("settings", self._factory_settings, "Paramètres")

    def show_actes(self):
        def _charger(p):
            if hasattr(p, "load_data"):
                p.load_data()
                p._update_file_attente()
        self._naviguer("actes", self._factory_actes, "Actes médicaux", _charger)

    def show_resultats(self):
        self._naviguer(
            "resultats", self._factory_resultats, "Résultats médicaux",
            lambda p: p.load_data() if hasattr(p, "load_data") else None
        )

    # ═══════════════════════════════════════════════════════════════
    # PROPRIÉTÉS D'ACCÈS DIRECT AUX PAGES (lazy)
    # Permettent aux vues d'accéder aux pages sans navigation animée.
    # ═══════════════════════════════════════════════════════════════

    @property
    def page_actes(self):
        return self._page("actes", self._factory_actes)

    @property
    def page_resultats(self):
        return self._page("resultats", self._factory_resultats)
