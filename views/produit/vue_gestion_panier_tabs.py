"""
Vue Gestion Produits avec architecture à onglets.
Similaire à la vue prescription avec 4 onglets.
"""
import qtawesome as qta
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QFrame, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QSize
from views.shared.theme_manager import theme_manager
from .vue_statistique_panier import StatistiquesStockWidget
from .vue_panier_produit import PanierProduitWidget
from .styles import ProduitStyles


class GestionProduitsView(QWidget):
    """
    Vue principale pour la gestion des produits avec onglets.
    4 onglets : Statistiques, Mouvements Stock, Produits en Stock, Panier
    """

    def __init__(self, controleur=None):
        super().__init__()
        self.controleur = controleur
        self.code_session = None
        self.logger = logging.getLogger(__name__)

        # Initialiser panier_ctrl AVANT _init_ui car il est utilisé dans _create_stats_tab
        from controllers.controleur_panierFourni import PanierFactureFourniControleur
        from controllers.controleur_stock_import_export import StockImportExportControleur
        self.panier_ctrl = PanierFactureFourniControleur()
        self.stock_import_ctrl = StockImportExportControleur()
        
        self._init_ui()
        
        # Appliquer le thème
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)
        
        # Initialiser les panneaux latéraux
        self._init_panneaux_lateraux()

    def _init_panneaux_lateraux(self):
        """Initialise les panneaux latéraux (Stock + Factures)"""
        from views.facturation.fournisseur.panneaux import PanneauStockProduits, PanneauFactures
        from controllers.controleur_factureFournisseur import FactureFournisseurControleur
        
        # Utiliser self.panier_ctrl déjà initialisé dans __init__
        facture_ctrl = FactureFournisseurControleur()
        
        self.panneau_stock = PanneauStockProduits(self, self.panier_ctrl)
        self.panneau_factures = PanneauFactures(self, facture_ctrl, self.panier_ctrl)
        self._badge_notification = None

    def _init_ui(self):
        """Initialise l'interface avec onglets"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(0)
        
        # Frame principal blanc
        main_frame = QFrame()
        main_frame.setObjectName("MainWhiteFrame")
        main_frame_layout = QVBoxLayout(main_frame)
        main_frame_layout.setContentsMargins(0, 0, 0, 0)
        main_frame_layout.setSpacing(0)
        
        # Barre du haut (titre + boutons actions)
        self._setup_top_bar(main_frame_layout)
        
        # Tabs Widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setIconSize(QSize(20, 20))
        self._apply_tab_styles()
        main_frame_layout.addWidget(self.tabs)
        
        # Créer les 4 onglets
        self._create_tabs()
        
        # Quick Actions (toujours visible en bas)
        self._setup_quick_actions(main_frame_layout)
        
        # Ajouter le frame principal
        main_layout.addWidget(main_frame)
        self._apply_main_frame_style(main_frame)

    def _setup_top_bar(self, parent_layout):
        """Barre du haut avec titre uniquement"""
        top_frame = QFrame()
        top_frame.setStyleSheet("background: transparent; border: none;")
        hbox = QHBoxLayout(top_frame)
        hbox.setContentsMargins(15, 10, 15, 10)
        hbox.setSpacing(10)
        
        # Titre
        titre = QLabel("Gestion des Produits & Stock")
        c = theme_manager.colors()
        titre.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {c['primary']};")
        self._titre_label = titre
        
        hbox.addWidget(titre)
        hbox.addStretch()
        
        parent_layout.addWidget(top_frame)

    def _setup_quick_actions(self, parent_layout):
        """Crée la barre d'actions rapides en bas"""
        actions_frame = QFrame()
        actions_frame.setStyleSheet("background: transparent; border: none;")
        hbox = QHBoxLayout(actions_frame)
        hbox.setContentsMargins(12, 8, 12, 8)
        hbox.setSpacing(8)
        
        # Créer les boutons d'action
        self.btn_add = self._create_quick_action_btn("fa5s.plus-square", "Nouveau Produit", "primary")
        self.btn_add.clicked.connect(self.ouvrir_formulaire_nouveau_produit)

        self.btn_modifier = self._create_quick_action_btn("fa5s.edit", "Modifier", "info")

        self.btn_rapports = self._create_quick_action_btn("fa5s.exchange-alt", "Rapports & exports", "success")
        self.btn_rapports.clicked.connect(self._on_rapports)

        self.btn_notification = self._create_quick_action_btn("fa5s.bell", "Notifications", "warning")
        self.btn_notification.clicked.connect(self._ouvrir_panneau_factures)
        self._creer_badge_notification()

        self.btn_stock = self._create_quick_action_btn("fa5s.boxes", "Gestion du Stock", "primary")
        self.btn_stock.clicked.connect(self._ouvrir_panneau_stock)

        self.btn_factures = self._create_quick_action_btn("fa5s.file-invoice-dollar", "Factures Fournisseurs", "accent")
        self.btn_factures.clicked.connect(self._ouvrir_panneau_factures)

        # Ajouter au layout
        hbox.addWidget(self.btn_add)
        hbox.addWidget(self.btn_modifier)
        hbox.addWidget(self.btn_rapports)
        hbox.addWidget(self.btn_notification)
        hbox.addWidget(self.btn_stock)
        hbox.addWidget(self.btn_factures)
        hbox.addStretch()
        
        parent_layout.addWidget(actions_frame)
    
    def _create_quick_action_btn(self, icon_name, text, color_key):
        """Crée un bouton d'action rapide"""
        c = theme_manager.colors()
        btn = QPushButton(f"  {text}")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(40)
        btn.setObjectName("QuickActionButton")
        btn.setProperty("color_key", color_key)
        btn.setProperty("icon_name", icon_name)
        
        color = c.get(color_key, c["primary"])
        btn.setIcon(qta.icon(icon_name, color=color))
        btn.setStyleSheet(f"""
            QPushButton#QuickActionButton {{
                background: {c['bg_card']};
                border: none;
                border-radius: 8px;
                padding-left: 15px;
                text-align: left;
                font-size: 12px;
                font-weight: 600;
                color: {c['text_primary']};
            }}
            QPushButton#QuickActionButton:hover {{
                background: {c['hover']};
            }}
        """)
        return btn
    
    def _creer_badge_notification(self):
        """Crée le badge de notification sur le bouton"""
        self._badge_notification = QLabel("0")
        self._badge_notification.setFixedSize(18, 18)
        self._badge_notification.setAlignment(Qt.AlignCenter)
        self._badge_notification.hide()
        self._badge_notification.setParent(self.btn_notification)
        self._badge_notification.move(28, -2)
        self._badge_notification.raise_()

    def _create_tabs(self):
        """Crée les 4 onglets"""
        # Onglet 1: Statistiques
        self.tab_stats = self._create_stats_tab()
        self.tab_stats.setObjectName("tab_stats")
        icon_stats = self._get_icon("chart-bar")
        self.tabs.addTab(self.tab_stats, icon_stats, "Statistiques")

        # Onglet 2: Mouvements Stock
        self.tab_mouvements = self._create_mouvements_tab()
        self.tab_mouvements.setObjectName("tab_mouvements")
        icon_mouvements = self._get_icon("exchange-alt")
        self.tabs.addTab(self.tab_mouvements, icon_mouvements, "Mouvements Stock")

        # Onglet 3: Produits en Stock
        self.tab_produits = self._create_produits_tab()
        self.tab_produits.setObjectName("tab_produits")
        icon_produits = self._get_icon("box-open")
        self.tabs.addTab(self.tab_produits, icon_produits, "Produits en Stock")

        # Onglet 4: Panier
        self.tab_panier = self._create_panier_tab()
        self.tab_panier.setObjectName("tab_panier")
        icon_panier = self._get_icon("cart-plus")
        self.tabs.addTab(self.tab_panier, icon_panier, "Panier d'approvisionnement")

    def _create_stats_tab(self):
        """Onglet Statistiques"""
        tab = QWidget()
        tab.setStyleSheet(f"background: {theme_manager.colors()['bg_card']};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)
        
        # Widget statistiques - Utiliser self.panier_ctrl au lieu de créer une nouvelle instance
        self.statistiques_widget = StatistiquesStockWidget(
            panier_ctrl=self.panier_ctrl,
            show_stock_detail=True
        )
        layout.addWidget(self.statistiques_widget)
        
        return tab

    def _create_mouvements_tab(self):
        """Onglet Mouvements Stock"""
        from PySide6.QtWidgets import QTableWidget, QHeaderView

        tab = QWidget()
        tab.setStyleSheet(f"background: {theme_manager.colors()['bg_card']};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)
        
        # Tableau des mouvements
        self.table_mouvements = QTableWidget(0, 5)
        self.table_mouvements.setHorizontalHeaderLabels([
            "Code", "Produit", "Type", "Date Expiration", "Quantité Entrée"
        ])
        
        header = self.table_mouvements.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table_mouvements.setColumnWidth(4, 120)
        
        self.table_mouvements.verticalHeader().setVisible(False)
        self.table_mouvements.setAlternatingRowColors(True)
        
        layout.addWidget(self.table_mouvements)
        
        return tab

    def _create_produits_tab(self):
        """Onglet Produits en Stock"""
        from PySide6.QtWidgets import QScrollArea, QGridLayout

        tab = QWidget()
        tab.setStyleSheet(f"background: {theme_manager.colors()['bg_card']};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(8)
        
        # Zone scrollable pour les cards produits
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        _bg = theme_manager.colors()['bg_card']
        scroll_area.setStyleSheet(
            f"QScrollArea {{ border: none; background: {_bg}; }}"
            f"QScrollArea > QWidget {{ background: {_bg}; }}"
        )
        self._scroll_produits = scroll_area

        container = QWidget()
        container.setStyleSheet(f"background: {_bg};")
        self.grid_produits = QGridLayout(container)
        self.grid_produits.setContentsMargins(5, 5, 5, 5)
        self.grid_produits.setSpacing(10)
        self.grid_produits.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)
        
        return tab

    def _create_panier_tab(self):
        """Onglet Panier d'approvisionnement - Formulaire à gauche + Panier à droite"""
        from controllers.controleur_panierFourni import PanierFactureFourniControleur
        from controllers.controleur_fournisseur import FournisseurControleur
        from controllers.controleur_factureFournisseur import FactureFournisseurControleur
        
        tab = QWidget()
        tab.setStyleSheet(f"background: {theme_manager.colors()['bg_card']};")
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        panier_ctrl = PanierFactureFourniControleur()
        fournisseur_ctrl = FournisseurControleur()
        facture_ctrl = FactureFournisseurControleur()
        
        # Widget panier en mode "split" (formulaire + panier côte à côte)
        self.panier_widget = PanierProduitWidget(
            panier_ctrl=panier_ctrl,
            produit_ctrl=self.controleur,
            fournisseur_ctrl=fournisseur_ctrl,
            facture_ctrl=facture_ctrl,
            parent=self,
            layout_mode="split"  # Mode split pour avoir formulaire à gauche et panier à droite
        )
        
        # Ajouter le widget panier (stretch 1 pour prendre tout l'espace)
        layout.addWidget(self.panier_widget, 1)
        
        return tab

    def _get_icon(self, icon_name):
        """Récupère une icône Font Awesome"""
        try:
            icon_map = {
                "chart-bar": "fa5s.chart-bar",
                "exchange-alt": "fa5s.exchange-alt",
                "box-open": "fa5s.box-open",
                "cart-plus": "fa5s.cart-plus"
            }
            return qta.icon(icon_map.get(icon_name, "fa5s.circle"), color=theme_manager.colors()['primary'])
        except:
            from PySide6.QtWidgets import QStyle
            return self.style().standardIcon(QStyle.SP_FileIcon)

    def _apply_main_frame_style(self, frame):
        """Applique le style au frame principal"""
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame#MainWhiteFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
        """)

    def _apply_tab_styles(self):
        """Applique les styles aux onglets"""
        c = theme_manager.colors()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {c['bg_card']};
                border-radius: 12px;
            }}
            QTabBar {{
                background: {c['bg_card']};
            }}
            QTabBar::tab {{
                background: {c['bg_card']};
                color: {c['text_secondary']};
                padding: 10px 20px;
                margin-right: 4px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 13px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                color: {c['primary']};
                border-bottom: 2px solid {c['primary']};
                font-weight: 600;
            }}
            QTabBar::tab:hover {{
                color: {c['primary']};
                background: {c['hover']};
            }}
        """)

    def apply_theme(self):
        """Applique le thème actif"""
        c = theme_manager.colors()
        self.setStyleSheet(f"GestionProduitsView {{ background-color: {c['bg_main']}; }}")

        if hasattr(self, 'tabs'):
            self._apply_tab_styles()
            main_frame = self.findChild(QFrame, "MainWhiteFrame")
            if main_frame:
                self._apply_main_frame_style(main_frame)

        # Appliquer styles aux boutons quick actions
        if hasattr(self, 'btn_add'):
            for btn_name in ['btn_add', 'btn_modifier', 'btn_rapports',
                             'btn_notification', 'btn_stock', 'btn_factures']:
                if hasattr(self, btn_name):
                    btn = getattr(self, btn_name)
                    color_key = btn.property("color_key") or "primary"
                    color = c.get(color_key, c["primary"])
                    btn.setIcon(qta.icon(btn.property("icon_name") or "fa5s.circle", color=color))
                    btn.setStyleSheet(f"""
                        QPushButton#QuickActionButton {{
                            background: {c['bg_card']};
                            border: none;
                            border-radius: 8px;
                            padding-left: 15px;
                            text-align: left;
                            font-size: 12px;
                            font-weight: 600;
                            color: {c['text_primary']};
                        }}
                        QPushButton#QuickActionButton:hover {{
                            background: {c['hover']};
                        }}
                    """)

        if hasattr(self, 'table_mouvements'):
            self.table_mouvements.setStyleSheet(ProduitStyles.table())

        for attr in ('tab_stats', 'tab_mouvements', 'tab_produits', 'tab_panier'):
            tab = getattr(self, attr, None)
            if tab and tab.objectName():
                tab.setStyleSheet(f"QWidget#{tab.objectName()} {{ background-color: {c['bg_card']}; }}")

        if hasattr(self, '_scroll_produits'):
            _bg = c['bg_card']
            self._scroll_produits.setStyleSheet(
                f"QScrollArea {{ border: none; background: {_bg}; }}"
                f"QScrollArea > QWidget {{ background: {_bg}; }}"
            )

        if hasattr(self, '_titre_label'):
            self._titre_label.setStyleSheet(
                f"font-size: 18px; font-weight: bold; color: {c['primary']};"
            )

    def charger_donnees(self, code_session=None):
        """Charge les données pour la session"""
        if code_session:
            self.code_session = code_session
        
        # Charger statistiques
        if hasattr(self, 'statistiques_widget'):
            self.statistiques_widget.charger_statistiques(code_session)
        
        # Charger produits en stock
        self._charger_stock_detail_liste(code_session)
        
        # Charger panier
        if hasattr(self, 'panier_widget'):
            self.panier_widget.charger_donnees(code_session)
        
        # Charger mouvements
        if hasattr(self, 'table_mouvements'):
            self._charger_mouvements_stock(code_session)
        
        self._mettre_a_jour_badge_notification()

    def _charger_stock_detail_liste(self, code_session: str):
        """Charge la liste des produits en stock"""
        if not self.panier_ctrl or not hasattr(self, 'grid_produits'):
            return
        
        try:
            from .statistiques_panier.components.product_stock_card import ProductStockCard
            from PySide6.QtWidgets import QLabel
            
            # Vider la grille
            while self.grid_produits.count():
                item = self.grid_produits.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            produits = self.panier_ctrl.obtenir_stock_detaille(code_session, limite=30)
            
            if not produits:
                lbl_vide = QLabel("Aucun produit en stock pour cette session.")
                lbl_vide.setStyleSheet(
                    f"color: {theme_manager.colors()['text_muted']}; font-size: 13px; padding: 20px;"
                )
                self.grid_produits.addWidget(lbl_vide, 0, 0)
                return
            
            row = 0
            col = 0
            for produit in produits:
                card = ProductStockCard(
                    libelle=produit.get('designation', 'Produit'),
                    type_produit=produit.get('type', 'Comprimé'),
                    quantite=produit.get('quantite', 0)
                )
                self.grid_produits.addWidget(card, row, col)
                
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
        except Exception as e:
            self.logger.error(f"[GestionProduitsView] Erreur chargement stock: {e}", exc_info=True)

    def _charger_mouvements_stock(self, code_session: str):
        """Charge les mouvements de stock"""
        from PySide6.QtWidgets import QTableWidgetItem
        
        if not code_session or not hasattr(self, 'table_mouvements'):
            return
        
        from controllers.controleur_panierFourni import PanierFactureFourniControleur
        panier_ctrl = PanierFactureFourniControleur()
        
        mouvements = panier_ctrl.lister_par_session(code_session)
        self.table_mouvements.setRowCount(0)
        
        for mouvement in mouvements:
            row = self.table_mouvements.rowCount()
            self.table_mouvements.insertRow(row)
            
            code = mouvement.code_produit if hasattr(mouvement, 'code_produit') else ''
            self.table_mouvements.setItem(row, 0, QTableWidgetItem(code))
            
            libelle = mouvement.designation if hasattr(mouvement, 'designation') else ''
            self.table_mouvements.setItem(row, 1, QTableWidgetItem(libelle))
            
            type_p = mouvement.type if hasattr(mouvement, 'type') else ''
            self.table_mouvements.setItem(row, 2, QTableWidgetItem(type_p))
            
            date_exp = ''
            if hasattr(mouvement, 'date_expiration') and mouvement.date_expiration:
                date_exp = mouvement.date_expiration.strftime('%d/%m/%Y')
            self.table_mouvements.setItem(row, 3, QTableWidgetItem(date_exp))
            
            qte = str(mouvement.quantite_four) if hasattr(mouvement, 'quantite_four') else '0'
            item_qte = QTableWidgetItem(qte)
            item_qte.setTextAlignment(Qt.AlignCenter)
            self.table_mouvements.setItem(row, 4, item_qte)

    def _mettre_a_jour_badge_notification(self):
        """Met à jour le badge de notification"""
        if not self._badge_notification or not self.code_session:
            return
        
        try:
            from controllers.controleur_factureFournisseur import FactureFournisseurControleur
            facture_ctrl = FactureFournisseurControleur()
            nb_factures = facture_ctrl.obtenir_total_factures_session(self.code_session)
            
            c = theme_manager.colors()
            if nb_factures > 0:
                self._badge_notification.setText(str(nb_factures))
                self._badge_notification.show()
                self._badge_notification.setStyleSheet(
                    f"background:{c['warning']}; color:{c['text_inverse']}; "
                    "border-radius:9px; font-size:9px; font-weight:700; border:none;"
                )
            else:
                self._badge_notification.hide()
        except Exception as e:
            self.logger.error(f"[GestionProduitsView] Erreur badge: {e}", exc_info=True)

    # =========================================================================
    # RAPPORTS & EXPORTS — menu déroulant (pattern identique examen/chirurgie)
    # =========================================================================

    def _on_rapports(self):
        """Affiche le menu export/import au-dessus du bouton Rapports & exports."""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtCore import QPoint
        import qtawesome as qta
        c = theme_manager.colors()

        # Injecter la session dans le contrôleur avant toute opération lots
        self.stock_import_ctrl.set_code_session(self.code_session)

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {c['bg_card']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 6px 4px;
            }}
            QMenu::item {{
                padding: 9px 20px 9px 12px;
                border-radius: 6px;
                font-size: 13px;
                color: {c['text_primary']};
                min-width: 240px;
            }}
            QMenu::item:selected {{
                background: {c['primary_light']};
                color: {c['primary']};
            }}
            QMenu::item:disabled {{
                color: {c.get('text_muted', '#999')};
                font-weight: 600;
                font-size: 11px;
            }}
            QMenu::separator {{
                height: 1px;
                background: {c['border']};
                margin: 4px 10px;
            }}
        """)

        # ── Section PRODUITS ──
        lbl_p = menu.addAction("  PRODUITS (catalogue)")
        lbl_p.setEnabled(False)
        act_exp_p_xl = menu.addAction(qta.icon("fa5s.file-excel", color="#217346"), "    Exporter Excel (.xlsx)")
        act_exp_p_cs = menu.addAction(qta.icon("fa5s.file-csv",   color="#0070c0"), "    Exporter CSV (.csv)")
        menu.addSeparator()
        act_imp_p_xl = menu.addAction(qta.icon("fa5s.upload", color="#217346"),     "    Importer Excel (.xlsx)")
        act_imp_p_cs = menu.addAction(qta.icon("fa5s.upload", color="#0070c0"),     "    Importer CSV (.csv)")

        menu.addSeparator()

        # ── Section LOTS DE STOCK ──
        lbl_l = menu.addAction("  LOTS DE STOCK — date expiration (FEFO)")
        lbl_l.setEnabled(False)
        act_exp_l_xl = menu.addAction(qta.icon("fa5s.file-excel", color="#217346"), "    Exporter Excel (.xlsx)")
        act_exp_l_cs = menu.addAction(qta.icon("fa5s.file-csv",   color="#0070c0"), "    Exporter CSV (.csv)")
        menu.addSeparator()
        act_imp_l_xl = menu.addAction(qta.icon("fa5s.upload", color="#217346"),     "    Importer Excel (.xlsx)")
        act_imp_l_cs = menu.addAction(qta.icon("fa5s.upload", color="#0070c0"),     "    Importer CSV (.csv)")

        # Connexions produits
        act_exp_p_xl.triggered.connect(lambda: self._apercu_export_produits("excel"))
        act_exp_p_cs.triggered.connect(lambda: self._apercu_export_produits("csv"))
        act_imp_p_xl.triggered.connect(lambda: self._apercu_import("excel", "produits"))
        act_imp_p_cs.triggered.connect(lambda: self._apercu_import("csv",   "produits"))

        # Connexions lots
        act_exp_l_xl.triggered.connect(lambda: self._apercu_export_lots("excel"))
        act_exp_l_cs.triggered.connect(lambda: self._apercu_export_lots("csv"))
        act_imp_l_xl.triggered.connect(lambda: self._apercu_import("excel", "lots"))
        act_imp_l_cs.triggered.connect(lambda: self._apercu_import("csv",   "lots"))

        # Positionner au-dessus du bouton (même logique que examen/chirurgie)
        menu.adjustSize()
        btn = self.btn_rapports
        pos = btn.mapToGlobal(QPoint(0, 0))
        pos.setY(pos.y() - menu.sizeHint().height() - 6)
        menu.exec(pos)

    def _apercu_export_produits(self, format_fichier: str):
        """Export produits avec aperçu (pattern ApercuActeModal)."""
        from views.acte_medical.export_import_acte import ApercuActeModal
        from views.shared.message_box import CustomMessageBox
        from PySide6.QtWidgets import QFileDialog

        donnees_dicts = self.stock_import_ctrl.obtenir_produits_pour_export()
        if not donnees_dicts:
            CustomMessageBox("Export Produits", "Aucun produit à exporter.",
                             msg_type="info", parent=self).exec()
            return

        colonnes = ['code_produit', 'libelle', 'type', 'prix_achat_unitaire', 'prix_vente_unitaire']
        donnees  = [[str(d.get(col, "")) for col in colonnes] for d in donnees_dicts]
        ext      = "xlsx" if format_fichier == "excel" else "csv"

        modal = ApercuActeModal(
            self,
            f"Aperçu export {ext.upper()} — Produits",
            f"{len(donnees)} produit(s) prêt(s) à exporter",
            colonnes, donnees, mode="export"
        )
        if not (modal.exec() and modal._confirme):
            return

        filtre  = "Excel Files (*.xlsx)" if format_fichier == "excel" else "CSV Files (*.csv)"
        chemin, _ = QFileDialog.getSaveFileName(
            self, f"Enregistrer — {ext.upper()}", f"produits_export.{ext}", filtre
        )
        if not chemin:
            return

        ok, msg = self.stock_import_ctrl.export_to_excel(chemin) \
                  if format_fichier == "excel" \
                  else self.stock_import_ctrl.export_to_csv(chemin)
        CustomMessageBox(
            "Export réussi" if ok else "Erreur export",
            msg, msg_type="success" if ok else "error", parent=self
        ).exec()

    def _apercu_export_lots(self, format_fichier: str):
        """Export lots de stock avec aperçu (pattern ApercuActeModal)."""
        from views.acte_medical.export_import_acte import ApercuActeModal
        from views.shared.message_box import CustomMessageBox
        from PySide6.QtWidgets import QFileDialog

        if not self.code_session:
            CustomMessageBox("Export Lots", "Aucune session active.",
                             msg_type="warning", parent=self).exec()
            return

        donnees_dicts = self.stock_import_ctrl.obtenir_lots_pour_export()
        if not donnees_dicts:
            CustomMessageBox("Export Lots", "Aucun lot de stock à exporter pour cette session.",
                             msg_type="info", parent=self).exec()
            return

        colonnes = ['code_produit', 'designation', 'quantite_four',
                    'prix_unitaire', 'date_expiration', 'code_facture_four']
        donnees  = [[str(d.get(col, "")) for col in colonnes] for d in donnees_dicts]
        ext      = "xlsx" if format_fichier == "excel" else "csv"

        modal = ApercuActeModal(
            self,
            f"Aperçu export {ext.upper()} — Lots de stock",
            f"{len(donnees)} lot(s) — date expiration visible pour vérification FEFO",
            colonnes, donnees, mode="export"
        )
        if not (modal.exec() and modal._confirme):
            return

        filtre  = "Excel Files (*.xlsx)" if format_fichier == "excel" else "CSV Files (*.csv)"
        chemin, _ = QFileDialog.getSaveFileName(
            self, f"Enregistrer — {ext.upper()}", f"lots_stock_export.{ext}", filtre
        )
        if not chemin:
            return

        ok, msg = self.stock_import_ctrl.export_lots_to_excel(chemin) \
                  if format_fichier == "excel" \
                  else self.stock_import_ctrl.export_lots_to_csv(chemin)
        CustomMessageBox(
            "Export réussi" if ok else "Erreur export",
            msg, msg_type="success" if ok else "error", parent=self
        ).exec()

    def _apercu_import(self, format_fichier: str, type_donnee: str):
        """
        Import avec aperçu du fichier avant confirmation (pattern ApercuActeModal.ouvrir_import).
        type_donnee : 'produits' ou 'lots'
        """
        from views.acte_medical.export_import_acte import ApercuActeModal
        from views.shared.message_box import CustomMessageBox
        from PySide6.QtWidgets import QFileDialog

        if type_donnee == "lots" and not self.code_session:
            CustomMessageBox("Import Lots",
                             "Aucune session active — impossible d'importer des lots de stock.",
                             msg_type="warning", parent=self).exec()
            return

        ext    = "xlsx" if format_fichier == "excel" else "csv"
        filtre = "Excel Files (*.xlsx)" if format_fichier == "excel" else "CSV Files (*.csv)"
        label  = "Produits" if type_donnee == "produits" else "Lots de stock"

        chemin, _ = QFileDialog.getOpenFileName(
            self, f"Sélectionner le fichier {ext.upper()} — {label}", "", filtre
        )
        if not chemin:
            return

        # Lire le fichier pour l'aperçu
        try:
            import pandas as pd
            df = pd.read_excel(chemin) if format_fichier == "excel" \
                 else pd.read_csv(chemin, sep=None, engine='python', encoding="utf-8-sig")
            if df.empty:
                CustomMessageBox("Import", "Le fichier ne contient aucune donnée.",
                                 msg_type="warning", parent=self).exec()
                return
            colonnes = list(df.columns)
            donnees  = [[str(v) for v in row] for _, row in df.iterrows()]
        except Exception as e:
            CustomMessageBox("Erreur de lecture", f"Impossible de lire le fichier :\n{e}",
                             msg_type="error", parent=self).exec()
            return

        modal = ApercuActeModal(
            self,
            f"Aperçu import {ext.upper()} — {label}",
            f"{len(donnees)} ligne(s) détectée(s) dans le fichier",
            colonnes, donnees, mode="import"
        )
        if not (modal.exec() and modal._confirme):
            return

        # Appeler la bonne méthode du contrôleur
        if type_donnee == "produits":
            ok, msg = self.stock_import_ctrl.import_produits(chemin, format_fichier)
        else:
            ok, msg = self.stock_import_ctrl.import_lots(chemin, format_fichier)

        CustomMessageBox(
            f"Import {label} réussi" if ok else f"Import {label} — résultat",
            msg, msg_type="success" if ok else "warning", parent=self
        ).exec()

        if ok:
            self.charger_donnees(self.code_session)

    def ouvrir_formulaire_nouveau_produit(self):
        """Ouvre le formulaire de création de produit"""
        from PySide6.QtWidgets import QMessageBox
        from .produit_form import ProduitFormDialog
        
        if not self.controleur:
            QMessageBox.warning(self, "Erreur", "Contrôleur non initialisé")
            return
        
        formulaire = ProduitFormDialog(
            controleur=self.controleur,
            produit_obj=None,
            parent=self
        )
        
        if formulaire.exec() == ProduitFormDialog.Accepted:
            self.logger.info("[INFO] Nouveau produit créé")

    def _ouvrir_panneau_stock(self):
        """Ouvre le panneau stock"""
        from PySide6.QtWidgets import QMessageBox
        
        if self.code_session:
            self.panneau_stock.actualiser(self.code_session)
            self.panneau_stock.basculer()
        else:
            QMessageBox.warning(self, "Session non définie", "Aucune session active")

    def _ouvrir_panneau_factures(self):
        """Ouvre le panneau factures"""
        from PySide6.QtWidgets import QMessageBox
        
        if self.code_session:
            self.panneau_factures.actualiser(self.code_session)
            self.panneau_factures.basculer()
        else:
            QMessageBox.warning(self, "Session non définie", "Aucune session active")
