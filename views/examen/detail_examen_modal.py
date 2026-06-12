import os
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QWidget, QPushButton,
    QGraphicsDropShadowEffect
)
from views.shared.theme_manager import theme_manager


class DetailsExamenModal(QDialog):
    """
    Modal d affichage complet d un examen medical.
    Layout :
        - Header  : infos cabinet + logo
        - Bandeau : patient + code + date + medecin
        - Corps   : 2 colonnes
            Gauche  : Libelle + Resultat (zone large)
            Droite  : Infos patient + Facturation + Codes
        - Footer  : Fermer + Imprimer
    """

    def __init__(self, parent, code_examen: str, ctrl):
        super().__init__(parent)
        self.ctrl        = ctrl
        self.code_examen = code_examen

        self.data        = self.ctrl.obtenir_examen_complet(code_examen) or {}
        self.info_cabinet = (
            self.ctrl.get_cabinet_info()
            if hasattr(self.ctrl, "get_cabinet_info") else {}
        )

        self.setWindowTitle(f"Dossier Examen - {code_examen}")
        self.setFixedSize(680, 640)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._init_ui()
        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # UI PRINCIPALE
    # =========================================================================

    def _init_ui(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 80))

        self.container = QFrame(self)
        self.container.setGraphicsEffect(shadow)

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

        self.apply_theme()

    # =========================================================================
    # APPLY THEME — styles + reconstruction du contenu scrollable
    # =========================================================================

    def apply_theme(self):
        c = theme_manager.colors()

        # Container principal
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_card']};
                border-radius: 20px;
                border: 1px solid {c['border']};
            }}
        """)

        # Header
        self._header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {c['bg_card']}, stop:1 {c['bg_main']});
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom: 1px solid {c['border_light']};
            }}
        """)
        self._lbl_nom.setStyleSheet(
            f"font-weight: 900; font-size: 16px; color: {c['primary']};"
            "border: none; background: transparent;"
        )
        self._lbl_adr.setStyleSheet(
            f"color: {c['text_secondary']}; font-size: 10px; border: none; background: transparent;"
        )
        self._badge.setStyleSheet(f"""
            background-color: {c['primary_light']};
            color: {c['primary']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            font-weight: bold;
            font-size: 10px;
            padding: 4px 8px;
        """)

        # Bandeau
        self._bandeau.setStyleSheet(
            f"background-color: {c['text_primary']}; border: none;"
        )
        self._lbl_patient.setStyleSheet(
            f"color: {c['bg_main']}; font-weight: bold; font-size: 13px; border:none;"
        )
        self._lbl_medecin.setStyleSheet(
            f"color: {c['text_muted']}; font-size: 10px; border: none;"
        )
        self._lbl_code.setStyleSheet(
            f"color: {c['primary']}; font-weight: bold; font-size: 13px;"
            "font-family: 'Consolas'; border: none;"
        )
        self._lbl_date.setStyleSheet(
            f"color: {c['text_secondary']}; font-size: 10px; border: none;"
        )

        # Scroll
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {c['bg_main']}; }}
            QScrollBar:vertical {{
                border: none; background: {c['border_light']};
                width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']}; border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {c['text_muted']}; }}
        """)

        # Reconstruction du contenu scrollable avec les nouvelles couleurs
        old = self._scroll.takeWidget()
        if old:
            old.deleteLater()
        content = QWidget()
        content.setStyleSheet(f"background: {c['bg_main']};")
        root = QHBoxLayout(content)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)
        root.addLayout(self._colonne_gauche(), 55)
        root.addLayout(self._colonne_droite(), 45)
        self._scroll.setWidget(content)

        # Footer
        self._footer.setStyleSheet(f"""
            background-color: {c['bg_main']};
            border-bottom-left-radius: 20px;
            border-bottom-right-radius: 20px;
            border-top: 1px solid {c['border']};
        """)
        self._btn_close.setIcon(qta.icon("fa5s.times", color=c['text_secondary']))
        self._btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_card']}; color: {c['text_secondary']};
                border-radius: 8px; font-weight: bold;
                padding: 8px 20px; border: 1px solid {c['border']};
            }}
            QPushButton:hover {{ background-color: {c['border_light']}; }}
        """)
        self._btn_print.setIcon(qta.icon("fa5s.print", color=c['text_inverse']))
        self._btn_print.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['primary']}; color: {c['text_inverse']};
                border-radius: 8px; font-weight: bold;
                padding: 8px 25px; border: none;
            }}
            QPushButton:hover {{ background-color: {c['primary_hover']}; }}
        """)

    # =========================================================================
    # HEADER
    # =========================================================================

    def _setup_header(self, layout):
        self._header = QFrame()
        self._header.setFixedHeight(80)

        h = QHBoxLayout(self._header)
        h.setContentsMargins(25, 10, 25, 10)

        cab = QVBoxLayout()
        cab.setSpacing(2)
        self._lbl_nom = QLabel(self.info_cabinet.get("nom_cabinet", "Cabinet Medical").upper())
        self._lbl_adr = QLabel(self.info_cabinet.get("adresse_cabinet", ""))
        self._lbl_adr.setWordWrap(True)
        cab.addWidget(self._lbl_nom)
        cab.addWidget(self._lbl_adr)
        h.addLayout(cab, 4)

        self._badge = QLabel("  EXAMEN MÉDICAL  ")
        h.addWidget(self._badge, 0, Qt.AlignVCenter)
        h.addStretch()

        logo_path = self.info_cabinet.get("logo_url")
        if logo_path and os.path.exists(logo_path):
            ll = QLabel()
            ll.setPixmap(QPixmap(logo_path).scaled(
                55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            ll.setStyleSheet("border: none; background: transparent;")
            h.addWidget(ll, 0, Qt.AlignRight)

        layout.addWidget(self._header)

    # =========================================================================
    # BANDEAU
    # =========================================================================

    def _setup_bandeau(self, layout):
        d = self.data
        nom_patient = (
            f"{d.get('patient_nom', '')} {d.get('patient_prenom', '')}".strip()
            or "Inconnu"
        )
        medecin = (
            f"Dr. {d.get('personnel_nom', '')} {d.get('personnel_prenom', '')} "
            f"— {d.get('personnel_fonction', '')}".strip()
        )
        date_val = d.get("date_examen", "")
        date_str = (
            date_val.strftime("%d/%m/%Y à %H:%M")
            if hasattr(date_val, "strftime") else str(date_val)
        )

        self._bandeau = QFrame()
        self._bandeau.setFixedHeight(75)

        b = QHBoxLayout(self._bandeau)
        b.setContentsMargins(25, 0, 25, 0)
        b.setSpacing(0)

        left = QVBoxLayout()
        left.setSpacing(3)
        self._lbl_patient = QLabel(f"PATIENT : {nom_patient.upper()}")
        self._lbl_medecin = QLabel(medecin)
        left.addWidget(self._lbl_patient)
        left.addWidget(self._lbl_medecin)
        b.addLayout(left)
        b.addStretch()

        right = QVBoxLayout()
        right.setSpacing(3)
        right.setAlignment(Qt.AlignRight)
        self._lbl_code = QLabel(f"N° {self.code_examen}")
        self._lbl_date = QLabel(date_str)
        right.addWidget(self._lbl_code, 0, Qt.AlignRight)
        right.addWidget(self._lbl_date, 0, Qt.AlignRight)
        b.addLayout(right)

        layout.addWidget(self._bandeau)

    # =========================================================================
    # CORPS  — 2 colonnes (contenu reconstruit dans apply_theme)
    # =========================================================================

    def _setup_corps(self, layout):
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        layout.addWidget(self._scroll)

    # ─── COLONNE GAUCHE : Libelle + Resultat ───

    def _colonne_gauche(self) -> QVBoxLayout:
        c = theme_manager.colors()
        col = QVBoxLayout()
        col.setSpacing(12)
        d = self.data

        col.addWidget(self._carte(
            titre     = "Libellé de l'Examen",
            icone     = "fa5s.microscope",
            couleur_bg= c['primary_light'],
            couleur_b = c['border'],
            couleur_t = c['primary'],
            contenu   = d.get("libelle_examen", "—"),
            grand     = False
        ))

        col.addWidget(self._carte(
            titre     = "Résultat de l'Examen",
            icone     = "fa5s.file-medical-alt",
            couleur_bg= c['success_bg'],
            couleur_b = c['border'],
            couleur_t = c['success'],
            contenu   = d.get("resultat_examen", "—"),
            grand     = True
        ))

        col.addStretch()
        return col

    # ─── COLONNE DROITE : Infos + Facturation + Codes ───

    def _colonne_droite(self) -> QVBoxLayout:
        c = theme_manager.colors()
        col = QVBoxLayout()
        col.setSpacing(12)
        d = self.data

        col.addWidget(self._bloc_infos(
            titre  = "Informations Patient",
            icone  = "fa5s.user-injured",
            couleur= c['primary'],
            lignes = [
                ("Nom complet",
                 f"{d.get('patient_nom','')} {d.get('patient_prenom','')}".strip() or "—"),
                ("Téléphone",  d.get("patient_telephone", "—")),
                ("Adresse",    d.get("patient_adresse",   "—")),
            ]
        ))

        frais  = d.get("frais_examen", 0)
        statut = d.get("statut_facture", "—")
        col.addWidget(self._bloc_facturation(frais, statut))

        col.addWidget(self._bloc_infos(
            titre  = "Traçabilité",
            icone  = "fa5s.link",
            couleur= c['accent'],
            lignes = [
                ("Code Examen",       d.get("code",              "—")),
                ("Code Consultation", d.get("code_consultation", "—")),
                ("Code Visite",       d.get("code_visite",       "—")),
                ("Code Session",      d.get("code_session",      "—")),
            ]
        ))

        col.addStretch()
        return col

    # =========================================================================
    # COMPOSANTS RÉUTILISABLES
    # =========================================================================

    def _carte(self, titre, icone, couleur_bg, couleur_b,
               couleur_t, contenu, grand=False) -> QFrame:
        c = theme_manager.colors()
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {couleur_bg}; border: 1px solid {couleur_b};"
            "border-radius: 12px;"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        head = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(qta.icon(icone, color=couleur_t).pixmap(14, 14))
        ic.setStyleSheet("border: none; background: transparent;")
        tl = QLabel(titre.upper())
        tl.setStyleSheet(
            f"font-weight: bold; color: {couleur_t}; font-size: 10px;"
            "letter-spacing: 0.5px; border: none; background: transparent;"
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

        lbl = QLabel(contenu or "—")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 12px; line-height: 1.5;"
            "border: none; background: transparent;"
        )
        if grand:
            lbl.setMinimumHeight(100)
            lbl.setAlignment(Qt.AlignTop)
        lay.addWidget(lbl)

        return frame

    def _bloc_infos(self, titre, icone, couleur, lignes) -> QFrame:
        c = theme_manager.colors()
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {c['bg_card']}; border: 1px solid {c['border']}; border-radius: 12px;"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)

        head = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(qta.icon(icone, color=couleur).pixmap(13, 13))
        ic.setStyleSheet("border: none; background: transparent;")
        tl = QLabel(titre.upper())
        tl.setStyleSheet(
            f"font-weight: bold; color: {couleur}; font-size: 10px;"
            "letter-spacing: 0.5px; border: none; background: transparent;"
        )
        head.addWidget(ic)
        head.addSpacing(5)
        head.addWidget(tl)
        head.addStretch()
        lay.addLayout(head)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {c['border']}; border: none;")
        lay.addWidget(sep)

        for label, valeur in lignes:
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl_k = QLabel(f"{label} :")
            lbl_k.setFixedWidth(120)
            lbl_k.setStyleSheet(
                f"color: {c['text_secondary']}; font-size: 11px; font-weight: 600;"
                "border: none; background: transparent;"
            )
            lbl_v = QLabel(str(valeur) if valeur else "—")
            lbl_v.setWordWrap(True)
            lbl_v.setStyleSheet(
                f"color: {c['text_primary']}; font-size: 11px;"
                "border: none; background: transparent;"
            )
            row.addWidget(lbl_k)
            row.addWidget(lbl_v, 1)
            lay.addLayout(row)

        return frame

    def _bloc_facturation(self, frais, statut) -> QFrame:
        c = theme_manager.colors()
        paye   = "payé" in str(statut).lower()
        bg     = c['success_bg'] if paye else c['warning_bg']
        border = c['border']
        c_stat = c['success']    if paye else c['warning']
        c_icon = "fa5s.check-circle" if paye else "fa5s.clock"

        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {bg}; border: 1px solid {border}; border-radius: 12px;"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        head = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(
            qta.icon("fa5s.file-invoice-dollar", color=c['primary']).pixmap(13, 13))
        ic.setStyleSheet("border: none; background: transparent;")
        tl = QLabel("FACTURATION")
        tl.setStyleSheet(
            f"font-weight: bold; color: {c['primary']}; font-size: 10px;"
            "letter-spacing: 0.5px; border: none; background: transparent;"
        )
        head.addWidget(ic)
        head.addSpacing(5)
        head.addWidget(tl)
        head.addStretch()
        lay.addLayout(head)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {border}; border: none;")
        lay.addWidget(sep)

        row_frais = QHBoxLayout()
        lbl_fk = QLabel("Frais d'examen :")
        lbl_fk.setStyleSheet(
            f"color: {c['text_secondary']}; font-size: 11px; font-weight: 600;"
            "border: none; background: transparent;"
        )
        lbl_fv = QLabel(f"{frais:,} GNF".replace(",", " ") if frais else "— GNF")
        lbl_fv.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 13px; font-weight: bold;"
            "border: none; background: transparent;"
        )
        row_frais.addWidget(lbl_fk)
        row_frais.addStretch()
        row_frais.addWidget(lbl_fv)
        lay.addLayout(row_frais)

        row_s = QHBoxLayout()
        ic_s = QLabel()
        ic_s.setPixmap(qta.icon(c_icon, color=c_stat).pixmap(13, 13))
        ic_s.setStyleSheet("border: none; background: transparent;")
        lbl_s = QLabel(str(statut))
        lbl_s.setStyleSheet(
            f"color: {c_stat}; font-size: 11px; font-weight: bold;"
            "border: none; background: transparent;"
        )
        row_s.addWidget(ic_s)
        row_s.addSpacing(5)
        row_s.addWidget(lbl_s)
        row_s.addStretch()
        lay.addLayout(row_s)

        return frame

    # =========================================================================
    # FOOTER
    # =========================================================================

    def _setup_footer(self, layout):
        self._footer = QFrame()
        self._footer.setFixedHeight(65)

        f = QHBoxLayout(self._footer)
        f.setContentsMargins(25, 0, 25, 0)
        f.setSpacing(12)

        self._btn_close = QPushButton(" Fermer")
        self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.clicked.connect(self.close)
        self._btn_close.setFixedHeight(38)

        self._btn_print = QPushButton(" Imprimer")
        self._btn_print.setCursor(Qt.PointingHandCursor)
        self._btn_print.setFixedHeight(38)

        f.addWidget(self._btn_close)
        f.addStretch()
        f.addWidget(self._btn_print)
        layout.addWidget(self._footer)
