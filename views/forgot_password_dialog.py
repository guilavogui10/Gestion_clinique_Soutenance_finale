"""
forgot_password_dialog.py
-------------------------
Dialogue moderne pour la réinitialisation de mot de passe avec autorisation du DG.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QStackedWidget,
    QMessageBox
)
from PySide6.QtCore import Slot

from controllers.controleur_password_reset import PasswordResetController

class ForgotPasswordDialog(QDialog):
    send_request_finished = Signal(dict, str)
    verify_finished = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.controller = PasswordResetController()
        self.user_email = ""
        
        self.send_request_finished.connect(self._update_ui_after_send)
        self.verify_finished.connect(self._update_ui_after_verify)
        
        self.setWindowTitle("Mot de passe oublié")
        self.setModal(True)
        self.setFixedSize(480, 480)
        
        # Enlever la barre de titre par défaut
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(35, 30, 35, 30)
        container_layout.setSpacing(0)
        
        self._build_header(container_layout)
        
        # Stacked Widget pour les deux étapes
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background: transparent; border: none;")
        
        # Etape 1 : Demande d'e-mail
        step1_widget = QFrame()
        self._build_step1(step1_widget)
        self.stacked_widget.addWidget(step1_widget)
        
        # Etape 2 : Saisie du code
        step2_widget = QFrame()
        self._build_step2(step2_widget)
        self.stacked_widget.addWidget(step2_widget)
        
        container_layout.addWidget(self.stacked_widget)
        
        main_layout.addWidget(container)

    def _build_header(self, parent_layout):
        header_layout = QVBoxLayout()
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignCenter)
        
        icon_container = QFrame()
        icon_container.setFixedSize(80, 80)
        icon_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #E74C3C,
                    stop:1 #C0392B
                );
                border-radius: 40px;
            }
        """)
        
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon("fa5s.unlock-alt", color="white").pixmap(40, 40))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background: transparent; border: none;")
        icon_layout.addWidget(icon_label)
        
        header_layout.addWidget(icon_container, alignment=Qt.AlignCenter)
        
        title = QLabel("Mot de passe oublié")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #2C3E50;
            background: transparent;
            border: none;
        """)
        header_layout.addWidget(title)
        
        parent_layout.addLayout(header_layout)
        parent_layout.addSpacing(20)

    def _build_step1(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Message
        message = QLabel(
            "Veuillez saisir votre adresse e-mail. Une demande d'autorisation sera envoyée au Directeur Général pour valider la réinitialisation."
        )
        message.setWordWrap(True)
        message.setStyleSheet("""
            font-size: 13px;
            color: #475569;
            background: transparent;
            border: none;
            line-height: 1.5;
        """)
        layout.addWidget(message)
        layout.addSpacing(20)
        
        # Champ Email
        label = QLabel("Adresse e-mail")
        label.setStyleSheet("font-size: 13px; font-weight: 600; color: #475569; border: none;")
        layout.addWidget(label)
        layout.addSpacing(8)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Entrez votre e-mail")
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: #F8FAFC;
                border: 2px solid #E2E8F0;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                color: #1E293B;
            }
            QLineEdit:focus {
                border-color: #E74C3C;
                background-color: white;
            }
        """)
        self.email_input.textChanged.connect(self._on_email_changed)
        layout.addWidget(self.email_input)
        layout.addSpacing(25)
        
        # Label d'information (chargement ou erreur)
        self.info_label1 = QLabel("")
        self.info_label1.setWordWrap(True)
        self.info_label1.setStyleSheet("color: #E74C3C; font-size: 12px; border: none;")
        self.info_label1.hide()
        layout.addWidget(self.info_label1)
        layout.addSpacing(10)
        
        # Boutons
        self.btn_send_request = QPushButton("  Demander l'autorisation")
        self.btn_send_request.setIcon(qta.icon("fa5s.paper-plane", color="white"))
        self.btn_send_request.setFixedHeight(45)
        self.btn_send_request.setCursor(Qt.PointingHandCursor)
        self.btn_send_request.setEnabled(False)
        self.btn_send_request.setStyleSheet("""
            QPushButton {
                background-color: #CBD5E1;
                color: #94A3B8;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:enabled {
                background-color: #E74C3C;
                color: white;
            }
            QPushButton:enabled:hover {
                background-color: #C0392B;
            }
        """)
        self.btn_send_request.clicked.connect(self._on_send_request)
        layout.addWidget(self.btn_send_request)
        layout.addSpacing(10)
        
        self.btn_already_have_code = QPushButton("  J'ai déjà reçu un code")
        self.btn_already_have_code.setIcon(qta.icon("fa5s.key", color="#E74C3C"))
        self.btn_already_have_code.setFixedHeight(40)
        self.btn_already_have_code.setCursor(Qt.PointingHandCursor)
        self.btn_already_have_code.setEnabled(False)
        self.btn_already_have_code.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #E74C3C;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:enabled:hover {
                background-color: #FEF2F2;
                border-color: #FCA5A5;
            }
            QPushButton:disabled {
                color: #94A3B8;
                background-color: #F1F5F9;
            }
        """)
        self.btn_already_have_code.clicked.connect(self._on_already_have_code)
        layout.addWidget(self.btn_already_have_code)
        layout.addSpacing(12)
        
        btn_cancel = QPushButton("  Annuler")
        btn_cancel.setIcon(qta.icon("fa5s.times", color="#64748B"))
        btn_cancel.setFixedHeight(40)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #64748B;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
                border-color: #64748B;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)
        
        layout.addStretch()

    def _build_step2(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Message
        self.msg_step2 = QLabel()
        self.msg_step2.setWordWrap(True)
        self.msg_step2.setStyleSheet("""
            font-size: 13px;
            color: #0C4A6E;
            background-color: #F0F9FF;
            border: 1px solid #BAE6FD;
            border-radius: 12px;
            padding: 15px;
            line-height: 1.5;
        """)
        layout.addWidget(self.msg_step2)
        layout.addSpacing(20)
        
        # Champ OTP
        label = QLabel("Code d'autorisation (obtenu auprès du DG)")
        label.setStyleSheet("font-size: 13px; font-weight: 600; color: #475569; border: none;")
        layout.addWidget(label)
        layout.addSpacing(8)
        
        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Code à 6 chiffres")
        self.otp_input.setMaxLength(6)
        self.otp_input.setAlignment(Qt.AlignCenter)
        self.otp_input.setStyleSheet("""
            QLineEdit {
                background-color: #F8FAFC;
                border: 2px solid #E2E8F0;
                border-radius: 10px;
                padding: 14px;
                font-size: 20px;
                font-weight: bold;
                color: #1E293B;
                letter-spacing: 8px;
            }
            QLineEdit:focus {
                border-color: #3ECFCF;
                background-color: white;
            }
        """)
        self.otp_input.textChanged.connect(self._on_otp_changed)
        layout.addWidget(self.otp_input)
        layout.addSpacing(20)
        
        # Timer (remplacé par texte statique pour 24h)
        self.timer_label = QLabel("Ce code est valable 24 heures maximum.")
        self.timer_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #059669; border: none;")
        layout.addWidget(self.timer_label, alignment=Qt.AlignCenter)
        layout.addSpacing(10)
        
        # Info label
        self.info_label2 = QLabel("")
        self.info_label2.setWordWrap(True)
        self.info_label2.setStyleSheet("color: #E74C3C; font-size: 12px; border: none;")
        self.info_label2.hide()
        layout.addWidget(self.info_label2)
        layout.addSpacing(10)
        
        # Boutons
        self.btn_verify = QPushButton("  Valider et Réinitialiser")
        self.btn_verify.setIcon(qta.icon("fa5s.check-circle", color="white"))
        self.btn_verify.setFixedHeight(45)
        self.btn_verify.setCursor(Qt.PointingHandCursor)
        self.btn_verify.setEnabled(False)
        self.btn_verify.setStyleSheet("""
            QPushButton {
                background-color: #CBD5E1;
                color: #94A3B8;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:enabled {
                background-color: #3ECFCF;
                color: white;
            }
            QPushButton:enabled:hover {
                background-color: #35B8B8;
            }
        """)
        self.btn_verify.clicked.connect(self._on_verify)
        layout.addWidget(self.btn_verify)
        layout.addSpacing(12)
        
        btn_cancel = QPushButton("  Annuler")
        btn_cancel.setIcon(qta.icon("fa5s.times", color="#64748B"))
        btn_cancel.setFixedHeight(40)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #64748B;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
                border-color: #64748B;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)
        
        layout.addStretch()

    def _on_email_changed(self, text):
        is_valid = len(text.strip()) > 5 and "@" in text
        self.btn_send_request.setEnabled(is_valid)
        self.btn_already_have_code.setEnabled(is_valid)

    def _on_already_have_code(self):
        email = self.email_input.text().strip()
        self.user_email = email
        self.msg_step2.setText(
            f"Veuillez saisir le code d'autorisation que le Directeur Général vous a transmis "
            f"pour le compte {email}."
        )
        self.stacked_widget.setCurrentIndex(1)

    def _on_otp_changed(self, text):
        filtered = ''.join(c for c in text if c.isdigit())
        if filtered != text:
            self.otp_input.setText(filtered)
            return
        self.btn_verify.setEnabled(len(filtered) == 6)

    def _on_send_request(self):
        email = self.email_input.text().strip()
        self.info_label1.setText("Recherche de l'utilisateur et du Directeur Général...")
        self.info_label1.setStyleSheet("color: #F39C12;")
        self.info_label1.show()
        self.btn_send_request.setEnabled(False)
        
        import threading
        
        def process():
            result = self.controller.initier_reinitialisation(email)
            self.send_request_finished.emit(result, email)
            
        threading.Thread(target=process).start()

    @Slot()
    def _update_ui_after_send(self, result, email):
        self.btn_send_request.setEnabled(True)
        if result.get("status") == "success":
            self.user_email = email
            email_dg = result.get("email_dg_masque", "DG")
            self.msg_step2.setText(
                f"Une demande d'autorisation a été envoyée au Directeur Général ({email_dg}).\n\n"
                f"Veuillez le contacter pour obtenir le code de validation à 6 chiffres. Ce code est valable 24 heures."
            )
            self.stacked_widget.setCurrentIndex(1)
        else:
            self.info_label1.setText(result.get("message", "Erreur inconnue."))
            self.info_label1.setStyleSheet("color: #E74C3C;")

    def _on_verify(self):
        code = self.otp_input.text().strip()
        self.info_label2.setText("Vérification en cours...")
        self.info_label2.setStyleSheet("color: #F39C12;")
        self.info_label2.show()
        self.btn_verify.setEnabled(False)
        
        import threading
        
        def process():
            result = self.controller.valider_reinitialisation(self.user_email, code)
            self.verify_finished.emit(result)
            
        threading.Thread(target=process).start()

    @Slot()
    def _update_ui_after_verify(self, result):
        self.btn_verify.setEnabled(True)
        if result.get("status") in ["success", "warning"]:
            msg = result.get("message", "Mot de passe réinitialisé.")
            QMessageBox.information(self, "Succès", msg)
            self.accept()
        else:
            self.info_label2.setText(result.get("message", "Erreur inconnue."))
            self.info_label2.setStyleSheet("color: #E74C3C;")
