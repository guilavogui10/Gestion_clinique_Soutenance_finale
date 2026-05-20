"""
Vue Examen - interface principale de gestion des examens.
Architecture à onglets pour une interface cohérente avec consultation
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea,
                                QTabWidget, QFrame, QDialog, QHBoxLayout,
                                QLabel, QPushButton, QDateEdit,
                                QComboBox, QSizePolicy, QLineEdit)
from PySide6.QtCore import Qt, QSize, QDate
from views.shared.theme_manager import theme_manager
from .components import (
    KpiCardsSection,
    ExamensTable,
    QuickActions,
    ChartsSection
)
from .historique_examen import HistoriquePatientView


class ExamenView(QWidget):
    """Vue principale examen."""
    
    def __init__(self, examen_ctrl, permission_ctrl=None, user_info=None, parent=None):
        super().__init__(parent)
        self.ctrl = examen_ctrl
        self.permission_ctrl = permission_ctrl
        self.user_info = user_info or {}
        self.code_session = None
        
        # Créer le helper de permissions si disponible
        self.permission_helper = None
        if self.permission_ctrl and self.user_info:
            from views.shared.permission_helper import PermissionHelper
            self.permission_helper = PermissionHelper(self, self.permission_ctrl, self.user_info)
        
        self.init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def init_ui(self):
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
        
        # Onglet 3: Liste des examens
        self.tab_liste = self._create_liste_tab()
        icon_liste = self._get_icon("list")
        self.tabs.addTab(self.tab_liste, icon_liste, "Liste des examens")
        
        # Onglet 4: Patients en attente
        self.tab_attente = self._create_attente_tab()
        icon_attente = self._get_icon("clock")
        self.tabs.addTab(self.tab_attente, icon_attente, "Patients en attente")

        # Onglet 5: Historique patient
        self.tab_historique = self._create_historique_tab()
        icon_hist = self._get_icon("history")
        self.tabs.addTab(self.tab_historique, icon_hist, "Historique patient")
        
        # Quick Actions (toujours visible en bas)
        self.quick_actions = QuickActions()
        self.quick_actions.new_examen_clicked.connect(self.on_new_examen)
        self.quick_actions.patients_waiting_clicked.connect(self.on_patients_waiting)
        self.quick_actions.advanced_search_clicked.connect(self.on_advanced_search)
        self.quick_actions.reports_clicked.connect(self.on_reports)
        self.quick_actions.patient_history_clicked.connect(self.on_patient_history)
        main_frame_layout.addWidget(self.quick_actions)
        
        # Ajouter le frame principal au layout
        main_layout.addWidget(main_frame)
        
        # Appliquer le style au frame principal
        self._apply_main_frame_style(main_frame)
    
    def charger_examens(self, code_session):
        self.code_session = code_session
        # Mettre à jour les sous-vues AVANT charger_donnees
        if hasattr(self, 'vue_attente'):
            self.vue_attente.code_session = code_session
        if hasattr(self, 'form_widget'):
            self.form_widget.code_session = code_session
            self.form_widget.edit_session.setText(code_session or "")
        self.charger_donnees()
    
    def charger_donnees(self):
        if not self.code_session:
            return
        examens = self.ctrl.lister_examens(self.code_session)
        self.table.load_examens(examens, self.code_session)
        self.kpi_cards.rafraichir(self.code_session)
        # Rafraîchir les graphiques
        if hasattr(self, 'charts'):
            self.charts.update_data(self.code_session)
        # Rafraîchir la vue des patients en attente
        if hasattr(self, 'vue_attente'):
            self.vue_attente.charger_patients()
        # Rafraîchir le combo patient de l'historique
        if hasattr(self, 'vue_historique'):
            self.vue_historique.set_session(self.code_session)
    
    def on_view_examen(self, examen):
        from .detail_examen_modal import DetailsExamenModal
        DetailsExamenModal(self, examen.code, self.ctrl).exec()
    
    def on_delete_examen(self, examen):
        """Supprime un examen après confirmation (déjà faite dans la table)"""
        ok, msg = self.ctrl.supprimer_examen(examen.code)
        from views.shared.message_box import CustomMessageBox
        CustomMessageBox("Succès" if ok else "Erreur", msg, ok, self).exec()
        if ok:
            self.charger_donnees()

    def on_edit_examen(self, examen):
        """Modifier un examen - Vérification des permissions"""
        if not self.permission_helper:
            print(f"Éditer examen: {examen.code}")
            return
        
        def executer_modification():
            print(f"Éditer examen: {examen.code}")
        
        self.permission_helper.verifier_et_executer(
            action=self.permission_ctrl.ACTION_MODIFICATION,
            contexte=f"Examen {examen.code}",
            callback_success=executer_modification
        )
    
    def on_new_examen(self):
        """Créer un nouvel examen - Vérification des permissions"""
        if not self.permission_helper:
            self.tabs.setCurrentIndex(1)
            return
        
        if not self.permission_helper.peut_creer():
            def executer_creation():
                self.tabs.setCurrentIndex(1)
            
            self.permission_helper.verifier_et_executer(
                action=self.permission_ctrl.ACTION_MODIFICATION,
                contexte="Création d'un nouvel examen",
                callback_success=executer_creation
            )
        else:
            self.tabs.setCurrentIndex(1)

    def on_patients_waiting(self):
        """Bascule vers l'onglet Patients en attente."""
        self.tabs.setCurrentIndex(3)

    def _ouvrir_nouveau_avec_consultation(self, code_consultation: str):
        self.tabs.setCurrentIndex(1)
        if hasattr(self, 'form_widget'):
            self.form_widget.recharger_pour_patient(code_consultation, self.code_session)
    
    def on_advanced_search(self):
        """Recherche avancée entre deux dates."""
        if not self.code_session:
            return
        dialog = _RechercheEntresDatesDialog(self.ctrl, self.code_session, parent=self)
        if dialog.exec() == QDialog.Accepted:
            resultats = dialog.resultats
            self.tabs.setCurrentIndex(2)
            self.table.load_examens(resultats, self.code_session)

    def on_reports(self):
        """Affiche le résumé/rapport de la session courante."""
        if not self.code_session:
            return
        dialog = _ResumeSessionDialog(self.ctrl, self.code_session, parent=self)
        dialog.exec()

    def on_patient_history(self):
        """Bascule vers l'onglet Historique patient."""
        self.tabs.setCurrentIndex(4)
    
    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_main']};
            }}
        """)
        self._apply_tab_styles()
        if hasattr(self, 'tabs'):
            main_frame = self.findChild(QFrame, "MainWhiteFrame")
            if main_frame:
                self._apply_main_frame_style(main_frame)
    
    def _get_icon(self, icon_name):
        """Récupère une icône Font Awesome ou standard"""
        try:
            import qtawesome as qta
            icon_map = {
                "chart-line": "fa5s.chart-line",
                "list": "fa5s.list",
                "clock": "fa5s.clock",
                "plus": "fa5s.plus-circle",
                "history": "fa5s.history",
            }
            return qta.icon(icon_map.get(icon_name, "fa5s.circle"), color=theme_manager.colors()['primary'])
        except:
            from PySide6.QtWidgets import QStyle
            style_map = {
                "chart-line": QStyle.SP_FileDialogDetailedView,
                "list": QStyle.SP_FileDialogListView,
                "clock": QStyle.SP_BrowserReload
            }
            return self.style().standardIcon(style_map.get(icon_name, QStyle.SP_FileIcon))
    
    def _create_nouveau_tab(self):
        """Crée l'onglet Nouveau avec le formulaire d'examen"""
        from .examen_form_widget import ExamenFormWidget
        
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area pour le formulaire
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Widget formulaire
        self.form_widget = ExamenFormWidget(self.ctrl, self.code_session)
        self.form_widget.examen_saved.connect(self._on_examen_saved)
        scroll.setWidget(self.form_widget)
        
        layout.addWidget(scroll)
        
        return tab
    
    def _on_examen_saved(self):
        """Appelé quand un examen est enregistré"""
        self.charger_donnees()
        # Revenir à l'onglet Liste
        self.tabs.setCurrentIndex(2)
    
    def _create_stats_tab(self):
        """Crée l'onglet Statistiques"""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)
        
        # KPI Cards directement dans le layout
        self.kpi_cards = KpiCardsSection(self.ctrl)
        layout.addWidget(self.kpi_cards)
        
        # Charts Section - 3 graphiques
        self.charts = ChartsSection(self.ctrl)
        layout.addWidget(self.charts, 1)
        
        return tab
    
    def _create_liste_tab(self):
        """Crée l'onglet Liste des examens"""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        
        self.table = ExamensTable(self.ctrl)
        self.table.view_clicked.connect(self.on_view_examen)
        self.table.edit_clicked.connect(self.on_edit_examen)
        self.table.delete_clicked.connect(self.on_delete_examen)
        self.table.new_clicked.connect(self.on_new_examen)
        layout.addWidget(self.table)
        
        return tab
    
    def _create_attente_tab(self):
        """Crée l'onglet Patients en attente"""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(0)
        
        # Importer et afficher la vue des patients en attente
        from .patients_examen_attente import PatientsAttenteExamenView
        
        self.vue_attente = PatientsAttenteExamenView(
            self.ctrl,
            self.code_session if hasattr(self, 'code_session') and self.code_session else "",
            parent=tab
        )
        self.vue_attente.ouvrir_formulaire.connect(self._ouvrir_nouveau_avec_consultation)
        layout.addWidget(self.vue_attente)
        
        return tab

    def _create_historique_tab(self):
        """Crée l'onglet Historique patient (5ème onglet)."""
        tab = QWidget()
        tab.setStyleSheet("background: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.vue_historique = HistoriquePatientView(
            self.ctrl,
            self.code_session if hasattr(self, 'code_session') and self.code_session else "",
            parent=tab
        )
        layout.addWidget(self.vue_historique)
        return tab
    
    def _apply_main_frame_style(self, frame):
        """Applique le style au frame principal blanc"""
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame#MainWhiteFrame {{
                background: white;
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
        """)
    
    def _apply_tab_styles(self):
        """Applique les styles aux onglets"""
        from .styles import ExamenStyles
        self.tabs.setStyleSheet(ExamenStyles.tab_widget())


# ---------------------------------------------------------------------------
# Dialogs pour les Quick Actions
# ---------------------------------------------------------------------------

class _RechercheEntresDatesDialog(QDialog):
    """Recherche des examens entre deux dates."""

    def __init__(self, ctrl, code_session, parent=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.code_session = code_session
        self.resultats = []
        self._build()

    def _build(self):
        self.setWindowTitle("Recherche avancée — entre deux dates")
        self.setMinimumWidth(480)
        self.setModal(True)
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QDialog {{ background: {c['bg_main']}; }}
            QLabel {{ color: {c['text_primary']}; font-size: 13px; }}
            QDateEdit {{
                background: {c['bg_input']}; border: 1px solid {c['border']};
                border-radius: 8px; padding: 6px 12px;
                color: {c['text_primary']}; font-size: 13px; min-height: 32px;
            }}
            QDateEdit:focus {{ border-color: {c['primary']}; }}
            QPushButton#PrimaryBtn {{
                background: {c['primary']}; color: white; border: none;
                border-radius: 8px; padding: 8px 24px; font-weight: 700; font-size: 13px;
            }}
            QPushButton#PrimaryBtn:hover {{ background: {c['primary_hover']}; }}
            QPushButton#SecondaryBtn {{
                background: {c['bg_card']}; color: {c['text_primary']};
                border: 1px solid {c['border']}; border-radius: 8px;
                padding: 8px 20px; font-size: 13px;
            }}
            QPushButton#SecondaryBtn:hover {{ background: {c['hover']}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        layout.addWidget(QLabel("<b>Définir la plage de dates :</b>"))

        grid = QHBoxLayout()
        date_debut_lbl = QLabel("Du :")
        date_debut_lbl.setFixedWidth(40)
        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate().addMonths(-1))
        self.date_debut.setDisplayFormat("dd/MM/yyyy")

        date_fin_lbl = QLabel("Au :")
        date_fin_lbl.setFixedWidth(40)
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setDisplayFormat("dd/MM/yyyy")

        grid.addWidget(date_debut_lbl)
        grid.addWidget(self.date_debut, 1)
        grid.addSpacing(16)
        grid.addWidget(date_fin_lbl)
        grid.addWidget(self.date_fin, 1)
        layout.addLayout(grid)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(f"color: {c['text_secondary']}; font-size: 12px;")
        layout.addWidget(self.lbl_count)

        btns = QHBoxLayout()
        btn_annuler = QPushButton("Annuler")
        btn_annuler.setObjectName("SecondaryBtn")
        btn_annuler.clicked.connect(self.reject)
        btn_rechercher = QPushButton("Rechercher")
        btn_rechercher.setObjectName("PrimaryBtn")
        btn_rechercher.clicked.connect(self._rechercher)
        btns.addStretch()
        btns.addWidget(btn_annuler)
        btns.addWidget(btn_rechercher)
        layout.addLayout(btns)

    def _rechercher(self):
        from datetime import date
        d_debut = self.date_debut.date().toPython()
        d_fin   = self.date_fin.date().toPython()
        try:
            self.resultats = self.ctrl.rechercher_entre_dates(
                self.code_session, d_debut, d_fin
            ) or []
        except Exception:
            self.resultats = []
        self.lbl_count.setText(f"{len(self.resultats)} résultat(s) trouvé(s)")
        if self.resultats:
            self.accept()


class _ResumeSessionDialog(QDialog):
    """Rapport / résumé de la session courante."""

    def __init__(self, ctrl, code_session, parent=None):
        super().__init__(parent)
        self.ctrl = ctrl
        self.code_session = code_session
        self._build()

    def _build(self):
        self.setWindowTitle("Rapport de session")
        self.setMinimumWidth(480)
        self.setModal(True)
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QDialog {{ background: {c['bg_main']}; }}
            QLabel {{ color: {c['text_primary']}; font-size: 13px; }}
            QPushButton#SecondaryBtn {{
                background: {c['bg_card']}; color: {c['text_primary']};
                border: 1px solid {c['border']}; border-radius: 8px;
                padding: 8px 20px; font-size: 13px;
            }}
            QPushButton#SecondaryBtn:hover {{ background: {c['hover']}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        layout.addWidget(QLabel(f"<b>Session :</b> {self.code_session}"))

        try:
            resume = self.ctrl.obtenir_resume_session(self.code_session) or {}
        except Exception:
            resume = {}

        donnees = [
            ("Total examens (session)",   resume.get("total_examens", 0)),
            ("Examens aujourd'hui",        resume.get("examens_aujourd_hui", 0)),
            ("Examens en attente",         resume.get("en_attente", 0)),
            ("Patients distincts",         resume.get("patients_distincts", 0)),
            ("Revenu total (GNF)",         self._fmt_money(resume.get("revenu_total", 0))),
            ("Revenu aujourd'hui (GNF)",   self._fmt_money(resume.get("revenu_aujourd_hui", 0))),
            ("Moyenne / examen (GNF)",     self._fmt_money(resume.get("moyenne_par_examen", 0))),
        ]

        for libelle, valeur in donnees:
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0)
            lbl_lib = QLabel(libelle)
            lbl_lib.setStyleSheet(f"color: {c['text_secondary']}; font-size: 12px;")
            lbl_val = QLabel(str(valeur))
            lbl_val.setStyleSheet(f"color: {c['text_primary']}; font-size: 13px; font-weight: 700;")
            lbl_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_l.addWidget(lbl_lib)
            row_l.addStretch()
            row_l.addWidget(lbl_val)
            layout.addWidget(row_w)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {c['border']};")
        layout.addWidget(sep)

        # Top libellés
        try:
            tops = self.ctrl.obtenir_top_libelles(self.code_session, 5) or []
        except Exception:
            tops = []

        if tops:
            layout.addWidget(QLabel("<b>Top 5 libellés les plus fréquents :</b>"))
            for item in tops:
                lib  = item.get("libelle_examen", "-") if isinstance(item, dict) else str(item)
                nb   = item.get("nb", "") if isinstance(item, dict) else ""
                row_w = QWidget()
                row_l = QHBoxLayout(row_w)
                row_l.setContentsMargins(0, 0, 0, 0)
                row_l.addWidget(QLabel(f"• {lib}"))
                row_l.addStretch()
                if nb:
                    cnt = QLabel(f"{nb} fois")
                    cnt.setStyleSheet(f"color: {c['primary']}; font-weight: 700;")
                    row_l.addWidget(cnt)
                layout.addWidget(row_w)

        btns = QHBoxLayout()
        btn_fermer = QPushButton("Fermer")
        btn_fermer.setObjectName("SecondaryBtn")
        btn_fermer.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(btn_fermer)
        layout.addLayout(btns)

    @staticmethod
    def _fmt_money(val):
        try:
            return f"{float(val):,.0f}".replace(",", " ")
        except Exception:
            return str(val or 0)


