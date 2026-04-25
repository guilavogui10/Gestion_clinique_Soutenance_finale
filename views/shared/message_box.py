from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame, QGridLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter
import qtawesome as qta
from views.shared.theme_manager import theme_manager
from views.shared.styles import Styles


class CustomMessageBox(QDialog):
    """
    Boîte de dialogue moderne avec design épuré.
    Supporte 3 types : success, error, info
    S'adapte automatiquement aux thèmes (clair/sombre/ocean)
    Avec overlay semi-transparent pour se démarquer de l'interface
    """
    
    def __init__(self, title, message, msg_type="success", show_cancel=False, parent=None, is_success=None):
        """
        Args:
            title: Titre de la boîte (peut être vide)
            message: Message principal
            msg_type: "success", "error", "warning", "info"
            show_cancel: Si True, affiche le bouton Annuler
            parent: Widget parent
            is_success: (DEPRECATED) Utiliser msg_type à la place. Gardé pour rétrocompatibilité.
        """
        super().__init__(parent)
        
        # Rétrocompatibilité avec l'ancien paramètre is_success
        if is_success is not None:
            self.msg_type = "success" if is_success else "error"
        else:
            self.msg_type = msg_type
        
        self.show_cancel = show_cancel
        self.result_value = False
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self._build_ui(title, message)
        theme_manager.theme_changed.connect(self._apply_theme)
        self._apply_theme()
        
        # Animation d'entrée
        self._animate_in()
    
    def paintEvent(self, event):
        """Dessine l'overlay semi-transparent avec bords arrondis derrière la boîte."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculer la taille et position de l'overlay arrondi
        # L'overlay doit être plus grand que la boîte blanche
        overlay_width = 560
        overlay_height = self.frame.height() + 80
        overlay_x = (self.width() - overlay_width) // 2
        overlay_y = (self.height() - overlay_height) // 2
        
        # Dessiner l'overlay gris avec bords arrondis
        overlay_color = QColor(0, 0, 0, 120)  # Noir avec 47% d'opacité
        painter.setBrush(overlay_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(overlay_x, overlay_y, overlay_width, overlay_height, 24, 24)
        
        painter.end()
    
    def _animate_in(self):
        """Animation d'apparition de la boîte."""
        self.frame.setGraphicsEffect(None)  # Retire temporairement l'ombre
        
        # Animation d'échelle (zoom in)
        self.frame.setStyleSheet(self.frame.styleSheet() + "QFrame#MessageBoxFrame { transform: scale(0.8); }")
        
        # Réappliquer l'ombre après un court délai
        from PySide6.QtCore import QTimer
        QTimer.singleShot(50, self._restore_shadow)
    
    def _restore_shadow(self):
        """Restaure l'ombre après l'animation."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.frame.setGraphicsEffect(shadow)
    
    def _build_ui(self, title, message):
        """Construit l'interface de la boîte de dialogue."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Frame principal avec ombre
        self.frame = QFrame()
        self.frame.setObjectName("MessageBoxFrame")
        self.frame.setFixedWidth(480)
        
        # Ombre portée douce et prononcée
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.frame.setGraphicsEffect(shadow)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(40, 40, 40, 40)
        frame_layout.setSpacing(20)
        
        # Icône circulaire en haut
        self.icon_container = QFrame()
        self.icon_container.setFixedSize(80, 80)
        self.icon_container.setObjectName("IconContainer")
        icon_container_layout = QVBoxLayout(self.icon_container)
        icon_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_icon = QLabel()
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        icon_container_layout.addWidget(self.lbl_icon)
        
        icon_wrapper = QHBoxLayout()
        icon_wrapper.addStretch()
        icon_wrapper.addWidget(self.icon_container)
        icon_wrapper.addStretch()
        frame_layout.addLayout(icon_wrapper)
        
        # Zone de message avec fond subtil
        self.message_container = QFrame()
        self.message_container.setObjectName("MessageContainer")
        message_layout = QVBoxLayout(self.message_container)
        message_layout.setContentsMargins(24, 20, 24, 20)
        message_layout.setSpacing(8)
        
        # Titre (optionnel)
        if title:
            self.lbl_title = QLabel(title)
            self.lbl_title.setObjectName("MessageTitle")
            self.lbl_title.setAlignment(Qt.AlignCenter)
            self.lbl_title.setWordWrap(True)
            message_layout.addWidget(self.lbl_title)
        else:
            self.lbl_title = None
        
        # Message principal
        self.lbl_message = QLabel(message)
        self.lbl_message.setObjectName("MessageText")
        self.lbl_message.setAlignment(Qt.AlignCenter)
        self.lbl_message.setWordWrap(True)
        message_layout.addWidget(self.lbl_message)
        
        frame_layout.addWidget(self.message_container)
        frame_layout.addSpacing(10)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        buttons_layout.addStretch()
        
        if self.show_cancel:
            self.btn_cancel = QPushButton("Annuler")
            self.btn_cancel.setObjectName("CancelButton")
            self.btn_cancel.setFixedSize(140, 45)
            self.btn_cancel.setCursor(Qt.PointingHandCursor)
            self.btn_cancel.clicked.connect(self.reject)
            buttons_layout.addWidget(self.btn_cancel)
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setObjectName("OkButton")
        self.btn_ok.setFixedSize(140, 45)
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.clicked.connect(self._on_accept)
        buttons_layout.addWidget(self.btn_ok)
        
        buttons_layout.addStretch()
        frame_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(self.frame)
    
    def _on_accept(self):
        """Gère l'acceptation de la boîte."""
        self.result_value = True
        self.accept()
    
    def _get_icon_config(self):
        """Retourne l'icône et la couleur selon le type de message."""
        c = theme_manager.colors()
        configs = {
            "success": ("fa5s.check-circle", c['success']),
            "error": ("fa5s.times-circle", c['danger']),
            "warning": ("fa5s.exclamation-triangle", c['warning']),
            "info": ("fa5s.info-circle", c['info']),
        }
        return configs.get(self.msg_type, configs["info"])
    
    def _apply_theme(self):
        """Applique le thème actif à la boîte de dialogue."""
        c = theme_manager.colors()
        icon_name, accent_color = self._get_icon_config()
        
        # Frame principal - Toujours blanc/clair pour contraster avec l'overlay
        frame_bg = "#FFFFFF" if theme_manager.current != "sombre" else "#1C2430"
        self.frame.setStyleSheet(f"""
            QFrame#MessageBoxFrame {{
                background-color: {frame_bg};
                border-radius: 20px;
                border: none;
            }}
        """)
        
        # Conteneur icône circulaire
        self.icon_container.setStyleSheet(f"""
            QFrame#IconContainer {{
                background-color: transparent;
                border: 3px solid {accent_color};
                border-radius: 40px;
            }}
        """)
        
        # Icône
        self.lbl_icon.setPixmap(qta.icon(icon_name, color=accent_color).pixmap(40, 40))
        self.lbl_icon.setStyleSheet("background: transparent; border: none;")
        
        # Conteneur message - Fond subtil
        msg_bg = "#F5F7FA" if theme_manager.current != "sombre" else "#0F1419"
        self.message_container.setStyleSheet(f"""
            QFrame#MessageContainer {{
                background-color: {msg_bg};
                border-radius: 12px;
                border: none;
            }}
        """)
        
        # Titre
        title_color = "#1A2E35" if theme_manager.current != "sombre" else c['text_primary']
        if self.lbl_title:
            self.lbl_title.setStyleSheet(f"""
                QLabel#MessageTitle {{
                    color: {title_color};
                    font-size: 16px;
                    font-weight: 700;
                    background: transparent;
                    border: none;
                }}
            """)
        
        # Message
        text_color = "#5F7A84" if theme_manager.current != "sombre" else c['text_secondary']
        self.lbl_message.setStyleSheet(f"""
            QLabel#MessageText {{
                color: {text_color};
                font-size: 14px;
                font-weight: 500;
                background: transparent;
                border: none;
                line-height: 1.5;
            }}
        """)
        
        # Bouton OK (primaire)
        self.btn_ok.setStyleSheet(f"""
            QPushButton#OkButton {{
                background-color: {accent_color};
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton#OkButton:hover {{
                background-color: {c['primary_hover']};
            }}
            QPushButton#OkButton:pressed {{
                background-color: {c['primary_hover']};
            }}
        """)
        
        # Bouton Annuler (secondaire)
        cancel_text = "#5F7A84" if theme_manager.current != "sombre" else c['text_secondary']
        cancel_border = "#D8E2E0" if theme_manager.current != "sombre" else c['border']
        if self.show_cancel:
            self.btn_cancel.setStyleSheet(f"""
                QPushButton#CancelButton {{
                    background-color: transparent;
                    color: {cancel_text};
                    border: 2px solid {cancel_border};
                    border-radius: 12px;
                    font-size: 14px;
                    font-weight: 600;
                }}
                QPushButton#CancelButton:hover {{
                    background-color: {msg_bg};
                    border-color: {cancel_text};
                    color: {title_color};
                }}
                QPushButton#CancelButton:pressed {{
                    background-color: {cancel_border};
                }}
            """)
    
    @staticmethod
    def show_success(message, title="Succès", show_cancel=False, parent=None):
        """Affiche une boîte de succès."""
        dialog = CustomMessageBox(title, message, "success", show_cancel, parent)
        return dialog.exec() == QDialog.Accepted
    
    @staticmethod
    def show_error(message, title="Erreur", show_cancel=False, parent=None):
        """Affiche une boîte d'erreur."""
        dialog = CustomMessageBox(title, message, "error", show_cancel, parent)
        return dialog.exec() == QDialog.Accepted
    
    @staticmethod
    def show_warning(message, title="Attention", show_cancel=False, parent=None):
        """Affiche une boîte d'avertissement."""
        dialog = CustomMessageBox(title, message, "warning", show_cancel, parent)
        return dialog.exec() == QDialog.Accepted
    
    @staticmethod
    def show_info(message, title="Information", show_cancel=False, parent=None):
        """Affiche une boîte d'information."""
        dialog = CustomMessageBox(title, message, "info", show_cancel, parent)
        return dialog.exec() == QDialog.Accepted
    
    @staticmethod
    def show_question(message, title="Confirmation", parent=None):
        """Affiche une boîte de confirmation avec boutons OK/Annuler."""
        dialog = CustomMessageBox(title, message, "info", show_cancel=True, parent=parent)
        return dialog.exec() == QDialog.Accepted



