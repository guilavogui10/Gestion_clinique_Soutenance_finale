"""
Module facturation - Vue principale avec onglets.
"""

from .vue_facturation_tabs import FacturationView
from .patient.vue_facture_patient import FacturePatientView

__all__ = ['FacturationView', 'FacturePatientView']
