from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QFrame, QGridLayout, QScrollArea)
from PySide6.QtCore import Qt, QMargins, Signal
from PySide6.QtGui import QIcon, QColor
from PySide6.QtCharts import QChart, QChartView, QPieSeries
import qtawesome as qta
import os
import logging

from controllers.controleur_statistiques_financieres import StatistiquesFinancieresControleur

class StatistiquesFinancieresWidget(QWidget):
    # Signaux pour les quick actions
    export_rapport_clicked = Signal()
    nouvelle_facture_clicked = Signal()
    paiement_fournisseur_clicked = Signal()
    recherche_transaction_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.code_session = None
        
        # Injection du contrôleur statistiques
        self.ctrl = StatistiquesFinancieresControleur()
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Ligne du haut : Cards KPI (1 seule ligne de 6 cards)
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(8)
        kpi_row.setContentsMargins(0, 0, 0, 0)
        self.kpi_cards_list = []
        layout.addLayout(kpi_row)
        self.kpi_row = kpi_row
        
        # Ligne du milieu : 2 graphiques côte à côte
        row_charts = QHBoxLayout()
        row_charts.setSpacing(10)
        row_charts.setContentsMargins(0, 0, 0, 0)
        
        self.stock_widget = self.create_stock_table()
        self.donut_widget = self.create_donut_chart()
        
        row_charts.addWidget(self.stock_widget, 1)
        row_charts.addWidget(self.donut_widget, 1)
        layout.addLayout(row_charts, 1)
        
        # Ligne du bas : Transactions + Résumé
        row_bottom = QHBoxLayout()
        row_bottom.setSpacing(10)
        row_bottom.setContentsMargins(0, 0, 0, 0)
        
        self.transactions_widget = self.create_transactions_table()
        self.summary_widget = self.create_summary_card()
        
        row_bottom.addWidget(self.transactions_widget, 1)
        row_bottom.addWidget(self.summary_widget, 1)
        layout.addLayout(row_bottom, 1)
        
        # Quick Actions en bas
        quick_actions = self.create_quick_actions()
        layout.addWidget(quick_actions)
        
        self.apply_styles()
    
    def create_kpi_card(self, title, amount, percentage, trend_up, color, icon_name):
        card = QFrame()
        card.setObjectName("KPICard")
        card.setFixedHeight(75)
        card.setMaximumWidth(220)
        layout = QHBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Icône à gauche dans un rectangle coloré
        icon_container = QFrame()
        icon_container.setObjectName("IconContainer")
        icon_container.setStyleSheet(f"""
            background-color: {color};
            border-radius: 6px;
        """)
        icon_container.setFixedSize(32, 32)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = qta.icon(icon_name, color='white')
        icon_label.setPixmap(icon.pixmap(18, 18))
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_container)
        
        # Contenu à droite
        content_layout = QVBoxLayout()
        content_layout.setSpacing(1)
        
        title_label = QLabel(title)
        title_label.setObjectName("KPITitle")
        title_label.setWordWrap(True)
        content_layout.addWidget(title_label)
        
        amount_label = QLabel(f"{amount:,} GNF".replace(",", " "))
        amount_label.setObjectName("KPIAmount")
        content_layout.addWidget(amount_label)
        
        # Afficher le badge seulement si le pourcentage est > 0
        if percentage > 0:
            badge = QLabel(f"{'↑' if trend_up else '↓'} {percentage:.1f}%")
            badge.setObjectName("TrendBadgeUp" if trend_up else "TrendBadgeDown")
            content_layout.addWidget(badge)
        
        content_layout.addStretch()
        layout.addLayout(content_layout)
        
        return card
    
    def create_stock_table(self):
        widget = QFrame()
        widget.setObjectName("GraphCard")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        title = QLabel("Valeur du stock par type de produit")
        title.setObjectName("GraphTitle")
        layout.addWidget(title)
        
        table = QTableWidget(5, 4)
        table.setObjectName("StockTable")
        table.setHorizontalHeaderLabels(["Type de produit", "Valeur en stock", "Pourcentage", ""])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.stock_table = table
        layout.addWidget(table)
        
        return widget
    
    def create_donut_chart(self):
        widget = QFrame()
        widget.setObjectName("GraphCard")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        title = QLabel("Répartition des revenus par service")
        title.setObjectName("GraphTitle")
        layout.addWidget(title)
        
        # Layout horizontal pour graphique + légende
        chart_layout = QHBoxLayout()
        chart_layout.setSpacing(10)
        
        # Graphique donut
        series = QPieSeries()
        series.setHoleSize(0.5)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setVisible(False)
        chart.setBackgroundVisible(False)
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.setTitle("")
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(chart_view.renderHints())
        chart_view.setFixedSize(160, 160)
        
        self.donut_series = series
        self.donut_chart = chart
        
        # Légende personnalisée à droite
        legend_widget = QWidget()
        legend_layout = QVBoxLayout(legend_widget)
        legend_layout.setSpacing(8)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.legend_layout = legend_layout
        
        chart_layout.addWidget(chart_view)
        chart_layout.addWidget(legend_widget, 1)
        
        layout.addLayout(chart_layout)
        
        return widget
    
    def create_transactions_table(self):
        widget = QFrame()
        widget.setObjectName("GraphCard")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        title = QLabel("Transactions récentes")
        title.setObjectName("GraphTitle")
        layout.addWidget(title)
        
        table = QTableWidget(0, 6)
        table.setObjectName("TransactionsTable")
        table.setHorizontalHeaderLabels(["Date", "Description", "Catégorie", "Montant", "Type", "Méthode"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.transactions_table = table
        layout.addWidget(table)
        
        return widget
    
    def create_summary_card(self):
        widget = QFrame()
        widget.setObjectName("SummaryCard")
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        title = QLabel("Résumé financier")
        title.setObjectName("GraphTitle")
        layout.addWidget(title)
        
        # Encaissements
        enc_label = QLabel("Total des encaissements")
        enc_label.setObjectName("SummaryLabel")
        self.enc_amount = QLabel("0 GNF")
        self.enc_amount.setObjectName("SummaryAmountPositive")
        layout.addWidget(enc_label)
        layout.addWidget(self.enc_amount)
        
        # Décaissements
        dec_label = QLabel("Total des décaissements")
        dec_label.setObjectName("SummaryLabel")
        self.dec_amount = QLabel("0 GNF")
        self.dec_amount.setObjectName("SummaryAmountNegative")
        layout.addWidget(dec_label)
        layout.addWidget(self.dec_amount)
        
        # Solde
        solde_label = QLabel("Solde net (Période)")
        solde_label.setObjectName("SummaryLabel")
        self.solde_amount = QLabel("0 GNF")
        self.solde_amount.setObjectName("SummaryAmountSolde")
        layout.addWidget(solde_label)
        layout.addWidget(self.solde_amount)
        
        layout.addStretch()
        
        return widget
    
    def create_quick_actions(self):
        """Crée la section quick actions en bas"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)
        
        actions = [
            ("fa5s.file-export", "Exporter le rapport", "#3B82F6", self.export_rapport_clicked),
            ("fa5s.file-invoice", "Nouvelle facture", "#10B981", self.nouvelle_facture_clicked),
            ("fa5s.money-bill-wave", "Paiement fournisseur", "#F97316", self.paiement_fournisseur_clicked),
            ("fa5s.search", "Rechercher transaction", "#8B5CF6", self.recherche_transaction_clicked),
        ]
        
        for icon_name, text, color, signal in actions:
            btn = QPushButton(f"  {text}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.setObjectName("QuickActionButton")
            icon = qta.icon(icon_name, color=color)
            btn.setIcon(icon)
            btn.clicked.connect(signal.emit)
            layout.addWidget(btn)
        
        return widget
    
    def charger_donnees(self, code_session: str):
        """Charge les données réelles depuis le service statistiques."""
        if not code_session:
            self.logger.warning("Code session manquant")
            return
        
        self.code_session = code_session
        self.logger.info(f"Chargement statistiques pour session {code_session}")
        
        try:
            # Récupérer les statistiques complètes
            stats = self.ctrl.obtenir_statistiques_completes(code_session)
            
            # Charger les KPI cards
            self._charger_kpi_cards(stats)
            
            # Charger le tableau stock
            self._charger_tableau_stock(code_session)
            
            # Charger le graphique donut
            self._charger_graphique_revenus(stats)
            
            # Charger les transactions
            self._charger_transactions(code_session)
            
            # Charger le résumé financier
            self._charger_resume_financier(stats)
            
            self.logger.info("Statistiques chargées avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur chargement statistiques: {e}")
    
    def _charger_kpi_cards(self, stats: dict):
        """Charge les 6 cards KPI."""
        # Nettoyer les cards existantes
        for i in reversed(range(self.kpi_row.count())):
            widget = self.kpi_row.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Définir les services avec leurs configurations
        services_config = [
            ('consultations', 'Consultations', stats.get('consultations', 0), "#3B82F6", "fa5s.stethoscope"),
            ('examens', 'Examens', stats.get('examens', 0), "#8B5CF6", "fa5s.microscope"),
            ('chirurgies', 'Chirurgies', stats.get('chirurgies', 0), "#F97316", "fa5s.cut"),
            ('lunettes', 'Commandes lunettes', stats.get('lunettes', 0), "#10B981", "fa5s.glasses"),
            ('prescriptions', 'Prescriptions', stats.get('prescriptions', 0), "#EC4899", "fa5s.prescription"),
            ('paiements_fournisseurs', 'Paiement fournisseurs', stats.get('paiements_fournisseurs', 0), "#06B6D4", "fa5s.shopping-cart"),
        ]
        
        for service_key, title, amount, color, icon in services_config:
            # Calculer la variation pour ce service
            pct, trend_up = self.ctrl.calculer_variation_mois_precedent(self.code_session, service_key)
            
            card = self.create_kpi_card(title, int(amount), pct, trend_up, color, icon)
            self.kpi_row.addWidget(card)
    
    def _charger_tableau_stock(self, code_session: str):
        """Charge le tableau valeur du stock par type."""
        try:
            stock_data = self.ctrl.obtenir_valeur_stock_par_type(code_session)
            
            # Ajouter une ligne TOTAL
            total_valeur = sum(item['valeur'] for item in stock_data)
            stock_data.append({'type': 'TOTAL', 'valeur': total_valeur, 'pourcentage': 100.0})
            
            self.stock_table.setRowCount(len(stock_data))
            
            for i, item in enumerate(stock_data):
                self.stock_table.setItem(i, 0, QTableWidgetItem(item['type']))
                self.stock_table.setItem(i, 1, QTableWidgetItem(f"{int(item['valeur']):,} GNF".replace(",", " ")))
                self.stock_table.setItem(i, 2, QTableWidgetItem(f"{item['pourcentage']}%"))
                
                if i < len(stock_data) - 1:  # Pas de barre pour TOTAL
                    pct = item['pourcentage']
                    progress = QLabel(f"{'█' * int(pct/10)}")
                    progress.setStyleSheet("color: #10B981;")
                    self.stock_table.setCellWidget(i, 3, progress)
                    
        except Exception as e:
            self.logger.error(f"Erreur chargement tableau stock: {e}")
    
    def _charger_graphique_revenus(self, stats: dict):
        """Charge le graphique donut des revenus par service."""
        try:
            # Nettoyer le graphique
            self.donut_series.clear()
            
            # Nettoyer la légende
            for i in reversed(range(self.legend_layout.count())):
                widget = self.legend_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            revenus = [
                ("Consultations", stats.get('consultations', 0), "#3B82F6"),
                ("Examens", stats.get('examens', 0), "#8B5CF6"),
                ("Chirurgies", stats.get('chirurgies', 0), "#F97316"),
                ("Commandes lunettes", stats.get('lunettes', 0), "#10B981"),
                ("Prescriptions", stats.get('prescriptions', 0), "#EC4899"),
            ]
            
            total_revenus = sum(montant for _, montant, _ in revenus)
            
            if total_revenus == 0:
                return
            
            for nom, montant, couleur in revenus:
                if montant > 0:
                    slice = self.donut_series.append(nom, montant)
                    slice.setLabelVisible(False)
                    slice.setBorderColor(QColor("white"))
                    slice.setBorderWidth(2)
                    slice.setColor(QColor(couleur))
                    
                    # Ajouter à la légende
                    legend_item = QWidget()
                    legend_item_layout = QHBoxLayout(legend_item)
                    legend_item_layout.setContentsMargins(0, 0, 0, 0)
                    legend_item_layout.setSpacing(10)
                    
                    color_box = QLabel()
                    color_box.setFixedSize(10, 10)
                    color_box.setStyleSheet(f"background-color: {couleur}; border-radius: 2px;")
                    legend_item_layout.addWidget(color_box)
                    
                    text_label = QLabel(f"{nom}")
                    text_label.setStyleSheet("font-size: 11px; color: #374151; font-weight: 500;")
                    legend_item_layout.addWidget(text_label)
                    legend_item_layout.addStretch()
                    
                    pct = (montant / total_revenus) * 100
                    amount_label = QLabel(f"{int(montant):,} GNF".replace(",", " "))
                    amount_label.setStyleSheet("font-size: 10px; color: #1F2937; font-weight: 600;")
                    legend_item_layout.addWidget(amount_label)
                    
                    pct_label = QLabel(f"{pct:.1f}%")
                    pct_label.setStyleSheet("font-size: 10px; color: #6B7280; font-weight: 500;")
                    legend_item_layout.addWidget(pct_label)
                    
                    self.legend_layout.addWidget(legend_item)
                    
        except Exception as e:
            self.logger.error(f"Erreur chargement graphique revenus: {e}")
    
    def _charger_transactions(self, code_session: str):
        """Charge le tableau des transactions récentes."""
        try:
            transactions = self.ctrl.obtenir_transactions_recentes(code_session, 10)
            
            self.transactions_table.setRowCount(len(transactions))
            
            for i, trans in enumerate(transactions):
                self.transactions_table.setItem(i, 0, QTableWidgetItem(trans['date']))
                self.transactions_table.setItem(i, 1, QTableWidgetItem(trans['description']))
                self.transactions_table.setItem(i, 2, QTableWidgetItem(trans['categorie']))
                
                montant = trans['montant']
                montant_item = QTableWidgetItem(f"{int(montant):,} GNF".replace(",", " "))
                if montant < 0:
                    montant_item.setForeground(Qt.GlobalColor.red)
                self.transactions_table.setItem(i, 3, montant_item)
                
                self.transactions_table.setItem(i, 4, QTableWidgetItem(trans['type']))
                self.transactions_table.setItem(i, 5, QTableWidgetItem(trans['methode']))
                
        except Exception as e:
            self.logger.error(f"Erreur chargement transactions: {e}")
    
    def _charger_resume_financier(self, stats: dict):
        """Charge le résumé financier."""
        try:
            enc = int(stats.get('total_encaissements', 0))
            dec = int(stats.get('total_decaissements', 0))
            solde = int(stats.get('solde_net', 0))
            
            self.enc_amount.setText(f"{enc:,} GNF".replace(",", " "))
            self.dec_amount.setText(f"{dec:,} GNF".replace(",", " "))
            self.solde_amount.setText(f"{solde:,} GNF".replace(",", " "))
            
        except Exception as e:
            self.logger.error(f"Erreur chargement résumé financier: {e}")
    
    def apply_styles(self):
        self.setStyleSheet("""
            #KPICard, #GraphCard, #SummaryCard, #TotalCard {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 0px;
            }
            #KPITitle, #GraphTitle {
                font-size: 10px;
                font-weight: 600;
                color: #6B7280;
            }
            #KPIAmount {
                font-size: 13px;
                font-weight: bold;
                color: #1F2937;
            }
            #TotalAmount {
                font-size: 15px;
                font-weight: bold;
                color: #3B82F6;
            }
            #TrendBadgeUp {
                background: #D1FAE5;
                color: #065F46;
                padding: 2px 6px;
                border-radius: 8px;
                font-size: 9px;
                font-weight: 600;
            }
            #TrendBadgeDown {
                background: #FEE2E2;
                color: #991B1B;
                padding: 2px 6px;
                border-radius: 8px;
                font-size: 9px;
                font-weight: 600;
            }
            #StockTable, #TransactionsTable {
                border: none;
                gridline-color: #E5E7EB;
            }
            #SummaryLabel {
                font-size: 11px;
                color: #6B7280;
            }
            #SummaryAmountPositive {
                font-size: 18px;
                font-weight: bold;
                color: #10B981;
            }
            #SummaryAmountNegative {
                font-size: 18px;
                font-weight: bold;
                color: #EF4444;
            }
            #SummaryAmountSolde {
                font-size: 18px;
                font-weight: bold;
                color: #3B82F6;
            }
            QPushButton#QuickActionButton {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding-left: 15px;
                text-align: left;
                font-size: 12px;
                font-weight: 600;
                color: #374151;
            }
            QPushButton#QuickActionButton:hover {
                background: #F3F4F6;
                border-color: #D1D5DB;
            }
        """)
