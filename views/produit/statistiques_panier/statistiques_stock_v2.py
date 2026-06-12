"""
Widget de statistiques de stock avec graphiques et alertes
Basé sur l'image fournie avec 4 sections principales
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
import qtawesome as qta
from views.shared.theme_manager import theme_manager


class DonutChart(QChartView):
    """Graphique en donut personnalisé"""
    
    def __init__(self, title, data_dict, color_map, total_label="Total"):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        
        # Créer la série
        series = QPieSeries()
        series.setHoleSize(0.5)
        
        total = sum(data_dict.values())
        
        for label, value in data_dict.items():
            slice_obj = series.append(f"{label}\n{value}", value)
            slice_obj.setLabelVisible(True)
            slice_obj.setLabelPosition(QPieSlice.LabelOutside)
            
            # Appliquer la couleur
            if label in color_map:
                slice_obj.setBrush(QColor(color_map[label]))
        
        # Créer le chart
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(title)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundVisible(False)
        
        # Style du titre
        font = chart.titleFont()
        font.setPointSize(12)
        font.setBold(True)
        chart.setTitleFont(font)
        
        self.setChart(chart)
        self.setStyleSheet("background: transparent; border: none;")


class AlerteCard(QFrame):
    """Card d'alerte avec icône et texte"""
    
    def __init__(self, icon_name, text, count, color):
        super().__init__()
        self.setObjectName("AlerteCard")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        
        # Icône
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=color).pixmap(24, 24))
        layout.addWidget(icon_label)
        
        # Texte
        text_label = QLabel(f"{count} {text}")
        text_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 600;")
        layout.addWidget(text_label, 1)
        
        c = theme_manager.colors()
        self.setStyleSheet(f"""
            QFrame#AlerteCard {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
            }}
            QFrame#AlerteCard:hover {{
                border-color: {color};
                background: {c['hover']};
            }}
        """)


