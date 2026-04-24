"""
Widget Statistiques Stock - Version RefactorisÃ©e COMPLÃˆTE.
Architecture : MVC + Composition + Separation of Concerns.
ResponsabilitÃ© : Orchestration des composants et gestion du workflow.
"""

import logging
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox

# Composants UI
from .components import StatCard, DonutCard, StockDetailCard
from .styles.statistiques_styles import StatistiquesStyles
from .handlers.statistiques_loader import StatistiquesDataLoader
from .handlers.ui_updater import UIUpdater
from views.shared.theme_manager import theme_manager


class StatistiquesStockWidget(QWidget):
    """
    Widget contenant toutes les statistiques et graphes du stock.
    Version refactorisÃ©e avec architecture modulaire COMPLÃˆTE.
    
    ResponsabilitÃ©s :
    - Orchestration des composants UI
    - Gestion du workflow mÃ©tier
    - Communication avec le contrÃ´leur via handler
    
    Architecture :
    - MVC : Injection du contrÃ´leur
    - Composition : Utilisation de composants modulaires
    - Service Layer : Handlers pour la logique
    """
    
    def __init__(self, panier_ctrl=None, parent=None, show_stock_detail: bool = True):
        """
        Initialise le widget avec injection du contrÃ´leur.
        
        Args:
            panier_ctrl: Instance de PanierFactureFourniControleur (injection)
            parent: Widget parent Qt
        """
        super().__init__(parent)
        
        print("[StatistiquesWidget] Initialisation version refactorisÃ©e")
        
        # Injection du contrÃ´leur (Architecture MVC)
        self.panier_ctrl = panier_ctrl
        self.show_stock_detail = show_stock_detail
        
        # Logger pour traÃ§abilitÃ©
        self.logger = logging.getLogger(__name__)
        self.logger.info("[StatistiquesWidget] Initialisation")
        
        # Ã‰tat interne
        self.code_session = None
        self._donnees_chargees = False
        
        # Initialisation des handlers (lazy loading)
        self._data_loader = None
        self._ui_updater = UIUpdater()
        
        # RÃ©fÃ©rences aux composants UI (seront crÃ©Ã©s dans _init_ui)
        self.cards_expiration = {}
        self.cards_type = {}
        self.card_detail = None
        
        # Construction de l'interface
        self._init_ui()

        # Thème
        self.apply_theme()
        theme_manager.theme_changed.connect(self.apply_theme)
    
    @property
    def data_loader(self):
        """Lazy loading du handler de donnÃ©es."""
        if self._data_loader is None:
            if not self.panier_ctrl:
                self.logger.warning("[StatistiquesWidget] ContrÃ´leur non injectÃ©")
                return None
            
            self._data_loader = StatistiquesDataLoader(self.panier_ctrl)
        
        return self._data_loader
    
    def _init_ui(self) -> None:
        """Initialisation de l'interface des statistiques."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(0)
        
        # UNE SEULE LIGNE : 7 cards compactes (4 expiration + 3 types)
        self._setup_cards_compactes(layout)
    
    def _setup_cards_compactes(self, parent_layout: QVBoxLayout) -> None:
        """
        CrÃ©e TOUTES les cards (7 au total) sur UNE SEULE LIGNE compacte.
        Pattern : Factory + Composition.
        
        Args:
            parent_layout: Layout parent oÃ¹ ajouter les cards
        """
        layout = QHBoxLayout()
        layout.setSpacing(10)
        
        _c = theme_manager.colors()
        
        # Cards d'expiration (4 cards)
        self.cards_expiration['expires'] = StatCard(
            "ExpirÃ©s",
            "0",
            "fa5s.skull-crossbones",
            _c['danger'],
            compact=True
        )
        
        self.cards_expiration['bientot'] = StatCard(
            "BientÃ´t",
            "0",
            "fa5s.hourglass-half",
            _c['warning'],
            compact=True
        )
        
        self.cards_expiration['valides'] = StatCard(
            "Valides",
            "0",
            "fa5s.check-circle",
            _c['success'],
            compact=True
        )
        
        self.cards_expiration['valeur'] = StatCard(
            "Valeur Stock",
            "0 GNF",
            "fa5s.coins",
            _c['primary'],
            compact=True
        )
        
        # Cards par type (3 cards)
        self.cards_type['liquide'] = StatCard(
            "Liquide",
            "0",
            "fa5s.tint",
            _c['info'],
            compact=True
        )
        
        self.cards_type['pommade'] = StatCard(
            "Pommade",
            "0",
            "fa5s.prescription-bottle",
            _c['accent'],
            compact=True
        )
        
        self.cards_type['comprime'] = StatCard(
            "ComprimÃ©",
            "0",
            "fa5s.pills",
            _c['warning'],
            compact=True
        )
        
        # Pas de card_detail dans le nouveau design
        self.card_detail = None
        
        # Ajouter toutes les cards sur une ligne
        layout.addWidget(self.cards_expiration['expires'], 1)
        layout.addWidget(self.cards_expiration['bientot'], 1)
        layout.addWidget(self.cards_expiration['valides'], 1)
        layout.addWidget(self.cards_expiration['valeur'], 1)
        layout.addWidget(self.cards_type['liquide'], 1)
        layout.addWidget(self.cards_type['pommade'], 1)
        layout.addWidget(self.cards_type['comprime'], 1)
        
        parent_layout.addLayout(layout)
    
    # =========================================================================
    # PROPRIÃ‰TÃ‰S D'ACCÃˆS (RÃ‰TROCOMPATIBILITÃ‰)
    # =========================================================================
    
    @property
    def card_expires(self):
        """AccÃ¨s Ã  la card 'Produits ExpirÃ©s' (rÃ©trocompatibilitÃ©)."""
        return self.cards_expiration.get('expires')
    
    @property
    def card_bientot(self):
        """AccÃ¨s Ã  la card 'BientÃ´t ExpirÃ©s' (rÃ©trocompatibilitÃ©)."""
        return self.cards_expiration.get('bientot')
    
    @property
    def card_valides(self):
        """AccÃ¨s Ã  la card 'Produits Valides' (rÃ©trocompatibilitÃ©)."""
        return self.cards_expiration.get('valides')
    
    @property
    def card_valeur(self):
        """AccÃ¨s Ã  la card 'Valeur Stock Global' (rÃ©trocompatibilitÃ©)."""
        return self.cards_expiration.get('valeur')
    
    @property
    def card_liquide(self):
        """AccÃ¨s Ã  la card 'Stock Liquide' (rÃ©trocompatibilitÃ©)."""
        return self.cards_type.get('liquide')
    
    @property
    def card_pommade(self):
        """AccÃ¨s Ã  la card 'Stock Pommade' (rÃ©trocompatibilitÃ©)."""
        return self.cards_type.get('pommade')
    
    @property
    def card_comprime(self):
        """AccÃ¨s Ã  la card 'Stock ComprimÃ©' (rÃ©trocompatibilitÃ©)."""
        return self.cards_type.get('comprime')
    
    @property
    def frame_detail_stock(self):
        """AccÃ¨s au frame de dÃ©tail du stock (rÃ©trocompatibilitÃ©)."""
        return self.card_detail
    
    @property
    def container_lignes_stock(self):
        """AccÃ¨s au container des lignes de stock (rÃ©trocompatibilitÃ©)."""
        if self.card_detail:
            return self.card_detail.scroll_area.widget()
        return None
    
    @property
    def layout_lignes_stock(self):
        """AccÃ¨s au layout des lignes de stock (rÃ©trocompatibilitÃ©)."""
        container = self.container_lignes_stock
        if container:
            return container.layout()
        return None
    
    # =========================================================================
    # MÃ‰THODES PUBLIQUES - API DU WIDGET
    # =========================================================================
    
    def charger_statistiques(self, code_session: str) -> bool:
        """
        Charge toutes les statistiques pour une session donnÃ©e.
        Point d'entrÃ©e principal pour le chargement des donnÃ©es.
        
        Args:
            code_session: Code de la session active
        
        Returns:
            bool: True si le chargement a rÃ©ussi, False sinon
        
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
                "ContrÃ´leur non initialisÃ©",
                "Le contrÃ´leur panier n'a pas Ã©tÃ© injectÃ© lors de l'initialisation."
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
        
        # Mettre Ã  jour l'interface avec les donnÃ©es via le handler UI
        self._mettre_a_jour_interface(dto)
        self._donnees_chargees = True
        
        self.logger.info("[StatistiquesWidget] Statistiques chargÃ©es avec succÃ¨s")
        return True
    
    def actualiser(self) -> bool:
        """
        Actualise les statistiques avec les derniÃ¨res donnÃ©es.
        Recharge les donnÃ©es pour la session en cours.
        
        Returns:
            bool: True si l'actualisation a rÃ©ussi, False sinon
        
        Usage:
            >>> widget.actualiser()  # Recharge les donnÃ©es
        """
        if not self.code_session:
            self.logger.warning("[StatistiquesWidget] Aucune session active pour actualisation")
            return False
        
        self.logger.info("[StatistiquesWidget] Actualisation des statistiques")
        return self.charger_statistiques(self.code_session)
    
    def reinitialiser(self) -> None:
        """
        RÃ©initialise le widget Ã  son Ã©tat initial.
        Efface toutes les donnÃ©es affichÃ©es.
        """
        self.logger.info("[StatistiquesWidget] RÃ©initialisation")
        
        self.code_session = None
        self._donnees_chargees = False
        self._afficher_donnees_vides()
    
    # =========================================================================
    # MÃ‰THODES PRIVÃ‰ES - MISE Ã€ JOUR INTERFACE
    # =========================================================================
    
    def _mettre_a_jour_interface(self, dto) -> None:
        """
        Met Ã  jour tous les composants de l'interface avec les donnÃ©es du DTO.
        DÃ©lÃ¨gue au UIUpdater.
        
        Args:
            dto: StatistiquesDTO contenant toutes les donnÃ©es
        """
        self.logger.debug("[StatistiquesWidget] Mise Ã  jour interface")
        
        try:
            # DÃ©lÃ©guer au handler UI
            self._ui_updater.mettre_a_jour_cards_expiration(dto, self.cards_expiration)
            self._ui_updater.mettre_a_jour_cards_type(dto, self.cards_type)
            if self.card_detail:
                self._ui_updater.mettre_a_jour_stock_detaille(dto, self.card_detail)
            
        except Exception as e:
            self.logger.error(f"[StatistiquesWidget] Erreur mise Ã  jour interface: {e}")
            self._afficher_erreur("Erreur d'affichage", str(e))
    
    def _afficher_donnees_vides(self) -> None:
        """
        Affiche des valeurs vides/zero dans tous les composants.
        Utilise lors de la reinitialisation ou en cas d'erreur.
        """
        try:
            self._ui_updater.afficher_donnees_vides(
                self.cards_expiration,
                self.cards_type,
                self.card_detail
            )
        except Exception as e:
            self.logger.error(f"[StatistiquesWidget] Erreur affichage donnees vides: {e}")

    # =========================================================================
    # THÈME
    # =========================================================================

    def apply_theme(self):
        """Met à jour les couleurs des cards selon le thème actif."""
        _c = theme_manager.colors()

        # Mapping couleur accent par card d'expiration
        exp_colors = {
            'expires': _c['danger'],
            'bientot': _c['warning'],
            'valides': _c['success'],
            'valeur':  _c['primary'],
        }
        for key, card in self.cards_expiration.items():
            if card and key in exp_colors:
                card.update_theme_color(exp_colors[key])

        # Mapping couleur accent par card de type
        type_colors = {
            'liquide':  _c['info'],
            'pommade':  _c['accent'],
            'comprime': _c['warning'],
        }
        for key, card in self.cards_type.items():
            if card and key in type_colors:
                card.update_theme_color(type_colors[key])

