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


class DetailsCommandeLunetteModal(QDialog):
    """
    Modal d affichage complet d une commande de lunettes.
    Layout :
        - Header  : infos cabinet + logo
        - Bandeau : patient + code + date + medecin
        - Corps   : 2 colonnes
            Gauche  : Numéros Cadre/Verre + Dates
            Droite  : Infos patient + Facturation + Codes
        - Footer  : Fermer + Imprimer
    """

    def __init__(self, parent, code_commande: str, ctrl):
        super().__init__(parent)
        self.ctrl         = ctrl
        self.code_commande = code_commande

        self.data         = self.ctrl.obtenir_commande_complete(code_commande) or {}
        self.info_cabinet = (
            self.ctrl.get_cabinet_info()
            if hasattr(self.ctrl, "get_cabinet_info") else {}
        )

        self.setWindowTitle(f"Dossier Commande Lunettes - {code_commande}")
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
            f"border: none; background: {MC.BG_CARD};"
        )
        adr = QLabel(self.info_cabinet.get("adresse_cabinet", ""))
        adr.setStyleSheet(f"color: {MC.TEXT_SECONDARY}; font-size: 10px; border: none; background: {MC.BG_CARD};")
        adr.setWordWrap(True)
        cab.addWidget(nom)
        cab.addWidget(adr)
        h.addLayout(cab, 4)

        # Badge "COMMANDE LUNETTES"
        badge = QLabel("  COMMANDE LUNETTES  ")
        badge.setStyleSheet(f"""
            background-color: {MC.INFO_BG};
            color: {MC.INFO};
            border: 1px solid {MC.BORDER_LIGHT};
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
            ll.setStyleSheet(f"border: none; background: {MC.BG_CARD};")
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
        date_val = d.get("date_commande", "")
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
        lbl_code = QLabel(f"N° {self.code_commande}")
        lbl_code.setStyleSheet(
            f"color: {MC.INFO}; font-weight: bold; font-size: 13px;"
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

    # ─── COLONNE GAUCHE : Numéros + Dates ───

    def _colonne_gauche(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(12)

        d = self.data

        # ── Carte Numéro Cadre ──
        col.addWidget(self._carte(
            titre     = "Numéro de Cadre",
            icone     = "fa5s.glasses",
            couleur_bg= MC.INFO_BG,
            couleur_b = MC.BORDER_LIGHT,
            couleur_t = MC.INFO,
            contenu   = d.get("numero_cadre", "—"),
            grand     = False
        ))

        # ── Carte Numéro Verre ──
        col.addWidget(self._carte(
            titre     = "Numéro Verre Prescrit",
            icone     = "fa5s.eye",
            couleur_bg= MC.SUCCESS_BG,
            couleur_b = MC.SUCCESS,
            couleur_t = MC.PRIMARY,
            contenu   = d.get("numero_verre", "—"),
            grand     = False
        ))

        # ── Carte Dates ──
        date_livraison = d.get("date_livraison", "")
        date_liv_str = (
            date_livraison.strftime("%d/%m/%Y")
            if hasattr(date_livraison, "strftime") else str(date_livraison) if date_livraison else "—"
        )
        
        col.addWidget(self._carte(
            titre     = "Date de Livraison Prévue",
            icone     = "fa5s.calendar-alt",
            couleur_bg= MC.WARNING_BG,
            couleur_b = MC.WARNING,
            couleur_t = MC.WARNING,
            contenu   = date_liv_str,
            grand     = False
        ))

        # ── Carte Statut ──
        statut = d.get("statut", "—")
        col.addWidget(self._carte(
            titre     = "Statut de la Commande",
            icone     = "fa5s.info-circle",
            couleur_bg= MC.INFO_BG,
            couleur_b = MC.ACCENT,
            couleur_t = MC.ACCENT,
            contenu   = str(statut).upper(),
            grand     = False
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
        prix   = d.get("prix", 0)
        statut = d.get("statut_facture", "—")
        col.addWidget(self._bloc_facturation(prix, statut))

        # ── Codes de traçabilité ──
        col.addWidget(self._bloc_infos(
            titre  = "Traçabilité",
            icone  = "fa5s.link",
            couleur= MC.ACCENT,
            lignes = [
                ("Code Commande",     d.get("code",              "—")),
                ("Code Consultation", d.get("code_consultation", "—")),
                ("Code Acte",         d.get("code_acte",         "—")),
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
        ic.setStyleSheet(f"border: none; background: {MC.BG_CARD};")
        tl = QLabel(titre.upper())
        tl.setStyleSheet(
            f"font-weight: bold; color: {couleur_t}; font-size: 10px;"
            f"letter-spacing: 0.5px; border: none; background: {MC.BG_CARD};"
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
            f"border: none; background: {MC.BG_CARD};"
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
        ic.setStyleSheet(f"border: none; background: {MC.BG_CARD};")
        tl = QLabel(titre.upper())
        tl.setStyleSheet(
            f"font-weight: bold; color: {couleur}; font-size: 10px;"
            f"letter-spacing: 0.5px; border: none; background: {MC.BG_CARD};"
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
                f"border: none; background: {MC.BG_CARD};"
            )
            lbl_v = QLabel(str(valeur) if valeur else "—")
            lbl_v.setWordWrap(True)
            lbl_v.setStyleSheet(
                f"color: {MC.TEXT_PRIMARY}; font-size: 11px;"
                f"border: none; background: {MC.BG_CARD};"
            )
            row.addWidget(lbl_k)
            row.addWidget(lbl_v, 1)
            lay.addLayout(row)

        return frame

    def _bloc_facturation(self, prix, statut) -> QFrame:
        """Bloc facturation avec couleur selon statut."""
        paye   = "payé" in str(statut).lower() or "attente payement" in str(statut).lower()
        bg     = MC.SUCCESS_BG if paye else MC.WARNING_BG
        border = MC.SUCCESS   if paye else MC.WARNING
        c_stat = MC.SUCCESS   if paye else MC.WARNING
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
        ic.setStyleSheet(f"border: none; background: {MC.BG_CARD};")
        tl = QLabel("FACTURATION")
        tl.setStyleSheet(
            f"font-weight: bold; color: {MC.PRIMARY}; font-size: 10px;"
            f"letter-spacing: 0.5px; border: none; background: {MC.BG_CARD};"
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

        # Prix
        row_prix = QHBoxLayout()
        lbl_pk = QLabel("Prix :")
        lbl_pk.setStyleSheet(
            f"color: {MC.TEXT_SECONDARY}; font-size: 11px; font-weight: 600;"
            f"border: none; background: {MC.BG_CARD};"
        )
        lbl_pv = QLabel(f"{prix:,} GNF".replace(",", " ") if prix else "— GNF")
        lbl_pv.setStyleSheet(
            f"color: {MC.TEXT_PRIMARY}; font-size: 13px; font-weight: bold;"
            f"border: none; background: {MC.BG_CARD};"
        )
        row_prix.addWidget(lbl_pk)
        row_prix.addStretch()
        row_prix.addWidget(lbl_pv)
        lay.addLayout(row_prix)

        # Statut
        row_s = QHBoxLayout()
        ic_s = QLabel()
        ic_s.setPixmap(qta.icon(c_icon, color=c_stat).pixmap(13, 13))
        ic_s.setStyleSheet(f"border: none; background: {MC.BG_CARD};")
        lbl_s = QLabel(str(statut))
        lbl_s.setStyleSheet(
            f"color: {c_stat}; font-size: 11px; font-weight: bold;"
            f"border: none; background: {MC.BG_CARD};"
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
            qta.icon("fa5s.print", color=MC.TEXT_INVERSE), " Imprimer")
        btn_print.setCursor(Qt.PointingHandCursor)
        btn_print.setFixedHeight(38)
        btn_print.setStyleSheet(f"""
            QPushButton {{
                background-color: {MC.INFO}; color: {MC.TEXT_INVERSE};
                border-radius: 8px; font-weight: bold;
                padding: 8px 25px; border: none;
            }}
            QPushButton:hover {{ background-color: {MC.PRIMARY_HOVER}; }}
        """)

        f.addWidget(btn_close)
        f.addStretch()
        f.addWidget(btn_print)
        layout.addWidget(footer)
