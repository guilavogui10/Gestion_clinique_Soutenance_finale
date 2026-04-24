from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QPoint, QEasingCurve
from PySide6.QtGui import QColor
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class StatCard(QFrame):
    def __init__(self, title, value, icon_name, color_key, parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setFixedHeight(110)
        self._icon_name = icon_name
        self._color_key = color_key

        # Ombre
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(15)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(self._shadow)

        # Animation
        self._ani = QPropertyAnimation(self, b"pos")
        self._ani.setDuration(150)
        self._ani.setEasingCurve(QEasingCurve.OutCubic)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        # Icône encerclée
        top_layout = QHBoxLayout()
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(42, 42)
        top_layout.addWidget(self.icon_label)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Valeur
        self.lbl_value = QLabel(str(value))
        self.lbl_value.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_value)

        # Titre
        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_title)

        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def apply_theme(self):
        c = theme_manager.colors()
        accent = c.get(self._color_key, c['primary'])

        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background-color: {c['bg_card']};
                border-radius: 20px;
                border: 1px solid {c['border']};
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        self.icon_label.setPixmap(
            qta.icon(self._icon_name, color=c['text_inverse']).pixmap(QSize(22, 22))
        )
        self.icon_label.setStyleSheet(
            f"background-color: {accent}; border-radius: 21px; border: none;"
        )
        self.lbl_value.setStyleSheet(
            f"color: {c['text_primary']}; font-size: 24px; font-weight: bold;"
        )
        self.lbl_title.setStyleSheet(
            f"color: {c['text_secondary']}; font-size: 11px; font-weight: 500;"
        )

    def enterEvent(self, event):
        self._ani.setStartValue(self.pos())
        self._ani.setEndValue(QPoint(self.pos().x(), self.pos().y() - 5))
        self._shadow.setBlurRadius(25)
        self._ani.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._ani.setStartValue(self.pos())
        self._ani.setEndValue(QPoint(self.pos().x(), self.pos().y() + 5))
        self._shadow.setBlurRadius(15)
        self._ani.start()
        super().leaveEvent(event)

    def set_value(self, value):
        self.lbl_value.setText(str(value))


class StatsConsultationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(130)  # ← espace garanti entre cards et frames du bas
        self.init_ui()

    def init_ui(self):
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(16)  # ← espacement égal entre les cards

        self.card_jour = StatCard(
            title="Consultations du Jour",
            value="0",
            icon_name="fa5s.calendar-day",
            color_key="primary"
        )
        self.card_session = StatCard(
            title="Session en Cours",
            value="—",
            icon_name="fa5s.clock",
            color_key="success"
        )
        self.card_attente = StatCard(
            title="Patients en Attente",
            value="0",
            icon_name="fa5s.user-clock",
            color_key="warning"
        )

        # Supprime setFixedSize dans StatCard et utilise setMinimumHeight
        outer_layout.addWidget(self.card_jour)
        outer_layout.addWidget(self.card_session)
        outer_layout.addWidget(self.card_attente)

    def mettre_a_jour(self, nb_jour, code_session, nb_attente):
        self.card_jour.set_value(nb_jour)
        self.card_session.set_value(code_session)
        self.card_attente.set_value(nb_attente)