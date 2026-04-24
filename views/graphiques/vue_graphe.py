import sys
import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                             QLabel, QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt, QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import mplcursors
from views.shared.modal_theme import MC

class GrapheView(QWidget):
    def __init__(self):
        super().__init__()
        # Palette de couleurs moderne (depuis le thème actif)
        self.colors = {
            "bg": MC.BG_MAIN,
            "card": MC.BG_CARD,
            "text": MC.TEXT_PRIMARY,
            "subtext": MC.TEXT_MUTED,
            "accent_list": [MC.INFO, MC.ACCENT, MC.WARNING, MC.SUCCESS, MC.DANGER]
        }
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {self.colors['bg']};")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- 1. BARRE DES KPIs (Cartes du haut) ---
        kpi_layout = QHBoxLayout()
        self.kpi_widgets = {}
        kpis = [
            ("TOTAL PATIENTS", "38BDF8"),
            ("TOTAL EXAMENS", "818CF8"),
            ("TOTAL CHIRURGIE", "FB923C"),
            ("TOTAL CONSULTATION", "F472B6")
        ]

        for title, color in kpis:
            card = self.create_kpi_card(title, color)
            kpi_layout.addWidget(card)
            self.kpi_widgets[title] = card

        main_layout.addLayout(kpi_layout)

        # --- 2. GRILLE DES GRAPHIQUES ---
        charts_grid = QGridLayout()
        charts_grid.setSpacing(15)

        # Ajout des différents graphiques
        charts_grid.addWidget(self.create_chart_card("Évolution Consultations", "line"), 0, 0, 1, 2)
        charts_grid.addWidget(self.create_chart_card("Répartition Examens", "pie"), 0, 2, 1, 1)
        charts_grid.addWidget(self.create_chart_card("Tranches d'âges", "bar"), 1, 0, 1, 1)
        charts_grid.addWidget(self.create_chart_card("Types de Chirurgies", "barh"), 1, 1, 1, 2)

        main_layout.addLayout(charts_grid)

        # Timer pour l'animation des données (comme dans ton code original)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_random_stats)
        self.timer.start(5000)

    def create_kpi_card(self, title, accent_color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['card']};
                border-radius: 12px;
                border: 1px solid #334155;
            }}
        """)
        card.setMinimumHeight(100)
        
        layout = QVBoxLayout(card)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {self.colors['subtext']}; font-weight: bold; font-size: 11px;")
        
        lbl_value = QLabel(str(random.randint(100, 999)))
        lbl_value.setObjectName("value")
        lbl_value.setStyleSheet(f"color: #{accent_color}; font-size: 28px; font-weight: bold; background: transparent; border: none;")
        
        layout.addWidget(lbl_title, alignment=Qt.AlignCenter)
        layout.addWidget(lbl_value, alignment=Qt.AlignCenter)
        return card

    def create_chart_card(self, title, chart_type):
        container = QFrame()
        container.setStyleSheet(f"background-color: {self.colors['card']}; border-radius: 15px;")
        layout = QVBoxLayout(container)

        # Création de la figure Matplotlib
        fig = Figure(figsize=(5, 4), dpi=100, facecolor=self.colors['card'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.colors['card'])
        ax.set_title(title, color=self.colors['text'], fontsize=10, pad=10)
        
        # Style des axes
        ax.tick_params(colors=self.colors['subtext'], labelsize=7)
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Génération des données statiques pour le moment
        self.plot_data(ax, chart_type)

        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        
        # Ajout de l'interactivité avec mplcursors
        cursor = mplcursors.cursor(ax.containers if chart_type != "line" else ax.get_lines(), hover=True)
        
        return container

    def plot_data(self, ax, chart_type):
        color = random.choice(self.colors['accent_list'])
        if chart_type == "line":
            ax.plot(range(12), [random.randint(10, 50) for _ in range(12)], color=color, marker='o', linewidth=2)
        elif chart_type == "bar":
            ax.bar(["-18", "18-45", "45+"], [30, 55, 40], color=color, alpha=0.7)
        elif chart_type == "pie":
            ax.pie([40, 30, 30], labels=["A", "B", "C"], colors=self.colors['accent_list'], 
                   textprops={'color':"w", 'fontsize':7}, wedgeprops={'width':0.5})
        elif chart_type == "barh":
            ax.barh(["Urgent", "Normal"], [20, 80], color=color)

    def update_random_stats(self):
        # Simulation de mise à jour dynamique des chiffres
        for card in self.kpi_widgets.values():
            val_label = card.findChild(QLabel, "value")
            if val_label:
                val_label.setText(str(random.randint(10, 500)))