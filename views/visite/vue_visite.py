"""
Vue Visite - Interface principale de gestion des visites
Architecture à onglets pour une interface moins chargée
"""
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
                                QTabWidget, QPushButton, QFrame)
from PySide6.QtCore import Qt, QEvent, QSize, Signal
from PySide6.QtGui import QIcon
from views.shared.theme_manager import theme_manager

# Import des composants modulaires
from .components import (
    HeaderSection,
    KpiCardsSection,
    ChartsSection,
    VisitsTable,
    SidebarStats,
    QuickActions,
    VisitCardsPanel,
)


class VisiteView(QWidget):
    """Vue principale pour la gestion des visites médicales"""

    rdv_visite_created = Signal(str, str)  # (code_visite, code_session)

    def __init__(self, visite_controleur):
        super().__init__()
        self.ctrl = visite_controleur
        self.logger = logging.getLogger(__name__)
        
        self.init_ui()
        self.connect_signals()
        self.load_data()
        
        # Appliquer le thème
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
        
        # Installer le filtre d'événements pour la responsivité
        self.installEventFilter(self)
    
    def init_ui(self):
        """Initialise l'interface utilisateur avec onglets"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(0)
        
        # Frame principal blanc qui contient tout
        main_frame = QFrame()
        main_frame.setObjectName("MainWhiteFrame")
        main_frame_layout = QVBoxLayout(main_frame)
        main_frame_layout.setContentsMargins(0, 0, 0, 0)
        main_frame_layout.setSpacing(0)
        
        # Tabs Widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setIconSize(QSize(20, 20))
        self._apply_tab_styles()
        main_frame_layout.addWidget(self.tabs)
        
        # Onglet 1: Statistiques
        self.tab_stats = self._create_stats_tab()
        icon_stats = self._get_icon("chart-line")
        self.tabs.addTab(self.tab_stats, icon_stats, "Statistiques")
        
        # Onglet 2: Nouveau
        self.tab_nouveau = self._create_nouveau_tab()
        icon_nouveau = self._get_icon("plus")
        self.tabs.addTab(self.tab_nouveau, icon_nouveau, "Nouveau")
        
        # Onglet 3: Liste des visites
        self.tab_liste = self._create_liste_tab()
        icon_liste = self._get_icon("list")
        self.tabs.addTab(self.tab_liste, icon_liste, "Liste des visites")
        
        # Onglet 4: Statut patients
        self.tab_statut = self._create_statut_tab()
        icon_statut = self._get_icon("clock")
        self.tabs.addTab(self.tab_statut, icon_statut, "Statut patients")
        
        # Quick Actions (toujours visible en bas)
        self.quick_actions = QuickActions()
        main_frame_layout.addWidget(self.quick_actions)
        
        # Ajouter le frame principal au layout
        main_layout.addWidget(main_frame)
        
        # Appliquer le style au frame principal
        self._apply_main_frame_style(main_frame)
    
    def _get_icon(self, icon_name):
        """Récupère une icône Font Awesome ou standard"""
        try:
            # Essayer d'utiliser qtawesome si disponible
            import qtawesome as qta
            icon_map = {
                "chart-line": "fa5s.chart-line",
                "plus": "fa5s.plus-circle",
                "list": "fa5s.list",
                "clock": "fa5s.clock"
            }
            return qta.icon(icon_map.get(icon_name, "fa5s.circle"), color=theme_manager.colors()['primary'])
        except:
            # Fallback sur les icônes standard de Qt
            from PySide6.QtWidgets import QStyle
            style_map = {
                "chart-line": QStyle.SP_FileDialogDetailedView,
                "plus": QStyle.SP_FileIcon,
                "list": QStyle.SP_FileDialogListView,
                "clock": QStyle.SP_BrowserReload
            }
            return self.style().standardIcon(style_map.get(icon_name, QStyle.SP_FileIcon))
    
    def _create_stats_tab(self):
        """Crée l'onglet Statistiques"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)

        self._scroll_stats = QScrollArea()
        self._scroll_stats.setWidgetResizable(True)
        self._scroll_stats.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_stats.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        self.kpi_cards = KpiCardsSection(self.ctrl)
        content_layout.addWidget(self.kpi_cards)

        self.charts = ChartsSection(self.ctrl)
        content_layout.addWidget(self.charts, 1)

        self._scroll_stats.setWidget(content)
        layout.addWidget(self._scroll_stats)

        return tab
    
    def _create_nouveau_tab(self):
        """Crée l'onglet Nouveau avec formulaire intégré"""
        from .visite_form_widget import VisiteFormWidget

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.form_widget = VisiteFormWidget(self.ctrl)
        self.form_widget.visite_saved.connect(self.load_data)
        self.form_widget.rdv_visite_created.connect(self.rdv_visite_created)
        scroll.setWidget(self.form_widget)

        layout.addWidget(scroll)

        return tab
    
    def _create_liste_tab(self):
        """Crée l'onglet Liste des visites"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        
        # Table des visites
        self.visits_table = VisitsTable(self.ctrl)
        layout.addWidget(self.visits_table)
        
        return tab
    
    def _create_statut_tab(self):
        """Crée l'onglet Statut patients (surveillance en temps réel)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(12)

        # Barre supérieure avec bouton Actualiser
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.btn_actualiser_statut = QPushButton("  Actualiser")
        try:
            import qtawesome as qta
            self.btn_actualiser_statut.setIcon(qta.icon("fa5s.sync-alt", color=theme_manager.colors()['primary']))
        except Exception:
            pass
        self.btn_actualiser_statut.setFixedHeight(32)
        self.btn_actualiser_statut.setCursor(Qt.PointingHandCursor)
        self.btn_actualiser_statut.clicked.connect(self.load_data)
        top_bar.addWidget(self.btn_actualiser_statut)
        layout.addLayout(top_bar)

        horizontal_layout = QHBoxLayout()
        horizontal_layout.setSpacing(12)

        # --- Panneau gauche : cartes de visites actives ---
        self.visits_cards_panel = VisitCardsPanel()
        left_frame = QFrame()
        left_frame.setObjectName("StatutFrame")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(self.visits_cards_panel)
        self._apply_statut_frame_style(left_frame)

        # --- Panneau droit : alertes & attentes ---
        self.sidebar = SidebarStats(self.ctrl)
        right_frame = QFrame()
        right_frame.setObjectName("StatutFrame")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.addWidget(self.sidebar.alerts_frame)
        right_layout.addStretch()
        self._apply_statut_frame_style(right_frame)

        horizontal_layout.addWidget(left_frame, 3)
        horizontal_layout.addWidget(right_frame, 2)
        layout.addLayout(horizontal_layout)

        return tab
    
    def _apply_main_frame_style(self, frame):
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame#MainWhiteFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
        """)
    
    def _apply_statut_frame_style(self, frame):
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame#StatutFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
            }}
        """)
    
    def connect_signals(self):
        """Connecte tous les signaux des composants"""
        self.visits_table.btn_new_visit.clicked.connect(self._ouvrir_formulaire_visite)
        self.visits_table.view_clicked.connect(self._voir_details_visite)
        
        self.quick_actions.new_visit_clicked.connect(self._ouvrir_formulaire_visite)
        self.quick_actions.progression_clicked.connect(self._ouvrir_suivi_progression)
        self.quick_actions.priorities_clicked.connect(self._ouvrir_priorites)
        self.quick_actions.details_clicked.connect(self._ouvrir_details)
        self.quick_actions.export_clicked.connect(self._exporter_rapport)
        
        self.sidebar.view_all_alerts.connect(self._voir_toutes_alertes)
    
    def load_data(self):
        """Charge toutes les données"""
        try:
            actif, code_session = self.ctrl.verifier_session_active()
            if not actif:
                self.logger.warning("Aucune session active")
                return
            
            perf_stats = self.ctrl.obtenir_statistiques_performance()
            self._load_kpi_data(perf_stats)
            self._load_charts_data(perf_stats)
            self._load_table_data()
            self._load_sidebar_data()
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des données: {e}")
    
    def _load_kpi_data(self, perf_stats=None):
        """Charge les données des KPI cards"""
        try:
            today_count = self.ctrl.obtenir_nombre_visites_aujourdhui()
            completed_count = self.ctrl.obtenir_nombre_visites_terminees()
            urgent_count = self.ctrl.obtenir_nombre_urgences()
            
            if perf_stats is None:
                perf_stats = self.ctrl.obtenir_statistiques_performance()
            ongoing_count = perf_stats.get('visites_actives', 0)
            avg_duration = perf_stats.get('duree_moyenne', 0)
            tendance = perf_stats.get('tendance', '+0%')
            
            try:
                today_vs_yesterday = int(tendance.replace('%', '').replace('+', ''))
            except:
                today_vs_yesterday = 0
            
            total = today_count + completed_count + ongoing_count
            completed_pct = round((completed_count / total * 100), 1) if total > 0 else 0
            
            stats = {
                'today_count': today_count,
                'today_vs_yesterday': today_vs_yesterday,
                'completed_count': completed_count,
                'completed_pct': completed_pct,
                'ongoing_count': ongoing_count,
                'urgent_count': urgent_count,
                'avg_duration': avg_duration
            }
            
            self.kpi_cards.update_data(stats)
            
        except Exception as e:
            self.logger.error(f"Erreur chargement KPI: {e}")
    
    def _load_charts_data(self, stats_performance=None):
        """Charge les données des graphiques"""
        try:
            stats_mensuelles = self.ctrl.obtenir_stats_mensuelles()
            stats_ages = self.ctrl.get_stat_visites_par_age()
            
            if stats_performance is None:
                stats_performance = self.ctrl.obtenir_statistiques_performance()
            
            self.charts.update_data(stats_mensuelles, stats_ages, stats_performance)
            
        except Exception as e:
            self.logger.error(f"Erreur chargement graphiques: {e}")
    
    def _load_table_data(self):
        """Charge les données de la table"""
        try:
            visites = self.ctrl.obtenir_visites_prioritaires()
            self.visits_table.load_visits(visites)
            
        except Exception as e:
            self.logger.error(f"Erreur chargement table: {e}")
    
    def _load_sidebar_data(self):
        """Charge les données du sidebar et du panneau de visites actives"""
        try:
            # Panneau gauche : visites actives avec durée
            visites_actives = self.ctrl.obtenir_visites_actives_avec_duree()
            self.visits_cards_panel.update_cards(visites_actives)

            # Panneau droit : alertes
            bilan = self.ctrl.obtenir_bilan_performance_session()
            self.sidebar.update_repartition(bilan)

            codes_actifs = [v['code_visite'] for v in visites_actives] if visites_actives else []
            alertes = self.ctrl.verifier_alertes_temps_attente_batch(codes_actifs, seuil_minutes=20)
            self.sidebar.update_alerts(alertes)

        except Exception as e:
            self.logger.error(f"Erreur chargement sidebar: {e}")
    
    def _is_today(self, date_visite):
        """Vérifie si une date est aujourd'hui"""
        from datetime import datetime, date
        
        if isinstance(date_visite, str):
            try:
                date_obj = datetime.strptime(date_visite, "%Y-%m-%d %H:%M:%S").date()
            except:
                return False
        elif hasattr(date_visite, 'date'):
            date_obj = date_visite.date()
        else:
            date_obj = date_visite
        
        return date_obj == date.today()
    
    def showEvent(self, event):
        """Recharge les données à chaque fois que la vue devient visible."""
        super().showEvent(event)
        self.load_data()

    # ========================================================================
    # SLOTS - Actions des composants
    # ========================================================================
    
    def _toggle_notifications(self):
        """Affiche/masque le panneau de notifications"""
        try:
            from .notification_panel import NotificationPanel
            
            if not hasattr(self, 'notification_panel'):
                self.notification_panel = NotificationPanel(controleur=self.ctrl, parent=self)
            
            self.notification_panel.toggle()
            
        except Exception as e:
            self.logger.error(f"Erreur notifications: {e}")
    
    def _ouvrir_formulaire_visite(self):
        """Ouvre l'onglet Nouveau avec le formulaire intégré"""
        self.tabs.setCurrentIndex(1)  # Onglet 2 = Nouveau
    
    def _voir_details_visite(self, visite):
        """Affiche les détails d'une visite."""
        try:
            from .details_visite_modal import DetailsVisiteModal

            details      = self.ctrl.obtenir_dossier_complet_visite(visite.get_code_visite())
            patient_name = f"{getattr(visite, 'nom_patient', '')} {getattr(visite, 'prenom_patient', '')}".strip()
            cabinet_info = self.ctrl.get_cabinet_info()

            # Récupérer le patient complet pour naissance/genre/profession/adresse
            patient_obj = None
            try:
                from controllers.controleur_patient import ControleurPatient
                code_pat = str(visite.get_code_patient() or "").strip()
                if code_pat:
                    patient_obj = ControleurPatient().reed_by_code_patient(code_pat)
            except Exception as _e:
                self.logger.warning(f"Patient non récupéré pour carnet: {_e}")

            # Numéro dans la file d'attente consultation (0 = pas en attente)
            numero_attente = 0
            try:
                from data.dao_consultation import ConsultationDAO
                numero_attente = ConsultationDAO().get_numero_attente_consultation(
                    visite.get_code_visite()
                )
            except Exception as _ne:
                self.logger.warning(f"Numéro attente non calculé: {_ne}")

            modal = DetailsVisiteModal(
                self,
                visite.get_code_visite(),
                patient_name,
                details,
                cabinet_info,
                visite=visite,
                patient_obj=patient_obj,
                numero_attente=numero_attente,
            )
            modal.exec()

        except Exception as e:
            self.logger.error(f"Erreur détails visite: {e}")
    
    def _ouvrir_suivi_progression(self):
        """Navigue vers la liste des visites pour suivre la progression"""
        self.tabs.setCurrentIndex(2)
    
    def _ouvrir_priorites(self):
        self._toggle_notifications()
    
    def _ouvrir_details(self):
        """Navigue vers la liste pour sélectionner une visite et voir ses détails"""
        self.tabs.setCurrentIndex(2)
    
    def _exporter_rapport(self):
        """Affiche le menu popup export/import au-dessus du bouton."""
        try:
            from .export_import_visite import ExportImportMenu
            ExportImportMenu.afficher(self, self.quick_actions.btn_export, self.ctrl)
        except Exception as e:
            self.logger.error(f"Erreur menu export/import: {e}")
    
    def _voir_toutes_alertes(self):
        self._toggle_notifications()
    
    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"background: {c['bg_main']};")
        self._apply_tab_styles()

        if hasattr(self, 'tabs'):
            # Cascade QWidget{} vers tous les descendants de chaque onglet
            for tab, bg in (
                (getattr(self, 'tab_stats',   None), c['bg_card']),
                (getattr(self, 'tab_nouveau', None), c['bg_main']),
                (getattr(self, 'tab_liste',   None), c['bg_card']),
                (getattr(self, 'tab_statut',  None), c['bg_card']),
            ):
                if tab:
                    tab.setStyleSheet(f"QWidget {{ background: {bg}; }}")

            # Scroll area onglet stats
            if hasattr(self, '_scroll_stats'):
                self._scroll_stats.setStyleSheet(
                    f"QScrollArea {{ background: {c['bg_card']}; border: none; }}"
                )

            main_frame = self.findChild(QFrame, "MainWhiteFrame")
            if main_frame:
                self._apply_main_frame_style(main_frame)

            # Frames de l'onglet statut
            for f in self.findChildren(QFrame, "StatutFrame"):
                self._apply_statut_frame_style(f)

        # Propagation explicite aux composants enfants
        for widget in (
            getattr(self, 'kpi_cards',         None),
            getattr(self, 'charts',            None),
            getattr(self, 'visits_table',      None),
            getattr(self, 'quick_actions',     None),
            getattr(self, 'form_widget',       None),
            getattr(self, 'sidebar',           None),
            getattr(self, 'visits_cards_panel',None),
        ):
            if widget and hasattr(widget, 'apply_theme'):
                try:
                    widget.apply_theme()
                except Exception:
                    pass
    
    def _apply_tab_styles(self):
        """Applique les styles aux onglets"""
        from .styles import VisiteStyles
        self.tabs.setStyleSheet(VisiteStyles.tab_widget())
    
    def eventFilter(self, obj, event):
        """Filtre d'événements — réservé pour extensions futures"""
        return super().eventFilter(obj, event)
    
    def resizeEvent(self, event):
        """Gère le redimensionnement de la fenêtre"""
        super().resizeEvent(event)
    
    def cleanup(self):
        """Nettoyage avant fermeture"""
        pass