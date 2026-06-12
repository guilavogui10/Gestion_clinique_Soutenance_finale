import qtawesome as qta
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QLabel, QGraphicsDropShadowEffect, QStackedWidget,
    QLineEdit, QTextEdit, QComboBox, QScrollArea, QSizePolicy,
    QGridLayout, QFileDialog
)
from views.shared.theme_manager import theme_manager
from views.settings.settings_form import SettingsForm


class ParametreView(QWidget):

    session_changed = Signal(str)
    """
    Interface Paramètres du cabinet ophtalmologique.
    Layout : panel catégories (gauche) + contenu principal (droite).
    Architecture identique à AdminView (sidebar + stacked content).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._categorie_active = 0
        self._tab_active = 0
        self._init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # CONSTRUCTION PRINCIPALE
    # =========================================================================

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Panel catégories (gauche)
        self.categories_panel = self._creer_categories_panel()
        layout.addWidget(self.categories_panel, 0, Qt.AlignTop)

        # Zone de contenu (droite, stacked) dans un frame blanc arrondi
        self.content_frame = QFrame()
        self.content_frame.setObjectName("param_content_frame")
        c = theme_manager.colors()
        self.content_frame.setStyleSheet(f"""
            QFrame#param_content_frame {{
                background-color: {c['bg_card']};
                border-radius: 18px;
                border: 1px solid {c['border']};
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.content_frame.setGraphicsEffect(shadow)
        
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(0)
        
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("QStackedWidget { background-color: #FFFFFF; }")
        self._construire_pages()
        content_layout.addWidget(self.content_stack)
        
        layout.addWidget(self.content_frame, 1)

    # =========================================================================
    # PANEL CATÉGORIES (SIDEBAR COMPACTE — style identique à AdminView)
    # =========================================================================

    def _creer_categories_panel(self) -> QFrame:
        c = theme_manager.colors()

        panel = QFrame()
        panel.setFixedWidth(100)
        panel.setObjectName("param_categories_panel")
        panel.setStyleSheet(f"""
            QFrame#param_categories_panel {{
                background-color: {c['bg_card']};
                border-radius: 18px;
                border: 1px solid {c['border']};
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 30))
        panel.setGraphicsEffect(shadow)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(6)

        # Titre compact
        titre = QLabel("Paramètres")
        titre.setObjectName("param_cat_titre")
        titre.setAlignment(Qt.AlignCenter)
        titre.setStyleSheet(f"""
            color: {c['primary']};
            font-size: 10px;
            font-weight: 700;
            border: none;
        """)
        layout.addWidget(titre)
        layout.addSpacing(4)

        # Liste des catégories
        self._categories = [
            ("Général",       "fa5s.home"),
            ("Visite",        "fa5s.user-md"),
            ("Utilisateurs",  "fa5s.users"),
            ("Consultations", "fa5s.stethoscope"),
            ("Examens",       "fa5s.eye"),
            ("Pharmacie",     "fa5s.pills"),
            ("Paiements",     "fa5s.credit-card"),
            ("Rendez-vous",   "fa5s.calendar-alt"),
            ("Stats & KPI",   "fa5s.chart-bar"),
            ("Sécurité",      "fa5s.shield-alt"),
            ("Apparence",     "fa5s.paint-brush"),
            ("Session",       "fa5s.history"),
        ]

        self.cat_buttons = []
        for idx, (nom, icone) in enumerate(self._categories):
            btn = self._creer_bouton_categorie(nom, icone, idx == 0, idx)
            self.cat_buttons.append(btn)
            layout.addWidget(btn, 0, Qt.AlignCenter)

        layout.addStretch()
        return panel

    def _creer_bouton_categorie(self, texte: str, icone: str, actif: bool, index: int) -> QPushButton:
        """Bouton compact : texte en haut, icône en bas — identique à AdminView."""
        c = theme_manager.colors()

        btn = QPushButton()
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(76, 56)

        inner = QVBoxLayout(btn)
        inner.setContentsMargins(5, 8, 5, 8)
        inner.setSpacing(4)

        # Texte en HAUT
        lbl_texte = QLabel(texte)
        lbl_texte.setObjectName(f"cat_texte_{index}")
        lbl_texte.setAlignment(Qt.AlignCenter)
        lbl_texte.setWordWrap(True)
        lbl_texte.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 9px; font-weight: 600; "
            "border: none; background: transparent;"
        )

        # Icône en BAS
        couleur_icon = c['primary'] if not actif else c['primary']
        lbl_icon = QLabel()
        lbl_icon.setObjectName(f"cat_icon_{index}")
        lbl_icon.setPixmap(qta.icon(icone, color=couleur_icon).pixmap(QSize(22, 22)))
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_icon.setStyleSheet("border: none; background: transparent;")

        inner.addWidget(lbl_texte)
        inner.addWidget(lbl_icon)

        bg = c['hover'] if actif else "transparent"
        border_left = f"border-left: 3px solid {c['primary']};" if actif else "border-left: 3px solid transparent;"
        btn.setStyleSheet(self._style_bouton_cat(bg, border_left, c))

        btn.clicked.connect(lambda _, i=index: self._selectionner_categorie(i))
        return btn

    def _style_bouton_cat(self, bg: str, border_left: str, c: dict) -> str:
        return f"""
            QPushButton {{
                background-color: {bg};
                border: none;
                {border_left}
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {c['hover']};
            }}
        """

    def _selectionner_categorie(self, index: int):
        c = theme_manager.colors()
        self._categorie_active = index

        for i, (btn, (_, icone)) in enumerate(zip(self.cat_buttons, self._categories)):
            actif = (i == index)
            bg = c['hover'] if actif else "transparent"
            border_left = f"border-left: 3px solid {c['primary']};" if actif else "border-left: 3px solid transparent;"
            btn.setStyleSheet(self._style_bouton_cat(bg, border_left, c))

            lbl_icon  = btn.findChild(QLabel, f"cat_icon_{i}")
            lbl_texte = btn.findChild(QLabel, f"cat_texte_{i}")

            if lbl_icon:
                lbl_icon.setPixmap(qta.icon(icone, color=c['primary']).pixmap(QSize(22, 22)))
            if lbl_texte:
                lbl_texte.setStyleSheet(
                    f"color: {c['text_primary']}; font-size: 9px; font-weight: 600; "
                    "border: none; background: transparent;"
                )

        self.content_stack.setCurrentIndex(index)

    # =========================================================================
    # PAGES DE CONTENU
    # =========================================================================

    def _construire_pages(self):
        """Construit toutes les pages du stacked widget."""
        # Page 0: Général (avec formulaire complet)
        self.page_general = self._creer_page_general()
        self.content_stack.addWidget(self.page_general)
        
        # Page 1: Visite (paramètres de visite)
        from views.settings.settings_visite import SettingsVisite
        self.page_visite = SettingsVisite()
        self.content_stack.addWidget(self.page_visite)

        # Pages 2-11: placeholders pour les autres catégories
        placeholders = [
            ("fa5s.users",       "Utilisateurs & Rôles",  "Gérez les comptes et permissions des utilisateurs."),
            ("fa5s.stethoscope", "Consultations",          "Configurez les paramètres des consultations."),
            ("fa5s.eye",         "Examens",                "Paramètres des types d'examens ophtalmologiques."),
            ("fa5s.pills",       "Produits / Pharmacie",   "Gestion du stock et des produits pharmaceutiques."),
            ("fa5s.credit-card", "Paiements",              "Modes de paiement et paramètres de facturation."),
            ("fa5s.calendar-alt","Rendez-vous",            "Configuration des créneaux et rappels."),
            ("fa5s.chart-bar",   "Statistiques & KPI",     "Indicateurs clés de performance du cabinet."),
            ("fa5s.shield-alt",  "Sécurité & Sauvegarde",  "Sauvegardes automatiques et journaux de sécurité."),
            ("fa5s.paint-brush", "Interface & Apparence",  "Personnalisez l'apparence de l'application."),
        ]
        for icone, titre, sous_titre in placeholders:
            page = self._creer_page_placeholder(icone, titre, sous_titre)
            self.content_stack.addWidget(page)

        # Page 11 : Sélection de session
        self.page_session = self._creer_page_session()
        self.content_stack.addWidget(self.page_session)

    # =========================================================================
    # PAGE SESSION
    # =========================================================================

    def _creer_page_session(self) -> QWidget:
        """
        Page d'accès sécurisé à la sélection de session.
        Le Directeur Général s'authentifie via e-mail + OTP avant de choisir
        la session à consulter dans le tableau de bord et les analyses.
        """
        c = theme_manager.colors()
        page = QWidget()
        page.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(0)

        # ── Titre ────────────────────────────────────────────────────────────
        lbl_titre = QLabel("Sélection de session")
        lbl_titre.setStyleSheet(
            f"color: {c['primary']}; font-size: 16px; font-weight: 700; border: none; padding-bottom: 2px;"
        )
        layout.addWidget(lbl_titre)

        lbl_desc = QLabel(
            "Consultez les données d'une session passée. Cette action est réservée au "
            "Directeur Général et nécessite une vérification par code e-mail."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(
            f"color: {c['text_muted']}; font-size: 12px; border: none; padding-bottom: 10px;"
        )
        layout.addWidget(lbl_desc)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {c['border']}; border: none;")
        layout.addWidget(sep)
        layout.addSpacing(12)

        # ── Carte session active ─────────────────────────────────────────────
        card_active = QFrame()
        card_active.setObjectName("session_active_card")
        card_active.setStyleSheet(f"""
            QFrame#session_active_card {{
                background-color: {c['bg_card']};
                border-radius: 12px;
                border: 1px solid {c['border']};
            }}
        """)
        ca_layout = QVBoxLayout(card_active)
        ca_layout.setContentsMargins(16, 14, 16, 14)
        ca_layout.setSpacing(8)

        row_titre = QHBoxLayout()
        ic_hist = QLabel()
        ic_hist.setPixmap(qta.icon("fa5s.history", color=c['primary']).pixmap(QSize(16, 16)))
        ic_hist.setStyleSheet("border: none; background: transparent;")
        lbl_active_titre = QLabel("Session actuellement consultée")
        lbl_active_titre.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 13px; font-weight: 600; border: none;"
        )
        row_titre.addWidget(ic_hist)
        row_titre.addSpacing(6)
        row_titre.addWidget(lbl_active_titre)
        row_titre.addStretch()
        ca_layout.addLayout(row_titre)

        self._lbl_session_courante = QLabel("Session active (base de données)")
        self._lbl_session_courante.setObjectName("lbl_session_courante")
        self._lbl_session_courante.setStyleSheet(
            f"color: {c['primary']}; font-size: 14px; font-weight: 700; border: none; padding: 4px 0;"
        )
        ca_layout.addWidget(self._lbl_session_courante)

        self._lbl_session_info = QLabel("")
        self._lbl_session_info.setStyleSheet(
            f"color: {c['text_muted']}; font-size: 11px; border: none;"
        )
        self._lbl_session_info.hide()
        ca_layout.addWidget(self._lbl_session_info)

        layout.addWidget(card_active)
        layout.addSpacing(14)

        # ── Bouton Changer de session ────────────────────────────────────────
        self._btn_changer_session = QPushButton()
        self._btn_changer_session.setFixedHeight(42)
        self._btn_changer_session.setCursor(Qt.PointingHandCursor)
        self._btn_changer_session.setObjectName("btn_changer_session")
        bl = QHBoxLayout(self._btn_changer_session)
        bl.setContentsMargins(20, 0, 20, 0)
        bl.setSpacing(8)
        _ic_btn = QLabel()
        _ic_btn.setPixmap(qta.icon("fa5s.shield-alt", color="#FFFFFF").pixmap(QSize(14, 14)))
        _ic_btn.setStyleSheet("border: none; background: transparent;")
        _lbl_btn = QLabel("Changer de session (accès DG)")
        _lbl_btn.setStyleSheet(
            f"color: #FFFFFF; font-size: 13px; font-weight: 600; border: none; background: transparent;"
        )
        bl.addStretch()
        bl.addWidget(_ic_btn)
        bl.addWidget(_lbl_btn)
        bl.addStretch()
        self._btn_changer_session.setStyleSheet(f"""
            QPushButton#btn_changer_session {{
                background-color: {c['primary']};
                border: none;
                border-radius: 10px;
            }}
            QPushButton#btn_changer_session:hover {{
                background-color: {c.get('primary_dark', c['primary'])};
            }}
        """)
        self._btn_changer_session.clicked.connect(self._ouvrir_dialog_session)
        layout.addWidget(self._btn_changer_session)

        layout.addStretch()

        # Afficher la session courante au chargement
        self._maj_affichage_session_courante()

        return page

    def _maj_affichage_session_courante(self, code_session: str = ""):
        """Met à jour le label indiquant la session actuellement consultée."""
        from core import session_manager
        override = session_manager.get_override()
        if code_session:
            override = code_session
        if override:
            self._lbl_session_courante.setText(override)
            self._lbl_session_info.setText("Session sélectionnée par le Directeur Général")
            self._lbl_session_info.show()
        else:
            self._lbl_session_courante.setText("Session active (base de données)")
            self._lbl_session_info.hide()

    def _ouvrir_dialog_session(self):
        """Ouvre le modal d'autorisation DG → sélection de session."""
        from views.settings.dialog_autorisation_session import DialogAutorisationSession
        dlg = DialogAutorisationSession(self)
        dlg.session_confirmee.connect(self._on_session_confirmee)
        dlg.exec()

    def _on_session_confirmee(self, code_session: str):
        """Appelé quand le DG a validé son OTP et confirmé une session."""
        from core import session_manager
        session_manager.set_session_override(code_session)
        self._maj_affichage_session_courante(code_session)
        self.session_changed.emit(code_session)

    def rafraichir_sessions(self):
        """Rafraîchit l'indicateur de session (appelable depuis l'extérieur)."""
        if hasattr(self, '_lbl_session_courante'):
            self._maj_affichage_session_courante()

    # =========================================================================

    def _creer_page_placeholder(self, icone: str, titre: str, sous_titre: str) -> QWidget:
        c = theme_manager.colors()
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        lbl_icon = QLabel()
        lbl_icon.setPixmap(qta.icon(icone, color=c['text_muted']).pixmap(QSize(48, 48)))
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_icon.setStyleSheet("border: none;")

        lbl_titre = QLabel(titre)
        lbl_titre.setAlignment(Qt.AlignCenter)
        lbl_titre.setStyleSheet(f"color: {c['text_primary']}; font-size: 18px; font-weight: 700; border: none;")

        lbl_sub = QLabel(sous_titre)
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet(f"color: {c['text_muted']}; font-size: 13px; border: none;")

        layout.addWidget(lbl_icon)
        layout.addWidget(lbl_titre)
        layout.addWidget(lbl_sub)
        return page

    # =========================================================================
    # PAGE GÉNÉRAL
    # =========================================================================

    def _creer_page_general(self) -> QWidget:
        c = theme_manager.colors()

        page = QWidget()
        page.setStyleSheet("background-color: #FFFFFF;")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        # ── En-tête de page ──────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("param_header")
        header.setStyleSheet("QWidget#param_header { border: none; background-color: #FFFFFF; }")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 4)  # réduit de 8 → 4
        h_layout.setSpacing(0)

        lbl_titre = QLabel("Paramètres généraux du cabinet")
        lbl_titre.setObjectName("param_page_titre")
        lbl_titre.setStyleSheet(
            f"color: {c['primary']}; font-size: 16px; font-weight: 700; border: none;"  # 18→16px
        )

        h_layout.addWidget(lbl_titre)
        page_layout.addWidget(header)

        # ── Barre d'onglets ──────────────────────────────────────────────────
        self.tabs_bar = self._creer_tabs_bar()
        page_layout.addWidget(self.tabs_bar)

        # ── Contenu des onglets ──────────────────────────────────────────────
        self.tabs_stack = QStackedWidget()

        tab_informations = self._creer_tab_informations()
        self.tabs_stack.addWidget(tab_informations)

        for nom, icone in [("Localisation", "fa5s.map-marker-alt"),
                            ("Préférences",  "fa5s.cog"),
                            ("Documents",    "fa5s.file-alt")]:
            self.tabs_stack.addWidget(self._creer_tab_placeholder_simple(nom, icone))

        page_layout.addWidget(self.tabs_stack, 1)
        return page

    # ── BARRE D'ONGLETS ───────────────────────────────────────────────────────

    def _creer_tabs_bar(self) -> QFrame:
        c = theme_manager.colors()

        bar = QFrame()
        bar.setObjectName("param_tabs_bar")
        bar.setFixedHeight(40)  # 48 → 40
        bar.setStyleSheet(f"""
            QFrame#param_tabs_bar {{
                border: none;
                border-bottom: 1.5px solid {c['border']};
                background-color: #FFFFFF;
            }}
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tabs_info = [
            ("Informations", "fa5s.info-circle"),
            ("Localisation",  "fa5s.map-marker-alt"),
            ("Préférences",   "fa5s.cog"),
            ("Documents",     "fa5s.file-alt"),
        ]

        self.tab_buttons = []
        for i, (nom, icone) in enumerate(self._tabs_info):
            btn = self._creer_bouton_tab(nom, icone, i == 0, i)
            self.tab_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()
        return bar

    def _creer_bouton_tab(self, texte: str, icone: str, actif: bool, index: int) -> QPushButton:
        c = theme_manager.colors()

        btn = QPushButton()
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(40)  # 48 → 40
        btn.setMinimumWidth(120)
        btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        inner = QHBoxLayout(btn)
        inner.setContentsMargins(16, 0, 16, 0)
        inner.setSpacing(7)

        ic = c['primary'] if actif else c['text_secondary']
        lbl_icon = QLabel()
        lbl_icon.setObjectName(f"tab_icon_{index}")
        lbl_icon.setPixmap(qta.icon(icone, color=ic).pixmap(QSize(14, 14)))
        lbl_icon.setStyleSheet("border: none; background: transparent;")
        lbl_icon.setAttribute(Qt.WA_TransparentForMouseEvents)

        lbl_texte = QLabel(texte)
        lbl_texte.setObjectName(f"tab_texte_{index}")
        tc = c['primary'] if actif else c['text_secondary']
        lbl_texte.setStyleSheet(
            f"color: {tc}; font-size: 13px; "
            f"font-weight: {'700' if actif else '500'}; "
            "border: none; background: transparent;"
        )
        lbl_texte.setAttribute(Qt.WA_TransparentForMouseEvents)

        inner.addWidget(lbl_icon)
        inner.addWidget(lbl_texte)

        border = f"border-bottom: 3px solid {c['primary']};" if actif else "border-bottom: 3px solid transparent;"
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                border: none;
                {border}
                border-radius: 0px;
            }}
            QPushButton:hover {{
                background-color: {c['hover']};
            }}
        """)

        btn.clicked.connect(lambda _, i=index: self._selectionner_tab(i))
        return btn

    def _selectionner_tab(self, index: int):
        c = theme_manager.colors()
        self._tab_active = index

        for i, (btn, (_, icone)) in enumerate(zip(self.tab_buttons, self._tabs_info)):
            actif = (i == index)
            ic = c['primary'] if actif else c['text_secondary']
            tc = c['primary'] if actif else c['text_secondary']
            poids = "700" if actif else "500"
            border = f"border-bottom: 3px solid {c['primary']};" if actif else "border-bottom: 3px solid transparent;"

            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FFFFFF;
                    border: none;
                    {border}
                    border-radius: 0px;
                }}
                QPushButton:hover {{ background-color: {c['hover']}; }}
            """)

            lbl_icon  = btn.findChild(QLabel, f"tab_icon_{i}")
            lbl_texte = btn.findChild(QLabel, f"tab_texte_{i}")
            if lbl_icon:
                lbl_icon.setPixmap(qta.icon(icone, color=ic).pixmap(QSize(14, 14)))
            if lbl_texte:
                lbl_texte.setStyleSheet(
                    f"color: {tc}; font-size: 13px; font-weight: {poids}; "
                    "border: none; background: transparent;"
                )

        self.tabs_stack.setCurrentIndex(index)

    def _creer_tab_informations(self) -> QWidget:
        """Onglet Informations : utilise le formulaire séparé SettingsForm."""
        # Retourne directement le formulaire
        return SettingsForm()

    def _creer_boutons_action(self) -> QHBoxLayout:
        c = theme_manager.colors()
        layout = QHBoxLayout()
        layout.addStretch()

        # Annuler
        self.btn_annuler = QPushButton()
        self.btn_annuler.setCursor(Qt.PointingHandCursor)
        self.btn_annuler.setFixedHeight(32)     # 38 → 32
        al = QHBoxLayout(self.btn_annuler)
        al.setContentsMargins(16, 0, 16, 0)
        al.setSpacing(7)
        _icon_x = QLabel()
        _icon_x.setPixmap(qta.icon("fa5s.times", color=c['text_primary']).pixmap(QSize(12, 12)))
        _icon_x.setStyleSheet("border: none; background: transparent;")
        _lbl_a = QLabel("Annuler")
        _lbl_a.setObjectName("btn_annuler_lbl")
        _lbl_a.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 13px; font-weight: 500; "
            "border: none; background: transparent;"
        )
        al.addWidget(_icon_x); al.addWidget(_lbl_a)
        self.btn_annuler.setObjectName("btn_annuler")
        self.btn_annuler.setStyleSheet(f"""
            QPushButton#btn_annuler {{
                background-color: #FFFFFF;
                border: 1px solid {c['border']};
                border-radius: 10px;
            }}
            QPushButton#btn_annuler:hover {{
                background-color: {c['hover']};
            }}
        """)

        # Enregistrer
        self.btn_enregistrer = QPushButton()
        self.btn_enregistrer.setCursor(Qt.PointingHandCursor)
        self.btn_enregistrer.setFixedHeight(32)  # 38 → 32
        el = QHBoxLayout(self.btn_enregistrer)
        el.setContentsMargins(20, 0, 20, 0)
        el.setSpacing(7)
        _icon_s = QLabel()
        _icon_s.setPixmap(qta.icon("fa5s.save", color=c['text_inverse']).pixmap(QSize(12, 12)))
        _icon_s.setStyleSheet("border: none; background: transparent;")
        _lbl_e = QLabel("Enregistrer")
        _lbl_e.setObjectName("btn_enreg_lbl")
        _lbl_e.setStyleSheet(
            f"color: {c['text_inverse']}; font-size: 13px; font-weight: 600; "
            "border: none; background: transparent;"
        )
        el.addWidget(_icon_s); el.addWidget(_lbl_e)
        self.btn_enregistrer.setObjectName("btn_enregistrer")
        self.btn_enregistrer.setStyleSheet(f"""
            QPushButton#btn_enregistrer {{
                background-color: {c['primary']};
                border: none;
                border-radius: 10px;
            }}
            QPushButton#btn_enregistrer:hover {{
                opacity: 0.9;
            }}
        """)

        layout.addWidget(self.btn_annuler)
        layout.addSpacing(10)
        layout.addWidget(self.btn_enregistrer)
        return layout

    # ── PANEL APERÇU ──────────────────────────────────────────────────────────

    def _creer_apercu_panel(self) -> QFrame:
        c = theme_manager.colors()

        frame = QFrame()
        frame.setMinimumWidth(240)
        frame.setObjectName("param_apercu")
        frame.setStyleSheet(f"""
            QFrame#param_apercu {{
                background-color: {c['bg_card']};
                border-radius: 16px;
                border: 1px solid {c['border']};
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 25))
        frame.setGraphicsEffect(shadow)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)   # 18 → 14
        layout.setSpacing(8)                         # 12 → 8

        # Titre
        lbl_apercu = QLabel("Aperçu")
        lbl_apercu.setObjectName("apercu_titre")
        lbl_apercu.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 15px; font-weight: 700; border: none;"  # 14→15
        )
        layout.addWidget(lbl_apercu)

        # Logo preview
        logo_frame = QFrame()
        logo_frame.setFixedHeight(85)               # 95 → 85
        logo_frame.setObjectName("apercu_logo_frame")
        logo_frame.setStyleSheet(f"""
            QFrame#apercu_logo_frame {{
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid {c['border']};
            }}
        """)
        lf_layout = QVBoxLayout(logo_frame)
        lf_layout.setAlignment(Qt.AlignCenter)
        lf_layout.setSpacing(3)

        lbl_eye = QLabel()
        lbl_eye.setPixmap(qta.icon("fa5s.eye", color=c['primary']).pixmap(QSize(28, 28)))  # 32→28
        lbl_eye.setAlignment(Qt.AlignCenter)
        lbl_eye.setStyleSheet("border: none; background: transparent;")

        lbl_vp = QLabel("VISION PLUS")
        lbl_vp.setAlignment(Qt.AlignCenter)
        lbl_vp.setStyleSheet(
            f"color: {c['primary']}; font-size: 13px; font-weight: 800; "   # 10→13px
            "border: none; background: transparent;"
        )

        lbl_cab = QLabel("CABINET OPHTALMOLOGIQUE")
        lbl_cab.setAlignment(Qt.AlignCenter)
        lbl_cab.setStyleSheet(
            f"color: {c['text_muted']}; font-size: 9px; "                   # 7→9px
            "border: none; background: transparent;"
        )

        lf_layout.addWidget(lbl_eye)
        lf_layout.addWidget(lbl_vp)
        lf_layout.addWidget(lbl_cab)
        layout.addWidget(logo_frame)

        # Séparateur
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setObjectName("apercu_sep")
        sep.setStyleSheet(f"background: {c['border']}; border: none;")
        layout.addWidget(sep)

        # Champs d'aperçu
        apercu_data = [
            ("Nom",               "Cabinet Ophtalmologique Vision Plus"),
            ("Téléphone",         "+224 612 34 56 78"),
            ("Email",             "contact@visionplus.com"),
            ("Devise",            "GNF - Franc guinéen"),
            ("Langue",            "Français"),
            ("Fuseau horaire",    "Afrique/Conakry"),
            ("Exercice comptable","01/01 - 31/12"),
        ]

        for cle, val in apercu_data:
            row_w = QWidget()
            row_w.setStyleSheet("background-color: #FFFFFF;")
            row_l = QVBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.setSpacing(1)

            lbl_cle = QLabel(cle)
            lbl_cle.setStyleSheet(
                f"color: {c['text_muted']}; font-size: 11px; font-weight: 600; border: none;"  # 9→11px
            )

            lbl_val = QLabel(val)
            lbl_val.setWordWrap(True)
            lbl_val.setStyleSheet(
                f"color: {c['text_primary']}; font-size: 12px; border: none;"  # 10→12px
            )

            row_l.addWidget(lbl_cle)
            row_l.addWidget(lbl_val)
            layout.addWidget(row_w)

        layout.addSpacing(4)

        # Bouton Modifier
        self.btn_modifier_apercu = QPushButton()
        self.btn_modifier_apercu.setCursor(Qt.PointingHandCursor)
        self.btn_modifier_apercu.setFixedHeight(36)
        self.btn_modifier_apercu.setObjectName("btn_modifier_apercu")
        ml = QHBoxLayout(self.btn_modifier_apercu)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(6)
        ml.addStretch()
        lbl_m_icon = QLabel()
        lbl_m_icon.setPixmap(qta.icon("fa5s.pen", color=c['primary']).pixmap(QSize(11, 11)))
        lbl_m_icon.setStyleSheet("border: none; background: transparent;")
        lbl_m = QLabel("Modifier")
        lbl_m.setStyleSheet(
            f"color: {c['primary']}; font-size: 13px; font-weight: 600; "  # 12→13px
            "border: none; background: transparent;"
        )
        ml.addWidget(lbl_m_icon)
        ml.addWidget(lbl_m)
        ml.addStretch()
        self.btn_modifier_apercu.setStyleSheet(f"""
            QPushButton#btn_modifier_apercu {{
                background-color: #FFFFFF;
                border: 1px solid {c['border']};
                border-radius: 8px;
            }}
            QPushButton#btn_modifier_apercu:hover {{
                background-color: {c['hover']};
            }}
        """)
        layout.addWidget(self.btn_modifier_apercu)

        return frame

    # ── ONGLET PLACEHOLDER ────────────────────────────────────────────────────

    def _creer_tab_placeholder_simple(self, nom: str, icone: str) -> QWidget:
        c = theme_manager.colors()
        w = QWidget()
        w.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        lbl_ic = QLabel()
        lbl_ic.setPixmap(qta.icon(icone, color=c['text_muted']).pixmap(QSize(40, 40)))
        lbl_ic.setAlignment(Qt.AlignCenter)
        lbl_ic.setStyleSheet("border: none;")

        lbl_nom = QLabel(nom)
        lbl_nom.setAlignment(Qt.AlignCenter)
        lbl_nom.setStyleSheet(f"color: {c['text_muted']}; font-size: 15px; border: none;")

        layout.addWidget(lbl_ic)
        layout.addWidget(lbl_nom)
        return w

    # ── WIDGETS UTILITAIRES ───────────────────────────────────────────────────

    def _creer_logo_widget(self) -> QWidget:
        c = theme_manager.colors()

        w = QWidget()
        w.setStyleSheet("background-color: #FFFFFF;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Preview
        preview = QFrame()
        preview.setFixedSize(80, 68)
        preview.setObjectName("logo_preview_frame")
        preview.setStyleSheet(f"""
            QFrame#logo_preview_frame {{
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid {c['border']};
            }}
        """)
        pl = QVBoxLayout(preview)
        pl.setAlignment(Qt.AlignCenter)
        pl.setSpacing(2)

        lbl_eye2 = QLabel()
        lbl_eye2.setPixmap(qta.icon("fa5s.eye", color=c['primary']).pixmap(QSize(22, 22)))
        lbl_eye2.setAlignment(Qt.AlignCenter)
        lbl_eye2.setStyleSheet("border: none; background: transparent;")

        lbl_vp2 = QLabel("VISION PLUS")
        lbl_vp2.setAlignment(Qt.AlignCenter)
        lbl_vp2.setStyleSheet(
            f"color: {c['primary']}; font-size: 6px; font-weight: 700; "
            "border: none; background: transparent;"
        )

        pl.addWidget(lbl_eye2)
        pl.addWidget(lbl_vp2)

        # Droite
        right = QWidget()
        right.setStyleSheet("background-color: #FFFFFF;")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(5)

        self.btn_changer_logo = QPushButton()
        self.btn_changer_logo.setCursor(Qt.PointingHandCursor)
        self.btn_changer_logo.setFixedHeight(30)    # 34 → 30
        bll = QHBoxLayout(self.btn_changer_logo)
        bll.setContentsMargins(10, 0, 10, 0)
        bll.setSpacing(6)
        _ic_up = QLabel()
        _ic_up.setPixmap(qta.icon("fa5s.upload", color=c['primary']).pixmap(QSize(11, 11)))
        _ic_up.setStyleSheet("border: none; background: transparent;")
        _lbl_up = QLabel("Changer le logo")
        _lbl_up.setStyleSheet(
            f"color: {c['primary']}; font-size: 11px; font-weight: 600; "
            "border: none; background: transparent;"
        )
        bll.addWidget(_ic_up); bll.addWidget(_lbl_up)
        self.btn_changer_logo.setObjectName("btn_changer_logo")
        self.btn_changer_logo.setStyleSheet(f"""
            QPushButton#btn_changer_logo {{
                background-color: #FFFFFF;
                border: 1px solid {c['primary']};
                border-radius: 7px;
            }}
            QPushButton#btn_changer_logo:hover {{
                background-color: {c['hover']};
            }}
        """)
        self.btn_changer_logo.clicked.connect(self._choisir_logo)

        lbl_fmt = QLabel("Formats acceptés : PNG, JPG")
        lbl_fmt.setStyleSheet(f"color: {c['text_muted']}; font-size: 10px; border: none;")
        lbl_size = QLabel("Taille max : 2 Mo")
        lbl_size.setStyleSheet(f"color: {c['text_muted']}; font-size: 10px; border: none;")

        rl.addWidget(self.btn_changer_logo)
        rl.addWidget(lbl_fmt)
        rl.addWidget(lbl_size)

        layout.addWidget(preview)
        layout.addWidget(right)
        layout.addStretch()
        return w

    def _creer_date_input(self, valeur: str) -> QWidget:
        c = theme_manager.colors()
        w = QWidget()
        w.setStyleSheet("background-color: #FFFFFF;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        inp = QLineEdit(valeur)
        inp.setFixedHeight(28)   # 34 → 28
        inp.setStyleSheet(f"""
            QLineEdit {{
                background-color: #FFFFFF;
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                border-top-left-radius: 8px;
                border-bottom-left-radius: 8px;
                padding: 0 12px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {c['primary']};
            }}
        """)

        btn_cal = QPushButton()
        btn_cal.setFixedSize(28, 28)    # 34 → 28
        btn_cal.setCursor(Qt.PointingHandCursor)
        btn_cal.setIcon(qta.icon("fa5s.calendar-alt", color=c['text_muted']))
        btn_cal.setIconSize(QSize(13, 13))
        btn_cal.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                border: 1px solid {c['border']};
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {c['hover']};
            }}
        """)

        layout.addWidget(inp, 1)
        layout.addWidget(btn_cal)
        return w

    def _choisir_logo(self):
        """Ouvre un sélecteur de fichier pour changer le logo."""
        fichier, _ = QFileDialog.getOpenFileName(
            self, "Choisir un logo", "",
            "Images (*.png *.jpg *.jpeg)"
        )
        if fichier:
            print(f"[ParametreView] Logo sélectionné : {fichier}")

    # ── HELPERS CSS / WIDGETS ─────────────────────────────────────────────────

    def _mk_label(self, texte: str) -> QLabel:
        c = theme_manager.colors()
        lbl = QLabel(texte)
        lbl.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 11px; font-weight: 600; border: none;"  # 12→11px
        )
        return lbl

    def _mk_input(self, valeur: str = "") -> QLineEdit:
        inp = QLineEdit(valeur)
        inp.setFixedHeight(28)   # 34 → 28
        inp.setStyleSheet(self._css_input())
        return inp

    def _mk_combo(self, options: list) -> QComboBox:
        c = theme_manager.colors()
        cb = QComboBox()
        cb.addItems(options)
        cb.setFixedHeight(28)   # 34 → 28
        cb.setStyleSheet(f"""
            QComboBox {{
                background-color: #FFFFFF;
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 0 12px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 26px;
                subcontrol-origin: padding;
                subcontrol-position: center right;
            }}
            QComboBox QAbstractItemView {{
                background-color: #FFFFFF;
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                outline: none;
                selection-background-color: {c['primary']};
                selection-color: {c['text_inverse']};
                padding: 4px;
            }}
        """)
        return cb

    def _css_input(self) -> str:
        c = theme_manager.colors()
        return f"""
            QLineEdit, QTextEdit {{
                background-color: #FFFFFF;
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 1.5px solid {c['primary']};
            }}
        """

    @staticmethod
    def _vspace(h: int):
        from PySide6.QtWidgets import QSpacerItem, QSizePolicy
        return QSpacerItem(0, h, QSizePolicy.Minimum, QSizePolicy.Fixed)

    # =========================================================================
    # APPLICATION DU THÈME
    # =========================================================================

    def apply_theme(self):
        """Ré-applique les couleurs sur tous les composants."""
        c = theme_manager.colors()

        # Panel catégories
        self.categories_panel.setStyleSheet(f"""
            QFrame#param_categories_panel {{
                background-color: {c['bg_card']};
                border-radius: 18px;
                border: 1px solid {c['border']};
            }}
        """)
        
        # Content frame
        if hasattr(self, 'content_frame'):
            self.content_frame.setStyleSheet(f"""
                QFrame#param_content_frame {{
                    background-color: {c['bg_card']};
                    border-radius: 18px;
                    border: 1px solid {c['border']};
                }}
            """)

        # Titre compact
        for lbl in self.categories_panel.findChildren(QLabel):
            if lbl.objectName() == "param_cat_titre":
                lbl.setStyleSheet(
                    f"color: {c['primary']}; font-size: 10px; font-weight: 700; border: none;"
                )
                break

        # Boutons catégories (style compact)
        for i, (btn, (_, icone)) in enumerate(zip(self.cat_buttons, self._categories)):
            actif = (i == self._categorie_active)
            bg = c['hover'] if actif else "transparent"
            border_left = f"border-left: 3px solid {c['primary']};" if actif else "border-left: 3px solid transparent;"
            btn.setStyleSheet(self._style_bouton_cat(bg, border_left, c))
            lbl_icon  = btn.findChild(QLabel, f"cat_icon_{i}")
            lbl_texte = btn.findChild(QLabel, f"cat_texte_{i}")
            if lbl_icon:
                lbl_icon.setPixmap(qta.icon(icone, color=c['primary']).pixmap(QSize(22, 22)))
            if lbl_texte:
                lbl_texte.setStyleSheet(
                    f"color: {c['text_primary']}; font-size: 9px; font-weight: 600; "
                    "border: none; background: transparent;"
                )

        # Tabs bar
        self.tabs_bar.setStyleSheet(f"""
            QFrame#param_tabs_bar {{
                border: none;
                border-bottom: 1.5px solid {c['border']};
                background-color: #FFFFFF;
            }}
        """)

        # Tab buttons
        for i, (btn, (_, icone)) in enumerate(zip(self.tab_buttons, self._tabs_info)):
            actif = (i == self._tab_active)
            border = f"border-bottom: 3px solid {c['primary']};" if actif else "border-bottom: 3px solid transparent;"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FFFFFF;
                    border: none;
                    {border}
                    border-radius: 0px;
                }}
                QPushButton:hover {{ background-color: {c['hover']}; }}
            """)
            lbl_icon  = btn.findChild(QLabel, f"tab_icon_{i}")
            lbl_texte = btn.findChild(QLabel, f"tab_texte_{i}")
            ic = c['primary'] if actif else c['text_secondary']
            tc = c['primary'] if actif else c['text_secondary']
            if lbl_icon:
                lbl_icon.setPixmap(qta.icon(icone, color=ic).pixmap(QSize(14, 14)))
            if lbl_texte:
                lbl_texte.setStyleSheet(
                    f"color: {tc}; font-size: 13px; "
                    f"font-weight: {'700' if actif else '500'}; "
                    "border: none; background: transparent;"
                )

        # Aperçu panel
        if hasattr(self, 'apercu_panel'):
            self.apercu_panel.setStyleSheet(f"""
                QFrame#param_apercu {{
                    background-color: {c['bg_card']};
                    border-radius: 16px;
                    border: 1px solid {c['border']};
                }}
            """)

        # Inputs — toujours blanc
        for inp in self.findChildren(QLineEdit):
            inp.setStyleSheet(self._css_input())
        for ta in self.findChildren(QTextEdit):
            ta.setStyleSheet(self._css_input())

        # Combos — toujours blanc
        for cb in self.findChildren(QComboBox):
            cb.setStyleSheet(f"""
                QComboBox {{
                    background-color: #FFFFFF;
                    color: {c['text_primary']};
                    border: 1px solid {c['border']};
                    border-radius: 8px;
                    padding: 0 12px;
                    font-size: 12px;
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 26px;
                    subcontrol-origin: padding;
                    subcontrol-position: center right;
                }}
                QComboBox QAbstractItemView {{
                    background-color: #ffffff;
                    color: {c['text_primary']};
                    border: 1px solid {c['border']};
                    selection-background-color: {c['primary']};
                    selection-color: {c['text_inverse']};
                }}
            """)

    def rafraichir(self):
        """Rafraîchit les données depuis la source."""
        pass