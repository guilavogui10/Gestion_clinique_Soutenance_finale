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

    # ── Alias courts (compatibilité avec les appels warning/success/confirm/info/error) ──

    @staticmethod
    def warning(parent, title, message):
        return CustomMessageBox.show_warning(message, title, parent=parent)

    @staticmethod
    def success(parent, title, message):
        return CustomMessageBox.show_success(message, title, parent=parent)

    @staticmethod
    def confirm(parent, title, message):
        return CustomMessageBox.show_question(message, title, parent=parent)

    @staticmethod
    def question(parent, title, message):
        return CustomMessageBox.show_question(message, title, parent=parent)

    @staticmethod
    def info(parent, title, message):
        return CustomMessageBox.show_info(message, title, parent=parent)

    @staticmethod
    def error(parent, title, message):
        return CustomMessageBox.show_error(message, title, parent=parent)



class PatientDetailDialog(QDialog):
    """
    Modal fiche patient — design identique à CustomMessageBox :
    frameless, overlay semi-transparent, frame blanc arrondi avec ombre.
    Couleur principale bleue (primary du thème).
    """

    def __init__(self, patient, parent=None):
        super().__init__(parent)
        self.patient = patient

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)

        self._build_ui()
        self._apply_shadow()
        self._apply_styles()

    # ------------------------------------------------------------------
    # Overlay semi-transparent (même technique que CustomMessageBox)
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

    # ------------------------------------------------------------------
    # Ombre portée sur le frame blanc
    # ------------------------------------------------------------------
    def _apply_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 110))
        self.frame.setGraphicsEffect(shadow)

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------
    def _build_ui(self):
        c = theme_manager.colors()
        primary = c['primary']

        outer = QVBoxLayout(self)
        outer.setContentsMargins(50, 50, 50, 50)
        outer.setAlignment(Qt.AlignCenter)

        # ── Frame blanc central ────────────────────────────────────────
        self.frame = QFrame()
        self.frame.setObjectName("PDetailFrame")
        self.frame.setFixedWidth(540)

        fl = QVBoxLayout(self.frame)
        fl.setContentsMargins(36, 28, 36, 32)
        fl.setSpacing(0)

        # ── Bouton ✕ (coin haut droit) ─────────────────────────────────
        top_row = QHBoxLayout()
        top_row.addStretch()
        self._btn_x = QPushButton("✕")
        self._btn_x.setObjectName("PDetailClose")
        self._btn_x.setFixedSize(30, 30)
        self._btn_x.setCursor(Qt.PointingHandCursor)
        self._btn_x.clicked.connect(self.reject)
        top_row.addWidget(self._btn_x)
        fl.addLayout(top_row)
        fl.addSpacing(4)

        # ── Avatar circulaire bleu ────────────────────────────────────
        avatar_frame = QFrame()
        avatar_frame.setObjectName("PDetailAvatar")
        avatar_frame.setFixedSize(76, 76)
        av_lay = QVBoxLayout(avatar_frame)
        av_lay.setContentsMargins(0, 0, 0, 0)
        av_lay.setAlignment(Qt.AlignCenter)
        lbl_av = QLabel()
        lbl_av.setAlignment(Qt.AlignCenter)
        lbl_av.setPixmap(qta.icon("fa5s.user", color="white").pixmap(34, 34))
        av_lay.addWidget(lbl_av)

        av_wrap = QHBoxLayout()
        av_wrap.addStretch()
        av_wrap.addWidget(avatar_frame)
        av_wrap.addStretch()
        fl.addLayout(av_wrap)
        fl.addSpacing(14)

        # ── Nom complet ───────────────────────────────────────────────
        nom = f"{self.patient.get_nom()} {self.patient.get_prenom()}"
        lbl_nom = QLabel(nom)
        lbl_nom.setObjectName("PDetailNom")
        lbl_nom.setAlignment(Qt.AlignCenter)
        lbl_nom.setWordWrap(True)
        fl.addWidget(lbl_nom)
        fl.addSpacing(6)

        # ── Badge code patient ────────────────────────────────────────
        badge_wrap = QHBoxLayout()
        badge_wrap.addStretch()
        lbl_badge = QLabel(f"  #{self.patient.get_code_patient()}  ")
        lbl_badge.setObjectName("PDetailBadge")
        lbl_badge.setAlignment(Qt.AlignCenter)
        badge_wrap.addWidget(lbl_badge)
        badge_wrap.addStretch()
        fl.addLayout(badge_wrap)
        fl.addSpacing(22)

        # ── Séparateur ────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("PDetailSep")
        fl.addWidget(sep)
        fl.addSpacing(20)

        # ── Cards d'information (grille 2 colonnes) ───────────────────
        infos_2col = [
            ("fa5s.phone-alt",     "Téléphone",      str(self.patient.get_telephone() or "—")),
            ("fa5s.venus-mars",    "Genre",           str(self.patient.get_genre()     or "—")),
            ("fa5s.birthday-cake", "Date naissance",  str(self.patient.get_naissance() or "—")),
            ("fa5s.briefcase",     "Profession",      str(self.patient.get_profession()or "—")),
        ]

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        for idx, (ico, lbl, val) in enumerate(infos_2col):
            card = self._make_card(ico, lbl, val)
            grid.addWidget(card, idx // 2, idx % 2)

        fl.addLayout(grid)
        fl.addSpacing(10)

        # Adresse pleine largeur
        fl.addWidget(self._make_card("fa5s.map-marker-alt", "Adresse",
                                     str(self.patient.get_adresse() or "—")))
        fl.addSpacing(28)

        # ── Boutons ───────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_fermer = QPushButton("  Fermer")
        btn_fermer.setObjectName("PDetailSecondary")
        btn_fermer.setFixedHeight(44)
        btn_fermer.setCursor(Qt.PointingHandCursor)
        btn_fermer.setIcon(qta.icon("fa5s.times", color=c['text_secondary']))
        btn_fermer.clicked.connect(self.reject)

        self.btn_print = QPushButton("  Imprimer le carnet")
        self.btn_print.setObjectName("PDetailPrimary")
        self.btn_print.setFixedHeight(44)
        self.btn_print.setCursor(Qt.PointingHandCursor)
        self.btn_print.setIcon(qta.icon("fa5s.print", color="white"))
        self.btn_print.clicked.connect(self.imprimer_carnet)

        btn_row.addWidget(btn_fermer, 1)
        btn_row.addWidget(self.btn_print, 2)
        fl.addLayout(btn_row)

        outer.addWidget(self.frame)

    # ------------------------------------------------------------------
    # Card info individuelle
    # ------------------------------------------------------------------
    def _make_card(self, icon_name: str, label: str, value: str) -> QFrame:
        c = theme_manager.colors()
        card = QFrame()
        card.setObjectName("PDetailCard")
        row = QHBoxLayout(card)
        row.setContentsMargins(14, 11, 14, 11)
        row.setSpacing(12)

        lbl_ic = QLabel()
        lbl_ic.setPixmap(qta.icon(icon_name, color=c['primary']).pixmap(16, 16))
        lbl_ic.setFixedSize(18, 18)
        row.addWidget(lbl_ic)

        col = QVBoxLayout()
        col.setSpacing(2)
        lbl_l = QLabel(label)
        lbl_l.setObjectName("PDetailCardLabel")
        lbl_v = QLabel(value)
        lbl_v.setObjectName("PDetailCardValue")
        lbl_v.setWordWrap(True)
        col.addWidget(lbl_l)
        col.addWidget(lbl_v)
        row.addLayout(col)
        return card

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------
    def _apply_styles(self):
        c = theme_manager.colors()

        self.frame.setStyleSheet(f"""
            QFrame#PDetailFrame {{
                background: {c['bg_card']};
                border-radius: 20px;
                border: none;
            }}
        """)

        self.setStyleSheet(f"""
            QPushButton#PDetailClose {{
                background: {c['bg_input']};
                border: none;
                border-radius: 15px;
                color: {c['text_muted']};
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton#PDetailClose:hover {{
                background: {c['hover']};
                color: {c['text_primary']};
            }}

            QFrame#PDetailAvatar {{
                background: {c['primary']};
                border-radius: 38px;
            }}

            QLabel#PDetailNom {{
                color: {c['text_primary']};
                font-size: 22px;
                font-weight: 700;
                background: transparent;
            }}

            QLabel#PDetailBadge {{
                background: {c['primary_light']};
                color: {c['primary']};
                font-size: 12px;
                font-weight: 600;
                border-radius: 10px;
                padding: 3px 0px;
            }}

            QFrame#PDetailSep {{
                color: {c['border_light']};
                max-height: 1px;
            }}

            QFrame#PDetailCard {{
                background: {c['bg_input']};
                border-radius: 10px;
                border: 1px solid {c['border_light']};
            }}
            QLabel#PDetailCardLabel {{
                color: {c['text_muted']};
                font-size: 10px;
                font-weight: 500;
                background: transparent;
            }}
            QLabel#PDetailCardValue {{
                color: {c['text_primary']};
                font-size: 13px;
                font-weight: 600;
                background: transparent;
            }}

            QPushButton#PDetailSecondary {{
                background: transparent;
                border: 2px solid {c['border']};
                border-radius: 12px;
                color: {c['text_secondary']};
                font-size: 13px;
                font-weight: 600;
                padding-left: 6px;
                text-align: left;
            }}
            QPushButton#PDetailSecondary:hover {{
                background: {c['hover']};
                border-color: {c['text_muted']};
                color: {c['text_primary']};
            }}

            QPushButton#PDetailPrimary {{
                background: {c['primary']};
                border: none;
                border-radius: 12px;
                color: {c['text_inverse']};
                font-size: 13px;
                font-weight: 700;
                padding-left: 6px;
                text-align: left;
            }}
            QPushButton#PDetailPrimary:hover {{
                background: {c['primary_hover']};
            }}
        """)

    # ------------------------------------------------------------------
    # Impression carnet
    # ------------------------------------------------------------------
    def imprimer_carnet(self):
        from PySide6.QtWidgets import QFileDialog

        dossier = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier d'enregistrement")
        if dossier:
            reussite, message = self.parent().controleur.generer_carnet_par_code(
                self.patient.get_code_patient(),
                dossier
            )
            titre = "Succès" if reussite else "Erreur"
            CustomMessageBox(title=titre, message=message, is_success=reussite, parent=self).exec()
            if reussite:
                self.accept()
