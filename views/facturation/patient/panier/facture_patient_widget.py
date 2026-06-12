"""
Widget facture patient - Nouveau design "Paiement de Facture".
Architecture : MVC + composants + handlers.
Responsabilite : orchestrer UI et workflow facture patient.
"""

from typing import Any, Dict, List, Optional

import qtawesome as qta
from PySide6.QtCore import Qt, Signal, QDate, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QScrollArea, QWidget,
    QPushButton, QComboBox, QCheckBox, QLineEdit, QDateEdit, QSizePolicy,
    QButtonGroup
)

from .components.animated_frame import AnimatedFrame
from .components.facture_patient_line_dialog import FacturePatientLineDialog
from views.shared.message_box import CustomMessageBox
from .handlers.facture_patient_data_loader import FacturePatientDataLoader
from .handlers.facture_patient_operations import FacturePatientOperations
from .styles.facture_patient_styles import FacturePatientStyles
from views.shared.modal_theme import MC
from views.shared.theme_manager import theme_manager
from views.shared.theme_fix import force_theme_recursive, fix_black_widgets


class FacturePatientWidget(AnimatedFrame):
    """Widget principal facture patient - Design Paiement de Facture."""

    paiement_effectue = Signal()
    facture_mise_a_jour = Signal()

    # Couleurs dynamiques liées au thème
    @property
    def BLEU(self):        return theme_manager.colors()['primary']
    @property
    def VERT(self):        return theme_manager.colors()['success']
    @property
    def ROUGE(self):       return theme_manager.colors()['danger']
    @property
    def BG_PAGE(self):     return theme_manager.colors()['bg_main']
    @property
    def BG_CARD(self):     return theme_manager.colors()['bg_card']
    @property
    def BORDER(self):      return theme_manager.colors()['border']
    @property
    def TXT_PRIMARY(self): return theme_manager.colors()['text_primary']
    @property
    def TXT_SEC(self):     return theme_manager.colors()['text_secondary']

    def __init__(self, facture_ctrl=None, panier_ctrl=None, parent=None):
        super().__init__(parent)

        self.facture_ctrl = facture_ctrl
        self.panier_ctrl = panier_ctrl

        self.code_session: Optional[str] = None
        self.code_visite: Optional[str] = None
        self.code_facture: Optional[str] = None
        self._patient_data: Dict[str, Any] = {}
        self._date_facture_str: str = "—"
        self.lignes_panier: List[Any] = []
        self._services_visite: List[Dict[str, Any]] = []

        self.data_loader = FacturePatientDataLoader(self.BLEU)
        self.operations = FacturePatientOperations(facture_ctrl, panier_ctrl, self.BLEU)

        self._init_ui()
        self._connecter_signaux()
        theme_manager.theme_changed.connect(self.apply_theme)

    # =========================================================================
    # UI PRINCIPALE
    # =========================================================================

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 1. Carte patient + KPI (sans en-tête) ─────────────────────────
        root.addWidget(self._build_patient_bar())

        # ── 2. Corps : panier (gauche) | paiement (droite) ─────────────────
        body = QHBoxLayout()
        body.setContentsMargins(16, 12, 16, 12)
        body.setSpacing(16)
        self._left_panel  = self._build_left_panel()
        self._right_panel = self._build_right_panel()
        body.addWidget(self._left_panel,  6)
        body.addWidget(self._right_panel, 4)
        root.addLayout(body, 1)

        # Appliquer le thème après que tous les widgets sont créés
        self.apply_theme()
        # Forcer le thème récursivement pour éliminer les widgets noirs
        force_theme_recursive(self, force_bg=True)

    # ─── En-tête ──────────────────────────────────────────────────────────

    def _build_top_header(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(64)
        bar.setStyleSheet(
            f"background: {self.BG_CARD}; border-bottom: 1px solid {self.BORDER}; border-radius: 0;"
        )
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)

        # Titre
        vbox = QVBoxLayout()
        vbox.setSpacing(0)
        title = QLabel("Paiement de Facture")
        title.setStyleSheet(
            f"font-size:18px; font-weight:bold; color:{self.TXT_PRIMARY}; border:none; background:transparent;"
        )
        sub = QLabel("Facturez et encaissez les services du patient")
        sub.setStyleSheet(f"font-size:11px; color:{self.TXT_SEC}; border:none; background:transparent;")
        vbox.addWidget(title)
        vbox.addWidget(sub)
        lay.addLayout(vbox)
        lay.addStretch()

        # Sélecteur patient
        combo_label = QLabel("Patient :")
        combo_label.setStyleSheet(
            f"font-size:12px; font-weight:bold; color:{self.TXT_SEC}; border:none; background:transparent;"
        )
        self.combo_visite = QComboBox()
        self.combo_visite.setFixedHeight(36)
        self.combo_visite.setMinimumWidth(300)
        self.combo_visite.setStyleSheet(f"""
            QComboBox {{
                background: {self.BG_CARD};
                border: 1.5px solid {self.BORDER};
                border-radius: 10px;
                padding-left: 12px;
                font-size: 13px;
                color: {self.TXT_PRIMARY};
            }}
            QComboBox:focus {{ border: 1.5px solid {self.BLEU}; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
        """)
        lay.addWidget(combo_label)
        lay.addSpacing(8)
        lay.addWidget(self.combo_visite)

        return bar

    # ─── Barre patient / KPI ──────────────────────────────────────────────

    def _build_patient_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("PatientBar")
        bar.setStyleSheet(
            f"QFrame#PatientBar {{ background: {self.BG_CARD}; border-bottom: 1px solid {self.BORDER}; border-radius: 0; }}"
        )
        self._patient_bar = bar
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 10, 20, 10)
        lay.setSpacing(16)

        # Avatar + infos patient
        avatar = QLabel()
        avatar.setPixmap(qta.icon("fa5s.user-circle", color=self.BLEU).pixmap(46, 46))
        avatar.setFixedSize(48, 48)
        lay.addWidget(avatar)

        info_box = QVBoxLayout()
        info_box.setSpacing(2)
        self.lbl_patient_nom = QLabel("—")
        self.lbl_patient_nom.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{self.TXT_PRIMARY}; border:none; background:transparent;"
        )
        info_row = QHBoxLayout()
        info_row.setSpacing(16)
        self.lbl_telephone = QLabel("—")
        self.lbl_patient_id = QLabel("—")
        self.lbl_badge_urgent = QLabel("URGENT")
        self.lbl_badge_urgent.setStyleSheet(
            f"background:{theme_manager.colors()['danger_bg']}; color:{self.ROUGE}; border-radius:8px; padding:2px 8px;"
            " font-size:10px; font-weight:bold;"
        )
        self.lbl_badge_urgent.setVisible(False)
        for lbl in (self.lbl_telephone, self.lbl_patient_id):
            lbl.setStyleSheet(
                f"font-size:11px; color:{self.TXT_SEC}; border:none; background:transparent;"
            )
        info_row.addWidget(self.lbl_telephone)
        info_row.addWidget(self.lbl_patient_id)
        info_row.addWidget(self.lbl_badge_urgent)
        info_row.addStretch()
        info_box.addWidget(self.lbl_patient_nom)
        info_box.addLayout(info_row)
        lay.addLayout(info_box)
        
        # Sélecteur patient intégré dans la barre
        combo_label = QLabel("Patient :")
        combo_label.setStyleSheet(
            f"font-size:12px; font-weight:bold; color:{self.TXT_SEC}; border:none; background:transparent;"
        )
        self.combo_visite = QComboBox()
        self.combo_visite.setFixedHeight(36)
        self.combo_visite.setMinimumWidth(300)
        self.combo_visite.setStyleSheet(f"""
            QComboBox {{
                background: {self.BG_CARD};
                border: 1.5px solid {self.BORDER};
                border-radius: 10px;
                padding-left: 12px;
                font-size: 13px;
                color: {self.TXT_PRIMARY};
            }}
            QComboBox:focus {{ border: 1.5px solid {self.BLEU}; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
        """)
        lay.addWidget(combo_label)
        lay.addSpacing(8)
        lay.addWidget(self.combo_visite)
        lay.addStretch()

        # KPI chips — backgrounds dérivés du thème
        _c = theme_manager.colors()
        self.kpi_total = self._make_kpi("Total des services", "0 GNF", self.BLEU, _c['primary_light'])
        self.kpi_paye  = self._make_kpi("Déjà payé",          "0 GNF", self.VERT, _c['success_bg'])
        self.kpi_reste = self._make_kpi("Reste à payer",      "0 GNF", self.ROUGE, _c['danger_bg'])

        for kpi in (self.kpi_total, self.kpi_paye, self.kpi_reste):
            lay.addWidget(kpi)

        return bar

    def _make_kpi(self, label: str, value: str, color: str, bg: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {bg}; border-radius: 12px; border: 1.5px solid {color}30;"
        )
        frame.setFixedHeight(60)
        frame.setMinimumWidth(160)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(16, 6, 16, 6)
        lay.setSpacing(2)

        lbl_label = QLabel(label)
        lbl_label.setStyleSheet(
            f"font-size:10px; color:{self.TXT_SEC}; border:none; background:transparent;"
        )
        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{color}; border:none; background:transparent;"
        )
        lbl_value.setObjectName("kpi_value")
        lay.addWidget(lbl_label)
        lay.addWidget(lbl_value)

        return frame

    # ─── Panneau gauche : panier ──────────────────────────────────────────

    def _build_left_panel(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet(
            f"background: {self.BG_CARD}; border-radius: 16px; border: 1px solid {self.BORDER};"
        )
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        # Section header
        sec_row = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("fa5s.shopping-cart", color=self.BLEU).pixmap(20, 20))
        sec_title = QLabel("Panier des services à facturer")
        sec_title.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{self.TXT_PRIMARY}; border:none; background:transparent;"
        )
        sec_sub = QLabel("Sélectionnez les services à inclure dans la facture")
        sec_sub.setStyleSheet(
            f"font-size:11px; color:{self.TXT_SEC}; border:none; background:transparent;"
        )
        sec_info = QVBoxLayout()
        sec_info.setSpacing(1)
        sec_info.addWidget(sec_title)
        sec_info.addWidget(sec_sub)

        self.btn_add_service = QPushButton(
            qta.icon("fa5s.plus", color=theme_manager.colors()['text_inverse']), " Ajouter un service"
        )
        self.btn_add_service.setFixedHeight(32)
        self.btn_add_service.setCursor(Qt.PointingHandCursor)
        self.btn_add_service.setEnabled(False)
        self.btn_add_service.setStyleSheet(f"""
            QPushButton {{
                background: {self.BLEU};
                color: {theme_manager.colors()['text_inverse']};
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background: {theme_manager.colors()['primary_hover']}; }}
            QPushButton:disabled {{ background: {theme_manager.colors()['border']}; }}
        """)

        sec_row.addWidget(icon_lbl)
        sec_row.addSpacing(8)
        sec_row.addLayout(sec_info, 1)
        sec_row.addWidget(self.btn_add_service)
        lay.addLayout(sec_row)

        # Sélecteur de service (pour choisir quoi ajouter)
        self.combo_service = QComboBox()
        self.combo_service.setFixedHeight(32)
        self.combo_service.setStyleSheet(f"""
            QComboBox {{
                background: {self.BG_CARD};
                border: 1.5px solid {self.BORDER};
                border-radius: 10px;
                padding-left: 12px;
                font-size: 12px;
                color: {self.TXT_PRIMARY};
            }}
            QComboBox:focus {{ border: 1.5px solid {self.BLEU}; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
        """)
        self._remplir_combo_services_visite([])

        btn_add_all = QPushButton(
            qta.icon("fa5s.layer-group", color=self.BLEU), " Ajouter tous"
        )
        btn_add_all.setFixedHeight(32)
        btn_add_all.setCursor(Qt.PointingHandCursor)
        btn_add_all.setObjectName("btn_add_all")
        btn_add_all.setStyleSheet(f"""
            QPushButton {{
                background: {self.BG_CARD};
                color: {self.BLEU};
                border: 1.5px solid {self.BLEU};
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: {theme_manager.colors()['primary_light']}; }}
        """)
        self.btn_add_all = btn_add_all

        service_row = QHBoxLayout()
        service_row.addWidget(self.combo_service, 1)
        service_row.addWidget(btn_add_all)
        lay.addLayout(service_row)

        # ── Liste des services (scrollable) ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        _bg = theme_manager.colors()['bg_card']
        self.scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {_bg}; }}"
            f"QScrollArea > QWidget {{ background: {_bg}; }}"
        )
        self.scroll.verticalScrollBar().setStyleSheet(FacturePatientStyles.scrollbar())

        self.container_lignes = QWidget()
        self.container_lignes.setStyleSheet("background: transparent;")
        self.layout_lignes = QVBoxLayout(self.container_lignes)
        self.layout_lignes.setContentsMargins(0, 0, 0, 0)
        self.layout_lignes.setSpacing(8)
        self.layout_lignes.addStretch()

        self.scroll.setWidget(self.container_lignes)
        self.scroll.setMinimumHeight(150)
        lay.addWidget(self.scroll, 1)

        # Info hint
        self._hint_frame = QFrame()
        self._hint_frame.setStyleSheet(
            f"background: {self.BG_PAGE}; border-radius: 8px; border: 1px solid {self.BORDER};"
        )
        hint_lay = QHBoxLayout(self._hint_frame)
        hint_lay.setContentsMargins(12, 6, 12, 6)
        info_ico = QLabel()
        info_ico.setPixmap(qta.icon("fa5s.info-circle", color=self.BLEU).pixmap(14, 14))
        self._hint_txt = QLabel("Décochez un service pour le retirer du panier")
        self._hint_txt.setStyleSheet(
            f"font-size:11px; color:{self.BLEU}; border:none; background:transparent;"
        )
        hint_lay.addWidget(info_ico)
        hint_lay.addSpacing(6)
        hint_lay.addWidget(self._hint_txt)
        hint_lay.addStretch()
        lay.addWidget(self._hint_frame)

        # Total + vider panier
        bottom_row = QHBoxLayout()
        self.btn_vider = QPushButton(
            qta.icon("fa5s.trash-alt", color=self.ROUGE), " Vider le panier"
        )
        self.btn_vider.setFixedHeight(32)
        self.btn_vider.setCursor(Qt.PointingHandCursor)
        self.btn_vider.setStyleSheet(f"""
            QPushButton {{
                background: {self.BG_CARD};
                color: {self.ROUGE};
                border: 1.5px solid {self.ROUGE};
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background: {theme_manager.colors()['danger_bg']}; }}
        """)
        self.lbl_total_panier = QLabel("Total à payer : 0 GNF")
        self.lbl_total_panier.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{self.BLEU}; border:none; background:transparent;"
        )
        bottom_row.addWidget(self.btn_vider)
        bottom_row.addStretch()
        bottom_row.addWidget(self.lbl_total_panier)
        lay.addLayout(bottom_row)

        return panel

    def _build_resume_section(self) -> QFrame:
        self._resume_frame = QFrame()
        frame = self._resume_frame
        frame.setStyleSheet(
            f"background: {self.BG_PAGE}; border-radius: 12px; border: 1px solid {self.BORDER};"
        )
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(0)

        # Chiffres
        vbox = QVBoxLayout()
        vbox.setSpacing(6)
        title = QLabel("Résumé de la facture")
        title.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{self.TXT_PRIMARY}; border:none; background:transparent;"
        )
        vbox.addWidget(title)

        self.lbl_nb_services = QLabel("Nombre de services : 0")
        self.lbl_nb_services.setStyleSheet(
            f"font-size:12px; color:{self.TXT_SEC}; border:none; background:transparent;"
        )
        self.lbl_total_services = QLabel("Total des services : 0 GNF")
        self.lbl_total_services.setStyleSheet(
            f"font-size:12px; color:{self.BLEU}; font-weight:bold; border:none; background:transparent;"
        )
        self.lbl_deja_paye = QLabel("Déjà payé : 0 GNF")
        self.lbl_deja_paye.setStyleSheet(
            f"font-size:12px; color:{self.VERT}; border:none; background:transparent;"
        )
        self.lbl_reste_a_payer = QLabel("Reste à payer : 0 GNF")
        self.lbl_reste_a_payer.setStyleSheet(
            f"font-size:13px; color:{self.ROUGE}; font-weight:bold; border:none; background:transparent;"
        )
        for w in (self.lbl_nb_services, self.lbl_total_services,
                  self.lbl_deja_paye, self.lbl_reste_a_payer):
            vbox.addWidget(w)

        lay.addLayout(vbox, 1)

        # Icône illustrative
        ico_lbl = QLabel()
        ico_lbl.setPixmap(qta.icon("fa5s.receipt", color=self.TXT_SEC).pixmap(48, 48))
        ico_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(ico_lbl)

        return frame

    # ─── Panneau droit : paiement ──────────────────────────────────────────

    def _build_right_panel(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet(
            f"background: {self.BG_CARD}; border-radius: 16px; border: 1px solid {self.BORDER};"
        )
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        # Mode de paiement
        mode_title = QLabel("Mode de paiement")
        mode_title.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{self.TXT_PRIMARY}; border:none; background:transparent;"
        )
        mode_sub = QLabel("Choisissez le mode de paiement")
        mode_sub.setStyleSheet(
            f"font-size:11px; color:{self.TXT_SEC}; border:none; background:transparent;"
        )
        lay.addWidget(mode_title)
        lay.addWidget(mode_sub)

        # Boutons mode paiement
        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)

        self._mode_group = QButtonGroup(self)
        # (label, icon_name_or_None, logo_text, logo_bg, logo_fg)
        modes = [
            ("Espèces",      "fa5s.money-bill-wave", None,  None,       None),
            ("Mobile Money", None,                   "mtn", "#FFCC00",  "#1C1C1C"),
            ("Orange Money", None,                   "OM",  "#FF6600",  "#FFFFFF"),
        ]
        self._mode_buttons: List[QPushButton] = []
        for idx, (label, icon_name, logo_text, logo_bg, logo_fg) in enumerate(modes):
            if logo_text:
                icon_obj = self._logo_pixmap_icon(logo_text, logo_bg, logo_fg)
                btn = QPushButton(icon_obj, f"  {label}")
            else:
                btn = QPushButton(
                    qta.icon(icon_name, color=self.BLEU if idx == 0 else self.TXT_SEC),
                    f"  {label}"
                )
            btn.setIconSize(QSize(28, 16))
            btn.setFixedHeight(40)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setChecked(idx == 0)
            btn.setProperty("mode_label", label)
            self._update_mode_btn_style(btn, idx == 0)
            self._mode_group.addButton(btn, idx)
            self._mode_buttons.append(btn)
            mode_row.addWidget(btn)

        self._mode_group.idClicked.connect(self._on_mode_change)
        lay.addLayout(mode_row)
        lay.addSpacing(6)

        # Téléphone
        self.lbl_telephone_paiement = self._field_label("Téléphone")
        self.input_telephone_paiement = QLineEdit()
        self.input_telephone_paiement.setPlaceholderText("Ex: 628123456")
        self.input_telephone_paiement.setFixedHeight(32)
        self.input_telephone_paiement.setStyleSheet(self._input_style())
        self.input_telephone_paiement.setEnabled(True)
        
        phone_lay = QVBoxLayout()
        phone_lay.setSpacing(4)
        phone_lay.addWidget(self.lbl_telephone_paiement)
        phone_lay.addWidget(self.input_telephone_paiement)
        lay.addLayout(phone_lay)
        lay.addSpacing(6)

        # Montant à payer | Montant payé | Monnaie à rendre — sur la même ligne
        amounts_row = QHBoxLayout()
        amounts_row.setSpacing(6)

        def _amount_col(label_text: str, readonly: bool = False):
            col = QVBoxLayout()
            col.setSpacing(4)
            col.addWidget(self._field_label(label_text))
            inp = QLineEdit("0")
            inp.setReadOnly(readonly)
            inp.setFixedHeight(32)
            inp.setStyleSheet(self._input_style(readonly=readonly))
            col.addWidget(inp)
            return col, inp

        col_total, self.input_montant_total = _amount_col("À payer (GNF)", readonly=True)
        col_paye,  self.input_montant_paye  = _amount_col("Payé (GNF)",    readonly=False)
        col_rendu, self.input_monnaie       = _amount_col("Monnaie (GNF)", readonly=True)

        self.input_montant_paye.textChanged.connect(self._on_montant_paye_change)

        amounts_row.addLayout(col_total, 1)
        amounts_row.addLayout(col_paye,  1)
        amounts_row.addLayout(col_rendu, 1)
        lay.addLayout(amounts_row)

        # Séparateur
        self._sep_paiement = QFrame()
        self._sep_paiement.setFixedHeight(1)
        self._sep_paiement.setStyleSheet(f"background: {self.BORDER}; border: none;")
        lay.addWidget(self._sep_paiement)

        # (Paiement partiel et option dette retirés)

        lay.addStretch()

        # Footer buttons
        footer = QHBoxLayout()
        footer.setSpacing(8)

        self.btn_annuler = QPushButton("✕  Annuler")
        self.btn_annuler.setFixedHeight(34)
        self.btn_annuler.setCursor(Qt.PointingHandCursor)
        self.btn_annuler.setStyleSheet(f"""
            QPushButton {{
                background: {self.BG_CARD};
                color: {self.TXT_SEC};
                border: 1.5px solid {self.BORDER};
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: {self.BG_PAGE}; }}
        """)

        self.btn_payer = QPushButton("✓  Encaisser le paiement")
        self.btn_payer.setFixedHeight(34)
        self.btn_payer.setCursor(Qt.PointingHandCursor)
        self.btn_payer.setStyleSheet(f"""
            QPushButton {{
                background: {self.VERT};
                color: {theme_manager.colors()['text_inverse']};
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background: {theme_manager.colors()['primary_hover']}; }}
        """)

        footer.addWidget(self.btn_annuler)
        footer.addWidget(self.btn_payer, 1)
        lay.addLayout(footer)

        return panel

    # ─── Helpers UI ───────────────────────────────────────────────────────

    @staticmethod
    def _logo_pixmap_icon(text: str, bg: str, fg: str, w: int = 36, h: int = 22):
        """Crée une icône QPainter simulant un logo (MTN, Orange Money)."""
        from PySide6.QtGui import QIcon
        pm = QPixmap(w, h)
        pm.fill(Qt.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(bg))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 5, 5)
        painter.setPen(QColor(fg))
        font = QFont("Arial", max(int(h * 0.42), 7), QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 0, w, h, Qt.AlignCenter, text)
        painter.end()
        return QIcon(pm)

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size:12px; font-weight:bold; color:{self.TXT_PRIMARY}; border:none; background:transparent;"
        )
        return lbl

    def _input_style(self, readonly: bool = False) -> str:
        bg = self.BG_PAGE if readonly else self.BG_CARD
        return f"""
            QLineEdit {{
                background: {bg};
                border: 1.5px solid {self.BORDER};
                border-radius: 8px;
                padding-left: 12px;
                font-size: 13px;
                color: {self.TXT_PRIMARY};
            }}
            QLineEdit:focus {{ border: 1.5px solid {self.BLEU}; }}
            QDateEdit {{
                background: {self.BG_CARD};
                border: 1.5px solid {self.BORDER};
                border-radius: 8px;
                padding-left: 12px;
                font-size: 13px;
                color: {self.TXT_PRIMARY};
            }}
        """

    def _partial_row(self, label_text: str, value_text: str, color: str) -> QFrame:
        row = QFrame()
        row.setStyleSheet("background: transparent; border: none;")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            f"font-size:11px; color:{self.TXT_SEC}; border:none; background:transparent;"
        )
        val = QLabel(value_text)
        val.setStyleSheet(
            f"font-size:11px; font-weight:bold; color:{color}; border:none; background:transparent;"
        )
        val.setObjectName("partial_value")
        lay.addWidget(lbl)
        lay.addStretch()
        lay.addWidget(val)
        return row

    def _update_mode_btn_style(self, btn: QPushButton, selected: bool) -> None:
        if selected:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {theme_manager.colors()['primary_light']};
                    color: {self.BLEU};
                    border: 2px solid {self.BLEU};
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 4px 8px;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {self.BG_CARD};
                    color: {self.TXT_SEC};
                    border: 1.5px solid {self.BORDER};
                    border-radius: 10px;
                    font-size: 11px;
                    padding: 4px 8px;
                }}
                QPushButton:hover {{ background: {self.BG_PAGE}; }}
            """)

    # ─── Ligne de service dans le panier ──────────────────────────────────

    def _build_service_row(self, index: int, data: Dict[str, Any]) -> QFrame:
        """Construit une ligne de service avec case à cocher."""
        designation = data.get("designation", "")
        description = data.get("description", "")
        prix = float(data.get("prix", 0.0))
        quantite = int(data.get("quantite", 1))
        date_str = data.get("date", "—")
        code_paniere = data.get("code_paniere", "")

        row = QFrame()
        row.setFixedHeight(64)
        row.setStyleSheet(f"""
            QFrame {{
                background: {self.BG_CARD};
                border-radius: 10px;
                border: 1px solid {self.BORDER};
            }}
            QFrame:hover {{ border: 1px solid {self.BLEU}30; }}
            QLabel {{ border: none; background: transparent; }}
        """)

        # Stocker les données
        row.code_paniere = code_paniere
        row.designation = designation
        row.description = description
        row.quantite = quantite
        row.prix = prix

        lay = QHBoxLayout(row)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(12)

        # Checkbox
        chk = QCheckBox()
        chk.setChecked(True)
        chk.setFixedSize(18, 18)
        chk.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 16px; height: 16px;
                border-radius: 4px;
                border: 2px solid {self.BORDER};
                background: {self.BG_CARD};
            }}
            QCheckBox::indicator:checked {{
                background: {self.BLEU};
                border: 2px solid {self.BLEU};
            }}
        """)
        row.chk = chk

        # Icône service
        ico_lbl = QLabel()
        ico_lbl.setPixmap(self._icone_service(designation).pixmap(28, 28))
        ico_lbl.setFixedSize(32, 32)

        # Nom + description
        name_box = QVBoxLayout()
        name_box.setSpacing(1)
        lbl_name = QLabel(designation or "Service")
        lbl_name.setStyleSheet(
            f"font-size:12px; font-weight:bold; color:{self.TXT_PRIMARY};"
        )
        lbl_desc = QLabel(description or "—")
        lbl_desc.setStyleSheet(f"font-size:10px; color:{self.TXT_SEC};")
        name_box.addWidget(lbl_name)
        name_box.addWidget(lbl_desc)
        row.lbl_name = lbl_name
        row.lbl_desc = lbl_desc

        # Date
        lbl_date = QLabel(date_str)
        lbl_date.setStyleSheet(f"font-size:10px; color:{self.TXT_SEC};")
        lbl_date.setFixedWidth(80)
        lbl_date.setAlignment(Qt.AlignCenter)

        # Prix
        total = prix * quantite
        lbl_prix = QLabel(f"{total:,.0f} GNF".replace(",", " "))
        lbl_prix.setStyleSheet(
            f"font-size:12px; font-weight:bold; color:{self.TXT_PRIMARY};"
        )
        lbl_prix.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_prix.setFixedWidth(100)
        row.lbl_prix = lbl_prix

        # Supprimer
        btn_del = QPushButton()
        btn_del.setIcon(qta.icon("fa5s.trash-alt", color=self.ROUGE))
        btn_del.setFixedSize(30, 30)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background: {theme_manager.colors()['danger_bg']};
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{ background: {theme_manager.colors()['danger']}20; }}
        """)
        btn_del.clicked.connect(lambda: self._supprimer_ligne(row))

        # Connecter checkbox
        chk.toggled.connect(lambda checked, r=row: self._on_service_toggled(r, checked))

        lay.addWidget(chk)
        lay.addWidget(ico_lbl)
        lay.addLayout(name_box, 1)
        lay.addWidget(lbl_date)
        lay.addWidget(lbl_prix)
        lay.addWidget(btn_del)

        return row

    # =========================================================================
    # SIGNALS
    # =========================================================================

    def _connecter_signaux(self) -> None:
        self.combo_visite.currentIndexChanged.connect(self._on_visite_change)
        self.btn_add_service.clicked.connect(self._ajouter_service)
        self.btn_add_all.clicked.connect(self._ajouter_tous_services)
        self.btn_annuler.clicked.connect(self._annuler_facture)
        self.btn_payer.clicked.connect(self._payer_facture)
        self.btn_vider.clicked.connect(self._vider_panier)
        self.combo_service.currentIndexChanged.connect(self._toggle_add_button)

    # =========================================================================
    # CHARGEMENT DONNÉES
    # =========================================================================

    def charger_donnees(self, code_session: str) -> None:
        self.code_session = code_session
        self.data_loader.charger_patients_en_attente(
            self.facture_ctrl, self.combo_visite, code_session
        )

    def _on_visite_change(self, index: int) -> None:
        patient = self.combo_visite.currentData()
        if not patient:
            self._reset_view()
            return

        self.code_visite = patient.get("code_visite")
        ok, msg, code_facture = self.operations.generer_facture(
            self.code_visite, patient.get("telephone", ""), creer_panier=False
        )
        if not ok:
            CustomMessageBox.error(self, "Erreur", msg)
            self._reset_view()
            return

        self.code_facture = code_facture
        self._charger_date_facture()
        self._patient_data = patient
        self._remplir_patient(patient)
        self._charger_services_visite()
        self._reinitialiser_lignes()
        self._recalculer_total()

    # =========================================================================
    # ACTIONS LIGNES
    # =========================================================================

    def _ajouter_service(self) -> None:
        if not self.code_facture:
            return
        data = self.combo_service.currentData()
        if not data:
            return
        ok, msg, code_panier = self.operations.ajouter_ligne(self.code_facture, data)
        if ok:
            data["code_paniere"] = code_panier
            self._ajouter_ligne_visuelle(data)
            current_index = self.combo_service.currentIndex()
            if current_index > 0:
                self.combo_service.removeItem(current_index)
            self._toggle_add_button()
            self._recalculer_total()

    def _ajouter_tous_services(self) -> None:
        if not self.code_facture:
            return
        if self.combo_service.count() <= 1:
            return

        while self.combo_service.count() > 1:
            self.combo_service.setCurrentIndex(1)
            data = self.combo_service.currentData()
            if not data:
                break
            ok, msg, code_panier = self.operations.ajouter_ligne(self.code_facture, data)
            if ok:
                data["code_paniere"] = code_panier
                self._ajouter_ligne_visuelle(data)
            self.combo_service.removeItem(1)

        self._toggle_add_button()
        self._recalculer_total()

    def _ajouter_ligne_visuelle(self, data: Dict[str, Any]) -> None:
        index = len(self.lignes_panier) + 1
        ligne = self._build_service_row(index, data)
        self.lignes_panier.append(ligne)
        count = self.layout_lignes.count()
        self.layout_lignes.insertWidget(count - 1, ligne)

    def _supprimer_ligne(self, ligne_widget) -> None:
        if not hasattr(ligne_widget, "code_paniere"):
            return
        ok, msg = self.operations.supprimer_ligne(ligne_widget.code_paniere, self)
        if ok:
            self._restituer_service_au_combo(ligne_widget)
            self.lignes_panier.remove(ligne_widget)
            ligne_widget.deleteLater()
            self._recalculer_total()
            if self.facture_ctrl and self.code_facture:
                self.facture_ctrl.recalculer_montant_facture(self.code_facture)
        else:
            if msg != "Suppression annulee":
                CustomMessageBox.error(self, "Erreur", msg)

    def _on_service_toggled(self, row, checked: bool) -> None:
        """Cocheé/décoché un service — l'inclure ou l'exclure du panier."""
        if not checked:
            self._supprimer_ligne(row)

    def _vider_panier(self) -> None:
        if not self.lignes_panier:
            return
        for ligne in list(self.lignes_panier):
            self.operations.supprimer_ligne(ligne.code_paniere, self)
            ligne.deleteLater()
        self.lignes_panier.clear()
        self._recalculer_total()

    # =========================================================================
    # FACTURE
    # =========================================================================

    def _payer_facture(self) -> None:
        if not self.code_facture:
            return
            
        checked_id = self._mode_group.checkedId()
        mode_label = self._mode_group.button(checked_id).property("mode_label") if checked_id >= 0 else "Espèces"
        telephone = self.input_telephone_paiement.text().strip() if hasattr(self, 'input_telephone_paiement') else ""

        ok, msg = self.operations.encaisser_facture_direct(
            self.code_facture, mode_label, telephone
        )
        if ok:
            CustomMessageBox.success(self, "Succes", "Paiement enregistré avec succès.")
            
            # Demander l'impression
            if CustomMessageBox.confirm(self, "Impression", "Voulez-vous imprimer la facture ?"):
                import os
                import tempfile
                from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
                
                info_cabinet = self.facture_ctrl.get_cabinet_info() if self.facture_ctrl else {}
                fd, path = tempfile.mkstemp(suffix=".pdf", prefix=f"facture_{self.code_facture}_")
                os.close(fd)
                
                pdf_ok, pdf_msg = self.facture_ctrl.generer_facture_pdf(self.code_facture, path)
                if pdf_ok and os.path.exists(path):
                    ApercuPDFDialog(path, f"Aperçu - Facture {self.code_facture}", self).exec()
                else:
                    CustomMessageBox.error(self, "Erreur PDF", f"Erreur de génération du PDF :\n{pdf_msg}")
            
            self._reset_view()
            if self.code_session:
                self.charger_donnees(self.code_session)
            self.paiement_effectue.emit()
            self.facture_mise_a_jour.emit()
        else:
            CustomMessageBox.error(self, "Erreur", msg)

    def _annuler_facture(self) -> None:
        if not self.code_facture:
            return
        ok, msg = self.operations.annuler_facture(self.code_facture, self)
        if ok:
            CustomMessageBox.success(self, "Succes", msg)
            self._reset_view()
            if self.code_session:
                self.charger_donnees(self.code_session)
            self.facture_mise_a_jour.emit()
        else:
            if msg != "Annulation annulee":
                CustomMessageBox.error(self, "Erreur", msg)


    # =========================================================================
    # ÉVÉNEMENTS UI
    # =========================================================================

    def _on_mode_change(self, idx: int) -> None:
        for i, btn in enumerate(self._mode_buttons):
            self._update_mode_btn_style(btn, i == idx)
            btn.setIcon(
                qta.icon(
                    ["fa5s.money-bill-wave", "fa5s.mobile-alt", "fa5s.exchange-alt"][i],
                    color=self.BLEU if i == idx else self.TXT_SEC
                )
            )

    def _on_montant_paye_change(self, text: str) -> None:
        try:
            paye = float(text.replace(" ", "").replace(",", "") or 0)
        except ValueError:
            paye = 0.0
        try:
            total = float(self.input_montant_total.text().replace(" ", "").replace(",", "") or 0)
        except ValueError:
            total = 0.0

        monnaie = max(0.0, paye - total)
        reste = max(0.0, total - paye)

        self.input_monnaie.setText(f"{monnaie:,.0f}".replace(",", " "))


    # =========================================================================
    # UI HELPERS
    # =========================================================================

    def _remplir_patient(self, data: Dict[str, Any]) -> None:
        nom = data.get("nom", "")
        prenom = data.get("prenom", "")
        self.lbl_patient_nom.setText(f"{prenom} {nom}".strip() or "—")
        self.lbl_patient_id.setText(f"ID Patient: {data.get('code_patient', '—')}")
        tel = data.get("telephone", "—") or "—"
        self.lbl_telephone.setText(tel)
        urgent = bool(data.get("urgent"))
        self.lbl_badge_urgent.setVisible(urgent)
        if hasattr(self, 'input_telephone_paiement'):
            self.input_telephone_paiement.setText(data.get("telephone", "") or "")

    def _charger_date_facture(self) -> None:
        self._date_facture_str = "—"
        try:
            if self.facture_ctrl and self.code_facture:
                facture = self.facture_ctrl.obtenir_par_code(self.code_facture)
                if facture and facture.get_date_facture():
                    dt = facture.get_date_facture()
                    self._date_facture_str = (
                        dt.strftime("%d/%m/%Y") if hasattr(dt, "strftime") else str(dt)
                    )
        except Exception:
            self._date_facture_str = "—"

    def _reinitialiser_lignes(self) -> None:
        for ligne in self.lignes_panier:
            ligne.deleteLater()
        self.lignes_panier.clear()

    def _reset_view(self) -> None:
        self.code_visite = None
        self.code_facture = None
        self._patient_data = {}
        self._date_facture_str = "—"
        self._reinitialiser_lignes()
        self._recalculer_total()
        self.lbl_patient_nom.setText("—")
        self.lbl_patient_id.setText("—")
        self.lbl_telephone.setText("—")
        self.lbl_badge_urgent.setVisible(False)
        self.combo_visite.blockSignals(True)
        self.combo_visite.setCurrentIndex(0)
        self.combo_visite.blockSignals(False)
        self.input_montant_paye.setText("0")
        if hasattr(self, 'input_telephone_paiement'):
            self.input_telephone_paiement.clear()

    def _remplir_combo_services_visite(self, services: List[Dict[str, Any]]) -> None:
        self.combo_service.clear()
        self.combo_service.addItem(
            qta.icon("fa5s.list", color=self.BLEU),
            "  Sélectionner un service...",
            None
        )
        for s in services:
            designation = s.get("designation", "")
            ref = s.get("numero_reference", "")
            prix = float(s.get("prix_applique", 0) or 0)
            label = f"  {designation}  •  {prix:,.0f} GNF".replace(",", " ")
            icon = self._icone_service(designation)
            data = {
                "designation": designation,
                "description": ref,
                "quantite": int(s.get("quantite_facture", 1) or 1),
                "prix": prix,
            }
            self.combo_service.addItem(icon, label, data)

    def _restituer_service_au_combo(self, ligne_widget) -> None:
        designation = getattr(ligne_widget, "designation", "")
        description = getattr(ligne_widget, "description", "")
        quantite = int(getattr(ligne_widget, "quantite", 1) or 1)
        prix = float(getattr(ligne_widget, "prix", 0.0) or 0.0)
        label = f"  {designation}  •  {prix:,.0f} GNF".replace(",", " ")
        icon = self._icone_service(designation)
        data = {
            "designation": designation,
            "description": description,
            "quantite": quantite,
            "prix": prix,
        }
        self.combo_service.addItem(icon, label, data)
        self._toggle_add_button()

    def _icone_service(self, designation: str):
        _c = theme_manager.colors()
        d = (designation or "").lower()
        if "consult" in d:
            return qta.icon("fa5s.stethoscope", color=_c['primary'])
        if "examen" in d or "exam" in d:
            return qta.icon("fa5s.microscope",  color=_c['info'])
        if "chirurg" in d:
            return qta.icon("fa5s.procedures",  color=_c['warning'])
        if "lunette" in d:
            return qta.icon("fa5s.glasses",     color=_c['success'])
        if "pharma" in d or "medic" in d:
            return qta.icon("fa5s.pills",       color=_c['accent'])
        return qta.icon("fa5s.file-medical",    color=_c['primary'])

    def _charger_services_visite(self) -> None:
        services = []
        if self.facture_ctrl and self.code_visite:
            try:
                services = self.facture_ctrl.lister_services_visite(self.code_visite) or []
            except Exception:
                services = []
        self._remplir_combo_services_visite(services)
        self._toggle_add_button()

    def _toggle_add_button(self) -> None:
        data = self.combo_service.currentData()
        can_add = bool(data) and bool(self.code_facture)
        self.btn_add_service.setEnabled(can_add)
        self.btn_add_all.setEnabled(self.combo_service.count() > 1 and bool(self.code_facture))

    def _recalculer_total(self) -> None:
        total = 0.0
        for ligne in self.lignes_panier:
            total += float(getattr(ligne, "quantite", 0)) * float(getattr(ligne, "prix", 0.0))

        total_str = f"{total:,.0f} GNF".replace(",", " ")
        self.lbl_total_panier.setText(f"Total à payer : {total_str}")
        self.input_montant_total.setText(f"{total:,.0f}".replace(",", " "))

        # KPI
        for kpi in (self.kpi_total, self.kpi_reste):
            val_lbl = kpi.findChild(QLabel, "kpi_value")
            if val_lbl:
                val_lbl.setText(total_str)
        paye_kpi = self.kpi_paye.findChild(QLabel, "kpi_value")
        if paye_kpi:
            paye_kpi.setText("0 GNF")


    # =========================================================================
    # THÈME
    # =========================================================================

    def apply_theme(self) -> None:
        c = theme_manager.colors()
        
        # CORRECTIF : Forcer le thème sur tous les widgets pour éliminer le noir
        from views.shared.theme_fix import fix_black_widgets
        fix_black_widgets(self)

        # ── Cascade globale sur le widget racine ────────────────────────────
        self.setStyleSheet(f"""
            FacturePatientWidget {{
                background-color: {c['bg_main']};
                border-radius: 0px; border: none;
            }}
            QLabel {{
                background: transparent;
                color: {c['text_primary']};
                border: none;
            }}
            QScrollArea {{
                border: none;
                background: {c['bg_card']};
            }}
            QScrollArea > QWidget {{
                background: {c['bg_card']};
            }}
            QScrollBar:vertical {{
                border: none; background: {c['bg_main']};
                width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']}; min-height: 20px; border-radius: 3px;
            }}
        """)

        # ── Scroll area + conteneur lignes ─────────────────────────────────
        from PySide6.QtWidgets import QScrollArea as _QSA
        if hasattr(self, 'scroll') and isinstance(self.scroll, _QSA):
            self.scroll.setStyleSheet(
                f"QScrollArea {{ border: none; background: {c['bg_card']}; }}"
                f"QScrollArea > QWidget {{ background: {c['bg_card']}; }}"
            )
        if hasattr(self, 'container_lignes'):
            self.container_lignes.setStyleSheet(f"background: {c['bg_card']};")

        # ── Panels principaux ───────────────────────────────────────────────
        _panel = f"background: {c['bg_card']}; border-radius: 16px; border: 1px solid {c['border']};"
        if hasattr(self, '_left_panel'):   self._left_panel.setStyleSheet(_panel)
        if hasattr(self, '_right_panel'):  self._right_panel.setStyleSheet(_panel)

        # ── Barre patient ───────────────────────────────────────────────────
        if hasattr(self, '_patient_bar'):
            self._patient_bar.setStyleSheet(
                f"QFrame#PatientBar {{ background: {c['bg_card']}; border-bottom: 1px solid {c['border']}; border-radius: 0; }}"
            )
        if hasattr(self, 'lbl_patient_nom'):
            self.lbl_patient_nom.setStyleSheet(
                f"font-size:15px; font-weight:bold; color:{c['text_primary']}; border:none; background:transparent;")
        if hasattr(self, 'lbl_badge_urgent'):
            self.lbl_badge_urgent.setStyleSheet(
                f"background:{c['danger_bg']}; color:{c['danger']}; border-radius:8px; padding:2px 8px; font-size:10px; font-weight:bold;")
        for attr in ('lbl_telephone', 'lbl_patient_id'):
            lbl = getattr(self, attr, None)
            if lbl:
                lbl.setStyleSheet(f"font-size:11px; color:{c['text_secondary']}; border:none; background:transparent;")

        # ── KPI chips ───────────────────────────────────────────────────────
        if hasattr(self, 'kpi_total'):
            self.kpi_total.setStyleSheet(f"background:{c['primary_light']}; border-radius:12px; border:1.5px solid {c['primary']}30;")
        if hasattr(self, 'kpi_paye'):
            self.kpi_paye.setStyleSheet(f"background:{c['success_bg']}; border-radius:12px; border:1.5px solid {c['success']}30;")
        if hasattr(self, 'kpi_reste'):
            self.kpi_reste.setStyleSheet(f"background:{c['danger_bg']}; border-radius:12px; border:1.5px solid {c['danger']}30;")

        # ── Combo patient ────────────────────────────────────────────────────
        _combo = f"""
            QComboBox {{
                background: {c['bg_card']}; color: {c['text_primary']};
                border: 1.5px solid {c['border']}; border-radius: 10px; padding-left: 12px; font-size: 13px;
            }}
            QComboBox:focus {{ border: 1.5px solid {c['border_focus']}; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
        """
        if hasattr(self, 'combo_visite'):  self.combo_visite.setStyleSheet(_combo)

        # ── Panneau gauche ───────────────────────────────────────────────────
        _combo_sm = f"""
            QComboBox {{
                background: {c['bg_card']}; color: {c['text_primary']};
                border: 1.5px solid {c['border']}; border-radius: 10px; padding-left: 12px; font-size: 12px;
            }}
            QComboBox:focus {{ border: 1.5px solid {c['primary']}; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
        """
        if hasattr(self, 'combo_service'):  self.combo_service.setStyleSheet(_combo_sm)

        if hasattr(self, 'btn_add_service'):
            self.btn_add_service.setStyleSheet(f"""
                QPushButton {{
                    background: {c['primary']}; color: {c['text_inverse']};
                    border-radius: 10px; font-weight: bold; font-size: 12px; padding: 0 16px;
                }}
                QPushButton:hover {{ background: {c['primary_hover']}; }}
                QPushButton:disabled {{ background: {c['border']}; color: {c['text_muted']}; }}
            """)
        if hasattr(self, 'btn_add_all'):
            self.btn_add_all.setStyleSheet(f"""
                QPushButton {{
                    background: {c['bg_card']}; color: {c['primary']};
                    border: 1.5px solid {c['primary']}; border-radius: 10px;
                    font-weight: bold; font-size: 12px; padding: 0 14px;
                }}
                QPushButton:hover {{ background: {c['primary_light']}; }}
            """)
        if hasattr(self, 'btn_vider'):
            self.btn_vider.setStyleSheet(f"""
                QPushButton {{
                    background: {c['bg_card']}; color: {c['danger']};
                    border: 1.5px solid {c['danger']}; border-radius: 10px;
                    font-weight: bold; font-size: 12px; padding: 0 16px;
                }}
                QPushButton:hover {{ background: {c['danger_bg']}; }}
            """)

        # ── Labels totaux ────────────────────────────────────────────────────
        if hasattr(self, 'lbl_total_panier'):
            self.lbl_total_panier.setStyleSheet(
                f"font-size:15px; font-weight:bold; color:{c['primary']}; border:none; background:transparent;")
        if hasattr(self, 'lbl_nb_services'):
            self.lbl_nb_services.setStyleSheet(
                f"font-size:12px; color:{c['text_secondary']}; border:none; background:transparent;")
        if hasattr(self, 'lbl_total_services'):
            self.lbl_total_services.setStyleSheet(
                f"font-size:12px; color:{c['primary']}; font-weight:bold; border:none; background:transparent;")
        if hasattr(self, 'lbl_deja_paye'):
            self.lbl_deja_paye.setStyleSheet(
                f"font-size:12px; color:{c['success']}; border:none; background:transparent;")
        if hasattr(self, 'lbl_reste_a_payer'):
            self.lbl_reste_a_payer.setStyleSheet(
                f"font-size:13px; color:{c['danger']}; font-weight:bold; border:none; background:transparent;")

        # ── Panneau droit ────────────────────────────────────────────────────
        _input_edit = f"""
            QLineEdit {{
                background: {c['bg_card']}; color: {c['text_primary']};
                border: 1.5px solid {c['border']}; border-radius: 8px; padding-left: 12px; font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1.5px solid {c['border_focus']}; }}
        """
        _input_ro = f"""
            QLineEdit {{
                background: {c['bg_input']}; color: {c['text_primary']};
                border: 1.5px solid {c['border']}; border-radius: 8px; padding-left: 12px; font-size: 13px;
            }}
        """
        for attr in ('input_montant_paye', 'input_telephone_paiement'):
            w = getattr(self, attr, None)
            if w: w.setStyleSheet(_input_edit)
        for attr in ('input_montant_total', 'input_monnaie'):
            w = getattr(self, attr, None)
            if w: w.setStyleSheet(_input_ro)
        if hasattr(self, 'btn_annuler'):
            self.btn_annuler.setStyleSheet(f"""
                QPushButton {{
                    background: {c['bg_card']}; color: {c['text_secondary']};
                    border: 1.5px solid {c['border']}; border-radius: 10px;
                    font-weight: bold; font-size: 12px; padding: 0 14px;
                }}
                QPushButton:hover {{ background: {c['hover']}; }}
            """)

        if hasattr(self, 'btn_payer'):
            self.btn_payer.setStyleSheet(f"""
                QPushButton {{
                    background: {c['success']}; color: {c['text_inverse']};
                    border: none; border-radius: 10px;
                    font-weight: bold; font-size: 12px; padding: 0 16px;
                }}
                QPushButton:hover {{ background: {c['primary']}; }}
            """)

        # ── Résumé section frame ─────────────────────────────────────────────
        if hasattr(self, '_resume_frame'):
            self._resume_frame.setStyleSheet(
                f"background: {c['bg_card']}; border-radius: 12px; border: 1px solid {c['border']};")

        # ── Hint + séparateur ───────────────────────────────────────────────
        if hasattr(self, '_hint_frame'):
            self._hint_frame.setStyleSheet(
                f"background: {c['bg_card']}; border-radius: 8px; border: 1px solid {c['border']};")
        if hasattr(self, '_hint_txt'):
            self._hint_txt.setStyleSheet(
                f"font-size:11px; color:{c['primary']}; border:none; background:transparent;")
        if hasattr(self, '_sep_paiement'):
            self._sep_paiement.setStyleSheet(f"background: {c['border']}; border: none;")


        # ── Boutons mode paiement ────────────────────────────────────────────
        if hasattr(self, '_mode_buttons') and hasattr(self, '_mode_group'):
            checked_id = self._mode_group.checkedId()
            for idx, btn in enumerate(self._mode_buttons):
                self._update_mode_btn_style(btn, idx == checked_id)

        # ── Lignes du panier (rows dynamiques) ──────────────────────────────
        if hasattr(self, 'layout_lignes'):
            for i in range(self.layout_lignes.count()):
                item = self.layout_lignes.itemAt(i)
                if item and item.widget():
                    row = item.widget()
                    row.setStyleSheet(f"""
                        QFrame {{
                            background: {c['bg_card']};
                            border-radius: 10px;
                            border: 1px solid {c['border']};
                        }}
                        QFrame:hover {{ border: 1px solid {c['primary']}30; }}
                        QLabel {{ border: none; background: transparent; color: {c['text_primary']}; }}
                    """)

    # =========================================================================
    # API PUBLIQUE
    # =========================================================================

    def selectionner_visite(self, code_visite: str) -> None:
        if not code_visite:
            return
        for i in range(self.combo_visite.count()):
            data = self.combo_visite.itemData(i)
            if isinstance(data, dict) and data.get("code_visite") == code_visite:
                self.combo_visite.setCurrentIndex(i)
                return
