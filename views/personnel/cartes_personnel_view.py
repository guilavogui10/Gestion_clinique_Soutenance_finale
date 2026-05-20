"""
Vue cartes personnel - affichage en grille des cartes membres
"""
import os
import qtawesome as qta
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QScrollArea, QGridLayout, QPushButton, QFileDialog,
    QGraphicsDropShadowEffect
)
from PySide6.QtGui import QColor
from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox


class CarteMembreWidget(QFrame):
    """Widget représentant une carte membre individuelle"""
    
    generer_pdf_clicked = Signal(object)
    
    def __init__(self, personnel, ctrl, parent=None):
        super().__init__(parent)
        self.personnel = personnel
        self.ctrl = ctrl
        self._setup_shadow()
        self._init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def _setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 45))
        self.setGraphicsEffect(shadow)
    
    def enterEvent(self, event):
        shadow = self.graphicsEffect()
        if shadow:
            shadow.setBlurRadius(28)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        shadow = self.graphicsEffect()
        if shadow:
            shadow.setBlurRadius(18)
        super().leaveEvent(event)
    
    def _init_ui(self):
        self.setFixedSize(280, 380)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header avec fond blanc
        header = QFrame()
        header.setFixedHeight(100)
        header.setObjectName("CardHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(4)
        
        # Titre carte
        lbl_titre = QLabel("CARTE DE MEMBRE")
        lbl_titre.setAlignment(Qt.AlignCenter)
        lbl_titre.setObjectName("CardTitle")
        header_layout.addWidget(lbl_titre)
        
        # Code
        code = self.personnel.get("code", "")
        lbl_code = QLabel(code)
        lbl_code.setAlignment(Qt.AlignCenter)
        lbl_code.setObjectName("CardCode")
        header_layout.addWidget(lbl_code)
        
        main_layout.addWidget(header)
        
        # Corps de la carte
        body = QFrame()
        body.setObjectName("CardBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(14, 14, 14, 14)
        body_layout.setSpacing(10)
        
        # Photo
        photo_frame = QFrame()
        photo_frame.setFixedSize(100, 120)
        photo_frame.setObjectName("PhotoFrame")
        photo_layout = QVBoxLayout(photo_frame)
        photo_layout.setContentsMargins(4, 4, 4, 4)
        
        photo_lbl = QLabel()
        photo_lbl.setAlignment(Qt.AlignCenter)
        photo_lbl.setFixedSize(90, 110)
        photo_path = self._get_photo_path()
        if photo_path:
            photo_lbl.setPixmap(QPixmap(photo_path).scaled(
                90, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        else:
            c = theme_manager.colors()
            photo_lbl.setPixmap(qta.icon("fa5s.user-circle", color=c['text_muted']).pixmap(50, 50))
        photo_layout.addWidget(photo_lbl)
        
        body_layout.addWidget(photo_frame, 0, Qt.AlignCenter)
        
        # Nom complet
        nom_complet = f"{self.personnel.get('nom', '')} {self.personnel.get('prenom', '')}".strip().upper()
        lbl_nom = QLabel(nom_complet or "INCONNU")
        lbl_nom.setWordWrap(True)
        lbl_nom.setAlignment(Qt.AlignCenter)
        lbl_nom.setObjectName("CardNom")
        body_layout.addWidget(lbl_nom)
        
        # Fonction
        fonction = self.personnel.get("fonction", "")
        lbl_fonction = QLabel(fonction)
        lbl_fonction.setWordWrap(True)
        lbl_fonction.setAlignment(Qt.AlignCenter)
        lbl_fonction.setObjectName("CardFonction")
        body_layout.addWidget(lbl_fonction)
        
        # Séparateur
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setObjectName("CardSeparator")
        body_layout.addWidget(sep)
        
        # Contact avec icône Font Awesome
        contact_layout = QHBoxLayout()
        contact_layout.setSpacing(6)
        contact_layout.setAlignment(Qt.AlignCenter)
        
        contact_icon = QLabel()
        contact_icon.setFixedSize(14, 14)
        contact_icon.setStyleSheet("border: none; background: transparent;")
        self._contact_icon = contact_icon
        
        contact = self.personnel.get("contact", "")
        lbl_contact = QLabel(contact)
        lbl_contact.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lbl_contact.setObjectName("CardContact")
        
        contact_layout.addWidget(contact_icon)
        contact_layout.addWidget(lbl_contact)
        body_layout.addLayout(contact_layout)
        
        # Email avec icône Font Awesome
        email_layout = QHBoxLayout()
        email_layout.setSpacing(6)
        email_layout.setAlignment(Qt.AlignCenter)
        
        email_icon = QLabel()
        email_icon.setFixedSize(14, 14)
        email_icon.setStyleSheet("border: none; background: transparent;")
        self._email_icon = email_icon
        
        email = self.personnel.get("mail", "")
        lbl_email = QLabel(email)
        lbl_email.setWordWrap(True)
        lbl_email.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lbl_email.setObjectName("CardEmail")
        
        email_layout.addWidget(email_icon)
        email_layout.addWidget(lbl_email)
        body_layout.addLayout(email_layout)
        
        body_layout.addStretch()
        
        # Bouton générer PDF
        btn_pdf = QPushButton(qta.icon("fa5s.file-pdf", color="white"), " Générer PDF")
        btn_pdf.setFixedHeight(36)
        btn_pdf.setCursor(Qt.PointingHandCursor)
        btn_pdf.setObjectName("BtnPdf")
        btn_pdf.clicked.connect(lambda: self.generer_pdf_clicked.emit(self.personnel))
        body_layout.addWidget(btn_pdf)
        
        main_layout.addWidget(body)
    
    def _get_photo_path(self):
        photo_name = self.personnel.get("photo_path")
        if not photo_name:
            return None
        script_dir = os.path.dirname(__file__)
        photo_path = os.path.normpath(
            os.path.join(script_dir, "..", "..", "connexion", "image", photo_name)
        )
        return photo_path if os.path.exists(photo_path) else None
    
    def apply_theme(self):
        c = theme_manager.colors()
        
        # Mettre à jour les icônes
        if hasattr(self, '_contact_icon'):
            self._contact_icon.setPixmap(qta.icon("fa5s.phone", color=c["text_secondary"]).pixmap(14, 14))
        if hasattr(self, '_email_icon'):
            self._email_icon.setPixmap(qta.icon("fa5s.envelope", color=c["text_secondary"]).pixmap(14, 14))
        
        self.setStyleSheet(f"""
            QFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
            QFrame#CardHeader {{
                background: white;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border: none;
            }}
            QLabel#CardTitle {{
                color: #2ecc71;
                font-size: 14px;
                font-weight: 900;
                letter-spacing: 0.5px;
                background: transparent;
                border: none;
            }}
            QLabel#CardCode {{
                color: #e74c3c;
                font-size: 11px;
                font-weight: 800;
                background: transparent;
                border: none;
            }}
            QFrame#CardBody {{
                background: {c['bg_card']};
                border: none;
            }}
            QFrame#PhotoFrame {{
                background: {c['bg_main']};
                border: 2px solid {c['primary']};
                border-radius: 12px;
            }}
            QLabel#CardNom {{
                color: {c['text_primary']};
                font-size: 13px;
                font-weight: 900;
                background: transparent;
                border: none;
            }}
            QLabel#CardFonction {{
                color: {c['primary']};
                font-size: 11px;
                font-weight: 800;
                background: transparent;
                border: none;
            }}
            QFrame#CardSeparator {{
                background: {c['border_light']};
                border: none;
            }}
            QLabel#CardContact, QLabel#CardEmail {{
                color: {c['text_secondary']};
                font-size: 11px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
            QPushButton#BtnPdf {{
                background: {c['danger']};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton#BtnPdf:hover {{
                background: {c['primary']};
            }}
        """)


class CartesPersonnelView(QWidget):
    """Vue pour afficher les cartes membres du personnel en grille"""
    
    def __init__(self, controleur, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.personnel_actuel = None
        
        self._init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 12, 20, 12)
        main_layout.setSpacing(12)
        
        # Header avec sélection personnel
        self._setup_header(main_layout)
        
        # Scroll area pour les cartes
        self._setup_cards_area(main_layout)
    
    def _setup_header(self, parent_layout):
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)
        
        # Icône + titre
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(24, 24)
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        self._header_icon = icon_lbl
        
        title_lbl = QLabel("Cartes Membres du Personnel")
        title_lbl.setObjectName("HeaderTitle")
        self._header_title = title_lbl
        
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        
        # Combo sélection personnel
        self.combo_personnel = QComboBox()
        self.combo_personnel.setObjectName("PersonnelCombo")
        self.combo_personnel.setFixedHeight(40)
        self.combo_personnel.setMinimumWidth(300)
        self.combo_personnel.addItem("-- Tous les personnels --", None)
        self.combo_personnel.currentIndexChanged.connect(self._on_personnel_changed)
        header_layout.addWidget(self.combo_personnel)
        
        parent_layout.addWidget(header_frame)
    
    def _setup_cards_area(self, parent_layout):
        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setObjectName("CardsScroll")
        
        # Container pour les cartes
        self.cards_container = QWidget()
        self.cards_container.setObjectName("CardsContainer")
        self.grid_layout = QGridLayout(self.cards_container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        
        self.scroll.setWidget(self.cards_container)
        parent_layout.addWidget(self.scroll, 1)
        
        # Message vide
        self.empty_widget = self._build_empty_state()
        parent_layout.addWidget(self.empty_widget)
        self.empty_widget.hide()
    
    def _build_empty_state(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)
        
        self._empty_icon = QLabel()
        self._empty_icon.setAlignment(Qt.AlignCenter)
        self._empty_icon.setStyleSheet("border: none; background: transparent;")
        
        self._empty_msg = QLabel("Aucun personnel enregistré.")
        self._empty_msg.setAlignment(Qt.AlignCenter)
        self._empty_msg.setWordWrap(True)
        self._empty_msg.setStyleSheet("border: none;")
        
        layout.addStretch()
        layout.addWidget(self._empty_icon)
        layout.addWidget(self._empty_msg)
        layout.addStretch()
        return widget
    
    def charger_personnel(self):
        """Charge la liste du personnel dans le combo"""
        self.combo_personnel.blockSignals(True)
        self.combo_personnel.clear()
        self.combo_personnel.addItem("-- Tous les personnels --", None)
        
        personnels = self.ctrl.get_all_personnels()
        for p in personnels:
            nom = f"{p.get('nom', '')} {p.get('prenom', '')}".strip()
            code = p.get("code", "")
            display = f"{nom} ({code})" if nom else code
            self.combo_personnel.addItem(display, p)
        
        self.combo_personnel.blockSignals(False)
        
        # Afficher toutes les cartes par défaut
        self.afficher_cartes(personnels)
    
    def _on_personnel_changed(self, index):
        """Appelé quand un personnel est sélectionné"""
        personnel = self.combo_personnel.currentData()
        if personnel:
            self.afficher_cartes([personnel])
        else:
            # Afficher tous
            personnels = self.ctrl.get_all_personnels()
            self.afficher_cartes(personnels)
    
    def afficher_cartes(self, personnels):
        """Affiche les cartes membres en grille"""
        # Vider la grille
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        
        if not personnels:
            self.scroll.hide()
            self.empty_widget.show()
            return
        
        self.empty_widget.hide()
        self.scroll.show()
        
        # Nombre de colonnes (4 cartes par ligne)
        nb_cols = 4
        
        # Ajouter les cartes
        for idx, personnel in enumerate(personnels):
            carte = CarteMembreWidget(personnel, self.ctrl)
            carte.generer_pdf_clicked.connect(self._generer_pdf)
            
            row = idx // nb_cols
            col = idx % nb_cols
            self.grid_layout.addWidget(carte, row, col)
    
    def _generer_pdf(self, personnel):
        """Génère le PDF de la carte membre"""
        code = personnel.get("code", "")
        if not code:
            CustomMessageBox("Erreur", "Code personnel introuvable.", False, self).exec()
            return
        
        chemin, _ = QFileDialog.getSaveFileName(
            self, "Générer carte membre", f"carte_{code}.pdf", "PDF Files (*.pdf)"
        )
        if not chemin:
            return
        
        ok, msg = self.ctrl.generer_carte_membre_pdf(code, chemin)
        CustomMessageBox("Succès" if ok else "Erreur", msg, ok, self).exec()
    
    def apply_theme(self):
        c = theme_manager.colors()
        
        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_main']};
            }}
            QFrame#HeaderFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}
            QLabel#HeaderTitle {{
                font-size: 15px;
                font-weight: 700;
                color: {c['text_primary']};
                border: none;
                background: transparent;
            }}
            QComboBox#PersonnelCombo {{
                background: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 0 12px;
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QComboBox#PersonnelCombo::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox#PersonnelCombo QAbstractItemView {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                selection-background-color: {c['primary_light']};
                selection-color: {c['primary']};
                color: {c['text_primary']};
            }}
            QScrollArea#CardsScroll {{
                background: transparent;
                border: none;
            }}
            QWidget#CardsContainer {{
                background: transparent;
            }}
        """)
        
        # Scrollbar
        self.scroll.verticalScrollBar().setStyleSheet(f"""
            QScrollBar:vertical {{
                background: {c['bg_main']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c['primary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        # Mettre à jour les icônes
        if hasattr(self, '_header_icon'):
            self._header_icon.setPixmap(qta.icon("fa5s.id-card", color=c["primary"]).pixmap(24, 24))
        
        if hasattr(self, '_empty_icon'):
            self._empty_icon.setPixmap(qta.icon("fa5s.inbox", color=c["text_muted"]).pixmap(72, 72))
            self._empty_msg.setStyleSheet(f"font-size: 14px; color: {c['text_muted']}; border: none;")
