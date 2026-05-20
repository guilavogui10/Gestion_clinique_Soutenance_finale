"""
Composants modulaires pour l'interface Personnel
"""
from .kpi_cards import KpiCardsSection
from .personnel_table import PersonnelTable
from .quick_actions import QuickActions
from .charts_section import ChartsSection

__all__ = [
    'KpiCardsSection',
    'PersonnelTable',
    'QuickActions',
    'ChartsSection'
]
