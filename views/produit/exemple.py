import qtawesome as qta
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QLabel, QComboBox, QMessageBox,
    QSizePolicy
)

# Import des composants modulaires
from .vue_panier_produit import PanierProduitWidget
from .vue_statistique_panier import StatistiquesStockWidget
from views.shared.animated_frame import AnimatedFrame
from .statistiques_panier.components import StockDetailCard
from .statistiques_panier.components.product_stock_card import ProductStockCard
from views.shared.theme_manager import theme_manager
from views.produit.styles import ProduitStyles


from .produit_form import ProduitFormDialog


# =============================================================================
# VUE PRINCIPALE
# =============================================================================

class GestionProduitsView(QWidget):
    """
    Vue principale pour la gestion des produits et du panier d approvisionnement.
    Interface uniquement â€” contrÃ´leurs Ã  brancher ultÃ©rieurement.
    """


    def __init__(self, controleur=None):
        super().__init__()
        self.controleur = controleur
        self.code_session = None
        self.panier_ctrl = None
        self._panier_overlay_visible = False
        self._panier_anim = None
        self._init_ui()
        
        # Appliquer le thème initial et écouter les changements
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)
        
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # PANNEAUX LATÃ‰RAUX (Stock + Factures)
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        from views.facturation.fournisseur.panneaux import PanneauStockProduits, PanneauFactures
        from controllers.controleur_panierFourni import PanierFactureFourniControleur
        from controllers.controleur_factureFournisseur import FactureFournisseurControleur
        
        panier_ctrl = PanierFactureFourniControleur()
        self.panier_ctrl = panier_ctrl
        facture_ctrl = FactureFournisseurControleur()
        
        # Panneau Stock
        self.panneau_stock = PanneauStockProduits(self, panier_ctrl)
        
        # Panneau Factures
        self.panneau_factures = PanneauFactures(self, facture_ctrl, panier_ctrl)
        
        # Badge de notification (sera mis Ã  jour automatiquement)
        self._badge_notification = None

    def apply_theme(self):
        """Applique le thème actif aux composants principaux de la vue produits."""
        c = theme_manager.colors()

        # Fond principal
        self.setStyleSheet(f"background-color: {c['bg_main']};")

        # Titre
        if hasattr(self, '_titre_label'):
            self._titre_label.setStyleSheet(
                f"font-size: 18px; font-weight: bold; color: {c['primary']};"
            )

        # Barre de recherche + combo
        self.search_bar.setStyleSheet(ProduitStyles.search_bar())
        self.combo_filtre.setStyleSheet(f"""
            QComboBox {{
                border-radius: 12px; border: 1px solid {c['border']};
                padding-left: 12px; background: {c['bg_card']};
                font-size: 12px; color: {c['text_primary']};
            }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
            QComboBox QAbstractItemView {{
                border-radius: 8px; background: {c['bg_card']};
                color: {c['text_primary']}; border: 1px solid {c['border']};
            }}
        """)

        # Boutons principaux
        self.btn_add.setStyleSheet(ProduitStyles.button_primary())
        self.btn_add.setIcon(qta.icon("fa5s.plus-square", color=c['text_inverse']))
        self.btn_modifier.setStyleSheet(
            f"background-color: {c['info']}; color: {c['text_inverse']};"
            "border-radius: 12px; font-weight: bold; font-size: 12px;"
        )
        self.btn_modifier.setIcon(qta.icon("fa5s.edit", color=c['text_inverse']))
        self.btn_ouvrir_panier.setStyleSheet(ProduitStyles.button_primary())
        self.btn_ouvrir_panier.setIcon(qta.icon("fa5s.cart-plus", color=c['text_inverse']))

        # Boutons icônes ronds
        round_qss = (
            f"background: {c['bg_card']}; border: 1px solid {c['border']};"
            "border-radius: 12px;"
        )
        icon_btns = [
            (self.btn_export_csv,   "fa5s.file-csv",           c['primary']),
            (self.btn_export_excel, "fa5s.file-excel",         c['success']),
            (self.btn_import,       "fa5s.file-import",        c['accent']),
            (self.btn_notification, "fa5s.bell",               c['warning']),
            (self.btn_stock,        "fa5s.boxes",              c['primary']),
            (self.btn_factures,     "fa5s.file-invoice-dollar", c['accent']),
        ]
        for btn, ico, clr in icon_btns:
            btn.setStyleSheet(round_qss)
            btn.setIcon(qta.icon(ico, color=clr))

        # Cadres (mouvements + stock detail)
        card_qss = ProduitStyles.card()
        self.frame_mouvements.setStyleSheet(card_qss)
        self.frame_stock_detail.setStyleSheet(card_qss)

        # Labels titre / icône / séparateur dans les cadres
        for frame in [self.frame_mouvements, self.frame_stock_detail]:
            if hasattr(frame, '_icon_lbl') and hasattr(frame, '_icon_name'):
                frame._icon_lbl.setPixmap(
                    qta.icon(frame._icon_name, color=c['primary']).pixmap(QSize(16, 16))
                )
            if hasattr(frame, '_title_lbl'):
                frame._title_lbl.setStyleSheet(
                    f"font-weight: bold; color: {c['primary']};"
                    "font-size: 12px; border: none;"
                )
            if hasattr(frame, '_separator'):
                frame._separator.setStyleSheet(
                    f"background: {c['border']}; border: none;"
                )

        # Table mouvements + scrollbar
        if hasattr(self, 'table_mouvements'):
            self.table_mouvements.setStyleSheet(ProduitStyles.table())
            self.table_mouvements.verticalScrollBar().setStyleSheet(
                ProduitStyles.scrollbar()
            )

        # Overlay panier
        if hasattr(self, 'panel_panier_overlay'):
            self.panel_panier_overlay.setStyleSheet(
                f"background-color: {c['bg_card']}; border-radius: 18px;"
                f" border: 1px solid {c['border']};"
            )
        if hasattr(self, '_overlay_titre'):
            self._overlay_titre.setStyleSheet(
                f"font-weight: bold; color: {c['primary']};"
                "font-size: 12px; border: none;"
            )
        if hasattr(self, 'btn_fermer_panier'):
            self.btn_fermer_panier.setStyleSheet(
                f"background-color: {c['danger']}; color: {c['text_inverse']};"
                "border-radius: 10px; font-weight: bold; font-size: 10px;"
            )
            self.btn_fermer_panier.setIcon(qta.icon("fa5s.times", color=c['text_inverse']))
        if hasattr(self, '_overlay_sep'):
            self._overlay_sep.setStyleSheet(
                f"background: {c['border']}; border: none;"
            )

        # Badge notification
        self._mettre_a_jour_badge_notification()

    # =========================================================================

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)

        self._setup_top_bar()
        self._setup_statistiques()
        self._setup_bottom_section()

    # =========================================================================
    # BARRE DU HAUT
    # =========================================================================

    def _setup_top_bar(self):
        hbox = QHBoxLayout()
        hbox.setSpacing(10)

        # Titre de la section
        titre = QLabel("Gestion des Produits & Stock")
        c = theme_manager.colors()
        titre.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {c['primary']};"
        )
        self._titre_label = titre

        # Barre de recherche
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("  Rechercher un produit...")
        self.search_bar.setFixedHeight(42)
        self.search_bar.setMinimumWidth(250)
        self.search_bar.setStyleSheet(ProduitStyles.search_bar())

        # Filtre par type
        self.combo_filtre = QComboBox()
        self.combo_filtre.addItems(["Tous les types", "Liquide", "Pommade", "ComprimÃ©"])
        self.combo_filtre.setFixedHeight(42)
        self.combo_filtre.setFixedWidth(160)
        c_combo = theme_manager.colors()
        self.combo_filtre.setStyleSheet(f"""
            QComboBox {{
                border-radius: 12px; border: 1px solid {c_combo['border']};
                padding-left: 12px; background: {c_combo['bg_card']};
                font-size: 12px; color: {c_combo['text_primary']};
            }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
            QComboBox QAbstractItemView {{ border-radius: 8px; background: {c_combo['bg_card']}; color: {c_combo['text_primary']}; }}
        """)

        # Bouton Nouveau produit
        self.btn_add = QPushButton(
            qta.icon("fa5s.plus-square", color="white"), " Nouveau Produit"
        )
        self.btn_add.setFixedHeight(42)
        self.btn_add.setMinimumWidth(155)
        self.btn_add.setStyleSheet(ProduitStyles.button_primary())
        self.btn_add.setCursor(Qt.PointingHandCursor)
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # CONNEXION : Bouton "Nouveau Produit" â†’ Formulaire de crÃ©ation
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        self.btn_add.clicked.connect(self.ouvrir_formulaire_nouveau_produit)

        # Bouton Modifier
        c_btn = theme_manager.colors()
        self.btn_modifier = QPushButton(
            qta.icon("fa5s.edit", color="white"), " Modifier"
        )
        self.btn_modifier.setFixedHeight(42)
        self.btn_modifier.setMinimumWidth(110)
        self.btn_modifier.setStyleSheet(
            f"background-color: {c_btn['info']}; color: {c_btn['text_inverse']};"
            "border-radius: 12px; font-weight: bold; font-size: 12px;"
        )
        self.btn_modifier.setCursor(Qt.PointingHandCursor)
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # CONNEXION : Bouton "Modifier" â†’ Formulaire de modification
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # self.btn_modifier.clicked.connect(self.ouvrir_formulaire_modifier_produit)

        # Boutons icÃ´nes (export, import, notification, stock)
        _ct = theme_manager.colors()
        self.btn_export_csv = self._creer_btn_icone(
            "fa5s.file-csv",    _ct['primary'], "Exporter CSV")
        self.btn_export_excel = self._creer_btn_icone(
            "fa5s.file-excel",  _ct['success'],            "Exporter Excel")
        self.btn_import = self._creer_btn_icone(
            "fa5s.file-import", _ct['accent'],            "Importer")
        self.btn_notification = self._creer_btn_icone(
            "fa5s.bell",        _ct['warning'],            "Notifications")
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # CONNEXION : Bouton Notification â†’ Ouvre le panneau factures
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        self.btn_notification.clicked.connect(self._ouvrir_panneau_factures)
        self._creer_badge_notification()
        
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # BOUTONS PANNEAUX LATÃ‰RAUX
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        self.btn_stock = self._creer_btn_icone(
            "fa5s.boxes",       _ct['primary'],  "Gestion du Stock")
        self.btn_stock.clicked.connect(self._ouvrir_panneau_stock)
        
        self.btn_factures = self._creer_btn_icone(
            "fa5s.file-invoice-dollar", _ct['accent'], "Factures Fournisseurs")
        self.btn_factures.clicked.connect(self._ouvrir_panneau_factures)

        hbox.addWidget(titre)
        hbox.addStretch()
        hbox.addWidget(self.search_bar)
        hbox.addWidget(self.combo_filtre)
        hbox.addWidget(self.btn_add)
        hbox.addWidget(self.btn_modifier)
        hbox.addSpacing(6)
        hbox.addWidget(self.btn_export_csv)
        hbox.addWidget(self.btn_export_excel)
        hbox.addWidget(self.btn_import)
        hbox.addWidget(self.btn_notification)
        hbox.addWidget(self.btn_stock)

        self.main_layout.addLayout(hbox)

    def _creer_btn_icone(self, icone: str, couleur: str, tooltip: str) -> QPushButton:
        btn = QPushButton(qta.icon(icone, color=couleur), "")
        btn.setFixedSize(42, 42)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        c = theme_manager.colors()
        btn.setStyleSheet(
            f"background: {c['bg_card']}; border: 1px solid {c['border']}; border-radius: 12px;"
        )
        return btn
    
    def _creer_badge_notification(self):
        """
        CrÃ©e un badge de notification sur le bouton notification.
        Le badge affiche le nombre de factures.
        """
        # CrÃ©er le badge
        self._badge_notification = QLabel("0")
        self._badge_notification.setFixedSize(18, 18)
        self._badge_notification.setAlignment(Qt.AlignCenter)
        c_badge = theme_manager.colors()
        self._badge_notification.setStyleSheet(
            f"background:{c_badge['warning']}; color:{c_badge['text_inverse']}; "
            f"border-radius:9px; font-size:9px; font-weight:700; border:none;"
        )
        self._badge_notification.hide()
        
        # Positionner le badge en haut Ã  droite du bouton
        self._badge_notification.setParent(self.btn_notification)
        self._badge_notification.move(28, -2)
        self._badge_notification.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ajuster_panier_overlay()

    
    def _mettre_a_jour_badge_notification(self):
        """
        Met Ã  jour le badge de notification avec le nombre de factures.
        AppelÃ© automatiquement lors du chargement des donnÃ©es.
        """
        if not self._badge_notification or not self.code_session:
            return
        
        try:
            # RÃ©cupÃ©rer le nombre de factures de la session
            from controllers.controleur_factureFournisseur import FactureFournisseurControleur
            facture_ctrl = FactureFournisseurControleur()
            nb_factures = facture_ctrl.obtenir_total_factures_session(self.code_session)
            
            c_n = theme_manager.colors()
            if nb_factures > 0:
                self._badge_notification.setText(str(nb_factures))
                self._badge_notification.show()
                self._badge_notification.setStyleSheet(
                    f"background:{c_n['warning']}; color:{c_n['text_inverse']}; "
                    "border-radius:9px; font-size:9px; font-weight:700; border:none;"
                )
                self.btn_notification.setStyleSheet(
                    f"background:{c_n['warning']}20; border:2px solid {c_n['warning']}; border-radius:12px;"
                )
            else:
                self._badge_notification.hide()
                self.btn_notification.setStyleSheet(
                    f"background:{c_n['bg_card']}; border:1px solid {c_n['border']}; border-radius:12px;"
                )
        except Exception as e:
            print(f"[GestionProduitsView] Erreur mise Ã  jour badge: {e}")

    # =========================================================================
    # STATISTIQUES ET GRAPHES
    # =========================================================================

    def _setup_statistiques(self):
        """Utilisation du composant statistiques modulaire avec injection du contrÃ´leur."""
        # CrÃ©er le contrÃ´leur panier pour les statistiques
        from controllers.controleur_panierFourni import PanierFactureFourniControleur
        panier_ctrl = PanierFactureFourniControleur()
        
        # CrÃ©er le widget avec injection du contrÃ´leur
        self.statistiques_widget = StatistiquesStockWidget(
            panier_ctrl=panier_ctrl,
            show_stock_detail=False
        )
        
        # Exposition des widgets pour compatibilitÃ©
        self.card_expires = self.statistiques_widget.card_expires
        self.card_bientot = self.statistiques_widget.card_bientot
        self.card_valides = self.statistiques_widget.card_valides
        self.card_valeur = self.statistiques_widget.card_valeur
        self.card_liquide = self.statistiques_widget.card_liquide
        self.card_pommade = self.statistiques_widget.card_pommade
        self.card_comprime = self.statistiques_widget.card_comprime
        self.frame_detail_stock = None
        self.container_lignes_stock = None
        self.layout_lignes_stock = None
        
        self.main_layout.addWidget(self.statistiques_widget)

    # =========================================================================
    # SECTION BAS : MOUVEMENTS STOCK (gauche) + PANIER (droite)
    # =========================================================================

    def _setup_bottom_section(self):
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        self.frame_mouvements = self._creer_cadre_arrondi(
            "Mouvements de Stock", "fa5s.exchange-alt")
        self._setup_table_mouvements()

        # Utilisation du composant panier modulaire
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # INJECTION DES CONTRÃ”LEURS DANS LE WIDGET PANIER
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        from controllers.controleur_panierFourni import PanierFactureFourniControleur
        from controllers.controleur_fournisseur import FournisseurControleur
        from controllers.controleur_factureFournisseur import FactureFournisseurControleur
        
        panier_ctrl = PanierFactureFourniControleur()
        fournisseur_ctrl = FournisseurControleur()
        facture_ctrl = FactureFournisseurControleur()
        
        self.panier_widget = PanierProduitWidget(
            panier_ctrl=panier_ctrl,
            produit_ctrl=self.controleur,
            fournisseur_ctrl=fournisseur_ctrl,
            facture_ctrl=facture_ctrl,
            layout_mode="split"
        )
        
        # Connecter le signal de finalisation pour actualiser les statistiques ET le tableau
        # Surcharger la mÃ©thode _finaliser_facture du panier_widget
        original_finaliser = self.panier_widget._finaliser_facture
        
        def finaliser_avec_actualisation():
            # Appeler la mÃ©thode originale
            original_finaliser()
            # Actualiser les statistiques
            print("[GestionProduitsView] Actualisation des statistiques aprÃ¨s finalisation...")
            if hasattr(self, 'statistiques_widget') and self.statistiques_widget:
                self.statistiques_widget.actualiser()
                self._charger_stock_detail_liste(self.code_session)
            
            # Actualiser le tableau des mouvements
            print("[GestionProduitsView] Actualisation du tableau des mouvements...")
            if hasattr(self, 'table_mouvements') and self.table_mouvements and self.code_session:
                self._charger_mouvements_stock(self.code_session)
        
        self.panier_widget._finaliser_facture = finaliser_avec_actualisation
        
        # Exposition des widgets du panier pour compatibilitÃ©
        self.combo_fournisseur = self.panier_widget.combo_fournisseur
        self.combo_produit = self.panier_widget.combo_produit
        self.input_designation = self.panier_widget.input_designation
        self.input_quantite = self.panier_widget.input_quantite
        self.input_prix = self.panier_widget.input_prix
        self.input_date_exp = self.panier_widget.input_date_exp
        self.btn_ajouter_panier = self.panier_widget.btn_ajouter_panier
        self.badge_panier = self.panier_widget.badge_panier
        self.container_panier = self.panier_widget.container_panier
        self.layout_lignes_panier = self.panier_widget.layout_lignes_panier
        self.lbl_total_facture = self.panier_widget.lbl_total_facture
        self.btn_finaliser = self.panier_widget.btn_finaliser
        self.btn_annuler_facture = self.panier_widget.btn_annuler_facture

        # Cadre droit : liste des produits + bouton d'ouverture panier
        self.frame_stock_detail = self._creer_cadre_stock_detail()
        self._setup_panier_overlay()

        bottom_layout.addWidget(self.frame_mouvements, 2)
        bottom_layout.addWidget(self.frame_stock_detail, 3)
        self.main_layout.addLayout(bottom_layout)

    # â”€â”€â”€ Cadre gÃ©nÃ©rique arrondi â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _creer_cadre_arrondi(self, titre: str, icone_name: str) -> AnimatedFrame:
        c = theme_manager.colors()
        frame = AnimatedFrame()
        frame.setStyleSheet(ProduitStyles.card())
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon(icone_name, color=c['primary']).pixmap(QSize(16, 16))
        )
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        title_lbl = QLabel(titre)
        title_lbl.setStyleSheet(
            f"font-weight: bold; color: {c['primary']}; font-size: 12px; border: none;"
        )
        header.addWidget(icon_lbl)
        header.addSpacing(6)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {c['border']}; border: none;")
        layout.addWidget(sep)

        frame._icon_name = icone_name
        frame._icon_lbl = icon_lbl
        frame._title_lbl = title_lbl
        frame._separator = sep
        return frame

    def _creer_cadre_stock_detail(self) -> AnimatedFrame:
        """Crée le panneau droit avec la liste des produits en stock (cards en grille)."""
        c = theme_manager.colors()
        frame = AnimatedFrame()
        frame.setStyleSheet(ProduitStyles.card())
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            qta.icon("fa5s.box-open", color=c['primary']).pixmap(QSize(16, 16))
        )
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        title_lbl = QLabel("Produits en Stock")
        title_lbl.setStyleSheet(
            f"font-weight: bold; color: {c['primary']}; font-size: 12px; border: none;"
        )

        self.btn_ouvrir_panier = QPushButton(
            qta.icon("fa5s.cart-plus", color=c['text_inverse']), " Ouvrir Panier"
        )
        self.btn_ouvrir_panier.setFixedHeight(34)
        self.btn_ouvrir_panier.setMinimumWidth(130)
        self.btn_ouvrir_panier.setStyleSheet(ProduitStyles.button_primary())
        self.btn_ouvrir_panier.setCursor(Qt.PointingHandCursor)
        self.btn_ouvrir_panier.setToolTip("Ouvrir le panier d'approvisionnement")
        self.btn_ouvrir_panier.clicked.connect(self._ouvrir_panier_overlay)

        header.addWidget(icon_lbl)
        header.addSpacing(6)
        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(self.btn_ouvrir_panier)
        layout.addLayout(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {c['border']}; border: none;")
        layout.addWidget(sep)

        # Zone scrollable pour les cards produits en grille
        from PySide6.QtWidgets import QScrollArea, QGridLayout
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
        """)
        scroll_area.verticalScrollBar().setStyleSheet(ProduitStyles.scrollbar())
        
        # Container pour la grille de cards
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.grid_produits = QGridLayout(container)
        self.grid_produits.setContentsMargins(5, 5, 5, 5)
        self.grid_produits.setSpacing(10)
        self.grid_produits.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

        frame._icon_name = "fa5s.box-open"
        frame._icon_lbl = icon_lbl
        frame._title_lbl = title_lbl
        frame._separator = sep
        return frame

    def _setup_panier_overlay(self) -> None:
        """PrÃ©pare le panneau panier glissant (overlay) pleine largeur."""
        self.panel_panier_overlay = QFrame(self)
        self.panel_panier_overlay.setAttribute(Qt.WA_StyledBackground, True)
        c_ov = theme_manager.colors()
        self.panel_panier_overlay.setStyleSheet(
            f"background-color: {c_ov['bg_card']}; border-radius: 18px;"
            f" border: 1px solid {c_ov['border']};"
        )

        overlay_layout = QVBoxLayout(self.panel_panier_overlay)
        overlay_layout.setContentsMargins(14, 12, 14, 12)
        overlay_layout.setSpacing(10)

        header = QHBoxLayout()
        titre = QLabel("Panier d'approvisionnement")
        titre.setStyleSheet(
            f"font-weight: bold; color: {c_ov['primary']}; font-size: 12px; border: none;"
        )
        self._overlay_titre = titre
        header.addWidget(titre)
        header.addStretch()
        self.btn_fermer_panier = QPushButton(qta.icon("fa5s.times", color=c_ov['text_inverse']), " Fermer")
        self.btn_fermer_panier.setFixedHeight(30)
        self.btn_fermer_panier.setMinimumWidth(90)
        self.btn_fermer_panier.setStyleSheet(
            f"background-color: {c_ov['danger']}; color: {c_ov['text_inverse']};"
            "border-radius: 10px; font-weight: bold; font-size: 10px;"
        )
        self.btn_fermer_panier.setCursor(Qt.PointingHandCursor)
        self.btn_fermer_panier.clicked.connect(self._fermer_panier_overlay)
        header.addWidget(self.btn_fermer_panier)
        overlay_layout.addLayout(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {c_ov['border']}; border: none;")
        self._overlay_sep = sep
        overlay_layout.addWidget(sep)

        # Panier produit (large et espacÃ©)
        overlay_layout.addWidget(self.panier_widget, 1)

        self.panel_panier_overlay.raise_()
        self.panel_panier_overlay.hide()
        self._ajuster_panier_overlay()
        
        # Créer aussi l\'overlay de paiement
        self._setup_payment_overlay()

    def _ajuster_panier_overlay(self) -> None:
        """Ajuste la taille/position du panneau panier glissant."""
        if not hasattr(self, 'panel_panier_overlay') or not self.panel_panier_overlay:
            return

        if not hasattr(self, 'main_layout') or not self.main_layout:
            return

        margins = self.main_layout.contentsMargins()
        x = 0
        w = self.width()
        if w <= 0:
            return

        y = self._overlay_top_y()
        h = self.height() - y - margins.bottom()
        if h <= 0:
            return

        self.panel_panier_overlay.setFixedSize(w, h)
        if self._panier_overlay_visible:
            self.panel_panier_overlay.move(x, y)
        else:
            self.panel_panier_overlay.move(x - w, y)
    def _setup_payment_overlay(self) -> None:
        """Prépare le panneau de paiement glissant (overlay) pleine largeur."""
        from views.facturation.patient.panier.components.payment_slide_panel import PaymentSlidePanel
        
        self.panel_payment_overlay = QFrame(self)
        self.panel_payment_overlay.setAttribute(Qt.WA_StyledBackground, True)
        c_ov = theme_manager.colors()
        self.panel_payment_overlay.setStyleSheet(
            f"background-color: {c_ov['bg_card']}; border-radius: 18px;"
            f" border: 1px solid {c_ov['border']};"
        )

        overlay_layout = QVBoxLayout(self.panel_payment_overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)

        # Créer le panneau de paiement DIRECTEMENT dans l'overlay
        self._payment_panel = PaymentSlidePanel(self)
        overlay_layout.addWidget(self._payment_panel)

        self.panel_payment_overlay.raise_()
        self.panel_payment_overlay.hide()
        self._payment_overlay_visible = False
        self._payment_anim = None


    def _overlay_top_y(self) -> int:
        """Calcule la position Y de l'overlay (niveau 2Ã¨me ligne des cards)."""
        try:
            if hasattr(self, 'statistiques_widget') and self.statistiques_widget:
                cards = [
                    self.card_expires, self.card_bientot, self.card_valides,
                    self.card_valeur, self.card_liquide, self.card_pommade,
                    self.card_comprime
                ]
                positions = []
                for card in cards:
                    if card:
                        pos = card.mapTo(self, QPoint(0, 0))
                        positions.append(pos.y())
                if positions:
                    positions.sort()
                    rows = []
                    for y in positions:
                        if not rows or abs(y - rows[-1]) > 8:
                            rows.append(y)
                    if len(rows) >= 2:
                        return rows[1]
                    # Une seule ligne de cards
                    return self.statistiques_widget.geometry().bottom() + 8
        except Exception:
            pass
        # Fallback: en dessous des statistiques si prÃ©sent
        if hasattr(self, 'statistiques_widget') and self.statistiques_widget:
            return self.statistiques_widget.geometry().bottom() + 8
        return 0

    def _animer_panier_overlay(self, ouvrir: bool) -> None:
        """Anime l'ouverture/fermeture du panneau panier."""
        if not hasattr(self, 'panel_panier_overlay') or not self.panel_panier_overlay:
            return
        if ouvrir and self._panier_overlay_visible:
            return
        if not ouvrir and not self._panier_overlay_visible:
            return

        self._ajuster_panier_overlay()
        margins = self.main_layout.contentsMargins()
        x = 0
        w = self.width()
        y = self._overlay_top_y()

        if ouvrir:
            self.panel_panier_overlay.show()
            self.panel_panier_overlay.raise_()
            start_pos = QPoint(x - w, y) if not self._panier_overlay_visible else self.panel_panier_overlay.pos()
            end_pos = QPoint(x, y)
        else:
            start_pos = self.panel_panier_overlay.pos()
            end_pos = QPoint(x - w, y)

        self._panier_anim = QPropertyAnimation(self.panel_panier_overlay, b"pos", self)
        self._panier_anim.setDuration(320)
        self._panier_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._panier_anim.setStartValue(start_pos)
        self._panier_anim.setEndValue(end_pos)

        if not ouvrir:
            self._panier_anim.finished.connect(self.panel_panier_overlay.hide)

        self._panier_anim.start()
        self._panier_overlay_visible = ouvrir

    def _ouvrir_panier_overlay(self) -> None:
        """Ouvre le panneau panier avec animation."""
        self._animer_panier_overlay(True)

    def _fermer_panier_overlay(self) -> None:
        """Ferme le panneau panier avec animation."""
        self._animer_panier_overlay(False)
    
    def _animer_payment_overlay(self, ouvrir: bool) -> None:
        """Anime l'ouverture/fermeture du panneau de paiement."""
        print(f"[GestionProduitsView] _animer_payment_overlay appele: ouvrir={ouvrir}")
        
        if not hasattr(self, 'panel_payment_overlay') or not self.panel_payment_overlay:
            print("[GestionProduitsView] ERREUR: panel_payment_overlay n'existe pas")
            return
        
        if ouvrir and self._payment_overlay_visible:
            print("[GestionProduitsView] Panneau deja ouvert")
            return
        if not ouvrir and not self._payment_overlay_visible:
            print("[GestionProduitsView] Panneau deja ferme")
            return

        self._ajuster_panier_overlay()
        margins = self.main_layout.contentsMargins()
        x = 0
        w = self.width()
        y = self._overlay_top_y()

        print(f"[GestionProduitsView] Dimensions: w={w}, y={y}")

        if ouvrir:
            self.panel_payment_overlay.show()
            self.panel_payment_overlay.raise_()
            print("[GestionProduitsView] panel_payment_overlay.show() et raise_() appeles")
            # Afficher aussi le contenu du panneau
            self._payment_panel.show()
            print("[GestionProduitsView] _payment_panel.show() appele")
            start_pos = QPoint(x - w, y)
            end_pos = QPoint(x, y)
        else:
            start_pos = self.panel_payment_overlay.pos()
            end_pos = QPoint(x - w, y)

        h = self.height() - y - margins.bottom()
        self.panel_payment_overlay.setFixedSize(w, h)
        print(f"[GestionProduitsView] Taille panneau: {w}x{h}")

        self._payment_anim = QPropertyAnimation(self.panel_payment_overlay, b"pos", self)
        self._payment_anim.setDuration(320)
        self._payment_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._payment_anim.setStartValue(start_pos)
        self._payment_anim.setEndValue(end_pos)

        if not ouvrir:
            # ✅ CORRECTION: S'assurer que le panneau est bien caché après l'animation
            def hide_panel_completely():
                print("[GestionProduitsView] Animation terminée - Masquage du panneau")
                self.panel_payment_overlay.hide()
                self._payment_panel.hide()
                # Forcer le rafraîchissement de l'interface
                self.update()
                self.repaint()
            
            self._payment_anim.finished.connect(hide_panel_completely)

        self._payment_anim.start()
        print(f"[GestionProduitsView] Animation demarree de {start_pos} vers {end_pos}")
        self._payment_overlay_visible = ouvrir

    def _ouvrir_payment_overlay(self) -> None:
        """Ouvre le panneau de paiement avec animation."""
        self._animer_payment_overlay(True)

    def _fermer_payment_overlay(self) -> None:
        """Ferme le panneau de paiement avec animation."""
        print("[GestionProduitsView] _fermer_payment_overlay appelé")
        self._animer_payment_overlay(False)
        
        # ✅ CORRECTION: Actualiser l'interface après fermeture
        if hasattr(self, 'code_session') and self.code_session:
            print("[GestionProduitsView] Actualisation de l'interface après fermeture du paiement")
            # Actualiser les statistiques
            if hasattr(self, 'statistiques_widget') and self.statistiques_widget:
                self.statistiques_widget.actualiser()
            # Actualiser le tableau des mouvements
            if hasattr(self, 'table_mouvements') and self.table_mouvements:
                self._charger_mouvements_stock(self.code_session)
            # Actualiser la liste des produits
            self._charger_stock_detail_liste(self.code_session)
            # Mettre à jour le badge de notification
            self._mettre_a_jour_badge_notification()


    # â”€â”€â”€ Table mouvements de stock â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _setup_table_mouvements(self):
        """Configure le tableau des mouvements d'approvisionnement du stock."""
        self.table_mouvements = QTableWidget(0, 5)
        self.table_mouvements.setHorizontalHeaderLabels([
            "Code", "Produit", "Type", "Date Expiration", "QuantitÃ© EntrÃ©e"
        ])
        self.table_mouvements.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_mouvements.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._appliquer_style_scrollbar(self.table_mouvements)

        header = self.table_mouvements.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Code
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Produit (extensible)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Date Expiration
        header.setSectionResizeMode(4, QHeaderView.Fixed)             # QuantitÃ© EntrÃ©e
        self.table_mouvements.setColumnWidth(4, 120)

        self.table_mouvements.setStyleSheet(ProduitStyles.table())
        self.table_mouvements.verticalHeader().setVisible(False)
        self.table_mouvements.setAlternatingRowColors(True)

        self.frame_mouvements.layout().addWidget(self.table_mouvements)
    
    def _charger_mouvements_stock(self, code_session: str):
        """
        Charge les mouvements d'approvisionnement du stock dans le tableau.
        Utilise la mÃ©thode lister_par_session du contrÃ´leur panier.
        
        Args:
            code_session: Code de la session active
        """
        if not code_session:
            print("[GestionProduitsView] Code session invalide pour charger les mouvements")
            return
        
        # RÃ©cupÃ©rer le contrÃ´leur panier
        from controllers.controleur_panierFourni import PanierFactureFourniControleur
        panier_ctrl = PanierFactureFourniControleur()
        
        # RÃ©cupÃ©rer les mouvements
        mouvements = panier_ctrl.lister_par_session(code_session)
        
        print(f"[GestionProduitsView] {len(mouvements)} mouvements rÃ©cupÃ©rÃ©s")
        
        # Vider le tableau
        self.table_mouvements.setRowCount(0)
        
        if not mouvements:
            print("[GestionProduitsView] Aucun mouvement Ã  afficher")
            return
        
        # Remplir le tableau
        for mouvement in mouvements:
            row_position = self.table_mouvements.rowCount()
            self.table_mouvements.insertRow(row_position)
            
            # Colonne 0 : Code produit
            code_produit = mouvement.code_produit if hasattr(mouvement, 'code_produit') else ''
            self.table_mouvements.setItem(row_position, 0, QTableWidgetItem(code_produit))
            
            # Colonne 1 : Libelle (nom du produit)
            # La mÃ©thode retourne des objets avec attributs supplÃ©mentaires via jointure
            libelle = ''
            if hasattr(mouvement, 'designation'):
                libelle = mouvement.designation
            elif hasattr(mouvement, 'libelle'):
                libelle = mouvement.libelle
            self.table_mouvements.setItem(row_position, 1, QTableWidgetItem(libelle))
            
            # Colonne 2 : Type
            type_produit = ''
            if hasattr(mouvement, 'type'):
                type_produit = mouvement.type
            self.table_mouvements.setItem(row_position, 2, QTableWidgetItem(type_produit))
            
            # Colonne 3 : Date expiration
            date_exp = ''
            if hasattr(mouvement, 'date_expiration') and mouvement.date_expiration:
                date_exp = mouvement.date_expiration.strftime('%d/%m/%Y') if hasattr(mouvement.date_expiration, 'strftime') else str(mouvement.date_expiration)
            self.table_mouvements.setItem(row_position, 3, QTableWidgetItem(date_exp))
            
            # Colonne 4 : QuantitÃ© entrÃ©e
            quantite = '0'
            if hasattr(mouvement, 'quantite_four'):
                quantite = str(mouvement.quantite_four)
            item_qte = QTableWidgetItem(quantite)
            item_qte.setTextAlignment(Qt.AlignCenter)
            self.table_mouvements.setItem(row_position, 4, item_qte)
        
        print(f"[GestionProduitsView] âœ… Tableau rempli avec {self.table_mouvements.rowCount()} lignes")

    # =========================================================================
    # MÃ‰THODE UTILITAIRE POUR CRÃ‰ER LIGNE PANIER (dÃ©lÃ©gation au widget)
    # =========================================================================

    def _creer_ligne_panier(self, designation: str, quantite: int,
                            prix: float, date_exp: str) -> QFrame:
        """
        CrÃ©e une ligne visuelle dans la liste du panier.
        DÃ©lÃ¨gue au composant PanierProduitWidget.
        """
        return self.panier_widget.creer_ligne_panier(designation, quantite, prix, date_exp)

    # =========================================================================
    # UTILITAIRES
    # =========================================================================

    def _appliquer_style_scrollbar(self, widget):
        widget.verticalScrollBar().setStyleSheet(ProduitStyles.scrollbar())

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # GESTION DES FORMULAIRES PRODUITS (Pattern MVC)
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def ouvrir_formulaire_nouveau_produit(self):
        
        # VÃ©rification de l'injection du contrÃ´leur
        if not self.controleur:
            QMessageBox.warning(
                self, 
                "Erreur", 
                "Le contrÃ´leur n'est pas initialisÃ©. Impossible d'ouvrir le formulaire."
            )
            return
        
        # CrÃ©ation du formulaire en mode "Nouveau produit" (produit_obj=None)
        formulaire = ProduitFormDialog(
            controleur=self.controleur,
            produit_obj=None,  # None = Mode crÃ©ation
            parent=self
        )
        
        # Ouverture modale du formulaire
        # exec() bloque l'exÃ©cution jusqu'Ã  la fermeture du formulaire
        resultat = formulaire.exec()
        
        # Si l'utilisateur a validÃ© (cliquÃ© sur "Enregistrer")
        if resultat == ProduitFormDialog.Accepted:
            # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
            # RAFRAÃŽCHISSEMENT DE LA VUE
            # Ici, vous devez appeler votre mÃ©thode de rafraÃ®chissement
            # Exemples possibles :
            # - self.charger_liste_produits()
            # - self.actualiser_table_produits()
            # - self.rafraichir_donnees()
            # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
            print("[INFO] Nouveau produit crÃ©Ã© avec succÃ¨s")
            # TODO: Appeler votre mÃ©thode de rafraÃ®chissement ici
            # self.charger_liste_produits()

    

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # CHARGEMENT DES DONNÃ‰ES
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    def _charger_stock_detail_liste(self, code_session: str) -> None:
        """Charge la liste des produits (cards en grille) dans le panneau droit."""
        if not self.panier_ctrl or not hasattr(self, 'grid_produits'):
            return
        try:
            # Vider la grille
            while self.grid_produits.count():
                item = self.grid_produits.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Récupérer les produits
            produits = self.panier_ctrl.obtenir_stock_detaille(code_session, limite=30)
            
            if not produits:
                return
            
            # Afficher les produits en grille (2 colonnes)
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
                if col >= 2:  # 2 colonnes
                    col = 0
                    row += 1
                    
        except Exception as e:
            print(f"[GestionProduitsView] Erreur chargement stock detail: {e}")

    def charger_donnees(self, code_session=None):
        """
        Charge les donnÃ©es de la page (produits, statistiques, panier, mouvements).
        AppelÃ© depuis le dashboard lors de l'affichage de la page.
        
        Args:
            code_session: Code de la session active (optionnel)
        """
        if code_session:
            self.code_session = code_session
        
        print(f"[GestionProduitsView] Chargement des donnÃ©es pour la session: {code_session}")
        
        # Charger les statistiques du stock
        if hasattr(self, 'statistiques_widget') and self.statistiques_widget:
            print("[GestionProduitsView] Chargement des statistiques...")
            succes = self.statistiques_widget.charger_statistiques(code_session)
            if succes:
                print("[GestionProduitsView] âœ… Statistiques chargÃ©es avec succÃ¨s")
            else:
                print("[GestionProduitsView] âŒ Ã‰chec du chargement des statistiques")
        
        # Charger la liste des produits (panneau droit)
        self._charger_stock_detail_liste(code_session)

        # Charger les donnÃ©es du panier
        if hasattr(self, 'panier_widget') and self.panier_widget:
            print("[GestionProduitsView] Chargement du panier...")
            self.panier_widget.charger_donnees(code_session)
        
        # Charger les mouvements de stock dans le tableau
        if hasattr(self, 'table_mouvements') and self.table_mouvements:
            print("[GestionProduitsView] Chargement des mouvements de stock...")
            self._charger_mouvements_stock(code_session)
        
        print(f"[GestionProduitsView] âœ… DonnÃ©es chargÃ©es pour la session: {code_session}")
        
        # Mettre Ã  jour le badge de notification
        self._mettre_a_jour_badge_notification()
        
        # Actualiser le panneau factures si ouvert
        if hasattr(self, 'panneau_factures') and self.panneau_factures._ouvert:
            print("[GestionProduitsView] Actualisation du panneau factures...")
            self.panneau_factures.actualiser(code_session)
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # GESTION DES PANNEAUX LATÃ‰RAUX
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    def _ouvrir_panneau_stock(self):
        """
        Ouvre le panneau latÃ©ral de gestion du stock.
        Charge les donnÃ©es pour la session en cours.
        """
        if self.code_session:
            print(f"[GestionProduitsView] Ouverture du panneau stock pour session: {self.code_session}")
            self.panneau_stock.actualiser(self.code_session)
            self.panneau_stock.basculer()
        else:
            QMessageBox.warning(
                self,
                "Session non dÃ©finie",
                "Aucune session active. Veuillez d'abord charger les donnÃ©es."
            )
    
    def _ouvrir_panneau_factures(self):
        """
        Ouvre le panneau latÃ©ral des factures fournisseurs.
        Charge les donnÃ©es pour la session en cours.
        """
        if self.code_session:
            print(f"[GestionProduitsView] Ouverture du panneau factures pour session: {self.code_session}")
            self.panneau_factures.actualiser(self.code_session)
            self.panneau_factures.basculer()
        else:
            QMessageBox.warning(
                self,
                "Session non dÃ©finie",
                "Aucune session active. Veuillez d'abord charger les donnÃ©es."
            )
    
    def _ouvrir_panneau_alertes(self):
        """
        Ouvre le panneau stock sur l'onglet Rupture pour afficher les alertes.
        Le panneau stock contient maintenant tous les onglets d'alertes.
        """
        if self.code_session:
            print(f"[GestionProduitsView] Ouverture du panneau alertes (onglet Rupture) pour session: {self.code_session}")
            self.panneau_stock.actualiser(self.code_session)
            # Ouvrir directement sur l'onglet Rupture
            self.panneau_stock._aller_onglet("rupture")
            self.panneau_stock.ouvrir()
        else:
            QMessageBox.warning(
                self,
                "Session non dÃ©finie",
                "Aucune session active. Veuillez d'abord charger les donnÃ©es."
            )

    
    def show_payment_panel(self):
        """Affiche le panneau de paiement apres fermeture du panier."""
        print("[GestionProduitsView] show_payment_panel appele")
        
        # Verifier que les donnees sont disponibles
        if not hasattr(self.panier_widget, '_payment_facture_data'):
            print("[GestionProduitsView] Erreur: Donnees de paiement non disponibles")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Donnees de paiement non disponibles")
            return
        
        # Charger les donnees dans le panneau de paiement
        print("[GestionProduitsView] Chargement des donnees dans le panneau")
        self._payment_panel.load_data(
            self.panier_widget._payment_facture_data,
            self.panier_widget._payment_produits_data,
            self.panier_widget._payment_fournisseur_data
        )
        
        # Fermer le panier d'abord
        if self._panier_overlay_visible:
            print("[GestionProduitsView] Fermeture du panier")
            self._fermer_panier_overlay()
        
        # Ouvrir le panneau de paiement immediatement (pas de timer)
        print("[GestionProduitsView] Ouverture du panneau de paiement")
        self._ouvrir_payment_overlay()