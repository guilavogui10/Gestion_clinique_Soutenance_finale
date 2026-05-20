"""
Composants modulaires pour l'interface Examen
"""
from .kpi_cards import KpiCardsSection
from .charts_section import ChartsSection
from .examens_table import ExamensTable
from .quick_actions import QuickActions

__all__ = [
    'KpiCardsSection',
    'ChartsSection',
    'ExamensTable',
    'QuickActions'
]
