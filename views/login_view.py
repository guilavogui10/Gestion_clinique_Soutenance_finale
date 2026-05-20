import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPixmap,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# ─────────────────────────────────────────────
#  Helper : icône qtawesome remplie d'un dégradé
# ─────────────────────────────────────────────
def _gradient_icon_pixmap(
    icon_name: str,
    size: int,
    color_top: QColor,
    color_bottom: QColor,
) -> QPixmap:
    """
    Rend l'icône en blanc puis applique un dégradé via CompositionMode_SourceIn.
    """
    base = qta.icon(icon_name, color="white").pixmap(size, size)

    out = QPixmap(size, size)
    out.fill(Qt.transparent)

    p = QPainter(out)
    p.setRenderHint(QPainter.Antialiasing)

    # 1) copie la forme (alpha) de l'icône
    p.setCompositionMode(QPainter.CompositionMode_Source)
    p.drawPixmap(0, 0, base)

    # 2) remplace la couleur par le dégradé, en conservant l'alpha
    grad = QLinearGradient(0, 0, 0, size)          # vertical : haut → bas
    grad.setColorAt(0.0, color_top)
    grad.setColorAt(1.0, color_bottom)
    p.setCompositionMode(QPainter.CompositionMode_SourceIn)
    p.fillRect(0, 0, size, size, grad)

    p.end()
    return out


# ─────────────────────────────────────────────
#  Panneau GAUCHE  –  fond turquoise + grand œil
# ─────────────────────────────────────────────
class LeftPanel(QFrame):
    """
    Panneau transparent (montre le fond du conteneur principal).
    Peint un grand œil dégradé semi-transparent en arrière-plan.
    """

    EYE_SIZE = 270  # px  –  bien agrandi

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background: transparent; border: none; }")

        # Dégradé : cyan clair en haut, turquoise plus soutenu en bas
        self._eye_bg = _gradient_icon_pixmap(
            "fa5s.eye",
            self.EYE_SIZE,
            QColor(160, 255, 235, 230),   # haut  – cyan lumineux
            QColor(20,  190, 160, 200),   # bas   – turquoise soutenu
        )

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        s = self.EYE_SIZE

        # Centré dans le panneau gauche, légèrement décalé vers le bas
        x = (w - s) // 2
        y = (h - s) // 2 + 10

        painter.setOpacity(0.22)          # filigrane discret mais visible
        painter.drawPixmap(x, y, s, s, self._eye_bg)


# ─────────────────────────────────────────────
#  Panneau DROIT  –  fond blanc avec courbe en S
# ─────────────────────────────────────────────
class WaveRightPanel(QFrame):
    """
    Panneau blanc dont le bord gauche est une courbe en S.
    Le ventre central est volontairement peu creusé (x0 ± 20 px max)
    pour éviter l'effet trop « rentré » signalé.
    """

    WAVE_X0 = 58    # position nominale de la séparation (px depuis le bord gauche du widget)
    RADIUS   = 25   # rayon des coins arrondis (côté droit, doit correspondre au conteneur)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(445)
        self.setStyleSheet("QFrame { background: transparent; border: none; }")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        x0   = self.WAVE_X0
        r    = self.RADIUS

        path = QPainterPath()
        path.moveTo(x0, 0)

        # ── Demi-S supérieure ──────────────────────────────────────────
        # • CP1 : tire vers la gauche  (creux supérieur)
        # • CP2 : pousse vers la droite, mais peu (ventre central modéré)
        # • Point milieu : reste proche de x0, pas trop à droite
        path.cubicTo(
            x0 - 30, h * 0.12,    # CP1 – creux à gauche
            x0 + 20, h * 0.36,    # CP2 – léger renflement droit
            x0 +  8, h * 0.50,    # milieu : +8 px seulement (pas « rentré »)
        )

        # ── Demi-S inférieure ─────────────────────────────────────────
        # Miroir de la demi-S supérieure
        path.cubicTo(
            x0 -  5, h * 0.64,    # CP3 – retour vers gauche
            x0 - 30, h * 0.88,    # CP4 – creux à gauche (symétrique)
            x0,      h,           # bas  – retour à x0
        )

        # ── Côté droit avec coins arrondis ───────────────────────────
        path.lineTo(w - r, h)
        path.quadTo(w, h, w, h - r)
        path.lineTo(w, r)
        path.quadTo(w, 0, w - r, 0)
        path.closeSubpath()

        painter.fillPath(path, QColor("white"))


