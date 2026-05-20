"""
Composants modulaires pour l'interface Visite
"""
from .header_section import HeaderSection
from .kpi_cards import KpiCardsSection
from .charts_section import ChartsSection
from .visits_table import VisitsTable
from .sidebar_stats import SidebarStats
from .quick_actions import QuickActions
from .visit_cards_panel import VisitCardsPanel

__all__ = [
    'HeaderSection',
    'KpiCardsSection',
    'ChartsSection',
    'VisitsTable',
    'SidebarStats',
    'QuickActions',
    'VisitCardsPanel',
]
