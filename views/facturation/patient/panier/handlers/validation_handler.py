"""
Handler pour la validation en temps réel.
Responsabilité : Validation des champs et application des styles visuels.
Pattern : Strategy Pattern pour différentes validations.
"""

from typing import Any
from views.shared.theme_manager import theme_manager


class ValidationHandler:
    """Gère la validation en temps réel des champs du formulaire."""
    
    def __init__(self, panier_ctrl):
        self.panier_ctrl = panier_ctrl
    
    def valider_quantite(self, input_widget: Any, texte: str) -> None:
        """
        Valide la quantité saisie.
        
        Args:
            input_widget: Widget QLineEdit à valider
            texte: Texte saisi par l'utilisateur
        """
        if not texte:
            self._reset_style(input_widget)
            return
        
        if self.panier_ctrl:
            valide, msg = self.panier_ctrl.valider_quantite(texte)
            self._appliquer_style(input_widget, valide)
    
    def valider_prix(self, input_widget: Any, texte: str) -> None:
        """
        Valide le prix saisi.
        
        Args:
            input_widget: Widget QLineEdit à valider
            texte: Texte saisi par l'utilisateur
        """
        if not texte:
            self._reset_style(input_widget)
            return
        
        if self.panier_ctrl:
            valide, msg = self.panier_ctrl.valider_prix(texte, "prix unitaire")
            self._appliquer_style(input_widget, valide)
    
    def valider_date(self, input_widget: Any, texte: str) -> None:
        """
        Valide la date d'expiration saisie.
        
        Args:
            input_widget: Widget QLineEdit à valider
            texte: Texte saisi par l'utilisateur
        """
        if not texte:
            self._reset_style(input_widget)
            return
        
        if self.panier_ctrl:
            valide, msg = self.panier_ctrl.valider_date_expiration(texte)
            self._appliquer_style(input_widget, valide)
    
    def _appliquer_style(self, widget: Any, valide: bool) -> None:
        """
        Applique le style visuel selon la validation.
        
        Args:
            widget: Widget à styler
            valide: True si valide, False sinon
        """
        c = theme_manager.colors()
        if valide:
            widget.setStyleSheet(
                f"border-radius: 8px; border: 2px solid {c['success']};"
                f"padding-left: 12px; background: {c['success_bg']}; font-size: 12px; color: {c['text_primary']};"
            )
        else:
            widget.setStyleSheet(
                f"border-radius: 8px; border: 2px solid {c['danger']};"
                f"padding-left: 12px; background: {c['danger_bg']}; font-size: 12px; color: {c['text_primary']};"
            )
    
    def _reset_style(self, widget: Any) -> None:
        """
        Réinitialise le style d'un champ.
        
        Args:
            widget: Widget à réinitialiser
        """
        c = theme_manager.colors()
        widget.setStyleSheet(
            f"border-radius: 8px; border: 1px solid {c['border']};"
            f"padding-left: 12px; background: {c['bg_input']}; font-size: 12px; color: {c['text_primary']};"
        )
