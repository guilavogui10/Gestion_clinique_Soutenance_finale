"""
otp_autorisation_dialog.py
---------------------------
Dialogue OTP pour autoriser des actions sensibles (modification, suppression, consultation résultats).
Réutilise le design du dialogue OTP de connexion.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
)


class OTPAutorisationDialog(QDialog):
    """
    Dialogue moderne pour la saisie du code OTP d'autorisation.
    Utilisé pour autoriser des actions sensibles.
    """
    
    resend_requested = Signal()
    
    def __init__(self, action: str, contexte: str, masked_email: str, est_pour_soi: bool = False, parent=None):
        """
        Args:
            action: Type d'action (modification, suppression, consultation)
            contexte: Description du contexte (ex: "Chirurgie #CH001")
            masked_email: Email masqué du destinataire
            est_pour_soi: True si l'OTP est envoyé à l'utilisateur lui-même (responsable)
        """
        super().__init__(parent)
        self.action = action
        self.contexte = contexte
        self.masked_email = masked_email
        self.est_pour_soi = est_pour_soi
        self.remaining_seconds = 300  # 5 minutes
        self.otp_code = ""
        
        self.setWindowTitle("Autorisation requise")
        self.setModal(True)
        self.setFixedSize(500, 450)
        
        # Enlever la barre de titre par défaut
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._init_ui()
        self._start_timer()
    
    def _init_ui(self):
        # Layout principal avec marges pour l'ombre
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Conteneur principal avec ombre
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
            }
        """)
        
        # Ombre portée
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(35, 30, 35, 30)
        container_layout.setSpacing(0)
        
        # En-tête avec icône
        self._build_header(container_layout)
        
        # Message principal
        self._build_message(container_layout)
        
        # Champs de saisie OTP (6 chiffres)
        self._build_otp_inputs(container_layout)
        
        # Timer
        self._build_timer(container_layout)
        
        # Boutons
        self._build_buttons(container_layout)
        
        main_layout.addWidget(container)
    
    def _build_header(self, parent_layout):
        header_layout = QVBoxLayout()
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignCenter)
        
        # Icône selon le type d'action
        icon_name = "fa5s.lock" if self.action == "consultation" else "fa5s.shield-alt"
        icon_color_start = "#F59E0B" if self.action == "suppression" else "#3ECFCF"
        icon_color_end = "#D97706" if self.action == "suppression" else "#2D9999"
        
        icon_container = QFrame()
        icon_container.setFixedSize(80, 80)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {icon_color_start},
                    stop:1 {icon_color_end}
                );
                border-radius: 40px;
            }}
        """)
        
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color="white").pixmap(40, 40))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background: transparent; border: none;")
        icon_layout.addWidget(icon_label)
        
        header_layout.addWidget(icon_container, alignment=Qt.AlignCenter)
        
        # Titre selon le type d'action
        if self.action == "consultation":
            titre = "Consultation de résultats"
        elif self.action == "modification":
            titre = "Autorisation de modification"
        elif self.action == "suppression":
            titre = "Autorisation de suppression"
        else:
            titre = "Autorisation requise"
        
        title = QLabel(titre)
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
    
    def _build_message(self, parent_layout):
        # Message avec icône
        msg_frame = QFrame()
        
        if self.action == "suppression":
            bg_color = "#FEF3C7"
            border_color = "#FDE68A"
            icon_color = "#D97706"
            text_color = "#92400E"
        else:
            bg_color = "#F0F9FF"
            border_color = "#BAE6FD"
            icon_color = "#0EA5E9"
            text_color = "#0C4A6E"
        
        msg_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        msg_layout = QHBoxLayout(msg_frame)
        msg_layout.setContentsMargins(15, 12, 15, 12)
        msg_layout.setSpacing(12)
        
        # Icône
        icon = QLabel()
        icon.setPixmap(qta.icon("fa5s.info-circle", color=icon_color).pixmap(20, 20))
        icon.setStyleSheet("background: transparent; border: none;")
        msg_layout.addWidget(icon, alignment=Qt.AlignTop)
        
        # Texte selon le contexte
        if self.est_pour_soi:
            message_text = (
                f"<b>Action :</b> {self.action.capitalize()}<br>"
                f"<b>Contexte :</b> {self.contexte}<br><br>"
                f"Un code de vérification a été envoyé à votre adresse :<br>"
                f"<b>{self.masked_email}</b><br><br>"
                f"Veuillez saisir ce code pour confirmer cette action."
            )
        else:
            message_text = (
                f"<b>Action :</b> {self.action.capitalize()}<br>"
                f"<b>Contexte :</b> {self.contexte}<br><br>"
                f"Un code d'autorisation a été envoyé au responsable :<br>"
                f"<b>{self.masked_email}</b><br><br>"
                f"Demandez-lui le code et saisissez-le ci-dessous."
            )
        
        message = QLabel(message_text)
        message.setWordWrap(True)
        message.setStyleSheet(f"""
            font-size: 12px;
            color: {text_color};
            background: transparent;
            border: none;
            line-height: 1.5;
        """)
        msg_layout.addWidget(message, 1)
        
        parent_layout.addWidget(msg_frame)
        parent_layout.addSpacing(25)
    
    def _build_otp_inputs(self, parent_layout):
        # Label
        label = QLabel("Code d'autorisation")
        label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #475569;
            background: transparent;
            border: none;
        """)
        parent_layout.addWidget(label)
        parent_layout.addSpacing(8)
        
        # Champ de saisie unique (6 chiffres)
        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Entrez le code à 6 chiffres")
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
        self.otp_input.returnPressed.connect(self._on_verify)
        
        parent_layout.addWidget(self.otp_input)
        parent_layout.addSpacing(20)
    
    def _build_timer(self, parent_layout):
        timer_frame = QFrame()
        timer_frame.setStyleSheet("""
            QFrame {
                background-color: #FEF3C7;
                border: 1px solid #FDE68A;
                border-radius: 10px;
            }
        """)
        
        timer_layout = QHBoxLayout(timer_frame)
        timer_layout.setContentsMargins(12, 8, 12, 8)
        timer_layout.setSpacing(8)
        
        # Icône horloge
        clock_icon = QLabel()
        clock_icon.setPixmap(qta.icon("fa5s.clock", color="#D97706").pixmap(16, 16))
        clock_icon.setStyleSheet("background: transparent; border: none;")
        timer_layout.addWidget(clock_icon)
        
        # Texte timer
        self.timer_label = QLabel("Code valide pendant : 05:00")
        self.timer_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 600;
            color: #92400E;
            background: transparent;
            border: none;
        """)
        timer_layout.addWidget(self.timer_label)
        timer_layout.addStretch()
        
        parent_layout.addWidget(timer_frame)
        parent_layout.addSpacing(20)
    
    def _build_buttons(self, parent_layout):
        # Bouton Vérifier
        self.btn_verify = QPushButton("  Autoriser l'action")
        self.btn_verify.setIcon(qta.icon("fa5s.check-circle", color="white"))
        self.btn_verify.setIconSize(qta.icon("fa5s.check-circle").pixmap(18, 18).size())
        self.btn_verify.setFixedHeight(48)
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
            QPushButton:enabled:pressed {
                background-color: #2D9999;
            }
        """)
        self.btn_verify.clicked.connect(self._on_verify)
        parent_layout.addWidget(self.btn_verify)
        parent_layout.addSpacing(12)
        
        # Ligne de séparation
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #E2E8F0; max-height: 1px; border: none;")
        parent_layout.addWidget(separator)
        parent_layout.addSpacing(12)
        
        # Boutons secondaires
        secondary_layout = QHBoxLayout()
        secondary_layout.setSpacing(10)
        
        # Bouton Renvoyer le code (seulement si pour soi)
        if self.est_pour_soi:
            self.btn_resend = QPushButton("  Renvoyer le code")
            self.btn_resend.setIcon(qta.icon("fa5s.redo", color="#3ECFCF"))
            self.btn_resend.setIconSize(qta.icon("fa5s.redo").pixmap(14, 14).size())
            self.btn_resend.setFixedHeight(40)
            self.btn_resend.setCursor(Qt.PointingHandCursor)
            self.btn_resend.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9;
                    color: #3ECFCF;
                    border: 1px solid #E2E8F0;
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                    border-color: #3ECFCF;
                }
            """)
            self.btn_resend.clicked.connect(self._on_resend)
            secondary_layout.addWidget(self.btn_resend)
        
        # Bouton Annuler
        btn_cancel = QPushButton("  Annuler")
        btn_cancel.setIcon(qta.icon("fa5s.times", color="#64748B"))
        btn_cancel.setIconSize(qta.icon("fa5s.times").pixmap(14, 14).size())
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
        secondary_layout.addWidget(btn_cancel)
        
        parent_layout.addLayout(secondary_layout)
    
    def _start_timer(self):
        """Démarre le compte à rebours de 5 minutes"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer)
        self.timer.start(1000)  # Mise à jour chaque seconde
    
    def _update_timer(self):
        """Met à jour l'affichage du timer"""
        self.remaining_seconds -= 1
        
        if self.remaining_seconds <= 0:
            self.timer.stop()
            self.timer_label.setText("Code expiré !")
            self.timer_label.setStyleSheet("""
                font-size: 11px;
                font-weight: 600;
                color: #DC2626;
                background: transparent;
                border: none;
            """)
            self.otp_input.setEnabled(False)
            self.btn_verify.setEnabled(False)
            return
        
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.timer_label.setText(f"Code valide pendant : {minutes:02d}:{seconds:02d}")
        
        # Changer la couleur si moins de 1 minute
        if self.remaining_seconds < 60:
            parent = self.timer_label.parent()
            if isinstance(parent, QFrame):
                parent.setStyleSheet("""
                    QFrame {
                        background-color: #FEE2E2;
                        border: 1px solid #FCA5A5;
                        border-radius: 10px;
                    }
                """)
            self.timer_label.setStyleSheet("""
                font-size: 11px;
                font-weight: 600;
                color: #DC2626;
                background: transparent;
                border: none;
            """)
    
    def _on_otp_changed(self, text):
        """Active le bouton Vérifier si 6 chiffres sont saisis"""
        # Filtrer pour ne garder que les chiffres
        filtered = ''.join(c for c in text if c.isdigit())
        if filtered != text:
            self.otp_input.setText(filtered)
            return
        
        self.btn_verify.setEnabled(len(filtered) == 6)
    
    def _on_verify(self):
        """Valide le code OTP saisi"""
        self.otp_code = self.otp_input.text().strip()
        if len(self.otp_code) == 6:
            self.accept()
    
    def _on_resend(self):
        """Demande le renvoi d'un nouveau code OTP"""
        self.resend_requested.emit()
        # Réinitialiser le timer
        self.remaining_seconds = 300
        self.otp_input.clear()
        self.otp_input.setEnabled(True)
        self.timer_label.setText("Code valide pendant : 05:00")
        self.timer_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 600;
            color: #92400E;
            background: transparent;
            border: none;
        """)
        # Réinitialiser le style du frame timer
        parent = self.timer_label.parent()
        if isinstance(parent, QFrame):
            parent.setStyleSheet("""
                QFrame {
                    background-color: #FEF3C7;
                    border: 1px solid #FDE68A;
                    border-radius: 10px;
                }
            """)
    
    def get_otp_code(self) -> str:
        """Retourne le code OTP saisi"""
        return self.otp_code
