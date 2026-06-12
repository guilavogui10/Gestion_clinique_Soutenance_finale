from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QBrush
import qtawesome as qta

from views.shared.theme_manager import theme_manager


class PatientPipelineWidget(QWidget):
    """
    Widget personnalisé très léger utilisant QPainter pour dessiner
    la barre de progression (pipeline) d'un patient.
    Remplace la création massive de widgets pour améliorer drastiquement
    les performances de l'interface.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stages_meta = []
        self.blink_state = True
        self.setFixedHeight(36)

        self.icon_cache = {}
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self):
        self.icon_cache.clear()
        self.update()

    def set_data(self, stages_meta):
        """
        stages_meta: list of tuples (state, dur_text, key)
        state in ['done', 'current', 'future']
        """
        self.stages_meta = stages_meta
        self.update()

    def set_blink_state(self, state: bool):
        if self.blink_state != state:
            self.blink_state = state
            self.update()

    def paintEvent(self, event):
        if not self.stages_meta:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        n = len(self.stages_meta)
        if n == 0:
            return

        width = self.width()

        circle_size = 20
        radius = circle_size / 2

        margin_x = 12
        available_w = width - 2 * margin_x
        step_x = available_w / max(1, n - 1) if n > 1 else 0

        y_text = 10
        y_circle_center = 24

        # Couleurs lues depuis le thème actif
        c = theme_manager.colors()
        color_done           = QColor(c['success'])
        color_current_wait   = QColor(c['warning'])
        color_current_wait_off = QColor(c['warning_bg'])
        color_current_act    = QColor(c['info'])
        color_current_act_off = QColor(c['primary_light'])
        color_future         = QColor(c['bg_main'])
        color_line_done      = QColor(c['success'])
        color_line_future    = QColor(c['border'])
        icon_color_future    = c['text_muted']

        # 1. Dessiner les lignes de connexion (en arrière-plan)
        pen_line = QPen()
        pen_line.setWidth(2)
        for i in range(n - 1):
            state, _, _ = self.stages_meta[i]
            x1 = margin_x + i * step_x
            x2 = margin_x + (i + 1) * step_x

            if state == 'done':
                pen_line.setColor(color_line_done)
            else:
                pen_line.setColor(color_line_future)

            painter.setPen(pen_line)
            painter.drawLine(int(x1 + radius), int(y_circle_center), int(x2 - radius), int(y_circle_center))

        # 2. Dessiner les noeuds et les textes
        font = QFont()
        font.setPixelSize(9)
        font.setBold(True)
        painter.setFont(font)
        fm = QFontMetrics(font)

        for i in range(n):
            state, dur, key = self.stages_meta[i]
            x_center = margin_x + i * step_x

            is_waiting = key.lower().startswith("attente")

            # A) Texte de durée au-dessus du rond courant
            if state == 'current' and dur:
                painter.setPen(color_current_wait if is_waiting else color_current_act)
                tw = fm.horizontalAdvance(str(dur))
                painter.drawText(int(x_center - tw/2), int(y_text), str(dur))

            # B) Fond du cercle
            circle_rect = QRectF(x_center - radius, y_circle_center - radius, circle_size, circle_size)

            icon_name = ""
            icon_color = c['text_inverse']
            icon_size = 10

            if state == 'done':
                painter.setBrush(QBrush(color_done))
                painter.setPen(Qt.NoPen)
                icon_name = "fa5s.check"
            elif state == 'current':
                if is_waiting:
                    painter.setBrush(QBrush(color_current_wait if self.blink_state else color_current_wait_off))
                    icon_name = "fa5s.clock"
                else:
                    painter.setBrush(QBrush(color_current_act if self.blink_state else color_current_act_off))
                    icon_name = "fa5s.play"
                    icon_size = 8
                painter.setPen(Qt.NoPen)
            else:  # future
                painter.setBrush(QBrush(color_future))
                painter.setPen(Qt.NoPen)
                icon_name = "fa5s.circle"
                icon_color = icon_color_future
                icon_size = 8

            painter.drawEllipse(circle_rect)

            # C) Icône FontAwesome à l'intérieur du cercle
            if icon_name:
                cache_key = f"{icon_name}_{icon_color}_{icon_size}"
                if cache_key not in self.icon_cache:
                    self.icon_cache[cache_key] = qta.icon(icon_name, color=icon_color).pixmap(icon_size, icon_size)

                pixmap = self.icon_cache[cache_key]
                px_x = int(x_center - pixmap.width() / 2)
                px_y = int(y_circle_center - pixmap.height() / 2)
                painter.drawPixmap(px_x, px_y, pixmap)
