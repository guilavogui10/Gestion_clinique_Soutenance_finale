"""
Point d'entree pour le widget facture patient.
Importe depuis l'architecture modulaire du panier.
"""

from .panier.facture_patient_widget import FacturePatientWidget
from .panier.components.animated_frame import AnimatedFrame

__all__ = ["FacturePatientWidget", "AnimatedFrame"]

