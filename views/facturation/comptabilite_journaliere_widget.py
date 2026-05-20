from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QPushButton)
from PySide6.QtCore import Qt, QMargins
from PySide6.QtGui import QFont, QColor
import qtawesome as qta
from views.shared.theme_manager import ThemeManager

class ComptabiliteJournaliereWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = ThemeManager()
        self.current_page = 1
        self.items_per_page = 10
        self.code_session = None
        
        # Initialiser les montants pour le donut
        self._montant_consultations = 0
        self._montant_examens = 0
        self._montant_chirurgies = 0
        self._montant_lunettes = 0
        self._montant_prescriptions = 0
        
        # Importer le contrôleur
        from controllers.controleur_statistiques_financieres import StatistiquesFinancieresControleur
        self.ctrl = StatistiquesFinancieresControleur()
        
        self._init_ui()
        # Ne pas charger les données de test au démarrage
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Espace de 6px en haut
        layout.addSpacing(6)
        
        # Cards KPI en haut (5 cards)
        layout.addLayout(self._create_kpi_cards())
        
        # Ligne 2: Résumé financier + Donut
        h_layout = QHBoxLayout()
        h_layout.setSpacing(10)
        h_layout.addWidget(self._create_resume_financier(), 1)
        h_layout.addWidget(self._create_donut_revenus(), 1)
        layout.addLayout(h_layout)
        
        # Ligne 3: Tableau détails des activités (pleine largeur)
        layout.addWidget(self._create_details_table())
        
        layout.addStretch()
        
    def _create_kpi_cards(self):
        h_layout = QHBoxLayout()
        h_layout.setSpacing(12)
        
        # Stocker les références aux cards pour mise à jour
        self.kpi_cards = []
        
        # 5 cards seulement
        cards_data = [
            ("Consultations", "--", "#3B82F6", "fa5s.stethoscope", ""),
            ("Examens", "--", "#8B5CF6", "fa5s.microscope", ""),
            ("Chirurgies", "--", "#F97316", "fa5s.cut", ""),
            ("Commandes lunettes", "--", "#10B981", "fa5s.glasses", ""),
            ("Prescriptions", "--", "#EC4899", "fa5s.prescription", "")
        ]
        
        for title, nombre, color, icon_name, variation in cards_data:
            card = self._create_kpi_card(title, nombre, color, icon_name, variation)
            self.kpi_cards.append(card)
            h_layout.addWidget(card)
            
        return h_layout
        
    def _create_kpi_card(self, title, nombre, color, icon_name, variation):
        card = QFrame()
        card.setMaximumWidth(250)
        card.setFixedHeight(90)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Icône
        icon_label = QLabel()
        icon = qta.icon(icon_name, color='white')
        icon_label.setPixmap(icon.pixmap(22, 22))
        icon_label.setFixedSize(40, 40)
        icon_label.setStyleSheet(f"background-color: {color}; border-radius: 10px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Contenu
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 11px; color: #6B7280; background: transparent;")
        lbl_title.setWordWrap(False)
        content_layout.addWidget(lbl_title)
        
        lbl_nombre = QLabel(nombre)
        lbl_nombre.setObjectName("CardNombre")
        lbl_nombre.setStyleSheet("font-size: 24px; font-weight: bold; background: transparent; color: #1F2937;")
        content_layout.addWidget(lbl_nombre)
        
        lbl_variation = QLabel(variation if variation else "")
        lbl_variation.setObjectName("CardVariation")
        lbl_variation.setStyleSheet("font-size: 10px; color: #10B981; background: transparent;")
        content_layout.addWidget(lbl_variation)
        
        layout.addLayout(content_layout)
        layout.addStretch()
        
        colors = self.theme_manager.colors()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg_card']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        
        # Stocker les labels pour mise à jour
        card.lbl_nombre = lbl_nombre
        card.lbl_variation = lbl_variation
        
        return card
        
    def _create_resume_financier(self):
        frame = QFrame()
        frame.setMaximumHeight(150)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)
        
        # Titre
        lbl_title = QLabel("Résumé financier de la journée")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; background: transparent; border: none;")
        layout.addWidget(lbl_title)
        
        # Layout horizontal pour les 2 éléments
        h_layout = QHBoxLayout()
        h_layout.setSpacing(30)
        
        # Total des services (gauche)
        v_left = QVBoxLayout()
        v_left.setSpacing(4)
        lbl_total_services = QLabel("Total des services")
        lbl_total_services.setStyleSheet("font-size: 12px; color: #6B7280; background: transparent; border: none;")
        v_left.addWidget(lbl_total_services)
        
        self.lbl_nb_services = QLabel("--")
        self.lbl_nb_services.setStyleSheet("font-size: 32px; font-weight: bold; color: #3B82F6; background: transparent; border: none;")
        v_left.addWidget(self.lbl_nb_services)
        h_layout.addLayout(v_left)
        
        # Montant total du jour (droite)
        v_right = QVBoxLayout()
        v_right.setSpacing(4)
        lbl_montant_label = QLabel("Montant total du jour")
        lbl_montant_label.setStyleSheet("font-size: 12px; color: #6B7280; background: transparent; border: none;")
        v_right.addWidget(lbl_montant_label)
        
        self.lbl_montant_jour = QLabel("-- GNF")
        self.lbl_montant_jour.setStyleSheet("font-size: 32px; font-weight: bold; color: #10B981; background: transparent; border: none;")
        v_right.addWidget(self.lbl_montant_jour)
        h_layout.addLayout(v_right)
        
        layout.addLayout(h_layout)
        layout.addStretch()
        
        colors = self.theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg_card']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        return frame
    
    def _create_donut_revenus(self):
        from PySide6.QtCharts import QChart, QChartView, QPieSeries
        from PySide6.QtGui import QPainter, QColor
        
        frame = QFrame()
        frame.setMaximumHeight(150)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(4)
        
        # Titre
        lbl_title = QLabel("Répartition des revenus par service")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; background: transparent; border: none;")
        layout.addWidget(lbl_title)
        
        # Graphique donut + légende
        h_layout = QHBoxLayout()
        h_layout.setSpacing(15)
        
        # Donut
        series = QPieSeries()
        # Valeurs dynamiques à partir des stats
        montant_consultations = getattr(self, '_montant_consultations', 0)
        montant_examens = getattr(self, '_montant_examens', 0)
        montant_chirurgies = getattr(self, '_montant_chirurgies', 0)
        montant_lunettes = getattr(self, '_montant_lunettes', 0)
        montant_prescriptions = getattr(self, '_montant_prescriptions', 0)
        
        series.append("Consultations", montant_consultations)
        series.append("Examens", montant_examens)
        series.append("Chirurgies", montant_chirurgies)
        series.append("Commandes", montant_lunettes)
        series.append("Prescriptions", montant_prescriptions)
        
        series.setHoleSize(0.5)
        
        # Couleurs
        colors_list = ["#3B82F6", "#8B5CF6", "#F97316", "#10B981", "#EC4899"]
        for i, slice in enumerate(series.slices()):
            slice.setBrush(QColor(colors_list[i]))
            slice.setBorderColor(QColor("white"))
            slice.setBorderWidth(3)
            slice.setLabelVisible(False)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)
        chart.legend().setVisible(False)
        chart.setBackgroundVisible(False)
        chart.setMargins(QMargins(0, 0, 0, 0))
        
        # Texte au centre
        total_donut = sum([self._montant_consultations, self._montant_examens,
                          self._montant_chirurgies, self._montant_lunettes,
                          self._montant_prescriptions])
        chart.setTitle(f"{total_donut:,.0f}\nGNF".replace(',', ' '))
        chart.setTitleFont(QFont("Arial", 11, QFont.Weight.Bold))
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setFixedSize(180, 120)
        chart_view.setStyleSheet("background: transparent; border: none;")
        h_layout.addWidget(chart_view)
        
        # Légende
        legend_layout = QVBoxLayout()
        legend_layout.setSpacing(4)
        
        legend_data = [
            ("Consultations", self._montant_consultations, "#3B82F6"),
            ("Examens", self._montant_examens, "#8B5CF6"),
            ("Chirurgies", self._montant_chirurgies, "#F97316"),
            ("Commandes", self._montant_lunettes, "#10B981"),
            ("Prescriptions", self._montant_prescriptions, "#EC4899")
        ]
        
        total_montant = sum([self._montant_consultations, self._montant_examens, 
                            self._montant_chirurgies, self._montant_lunettes, 
                            self._montant_prescriptions])
        
        for name, montant, color in legend_data:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(6)
            
            # Carré de couleur
            color_box = QLabel()
            color_box.setFixedSize(10, 10)
            color_box.setStyleSheet(f"background-color: {color}; border-radius: 2px; border: none;")
            item_layout.addWidget(color_box)
            
            # Nom
            lbl_name = QLabel(name)
            lbl_name.setStyleSheet("font-size: 11px; background: transparent; border: none;")
            lbl_name.setFixedWidth(110)
            item_layout.addWidget(lbl_name)
            
            # Montant et %
            pct = (montant / total_montant * 100) if total_montant > 0 else 0
            lbl_val = QLabel(f"{montant:,.0f} GNF ({pct:.1f}%)".replace(',', ' '))
            lbl_val.setStyleSheet("font-size: 10px; color: #6B7280; background: transparent; border: none;")
            item_layout.addWidget(lbl_val)
            
            item_layout.addStretch()
            legend_layout.addLayout(item_layout)
        
        legend_layout.addStretch()
        h_layout.addLayout(legend_layout)
        
        layout.addLayout(h_layout)
        
        colors = self.theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg_card']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        return frame
    
    def _create_details_table(self):
        frame = QFrame()
        frame.setMinimumHeight(450)
        frame.setMaximumHeight(450)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(4)
        
        # Titre
        lbl_title = QLabel("Détail des activités par service")
        lbl_title.setStyleSheet("font-size: 12px; font-weight: bold; background: transparent;")
        layout.addWidget(lbl_title)
        
        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Service", "Nombre d'actes", "Montant unitaire moyen", "Montant total"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setMinimumHeight(350)
        
        layout.addWidget(self.table, 1)
        
        # Pas de pagination - afficher tous les services
        
        colors = self.theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg_card']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
            }}
            QTableWidget {{
                border: none;
                background-color: transparent;
                gridline-color: {colors['border']};
            }}
            QTableWidget::item {{
                padding: 10px;
                background: transparent;
                border: none;
                color: #1F2937;
            }}
            QTableWidget::item:selected {{
                background-color: #EFF6FF;
                color: #1F2937;
            }}
            QHeaderView::section {{
                background-color: #F3F4F6;
                color: #374151;
                padding: 10px;
                border: none;
                border-bottom: 2px solid {colors['border']};
                font-weight: bold;
                font-size: 12px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QPushButton#PaginationButton, QPushButton#PageButton {{
                background: {colors['bg_card']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
                color: {colors['text_primary']};
                font-weight: 600;
            }}
            QPushButton#PageButton[active="true"] {{
                background: {colors['primary']};
                color: white;
                border: 1px solid {colors['primary']};
            }}
            QPushButton#PaginationButton:hover, QPushButton#PageButton:hover {{
                background: {colors['primary_light']};
            }}
        """)
        
        return frame
        
    def charger_donnees_test(self):
        """Charge des données de test (utilisé uniquement pour le développement)"""
        # Données statiques avec icônes
        self.all_data = [
            ("Consultations", "fa5s.stethoscope", "#3B82F6", "32", "22 188", "710 000"),
            ("Examens", "fa5s.microscope", "#8B5CF6", "28", "22 143", "620 000"),
            ("Chirurgies", "fa5s.cut", "#F97316", "5", "196 000", "980 000"),
            ("Commandes lunettes", "fa5s.glasses", "#10B981", "18", "23 333", "420 000"),
            ("Prescriptions", "fa5s.prescription", "#EC4899", "41", "6 098", "250 000"),
        ]
        
        self.update_table_page()
    
    def update_table_page(self):
        """Met à jour le tableau avec toutes les données (sans pagination)"""
        self.table.setRowCount(0)
        
        # Afficher toutes les données
        for row, (service, icon_name, color, nb_actes, montant_moy, total) in enumerate(self.all_data):
            self.table.insertRow(row)
            self.table.setRowHeight(row, 38)
            
            # Service avec icône
            service_widget = QWidget()
            service_widget.setStyleSheet("background: transparent; border: none;")
            service_layout = QHBoxLayout(service_widget)
            service_layout.setContentsMargins(8, 0, 8, 0)
            service_layout.setSpacing(8)
            service_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            
            icon_label = QLabel()
            icon = qta.icon(icon_name, color='white')
            icon_label.setPixmap(icon.pixmap(12, 12))
            icon_label.setFixedSize(20, 20)
            icon_label.setStyleSheet(f"background-color: {color}; border-radius: 4px; border: none;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            service_layout.addWidget(icon_label)
            
            lbl_service = QLabel(service)
            lbl_service.setStyleSheet("background: transparent; border: none; color: #1F2937; font-size: 10px;")
            service_layout.addWidget(lbl_service)
            service_layout.addStretch()
            
            self.table.setCellWidget(row, 0, service_widget)
            
            # Nombre d'actes
            item_nb = QTableWidgetItem(nb_actes)
            item_nb.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_nb.setForeground(QColor("#1F2937"))
            font_nb = QFont()
            font_nb.setPointSize(9)
            item_nb.setFont(font_nb)
            self.table.setItem(row, 1, item_nb)
            
            # Montant unitaire moyen
            item_moy = QTableWidgetItem(f"{montant_moy} GNF")
            item_moy.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_moy.setForeground(QColor("#1F2937"))
            font_moy = QFont()
            font_moy.setPointSize(9)
            item_moy.setFont(font_moy)
            self.table.setItem(row, 2, item_moy)
            
            # Total
            item_total = QTableWidgetItem(f"{total} GNF")
            item_total.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_total.setForeground(QColor("#1F2937"))
            font_total = QFont()
            font_total.setPointSize(9)
            item_total.setFont(font_total)
            self.table.setItem(row, 3, item_total)
        
        # Ajouter la ligne Total général
        total_row = self.table.rowCount()
        self.table.insertRow(total_row)
        self.table.setRowHeight(total_row, 38)
        
        item_total_label = QTableWidgetItem("Total général")
        item_total_label.setForeground(QColor("#1F2937"))
        font_bold = QFont()
        font_bold.setPointSize(9)
        font_bold.setBold(True)
        item_total_label.setFont(font_bold)
        self.table.setItem(total_row, 0, item_total_label)
        
        # Calculer le total des services
        total_services = sum(int(row[3]) for row in self.all_data)
        item_total_nb = QTableWidgetItem(str(total_services))
        item_total_nb.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item_total_nb.setForeground(QColor("#1F2937"))
        item_total_nb.setFont(font_bold)
        self.table.setItem(total_row, 1, item_total_nb)
        
        item_total_moy = QTableWidgetItem("—")
        item_total_moy.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item_total_moy.setForeground(QColor("#6B7280"))
        self.table.setItem(total_row, 2, item_total_moy)
        
        # Calculer le montant total
        total_montant = sum(int(row[5].replace(' ', '')) for row in self.all_data)
        item_total_montant = QTableWidgetItem(f"{total_montant:,} GNF".replace(',', ' '))
        item_total_montant.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        item_total_montant.setForeground(QColor("#10B981"))
        item_total_montant.setFont(font_bold)
        self.table.setItem(total_row, 3, item_total_montant)
            
    def apply_theme(self):
        colors = self.theme_manager.colors()
        self.setStyleSheet(f"background-color: {colors['bg_primary']};")
    
    def charger_donnees(self, code_session: str):
        """Charge les données réelles depuis la base de données"""
        if not code_session:
            return
        
        self.code_session = code_session
        
        # Récupérer les statistiques JOURNALIÈRES (aujourd'hui uniquement)
        stats = self.ctrl.obtenir_statistiques_journalieres(code_session)
        
        if not stats:
            return
        
        # Mettre à jour le tableau avec les données du jour
        self._update_table_data(stats)
    
    def _update_kpi_cards(self, stats):
        """Met à jour les valeurs des cards KPI"""
        if not hasattr(self, 'kpi_cards') or not self.kpi_cards:
            return
        
        # Données pour chaque card
        cards_values = [
            stats.get('nb_consultations', 0),
            stats.get('nb_examens', 0),
            stats.get('nb_chirurgies', 0),
            stats.get('nb_lunettes', 0),
            stats.get('nb_prescriptions', 0)
        ]
        
        for i, card in enumerate(self.kpi_cards):
            if i < len(cards_values):
                card.lbl_nombre.setText(str(cards_values[i]))
                # Variation à implémenter si nécessaire
                card.lbl_variation.setText("")
    
    def _update_resume_financier(self, stats):
        """Met à jour le résumé financier"""
        if not hasattr(self, 'lbl_nb_services') or not hasattr(self, 'lbl_montant_jour'):
            return
        
        total_services = stats.get('total_services', 0)
        total_montant = stats.get('total_montant', 0)
        
        self.lbl_nb_services.setText(str(total_services))
        self.lbl_montant_jour.setText(f"{total_montant:,.0f} GNF".replace(',', ' '))
    
    def _update_donut_revenus(self, stats):
        """Met à jour le donut des revenus"""
        # Stocker les montants pour le donut (initialiser à 0 si pas encore défini)
        self._montant_consultations = stats.get('montant_consultations', 0)
        self._montant_examens = stats.get('montant_examens', 0)
        self._montant_chirurgies = stats.get('montant_chirurgies', 0)
        self._montant_lunettes = stats.get('montant_lunettes', 0)
        self._montant_prescriptions = stats.get('montant_prescriptions', 0)
    
    def _update_table_data(self, stats):
        """Met à jour les données du tableau avec les statistiques réelles du jour"""
        # Mettre à jour les KPI cards
        self._update_kpi_cards(stats)
        
        # Mettre à jour le résumé financier
        self._update_resume_financier(stats)
        
        # Mettre à jour le donut
        self._update_donut_revenus(stats)
        
        # Construire les données du tableau à partir des stats journalières
        self.all_data = [
            (
                "Consultations",
                "fa5s.stethoscope",
                "#3B82F6",
                str(stats.get('nb_consultations', 0)),
                f"{stats.get('montant_unitaire_consultations', 0):,.0f}".replace(',', ' '),
                f"{stats.get('montant_consultations', 0):,.0f}".replace(',', ' ')
            ),
            (
                "Examens",
                "fa5s.microscope",
                "#8B5CF6",
                str(stats.get('nb_examens', 0)),
                f"{stats.get('montant_unitaire_examens', 0):,.0f}".replace(',', ' '),
                f"{stats.get('montant_examens', 0):,.0f}".replace(',', ' ')
            ),
            (
                "Chirurgies",
                "fa5s.cut",
                "#F97316",
                str(stats.get('nb_chirurgies', 0)),
                f"{stats.get('montant_unitaire_chirurgies', 0):,.0f}".replace(',', ' '),
                f"{stats.get('montant_chirurgies', 0):,.0f}".replace(',', ' ')
            ),
            (
                "Commandes lunettes",
                "fa5s.glasses",
                "#10B981",
                str(stats.get('nb_lunettes', 0)),
                f"{stats.get('montant_unitaire_lunettes', 0):,.0f}".replace(',', ' '),
                f"{stats.get('montant_lunettes', 0):,.0f}".replace(',', ' ')
            ),
            (
                "Prescriptions",
                "fa5s.prescription",
                "#EC4899",
                str(stats.get('nb_prescriptions', 0)),
                f"{stats.get('montant_unitaire_prescriptions', 0):,.0f}".replace(',', ' '),
                f"{stats.get('montant_prescriptions', 0):,.0f}".replace(',', ' ')
            ),
        ]
        
        # Mettre à jour l'affichage
        self.current_page = 1
        self.update_table_page()
    