class StatistiquesStockV2Widget(QWidget):
    """Widget de statistiques de stock version 2"""
    
    def __init__(self, panier_ctrl=None):
        super().__init__()
        self.panier_ctrl = panier_ctrl
        self._init_ui()
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)
    
    def _init_ui(self):
        """Initialise l'interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        _bg = theme_manager.colors()['bg_card']
        scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {_bg}; }}"
            f"QScrollArea > QWidget {{ background: {_bg}; }}"
        )
        self._scroll_v2 = scroll

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(12)
        
        # Ligne 1: 2 graphiques donut
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        
        self.chart_expiration = self._create_chart_frame("Répartition par statut d'expiration")
        self.chart_type = self._create_chart_frame("Répartition par type de produit")
        
        row1.addWidget(self.chart_expiration)
        row1.addWidget(self.chart_type)
        container_layout.addLayout(row1)
        
        # Ligne 2: Alertes & Notifications + Stock détaillé
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        
        self.alertes_frame = self._create_alertes_frame()
        self.stock_frame = self._create_stock_detail_frame()
        
        row2.addWidget(self.alertes_frame, 1)
        row2.addWidget(self.stock_frame, 2)
        container_layout.addLayout(row2)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
    
    def _create_chart_frame(self, title):
        """Crée un frame pour un graphique"""
        frame = QFrame()
        frame.setObjectName("ChartFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Titre
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 13px; font-weight: 700; padding: 12px;")
        layout.addWidget(title_label)
        
        # Placeholder pour le chart
        chart_container = QWidget()
        chart_container.setObjectName("ChartContainer")
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(chart_container)
        
        return frame
    
    def _create_alertes_frame(self):
        """Crée le frame des alertes"""
        frame = QFrame()
        frame.setObjectName("AlertesFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Titre
        title = QLabel("⚠️ Alertes & Notifications")
        title.setStyleSheet("font-size: 14px; font-weight: 700;")
        layout.addWidget(title)
        
        # Container pour les alertes
        self.alertes_container = QVBoxLayout()
        self.alertes_container.setSpacing(8)
        layout.addLayout(self.alertes_container)
        
        layout.addStretch()
        
        return frame
    
    def _create_stock_detail_frame(self):
        """Crée le frame du stock détaillé"""
        from PySide6.QtWidgets import QTableWidget, QHeaderView
        
        frame = QFrame()
        frame.setObjectName("StockDetailFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Titre
        title = QLabel("📦 Stock détaillé par produit (aperçu)")
        title.setStyleSheet("font-size: 14px; font-weight: 700;")
        layout.addWidget(title)
        
        # Tableau
        self.table_stock = QTableWidget(0, 4)
        self.table_stock.setObjectName("table_stock")
        self.table_stock.setHorizontalHeaderLabels([
            "Désignation", "Type", "Quantité totale", "Statut principal"
        ])
        
        header = self.table_stock.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.table_stock.verticalHeader().setVisible(False)
        self.table_stock.setMaximumHeight(250)
        
        layout.addWidget(self.table_stock)
        
        return frame
    
    def charger_statistiques(self, code_session):
        """Charge les statistiques pour la session"""
        if not self.panier_ctrl or not code_session:
            return
        
        try:
            # Obtenir les données
            stats = self.panier_ctrl.obtenir_statistiques_stock(code_session)
            
            # Charger les graphiques
            self._charger_chart_expiration(stats)
            self._charger_chart_type(stats)
            
            # Charger les alertes
            self._charger_alertes(stats)
            
            # Charger le tableau
            self._charger_tableau_stock(code_session)
            
        except Exception as e:
            print(f"[StatistiquesStockV2] Erreur: {e}")
    
    def _charger_chart_expiration(self, stats):
        """Charge le graphique d'expiration"""
        data = {
            "Expiré": stats.get("nb_expires", 0),
            "Bientôt (<30j)": stats.get("nb_bientot_expire", 0),
            "Valides (>30j)": stats.get("nb_valides", 0)
        }
        
        c = theme_manager.colors()
        colors = {
            "Expiré": c['danger'],
            "Bientôt (<30j)": c['warning'],
            "Valides (>30j)": c['success'],
        }
        
        chart = DonutChart(
            "Répartition des quantités par statut d'expiration",
            data,
            colors,
            "Total quantité"
        )
        
        # Remplacer le chart
        chart_container = self.chart_expiration.findChild(QWidget, "ChartContainer")
        if chart_container:
            layout = chart_container.layout()
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            layout.addWidget(chart)
    
    def _charger_chart_type(self, stats):
        """Charge le graphique par type"""
        data = {
            "Liquide": stats.get("qte_liquide", 0),
            "Pommade": stats.get("qte_pommade", 0),
            "Comprimé": stats.get("qte_comprime", 0)
        }
        
        c = theme_manager.colors()
        colors = {
            "Liquide": c['info'],
            "Pommade": c['accent'],
            "Comprimé": c['success'],
        }
        
        chart = DonutChart(
            "Répartition des quantités par type de produit",
            data,
            colors
        )
        
        # Remplacer le chart
        chart_container = self.chart_type.findChild(QWidget, "ChartContainer")
        if chart_container:
            layout = chart_container.layout()
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            layout.addWidget(chart)
    
    def _charger_alertes(self, stats):
        """Charge les alertes"""
        # Vider les alertes existantes
        while self.alertes_container.count():
            item = self.alertes_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Ajouter les nouvelles alertes
        c = theme_manager.colors()
        alertes = [
            ("fa5s.exclamation-triangle", "produits en rupture de stock",
             stats.get("nb_rupture", 0),      c['danger']),
            ("fa5s.clock", "lots à expirer dans 30 jours",
             stats.get("nb_bientot_expire", 0), c['warning']),
            ("fa5s.times-circle", "lots déjà expirés",
             stats.get("nb_expires", 0),       c['accent']),
            ("fa5s.exclamation-circle", "Stock faible",
             stats.get("nb_stock_faible", 0),  c['danger']),
        ]
        
        for icon, text, count, color in alertes:
            card = AlerteCard(icon, text, count, color)
            self.alertes_container.addWidget(card)
    
    def _charger_tableau_stock(self, code_session):
        """Charge le tableau de stock détaillé"""
        from PySide6.QtWidgets import QTableWidgetItem
        
        self.table_stock.setRowCount(0)
        
        # Obtenir les produits
        produits = self.panier_ctrl.obtenir_stock_detaille(code_session, limite=10)
        
        for produit in produits:
            row = self.table_stock.rowCount()
            self.table_stock.insertRow(row)
            
            # Désignation
            designation = produit.get('designation', '') if isinstance(produit, dict) else getattr(produit, 'designation', '')
            self.table_stock.setItem(row, 0, QTableWidgetItem(designation))
            
            # Type
            type_p = produit.get('type', '') if isinstance(produit, dict) else getattr(produit, 'type', '')
            self.table_stock.setItem(row, 1, QTableWidgetItem(type_p))
            
            # Quantité
            qte = produit.get('quantite', 0) if isinstance(produit, dict) else getattr(produit, 'quantite', 0)
            self.table_stock.setItem(row, 2, QTableWidgetItem(str(qte)))
            
            # Statut (à calculer selon date expiration)
            statut = "Valide"
            self.table_stock.setItem(row, 3, QTableWidgetItem(statut))
    
    def apply_theme(self):
        """Applique le thème"""
        c = theme_manager.colors()

        self.setStyleSheet(f"""
            StatistiquesStockV2Widget {{
                background: {c['bg_main']};
            }}
            QFrame#ChartFrame, QFrame#AlertesFrame, QFrame#StockDetailFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}
            QTableWidget#table_stock {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                gridline-color: {c['border_light']};
            }}
            QHeaderView::section {{
                background: {c['table_header_bg']};
                color: {c['text_secondary']};
                border: none;
                padding: 8px;
                font-size: 11px;
                font-weight: 700;
            }}
        """)
        if hasattr(self, '_scroll_v2'):
            _bg = c['bg_card']
            self._scroll_v2.setStyleSheet(
                f"QScrollArea {{ border: none; background: {_bg}; }}"
                f"QScrollArea > QWidget {{ background: {_bg}; }}"
            )
