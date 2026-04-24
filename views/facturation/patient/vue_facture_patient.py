"""
Vue principale Facture Patient.
Version simplifiee : affiche uniquement le widget facture (comme la maquette).
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout

from .panier.facture_patient_widget import FacturePatientWidget


class FacturePatientView(QWidget):
    """Vue principale de facturation patient (sans tableau)."""

    def __init__(self, facture_ctrl=None, panier_ctrl=None, parent=None):
        super().__init__(parent)
        self.facture_ctrl = facture_ctrl
        self.panier_ctrl = panier_ctrl
        self.code_session = None
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(0)

        self.widget_facture = FacturePatientWidget(
            facture_ctrl=self.facture_ctrl,
            panier_ctrl=self.panier_ctrl
        )

        self.main_layout.addWidget(self.widget_facture)

    # =========================================================================
    # API PUBLIQUE
    # =========================================================================

    def charger_donnees(self, code_session: str) -> None:
        self.code_session = code_session
        if self.widget_facture:
            self.widget_facture.charger_donnees(code_session)

