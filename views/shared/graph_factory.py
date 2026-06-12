"""
Graphiques patients modernisés avec design élégant
"""
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
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
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(16)
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
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        gc = Styles.graph_colors()

        # Conteneur pour les deux graphiques côte à côte
        graphs_row = QHBoxLayout()
        graphs_row.setSpacing(16)

        # --- 1. GRAPHIQUE GENRE (Donut moderne) ---
        genre_card = self._create_card_container(
            "Répartition par Genre",
            "fa5s.venus-mars",
            self._create_modern_donut(stats, gc)
        )
        graphs_row.addWidget(genre_card, 1)

        # --- 2. GRAPHIQUE ÂGE (Barres modernes) ---
        age_card = self._create_card_container(
            "Répartition par Âge",
            "fa5s.users",
            self._create_modern_bars(stats, gc)
        )
        graphs_row.addWidget(age_card, 1)

        self.layout.addLayout(graphs_row)
        self.layout.addStretch()

    def _create_card_container(self, title, icon_name, chart_widget):
        """Crée un conteneur carte pour un graphique"""
        c = theme_manager.colors()
        
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(12)
        
        # Header avec icône et titre
        header = QHBoxLayout()
        header.setSpacing(8)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=c['primary']).pixmap(18, 18))
        icon_label.setStyleSheet("border: none; background: transparent;")
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 700;
            color: {c['text_primary']};
            background: transparent;
            border: none;
        """)
        
        header.addWidget(icon_label)
        header.addWidget(title_label)
        header.addStretch()
        
        card_layout.addLayout(header)
        card_layout.addWidget(chart_widget, 1)
        
        return card

    def _create_modern_donut(self, stats, gc):
        """Crée un graphique camembert propre pour le genre"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Légende en haut
        legend_container = QWidget()
        legend_layout = QHBoxLayout(legend_container)
        legend_layout.setContentsMargins(10, 0, 10, 0)
        legend_layout.setSpacing(25)
        legend_layout.setAlignment(Qt.AlignCenter)
        
        filles = int(stats.get('filles', 0))
        garcons = int(stats.get('garçons', 0))
        
        legend_layout.addWidget(self._create_compact_legend("Femmes", filles, '#FF6B9D', 'fa5s.venus'))
        legend_layout.addWidget(self._create_compact_legend("Hommes", garcons, '#4A90E2', 'fa5s.mars'))
        
        layout.addWidget(legend_container)
        
        # Graphique camembert
        bg = gc['bg']
        text_color = gc['text']
        fig, ax = plt.subplots(figsize=(6, 5), facecolor=bg)
        
        tailles = [filles, garcons]
        labels = ['Femmes', 'Hommes']
        total = sum(tailles)
        
        if total > 0:
            colors = ['#FF6B9D', '#4A90E2']
            explode = (0.05, 0.05)
            
            wedges, texts, autotexts = ax.pie(
                tailles,
                labels=None,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                explode=explode,
                textprops={'size': 9, 'weight': 'bold'},
                wedgeprops={'linewidth': 0, 'edgecolor': 'none'}
            )
            
            # Style des pourcentages
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(9)
                autotext.set_weight('bold')
        else:
            ax.text(0, 0, "Aucune\ndonnée", ha='center', va='center',
                    fontweight='bold', size=12, color=gc['text_muted'])
        
        ax.set_facecolor(bg)
        ax.axis('equal')
        fig.tight_layout()
        
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas, 1)
        
        return container

    def _create_modern_bars(self, stats, gc):
        """Crée un graphique en barres verticales propre pour l'âge"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Légende compacte en haut
        legend_container = QWidget()
        legend_layout = QHBoxLayout(legend_container)
        legend_layout.setContentsMargins(10, 0, 10, 0)
        legend_layout.setSpacing(20)
        legend_layout.setAlignment(Qt.AlignCenter)
        
        enfants = int(stats.get('enfants', 0))
        jeunes = int(stats.get('jeunes', 0))
        adultes = int(stats.get('adultes', 0))
        
        legend_layout.addWidget(self._create_compact_legend("Enfants (0-12)", enfants, '#FF9800', 'fa5s.baby'))
        legend_layout.addWidget(self._create_compact_legend("Jeunes (13-25)", jeunes, '#4CAF50', 'fa5s.child'))
        legend_layout.addWidget(self._create_compact_legend("Adultes (26+)", adultes, '#9C27B0', 'fa5s.user'))
        
        layout.addWidget(legend_container)
        
        # Graphique barres
        bg = gc['bg']
        text_color = gc['text']
        fig, ax = plt.subplots(figsize=(5, 4), facecolor=bg)
        
        categories = ['Enfants', 'Jeunes', 'Adultes']
        valeurs = [enfants, jeunes, adultes]
        colors = ['#FF9800', '#4CAF50', '#9C27B0']
        
        max_val = max(valeurs) if max(valeurs) > 0 else 10
        x = range(len(categories))
        
        # Barres verticales plus fines et allongées
        bars = ax.bar(x, valeurs, width=0.35, color=colors,
                     edgecolor='none', alpha=0.8)
        
        # Valeurs au-dessus des barres
        for bar, value in zip(bars, valeurs):
            if value > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max_val * 0.02,
                    str(int(value)),
                    ha='center', va='bottom',
                    fontsize=9, fontweight='600',
                    color=text_color
                )
        
        # Configuration - barres prennent plus de place
        ax.set_xticks(x)
        ax.set_xticklabels([])
        ax.set_xlim(-0.5, len(categories) - 0.5)
        ax.set_ylim(0, max_val * 1.2)
        ax.set_facecolor(bg)
        
        # Grille
        ax.grid(True, axis='y', linestyle='-', alpha=0.1, linewidth=0.8)
        ax.set_axisbelow(True)
        
        # Axes
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        ax.tick_params(colors=text_color, labelsize=9, length=0, pad=8)
        
        ax.set_ylabel('Nombre de patients', color=text_color,
                     fontsize=10, fontweight='500')
        
        fig.tight_layout()
        
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas, 1)
        
        return container

    def _create_compact_legend(self, label, value, color, icon_name):
        """Crée un élément de légende compact"""
        c = theme_manager.colors()
        
        item = QWidget()
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # Icône
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=color).pixmap(14, 14))
        
        # Texte
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            font-size: 9px;
            font-weight: 600;
            color: {c['text_secondary']};
        """)
        
        value_widget = QLabel(str(value))
        value_widget.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 700;
            color: {color};
        """)
        
        text_layout.addWidget(label_widget)
        text_layout.addWidget(value_widget)
        
        layout.addWidget(icon_label)
        layout.addLayout(text_layout)
        
        return item

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self._clear_layout(item.layout())
