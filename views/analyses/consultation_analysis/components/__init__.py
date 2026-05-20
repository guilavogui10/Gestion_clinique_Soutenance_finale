"""
Composants modulaires pour l'analyse consultation
"""
from .kpi_cards import KpiCardsAnalyse
from .charts_section import ChartsAnalyseSection
from .consultations_table import ConsultationsTableAnalyse
from .sidebar_stats import SidebarStatsAnalyse
from .quick_actions import QuickActionsAnalyse

__all__ = [
    'KpiCardsAnalyse',
    'ChartsAnalyseSection',
    'ConsultationsTableAnalyse',
    'SidebarStatsAnalyse',
    'QuickActionsAnalyse'
]
