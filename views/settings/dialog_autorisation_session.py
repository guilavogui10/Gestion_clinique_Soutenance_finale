"""
dialog_autorisation_session.py
-------------------------------
Modal 3 étapes pour le changement sécurisé de session de visualisation.

Étape 1 : E-mail du DG → vérification rôle → envoi OTP
Étape 2 : Saisie du code OTP → vérification Vault
Étape 3 : Sélection de la session → confirmation

Signal émis à la fin : session_confirmee(code_session: str)
"""

import threading

import qtawesome as qta
from PySide6.QtCore import Qt, QSize, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QGraphicsDropShadowEffect,
    QStackedWidget, QComboBox, QWidget,
)

from controllers.controleur_session_autorisation import SessionAutorisationControleur


# ──────────────────────────── Couleurs ────────────────────────────────────────
_PRIMARY   = "#3D9B9B"
_PRIMARY_H = "#2C7A7B"
_SUCCESS   = "#059669"
_DANGER    = "#E74C3C"
_WARNING   = "#F39C12"
_MUTED     = "#64748B"
_BORDER    = "#E2E8F0"
_BG_INPUT  = "#F8FAFC"
_TEXT_DARK = "#1E293B"
_TEXT_MED  = "#475569"
_TEXT_INFO = "#0C4A6E"
_BG_INFO   = "#F0F9FF"
_BORDER_INFO = "#BAE6FD"
_BG_SUCCESS  = "#F0FDF4"
_BORDER_SUCCESS = "#86EFAC"