# ─────────────────────────────────────────────
#  Vue principale
# ─────────────────────────────────────────────
class LoginView(QWidget):
    login_success = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Charger l'image de fond
        self.background_image = QPixmap("assets/images/fond.png")
        self._build_ui()
    
    def paintEvent(self, event):
        """Dessine l'image de fond sur toute la fenêtre."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.background_image.isNull():
            # Redimensionner l'image pour couvrir toute la fenêtre
            scaled_pixmap = self.background_image.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            # Centrer l'image
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            # Fond gris par défaut si l'image n'est pas trouvée
            painter.fillRect(self.rect(), QColor("#E5E7EB"))
        
        painter.end()

    # ── Construction de l'interface ──────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignCenter)

        # Conteneur principal : turquoise foncé, coins arrondis
        main_container = QFrame()
        main_container.setFixedSize(750, 560)
        main_container.setStyleSheet(
            "QFrame { background-color: #0d5f5a; border-radius: 25px; }"
        )

        shadow = QGraphicsDropShadowEffect(blurRadius=60, xOffset=0, yOffset=20)
        shadow.setColor(QColor(0, 0, 0, 110))
        main_container.setGraphicsEffect(shadow)

        layout = QHBoxLayout(main_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_left_panel(),  stretch=1)
        layout.addWidget(self._build_right_panel(), stretch=0)

        # Ajouter le conteneur avec un alignement à droite
        container_layout = QHBoxLayout()
        container_layout.addStretch(1)  # Espace à gauche
        container_layout.addWidget(main_container)
        container_layout.addSpacing(50)  # Marge à droite
        
        root.addLayout(container_layout)

    # ── Panneau gauche ───────────────────────────────────────────────
    def _build_left_panel(self) -> QWidget:
        panel = LeftPanel()

        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.setAlignment(Qt.AlignCenter)

        # Icône œil au premier plan (devant le fond dégradé)
        eye_fg = QLabel()
        eye_fg.setAlignment(Qt.AlignCenter)
        eye_fg.setPixmap(qta.icon("fa5s.eye", color="white").pixmap(110, 110))
        eye_fg.setStyleSheet("background: transparent; border: none;")
        vbox.addWidget(eye_fg)

        return panel

    # ── Panneau droit ────────────────────────────────────────────────
    def _build_right_panel(self) -> QWidget:
        panel = WaveRightPanel()

        x0   = WaveRightPanel.WAVE_X0
        vbox = QVBoxLayout(panel)
        # Marge gauche = position de la vague + respiration
        vbox.setContentsMargins(x0 + 22, 25, 38, 25)  # Marges haut/bas réduites (38/30 -> 25/25)
        vbox.setSpacing(0)

        # Titre
        title = QLabel("Welcome")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 30px; font-weight: 600; color: #2C3E50;"
            "border: none; background: transparent;"
        )
        vbox.addWidget(title)
        vbox.addSpacing(6)

        subtitle = QLabel("Log in to your account to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            "font-size: 12px; color: #95A5A6; border: none; background: transparent;"
        )
        vbox.addWidget(subtitle)
        vbox.addSpacing(28)

        # Champ e-mail
        ef = self._build_input_field("fa5s.user", "awesome@user.com")
        self.input_login = ef["input"]
        vbox.addWidget(ef["frame"])
        vbox.addSpacing(14)

        # Champ mot de passe
        pf = self._build_input_field("fa5s.lock", "············", is_password=True)
        self.input_password = pf["input"]
        self.btn_show_pass  = pf["toggle"]
        self.input_password.returnPressed.connect(self.handle_login)
        vbox.addWidget(pf["frame"])
        vbox.addSpacing(8)

        # Mot de passe oublié
        forgot_row = QHBoxLayout()
        forgot_row.addStretch()
        btn_forgot = QPushButton("Forgot your password?")
        btn_forgot.setCursor(Qt.PointingHandCursor)
        btn_forgot.setStyleSheet(
            "QPushButton { border:none; background:transparent; color:#3D9B9B;"
            "font-size:11px; text-decoration:underline; }"
            "QPushButton:hover { color:#2D8282; }"
        )
        forgot_row.addWidget(btn_forgot)
        vbox.addLayout(forgot_row)
        vbox.addSpacing(18)

        # Bouton Log In
        self.btn_login = QPushButton("Log In")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setFixedHeight(44)
        self.btn_login.setFont(QFont("", 13, QFont.Weight.Medium))
        self.btn_login.setStyleSheet(
            "QPushButton { background-color:#3ECFCF; color:white; border:none;"
            "border-radius:22px; font-weight:600; }"
            "QPushButton:hover   { background-color:#35B8B8; }"
            "QPushButton:pressed { background-color:#2D9999; }"
        )
        self.btn_login.clicked.connect(self.handle_login)
        
        # Bouton Quitter
        self.btn_quit = QPushButton("Quitter")
        self.btn_quit.setCursor(Qt.PointingHandCursor)
        self.btn_quit.setFixedHeight(44)
        self.btn_quit.setFont(QFont("", 13, QFont.Weight.Medium))
        self.btn_quit.setStyleSheet(
            "QPushButton { background-color:#3ECFCF; color:white; border:none;"
            "border-radius:22px; font-weight:600; }"
            "QPushButton:hover   { background-color:#35B8B8; }"
            "QPushButton:pressed { background-color:#2D9999; }"
        )
        self.btn_quit.clicked.connect(self._quit_application)
        
        # Layout horizontal pour les deux boutons
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(12)
        buttons_row.addWidget(self.btn_login)
        buttons_row.addWidget(self.btn_quit)
        
        vbox.addLayout(buttons_row)
        vbox.addSpacing(18)

        # Sign up
        signup_row = QHBoxLayout()
        signup_row.setAlignment(Qt.AlignCenter)
        lbl = QLabel("Don't have an account?")
        lbl.setStyleSheet(
            "font-size:11px; color:#7F8C8D; border:none; background:transparent;"
        )
        signup_row.addWidget(lbl)
        btn_signup = QPushButton("Sign up!")
        btn_signup.setCursor(Qt.PointingHandCursor)
        btn_signup.setStyleSheet(
            "QPushButton { border:none; background:transparent; color:#3D9B9B;"
            "font-size:11px; font-weight:600; }"
            "QPushButton:hover { color:#2D8282; }"
        )
        signup_row.addWidget(btn_signup)
        vbox.addLayout(signup_row)
        vbox.addSpacing(14)

        # Réseaux sociaux
        social_row = QHBoxLayout()
        social_row.setAlignment(Qt.AlignCenter)
        social_row.setSpacing(14)
        for icon_name in ("fa5b.facebook", "fa5b.twitter", "fa5b.linkedin"):
            btn = QPushButton()
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(34, 34)
            btn.setIcon(qta.icon(icon_name, color="#95A5A6"))
            btn.setIconSize(qta.icon(icon_name).pixmap(20, 20).size())
            btn.setStyleSheet(
                "QPushButton { border:none; background:transparent; }"
                "QPushButton:hover { background-color:#ECF0F1; border-radius:17px; }"
            )
            social_row.addWidget(btn)
        vbox.addLayout(social_row)

        return panel

    # ── Champ de saisie ──────────────────────────────────────────────
    def _build_input_field(self, icon_name: str, placeholder: str, is_password=False):
        frame = QFrame()
        frame.setFixedHeight(48)
        frame.setStyleSheet(
            "QFrame { background-color:#F8F9FA; border:1px solid #E9ECEF; border-radius:8px; }"
        )
        row = QHBoxLayout(frame)
        row.setContentsMargins(14, 0, 14, 0)
        row.setSpacing(10)

        ico = QLabel()
        ico.setPixmap(qta.icon(icon_name, color="#95A5A6").pixmap(17, 17))
        ico.setStyleSheet("border:none; background:transparent;")
        row.addWidget(ico)

        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFrame(False)
        inp.setStyleSheet(
            "QLineEdit { border:none; background:transparent; color:#2C3E50; font-size:13px;"
            "selection-background-color:#3ECFCF; }"
            "QLineEdit::placeholder { color:#BDC3C7; }"
        )
        if is_password:
            inp.setEchoMode(QLineEdit.Password)
        row.addWidget(inp, 1)

        toggle = None
        if is_password:
            toggle = QPushButton()
            toggle.setCursor(Qt.PointingHandCursor)
            toggle.setIcon(qta.icon("fa5s.eye", color="#95A5A6"))
            toggle.setStyleSheet("border:none; background:transparent;")
            toggle.clicked.connect(self._toggle_password)
            row.addWidget(toggle)

        return {"frame": frame, "input": inp, "toggle": toggle}

    # ── Logique ──────────────────────────────────────────────────────
    def _toggle_password(self):
        if self.input_password.echoMode() == QLineEdit.Password:
            self.input_password.setEchoMode(QLineEdit.Normal)
            self.btn_show_pass.setIcon(qta.icon("fa5s.eye-slash", color="#3D9B9B"))
        else:
            self.input_password.setEchoMode(QLineEdit.Password)
            self.btn_show_pass.setIcon(qta.icon("fa5s.eye", color="#95A5A6"))

    def handle_login(self):
        login = self.input_login.text().strip()
        pwd   = self.input_password.text()
        self.login_success.emit({"login": login, "pwd": pwd})
    
    def _quit_application(self):
        """Ferme l'application après confirmation et arrête les services."""
        from views.shared.message_box import CustomMessageBox
        
        reponse = CustomMessageBox.confirm(
            self,
            "Confirmation de fermeture",
            "Voulez-vous vraiment quitter l'application ?\n\nLes services Vault et MinIO seront arrêtés."
        )
        
        if reponse:
            # Arrêter les services Vault et MinIO
            self._stop_services()
            
            # Fermer l'application
            from PySide6.QtWidgets import QApplication
            QApplication.quit()
    
    def _stop_services(self):
        """Arrête les services Vault et MinIO via les gestionnaires Python."""
        try:
            from core.vault_manager import get_vault_manager
            from core.minio_manager import get_minio_manager
            
            print("[LoginView] Arrêt des services Vault et MinIO...")
            
            # Arrêter MinIO
            try:
                minio_manager = get_minio_manager()
                minio_manager.arreter_minio()
            except Exception as e:
                print(f"[LoginView] Erreur lors de l'arrêt de MinIO : {e}")
            
            # Arrêter Vault
            try:
                vault_manager = get_vault_manager()
                vault_manager.arreter_vault()
            except Exception as e:
                print(f"[LoginView] Erreur lors de l'arrêt de Vault : {e}")
            
            print("[LoginView] Services arrêtés avec succès")
        except Exception as e:
            print(f"[LoginView] Erreur lors de l'arrêt des services : {e}")