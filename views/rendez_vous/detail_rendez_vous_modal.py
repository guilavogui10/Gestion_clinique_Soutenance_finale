import os
from datetime import datetime

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from views.rendez_vous.styles import RendezVousStyles
from views.shared.modal_theme import MC


class DetailsRendezVousModal(QDialog):
    def __init__(self, parent, code_rdv: str, ctrl):
        super().__init__(parent)
        self.ctrl = ctrl
        self.code_rdv = code_rdv
        self.data = self.ctrl.obtenir_rendez_vous_complet(code_rdv) or {}
        self.info_cabinet = self.ctrl.get_cabinet_info() if hasattr(self.ctrl, "get_cabinet_info") else {}

        self.setWindowTitle(f"Dossier Rendez-vous - {code_rdv}")
        self.setFixedSize(700, 640)
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
        self.container.setStyleSheet(
            f"""
            QFrame {{
                background-color: {MC.BG_CARD};
                border-radius: 20px;
                border: 1px solid {MC.BORDER};
            }}
            """
        )

        main = QVBoxLayout(self.container)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        self._setup_header(main)
        self._setup_banner(main)
        self._setup_body(main)
        self._setup_footer(main)

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(20, 20, 20, 20)
        wrapper.addWidget(self.container)

    def _setup_header(self, layout):
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {MC.BG_CARD}, stop:1 {MC.BG_MAIN});
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom: 1px solid {MC.BORDER_LIGHT};
            }}
            """
        )
        h = QHBoxLayout(header)
        h.setContentsMargins(25, 10, 25, 10)

        cab = QVBoxLayout()
        cab.setSpacing(2)
        nom = QLabel(self.info_cabinet.get("nom_cabinet", "Cabinet Medical").upper())
        nom.setStyleSheet(
            f"font-weight: 900; font-size: 16px; color: {MC.PRIMARY}; border: none; background: transparent;"
        )
        adr = QLabel(self.info_cabinet.get("adresse_cabinet", ""))
        adr.setStyleSheet(f"color: {MC.TEXT_SECONDARY}; font-size: 10px; border: none; background: transparent;")
        adr.setWordWrap(True)
        cab.addWidget(nom)
        cab.addWidget(adr)
        h.addLayout(cab, 4)

        badge = QLabel("  RENDEZ-VOUS  ")
        badge.setStyleSheet(
            """
            background-color: #EFF6FF;
            color: #3B82F6;
            border: 1px solid #BFDBFE;
            border-radius: 8px;
            font-weight: bold;
            font-size: 10px;
            padding: 4px 8px;
            """
        )
        h.addWidget(badge, 0, Qt.AlignVCenter)
        h.addStretch()

        logo_path = self.info_cabinet.get("logo_url")
        if logo_path and os.path.exists(logo_path):
            ll = QLabel()
            ll.setPixmap(QPixmap(logo_path).scaled(55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            ll.setStyleSheet("border: none; background: transparent;")
            h.addWidget(ll, 0, Qt.AlignRight)

        layout.addWidget(header)

    def _setup_banner(self, layout):
        d = self.data
        nom_patient = f"{d.get('patient_nom', '')} {d.get('patient_prenom', '')}".strip() or "Inconnu"
        personnel = f"{d.get('personnel_nom', '')} {d.get('personnel_prenom', '')}".strip() or d.get("code_personnel", "-")

        date_val = d.get("date_rendez_vous", "")
        if hasattr(date_val, "strftime"):
            date_str = date_val.strftime("%d/%m/%Y a %H:%M")
        else:
            date_str = str(date_val)

        banner = QFrame()
        banner.setFixedHeight(78)
        banner.setStyleSheet(f"background-color: {MC.TEXT_PRIMARY}; border: none;")
        b = QHBoxLayout(banner)
        b.setContentsMargins(25, 0, 25, 0)

        left = QVBoxLayout()
        left.setSpacing(3)
        lbl_p = QLabel(f"PATIENT : {nom_patient.upper()}")
        lbl_p.setStyleSheet(f"color: {MC.BG_MAIN}; font-weight: bold; font-size: 13px; border:none;")
        lbl_m = QLabel(f"Personnel : {personnel}")
        lbl_m.setStyleSheet(f"color: {MC.TEXT_MUTED}; font-size: 10px; border: none;")
        left.addWidget(lbl_p)
        left.addWidget(lbl_m)
        b.addLayout(left)
        b.addStretch()

        right = QVBoxLayout()
        right.setSpacing(3)
        right.setAlignment(Qt.AlignRight)
        lbl_code = QLabel(f"No {self.code_rdv}")
        lbl_code.setStyleSheet(
            "color: #3B82F6; font-weight: bold; font-size: 13px; font-family: 'Consolas'; border: none;"
        )
        lbl_date = QLabel(date_str)
        lbl_date.setStyleSheet(f"color: {MC.TEXT_SECONDARY}; font-size: 10px; border: none;")
        right.addWidget(lbl_code, 0, Qt.AlignRight)
        right.addWidget(lbl_date, 0, Qt.AlignRight)
        b.addLayout(right)

        layout.addWidget(banner)

    def _setup_body(self, layout):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"""
            QScrollArea {{ border: none; background: {MC.BG_MAIN}; }}
            QScrollBar:vertical {{
                border: none; background: {MC.BORDER_LIGHT};
                width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {MC.BORDER}; border-radius: 3px;
            }}
            """
        )

        content = QWidget()
        content.setStyleSheet(f"background: {MC.BG_MAIN};")
        root = QHBoxLayout(content)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        root.addLayout(self._left_column(), 55)
        root.addLayout(self._right_column(), 45)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _left_column(self):
        col = QVBoxLayout()
        col.setSpacing(12)
        d = self.data

        col.addWidget(
            self._card(
                "Statut du rendez-vous",
                "fa5s.flag",
                "#EFF6FF",
                "#BFDBFE",
                "#3B82F6",
                self._pretty_status(d.get("statut_rendez_vous", "-")),
            )
        )
        col.addWidget(
            self._card(
                "Type de visite",
                "fa5s.notes-medical",
                "#F0FDF4",
                "#BBF7D0",
                MC.PRIMARY,
                str(d.get("type_visite", "-")).replace("_", " ").title(),
            )
        )
        col.addWidget(
            self._card(
                "Priorite",
                "fa5s.exclamation-circle",
                "#FFF7ED",
                "#FED7AA",
                "#EA580C",
                "Urgent" if d.get("urgent") else "Normale",
            )
        )
        col.addStretch()
        return col

    def _right_column(self):
        col = QVBoxLayout()
        col.setSpacing(12)
        d = self.data

        col.addWidget(
            self._info_block(
                "Informations patient",
                "fa5s.user-injured",
                MC.PRIMARY,
                [
                    ("Nom complet", f"{d.get('patient_nom', '')} {d.get('patient_prenom', '')}".strip() or "-"),
                    ("Telephone", d.get("patient_telephone", "-")),
                    ("Code patient", d.get("code_patient", "-")),
                ],
            )
        )
        col.addWidget(
            self._info_block(
                "Planification",
                "fa5s.calendar-alt",
                "#6366F1",
                [
                    ("Date/heure", self._format_datetime(d.get("date_rendez_vous"))),
                    ("Personnel", f"{d.get('personnel_nom', '')} {d.get('personnel_prenom', '')}".strip() or d.get("code_personnel", "-")),
                    ("Fonction", d.get("personnel_fonction", "-")),
                ],
            )
        )
        col.addWidget(
            self._info_block(
                "Tracabilite",
                "fa5s.link",
                "#0F766E",
                [
                    ("Code RDV", d.get("code_rendez_vous", "-")),
                    ("Code visite", d.get("code_visite", "-")),
                    ("Code session", d.get("code_session", "-")),
                ],
            )
        )
        col.addStretch()
        return col

    def _card(self, titre, icone, couleur_bg, couleur_b, couleur_t, contenu):
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {couleur_bg}; border: 1px solid {couleur_b}; border-radius: 12px;"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        head = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(qta.icon(icone, color=couleur_t).pixmap(14, 14))
        tl = QLabel(titre.upper())
        tl.setStyleSheet(
            f"font-weight: bold; color: {couleur_t}; font-size: 10px; border: none; background: transparent;"
        )
        head.addWidget(ic)
        head.addSpacing(5)
        head.addWidget(tl)
        head.addStretch()
        lay.addLayout(head)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {couleur_b}; border: none;")
        lay.addWidget(sep)

        lbl = QLabel(contenu or "-")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"color: {MC.TEXT_PRIMARY}; font-size: 12px; line-height: 1.5; border: none; background: transparent;"
        )
        lay.addWidget(lbl)
        return frame

    def _info_block(self, titre, icone, couleur, lignes):
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {MC.BG_CARD}; border: 1px solid {MC.BORDER}; border-radius: 12px;"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)

        head = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(qta.icon(icone, color=couleur).pixmap(13, 13))
        tl = QLabel(titre.upper())
        tl.setStyleSheet(
            f"font-weight: bold; color: {couleur}; font-size: 10px; border: none; background: transparent;"
        )
        head.addWidget(ic)
        head.addSpacing(5)
        head.addWidget(tl)
        head.addStretch()
        lay.addLayout(head)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {MC.BORDER}; border: none;")
        lay.addWidget(sep)

        for label, valeur in lignes:
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl_k = QLabel(f"{label} :")
            lbl_k.setFixedWidth(120)
            lbl_k.setStyleSheet(
                f"color: {MC.TEXT_SECONDARY}; font-size: 11px; font-weight: 600; border: none; background: transparent;"
            )
            lbl_v = QLabel(str(valeur) if valeur else "-")
            lbl_v.setWordWrap(True)
            lbl_v.setStyleSheet(
                f"color: {MC.TEXT_PRIMARY}; font-size: 11px; border: none; background: transparent;"
            )
            row.addWidget(lbl_k)
            row.addWidget(lbl_v, 1)
            lay.addLayout(row)

        return frame

    def _setup_footer(self, layout):
        footer = QFrame()
        footer.setFixedHeight(65)
        footer.setStyleSheet(
            f"""
            background-color: {MC.BG_MAIN};
            border-bottom-left-radius: 20px;
            border-bottom-right-radius: 20px;
            border-top: 1px solid {MC.BORDER};
            """
        )
        f = QHBoxLayout(footer)
        f.setContentsMargins(25, 0, 25, 0)
        f.setSpacing(12)

        btn_close = QPushButton(qta.icon("fa5s.times", color=MC.TEXT_SECONDARY), " Fermer")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.close)
        btn_close.setFixedHeight(38)
        btn_close.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {MC.BG_CARD};
                color: {MC.TEXT_SECONDARY};
                border-radius: 8px;
                font-weight: bold;
                padding: 8px 20px;
                border: 1px solid {MC.BORDER};
            }}
            QPushButton:hover {{ background-color: {MC.BORDER_LIGHT}; }}
            """
        )

        btn_print = QPushButton(qta.icon("fa5s.print", color="white"), " Imprimer")
        btn_print.setCursor(Qt.PointingHandCursor)
        btn_print.setFixedHeight(38)
        btn_print.setStyleSheet(
            """
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                padding: 8px 25px;
                border: none;
            }
            QPushButton:hover { background-color: #2563EB; }
            """
        )

        f.addWidget(btn_close)
        f.addStretch()
        f.addWidget(btn_print)
        layout.addWidget(footer)

    def _format_datetime(self, value):
        if hasattr(value, "strftime"):
            return value.strftime("%d/%m/%Y a %H:%M")
        if isinstance(value, str):
            for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
                try:
                    return datetime.strptime(value, pattern).strftime("%d/%m/%Y a %H:%M")
                except ValueError:
                    continue
        return str(value or "-")

    @staticmethod
    def _pretty_status(statut: str) -> str:
        mapping = {
            "attente": "En attente",
            "confirme": "Confirme",
            "en_cours": "En cours",
            "termine": "Termine",
            "annule": "Annule",
            "absent": "Absent",
            "reporte": "Reporte",
        }
        return mapping.get(str(statut or "").strip().lower(), str(statut or "-"))
