"""
Composants réutilisables pour la vue Patient
"""
from .kpi_cards import KpiCardsSection
from .patients_table import PatientsTable
from .quick_actions import QuickActions
from .charts_section import ChartsSection

__all__ = [
    'KpiCardsSection',
    'PatientsTable',
    'QuickActions',
    'ChartsSection'
]
