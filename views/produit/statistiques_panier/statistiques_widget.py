"""
Widget Statistiques Stock - Version Refactorisée COMPLÈTE.
Architecture : MVC + Composition + Separation of Concerns.
Responsabilité : Orchestration des composants et gestion du workflow.
"""

import logging
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt

# Composants UI
from .components import StatCard, DonutCard
from .components.stock_table_card import StockTableCard
from .styles.statistiques_styles import StatistiquesStyles
from .handlers.statistiques_loader import StatistiquesDataLoader
from .handlers.ui_updater import UIUpdater
from views.shared.theme_manager import theme_manager


class StatistiquesStockWidget(QWidget):
    """
    Widget contenant toutes les statistiques et graphes du stock.
    Version refactorisée avec architecture modulaire COMPLÈTE.
    
    Responsabilités :
    - Orchestration des composants UI
    - Gestion du workflow métier
    - Communication avec le contrôleur via handler
    
    Architecture :
    - MVC : Injection du contrôleur
    - Composition : Utilisation de composants modulaires
    - Service Layer : Handlers pour la logique
    """
    
    def __init__(self, panier_ctrl=None, parent=None, show_stock_detail: bool = True):
        """
        Initialise le widget avec injection du contrôleur.
        
        Args:
            panier_ctrl: Instance de PanierFactureFourniControleur (injection)
            parent: Widget parent Qt
        """
        super().__init__(parent)
        
        print("[StatistiquesWidget] Initialisation version refactorisée")
        
        # Injection du contrôleur (Architecture MVC)
        self.panier_ctrl = panier_ctrl
        self.show_stock_detail = show_stock_detail
        
        # Logger pour traçabilité
        self.logger = logging.getLogger(__name__)
        self.logger.info("[StatistiquesWidget] Initialisation")
        
        # État interne
        self.code_session = None
        self._donnees_chargees = False
        
        # Initialisation des handlers (lazy loading)
        self._data_loader = None
        self._ui_updater = UIUpdater()
        
        # Références aux composants UI (seront créés dans _init_ui)
        # Plus besoin de cards_expiration et cards_type
        
        # Construction de l'interface
        self._init_ui()

        # Thème
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)
    
    @property
    def data_loader(self):
        """Lazy loading du handler de données."""
        if self._data_loader is None:
            if not self.panier_ctrl:
                self.logger.warning("[StatistiquesWidget] Contrôleur non injecté")
                return None
            
            self._data_loader = StatistiquesDataLoader(self.panier_ctrl)
        
        return self._data_loader
    
    def _init_ui(self) -> None:
        """Initialisation de l'interface des statistiques."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Toujours afficher le dashboard (pas de cards compactes)
        self._setup_statistique_dashboard(layout)
    
    def _setup_statistique_dashboard(self, parent_layout: QVBoxLayout) -> None:
        """Crée la vue de statistiques avancée correspondant à la maquette."""
        _c = theme_manager.colors()

        # Ligne du haut : 2 graphiques donut
        row_charts = QHBoxLayout()
        row_charts.setSpacing(10)
        row_charts.setContentsMargins(0, 0, 0, 0)

        self.expiration_chart, self.expiration_donut, self.expiration_total_lbl, self.expiration_legend_labels = self._create_donut_panel(
            title="Répartition des quantités par statut d'expiration",
            total_label="4 850",
            pourcentage=0,
            couleur=_c['success'],
            icone="fa5s.skull-crossbones",
            legend_items=[
                ("Expirés", _c['danger']),
                ("Bientôt (-30j)", _c['warning']),
                ("Validés (+30j)", _c['success'])
            ]
        )
        self.type_chart, self.type_donut, self.type_total_lbl, self.type_legend_labels = self._create_donut_panel(
            title="Répartition des quantités par type de produit",
            total_label="4 850",
            pourcentage=0,
            couleur=_c['info'],
            icone="fa5s.box-open",
            legend_items=[
                ("Liquide", _c['info']),
                ("Pommade", _c['accent']),
                ("Comprimé", _c['warning'])
            ]
        )

        row_charts.addWidget(self.expiration_chart, 1)
        row_charts.addWidget(self.type_chart, 1)
        parent_layout.addLayout(row_charts, 1)

        # Ligne du bas : Alertes + Stock détaillé
        row_bottom = QHBoxLayout()
        row_bottom.setSpacing(10)
        row_bottom.setContentsMargins(0, 0, 0, 0)

        self.alert_panel = self._create_alert_panel()
        self.stock_table_card = StockTableCard()

        row_bottom.addWidget(self.alert_panel, 1)
        row_bottom.addWidget(self.stock_table_card, 1)
        parent_layout.addLayout(row_bottom, 1)

    def _create_donut_panel(self, title: str, total_label: str, pourcentage: int,
                            couleur: str, icone: str, legend_items: list):
        from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget
        from PySide6.QtCore import Qt

        frame = QFrame()
        c = theme_manager.colors()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border_light']};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(
            f"color: {c['text_primary']}; font-weight: bold; font-size: 13px; border: none; background: transparent;"
        )
        layout.addWidget(title_lbl)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # Camembert au centre avec taille augmentée
        from .components.multi_segment_donut import MultiSegmentDonut
        donut_widget = MultiSegmentDonut(
            segments=[],
            total=0,
            taille=160
        )
        donut_widget.setFixedSize(160, 160)

        # Partie gauche : Légende
        left = QWidget()
        left.setStyleSheet("background: transparent; border: none;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        left_layout.setAlignment(Qt.AlignVCenter)

        # Légende avec valeurs et pourcentages juste après le nom
        legend_container = QWidget()
        legend_container.setStyleSheet("background: transparent; border: none;")
        legend_layout = QVBoxLayout(legend_container)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(10)

        # Stocker les labels de légende pour mise à jour dynamique
        legend_labels = []
        for label_text, label_color in legend_items:
            legend_row = QHBoxLayout()
            legend_row.setSpacing(8)
            legend_row.setContentsMargins(0, 0, 0, 0)
            
            # Puce colorée
            bullet = QLabel(f"<span style='font-size:18px; color:{label_color};'>■</span>")
            bullet.setStyleSheet("border: none; background: transparent;")
            bullet.setFixedWidth(20)
            
            # Nom du statut
            name_lbl = QLabel(label_text)
            name_lbl.setStyleSheet(
                f"color: {c['text_secondary']}; font-size: 12px; border: none; background: transparent;"
            )
            
            # Valeur et pourcentage (sera mis à jour dynamiquement)
            value_lbl = QLabel("0 (0%)")
            value_lbl.setStyleSheet(
                f"color: {c['text_primary']}; font-size: 12px; font-weight: 600; border: none; background: transparent;"
            )
            
            legend_row.addWidget(bullet)
            legend_row.addWidget(name_lbl)
            legend_row.addWidget(value_lbl)
            legend_row.addStretch()
            
            legend_layout.addLayout(legend_row)
            legend_labels.append(value_lbl)

        left_layout.addWidget(legend_container)

        # Partie droite : Total au centre du camembert
        right = QWidget()
        right.setStyleSheet("background: transparent; border: none;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignCenter)
        
        total_container = QWidget()
        total_container.setStyleSheet("background: transparent; border: none;")
        total_container_layout = QVBoxLayout(total_container)
        total_container_layout.setContentsMargins(0, 0, 0, 0)
        total_container_layout.setSpacing(2)
        total_container_layout.setAlignment(Qt.AlignCenter)
        
        total_label_text = QLabel("Total")
        total_label_text.setAlignment(Qt.AlignCenter)
        total_label_text.setStyleSheet(
            f"color: {c['text_muted']}; font-size: 11px; border: none; background: transparent;"
        )
        
        total_lbl = QLabel(total_label)
        total_lbl.setAlignment(Qt.AlignCenter)
        total_lbl.setStyleSheet(
            f"color: {c['text_primary']}; font-weight: bold; font-size: 24px; border: none; background: transparent;"
        )
        
        total_label_text2 = QLabel("quantité")
        total_label_text2.setAlignment(Qt.AlignCenter)
        total_label_text2.setStyleSheet(
            f"color: {c['text_muted']}; font-size: 11px; border: none; background: transparent;"
        )
        
        total_container_layout.addWidget(total_label_text)
        total_container_layout.addWidget(total_lbl)
        total_container_layout.addWidget(total_label_text2)
        
        right_layout.addWidget(total_container)

        content_layout.addWidget(left, 1)
        content_layout.addWidget(donut_widget, alignment=Qt.AlignCenter)
        content_layout.addWidget(right, 1)

        layout.addLayout(content_layout)

        return frame, donut_widget, total_lbl, legend_labels

    def _create_alert_panel(self):
        from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QFrame
        from PySide6.QtCore import Qt

        c = theme_manager.colors()
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border_light']};
                border-radius: 12px;
            }}
        """)

        outer = QVBoxLayout(frame)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        title_lbl = QLabel("ALERTES & NOTIFICATIONS")
        title_lbl.setStyleSheet(
            f"color: {c['text_primary']}; font-weight: bold; font-size: 13px; border: none; background: transparent;"
        )
        outer.addWidget(title_lbl)

        self.alert_items = {}
        for key, text, color_value in [
            ("ruptures", "produits en rupture de stock", c['danger']),
            ("a_expirer", "lots à expirer dans les 30 jours", c['warning']),
            ("expires", "lots déjà expirés", c['danger']),
            ("stock_faible", "stock faible (< 10 unités)", c['accent'])
        ]:
            row = QHBoxLayout()
            row.setSpacing(10)
            
            badge = QLabel("0")
            badge.setAlignment(Qt.AlignCenter)
            badge.setFixedSize(32, 32)
            badge.setStyleSheet(
                f"background: {color_value}22; color: {color_value}; font-weight: bold; border-radius: 16px; font-size: 13px;"
            )
            
            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet(
                f"color: {c['text_secondary']}; font-size: 12px; border: none; background: transparent;"
            )

            row.addWidget(badge)
            row.addWidget(label, 1)
            outer.addLayout(row)
            self.alert_items[key] = badge

        outer.addStretch()

        self.alert_link = QLabel(
            f"<a href='#' style='color: {c['primary']}; font-weight: bold; text-decoration: none;'>Voir la liste →</a>"
        )
        self.alert_link.setTextFormat(Qt.RichText)
        self.alert_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.alert_link.setOpenExternalLinks(False)
        self.alert_link.setStyleSheet("border: none; background: transparent; font-size: 12px;")
        outer.addWidget(self.alert_link, alignment=Qt.AlignLeft)

        return frame

    def _mettre_a_jour_donut_charts(self, dto) -> None:
        """Met à jour les graphiques donut avec les données du DTO."""
        total_qte = dto.nb_expires + dto.nb_bientot_expires + dto.nb_valides
        total_types = dto.stock_liquide + dto.stock_pommade + dto.stock_comprime

        # Mettre à jour les totaux
        self.expiration_total_lbl.setText(f"{total_qte:,}".replace(",", " "))
        self.type_total_lbl.setText(f"{total_types:,}".replace(",", " "))

        c = theme_manager.colors()
        
        # Graphique expiration : segments pour Expirés, Bientôt, Valides
        segments_expiration = [
            (dto.pct_expires, c['danger'], "Expirés"),
            (dto.pct_bientot, c['warning'], "Bientôt"),
            (dto.pct_valides, c['success'], "Valides")
        ]
        self.expiration_donut.set_segments(segments_expiration, total_qte)
        
        # Mettre à jour les légendes avec valeurs et pourcentages - Expiration
        if hasattr(self, 'expiration_legend_labels'):
            valeurs_exp = [dto.nb_expires, dto.nb_bientot_expires, dto.nb_valides]
            pcts_exp = [dto.pct_expires, dto.pct_bientot, dto.pct_valides]
            for i, label in enumerate(self.expiration_legend_labels):
                if i < len(valeurs_exp):
                    val = valeurs_exp[i]
                    pct = pcts_exp[i]
                    label.setText(f"{val:,} ({pct:.1f}%)".replace(",", " "))
        
        # Graphique type : segments pour Liquide, Pommade, Comprimé
        segments_type = [
            (dto.pct_liquide, c['info'], "Liquide"),
            (dto.pct_pommade, c['accent'], "Pommade"),
            (dto.pct_comprime, c['warning'], "Comprimé")
        ]
        self.type_donut.set_segments(segments_type, total_types)
        
        # Mettre à jour les légendes avec valeurs et pourcentages - Type
        if hasattr(self, 'type_legend_labels'):
            valeurs_type = [dto.stock_liquide, dto.stock_pommade, dto.stock_comprime]
            pcts_type = [dto.pct_liquide, dto.pct_pommade, dto.pct_comprime]
            for i, label in enumerate(self.type_legend_labels):
                if i < len(valeurs_type):
                    val = valeurs_type[i]
                    pct = pcts_type[i]
                    label.setText(f"{val:,} ({pct:.1f}%)".replace(",", " "))
    
    # =========================================================================
    # MÉTHODES PUBLIQUES - API DU WIDGET
    # =========================================================================
    
    def charger_statistiques(self, code_session: str) -> bool:
        """
        Charge toutes les statistiques pour une session donnée.
        Point d'entrée principal pour le chargement des données.
        
        Args:
            code_session: Code de la session active
        
        Returns:
            bool: True si le chargement a réussi, False sinon
        
        Usage:
            >>> widget = StatistiquesStockWidget(panier_ctrl=controleur)
            >>> widget.charger_statistiques("SESSION_001")
        """
        self.logger.info(f"[StatistiquesWidget] Chargement statistiques session={code_session}")
        
        # Validation
        if not code_session:
            self._afficher_erreur("Code session invalide")
            return False
        
        if not self.panier_ctrl:
            self._afficher_erreur(
                "Contrôleur non initialisé",
                "Le contrôleur panier n'a pas été injecté lors de l'initialisation."
            )
            return False
        
        # Sauvegarder la session
        self.code_session = code_session
        
        # Charger via le handler
        ok, dto, msg = self.data_loader.charger_statistiques_completes(code_session)
        
        if not ok:
            self._afficher_erreur("Erreur de chargement", msg)
            self._afficher_donnees_vides()
            return False
        
        # Mettre à jour l'interface avec les données via le handler UI
        self._mettre_a_jour_interface(dto)
        self._donnees_chargees = True
        
        self.logger.info("[StatistiquesWidget] Statistiques chargées avec succès")
        return True
    
    def actualiser(self) -> bool:
        """
        Actualise les statistiques avec les dernières données.
        Recharge les données pour la session en cours.
        
        Returns:
            bool: True si l'actualisation a réussi, False sinon
        
        Usage:
            >>> widget.actualiser()  # Recharge les données
        """
        if not self.code_session:
            self.logger.warning("[StatistiquesWidget] Aucune session active pour actualisation")
            return False
        
        self.logger.info("[StatistiquesWidget] Actualisation des statistiques")
        return self.charger_statistiques(self.code_session)
    
    def reinitialiser(self) -> None:
        """
        Réinitialise le widget à son état initial.
        Efface toutes les données affichées.
        """
        self.logger.info("[StatistiquesWidget] Réinitialisation")
        
        self.code_session = None
        self._donnees_chargees = False
        self._afficher_donnees_vides()
    
    # =========================================================================
    # GESTION DES ERREURS
    # =========================================================================
    
    def _afficher_erreur(self, titre: str, message: str = "") -> None:
        """Affiche un message d'erreur à l'utilisateur."""
        self.logger.error(f"[StatistiquesWidget] {titre}: {message}")
        if message:
            QMessageBox.warning(self, titre, message)
    
    # =========================================================================
    # MÉTHODES PRIVÉES - MISE À JOUR INTERFACE
    # =========================================================================
    
    def _mettre_a_jour_interface(self, dto) -> None:
        """
        Met à jour tous les composants de l'interface avec les données du DTO.
        
        Args:
            dto: StatistiquesDTO contenant toutes les données
        """
        self.logger.debug("[StatistiquesWidget] Mise à jour interface")
        
        try:
            if hasattr(self, 'stock_table_card') and self.stock_table_card:
                self.stock_table_card.charger_produits(dto.stock_detaille)
            if hasattr(self, 'expiration_donut') and hasattr(self, 'type_donut'):
                self._mettre_a_jour_donut_charts(dto)
            if hasattr(self, 'alert_items'):
                self._ui_updater.mettre_a_jour_alertes(dto, self.alert_items)
        except Exception as e:
            self.logger.error(f"[StatistiquesWidget] Erreur mise à jour interface: {e}")
            self._afficher_erreur("Erreur d'affichage", str(e))
    
    def _afficher_donnees_vides(self) -> None:
        """Affiche des valeurs vides/zero dans tous les composants."""
        try:
            if hasattr(self, 'stock_table_card') and self.stock_table_card:
                self.stock_table_card.vider()
            if hasattr(self, 'alert_items'):
                self._ui_updater.mettre_a_jour_alertes(
                    type('dto', (), {
                        'nb_ruptures': 0,
                        'nb_lots_a_expirer': 0,
                        'nb_lots_expires': 0,
                        'nb_stock_faible': 0
                    })(),
                    self.alert_items
                )
            if hasattr(self, 'expiration_total_lbl'):
                self.expiration_total_lbl.setText("0")
            if hasattr(self, 'type_total_lbl'):
                self.type_total_lbl.setText("0")
            if hasattr(self, 'expiration_donut'):
                self.expiration_donut.set_segments([], 0)
            if hasattr(self, 'type_donut'):
                self.type_donut.set_segments([], 0)
        except Exception as e:
            self.logger.error(f"[StatistiquesWidget] Erreur affichage donnees vides: {e}")

    # =========================================================================
    # THÈME
    # =========================================================================

    def apply_theme(self):
        """Met à jour les couleurs selon le thème actif."""
        c = theme_manager.colors()
        self.setStyleSheet(f"StatistiquesStockWidget {{ background: {c['bg_main']}; }}")

        panel_style = f"""
            QFrame {{
                background: {c['bg_card']};
                border: 1px solid {c['border_light']};
                border-radius: 12px;
            }}
        """
        for frame in (
            getattr(self, 'expiration_chart', None),
            getattr(self, 'type_chart', None),
            getattr(self, 'alert_panel', None),
        ):
            if frame:
                frame.setStyleSheet(panel_style)

        if hasattr(self, 'stock_table_card'):
            fn = getattr(self.stock_table_card, 'apply_theme', None)
            if fn:
                fn()
