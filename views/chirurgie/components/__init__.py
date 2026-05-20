"""
Composants modulaires pour l'interface Chirurgie
"""
from .kpi_cards import KpiCardsSection as KPICards
from .charts_section import ChartsSection
from .chirurgies_table import ChirurgiesTable
from .quick_actions import QuickActions

__all__ = [
    'KPICards',
    'ChartsSection',
    'ChirurgiesTable',
    'QuickActions'
]