class DialogAutorisationSession(QDialog):
    """
    Modal sécurisé : vérifie que c'est le DG (email + OTP),
    puis laisse sélectionner la session à consulter.
    """

    session_confirmee = Signal(str)   # émis quand session choisie et confirmée

    _send_finished  = Signal(dict)    # résultat étape 1 (thread → UI)
    _verify_finished = Signal(dict)   # résultat étape 2 (thread → UI)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ctrl     = SessionAutorisationControleur()
        self._email_dg = ""
        self._sessions_data: list = []

        self._send_finished.connect(self._on_send_result)
        self._verify_finished.connect(self._on_verify_result)

        self.setWindowTitle("Accès Directeur Général — Sélection de session")
        self.setModal(True)
        self.setFixedSize(500, 560)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._init_ui()

    # =========================================================================
    # CONSTRUCTION
    # =========================================================================

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(15, 15, 15, 15)

        container = QFrame()
        container.setStyleSheet("QFrame { background-color: white; border-radius: 20px; }")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        container.setGraphicsEffect(shadow)

        inner = QVBoxLayout(container)
        inner.setContentsMargins(35, 28, 35, 28)
        inner.setSpacing(0)

        self._build_header(inner)

        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet("background: transparent; border: none;")

        step1 = QFrame()
        self._build_step1(step1)
        self.stacked.addWidget(step1)

        step2 = QFrame()
        self._build_step2(step2)
        self.stacked.addWidget(step2)

        step3 = QFrame()
        self._build_step3(step3)
        self.stacked.addWidget(step3)

        inner.addWidget(self.stacked)
        root.addWidget(container)

    # ── Header commun ─────────────────────────────────────────────────────────

    def _build_header(self, layout):
        hdr = QVBoxLayout()
        hdr.setSpacing(10)
        hdr.setAlignment(Qt.AlignCenter)

        icon_frame = QFrame()
        icon_frame.setFixedSize(76, 76)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {_PRIMARY}, stop:1 {_PRIMARY_H});
                border-radius: 38px;
            }}
        """)
        il = QHBoxLayout(icon_frame)
        il.setContentsMargins(0, 0, 0, 0)
        lbl_ic = QLabel()
        lbl_ic.setPixmap(qta.icon("fa5s.shield-alt", color="white").pixmap(36, 36))
        lbl_ic.setAlignment(Qt.AlignCenter)
        lbl_ic.setStyleSheet("background: transparent; border: none;")
        il.addWidget(lbl_ic)

        hdr.addWidget(icon_frame, alignment=Qt.AlignCenter)

        title = QLabel("Accès Directeur Général")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #2C3E50; "
            "background: transparent; border: none;"
        )
        hdr.addWidget(title)

        layout.addLayout(hdr)
        layout.addSpacing(16)

    # ── Étape 1 : E-mail ──────────────────────────────────────────────────────

    def _build_step1(self, w):
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        msg = QLabel(
            "Pour modifier la session de visualisation, saisissez l'adresse "
            "e-mail du Directeur Général. Un code de vérification lui sera envoyé."
        )
        msg.setWordWrap(True)
        msg.setStyleSheet(
            f"font-size: 13px; color: {_TEXT_MED}; background: transparent; "
            "border: none; line-height: 1.5;"
        )
        lay.addWidget(msg)
        lay.addSpacing(16)

        lbl_email = QLabel("Adresse e-mail du DG")
        lbl_email.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {_TEXT_MED}; border: none;"
        )
        lay.addWidget(lbl_email)
        lay.addSpacing(6)

        self._inp_email = QLineEdit()
        self._inp_email.setPlaceholderText("directeur@clinique.com")
        self._inp_email.setStyleSheet(f"""
            QLineEdit {{
                background-color: {_BG_INPUT};
                border: 2px solid {_BORDER};
                border-radius: 10px;
                padding: 11px;
                font-size: 14px;
                color: {_TEXT_DARK};
            }}
            QLineEdit:focus {{ border-color: {_PRIMARY}; background-color: white; }}
        """)
        self._inp_email.textChanged.connect(self._on_email_changed)
        lay.addWidget(self._inp_email)
        lay.addSpacing(18)

        self._lbl_info1 = QLabel("")
        self._lbl_info1.setWordWrap(True)
        self._lbl_info1.setStyleSheet(f"color: {_DANGER}; font-size: 12px; border: none;")
        self._lbl_info1.hide()
        lay.addWidget(self._lbl_info1)
        lay.addSpacing(6)

        self._btn_envoyer = self._mk_btn_primary(
            "  Envoyer le code", "fa5s.paper-plane", enabled=False
        )
        self._btn_envoyer.clicked.connect(self._on_envoyer)
        lay.addWidget(self._btn_envoyer)
        lay.addSpacing(8)

        self._btn_deja_code = self._mk_btn_secondary(
            "  J'ai déjà reçu un code", "fa5s.key", enabled=False
        )
        self._btn_deja_code.clicked.connect(self._on_deja_code)
        lay.addWidget(self._btn_deja_code)
        lay.addSpacing(8)

        lay.addWidget(self._mk_btn_annuler())
        lay.addStretch()

    # ── Étape 2 : Code OTP ────────────────────────────────────────────────────

    def _build_step2(self, w):
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._lbl_msg2 = QLabel()
        self._lbl_msg2.setWordWrap(True)
        self._lbl_msg2.setStyleSheet(f"""
            font-size: 13px; color: {_TEXT_INFO};
            background-color: {_BG_INFO};
            border: 1px solid {_BORDER_INFO};
            border-radius: 12px;
            padding: 14px;
            line-height: 1.5;
        """)
        lay.addWidget(self._lbl_msg2)
        lay.addSpacing(18)

        lbl_code = QLabel("Code de vérification (6 chiffres)")
        lbl_code.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {_TEXT_MED}; border: none;"
        )
        lay.addWidget(lbl_code)
        lay.addSpacing(6)

        self._inp_otp = QLineEdit()
        self._inp_otp.setPlaceholderText("_ _ _ _ _ _")
        self._inp_otp.setMaxLength(6)
        self._inp_otp.setAlignment(Qt.AlignCenter)
        self._inp_otp.setStyleSheet(f"""
            QLineEdit {{
                background-color: {_BG_INPUT};
                border: 2px solid {_BORDER};
                border-radius: 10px;
                padding: 13px;
                font-size: 22px;
                font-weight: bold;
                color: {_TEXT_DARK};
                letter-spacing: 10px;
            }}
            QLineEdit:focus {{ border-color: {_PRIMARY}; background-color: white; }}
        """)
        self._inp_otp.textChanged.connect(self._on_otp_changed)
        lay.addWidget(self._inp_otp)
        lay.addSpacing(10)

        lbl_validite = QLabel("Ce code est valable 5 minutes.")
        lbl_validite.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {_SUCCESS}; border: none;"
        )
        lay.addWidget(lbl_validite, alignment=Qt.AlignCenter)
        lay.addSpacing(8)

        self._lbl_info2 = QLabel("")
        self._lbl_info2.setWordWrap(True)
        self._lbl_info2.setStyleSheet(f"color: {_DANGER}; font-size: 12px; border: none;")
        self._lbl_info2.hide()
        lay.addWidget(self._lbl_info2)
        lay.addSpacing(8)

        self._btn_valider = self._mk_btn_primary(
            "  Valider l'accès", "fa5s.check-circle", enabled=False, color=_PRIMARY
        )
        self._btn_valider.clicked.connect(self._on_valider)
        lay.addWidget(self._btn_valider)
        lay.addSpacing(8)

        lay.addWidget(self._mk_btn_annuler())
        lay.addStretch()

    # ── Étape 3 : Sélection de session ────────────────────────────────────────

    def _build_step3(self, w):
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Bandeau succès
        bandeau = QFrame()
        bandeau.setStyleSheet(f"""
            QFrame {{
                background-color: {_BG_SUCCESS};
                border: 1px solid {_BORDER_SUCCESS};
                border-radius: 12px;
                padding: 6px;
            }}
        """)
        bl = QHBoxLayout(bandeau)
        bl.setContentsMargins(12, 8, 12, 8)
        bl.setSpacing(8)
        ic_ok = QLabel()
        ic_ok.setPixmap(qta.icon("fa5s.check-circle", color=_SUCCESS).pixmap(18, 18))
        ic_ok.setStyleSheet("background: transparent; border: none;")
        lbl_ok = QLabel("Accès autorisé — choisissez la session à consulter.")
        lbl_ok.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {_SUCCESS}; "
            "background: transparent; border: none;"
        )
        bl.addWidget(ic_ok)
        bl.addWidget(lbl_ok)
        bl.addStretch()
        lay.addWidget(bandeau)
        lay.addSpacing(14)

        lbl_sel = QLabel("Session à consulter")
        lbl_sel.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {_TEXT_MED}; border: none;"
        )
        lay.addWidget(lbl_sel)
        lay.addSpacing(6)

        self._combo_session = QComboBox()
        self._combo_session.setFixedHeight(34)
        self._combo_session.setStyleSheet(f"""
            QComboBox {{
                background-color: {_BG_INPUT};
                color: {_TEXT_DARK};
                border: 2px solid {_BORDER};
                border-radius: 10px;
                padding: 0 12px;
                font-size: 13px;
            }}
            QComboBox:focus {{ border-color: {_PRIMARY}; }}
            QComboBox::drop-down {{
                border: none; width: 28px;
                subcontrol-origin: padding; subcontrol-position: center right;
            }}
            QComboBox QAbstractItemView {{
                background-color: white;
                color: {_TEXT_DARK};
                border: 1px solid {_BORDER};
                selection-background-color: {_PRIMARY};
                selection-color: white;
                padding: 4px;
            }}
        """)
        self._combo_session.currentIndexChanged.connect(self._on_session_changed)
        lay.addWidget(self._combo_session)
        lay.addSpacing(10)

        # Carte détails
        self._details_card = QFrame()
        self._details_card.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid {_BORDER};
                border-radius: 10px;
            }}
        """)
        dl = QVBoxLayout(self._details_card)
        dl.setContentsMargins(12, 10, 12, 10)
        dl.setSpacing(5)

        self._lbl_d_nom    = QLabel("—")
        self._lbl_d_period = QLabel("—")
        self._lbl_d_statut = QLabel("—")

        for key_txt, val_lbl in [
            ("Nom :", self._lbl_d_nom),
            ("Période :", self._lbl_d_period),
            ("Statut :", self._lbl_d_statut),
        ]:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(6)
            lk = QLabel(key_txt)
            lk.setFixedWidth(68)
            lk.setStyleSheet(
                f"color: {_MUTED}; font-size: 11px; font-weight: 600; border: none;"
            )
            val_lbl.setStyleSheet(
                f"color: {_TEXT_DARK}; font-size: 11px; border: none;"
            )
            rl.addWidget(lk)
            rl.addWidget(val_lbl, 1)
            dl.addWidget(row)

        lay.addWidget(self._details_card)
        lay.addSpacing(12)

        self._btn_confirmer = self._mk_btn_primary(
            "  Confirmer la session", "fa5s.calendar-check", enabled=False, color=_PRIMARY
        )
        self._btn_confirmer.clicked.connect(self._on_confirmer)
        lay.addWidget(self._btn_confirmer)
        lay.addSpacing(8)

        lay.addWidget(self._mk_btn_annuler())
        lay.addStretch()

    # =========================================================================
    # HELPERS BOUTONS
    # =========================================================================

    def _mk_btn_primary(
        self, texte: str, icone: str, enabled: bool = True, color: str = _DANGER
    ) -> QPushButton:
        btn = QPushButton(texte)
        btn.setIcon(qta.icon(icone, color="white"))
        btn.setFixedHeight(44)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setEnabled(enabled)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #CBD5E1;
                color: #94A3B8;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:enabled {{
                background-color: {color};
                color: white;
            }}
            QPushButton:enabled:hover {{
                background-color: {_PRIMARY_H if color == _PRIMARY else "#C0392B"};
            }}
        """)
        return btn

    def _mk_btn_secondary(
        self, texte: str, icone: str, enabled: bool = True
    ) -> QPushButton:
        btn = QPushButton(texte)
        btn.setIcon(qta.icon(icone, color=_PRIMARY))
        btn.setFixedHeight(38)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setEnabled(enabled)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #F1F5F9;
                color: {_PRIMARY};
                border: 1px solid {_BORDER};
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:enabled:hover {{ background-color: #E0F2F1; border-color: {_PRIMARY}; }}
            QPushButton:disabled {{ color: #94A3B8; background-color: #F1F5F9; }}
        """)
        return btn

    def _mk_btn_annuler(self) -> QPushButton:
        btn = QPushButton("  Annuler")
        btn.setIcon(qta.icon("fa5s.times", color=_MUTED))
        btn.setFixedHeight(38)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #F1F5F9;
                color: {_MUTED};
                border: 1px solid {_BORDER};
                border-radius: 10px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #E2E8F0; border-color: {_MUTED}; }}
        """)
        btn.clicked.connect(self.reject)
        return btn

    # =========================================================================
    # LOGIQUE ÉTAPE 1 — E-MAIL
    # =========================================================================

    def _on_email_changed(self, text: str):
        ok = len(text.strip()) > 5 and "@" in text
        self._btn_envoyer.setEnabled(ok)
        self._btn_deja_code.setEnabled(ok)

    def _on_deja_code(self):
        self._email_dg = self._inp_email.text().strip()
        self._lbl_msg2.setText(
            f"Saisissez le code de vérification envoyé à <b>{self._email_dg}</b>."
        )
        self.stacked.setCurrentIndex(1)

    def _on_envoyer(self):
        email = self._inp_email.text().strip()
        self._lbl_info1.setText("Vérification en cours…")
        self._lbl_info1.setStyleSheet(f"color: {_WARNING}; font-size: 12px; border: none;")
        self._lbl_info1.show()
        self._btn_envoyer.setEnabled(False)

        def _run():
            result = self._ctrl.initier_autorisation(email)
            self._send_finished.emit(result)

        threading.Thread(target=_run, daemon=True).start()

    @Slot(dict)
    def _on_send_result(self, result: dict):
        self._btn_envoyer.setEnabled(True)
        if result.get("status") == "success":
            self._email_dg = self._inp_email.text().strip()
            email_masque   = result.get("email_masque", self._email_dg)
            self._lbl_msg2.setText(
                f"Un code de vérification a été envoyé à <b>{email_masque}</b>.\n\n"
                "Saisissez le code reçu. Il est valable <b>5 minutes</b>."
            )
            self.stacked.setCurrentIndex(1)
        else:
            self._lbl_info1.setText(result.get("message", "Erreur inconnue."))
            self._lbl_info1.setStyleSheet(f"color: {_DANGER}; font-size: 12px; border: none;")

    # =========================================================================
    # LOGIQUE ÉTAPE 2 — CODE OTP
    # =========================================================================

    def _on_otp_changed(self, text: str):
        filtered = "".join(c for c in text if c.isdigit())
        if filtered != text:
            self._inp_otp.setText(filtered)
            return
        self._btn_valider.setEnabled(len(filtered) == 6)

    def _on_valider(self):
        code = self._inp_otp.text().strip()
        self._lbl_info2.setText("Vérification en cours…")
        self._lbl_info2.setStyleSheet(f"color: {_WARNING}; font-size: 12px; border: none;")
        self._lbl_info2.show()
        self._btn_valider.setEnabled(False)

        def _run():
            result = self._ctrl.verifier_autorisation(self._email_dg, code)
            self._verify_finished.emit(result)

        threading.Thread(target=_run, daemon=True).start()

    @Slot(dict)
    def _on_verify_result(self, result: dict):
        self._btn_valider.setEnabled(True)
        if result.get("status") == "success":
            self._charger_sessions_combo()
            self.stacked.setCurrentIndex(2)
        else:
            self._lbl_info2.setText(result.get("message", "Erreur inconnue."))
            self._lbl_info2.setStyleSheet(
                f"color: {_DANGER}; font-size: 12px; border: none;"
            )

    # =========================================================================
    # LOGIQUE ÉTAPE 3 — SÉLECTION SESSION
    # =========================================================================

    def _charger_sessions_combo(self):
        self._combo_session.clear()
        self._sessions_data = []
        try:
            from controllers.controleur_visite import VisiteControleur
            sessions = VisiteControleur().lister_sessions_completes()
        except Exception:
            sessions = []

        for s in sessions:
            code   = s.get("code_session", "")
            nom    = s.get("nom_session") or code
            statut = s.get("statut", "")
            marqueur = "  ● En cours" if statut == "En_cours" else ""
            self._combo_session.addItem(f"{nom} ({code}){marqueur}", code)
            self._sessions_data.append(s)

        if self._combo_session.count() > 0:
            self._btn_confirmer.setEnabled(True)
            self._on_session_changed(0)

    def _on_session_changed(self, index: int):
        if index < 0 or index >= len(self._sessions_data):
            return
        s      = self._sessions_data[index]
        nom    = s.get("nom_session") or s.get("code_session", "—")
        debut  = str(s.get("date_debut") or "—")
        fin    = str(s.get("date_fin")   or "—")
        statut = s.get("statut", "—")
        self._lbl_d_nom.setText(nom)
        self._lbl_d_period.setText(f"{debut}  →  {fin}")
        self._lbl_d_statut.setText("En cours" if statut == "En_cours" else statut)

    def _on_confirmer(self):
        idx = self._combo_session.currentIndex()
        if idx < 0 or idx >= len(self._sessions_data):
            return
        code_session = self._sessions_data[idx].get("code_session", "")
        if code_session:
            self.session_confirmee.emit(code_session)
            self.accept()
