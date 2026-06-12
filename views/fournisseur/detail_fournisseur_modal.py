import os
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QFrame, QWidget, QPushButton, QGraphicsDropShadowEffect
)
from views.shared.modal_theme import MC
from views.shared.theme_manager import theme_manager


class DetailsFournisseurModal(QDialog):
    """
    Modal moderne pour afficher les informations du fournisseur.
    Layout :
        - Header  : infos cabinet + logo + badge
        - Bandeau : nom fournisseur + email
        - Corps   : cartes infos
        - Footer  : Fermer
    """

    def __init__(self, parent, fournisseur: dict, ctrl):
        super().__init__(parent)
        self.ctrl = ctrl
        self.data = fournisseur or {}
        self.info_cabinet = (
            self.ctrl.get_cabinet_info()
            if hasattr(self.ctrl, "get_cabinet_info") else {}
        )

        self.setWindowTitle("Details Fournisseur")
        self.setFixedSize(680, 520)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._init_ui()

    def _init_ui(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 80))

        self.container = QFrame(self)
        self.container.setGraphicsEffect(shadow)
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {MC.BG_CARD};
                border-radius: 20px;
                border: 1px solid {MC.BORDER};
            }}
            QLabel {{ border: none; background: transparent; }}
        """)

        main = QVBoxLayout(self.container)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        self._setup_header(main)
        self._setup_bandeau(main)
        self._setup_corps(main)
        self._setup_footer(main)

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(20, 20, 20, 20)
        wrapper.addWidget(self.container)

    def _setup_header(self, layout):
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {MC.BG_CARD}, stop:1 {MC.BG_MAIN});
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom: 1px solid {MC.BORDER_LIGHT};
            }}
        """)
        h = QHBoxLayout(header)
        h.setContentsMargins(25, 10, 25, 10)

        cab = QVBoxLayout()
        cab.setSpacing(2)
        nom = QLabel(self.info_cabinet.get("nom_cabinet", "Cabinet Medical").upper())
        nom.setStyleSheet(
            f"font-weight: 900; font-size: 16px; color: {MC.PRIMARY};"
            "border: none; background: transparent;"
        )
        adr = QLabel(self.info_cabinet.get("adresse_cabinet", ""))
        adr.setStyleSheet(f"color: {MC.TEXT_SECONDARY}; font-size: 10px; border: none; background: transparent;")
        adr.setWordWrap(True)
        cab.addWidget(nom)
        cab.addWidget(adr)
        h.addLayout(cab, 4)

        c = theme_manager.colors()
        badge = QLabel("  FOURNISSEUR  ")
        badge.setStyleSheet(f"""
            background-color: {c['success_bg']};
            color: {c['success']};
            border: 1px solid {c['success']};
            border-radius: 8px;
            font-weight: bold;
            font-size: 10px;
            padding: 4px 8px;
        """)
        h.addWidget(badge, 0, Qt.AlignVCenter)
        h.addStretch()

        logo_path = self.info_cabinet.get("logo_url")
        if logo_path and os.path.exists(logo_path):
            ll = QLabel()
            ll.setPixmap(QPixmap(logo_path).scaled(
                55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            ll.setStyleSheet("border: none; background: transparent;")
            h.addWidget(ll, 0, Qt.AlignRight)

        layout.addWidget(header)

    def _setup_bandeau(self, layout):
        nom = self.data.get("nom_entreprise", "Inconnu")
        mail = self.data.get("email_fournisseur", "")

        bandeau = QFrame()
        bandeau.setFixedHeight(70)
        bandeau.setStyleSheet(f"background-color: {MC.TEXT_PRIMARY}; border: none;")
        b = QHBoxLayout(bandeau)
        b.setContentsMargins(25, 0, 25, 0)
        b.setSpacing(0)

        left = QVBoxLayout()
        left.setSpacing(3)
        lbl_nom = QLabel(f"FOURNISSEUR : {nom.upper()}")
        lbl_nom.setStyleSheet(
            f"color: {MC.TEXT_INVERSE}; font-weight: bold; font-size: 13px; border:none;"
        )
        lbl_mail = QLabel(mail)
        lbl_mail.setStyleSheet(
            f"color: {MC.TEXT_MUTED}; font-size: 10px; border: none;"
        )
        left.addWidget(lbl_nom)
        left.addWidget(lbl_mail)
        b.addLayout(left)
        b.addStretch()

        layout.addWidget(bandeau)

    def _setup_corps(self, layout):
        body = QWidget()
        body.setStyleSheet(f"background: {MC.BG_MAIN};")
        root = QVBoxLayout(body)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        info_card = self._info_card("Informations", [
            ("Entreprise", self.data.get("nom_entreprise", ""), "fa5s.building"),
            ("Email", self.data.get("email_fournisseur", ""), "fa5s.envelope"),
            ("Telephone", self.data.get("telephone", ""), "fa5s.phone"),
            ("Adresse", self.data.get("adresse", ""), "fa5s.map-marker-alt"),
        ])
        root.addWidget(info_card)

        layout.addWidget(body)

    def _setup_footer(self, layout):
        footer = QFrame()
        footer.setFixedHeight(70)
        footer.setStyleSheet(f"""
            QFrame {{
                background: {MC.BG_MAIN};
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
                border-top: 1px solid {MC.BORDER_LIGHT};
            }}
        """)
        f = QHBoxLayout(footer)
        f.setContentsMargins(20, 0, 20, 0)
        f.addStretch()

        btn_close = QPushButton(qta.icon("fa5s.times", color="white"), " Fermer")
        btn_close.setFixedHeight(36)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {MC.PRIMARY};
                color: {MC.TEXT_INVERSE};
                border-radius: 8px;
                font-weight: bold;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background-color: {MC.PRIMARY_HOVER}; }}
        """)
        btn_close.clicked.connect(self.accept)
        f.addWidget(btn_close)

        layout.addWidget(footer)

    def _info_card(self, titre, items):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {MC.BG_CARD};
                border: none;
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        header = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(qta.icon("fa5s.info-circle", color=MC.PRIMARY).pixmap(16, 16))
        title = QLabel(titre)
        title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {MC.TEXT_PRIMARY};")
        header.addWidget(icon)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)

        col = 0
        row = 0
        for idx, (label, value, icon_name) in enumerate(items):
            ic = QLabel()
            ic.setPixmap(qta.icon(icon_name, color=MC.PRIMARY).pixmap(16, 16))
            lbl = QLabel(f"{label} :")
            lbl.setStyleSheet(f"color: {MC.TEXT_SECONDARY}; font-size: 11px;")
            val = QLabel(str(value))
            val.setStyleSheet(f"color: {MC.TEXT_PRIMARY}; font-size: 12px; font-weight: bold;")

            cell = QHBoxLayout()
            cell.setSpacing(6)
            cell.addWidget(ic)
            cell.addWidget(lbl)
            cell.addWidget(val)
            cell.addStretch()

            grid.addLayout(cell, row, col)

            if col == 0:
                col = 1
            else:
                col = 0
                row += 1

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        return card
