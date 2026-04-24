"""
Handler pour la validation en temps réel.
Responsabilité : Validation des champs et application des styles visuels.
Pattern : Strategy Pattern pour différentes validations.
"""

from typing import Any


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
        if valide:
            widget.setStyleSheet(
                "border-radius: 8px; border: 2px solid #27ae60;"
                "padding-left: 12px; background: #f0f8f5; font-size: 12px;"
            )
        else:
            widget.setStyleSheet(
                "border-radius: 8px; border: 2px solid #e74c3c;"
                "padding-left: 12px; background: #fdf2f2; font-size: 12px;"
            )
    
    def _reset_style(self, widget: Any) -> None:
        """
        Réinitialise le style d'un champ.
        
        Args:
            widget: Widget à réinitialiser
        """
        widget.setStyleSheet(
            "border-radius: 8px; border: 1px solid #e0e0e0;"
            "padding-left: 12px; background: white; font-size: 12px;"
        )
