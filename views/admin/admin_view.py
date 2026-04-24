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

    def __init__(self, visite_ctrl):
        super().__init__()
        self.visite_ctrl = visite_ctrl
        self.current_view = None
        self.code_session = None
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
    
    def _charger_session_active(self):
        """Charge le code de la session active."""
        try:
            actif, code_session = self.visite_ctrl.verifier_session_active()
            if actif:
                self.code_session = code_session
        except Exception as e:
            print(f"[AdminView] Erreur chargement session: {e}")
            self.code_session = None
    
    def _connecter_boutons(self):
        """Connecte les boutons aux méthodes d'affichage."""
        self.btn_dashboard.clicked.connect(self.afficher_dashboard)
        self.btn_consultation_main.clicked.connect(self._afficher_menu_consultation)
        self.btn_examen_main.clicked.connect(self._afficher_menu_examen)
        self.btn_chirurgie_main.clicked.connect(self._afficher_menu_chirurgie)
        self.btn_lunette_main.clicked.connect(self._afficher_menu_lunette)
        self.btn_rendez_vous.clicked.connect(self.afficher_analyse_rendez_vous)
        self.btn_stock.clicked.connect(self.afficher_analyse_stock)
        self.btn_vente.clicked.connect(self.afficher_analyse_vente)
        self.action_graphes.triggered.connect(self.afficher_analyse_consultation)
        self.action_graphes_examen.triggered.connect(self.afficher_analyse_examen)
        self.action_graphes_chirurgie.triggered.connect(self.afficher_analyse_chirurgie)
        self.action_graphes_lunette.triggered.connect(self.afficher_analyse_lunette)
        self.action_tableau.triggered.connect(self.afficher_table_consultation)
        self.action_tableau_examen.triggered.connect(self.afficher_table_examen)
        self.action_tableau_chirurgie.triggered.connect(self.afficher_table_chirurgie)
        self.action_tableau_lunette.triggered.connect(self.afficher_table_lunette)
    
    # =========================================================================
    # MÉTHODES D'AFFICHAGE DES ANALYSES
    # =========================================================================
    
    def afficher_dashboard(self):
        """Affiche le dashboard par défaut avec les frames vides."""
        self.stacked_widget.setCurrentIndex(0)

    def afficher_analyse_stock(self):
        """Affiche l'interface d'analyse du stock."""
        if not self.code_session:
            print("[AdminView] Aucune session active")
            return

        try:
            from views.analyses.analyse_stock import AnalyseStockView

            if not hasattr(self, 'page_stock'):
                self.page_stock = AnalyseStockView(
                    self.stock_ctrl,
                    self.code_session
                )
                self.stacked_widget.addWidget(self.page_stock)
                self.stock_index = self.stacked_widget.count() - 1
            else:
                self.page_stock.code_session = self.code_session
                self.page_stock.rafraichir()

            self.stacked_widget.setCurrentIndex(self.stock_index)

        except Exception as e:
            print(f"[AdminView] Erreur affichage analyse stock: {e}")
            import traceback
            traceback.print_exc()

    def afficher_analyse_rendez_vous(self):
        """Affiche l'interface d'analyse des rendez-vous."""
        if not self.code_session:
            print("[AdminView] Aucune session active")
            return

        try:
            from views.analyses.analyse_rendez_vous import AnalyseRendezVousView

            if not hasattr(self, 'page_rendez_vous'):
                self.page_rendez_vous = AnalyseRendezVousView(
                    self.rendez_vous_ctrl,
                    self.code_session
                )
                self.stacked_widget.addWidget(self.page_rendez_vous)
                self.rendez_vous_index = self.stacked_widget.count() - 1
            else:
                self.page_rendez_vous.code_session = self.code_session
                self.page_rendez_vous.rafraichir()

            self.stacked_widget.setCurrentIndex(self.rendez_vous_index)

        except Exception as e:
            print(f"[AdminView] Erreur affichage analyse rendez-vous: {e}")
            import traceback
            traceback.print_exc()

    def afficher_analyse_vente(self):
        """Affiche l'interface d'analyse des ventes patient."""
        if not self.code_session:
            print("[AdminView] Aucune session active")
            return

        try:
            from views.analyses.analyse_vente import AnalyseVenteView

            if not hasattr(self, 'page_vente'):
                self.page_vente = AnalyseVenteView(
                    self.vente_ctrl,
                    self.code_session
                )
                self.stacked_widget.addWidget(self.page_vente)
                self.vente_index = self.stacked_widget.count() - 1
            else:
                self.page_vente.code_session = self.code_session
                self.page_vente.rafraichir()

            self.stacked_widget.setCurrentIndex(self.vente_index)

        except Exception as e:
            print(f"[AdminView] Erreur affichage analyse vente: {e}")
            import traceback
            traceback.print_exc()

    def afficher_analyse_consultation(self):
        """Affiche l'interface d'analyse des consultations."""
        if not self.code_session:
            print("[AdminView] Aucune session active")
            return
        
        try:
            from views.analyses.analyse_consultation import AnalyseConsultationView
            
            # Vérifie si la page existe déjà
            if not hasattr(self, 'page_consultation'):
                # Crée la page d'analyse consultation
                self.page_consultation = AnalyseConsultationView(
                    self.consultation_ctrl,
                    self.code_session
                )
                self.stacked_widget.addWidget(self.page_consultation)
                self.consultation_index = self.stacked_widget.count() - 1
            else:
                # Rafraîchit les données
                self.page_consultation.rafraichir()
            
            # Affiche la page
            self.stacked_widget.setCurrentIndex(self.consultation_index)
            
        except Exception as e:
            print(f"[AdminView] Erreur affichage analyse consultation: {e}")
            import traceback
            traceback.print_exc()
    
    def _afficher_menu_consultation(self):
        """Affiche le menu popup à côté du bouton Consultation."""
        btn = self.btn_consultation_main
        # Afficher le menu à droite du bouton
        pos = btn.mapToGlobal(btn.rect().topRight())
        self.consultation_menu.exec(pos)
    
    def afficher_table_consultation(self):
        """Affiche l'interface de tableau des consultations."""
        if not self.code_session:
            print("[AdminView] Aucune session active")
            return
        
        try:
            from views.analyses.tableau_consultation import TableauConsultationView

            if not hasattr(self, 'page_tableau_consultation'):
                self.page_tableau_consultation = TableauConsultationView(
                    self.consultation_ctrl,
                    self.code_session
                )
                self.stacked_widget.addWidget(self.page_tableau_consultation)
                self.tableau_consultation_index = self.stacked_widget.count() - 1
            else:
                self.page_tableau_consultation.charger_consultations(self.code_session)

            self.stacked_widget.setCurrentIndex(self.tableau_consultation_index)

        except Exception as e:
            print(f"[AdminView] Erreur affichage tableau consultation: {e}")
            import traceback
            traceback.print_exc()
    
    def afficher_analyse_examen(self):
        """Affiche l'interface d'analyse des examens."""
        if not self.code_session:
            print("[AdminView] Aucune session active")
            return

        try:
            from views.analyses.analyse_examen import AnalyseExamenView

            if not hasattr(self, 'page_examen'):
                self.page_examen = AnalyseExamenView(
                    self.examen_ctrl,
                    self.code_session
                )
                self.stacked_widget.addWidget(self.page_examen)
                self.examen_index = self.stacked_widget.count() - 1
            else:
                self.page_examen.rafraichir()

            self.stacked_widget.setCurrentIndex(self.examen_index)

        except Exception as e:
            print(f"[AdminView] Erreur affichage analyse examen: {e}")
            import traceback
            traceback.print_exc()
            
    def afficher_analyse_lunette(self):
        """Affiche l'interface d'analyse des commandes lunettes."""
        if not self.code_session:
            print("[AdminView] Aucune session active")
            return

        try:
            from views.analyses.analyse_commande_lunette import AnalyseCommandeLunetteView

            if not hasattr(self, 'page_lunette'):
                self.page_lunette = AnalyseCommandeLunetteView(
                    self.lunette_ctrl,
                    self.code_session
                )
                self.stacked_widget.addWidget(self.page_lunette)
                self.lunette_index = self.stacked_widget.count() - 1
            else:
                self.page_lunette.rafraichir()

            self.stacked_widget.setCurrentIndex(self.lunette_index)

        except Exception as e:
            print(f"[AdminView] Erreur affichage analyse lunette: {e}")
            import traceback
            traceback.print_exc()
            
    def afficher_analyse_chirurgie(self):
        """Affiche l'interface d'analyse des chirurgies."""
        if not self.code_session:
            print("[AdminView] Aucune session active")
            return

        try:
            from views.analyses.analyse_chirurgie import AnalyseChirurgieView

            if not hasattr(self, 'page_chirurgie'):
                self.page_chirurgie = AnalyseChirurgieView(
                    self.chirurgie_ctrl,
                    self.code_session
                )
                self.stacked_widget.addWidget(self.page_chirurgie)
                self.chirurgie_index = self.stacked_widget.count() - 1
            else:
                self.page_chirurgie.rafraichir()

            self.stacked_widget.setCurrentIndex(self.chirurgie_index)

        except Exception as e:
            print(f"[AdminView] Erreur affichage analyse chirurgie: {e}")
            import traceback
            traceback.print_exc()
    
    def _afficher_menu_examen(self):
        """Affiche le menu popup à côté du bouton Examen."""
        btn = self.btn_examen_main
        # Afficher le menu à droite du bouton
        pos = btn.mapToGlobal(btn.rect().topRight())
        self.examen_menu.exec(pos)
    
    def afficher_table_examen(self):
        """Affiche l'interface de tableau des examens."""
        if not self.code_session:
            print("[AdminView] Aucune session active")
            return

        try:
            from views.analyses.tableau_examen import TableauExamenView

            if not hasattr(self, 'page_tableau_examen'):
                self.page_tableau_examen = TableauExamenView(
                    self.examen_ctrl,
                    self.code_session
                )
                self.stacked_widget.addWidget(self.page_tableau_examen)
                self.tableau_examen_index = self.stacked_widget.count() - 1
            else:
                self.page_tableau_examen.charger_examens(self.code_session)

            self.stacked_widget.setCurrentIndex(self.tableau_examen_index)

        except Exception as e:
            print(f"[AdminView] Erreur affichage tableau examen: {e}")
            import traceback
            traceback.print_exc()
            
    def _afficher_menu_chirurgie(self):
        """Affiche le menu popup à côté du bouton Chirurgie."""
        btn = self.btn_chirurgie_main
        # Afficher le menu à droite du bouton
        pos = btn.mapToGlobal(btn.rect().topRight())
        self.chirurgie_menu.exec(pos)
        
    def afficher_table_chirurgie(self):
        """Affiche l'interface de tableau des chirurgies."""
        if not self.code_session:
            print("[AdminView] Aucune session active")
            return

        try:
            from views.analyses.tableau_chirurgie import TableauChirurgieView

            if not hasattr(self, 'page_tableau_chirurgie'):
                self.page_tableau_chirurgie = TableauChirurgieView(
                    self.chirurgie_ctrl,
                    self.code_session
                )
                self.stacked_widget.addWidget(self.page_tableau_chirurgie)
                self.tableau_chirurgie_index = self.stacked_widget.count() - 1
            else:
                self.page_tableau_chirurgie.charger_chirurgies(self.code_session)

            self.stacked_widget.setCurrentIndex(self.tableau_chirurgie_index)

        except Exception as e:
            print(f"[AdminView] Erreur affichage tableau chirurgie: {e}")
            import traceback
            traceback.print_exc()
            
    def _afficher_menu_lunette(self):
        """Affiche le menu popup à côté du bouton Lunette."""
        btn = self.btn_lunette_main
        # Afficher le menu à droite du bouton
        pos = btn.mapToGlobal(btn.rect().topRight())
        self.lunette_menu.exec(pos)
        
    def afficher_table_lunette(self):
        """Affiche l'interface de tableau des commandes lunettes."""
        if not self.code_session:
            print("[AdminView] Aucune session active")
            return

        try:
            from views.analyses.tableau_lunette import TableauLunetteView

            if not hasattr(self, 'page_tableau_lunette'):
                self.page_tableau_lunette = TableauLunetteView(
                    self.lunette_ctrl,
                    self.code_session
                )
                self.stacked_widget.addWidget(self.page_tableau_lunette)
                self.tableau_lunette_index = self.stacked_widget.count() - 1
            else:
                self.page_tableau_lunette.charger_commandes(self.code_session)

            self.stacked_widget.setCurrentIndex(self.tableau_lunette_index)

        except Exception as e:
            print(f"[AdminView] Erreur affichage tableau lunette: {e}")
            import traceback
            traceback.print_exc()
    
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

        self.examen_menu = QMenu(self)
        self.examen_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding: 6px;
            }}
            QMenu::item {{
                background-color: transparent;
            }}
        """)

        self.action_graphes_examen = self.examen_menu.addAction(
            qta.icon("fa5s.chart-bar", color=c['success']), "Graphes"
        )
        self.action_tableau_examen = self.examen_menu.addAction(
            qta.icon("fa5s.table", color=c['success']), "Tableau"
        )

        self.btn_chirurgie_main = self._creer_bouton_service(
            "Chirurgie", "fa5s.chart-pie", c['warning']
        )
        self.chirurgie_menu = QMenu(self)
        self.chirurgie_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding: 6px;
            }}
            QMenu::item {{
                background-color: transparent;
            }}
        """)
        self.action_graphes_chirurgie = self.chirurgie_menu.addAction(
            qta.icon("fa5s.chart-bar", color=c['warning']), "Graphes"
        )
        self.action_tableau_chirurgie = self.chirurgie_menu.addAction(
            qta.icon("fa5s.table", color=c['warning']), "Tableau"
        )


        # bouton lunette avec menu popup (comme consultation)
        self.btn_lunette_main = self._creer_bouton_service(
            "Lunette", "fa5s.chart-line", c['success']
        )
        self.lunette_menu = QMenu(self)
        self.lunette_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding: 6px;
            }}
            QMenu::item {{
                background-color: transparent;
            }}
        """)
        self.action_graphes_lunette = self.lunette_menu.addAction(
            qta.icon("fa5s.chart-bar", color=c['success']), "Graphes"
        )
        self.action_tableau_lunette = self.lunette_menu.addAction(
            qta.icon("fa5s.table", color=c['success']), "Tableau"
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
        top_bar.setFixedHeight(70)
        top_bar.setObjectName("admin_topbar")
        top_bar.setStyleSheet(f"""
            QFrame#admin_topbar {{
                background-color: {c['bg_card']};
                border-bottom: 1px solid {c['border']};
            }}
        """)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 10, 20, 10)
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
        btn.setFixedHeight(45)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setIconSize(QSize(16, 16))
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
        return btn

    def _creer_bouton_icone_top_bar(self, icone: str, tooltip: str) -> QPushButton:
        """Crée un bouton icône pour la barre haute."""
        c = theme_manager.colors()
        btn = QPushButton(qta.icon(icone, color=c['primary']), "")
        btn.setFixedSize(45, 45)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setIconSize(QSize(18, 18))
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
        return btn

    # =========================================================================
    # ZONE DE CONTENU (FRAMES VIDES)
    # =========================================================================

    def _creer_zone_contenu(self) -> QWidget:
        """Crée la zone de contenu avec les frames."""
        widget = QWidget()
        main_layout = QHBoxLayout(widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Navigation gauche
        self.sidebar = self._creer_navigation_gauche()
        main_layout.addWidget(self.sidebar, 0, Qt.AlignTop)

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
        """Crée la page dashboard responsive avec les frames."""
        from views.admin.responsive_helper import ResponsiveGridContainer

        page = ResponsiveGridContainer(spacing=15)

        # Création des frames (tailles gérées par le conteneur responsive)
        self.frame_graphique = self._creer_frame_vide(
            "Statistiques Mensuelles", "fa5s.chart-bar"
        )
        self.frame_ratio = self._creer_frame_vide(
            "Ratio Income", "fa5s.chart-pie"
        )
        self.frame_balance = self._creer_frame_vide(
            "Balance", "fa5s.credit-card"
        )
        self.frame_budget = self._creer_frame_vide(
            "Budget Plan", "fa5s.wallet"
        )
        self.frame_invest = self._creer_frame_vide(
            "Investissement", "fa5s.chart-line"
        )
        self.frame_goals = self._creer_frame_vide(
            "Objectifs Financiers", "fa5s.bullseye"
        )
        self.frame_debts = self._creer_frame_vide(
            "Dettes", "fa5s.money-bill-wave"
        )

        # Section 1 : graphiques (chart = 2 colonnes en XL)
        page.ajouter_section(
            [self.frame_graphique, self.frame_ratio, self.frame_balance],
            xl_spans=[2, 1, 1]
        )
        # Section 2 : cartes financières (4 colonnes égales en XL)
        page.ajouter_section(
            [self.frame_budget, self.frame_invest,
             self.frame_goals, self.frame_debts]
        )

        return page

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

        # --- Examen popup menu ---
        self.examen_menu.setStyleSheet(f"""
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

        # --- Dashboard frames ---
        for frame in (self.frame_graphique, self.frame_ratio, self.frame_balance,
                      self.frame_budget, self.frame_invest, self.frame_goals,
                      self.frame_debts):
            frame.setStyleSheet(f"""
                QFrame#admin_card_frame {{
                    background-color: {c['bg_card']};
                    border-radius: 18px;
                    border: 1px solid {c['border']};
                }}
            """)
            # Update labels inside each frame
            for lbl in frame.findChildren(QLabel):
                text = lbl.text()
                if text == "Contenu à venir...":
                    lbl.setStyleSheet(
                        f"color: {c['text_muted']}; font-size: 12px; border: none;"
                    )
                elif text and text != "":
                    lbl.setStyleSheet(
                        f"font-weight: bold; color: {c['text_primary']}; "
                        "font-size: 13px; border: none;"
                    )
            # Update separators
            for child_frame in frame.findChildren(QFrame):
                if child_frame.maximumHeight() == 1:
                    child_frame.setStyleSheet(
                        f"background: {c['border']}; border: none;"
                    )

        # --- Propager aux vues enfants dans le stacked widget ---
        for i in range(self.stacked_widget.count()):
            page = self.stacked_widget.widget(i)
            if hasattr(page, 'apply_theme'):
                try:
                    page.apply_theme()
                except Exception:
                    pass
