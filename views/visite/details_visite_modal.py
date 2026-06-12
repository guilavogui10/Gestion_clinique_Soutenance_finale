"""
Modal détail visite — style uniforme PatientDetailDialog :
frameless, overlay semi-transparent, frame blanc arrondi, thème bleu.
Affiche infos visite + infos patient + actes médicaux (consultation,
examens, prescriptions, chirurgies, lunettes).
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QWidget, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter
import qtawesome as qta

from views.shared.theme_manager import theme_manager
from services.pdf_visite.visite_pdf import VisitePDFService
from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog


class DetailsVisiteModal(QDialog):
    """
    Modal dossier visite — même apparence que PatientDetailDialog.
    Accepte l'objet visite complet + le dict details + cabinet_info.
    """

    def __init__(self, parent, code_visite, patient_name, details_data,
                 cabinet_info=None, visite=None, patient_obj=None, numero_attente=0):
        super().__init__(parent)
        self.code_visite    = code_visite
        self.patient_name   = patient_name
        self.data           = details_data or {}
        self.cabinet_info   = cabinet_info or {}
        self.visite         = visite
        self.patient_obj    = patient_obj      # objet Patient complet (naissance, genre…)
        self.numero_attente = numero_attente

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)

        self._build_ui()
        self._apply_shadow()
        self._apply_styles()

    # ------------------------------------------------------------------
    # Overlay (identique PatientDetailDialog)
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if hasattr(self, 'frame') and self.frame.height() > 0:
            w = self.frame.width() + 80
            h = self.frame.height() + 80
            x = (self.width()  - w) // 2
            y = (self.height() - h) // 2
            painter.setBrush(QColor(0, 0, 0, 110))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, w, h, 24, 24)
        painter.end()

    def _apply_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 110))
        self.frame.setGraphicsEffect(shadow)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        c = theme_manager.colors()
        primary     = c['primary']
        pr_light    = c.get('primary_light', '#EBF0FB')

        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 16, 30, 16)
        outer.setAlignment(Qt.AlignCenter)

        # Frame blanc central
        self.frame = QFrame()
        self.frame.setObjectName("VDetailFrame")
        self.frame.setFixedWidth(560)

        fl = QVBoxLayout(self.frame)
        fl.setContentsMargins(20, 10, 20, 14)
        fl.setSpacing(0)

        # ── ✕ Fermer ──────────────────────────────────────────────────
        top = QHBoxLayout()
        top.addStretch()
        self._btn_x = QPushButton("✕")
        self._btn_x.setObjectName("VDetailClose")
        self._btn_x.setFixedSize(30, 30)
        self._btn_x.setCursor(Qt.PointingHandCursor)
        self._btn_x.clicked.connect(self.reject)
        top.addWidget(self._btn_x)
        fl.addLayout(top)
        fl.addSpacing(2)

        # ── Avatar + Nom + badge ───────────────────────────────────────
        av_frame = QFrame()
        av_frame.setObjectName("VDetailAvatar")
        av_frame.setFixedSize(54, 54)
        av_lay = QVBoxLayout(av_frame)
        av_lay.setContentsMargins(0, 0, 0, 0)
        av_lay.setAlignment(Qt.AlignCenter)
        lbl_av = QLabel()
        lbl_av.setAlignment(Qt.AlignCenter)
        lbl_av.setPixmap(qta.icon("fa5s.hospital-user", color="white").pixmap(26, 26))
        av_lay.addWidget(lbl_av)

        av_wrap = QHBoxLayout()
        av_wrap.addStretch()
        av_wrap.addWidget(av_frame)
        av_wrap.addStretch()
        fl.addLayout(av_wrap)
        fl.addSpacing(6)

        lbl_nom = QLabel(self.patient_name or "Patient inconnu")
        lbl_nom.setObjectName("VDetailNom")
        lbl_nom.setAlignment(Qt.AlignCenter)
        lbl_nom.setWordWrap(True)
        fl.addWidget(lbl_nom)
        fl.addSpacing(3)

        badge_wrap = QHBoxLayout()
        badge_wrap.addStretch()
        lbl_badge = QLabel(f"  {self.code_visite}  ")
        lbl_badge.setObjectName("VDetailBadge")
        lbl_badge.setAlignment(Qt.AlignCenter)
        badge_wrap.addWidget(lbl_badge)
        badge_wrap.addStretch()
        fl.addLayout(badge_wrap)
        fl.addSpacing(10)

        # ── Séparateur ────────────────────────────────────────────────
        fl.addWidget(self._sep())
        fl.addSpacing(8)

        # ── INFO VISITE (cards 2 colonnes) ────────────────────────────
        fl.addWidget(self._section_label("fa5s.calendar-check", "Informations de la visite"))
        fl.addSpacing(5)

        v = self.visite
        infos_visite = [
            ("fa5s.tag",           "Type de visite",  str(v.get_type_visite()   if v else "—") or "—"),
            ("fa5s.exclamation",   "Urgence",         str(v.get_urgent()         if v else "—") or "—"),
            ("fa5s.clock",         "Statut",          str(v.get_statut_patient() if v else "—") or "—"),
            ("fa5s.calendar-alt",  "Date visite",     self._fmt_date(v.get_date_visite() if v else None)),
        ]
        if self.numero_attente and self.numero_attente > 0:
            infos_visite.append(
                ("fa5s.sort-numeric-up", "N° file d'attente", str(self.numero_attente))
            )
        fl.addLayout(self._grid_cards(infos_visite, cols=2))
        fl.addSpacing(8)

        # ── INFO PATIENT ──────────────────────────────────────────────
        fl.addWidget(self._section_label("fa5s.user", "Informations patient"))
        fl.addSpacing(5)

        tel = getattr(v, 'tel_patient', '—') if v else '—'
        infos_patient = [
            ("fa5s.phone-alt",  "Téléphone",     str(tel) or "—"),
            ("fa5s.id-card",    "Code patient",  str(v.get_code_patient() if v else "—") or "—"),
        ]
        fl.addLayout(self._grid_cards(infos_patient, cols=2))
        fl.addSpacing(8)

        # ── Séparateur ────────────────────────────────────────────────
        fl.addWidget(self._sep())
        fl.addSpacing(6)

        # ── ACTES MÉDICAUX (zone scrollable) ──────────────────────────
        fl.addWidget(self._section_label("fa5s.notes-medical", "Actes médicaux"))
        fl.addSpacing(5)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(240)
        _c = theme_manager.colors()
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ border: none; background: {_c['bg_input']};
                width: 6px; border-radius: 3px; }}
            QScrollBar::handle:vertical {{ background: {_c['border']}; border-radius: 3px; }}
        """)
        actes_widget = QWidget()
        actes_widget.setStyleSheet("background: transparent;")
        actes_layout = QVBoxLayout(actes_widget)
        actes_layout.setContentsMargins(0, 0, 4, 0)
        actes_layout.setSpacing(8)

        sections = [
            ("fa5s.stethoscope", "Consultations",  "consultations",
             [("Diagnostic",   "diagnostique"),
              ("Résultat",     "resultat_consultation")]),
            ("fa5s.microscope","Examens",           "examens",
             [("Examen",      "libelle_examen"),
              ("Conclusion",  "conclusion_medicale")]),
            ("fa5s.pills",    "Prescriptions",     "prescriptions",
             [("Produit",     "designation"),
              ("Quantité",    "quantite_prescript"),
              ("Prix",        "prix_applique")]),
            ("fa5s.procedures","Chirurgies",        "chirurgies",
             [("Acte",        "libelle_chururgie"),
              ("Date",        "date_chururgie")]),
            ("fa5s.glasses",  "Optique",           "lunettes",
             [("Cadre",       "numero_cadre"),
              ("Verre",       "numero_verre")]),
        ]

        has_data = False
        for ico, titre, key, champs in sections:
            items = self.data.get(key, [])
            if not items:
                continue
            has_data = True
            actes_layout.addWidget(self._acte_card(ico, titre, items, champs))

        if not has_data:
            lbl_vide = QLabel("Aucun acte médical enregistré pour cette visite.")
            lbl_vide.setStyleSheet(f"color: {theme_manager.colors()['text_muted']}; font-size: 12px; padding: 12px;")
            lbl_vide.setAlignment(Qt.AlignCenter)
            actes_layout.addWidget(lbl_vide)

        actes_layout.addStretch()
        scroll.setMaximumHeight(180)
        scroll.setWidget(actes_widget)
        fl.addWidget(scroll)
        fl.addSpacing(10)

        # ── Boutons ───────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_fermer = QPushButton("  Fermer")
        btn_fermer.setObjectName("VDetailSecondary")
        btn_fermer.setFixedHeight(38)
        btn_fermer.setCursor(Qt.PointingHandCursor)
        btn_fermer.setIcon(qta.icon("fa5s.times", color=theme_manager.colors()['text_secondary']))
        btn_fermer.clicked.connect(self.reject)

        self.btn_print = QPushButton("  Imprimer la fiche")
        self.btn_print.setObjectName("VDetailPrimary")
        self.btn_print.setFixedHeight(38)
        self.btn_print.setCursor(Qt.PointingHandCursor)
        self.btn_print.setIcon(qta.icon("fa5s.print", color="white"))
        self.btn_print.clicked.connect(self._imprimer)

        btn_row.addWidget(btn_fermer, 1)
        btn_row.addWidget(self.btn_print, 2)
        fl.addLayout(btn_row)

        outer.addWidget(self.frame)

    # ------------------------------------------------------------------
    # Helpers UI
    # ------------------------------------------------------------------
    def _sep(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("VDetailSep")
        return sep

    def _section_label(self, icon_name: str, texte: str) -> QLabel:
        c = theme_manager.colors()
        lbl = QLabel(f"  {texte}")
        lbl.setObjectName("VDetailSectionLabel")
        lbl.setPixmap(qta.icon(icon_name, color=c['primary']).pixmap(14, 14))
        # Utilise HTML pour icône inline
        lbl = QLabel(texte)
        lbl.setObjectName("VDetailSectionLabel")
        return lbl

    def _grid_cards(self, infos: list, cols: int = 2) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(10)
        for i, (ico, label, value) in enumerate(infos):
            card = self._make_card(ico, label, value)
            grid.addWidget(card, i // cols, i % cols)
        return grid

    def _make_card(self, icon_name: str, label: str, value: str) -> QFrame:
        c = theme_manager.colors()
        card = QFrame()
        card.setObjectName("VDetailCard")
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(10)

        lbl_ic = QLabel()
        lbl_ic.setPixmap(qta.icon(icon_name, color=c['primary']).pixmap(15, 15))
        lbl_ic.setFixedSize(17, 17)
        row.addWidget(lbl_ic)

        col = QVBoxLayout()
        col.setSpacing(2)
        lbl_l = QLabel(label)
        lbl_l.setObjectName("VDetailCardLabel")
        lbl_v = QLabel(value or "—")
        lbl_v.setObjectName("VDetailCardValue")
        lbl_v.setWordWrap(True)
        col.addWidget(lbl_l)
        col.addWidget(lbl_v)
        row.addLayout(col)
        return card

    def _acte_card(self, icon_name: str, titre: str, items: list, champs: list) -> QFrame:
        c = theme_manager.colors()
        card = QFrame()
        card.setObjectName("VDetailActeCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)

        # Titre section
        head = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(qta.icon(icon_name, color=c['primary']).pixmap(14, 14))
        ic.setFixedSize(16, 16)
        t = QLabel(titre.upper())
        t.setObjectName("VDetailActeTitre")
        head.addWidget(ic)
        head.addSpacing(4)
        head.addWidget(t)
        head.addStretch()
        lay.addLayout(head)

        # Lignes de données
        for item in items:
            parts = []
            for label, key in champs:
                val = item.get(key, "") if isinstance(item, dict) else getattr(item, key, "")
                if val:
                    parts.append(f"{label}: {val}")
            if parts:
                lbl = QLabel("  •  " + "   |   ".join(parts))
                lbl.setObjectName("VDetailActeItem")
                lbl.setWordWrap(True)
                lay.addWidget(lbl)

        return card

    def _fmt_date(self, val) -> str:
        if not val:
            return "—"
        try:
            if hasattr(val, 'strftime'):
                return val.strftime('%d/%m/%Y %H:%M')
            return str(val)[:16]
        except Exception:
            return str(val)

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------
    def _apply_styles(self):
        c = theme_manager.colors()

        self.frame.setStyleSheet(f"""
            QFrame#VDetailFrame {{
                background: {c['bg_card']};
                border-radius: 20px;
                border: none;
            }}
        """)

        self.setStyleSheet(f"""
            QPushButton#VDetailClose {{
                background: {c['bg_input']}; border: none; border-radius: 15px;
                color: {c['text_muted']}; font-size: 13px; font-weight: 700;
            }}
            QPushButton#VDetailClose:hover {{ background: {c['hover']}; color: {c['text_primary']}; }}

            QFrame#VDetailAvatar {{
                background: {c['primary']};
                border-radius: 27px;
            }}

            QLabel#VDetailNom {{
                color: {c['text_primary']}; font-size: 17px; font-weight: 700; background: transparent;
            }}
            QLabel#VDetailBadge {{
                background: {c['primary_light']}; color: {c['primary']};
                font-size: 12px; font-weight: 700; border-radius: 10px; padding: 3px 0px;
            }}

            QFrame#VDetailSep {{ color: {c['border_light']}; max-height: 1px; }}

            QLabel#VDetailSectionLabel {{
                color: {c['primary']}; font-size: 12px; font-weight: 700; background: transparent;
                padding-bottom: 2px;
            }}

            QFrame#VDetailCard {{
                background: {c['bg_input']}; border-radius: 10px; border: 1px solid {c['border_light']};
            }}
            QLabel#VDetailCardLabel {{
                color: {c['text_muted']}; font-size: 10px; font-weight: 500; background: transparent;
            }}
            QLabel#VDetailCardValue {{
                color: {c['text_primary']}; font-size: 13px; font-weight: 600; background: transparent;
            }}

            QFrame#VDetailActeCard {{
                background: {c['bg_input']}; border-radius: 10px; border: 1px solid {c['border_light']};
            }}
            QLabel#VDetailActeTitre {{
                color: {c['primary']}; font-size: 10px; font-weight: 700; background: transparent;
            }}
            QLabel#VDetailActeItem {{
                color: {c['text_secondary']}; font-size: 11px; background: transparent;
            }}

            QPushButton#VDetailSecondary {{
                background: transparent; border: 2px solid {c['border']}; border-radius: 12px;
                color: {c['text_secondary']}; font-size: 13px; font-weight: 600;
                padding-left: 6px; text-align: left;
            }}
            QPushButton#VDetailSecondary:hover {{
                background: {c['hover']}; border-color: {c['text_muted']};
                color: {c['text_primary']};
            }}

            QPushButton#VDetailPrimary {{
                background: {c['primary']}; border: none; border-radius: 12px;
                color: {c['text_inverse']}; font-size: 13px; font-weight: 700;
                padding-left: 6px; text-align: left;
            }}
            QPushButton#VDetailPrimary:hover {{ background: {c['primary_hover']}; }}
        """)

    # ------------------------------------------------------------------
    # Impression
    # ------------------------------------------------------------------
    def _imprimer(self):
        from views.shared.message_box import CustomMessageBox
        try:
            pdf_path = VisitePDFService.generer_carnet_visite(
                code_visite    = self.code_visite,
                patient_name   = self.patient_name,
                visite         = self.visite,
                details        = self.data,
                cabinet_info   = self.cabinet_info,
                patient_obj    = self.patient_obj,
                numero_attente = self.numero_attente,
            )
            ApercuPDFDialog(pdf_path, f"Carnet de visite — {self.code_visite}", self).exec()
        except Exception as e:
            CustomMessageBox("Erreur", f"Impossible de générer le carnet :\n{e}",
                             msg_type="error", parent=self).exec()
