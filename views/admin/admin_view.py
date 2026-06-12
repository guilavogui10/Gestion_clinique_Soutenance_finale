import qtawesome as qta
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QLabel, QGraphicsDropShadowEffect, QStackedWidget, QMenu
)
from views.shared.theme_manager import theme_manager


class AdminView(QWidget):
    """
    Interface principale d'administration de la clinique.
    Design moderne inspiré de l'interface financière avec navigation gauche et haute.
    """

    def __init__(self, visite_ctrl, charger_avec_barre=None):
        super().__init__()
        self.visite_ctrl        = visite_ctrl
        self.charger_avec_barre = charger_avec_barre
        self.current_view       = None
        self.code_session       = None
        self._init_controleurs()
        self._init_ui()
        self._connecter_boutons()
        self._charger_session_active()
        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # INITIALISATION
    # =========================================================================

    def _init_controleurs(self):
        """Initialise les contrôleurs nécessaires."""
        from controllers.controleur_consultation import ConsultationControleur
        from controllers.controleur_examen import ExamenControleur
        from controllers.controleur_lunette import CommandeLunetteControleur
        from controllers.controleur_chururgie import ChirurgieControleur
        from controllers.controleur_rendez_vous import RendezVousControleur
        from controllers.controleur_panierFourni import PanierFactureFourniControleur
        from controllers.controleur_panier_facture_patient import PanierFacturePatientControleur
        self.consultation_ctrl = ConsultationControleur()
        self.examen_ctrl = ExamenControleur()
        self.lunette_ctrl = CommandeLunetteControleur()
        self.chirurgie_ctrl = ChirurgieControleur()
        self.rendez_vous_ctrl = RendezVousControleur()
        self.stock_ctrl = PanierFactureFourniControleur()
        self.vente_ctrl = PanierFacturePatientControleur()
        # Contrôleur de visites (déjà passé en param mais on en garde une ref)
        self._visite_ctrl_ref = self.visite_ctrl
    
    def _charger_session_active(self):
        """Charge le code de la session active et rafraîchit le dashboard."""
        try:
            actif, code_session = self.visite_ctrl.verifier_session_active()
            if actif:
                self.code_session = code_session
        except Exception as e:
            print(f"[AdminView] Erreur chargement session: {e}")
            self.code_session = None

        # Le chargement des stats se fait via _avec_chargement (barre de progression)
        if self.code_session:
            def _charger_dashboard():
                if hasattr(self, '_stats_tab_widget'):
                    self._stats_tab_widget.charger_donnees(self.code_session)
                if hasattr(self, '_graphes_tab_widget'):
                    self._graphes_tab_widget.charger_donnees(self.code_session)
            self._avec_chargement("Administration — Tableau de bord", _charger_dashboard)
    
    def _connecter_boutons(self):
        """Connecte les boutons aux méthodes d'affichage."""
        self.btn_dashboard.clicked.connect(self.afficher_dashboard)
        self.btn_consultation_main.clicked.connect(self._afficher_menu_consultation)
        self.action_graphes.triggered.connect(self.afficher_analyse_consultation)
        self.action_tableau.triggered.connect(self.afficher_table_consultation)
        self.btn_examen_main.clicked.connect(self._afficher_fonctionnalite_a_venir)
        self.btn_chirurgie_main.clicked.connect(self._afficher_fonctionnalite_a_venir)
        self.btn_lunette_main.clicked.connect(self._afficher_fonctionnalite_a_venir)
        self.btn_rendez_vous.clicked.connect(self._afficher_fonctionnalite_a_venir)
        self.btn_stock.clicked.connect(self._afficher_fonctionnalite_a_venir)
        self.btn_vente.clicked.connect(self._afficher_fonctionnalite_a_venir)
        self.btn_parametre.clicked.connect(self._afficher_parametre)


    
    # =========================================================================
    # MÉTHODES D'AFFICHAGE DES ANALYSES
    # =========================================================================
    
    # -------------------------------------------------------------------------
    # HELPER : exécute fn() avec la barre de progression du dashboard
    # -------------------------------------------------------------------------

    def _avec_chargement(self, nom: str, fn):
        """Lance fn() avec la barre de progression si disponible, sinon directement."""
        if self.charger_avec_barre:
            self.charger_avec_barre(nom, fn)
        else:
            fn()

    def _creer_ou_rafraichir(self, attr_page: str, attr_index: str, factory, charger_fn=None):
        """Crée la page si absente, sinon la rafraîchit, puis l'affiche."""
        if not hasattr(self, attr_page):
            page = factory()
            setattr(self, attr_page, page)
            self.stacked_widget.addWidget(page)
            setattr(self, attr_index, self.stacked_widget.count() - 1)
            if charger_fn:
                charger_fn(page)
        else:
            page = getattr(self, attr_page)
            if charger_fn:
                charger_fn(page)
            elif hasattr(page, 'rafraichir'):
                page.rafraichir()
        self.stacked_widget.setCurrentIndex(getattr(self, attr_index))

    # -------------------------------------------------------------------------
    # NAVIGATION INTERNE
    # -------------------------------------------------------------------------

    def _afficher_menu_consultation(self):
        pos = self.btn_consultation_main.mapToGlobal(self.btn_consultation_main.rect().topRight())
        self.consultation_menu.exec(pos)

    def _afficher_fonctionnalite_a_venir(self):
        """Affiche un modal pour indiquer que la fonctionnalité est à venir."""
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Fonctionnalité à venir")
        msg.setText("Cette fonctionnalité sera disponible prochainement.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def afficher_dashboard(self):
        self.stacked_widget.setCurrentIndex(0)
        if self.code_session:
            def _refresh():
                if hasattr(self, '_stats_tab_widget'):
                    self._stats_tab_widget.charger_donnees(self.code_session)
                if hasattr(self, '_graphes_tab_widget'):
                    self._graphes_tab_widget.charger_donnees(self.code_session)
            self._avec_chargement("Administration — Tableau de bord", _refresh)

    # -------------------------------------------------------------------------
    # ANALYSES (graphes)
    # -------------------------------------------------------------------------

    def afficher_analyse_consultation(self):
        if not self.code_session:
            return
        def _fn():
            from views.analyses.analyse_consultation import AnalyseConsultationView
            est_nouveau = not hasattr(self, 'page_consultation')
            def _charger(p):
                if est_nouveau:
                    p.charger_donnees()
                else:
                    p.rafraichir()
            self._creer_ou_rafraichir(
                'page_consultation', 'consultation_index',
                lambda: AnalyseConsultationView(self.consultation_ctrl, self.code_session),
                _charger
            )
        self._avec_chargement("Consultation — Analyses", _fn)

    # -------------------------------------------------------------------------
    # TABLEAUX (liste + recherche)
    # -------------------------------------------------------------------------

    def afficher_table_consultation(self):
        if not self.code_session:
            return
        def _fn():
            from views.analyses.tableau_consultation import TableauConsultationAdminView
            def _charger(p): p.charger_consultations(self.code_session)
            self._creer_ou_rafraichir(
                'page_tableau_consultation', 'tableau_consultation_index',
                lambda: TableauConsultationAdminView(self.consultation_ctrl, self.code_session),
                _charger
            )
        self._avec_chargement("Consultation — Tableau", _fn)

    # -------------------------------------------------------------------------
    # PARAMÈTRES (session selector)
    # -------------------------------------------------------------------------

    def _afficher_parametre(self):
        """Ouvre la vue Paramètres dans le stacked widget."""
        def _fn():
            from views.settings.vue_parametre import ParametreView

            def _factory():
                pv = ParametreView()
                pv.session_changed.connect(self._changer_session)
                return pv

            def _charger(p):
                p.rafraichir_sessions()

            self._creer_ou_rafraichir(
                'page_parametre', 'parametre_index',
                _factory,
                _charger
            )
        self._avec_chargement("Paramètres", _fn)

    def _changer_session(self, code_session: str):
        """Change la session consultée et recharge le dashboard."""
        if code_session == self.code_session:
            return
        self.code_session = code_session

        # Supprimer toutes les pages dynamiques (sauf page 0 = dashboard)
        pages_a_supprimer = [
            ('page_consultation',       'consultation_index'),
            ('page_tableau_consultation','tableau_consultation_index'),
            ('page_parametre',          'parametre_index'),
        ]
        indices_a_supprimer = []
        for attr_page, attr_idx in pages_a_supprimer:
            if hasattr(self, attr_page):
                indices_a_supprimer.append(getattr(self, attr_idx, -1))
        # Supprimer en ordre décroissant pour ne pas décaler les indices
        for idx in sorted(set(indices_a_supprimer), reverse=True):
            if idx > 0:
                widget = self.stacked_widget.widget(idx)
                if widget:
                    self.stacked_widget.removeWidget(widget)
                    widget.deleteLater()
        for attr_page, attr_idx in pages_a_supprimer:
            if hasattr(self, attr_page):
                delattr(self, attr_page)
            if hasattr(self, attr_idx):
                delattr(self, attr_idx)

        # Retour au dashboard et rechargement avec la nouvelle session
        self.stacked_widget.setCurrentIndex(0)

        def _refresh():
            if hasattr(self, '_stats_tab_widget'):
                self._stats_tab_widget.charger_donnees(self.code_session)
            if hasattr(self, '_graphes_tab_widget'):
                self._graphes_tab_widget.charger_donnees(self.code_session)
        self._avec_chargement(f"Administration — Session {code_session}", _refresh)

    # =========================================================================
    # CONSTRUCTION PRINCIPALE
    # =========================================================================

    def _init_ui(self):
        """Construction de l'interface principale."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Zone principale (navigation haute + contenu avec sidebar)
        self.main_area = self._creer_zone_principale()
        main_layout.addWidget(self.main_area)

    # =========================================================================
    # NAVIGATION GAUCHE (FRAME VERTICAL)
    # =========================================================================

    def _creer_navigation_gauche(self) -> QFrame:
        """Crée le frame de navigation vertical à gauche."""
        c = theme_manager.colors()
        frame = QFrame()
        frame.setFixedWidth(100)
        frame.setObjectName("admin_sidebar")
        frame.setStyleSheet(f"""
            QFrame#admin_sidebar {{
                background-color: {c['bg_card']};
                border-radius: 18px;
                border: 1px solid {c['border']};
            }}
        """)
        
        # Ombre portée
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 30))
        frame.setGraphicsEffect(shadow)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(6)

        # Titre
        titre = QLabel("Analyses")
        titre.setObjectName("admin_sidebar_title")
        titre.setStyleSheet(
            f"font-weight: bold; color: {c['primary']}; "
            "font-size: 12px; border: none;"
        )
        titre.setAlignment(Qt.AlignCenter)
        layout.addWidget(titre)

        layout.addSpacing(4)

        # Boutons des services avec icône graphe
        self.btn_dashboard = self._creer_bouton_service(
            "Dashboard", "fa5s.chart-area", c['primary']
        )
        
        # Bouton Consultation avec menu popup (comme un dashboard web)
        self.btn_consultation_main = self._creer_bouton_service(
            "Consultation", "fa5s.chart-line", c['info']
        )
        
        # Menu popup qui apparaît au clic
        self.consultation_menu = QMenu(self)
        self.consultation_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding: 6px;
            }}
            QMenu::item {{
                background-color: transparent;
                color: {c['text_primary']};
                padding: 10px 20px;
                font-size: 12px;
                font-weight: 600;
                border-radius: 8px;
                margin: 2px 4px;
            }}
            QMenu::item:hover {{
                background-color: {c['info']};
                color: {c['text_inverse']};
            }}
            QMenu::icon {{
                padding-left: 8px;
            }}
        """)
        self.action_graphes = self.consultation_menu.addAction(
            qta.icon("fa5s.chart-line", color=c['info']), "  Graphes"
        )
        self.action_tableau = self.consultation_menu.addAction(
            qta.icon("fa5s.table", color=c['info']), "  Tableau"
        )
        

        # bouton examen avec menu popup 
        self.btn_examen_main = self._creer_bouton_service(
            "Examen", "fa5s.vials", c['success']
        )



        self.btn_chirurgie_main = self._creer_bouton_service(
            "Chirurgie", "fa5s.chart-pie", c['warning']
        )



        # bouton lunette avec menu popup (comme consultation)
        self.btn_lunette_main = self._creer_bouton_service(
            "Lunette", "fa5s.chart-line", c['success']
        )


        self.btn_stock = self._creer_bouton_service(
            "Stock", "fa5s.chart-bar", c['danger']
        )
        self.btn_vente = self._creer_bouton_service(
            "Vente", "fa5s.chart-area", c['info']
        )
        self.btn_rendez_vous = self._creer_bouton_service(
            "Rendez-vous", "fa5s.calendar-alt", c['accent']
        )

        layout.addWidget(self.btn_dashboard, 0, Qt.AlignCenter)
        layout.addWidget(self.btn_consultation_main, 0, Qt.AlignCenter)
        layout.addWidget(self.btn_examen_main, 0, Qt.AlignCenter)
        layout.addWidget(self.btn_chirurgie_main, 0, Qt.AlignCenter)
        layout.addWidget(self.btn_lunette_main, 0, Qt.AlignCenter)
        layout.addWidget(self.btn_rendez_vous, 0, Qt.AlignCenter)
        layout.addWidget(self.btn_stock, 0, Qt.AlignCenter)
        layout.addWidget(self.btn_vente, 0, Qt.AlignCenter)
        layout.addStretch()

        return frame

    def _creer_bouton_service(self, texte: str, icone: str, couleur: str, width=76, height=56) -> QPushButton:
        """Crée un bouton de service avec nom et icône de graphe."""
        btn = QPushButton()
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(width, height)
        
        # Layout vertical pour le bouton
        layout = QVBoxLayout(btn)
        layout.setContentsMargins(5, 8, 5, 8)
        layout.setSpacing(5)
        
        # Nom du service
        label_nom = QLabel(texte)
        label_nom.setAlignment(Qt.AlignCenter)
        label_nom.setWordWrap(True)
        label_nom.setStyleSheet(
            f"color: {theme_manager.colors()['text_primary']}; font-size: 9px; font-weight: 600; "
            "border: none; background: transparent;"
        )
        
        # Icône d'analyse
        label_icone = QLabel()
        label_icone.setPixmap(
            qta.icon(icone, color=couleur).pixmap(QSize(24, 24))
        )
        label_icone.setAlignment(Qt.AlignCenter)
        label_icone.setStyleSheet("border: none; background: transparent;")
        
        layout.addWidget(label_nom)
        layout.addWidget(label_icone)
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {theme_manager.colors()['hover']};
            }}
        """)
        
        return btn

    # =========================================================================
    # ZONE PRINCIPALE (NAVIGATION HAUTE + CONTENU)
    # =========================================================================

    def _creer_zone_principale(self) -> QWidget:
        """Crée la zone principale avec navigation haute et contenu."""
        c = theme_manager.colors()
        widget = QWidget()
        widget.setObjectName("admin_main_area")
        widget.setStyleSheet(f"QWidget#admin_main_area {{ background-color: {c['bg_main']}; }}")

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Navigation haute
        self.top_bar = self._creer_navigation_haute()
        layout.addWidget(self.top_bar)

        # Container pour la navigation gauche + contenu
        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Zone de contenu directement dans le layout (sans scroll, comme dashboard_view)
        self.content_widget = self._creer_zone_contenu()

        content_layout.addWidget(self.content_widget, 1)

        layout.addWidget(content_container)

        return widget

    # =========================================================================
    # NAVIGATION HAUTE
    # =========================================================================

    def _creer_navigation_haute(self) -> QFrame:
        """Crée la barre de navigation horizontale en haut."""
        c = theme_manager.colors()
        top_bar = QFrame()
        top_bar.setFixedHeight(52)
        top_bar.setObjectName("admin_topbar")
        top_bar.setStyleSheet(f"""
            QFrame#admin_topbar {{
                background-color: {c['bg_card']};
                border-bottom: 1px solid {c['border']};
            }}
        """)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(15)

        # Boutons de navigation haute
        self.btn_compte = self._creer_bouton_top_bar("Compte", "fa5s.user-circle")
        self.btn_patient = self._creer_bouton_top_bar("Patient", "fa5s.user-injured")
        self.btn_personnel = self._creer_bouton_top_bar("Personnel", "fa5s.users")
        self.btn_parametre = self._creer_bouton_top_bar("Paramètre", "fa5s.cog")

        layout.addWidget(self.btn_compte)
        layout.addWidget(self.btn_patient)
        layout.addWidget(self.btn_personnel)
        layout.addWidget(self.btn_parametre)

        layout.addStretch()

        # Boutons d'action à droite
        self.btn_notification = self._creer_bouton_icone_top_bar(
            "fa5s.bell", "Notifications"
        )
        self.btn_messagerie = self._creer_bouton_icone_top_bar(
            "fa5s.envelope", "Messagerie"
        )
        self.btn_info = self._creer_bouton_icone_top_bar(
            "fa5s.info-circle", "Information"
        )

        layout.addWidget(self.btn_notification)
        layout.addWidget(self.btn_messagerie)
        layout.addWidget(self.btn_info)

        return top_bar

    def _creer_bouton_top_bar(self, texte: str, icone: str) -> QPushButton:
        """Crée un bouton pour la barre de navigation haute."""
        c = theme_manager.colors()
        btn = QPushButton(qta.icon(icone, color=c['primary']), f" {texte}")
        btn.setFixedHeight(36)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setIconSize(QSize(14, 14))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_main']};
                color: {c['primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
            }}
        """)
        return btn

    def _creer_bouton_icone_top_bar(self, icone: str, tooltip: str) -> QPushButton:
        """Crée un bouton icône pour la barre haute."""
        c = theme_manager.colors()
        btn = QPushButton(qta.icon(icone, color=c['primary']), "")
        btn.setFixedSize(36, 36)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setIconSize(QSize(16, 16))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_main']};
                border: 1px solid {c['border']};
                border-radius: 18px;
            }}
            QPushButton:hover {{
                background-color: {c['primary']};
            }}
        """)
        return btn

    # =========================================================================
    # ZONE DE CONTENU (FRAMES VIDES)
    # =========================================================================

    def _creer_zone_contenu(self) -> QWidget:
        """Crée la zone de contenu avec les frames."""
        widget = QWidget()
        main_layout = QHBoxLayout(widget)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(10)

        # Navigation gauche
        self.sidebar = self._creer_navigation_gauche()
        main_layout.addWidget(self.sidebar, 0)

        # QStackedWidget pour gérer les différentes vues
        self.stacked_widget = QStackedWidget()
        
        # Page 0: Dashboard par défaut (frames vides)
        self.page_dashboard = self._creer_page_dashboard()
        self.stacked_widget.addWidget(self.page_dashboard)
        
        # Page 1: Analyse Consultation (sera créée à la demande)
        # Les autres pages seront ajoutées dynamiquement
        
        main_layout.addWidget(self.stacked_widget, 1)

        return widget
    
    def _creer_page_dashboard(self) -> QWidget:
        """Crée la page dashboard avec 2 onglets vides."""
        import qtawesome as qta
        from PySide6.QtWidgets import QTabWidget, QWidget
        from PySide6.QtCore import QSize

        page = QWidget()
        page.setObjectName("AdminDashboardPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._dashboard_tabs = QTabWidget()
        self._dashboard_tabs.setTabPosition(QTabWidget.North)
        self._dashboard_tabs.setIconSize(QSize(18, 18))

        c = theme_manager.colors()

        # Onglet Statistiques — vue globale KPIs
        from views.admin.admin_stats_tab import AdminStatsTab
        self._stats_tab_widget = AdminStatsTab(
            consultation_ctrl=self.consultation_ctrl,
            examen_ctrl=self.examen_ctrl,
            chirurgie_ctrl=self.chirurgie_ctrl,
            lunette_ctrl=self.lunette_ctrl,
            rendez_vous_ctrl=self.rendez_vous_ctrl,
            visite_ctrl=self.visite_ctrl,
        )
        self._tab_stats = self._stats_tab_widget
        self._dashboard_tabs.addTab(
            self._tab_stats,
            qta.icon("fa5s.chart-bar", color=c['primary']),
            "  Statistiques"
        )

        # Onglet Graphes — courbes lissées multi-services
        from views.admin.admin_graphes_tab import AdminGraphesTab
        self._graphes_tab_widget = AdminGraphesTab(
            consultation_ctrl=self.consultation_ctrl,
            examen_ctrl=self.examen_ctrl,
            chirurgie_ctrl=self.chirurgie_ctrl,
            lunette_ctrl=self.lunette_ctrl,
        )
        self._tab_graphes = self._graphes_tab_widget
        self._dashboard_tabs.addTab(
            self._tab_graphes,
            qta.icon("fa5s.chart-line", color=c['primary']),
            "  Graphes"
        )

        self._appliquer_style_dashboard_tabs(c)
        layout.addWidget(self._dashboard_tabs)

        self._vue_dashboard = page
        return page

    def _appliquer_style_dashboard_tabs(self, c=None):
        if c is None:
            c = theme_manager.colors()
        self._dashboard_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {c['bg_card']};
            }}
            QTabBar {{
                background: {c['bg_card']};
                border: none;
            }}
            QTabBar::tab {{
                background: {c['bg_card']};
                color: {c['text_secondary']};
                border: none;
                border-bottom: 3px solid transparent;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: 600;
                min-width: 130px;
            }}
            QTabBar::tab:selected {{
                color: {c['primary']};
                border-bottom: 3px solid {c['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                color: {c['text_primary']};
            }}
        """)

    def _creer_frame_vide(self, titre: str, icone: str) -> QFrame:
        """Crée un cadre vide responsive avec titre et icône."""
        c = theme_manager.colors()
        frame = QFrame()
        frame.setMinimumHeight(120)
        frame.setObjectName("admin_card_frame")
        frame.setStyleSheet(f"""
            QFrame#admin_card_frame {{
                background-color: {c['bg_card']};
                border-radius: 18px;
                border: 1px solid {c['border']};
            }}
        """)

        # Ombre portée
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 30))
        frame.setGraphicsEffect(shadow)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # En-tête avec icône et titre
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon(icone, color=c['primary']).pixmap(QSize(20, 20))
        )
        icon_lbl.setStyleSheet("border: none; background: transparent;")

        title_lbl = QLabel(titre)
        title_lbl.setStyleSheet(
            f"font-weight: bold; color: {c['text_primary']}; font-size: 13px; border: none;"
        )

        header.addWidget(icon_lbl)
        header.addSpacing(8)
        header.addWidget(title_lbl)
        header.addStretch()

        layout.addLayout(header)

        # Séparateur
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {c['border']}; border: none;")
        layout.addWidget(sep)

        # Zone vide pour le contenu futur
        content_label = QLabel("Contenu à venir...")
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet(
            f"color: {c['text_muted']}; font-size: 12px; border: none;"
        )
        layout.addWidget(content_label)
        layout.addStretch()

        return frame

    # =========================================================================
    # APPLICATION DU THÈME
    # =========================================================================

    def apply_theme(self):
        """Ré-applique les couleurs du thème sur tous les composants."""
        c = theme_manager.colors()

        # --- Sidebar ---
        self.sidebar.setStyleSheet(f"""
            QFrame#admin_sidebar {{
                background-color: {c['bg_card']};
                border-radius: 18px;
                border: 1px solid {c['border']};
            }}
        """)
        # Titre dans la sidebar
        for lbl in self.sidebar.findChildren(QLabel):
            if lbl.objectName() == "admin_sidebar_title":
                lbl.setStyleSheet(
                    f"font-weight: bold; color: {c['primary']}; "
                    "font-size: 12px; border: none;"
                )

        # --- Main area background ---
        self.main_area.setStyleSheet(
            f"QWidget#admin_main_area {{ background-color: {c['bg_main']}; }}"
        )

        # --- Top bar ---
        self.top_bar.setStyleSheet(f"""
            QFrame#admin_topbar {{
                background-color: {c['bg_card']};
                border-bottom: 1px solid {c['border']};
            }}
        """)

        # --- Top bar text buttons ---
        for btn in (self.btn_compte, self.btn_patient,
                    self.btn_personnel, self.btn_parametre):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['bg_main']};
                    color: {c['primary']};
                    border: 1px solid {c['border']};
                    border-radius: 10px;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {c['primary']};
                    color: {c['text_inverse']};
                }}
            """)

        # --- Top bar icon buttons ---
        for btn in (self.btn_notification, self.btn_messagerie, self.btn_info):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['bg_main']};
                    border: 1px solid {c['border']};
                    border-radius: 22px;
                }}
                QPushButton:hover {{
                    background-color: {c['primary']};
                }}
            """)

        # --- Sidebar service buttons ---
        for btn in (self.btn_dashboard, self.btn_consultation_main,
                    self.btn_examen_main, self.btn_chirurgie_main, self.btn_lunette_main,
                    self.btn_rendez_vous, self.btn_stock, self.btn_vente):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 10px;
                }}
                QPushButton:hover {{
                    background-color: {c['hover']};
                }}
            """)
            # Update text labels inside buttons
            for lbl in btn.findChildren(QLabel):
                text = lbl.text()
                if text and not lbl.pixmap():
                    lbl.setStyleSheet(
                        f"color: {c['text_primary']}; font-size: 9px; "
                        "font-weight: 600; border: none; background: transparent;"
                    )

        # --- Consultation popup menu ---
        self.consultation_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding: 6px;
            }}
            QMenu::item {{
                background-color: transparent;
                color: {c['text_primary']};
                padding: 10px 20px;
                font-size: 12px;
                font-weight: 600;
                border-radius: 8px;
                margin: 2px 4px;
            }}
            QMenu::item:hover {{
                background-color: {c['info']};
                color: {c['text_inverse']};
            }}
            QMenu::icon {{
                padding-left: 8px;
            }}
        """)

        # --- Dashboard tabs ---
        if hasattr(self, '_dashboard_tabs'):
            self._appliquer_style_dashboard_tabs(c)
            import qtawesome as qta
            self._dashboard_tabs.setTabIcon(0, qta.icon("fa5s.chart-bar",  color=c['primary']))
            self._dashboard_tabs.setTabIcon(1, qta.icon("fa5s.chart-line", color=c['primary']))

        # --- Propager aux vues enfants dans le stacked widget ---
        for i in range(self.stacked_widget.count()):
            page = self.stacked_widget.widget(i)
            if hasattr(page, 'apply_theme'):
                try:
                    page.apply_theme()
                except Exception:
                    pass
