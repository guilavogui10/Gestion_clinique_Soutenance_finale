"""
Dialogue moderne pour validation du paiement patient.
Affiche entete facture, infos patient, services et total.
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QComboBox, QLineEdit, QScrollArea, QWidget, QSizePolicy, QFileDialog, QLayout
)

from ..styles.facture_patient_styles import FacturePatientStyles
from views.shared.modal_theme import MC
from views.shared.theme_manager import theme_manager


class FacturePatientInvoiceDialog(QDialog):
    """Dialogue professionnel pour valider le paiement d'une facture patient."""

    def __init__(
        self,
        parent=None,
        facture=None,
        patient_info: Optional[Dict[str, Any]] = None,
        lignes: Optional[List[Any]] = None,
        total: float = 0.0,
        cabinet_info: Optional[Dict[str, Any]] = None,
        pdf_exporter: Optional[Callable[[str], Tuple[bool, str]]] = None,
    ):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.facture = facture
        self.patient_info = patient_info or {}
        self.lignes = lignes or []
        self.total = total
        self.cabinet_info = cabinet_info or {}
        self.pdf_exporter = pdf_exporter
        self.mode_paiement = None
        self.telephone = ""
        self._init_ui()

    def _init_ui(self) -> None:
        self.setMinimumWidth(900)
        parent = self.parentWidget()
        target_height = int(parent.height() * 0.92) if (parent and parent.height() > 0) else 600
        self.setFixedHeight(target_height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {MC.BG_CARD};
                border: 2px solid {FacturePatientStyles.BLEU_PRINCIPAL};
                border-radius: 16px;
            }}
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(22, 20, 22, 20)
        frame_layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        logo_path = self.cabinet_info.get("logo_url")
        if logo_path:
            logo = QLabel()
            pix = QPixmap(logo_path)
            if not pix.isNull():
                logo.setPixmap(pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                logo.setFixedSize(30, 30)
                header.addWidget(logo)
        icon = QLabel()
        icon.setPixmap(
            qta.icon("fa5s.file-invoice-dollar",
                     color=FacturePatientStyles.BLEU_PRINCIPAL).pixmap(28, 28)
        )
        title = QLabel("Validation du paiement")
        title.setStyleSheet(
            f"font-size:16px; font-weight:bold; color:{FacturePatientStyles.BLEU_PRINCIPAL};"
        )
        header.addWidget(icon)
        header.addSpacing(6)
        header.addWidget(title)
        header.addStretch()
        frame_layout.addLayout(header)

        frame_layout.addWidget(self._build_entete_facture())
        frame_layout.addWidget(self._divider())

        row_infos = QHBoxLayout()
        row_infos.addWidget(self._build_patient_card(), 2)
        row_infos.addWidget(self._build_total_card(), 1)
        frame_layout.addLayout(row_infos)
        frame_layout.addWidget(self._divider())

        frame_layout.addWidget(self._build_services_list())
        frame_layout.addWidget(self._divider())

        frame_layout.addWidget(self._build_paiement_section())
        frame_layout.addWidget(self._divider())

        frame_layout.addLayout(self._build_buttons())
        layout.addWidget(frame)

    def _build_entete_facture(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet("QFrame { background: transparent; border: none; }")
        lay = QHBoxLayout(card)
        lay.setContentsMargins(12, 8, 12, 8)

        code = getattr(self.facture, "get_code_facture", lambda: "")()
        date_val = getattr(self.facture, "get_date_facture", lambda: None)()
        date_str = date_val.strftime("%d/%m/%Y") if hasattr(date_val, "strftime") else str(date_val or "—")
        statut = getattr(self.facture, "get_statut_facture", lambda: "")() or "—"

        lbl_code = QLabel(f"Facture: {code}")
        lbl_code.setStyleSheet(f"font-size:12px; font-weight:bold; color:{MC.TEXT_PRIMARY};")
        lbl_date = QLabel(f"Date: {date_str}")
        lbl_date.setStyleSheet(f"font-size:11px; color:{MC.TEXT_SECONDARY};")
        lbl_statut = QLabel(statut)
        lbl_statut.setStyleSheet(
            f"font-size:10px; font-weight:bold; color:{MC.TEXT_PRIMARY}; "
            f"border:none; background:{MC.BORDER_LIGHT}; border-radius:10px; padding:2px 8px;"
        )

        lay.addWidget(lbl_code)
        lay.addStretch()
        lay.addWidget(lbl_statut)
        lay.addWidget(lbl_date)
        return card

    def _build_patient_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet("QFrame { background: transparent; border: none; }")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(4)

        title = QLabel("Informations patient")
        title.setStyleSheet(
            FacturePatientStyles.section_title(theme_manager.colors()['text_primary']) +
            " border:none; background:transparent;"
        )
        lay.addWidget(title)

        nom = f"{self.patient_info.get('prenom', '')} {self.patient_info.get('nom', '')}".strip()
        lbl_nom = QLabel(nom or "—")
        lbl_nom.setStyleSheet(f"font-size:12px; font-weight:bold; color:{MC.TEXT_PRIMARY};")
        lay.addWidget(lbl_nom)

        lbl_codes = QLabel(
            f"Patient ID: {self.patient_info.get('code_patient', '—')}"
            f"   •   Visite: {self.patient_info.get('code_visite', '—')}"
        )
        lbl_codes.setStyleSheet(f"font-size:10px; color:{MC.TEXT_SECONDARY};")
        lay.addWidget(lbl_codes)

        lbl_tel = QLabel(f"Téléphone: {self.patient_info.get('telephone', '—')}")
        lbl_tel.setStyleSheet(f"font-size:10px; color:{MC.TEXT_SECONDARY};")
        lay.addWidget(lbl_tel)

        return card

    def _build_total_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet("QFrame { background: transparent; border: none; }")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(4)

        title = QLabel("Total à payer")
        title.setStyleSheet(
            FacturePatientStyles.section_title(theme_manager.colors()['text_primary']) +
            " border:none; background:transparent;"
        )
        lay.addWidget(title)

        lbl_total = QLabel(f"{self.total:,.0f} GNF".replace(",", " "))
        lbl_total.setStyleSheet(
            f"font-size:18px; font-weight:bold; color:{FacturePatientStyles.BLEU_PRINCIPAL};"
        )
        lay.addWidget(lbl_total)
        return card

    def _build_services_list(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet("QFrame { background: transparent; border: none; }")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(6)

        title = QLabel("Services de la facture")
        title.setStyleSheet(
            FacturePatientStyles.section_title(theme_manager.colors()['text_primary']) +
            " border:none; background:transparent;"
        )
        lay.addWidget(title)

        # Combinaison stable :
        #   setWidgetResizable(True)  → Qt gère la largeur du container automatiquement
        #   setMinimumHeight(contenu) → Qt ne peut pas réduire sous la hauteur réelle
        #   → scroll vertical s'active dès que contenu > maxHeight(260)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {MC.BG_CARD}; }}"
            f"QScrollArea > QWidget {{ background: {MC.BG_CARD}; }}"
        )
        scroll.verticalScrollBar().setStyleSheet(FacturePatientStyles.scrollbar())
        scroll.setFixedHeight(240)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        container = QWidget()
        container.setStyleSheet(f"background: {MC.BG_CARD};")
        list_layout = QVBoxLayout(container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(6)
        list_layout.setAlignment(Qt.AlignTop)

        row_height = 54
        row_style = f"QFrame {{ background: {MC.BG_CARD}; border: none; border-radius: 10px; }}"

        for l in self.lignes:
            designation = getattr(l, "get_designation", lambda: "")()
            ref = getattr(l, "get_numero_reference", lambda: "")()
            qte = getattr(l, "get_quantite_facture", lambda: 1)()
            prix = getattr(l, "get_prix_applique", lambda: 0.0)()
            total = float(qte) * float(prix)

            row = QFrame()
            row.setFixedHeight(row_height)
            row.setStyleSheet(row_style)
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(10, 6, 10, 6)
            row_lay.setSpacing(10)

            icon = QLabel()
            icon.setPixmap(self._icone_service(designation).pixmap(18, 18))
            row_lay.addWidget(icon)

            info = QVBoxLayout()
            lbl_name = QLabel(designation or "—")
            lbl_name.setStyleSheet(f"font-size:11px; font-weight:bold; color:{MC.TEXT_PRIMARY};")
            lbl_ref = QLabel(f"Réf: {ref}")
            lbl_ref.setStyleSheet(f"font-size:10px; color:{MC.TEXT_SECONDARY};")
            info.addWidget(lbl_name)
            info.addWidget(lbl_ref)
            row_lay.addLayout(info, 1)

            lbl_qte = QLabel(f"Qté: {qte}")
            lbl_qte.setStyleSheet(f"font-size:10px; color:{MC.TEXT_SECONDARY};")
            row_lay.addWidget(lbl_qte)

            lbl_total = QLabel(f"{total:,.0f} GNF".replace(",", " "))
            lbl_total.setStyleSheet(
                f"font-size:11px; font-weight:bold; color:{FacturePatientStyles.BLEU_PRINCIPAL};"
            )
            row_lay.addWidget(lbl_total)

            list_layout.addWidget(row)

        # setMinimumHeight garantit que Qt ne compresse pas le container
        # même avec setWidgetResizable(True) — c'est ce qui déclenche le scroll
        n = max(len(self.lignes), 1)
        container.setMinimumHeight(n * row_height + (n - 1) * 6)

        scroll.setWidget(container)
        lay.addWidget(scroll)
        return card

    def showEvent(self, event) -> None:
        super().showEvent(event)
        try:
            parent = self.parentWidget()
            window = parent.window() if parent else None
            if window:
                geo = window.frameGeometry()
                x = geo.x() + (geo.width() - self.width()) // 2
                y = geo.y() + (geo.height() - self.height()) // 2
                self.move(max(0, x), max(0, y))
            else:
                screen_geo = self.screen().availableGeometry()
                x = screen_geo.x() + (screen_geo.width() - self.width()) // 2
                y = screen_geo.y() + (screen_geo.height() - self.height()) // 2
                self.move(x, y)
        except Exception:
            pass

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
        if "pharma" in d:
            return qta.icon("fa5s.pills",       color=_c['accent'])
        return qta.icon("fa5s.file-medical",    color=_c['primary'])

    def _build_paiement_section(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet("QFrame { background: transparent; border: none; }")
        lay = QHBoxLayout(card)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(10)

        lbl_mode = QLabel("Mode de paiement")
        lbl_mode.setStyleSheet(f"font-size:11px; font-weight:bold; color:{MC.TEXT_SECONDARY};")
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Especes", "Mobile Money", "Carte bancaire"])
        self.combo_mode.setFixedHeight(32)
        self.combo_mode.setStyleSheet(
            f"border:1px solid {MC.BORDER}; border-radius:8px; padding-left:8px; font-size:11px;"
        )
        self.combo_mode.currentIndexChanged.connect(self._toggle_phone)

        lbl_tel = QLabel("Téléphone")
        lbl_tel.setStyleSheet(f"font-size:11px; font-weight:bold; color:{MC.TEXT_SECONDARY};")
        self.input_tel = QLineEdit()
        self.input_tel.setFixedHeight(32)
        self.input_tel.setPlaceholderText("Ex: 628123456")
        self.input_tel.setStyleSheet(
            f"border:1px solid {MC.BORDER}; border-radius:8px; padding-left:8px; font-size:11px;"
        )

        col1 = QVBoxLayout()
        col1.addWidget(lbl_mode)
        col1.addWidget(self.combo_mode)

        col2 = QVBoxLayout()
        col2.addWidget(lbl_tel)
        col2.addWidget(self.input_tel)

        lay.addLayout(col1)
        lay.addLayout(col2)
        return card

    def _build_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addStretch()

        btn_print = QPushButton("Imprimer")
        btn_print.setFixedSize(110, 34)
        btn_print.setStyleSheet(
            f"background:{MC.BG_INPUT}; border-radius:8px; font-weight:bold; font-size:12px;"
            f"border:1px solid {MC.BORDER}; color:{MC.TEXT_PRIMARY};"
        )
        btn_print.setEnabled(bool(self.pdf_exporter))
        btn_print.clicked.connect(self._export_pdf)

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setFixedSize(110, 34)
        btn_cancel.setStyleSheet(
            f"background:{MC.BORDER}; border-radius:8px; font-weight:bold; font-size:12px;"
        )
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Valider")
        btn_ok.setFixedSize(110, 34)
        btn_ok.setStyleSheet(
            f"background:{FacturePatientStyles.BLEU_PRINCIPAL}; color:{theme_manager.colors()['text_inverse']}; "
            "border-radius:8px; font-weight:bold; font-size:12px;"
        )
        btn_ok.clicked.connect(self._validate)

        row.addWidget(btn_print)
        row.addWidget(btn_cancel)
        row.addWidget(btn_ok)
        return row

    def _divider(self) -> QFrame:
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background:{MC.BORDER}; border:none;")
        return line

    def _toggle_phone(self) -> None:
        is_mobile = self.combo_mode.currentText() == "Mobile Money"
        self.input_tel.setEnabled(is_mobile)
        if not is_mobile:
            self.input_tel.clear()

    def _validate(self) -> None:
        self.mode_paiement = self.combo_mode.currentText()
        self.telephone = self.input_tel.text().strip()
        if self.mode_paiement == "Mobile Money" and not self.telephone:
            from views.shared.message_box import CustomMessageBox
            CustomMessageBox.warning(
                self, "Attention", "Telephone requis pour Mobile Money",
                FacturePatientStyles.BLEU_PRINCIPAL
            )
            return
        # Demander si l'utilisateur veut imprimer
        if self.pdf_exporter:
            from views.shared.message_box import CustomMessageBox
            if CustomMessageBox.confirm(
                self, "Impression", "Voulez-vous imprimer la facture ?"
            ):
                self._export_pdf()
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        return {
            "mode_paiement": self.mode_paiement,
            "telephone": self.telephone,
        }

    def _export_pdf(self) -> None:
        if not self.pdf_exporter:
            return
            
        import os
        import tempfile
        from views.patient.fonctions_avancees.apercu_pdf_dialog import ApercuPDFDialog
        from views.shared.message_box import CustomMessageBox
        
        code_facture = getattr(self.facture, "get_code_facture", lambda: "facture")()
        fd, path = tempfile.mkstemp(suffix=".pdf", prefix=f"facture_{code_facture}_")
        os.close(fd)
        
        ok, msg = self.pdf_exporter(path)
        if ok and os.path.exists(path):
            ApercuPDFDialog(path, f"Aperçu - Facture {code_facture}", self).exec()
        else:
            CustomMessageBox.error(self, "PDF", f"Erreur de génération du PDF :\n{msg}")
