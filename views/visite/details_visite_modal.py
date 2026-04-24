from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QFrame, QWidget, QPushButton, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPixmap
import qtawesome as qta
import os
from views.shared.modal_theme import MC

class DetailsVisiteModal(QDialog):
    def __init__(self, parent, code_visite, patient_name, details_data, cabinet_info=None):
        super().__init__(parent)
        # On récupère les infos du cabinet (soit via l'argument, soit via le parent/contrôleur)
        self.info_cabinet = cabinet_info if cabinet_info else parent.ctrl.get_cabinet_info()
        
        self.setWindowTitle(f"Dossier Médical - {code_visite}")
        self.setFixedSize(600, 650) # Légèrement plus large pour les infos cabinet
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.data = details_data
        self.code_visite = code_visite
        self.patient_name = patient_name

        self.init_ui()

    def init_ui(self):
        # 1. EFFET D'OMBRE EXTERNE
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 70))

        # 2. CONTENEUR PRINCIPAL
        self.main_container = QFrame(self)
        self.main_container.setGraphicsEffect(shadow)
        self.main_container.setStyleSheet(f"""
            QFrame {{
                background-color: {MC.BG_CARD};
                border-radius: 20px;
                border: 1px solid {MC.BORDER};
            }}
        """)
        
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- HEADER : BRANDING DU CABINET ---
        branding_header = QFrame()
        branding_header.setFixedHeight(110)
        branding_header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {MC.BG_CARD}, stop:1 {MC.BG_MAIN});
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom: 1px solid {MC.BORDER_LIGHT};
            }}
        """)
        branding_layout = QHBoxLayout(branding_header)
        branding_layout.setContentsMargins(25, 10, 25, 10)

        # Bloc Gauche : Nom et Adresse du Cabinet
        cabinet_text_layout = QVBoxLayout()
        cabinet_text_layout.setSpacing(2)
        
        nom_cab = QLabel(self.info_cabinet.get("nom_cabinet", "Cabinet Médical").upper())
        nom_cab.setStyleSheet(f"font-weight: 900; font-size: 20px; color: {MC.PRIMARY}; border: none; background: transparent;")
        
        addr_cab = QLabel(self.info_cabinet.get("adresse_cabinet", "Adresse non définie"))
        addr_cab.setStyleSheet(f"color: {MC.TEXT_SECONDARY}; font-size: 11px; border: none; background: transparent;")
        addr_cab.setWordWrap(True)

        tel_cab = QLabel(f"Contact: {self.info_cabinet.get('telephone_cabinet', '')}")
        tel_cab.setStyleSheet(f"color: {MC.PRIMARY}; font-size: 10px; font-weight: bold; border: none; background: transparent;")

        cabinet_text_layout.addWidget(nom_cab)
        cabinet_text_layout.addWidget(addr_cab)
        cabinet_text_layout.addWidget(tel_cab)
        cabinet_text_layout.addStretch()

        branding_layout.addLayout(cabinet_text_layout, 4)

        # Bloc Droite : Logo
        logo_path = self.info_cabinet.get('logo_url')
        if logo_path and os.path.exists(logo_path):
            logo_lbl = QLabel()
            pix = QPixmap(logo_path).scaled(85, 85, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setStyleSheet("border: none; background: transparent;")
            branding_layout.addWidget(logo_lbl, 0, Qt.AlignRight)

        main_layout.addWidget(branding_header)

        # --- BANDEAU INFOS VISITE (Patient & Code) ---
        visite_bar = QFrame()
        visite_bar.setFixedHeight(60)
        visite_bar.setStyleSheet(f"background-color: {MC.TEXT_PRIMARY}; border: none;")
        visite_layout = QHBoxLayout(visite_bar)
        visite_layout.setContentsMargins(25, 0, 25, 0)

        patient_info = QLabel(f"PATIENT: {self.patient_name.upper()}")
        patient_info.setStyleSheet(f"color: {MC.BG_MAIN}; font-weight: bold; font-size: 13px;")
        
        code_info = QLabel(f"N° VISITE: {self.code_visite}")
        code_info.setStyleSheet(f"color: {MC.SUCCESS}; font-weight: bold; font-size: 13px; font-family: 'Consolas';")

        visite_layout.addWidget(patient_info)
        visite_layout.addStretch()
        visite_layout.addWidget(code_info)
        
        main_layout.addWidget(visite_bar)

        # --- ZONE DE CONTENU SCROLLABLE ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: {MC.BG_CARD}; }}
            QScrollBar:vertical {{ border: none; background: {MC.BORDER_LIGHT}; width: 8px; border-radius: 4px; }}
            QScrollBar::handle:vertical {{ background: {MC.BORDER}; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background: {MC.TEXT_MUTED}; }}
        """)
        
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {MC.BG_CARD};")
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(18)
        self.content_layout.setContentsMargins(25, 25, 25, 25)

        # Mapping des sections avec icônes
        sections = [
            ("Consultations", "fa5s.stethoscope", 'consultation', ['diagnostique', 'resultat_consultation']),
            ("Examens Labo", "fa5s.microscope", 'examen', ['nom_examen', 'resultat_examen']),
            ("Prescriptions", "fa5s.pills", 'prescription', ['designation', 'quantite_prescript']),
            ("Chirurgies", "fa5s.procedures", 'chururgie', ['nom_chururgie']),
            ("Optique", "fa5s.glasses", 'commandeslunettes', ['numero_cadre', 'numero_verre'])
        ]

        for titre, ico, key, fields in sections:
            self.ajouter_section(titre, ico, self.data.get(key, []), fields)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # --- FOOTER ---
        footer = QFrame()
        footer.setFixedHeight(70)
        footer.setStyleSheet(f"background-color: {MC.BG_MAIN}; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px; border-top: 1px solid {MC.BORDER};")
        footer_layout = QHBoxLayout(footer)
        
        btn_close = QPushButton("Fermer le Dossier")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {MC.BG_CARD}; color: {MC.TEXT_SECONDARY}; border-radius: 8px; 
                font-weight: bold; padding: 10px 20px; border: 1px solid {MC.BORDER};
            }}
            QPushButton:hover {{ background-color: {MC.BORDER_LIGHT}; border-color: {MC.TEXT_MUTED}; }}
        """)

        btn_print = QPushButton(qta.icon("fa5s.print", color=MC.TEXT_INVERSE), " Imprimer")
        btn_print.setStyleSheet(f"""
            QPushButton {{
                background-color: {MC.PRIMARY}; color: {MC.TEXT_INVERSE}; border-radius: 8px; 
                font-weight: bold; padding: 10px 25px;
            }}
            QPushButton:hover {{ background-color: {MC.PRIMARY_HOVER}; }}
        """)

        footer_layout.addWidget(btn_close)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_print)
        main_layout.addWidget(footer)

        # LAYOUT FINAL
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(20, 20, 20, 20)
        wrapper.addWidget(self.main_container)

    def ajouter_section(self, titre, icone, items, champs):
        if not items: return

        frame = QFrame()
        frame.setStyleSheet(f"background-color: {MC.BG_CARD}; border: 1px solid {MC.BORDER_LIGHT}; border-radius: 12px;")
        lay = QVBoxLayout(frame)
        
        head = QHBoxLayout()
        ico_lbl = QLabel()
        ico_lbl.setPixmap(qta.icon(icone, color=MC.PRIMARY).pixmap(18, 18))
        t_lbl = QLabel(titre.upper())
        t_lbl.setStyleSheet(f"font-weight: bold; color: {MC.PRIMARY}; font-size: 11px; letter-spacing: 0.5px;")
        
        head.addWidget(ico_lbl)
        head.addWidget(t_lbl)
        head.addStretch()
        lay.addLayout(head)

        for item in items:
            txt = " • " + " | ".join([str(item[c]) for c in champs if c in item])
            l = QLabel(txt)
            l.setWordWrap(True)
            l.setStyleSheet(f"color: {MC.TEXT_PRIMARY}; font-size: 12px; padding: 4px; border: none; background: transparent;")
            lay.addWidget(l)

        self.content_layout.addWidget(frame)
        
        
    