class PatientDetailDialog(QDialog):
    def __init__(self, patient, parent=None):
        super().__init__(parent)
        self.patient = patient
        self.setWindowTitle(f"Détails - {patient.get_nom()}")
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        
        self.init_ui()
        self.apply_theme()

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(Styles.dialog_full())

    def init_ui(self):
        c = theme_manager.colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- HEADER (Avatar + Nom) ---
        header = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon("fa5s.user-circle", color=c['primary']).pixmap(80, 80))
        
        info_header = QVBoxLayout()
        lbl_nom = QLabel(f"{self.patient.get_nom()} {self.patient.get_prenom()}")
        lbl_nom.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {c['primary']};")
        lbl_code = QLabel(f"Code Patient: {self.patient.get_code_patient()}")
        lbl_code.setStyleSheet(f"font-size: 14px; color: {c['text_muted']}; font-style: italic;")
        
        info_header.addWidget(lbl_nom)
        info_header.addWidget(lbl_code)
        header.addWidget(icon_label)
        header.addLayout(info_header)
        header.addStretch()
        layout.addLayout(header)

        # --- SEPARATEUR ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {c['border_light']};")
        layout.addWidget(line)

        # --- CORPS (Informations détaillées) ---
        grid = QGridLayout()
        grid.setSpacing(15)

        def add_info_row(row, label, value, icon):
            ic = QLabel()
            ic.setPixmap(qta.icon(icon, color=c['primary']).pixmap(20, 20))
            lbl = QLabel(f"<b>{label}:</b>")
            val = QLabel(str(value))
            val.setStyleSheet(f"color: {c['text_primary']};")
            grid.addWidget(ic, row, 0)
            grid.addWidget(lbl, row, 1)
            grid.addWidget(val, row, 2)

        add_info_row(0, "Téléphone", self.patient.get_telephone(), "fa5s.phone")
        add_info_row(1, "Genre", self.patient.get_genre(), "fa5s.venus-mars")
        add_info_row(2, "Naissance", self.patient.get_naissance(), "fa5s.calendar-alt")
        add_info_row(3, "Profession", self.patient.get_profession(), "fa5s.briefcase")
        add_info_row(4, "Adresse", self.patient.get_adresse(), "fa5s.map-marker-alt")

        layout.addLayout(grid)
        layout.addStretch()

        # --- BOUTON IMPRIMER ---
        self.btn_print = QPushButton(qta.icon("fa5s.print", color=c['text_inverse']), " Imprimer le carnet")
        self.btn_print.setCursor(Qt.PointingHandCursor)
        self.btn_print.setFixedHeight(45)
        self.btn_print.setStyleSheet(Styles.button_primary())
        # Ici on connectera ta méthode d'impression
        self.btn_print.clicked.connect(self.imprimer_carnet)
        layout.addWidget(self.btn_print)

    def imprimer_carnet(self):
        from PySide6.QtWidgets import QFileDialog
        
        # 1. Sélection du dossier
        dossier = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier d'enregistrement")
        
        if dossier:
            # 2. Appel du contrôleur via le parent (PatientView)
            # On utilise self.parent() pour atteindre le contrôleur de PatientView
            reussite, message = self.parent().controleur.generer_carnet_par_code(
                self.patient.get_code_patient(), 
                dossier
            )
            
            # 3. Appel DIRECT de CustomMessageBox (puisque c'est dans le même fichier)
            titre = "Succès" if reussite else "Erreur"
            msg_dialog = CustomMessageBox(
                title=titre, 
                message=message, 
                is_success=reussite, 
                parent=self
            )
            msg_dialog.exec()
            
            if reussite:
                self.accept() # On ferme la fiche détail si l'impression est lancée
