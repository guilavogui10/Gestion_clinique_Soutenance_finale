"""
Handler PrescriptionValidationHandler.
Responsabilité : Validation en temps réel des champs du formulaire prescription.
Pattern : Strategy Pattern pour différentes validations.

Différences vs ValidationHandler panier :
  - valider_date() supprimée → FEFO automatique, pas de date à valider
  - valider_prix()  supprimée → prix readonly, auto-rempli
  - Seule valider_quantite() est nécessaire
"""

from typing import Any


class PrescriptionValidationHandler:
    """Gère la validation en temps réel des champs du formulaire prescription."""

    def __init__(self, prescription_ctrl):
        self.ctrl = prescription_ctrl

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def valider_quantite(self, input_widget: Any, valeur: str) -> None:
        """
        Valide la quantité saisie via le ModernQuantitySpinner.
        Le spinner émet un int via valueChanged — on reçoit str ici.

        Args:
            input_widget : ModernQuantitySpinner à styler
            valeur       : Valeur sous forme de chaîne
        """
        if not valeur:
            self._reset_style(input_widget)
            return

        if self.ctrl:
            try:
                qte = int(valeur)
                valide = qte > 0
            except ValueError:
                valide = False
            self._appliquer_style(input_widget, valide)

    # =========================================================================
    # STYLES
    # =========================================================================

    def _appliquer_style(self, widget: Any, valide: bool) -> None:
        """
        Applique le style visuel selon le résultat de la validation.

        Args:
            widget : Widget à styler (ModernQuantitySpinner ou QLineEdit)
            valide : True = vert, False = rouge
        """
        from views.shared.theme_manager import theme_manager
        c = theme_manager.colors()
        if valide:
            widget.setStyleSheet(
                f"border-radius: 8px; border: 2px solid {c['success']};"
                f"padding-left: 12px; background: {c['success_bg']}; font-size: 12px;"
            )
        else:
            widget.setStyleSheet(
                f"border-radius: 8px; border: 2px solid {c['danger']};"
                f"padding-left: 12px; background: {c['danger_bg']}; font-size: 12px;"
            )

    def _reset_style(self, widget: Any) -> None:
        """
        Réinitialise le style d'un champ à l'état neutre.

        Args:
            widget : Widget à réinitialiser
        """
        from views.shared.theme_manager import theme_manager
        c = theme_manager.colors()
        widget.setStyleSheet(
            f"border-radius: 8px; border: 1px solid {c['border']};"
            f"padding-left: 12px; background: {c['bg_input']}; font-size: 12px;"
        )