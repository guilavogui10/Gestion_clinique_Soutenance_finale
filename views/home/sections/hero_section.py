"""
hero_section.py
---------------
Section hero de la page d'accueil avec image en arrière-plan et texte en overlay.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QSize, Signal, QRect
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                               QPushButton, QFrame, QMenu)
from PySide6.QtGui import QPixmap, QFont, QPainter, QLinearGradient, QColor, QBrush

from views.shared.theme_manager import theme_manager
from views.home.components import BadgeConfiance


class HeroSection(QWidget):
    """
    Section hero avec image de fond pleine largeur et texte en overlay.
    Design: Image en z-index 0, texte avec fond blanc dégradé en z-index 1.
    """
    
    prendre_rdv_clicked = Signal()
    voir_services_clicked = Signal()
    service_selected = Signal(str)  # Signal pour la sélection d'un service spécifique
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(380)
        self.background_pixmap = None
        self._load_background_image()
        self._setup_ui()
        self._apply_theme()
        theme_manager.theme_changed.connect(self._apply_theme)
    
    def _load_background_image(self):
        """Charge l'image de fond."""
        try:
            pixmap = QPixmap("assets/images/eye.png")
            if not pixmap.isNull():
                self.background_pixmap = pixmap
            else:
                self.background_pixmap = None
        except:
            self.background_pixmap = None
    
    def paintEvent(self, event):
        """Dessine l'image de fond sur toute la largeur (z-index 0)."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # COUCHE 0: Image de fond sur toute la largeur
        if self.background_pixmap:
            scaled_pixmap = self.background_pixmap.scaled(
                self.width(), self.height(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            painter.fillRect(self.rect(), QColor("#E0F2FE"))
        
        # COUCHE 1: Dégradé blanc sur la partie gauche (overlay) - plus visible
        gradient = QLinearGradient(0, 0, self.width() * 0.55, 0)
        gradient.setColorAt(0, QColor(255, 255, 255, 255))    # Blanc totalement opaque
        gradient.setColorAt(0.5, QColor(255, 255, 255, 230))  # Très opaque
        gradient.setColorAt(0.8, QColor(255, 255, 255, 120))  # Semi-transparent
        gradient.setColorAt(1, QColor(255, 255, 255, 0))      # Totalement transparent
        
        painter.fillRect(0, 0, int(self.width() * 0.55), self.height(), gradient)
        
        super().paintEvent(event)
    
    def _setup_ui(self):
        """Configure l'interface avec le texte en overlay."""
        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === PARTIE GAUCHE : Texte + Boutons (overlay sur l'image) ===
        left_container = QWidget()
        left_container.setObjectName("left_overlay")
        left_container.setAttribute(Qt.WA_TranslucentBackground)
        
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(50, 40, 30, 40)
        left_layout.setSpacing(15)
        
        # Titre principal avec "yeux" en bleu
        title_container = QVBoxLayout()
        title_container.setSpacing(0)
        
        # Ligne 1: "Prenez soin de vos yeux,"
        title_line1_layout = QHBoxLayout()
        title_line1_layout.setSpacing(8)
        
        title_part1 = QLabel("Prenez soin de vos ")
        title_part1.setObjectName("hero_title")
        title_line1_layout.addWidget(title_part1)
        
        title_yeux = QLabel("yeux")
        title_yeux.setObjectName("hero_title_blue")
        title_line1_layout.addWidget(title_yeux)
        
        title_virgule = QLabel(",")
        title_virgule.setObjectName("hero_title")
        title_line1_layout.addWidget(title_virgule)
        
        title_line1_layout.addStretch()
        title_container.addLayout(title_line1_layout)
        
        # Ligne 2: "Nous prenons soin de vous"
        title_line2 = QLabel("Nous prenons soin de vous")
        title_line2.setObjectName("hero_title")
        title_container.addWidget(title_line2)
        
        left_layout.addLayout(title_container)
        left_layout.addSpacing(10)
        
        # Description
        desc = QLabel(
            "Notre clinique ophtalmologique vous offre des soins\n"
            "de qualité avec des équipements de pointe et une équipe\n"
            "d'experts à votre écoute."
        )
        desc.setObjectName("hero_desc")
        left_layout.addWidget(desc)
        
        left_layout.addSpacing(15)
        
        # Boutons CTA
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.btn_rdv = QPushButton()
        self.btn_rdv.setIcon(qta.icon('fa5s.calendar-check', color='white'))
        self.btn_rdv.setIconSize(QSize(14, 14))
        self.btn_rdv.setText("  Prendre rendez-vous")
        self.btn_rdv.setFixedHeight(42)
        self.btn_rdv.setMinimumWidth(180)
        self.btn_rdv.setCursor(Qt.PointingHandCursor)
        self.btn_rdv.setObjectName("btn_primary")
        self.btn_rdv.clicked.connect(self.prendre_rdv_clicked.emit)
        btn_layout.addWidget(self.btn_rdv)
        
        self.btn_services = QPushButton()
        self.btn_services.setIcon(qta.icon('fa5s.info-circle', color='#3B82F6'))
        self.btn_services.setIconSize(QSize(14, 14))
        self.btn_services.setText("  Nos services")
        self.btn_services.setFixedHeight(42)
        self.btn_services.setMinimumWidth(140)
        self.btn_services.setCursor(Qt.PointingHandCursor)
        self.btn_services.setObjectName("btn_secondary")
        self.btn_services.clicked.connect(self._show_services_menu)
        btn_layout.addWidget(self.btn_services)
        
        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)
        
        left_layout.addStretch()
        
        # Badges de confiance en bas
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(35)
        
        badge1 = BadgeConfiance(
            'fa5s.shield-alt', 
            'Soins de qualité',
            'Excellence médicale',
            '#3B82F6'
        )
        badges_layout.addWidget(badge1)
        
        badge2 = BadgeConfiance(
            'fa5s.users',
            'Équipe experte',
            'Professionnels qualifiés',
            '#3B82F6'
        )
        badges_layout.addWidget(badge2)
        
        badge3 = BadgeConfiance(
            'fa5s.cogs',
            'Technologie avancée',
            'Équipements modernes',
            '#3B82F6'
        )
        badges_layout.addWidget(badge3)
        
        badges_layout.addStretch()
        left_layout.addLayout(badges_layout)
        
        main_layout.addWidget(left_container, 40)
        
        # === PARTIE DROITE : Carte flottante ===
        right_container = QWidget()
        right_container.setObjectName("right_overlay")
        right_container.setAttribute(Qt.WA_TranslucentBackground)
        
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 50, 40)
        right_layout.setSpacing(0)
        
        right_layout.addStretch()
        
        # Carte flottante "Votre vue, notre priorité" (glassmorphism)
        floating_card = QFrame()
        floating_card.setFixedSize(320, 100)
        floating_card.setObjectName("floating_card")
        
        card_layout = QHBoxLayout(floating_card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(15)
        
        # Icône œil dans un cercle bleu
        icon_container = QFrame()
        icon_container.setFixedSize(55, 55)
        icon_container.setObjectName("icon_circle")
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        card_icon = QLabel()
        card_icon.setPixmap(qta.icon('fa5s.eye', color='white').pixmap(QSize(26, 26)))
        card_icon.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(card_icon)
        
        card_layout.addWidget(icon_container)
        
        # Texte
        card_text_layout = QVBoxLayout()
        card_text_layout.setSpacing(5)
        
        card_title = QLabel("Votre vue, notre priorité")
        card_title.setObjectName("card_title")
        card_text_layout.addWidget(card_title)
        
        card_desc = QLabel("Un diagnostic précis pour\nun traitement adapté")
        card_desc.setObjectName("card_desc")
        card_text_layout.addWidget(card_desc)
        
        card_layout.addLayout(card_text_layout)
        
        right_layout.addWidget(floating_card, 0, Qt.AlignRight)
        
        main_layout.addWidget(right_container, 60)
    
    def _show_services_menu(self):
        """Affiche le menu déroulant des services."""
        menu = QMenu(self)
        menu.setObjectName("services_menu")
        
        # Définir les services avec icônes
        services = [
            ('fa5s.stethoscope', 'Consultation', '#3B82F6'),
            ('fa5s.microscope', 'Examens', '#10B981'),
            ('fa5s.procedures', 'Chirurgie', '#8B5CF6'),
            ('fa5s.glasses', 'Lunettes', '#F59E0B'),
            ('fa5s.pills', 'Pharmacie', '#EF4444'),
            ('fa5s.calendar-check', 'Rendez-vous', '#06B6D4'),
        ]
        
        # Créer les actions du menu
        for icon_name, service_name, color in services:
            action = menu.addAction(
                qta.icon(icon_name, color=color),
                f"  {service_name}"
            )
            action.triggered.connect(lambda checked, s=service_name: self.service_selected.emit(s))
        
        # Appliquer le style au menu
        c = theme_manager.colors()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 0;
            }}
            QMenu::item {{
                padding: 10px 20px;
                color: #1F2937;
                font-size: 13px;
                font-weight: 500;
            }}
            QMenu::item:selected {{
                background-color: #EFF6FF;
                color: #3B82F6;
            }}
            QMenu::icon {{
                padding-left: 10px;
            }}
        """)
        
        # Afficher le menu sous le bouton
        menu.exec(self.btn_services.mapToGlobal(self.btn_services.rect().bottomLeft()))
    
    def _apply_theme(self):
        """Applique le thème actuel."""
        self.setStyleSheet(f"""
            HeroSection {{
                background-color: transparent;
                border: none;
            }}
            QWidget#left_overlay, QWidget#right_overlay {{
                background-color: transparent;
                border: none;
            }}
            QLabel#hero_title {{
                color: #1E293B;
                font-size: 32px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
            QLabel#hero_title_blue {{
                color: #3B82F6;
                font-size: 32px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
            QLabel#hero_desc {{
                color: #475569;
                font-size: 14px;
                line-height: 1.6;
                background: transparent;
                border: none;
            }}
            QPushButton#btn_primary {{
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 20px;
            }}
            QPushButton#btn_primary:hover {{
                background-color: #2563EB;
            }}
            QPushButton#btn_secondary {{
                background-color: white;
                color: #3B82F6;
                border: 2px solid #3B82F6;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 20px;
            }}
            QPushButton#btn_secondary:hover {{
                background-color: #EFF6FF;
            }}
            QFrame#floating_card {{
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(226, 232, 240, 0.8);
                border-radius: 12px;
            }}
            QFrame#icon_circle {{
                background-color: #3B82F6;
                border-radius: 25px;
                border: none;
            }}
            QLabel#card_title {{
                color: #1E293B;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
            QLabel#card_desc {{
                color: #64748B;
                font-size: 11px;
                background: transparent;
                border: none;
            }}
        """)
