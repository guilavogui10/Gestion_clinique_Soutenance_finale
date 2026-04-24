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
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {MC.BG_CARD};
                border-radius: 20px;
                border: 1px solid {MC.BORDER};
            }}
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

    # =========================================================================
    # HEADER
    # =========================================================================

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

        # Texte cabinet
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

        # Badge "EXAMEN MEDICAL"
        badge = QLabel("  EXAMEN MÉDICAL  ")
        badge.setStyleSheet("""
            background-color: #EFF6FF;
            color: #3B82F6;
            border: 1px solid #BFDBFE;
            border-radius: 8px;
            font-weight: bold;
            font-size: 10px;
            padding: 4px 8px;
        """)
        h.addWidget(badge, 0, Qt.AlignVCenter)
        h.addStretch()

        # Logo
        logo_path = self.info_cabinet.get("logo_url")
        if logo_path and os.path.exists(logo_path):
            ll = QLabel()
            ll.setPixmap(QPixmap(logo_path).scaled(
                55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            ll.setStyleSheet("border: none; background: transparent;")
            h.addWidget(ll, 0, Qt.AlignRight)

        layout.addWidget(header)

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

        bandeau = QFrame()
        bandeau.setFixedHeight(75)
        bandeau.setStyleSheet(
            f"background-color: {MC.TEXT_PRIMARY}; border: none;"
        )
        b = QHBoxLayout(bandeau)
        b.setContentsMargins(25, 0, 25, 0)
        b.setSpacing(0)

        # Gauche : patient + medecin
        left = QVBoxLayout()
        left.setSpacing(3)
        lbl_p = QLabel(f"PATIENT : {nom_patient.upper()}")
        lbl_p.setStyleSheet(
            f"color: {MC.BG_MAIN}; font-weight: bold; font-size: 13px; border:none;"
        )
        lbl_m = QLabel(medecin)
        lbl_m.setStyleSheet(
            f"color: {MC.TEXT_MUTED}; font-size: 10px; border: none;"
        )
        left.addWidget(lbl_p)
        left.addWidget(lbl_m)
        b.addLayout(left)
        b.addStretch()

        # Droite : code + date
        right = QVBoxLayout()
        right.setSpacing(3)
        right.setAlignment(Qt.AlignRight)
        lbl_code = QLabel(f"N° {self.code_examen}")
        lbl_code.setStyleSheet(
            "color: #3B82F6; font-weight: bold; font-size: 13px;"
            "font-family: 'Consolas'; border: none;"
        )
        lbl_date = QLabel(date_str)
        lbl_date.setStyleSheet(
            f"color: {MC.TEXT_SECONDARY}; font-size: 10px; border: none;"
        )
        right.addWidget(lbl_code, 0, Qt.AlignRight)
        right.addWidget(lbl_date, 0, Qt.AlignRight)
        b.addLayout(right)

        layout.addWidget(bandeau)

    # =========================================================================
    # CORPS  — 2 colonnes
    # =========================================================================

    def _setup_corps(self, layout):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {MC.BG_MAIN}; }}
            QScrollBar:vertical {{
                border: none; background: {MC.BORDER_LIGHT};
                width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {MC.BORDER}; border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {MC.TEXT_MUTED}; }}
        """)

        content = QWidget()
        content.setStyleSheet(f"background: {MC.BG_MAIN};")
        root = QHBoxLayout(content)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        root.addLayout(self._colonne_gauche(), 55)
        root.addLayout(self._colonne_droite(), 45)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    # ─── COLONNE GAUCHE : Libelle + Resultat ───

    def _colonne_gauche(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(12)

        d = self.data

        # ── Carte Libelle ──
        col.addWidget(self._carte(
            titre     = "Libellé de l'Examen",
            icone     = "fa5s.microscope",
            couleur_bg= "#EFF6FF",
            couleur_b = "#BFDBFE",
            couleur_t = "#3B82F6",
            contenu   = d.get("libelle_examen", "—"),
            grand     = False
        ))

        # ── Carte Resultat ──
        col.addWidget(self._carte(
            titre     = "Résultat de l'Examen",
            icone     = "fa5s.file-medical-alt",
            couleur_bg= "#F0FDF4",
            couleur_b = "#BBF7D0",
            couleur_t = MC.PRIMARY,
            contenu   = d.get("resultat_examen", "—"),
            grand     = True
        ))

        col.addStretch()
        return col

    # ─── COLONNE DROITE : Infos + Facturation + Codes ───

    def _colonne_droite(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(12)

        d = self.data

        # ── Infos Patient ──
        col.addWidget(self._bloc_infos(
            titre  = "Informations Patient",
            icone  = "fa5s.user-injured",
            couleur= MC.PRIMARY,
            lignes = [
                ("Nom complet",
                 f"{d.get('patient_nom','')} {d.get('patient_prenom','')}".strip() or "—"),
                ("Téléphone",  d.get("patient_telephone", "—")),
                ("Adresse",    d.get("patient_adresse",   "—")),
            ]
        ))

        # ── Facturation ──
        frais  = d.get("frais_examen", 0)
        statut = d.get("statut_facture", "—")
        col.addWidget(self._bloc_facturation(frais, statut))

        # ── Codes de traçabilité ──
        col.addWidget(self._bloc_infos(
            titre  = "Traçabilité",
            icone  = "fa5s.link",
            couleur= "#6366F1",
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
        """Carte avec titre coloré et contenu textuel."""
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {couleur_bg}; border: 1px solid {couleur_b};"
            "border-radius: 12px;"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        # Titre
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

        # Contenu
        lbl = QLabel(contenu or "—")
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"color: {MC.TEXT_PRIMARY}; font-size: 12px; line-height: 1.5;"
            "border: none; background: transparent;"
        )
        if grand:
            lbl.setMinimumHeight(100)
            lbl.setAlignment(Qt.AlignTop)
        lay.addWidget(lbl)

        return frame

    def _bloc_infos(self, titre, icone, couleur, lignes) -> QFrame:
        """Bloc liste de paires label : valeur."""
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {MC.BG_CARD}; border: 1px solid {MC.BORDER}; border-radius: 12px;"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)

        # Titre
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
        sep.setStyleSheet(f"background: {MC.BORDER}; border: none;")
        lay.addWidget(sep)

        # Lignes
        for label, valeur in lignes:
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl_k = QLabel(f"{label} :")
            lbl_k.setFixedWidth(120)
            lbl_k.setStyleSheet(
                f"color: {MC.TEXT_SECONDARY}; font-size: 11px; font-weight: 600;"
                "border: none; background: transparent;"
            )
            lbl_v = QLabel(str(valeur) if valeur else "—")
            lbl_v.setWordWrap(True)
            lbl_v.setStyleSheet(
                f"color: {MC.TEXT_PRIMARY}; font-size: 11px;"
                "border: none; background: transparent;"
            )
            row.addWidget(lbl_k)
            row.addWidget(lbl_v, 1)
            lay.addLayout(row)

        return frame

    def _bloc_facturation(self, frais, statut) -> QFrame:
        """Bloc facturation avec couleur selon statut."""
        paye   = "payé" in str(statut).lower()
        bg     = "#F0FDF4" if paye else "#FFF7ED"
        border = "#BBF7D0" if paye else "#FED7AA"
        c_stat = "#16A34A" if paye else "#EA580C"
        c_icon = "fa5s.check-circle" if paye else "fa5s.clock"

        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {bg}; border: 1px solid {border}; border-radius: 12px;"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        # Titre
        head = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(
            qta.icon("fa5s.file-invoice-dollar", color=MC.PRIMARY).pixmap(13, 13))
        ic.setStyleSheet("border: none; background: transparent;")
        tl = QLabel("FACTURATION")
        tl.setStyleSheet(
            f"font-weight: bold; color: {MC.PRIMARY}; font-size: 10px;"
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

        # Frais
        row_frais = QHBoxLayout()
        lbl_fk = QLabel("Frais d'examen :")
        lbl_fk.setStyleSheet(
            f"color: {MC.TEXT_SECONDARY}; font-size: 11px; font-weight: 600;"
            "border: none; background: transparent;"
        )
        lbl_fv = QLabel(f"{frais:,} GNF".replace(",", " ") if frais else "— GNF")
        lbl_fv.setStyleSheet(
            f"color: {MC.TEXT_PRIMARY}; font-size: 13px; font-weight: bold;"
            "border: none; background: transparent;"
        )
        row_frais.addWidget(lbl_fk)
        row_frais.addStretch()
        row_frais.addWidget(lbl_fv)
        lay.addLayout(row_frais)

        # Statut
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
        footer = QFrame()
        footer.setFixedHeight(65)
        footer.setStyleSheet(f"""
            background-color: {MC.BG_MAIN};
            border-bottom-left-radius: 20px;
            border-bottom-right-radius: 20px;
            border-top: 1px solid {MC.BORDER};
        """)
        f = QHBoxLayout(footer)
        f.setContentsMargins(25, 0, 25, 0)
        f.setSpacing(12)

        btn_close = QPushButton(
            qta.icon("fa5s.times", color=MC.TEXT_SECONDARY), " Fermer")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.close)
        btn_close.setFixedHeight(38)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {MC.BG_CARD}; color: {MC.TEXT_SECONDARY};
                border-radius: 8px; font-weight: bold;
                padding: 8px 20px; border: 1px solid {MC.BORDER};
            }}
            QPushButton:hover {{ background-color: {MC.BORDER_LIGHT}; }}
        """)

        btn_print = QPushButton(
            qta.icon("fa5s.print", color="white"), " Imprimer")
        btn_print.setCursor(Qt.PointingHandCursor)
        btn_print.setFixedHeight(38)
        btn_print.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6; color: white;
                border-radius: 8px; font-weight: bold;
                padding: 8px 25px; border: none;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)

        f.addWidget(btn_close)
        f.addStretch()
        f.addWidget(btn_print)
        layout.addWidget(footer)