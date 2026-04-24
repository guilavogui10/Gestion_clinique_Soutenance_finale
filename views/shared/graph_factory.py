import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import FancyBboxPatch
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
import qtawesome as qta
from views.shared.theme_manager import theme_manager
from views.shared.styles import Styles

class PatientGraphs(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_stats = None
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(0)
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        theme_manager.theme_changed.connect(self._on_theme_change)

    def _on_theme_change(self):
        if self._last_stats is not None:
            self.update_charts(self._last_stats)

    def update_charts(self, stats):
        self._last_stats = stats
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): self._clear_layout(item.layout())

        gc = Styles.graph_colors()

        # --- 1. SECTION GENRE (Horizontal) ---
        genre_widget = QWidget()
        genre_hbox = QHBoxLayout(genre_widget)
        genre_hbox.setContentsMargins(0, 0, 0, 0)
        
        # Donut à gauche (60%)
        genre_hbox.addWidget(self._create_genre_donut(stats, gc), 6)
        
        # Légende à droite (40%)
        genre_legende = QVBoxLayout()
        genre_legende.setAlignment(Qt.AlignCenter)
        genre_legende.setSpacing(8)
        genre_legende.addWidget(self._create_legend_item("fa5s.venus", "Filles", gc['series'][0]))
        genre_legende.addWidget(self._create_legend_item("fa5s.mars", "Garçons", gc['series'][1]))
        genre_hbox.addLayout(genre_legende, 4)
        
        self.layout.addWidget(genre_widget)

        # --- 2. SECTION ÂGE (Horizontal) ---
        age_widget = QWidget()
        age_hbox = QHBoxLayout(age_widget)
        age_hbox.setContentsMargins(0, 0, 0, 0)

        # Histogramme à gauche (60%)
        age_hbox.addWidget(self._create_age_bars(stats, gc), 6)

        # Légende Âge à droite (40%)
        age_legende = QVBoxLayout()
        age_legende.setAlignment(Qt.AlignCenter)
        age_legende.setSpacing(8)
        age_legende.addWidget(self._create_legend_item("fa5s.baby", "Enfants", gc['series'][2]))
        age_legende.addWidget(self._create_legend_item("fa5s.child", "Jeunes", gc['series'][1]))
        age_legende.addWidget(self._create_legend_item("fa5s.user", "Adultes", gc['series'][3]))
        age_hbox.addLayout(age_legende, 4)

        self.layout.addWidget(age_widget)
        self.layout.addStretch()

    def _create_legend_item(self, icon_name, text, color):
        item = QWidget()
        # Cette ligne enlève TOUT cadre ou ligne autour de l'élément de légende
        item.setStyleSheet("background: transparent; border: none;") 
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=color).pixmap(14, 14))
        icon_label.setStyleSheet("border: none;") # Sécurité supplémentaire
        
        text_label = QLabel(text)
        # On s'assure que le texte n'a pas de bordure non plus
        text_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 10px; border: none;")
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addStretch()
        return item

    def _create_genre_donut(self, stats, gc):
        bg = gc['bg']
        text_color = gc['text']
        fig, ax = plt.subplots(figsize=(2, 1.8), facecolor=bg)
        filles, garcons = int(stats.get('filles', 0)), int(stats.get('garçons', 0))
        tailles = [filles, garcons]
        total = sum(tailles)

        if total > 0:
            ax.pie(tailles, autopct='%1.0f%%', startangle=90,
                   colors=[gc['series'][0], gc['series'][1]],
                   pctdistance=0.75, wedgeprops={'width': 0.4, 'edgecolor': bg}, 
                   textprops={'color': text_color, 'weight':'bold', 'size':8}, radius=1.2)
            ax.text(0, 0, f"{total}\nTotal", ha='center', va='center',
                    fontweight='bold', size=9, color=text_color)
        
        ax.set_title("Repartition statistique par Genre", fontsize=9,
                     fontweight='bold', color=gc['title'], pad=5)
        ax.set_facecolor(bg)
        ax.axis('off')
        fig.subplots_adjust(0, 0, 1, 0.9)
        return FigureCanvas(fig)

    def _create_age_bars(self, stats, gc):
        bg = gc['bg']
        fig, ax = plt.subplots(figsize=(2.2, 2.0), facecolor=bg)
        valeurs = [int(stats.get('enfants', 0)), int(stats.get('jeunes', 0)), int(stats.get('adultes', 0))]
        couleurs = [gc['series'][2], gc['series'][1], gc['series'][3]]
        
        max_val = max(valeurs) if max(valeurs) > 0 else 5
        width = 0.6

        for i, val in enumerate(valeurs):
            val_visuelle = max(val, max_val * 0.12) if val > 0 else 0 
            if val_visuelle > 0:
                p = FancyBboxPatch((i - width/2, 0), width, val_visuelle,
                                boxstyle=f"round,pad=0,rounding_size={width/2}",
                                ec="none", fc=couleurs[i], mutation_scale=1, zorder=3)
                ax.add_patch(p)
            
            ax.text(i, val_visuelle + (max_val * 0.05), str(val), 
                    ha='center', fontweight='bold', color=couleurs[i], size=10)

        ax.set_xlim(-0.8, 2.8)
        ax.set_ylim(0, max_val * 1.4)
        ax.set_title("Repartition statistique par AGE", fontsize=9,
                     fontweight='bold', color=gc['title'], pad=10)
        ax.set_facecolor(bg)
        ax.axis('off')
        fig.subplots_adjust(left=0.1, right=0.9, bottom=0.05, top=0.85)
        return FigureCanvas(fig)

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
                elif item.layout(): self._clear_layout(item.layout())