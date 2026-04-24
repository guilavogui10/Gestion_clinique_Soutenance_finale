import os
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QWidget, QPushButton,
    QGraphicsDropShadowEffect
)
from views.shared.modal_theme import MC


class DetailsConsultationModal(QDialog):
    """
    Modal d'affichage du dossier complet d'une consultation.
    Affiche : infos patient, médecin, diagnostic, résultat,
    et tous les services liés (examens, chirurgies, lunettes, prescriptions).
    """

    def __init__(self, parent, code_consultation, ctrl):
        super().__init__(parent)
        self.ctrl             = ctrl
        self.code_consultation = code_consultation

        # Récupération des données via le contrôleur
        self.data_complete  = self.ctrl.obtenir_consultation_complete(code_consultation)
        self.data_services  = self.ctrl.obtenir_services_lies(code_consultation)
        self.info_cabinet   = self.ctrl.get_cabinet_info() if hasattr(self.ctrl, 'get_cabinet_info') else {}

        self.setWindowTitle(f"Dossier Consultation - {code_consultation}")
        self.setFixedSize(620, 680)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._init_ui()

    # =========================================================================
    # CONSTRUCTION DE L'INTERFACE
    # =========================================================================

    def _init_ui(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 70))

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

        self._setup_header(main_layout)
        self._setup_bandeau(main_layout)
        self._setup_contenu(main_layout)
        self._setup_footer(main_layout)

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(20, 20, 20, 20)
        wrapper.addWidget(self.main_container)

    def _setup_header(self, main_layout):
        """En-tête avec les informations du cabinet."""
        header = QFrame()
        header.setFixedHeight(110)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {MC.BG_CARD}, stop:1 {MC.BG_MAIN});
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom: 1px solid {MC.BORDER_LIGHT};
            }}
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(25, 10, 25, 10)

        # Texte cabinet
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        nom = QLabel(self.info_cabinet.get("nom_cabinet", "Cabinet Médical").upper())
        nom.setStyleSheet(f"font-weight: 900; font-size: 20px; color: {MC.PRIMARY}; border: none; background: transparent;")

        adresse = QLabel(self.info_cabinet.get("adresse_cabinet", "Adresse non définie"))
        adresse.setStyleSheet(f"color: {MC.TEXT_SECONDARY}; font-size: 11px; border: none; background: transparent;")
        adresse.setWordWrap(True)

        tel = QLabel(f"Contact: {self.info_cabinet.get('telephone_cabinet', '')}")
        tel.setStyleSheet(f"color: {MC.PRIMARY}; font-size: 10px; font-weight: bold; border: none; background: transparent;")

        text_layout.addWidget(nom)
        text_layout.addWidget(adresse)
        text_layout.addWidget(tel)
        text_layout.addStretch()
        layout.addLayout(text_layout, 4)

        # Logo cabinet
        logo_path = self.info_cabinet.get('logo_url')
        if logo_path and os.path.exists(logo_path):
            logo_lbl = QLabel()
            pix = QPixmap(logo_path).scaled(85, 85, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setStyleSheet("border: none; background: transparent;")
            layout.addWidget(logo_lbl, 0, Qt.AlignRight)

        main_layout.addWidget(header)

    def _setup_bandeau(self, main_layout):
        """Bandeau sombre avec nom patient et code consultation."""
        d = self.data_complete or {}

        nom_patient = f"{d.get('patient_nom', '')} {d.get('patient_prenom', '')}".strip() or "Inconnu"
        medecin     = f"Dr. {d.get('personnel_nom', '')} {d.get('personnel_prenom', '')}".strip()
        date_val    = d.get('date_consultation', '')
        date_str    = (
            date_val.strftime("%d/%m/%Y")
            if hasattr(date_val, 'strftime') else str(date_val)
        )

        bandeau = QFrame()
        bandeau.setFixedHeight(70)
        bandeau.setStyleSheet(f"background-color: {MC.TEXT_PRIMARY}; border: none;")
        layout = QHBoxLayout(bandeau)
        layout.setContentsMargins(25, 0, 25, 0)

        lbl_patient = QLabel(f"PATIENT : {nom_patient.upper()}")
        lbl_patient.setStyleSheet(f"color: {MC.BG_MAIN}; font-weight: bold; font-size: 13px;")

        lbl_code = QLabel(f"N° {self.code_consultation}  |  {date_str}")
        lbl_code.setStyleSheet(f"color: {MC.SUCCESS}; font-weight: bold; font-size: 12px; font-family: 'Consolas';")

        lbl_medecin = QLabel(medecin)
        lbl_medecin.setStyleSheet(f"color: {MC.TEXT_MUTED}; font-size: 11px;")

        left = QVBoxLayout()
        left.setSpacing(2)
        left.addWidget(lbl_patient)
        left.addWidget(lbl_medecin)

        layout.addLayout(left)
        layout.addStretch()
        layout.addWidget(lbl_code)

        main_layout.addWidget(bandeau)

    def _setup_contenu(self, main_layout):
        """Zone scrollable avec toutes les sections médicales."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: {MC.BG_CARD}; }}
            QScrollBar:vertical {{ border: none; background: {MC.BORDER_LIGHT}; width: 8px; border-radius: 4px; }}
            QScrollBar::handle:vertical {{ background: {MC.BORDER}; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background: {MC.TEXT_MUTED}; }}
        """)

        content = QWidget()
        content.setStyleSheet(f"background-color: {MC.BG_CARD};")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setSpacing(14)
        self.content_layout.setContentsMargins(25, 20, 25, 20)

        d = self.data_complete or {}
        s = self.data_services

        # Section Diagnostic & Résultat
        self._ajouter_section_consultation(d)

        # Sections services liés
        self._ajouter_section(
            "Examens Complémentaires", "fa5s.microscope",
            s.get('examens', []),
            ['nom_examen', 'resultat_examen']
        )
        self._ajouter_section(
            "Chirurgies", "fa5s.procedures",
            s.get('chirurgies', []),
            ['nom_chirurgie', 'date_chirurgie']
        )
        self._ajouter_section(
            "Commandes Lunettes", "fa5s.glasses",
            s.get('lunettes', []),
            ['numero_cadre', 'numero_verre']
        )
        self._ajouter_section(
            "Prescriptions", "fa5s.pills",
            s.get('prescriptions', []),
            ['designation', 'quantite_prescript']
        )

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _setup_footer(self, main_layout):
        """Pied de page avec boutons Fermer et Imprimer."""
        footer = QFrame()
        footer.setFixedHeight(70)
        footer.setStyleSheet(f"""
            background-color: {MC.BG_MAIN};
            border-bottom-left-radius: 20px;
            border-bottom-right-radius: 20px;
            border-top: 1px solid {MC.BORDER};
        """)
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(25, 0, 25, 0)

        btn_close = QPushButton("Fermer")
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
        btn_print.setCursor(Qt.PointingHandCursor)
        btn_print.setStyleSheet(f"""
            QPushButton {{
                background-color: {MC.PRIMARY}; color: {MC.TEXT_INVERSE}; border-radius: 8px;
                font-weight: bold; padding: 10px 25px;
            }}
            QPushButton:hover {{ background-color: {MC.PRIMARY_HOVER}; }}
        """)

        layout.addWidget(btn_close)
        layout.addStretch()
        layout.addWidget(btn_print)
        main_layout.addWidget(footer)

    # =========================================================================
    # SECTIONS DE CONTENU
    # =========================================================================

    def _ajouter_section_consultation(self, d: dict):
        """Section spéciale pour le diagnostic et le résultat de consultation."""
        if not d:
            return

        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {MC.SUCCESS_BG}; border: 1px solid {MC.BORDER_LIGHT}; border-radius: 12px;"
        )
        lay = QVBoxLayout(frame)
        lay.setSpacing(8)
        lay.setContentsMargins(15, 12, 15, 12)

        # En-tête
        head = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.stethoscope", color=MC.PRIMARY).pixmap(18, 18))
        titre = QLabel("CONSULTATION")
        titre.setStyleSheet(
            f"font-weight: bold; color: {MC.PRIMARY}; font-size: 11px; letter-spacing: 0.5px;"
        )
        head.addWidget(ico)
        head.addSpacing(6)
        head.addWidget(titre)
        head.addStretch()

        # Frais + statut
        frais = d.get('frais_consultation', 0)
        statut = d.get('statut_facture', '')
        lbl_frais = QLabel(f"{frais} GNF  —  {statut}")
        lbl_frais.setStyleSheet(f"color: {MC.PRIMARY}; font-weight: bold; font-size: 11px;")
        head.addWidget(lbl_frais)
        lay.addLayout(head)

        # Ligne séparatrice
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {MC.BORDER_LIGHT}; border: none;")
        lay.addWidget(sep)

        # Diagnostic
        lbl_diag_titre = QLabel("Diagnostic :")
        lbl_diag_titre.setStyleSheet(f"color: {MC.TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        lbl_diag = QLabel(d.get('diagnostique', '—'))
        lbl_diag.setWordWrap(True)
        lbl_diag.setStyleSheet(f"color: {MC.TEXT_PRIMARY}; font-size: 12px; padding-left: 8px;")

        # Résultat
        lbl_res_titre = QLabel("Résultat :")
        lbl_res_titre.setStyleSheet(f"color: {MC.TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        lbl_res = QLabel(d.get('resultat_consultation', '—'))
        lbl_res.setWordWrap(True)
        lbl_res.setStyleSheet(f"color: {MC.TEXT_PRIMARY}; font-size: 12px; padding-left: 8px;")

        # Services prescrits
        services = []
        if d.get('examen')            == 'Oui': services.append('Examen')
        if d.get('chirurgie')         == 'Oui': services.append('Chirurgie')
        if d.get('commandelunette')   == 'Oui': services.append('Lunettes')
        if d.get('prescription_produit') == 'Oui': services.append('Prescription')

        lay.addWidget(lbl_diag_titre)
        lay.addWidget(lbl_diag)
        lay.addWidget(lbl_res_titre)
        lay.addWidget(lbl_res)

        if services:
            lbl_serv = QLabel("Services : " + "  •  ".join(services))
            lbl_serv.setStyleSheet(
                f"color: {MC.PRIMARY}; font-size: 11px; font-weight: bold; padding-top: 4px;"
            )
            lay.addWidget(lbl_serv)

        self.content_layout.addWidget(frame)

    def _ajouter_section(self, titre: str, icone: str, items: list, champs: list):
        """Section générique pour les services liés (examens, chirurgies, etc.)."""
        if not items:
            return

        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {MC.BG_CARD}; border: 1px solid {MC.BORDER_LIGHT}; border-radius: 12px;"
        )
        lay = QVBoxLayout(frame)
        lay.setSpacing(6)
        lay.setContentsMargins(15, 12, 15, 12)

        # En-tête
        head = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon(icone, color=MC.PRIMARY).pixmap(18, 18))
        t_lbl = QLabel(titre.upper())
        t_lbl.setStyleSheet(
            f"font-weight: bold; color: {MC.PRIMARY}; font-size: 11px; letter-spacing: 0.5px;"
        )
        head.addWidget(ico)
        head.addSpacing(6)
        head.addWidget(t_lbl)
        head.addStretch()
        lay.addLayout(head)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {MC.BORDER_LIGHT}; border: none;")
        lay.addWidget(sep)

        for item in items:
            texte = "  •  ".join(
                str(item[c]) for c in champs if c in item and item[c]
            )
            lbl = QLabel(f"• {texte}")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                f"color: {MC.TEXT_PRIMARY}; font-size: 12px; padding: 3px 0px; border: none; background: transparent;"
            )
            lay.addWidget(lbl)

        self.content_layout.addWidget(frame)