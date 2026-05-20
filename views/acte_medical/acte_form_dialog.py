"""
Formulaire de création / modification d'un acte médical.
"""
import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QFrame, QGraphicsDropShadowEffect,
    QWidget, QGridLayout,
)
from views.shared.theme_manager import theme_manager
from views.shared.message_box import CustomMessageBox
from models.model_acte_medicale import ActeMedical


class ActeFormDialog(QDialog):
    """
    Dialog de création ou édition d'un acte médical.
    Emet `saved` avec le dict des données saisies.
    """
    saved = Signal(dict)

    def __init__(self, controleur, acte: ActeMedical = None,
                 code_consultation: str = None, parent=None):
        super().__init__(parent)
        self.ctrl = controleur
        self.acte = acte          # None = création, sinon édition
        self.code_consultation_prefill = code_consultation

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(560, 560)

        self._init_ui()
        self._connect_signals()

        if self.acte:
            self._prefill()
        elif self.code_consultation_prefill:
            self.edit_consultation.setText(self.code_consultation_prefill)
            self.edit_consultation.setReadOnly(True)

        theme_manager.theme_changed.connect(self._apply_theme)
        self._apply_theme()

    # =========================================================================
    def _init_ui(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 70))

        self.container = QFrame(self)
        self.container.setGraphicsEffect(shadow)
        self.container.setObjectName("FormContainer")

        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self.header = QFrame()
        self.header.setFixedHeight(70)
        self.header.setObjectName("FormHeader")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(24, 0, 16, 0)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setObjectName("FormHeaderIcon")
        self._header_icon_lbl = icon_lbl

        title_lbl = QLabel("Nouvel acte médical" if not self.acte else "Modifier l'acte médical")
        title_lbl.setObjectName("FormHeaderTitle")
        header_layout.addWidget(icon_lbl)
        header_layout.addSpacing(12)
        header_layout.addWidget(title_lbl, 1)

        btn_close = QPushButton()
        btn_close.setFixedSize(32, 32)
        btn_close.setObjectName("BtnClose")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.reject)
        self._btn_close = btn_close
        header_layout.addWidget(btn_close)
        main_layout.addWidget(self.header)

        # Body
        body = QFrame()
        body.setObjectName("FormBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 20, 24, 20)
        body_layout.setSpacing(14)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        # Code consultation
        grid.addWidget(self._lbl("Code consultation *"), 0, 0)
        self.edit_consultation = QLineEdit()
        self.edit_consultation.setPlaceholderText("ex: CSL-2024-0001")
        grid.addWidget(self.edit_consultation, 0, 1)

        # Type acte
        grid.addWidget(self._lbl("Type d'acte *"), 1, 0)
        self.combo_type = QComboBox()
        self.combo_type.addItems(["examen", "chirurgie", "lunette", "prescription"])
        grid.addWidget(self.combo_type, 1, 1)

        # Source acte
        grid.addWidget(self._lbl("Source"), 2, 0)
        self.combo_source = QComboBox()
        self.combo_source.addItems(["consultation", "bilan", "urgence", "controle"])
        grid.addWidget(self.combo_source, 2, 1)

        # Mode réalisation
        grid.addWidget(self._lbl("Mode réalisation"), 3, 0)
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["interne", "externe"])
        grid.addWidget(self.combo_mode, 3, 1)

        body_layout.addLayout(grid)

        # Décision médicale
        body_layout.addWidget(self._lbl("Décision médicale *"))
        self.text_decision = QTextEdit()
        self.text_decision.setPlaceholderText("Décrivez la décision médicale ou la prescription…")
        self.text_decision.setFixedHeight(90)
        body_layout.addWidget(self.text_decision)

        # Raison refus (visible uniquement si nécessaire)
        self.lbl_raison = self._lbl("Raison du refus")
        self.edit_raison = QLineEdit()
        self.edit_raison.setPlaceholderText("Optionnel — si refus ou ailleurs")
        body_layout.addWidget(self.lbl_raison)
        body_layout.addWidget(self.edit_raison)

        main_layout.addWidget(body)

        # Footer
        footer = QFrame()
        footer.setObjectName("FormFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 12, 24, 12)
        footer_layout.setSpacing(10)
        footer_layout.addStretch()

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setObjectName("BtnCancel")
        self.btn_cancel.setFixedHeight(40)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.setObjectName("BtnSave")
        self.btn_save.setFixedHeight(40)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self._on_save)

        footer_layout.addWidget(self.btn_cancel)
        footer_layout.addWidget(self.btn_save)
        main_layout.addWidget(footer)

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(20, 20, 20, 20)
        wrapper.addWidget(self.container)

    def _lbl(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("FieldLabel")
        return lbl

    def _connect_signals(self):
        pass

    def _prefill(self):
        a = self.acte
        self.edit_consultation.setText(str(a.code_consultation or ""))
        self.edit_consultation.setReadOnly(True)
        idx = self.combo_type.findText(a.type_acte or "")
        if idx >= 0:
            self.combo_type.setCurrentIndex(idx)
        idx = self.combo_source.findText(a.source_acte or "consultation")
        if idx >= 0:
            self.combo_source.setCurrentIndex(idx)
        idx = self.combo_mode.findText(a.mode_realisation or "interne")
        if idx >= 0:
            self.combo_mode.setCurrentIndex(idx)
        self.text_decision.setPlainText(a.decision_medicale or "")
        self.edit_raison.setText(a.raison_refus or "")

    def _on_save(self):
        code_cons = self.edit_consultation.text().strip()
        type_acte = self.combo_type.currentText()
        decision  = self.text_decision.toPlainText().strip()

        if not code_cons:
            CustomMessageBox.warning(self, "Champ manquant", "Le code consultation est obligatoire.")
            return
        if not decision:
            CustomMessageBox.warning(self, "Champ manquant", "La décision médicale est obligatoire.")
            return

        data = {
            "code_consultation": code_cons,
            "type_acte":        type_acte,
            "source_acte":      self.combo_source.currentText(),
            "mode_realisation": self.combo_mode.currentText(),
            "decision_medicale":decision,
            "raison_refus":     self.edit_raison.text().strip() or None,
        }
        if self.acte:
            data["id_acte"] = self.acte.id_acte

        self.saved.emit(data)
        self.accept()

    # =========================================================================
    def _apply_theme(self):
        c = theme_manager.colors()
        self.container.setStyleSheet(f"""
            QFrame#FormContainer {{
                background: {c['bg_card']};
                border-radius: 20px;
                border: 1px solid {c['border']};
            }}
            QFrame#FormHeader {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {c['bg_card']}, stop:1 {c['bg_main']});
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }}
            QLabel#FormHeaderTitle {{
                font-size: 16px; font-weight: bold; color: {c['text_primary']};
                background: transparent;
            }}
            QFrame#FormBody {{
                background: {c['bg_card']};
            }}
            QFrame#FormFooter {{
                background: {c['bg_main']};
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
                border-top: 1px solid {c['border']};
            }}
            QLabel#FieldLabel {{
                color: {c['text_secondary']};
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }}
            QLineEdit, QComboBox, QTextEdit {{
                padding: 9px 12px;
                border: 1px solid {c['border']};
                border-radius: 8px;
                background: {c['bg_input']};
                font-size: 13px;
                color: {c['text_primary']};
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
                border: 2px solid {c['border_focus']};
                background: {c['bg_card']};
            }}
            QLineEdit:disabled {{
                background: {c['bg_main']};
                color: {c['primary']};
            }}
            QPushButton#BtnSave {{
                background: {c['primary']};
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 0 24px;
                border: none;
            }}
            QPushButton#BtnSave:hover {{ background: {c['primary_hover']}; }}
            QPushButton#BtnCancel {{
                background: {c['bg_main']};
                color: {c['text_secondary']};
                border-radius: 8px;
                font-size: 14px;
                padding: 0 18px;
                border: 1px solid {c['border']};
            }}
            QPushButton#BtnCancel:hover {{ background: {c['hover']}; }}
            QPushButton#BtnClose {{
                background: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton#BtnClose:hover {{ background: {c['danger_bg']}; }}
        """)
        self._btn_close.setIcon(qta.icon("fa5s.times", color=c["danger"]))
        self._header_icon_lbl.setPixmap(
            qta.icon("fa5s.clipboard-list", color=c["primary"]).pixmap(28, 28)
        )
