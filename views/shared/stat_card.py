from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtCore import Qt
import qtawesome as qta
from views.shared.theme_manager import theme_manager
from views.shared.styles import Styles


class StatCard(QFrame):
    def __init__(self, title, value, icon_name, accent_color):
        super().__init__()
        self.setObjectName("StatCard")
        self._icon_name = icon_name
        self._accent_color = accent_color
        self.setFixedSize(250, 120)

        layout = QVBoxLayout(self)

        # Conteneur Haut (Icône à gauche)
        top_layout = QHBoxLayout()
        
        # Icône encerclée
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(45, 45)
        
        top_layout.addWidget(self.icon_label)
        top_layout.addStretch()
        
        self.lbl_title = QLabel(title)        
        self.lbl_value = QLabel(value)

        layout.addLayout(top_layout)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)

        # Appliquer le thème initial et écouter
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)

    def apply_theme(self):
        c = theme_manager.colors()
        accent = self._accent_color
        # Card frame style
        self.setStyleSheet(Styles.stat_card_style(accent))
        # Icon
        self.icon_label.setPixmap(
            qta.icon(self._icon_name, color=c['text_inverse']).pixmap(25, 25)
        )
        self.icon_label.setStyleSheet(
            f"background-color: {accent}; border-radius: 22px;"
        )
        # Title
        self.lbl_title.setStyleSheet(
            f"color: {c['text_secondary']}; font-size: 14px; font-weight: 500;"
        )
        # Value
        self.lbl_value.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 22px; font-weight: bold;"
        )