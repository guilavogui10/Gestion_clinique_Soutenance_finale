"""
Section graphiques / charts — Vue Acte Médical.
Répartition par type et par statut.
"""
import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget, QProgressBar,
)
from views.shared.theme_manager import theme_manager


class _BarChart(QFrame):
    """Mini graphe en barres horizontales."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("BarChartCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("ChartTitle")
        layout.addWidget(self.title_lbl)

        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(8)
        layout.addLayout(self.rows_layout)
        self.bar_rows = []

    def set_data(self, data: list, color: str):
        """data = [(label, value), ...]"""
        # Clear
        for i in reversed(range(self.rows_layout.count())):
            w = self.rows_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self.bar_rows.clear()

        total = max(sum(v for _, v in data), 1)
        for label, value in data:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            lbl = QLabel(label)
            lbl.setFixedWidth(100)
            lbl.setObjectName("BarLabel")

            bar = QProgressBar()
            bar.setRange(0, total)
            bar.setValue(value)
            bar.setFixedHeight(16)
            bar.setTextVisible(False)
            c = theme_manager.colors()
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background: {c['bg_main']};
                    border-radius: 6px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background: {color};
                    border-radius: 6px;
                }}
            """)

            val_lbl = QLabel(str(value))
            val_lbl.setFixedWidth(30)
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val_lbl.setObjectName("BarValue")

            row_layout.addWidget(lbl)
            row_layout.addWidget(bar, 1)
            row_layout.addWidget(val_lbl)
            self.rows_layout.addWidget(row)

    def apply_theme(self):
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QFrame#BarChartCard {{
                background: transparent;
                border: none;
                border-radius: 16px;
            }}
            QLabel#ChartTitle {{
                font-size: 14px; font-weight: bold; color: {c['text_primary']};
                background: transparent;
            }}
            QLabel#BarLabel {{ 
                color: {c['text_secondary']}; 
                font-size: 12px;
                background: transparent;
            }}
            QLabel#BarValue {{ 
                color: {c['text_muted']}; 
                font-size: 12px;
                background: transparent;
            }}
        """)


class ChartsSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(12)

        self.chart_type   = _BarChart("Répartition par type d'acte")
        self.chart_statut = _BarChart("Répartition par statut")

        layout.addWidget(self.chart_type, 1)
        layout.addWidget(self.chart_statut, 1)

        theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme()

    def update_charts(self, stats_type: dict, stats_statut: dict):
        c = theme_manager.colors()
        self.chart_type.set_data(
            [(k, v) for k, v in stats_type.items()], c["primary"]
        )
        self.chart_statut.set_data(
            [(k, v) for k, v in stats_statut.items()], c["accent"]
        )

    def apply_theme(self):
        self.chart_type.apply_theme()
        self.chart_statut.apply_theme()
