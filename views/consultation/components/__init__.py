"""
Composants modulaires pour l'interface Consultation
"""
from .kpi_cards import KpiCardsSection
from .consultations_table import ConsultationsTable
from .quick_actions import QuickActions
from .charts_section import ChartsSection

__all__ = [
    'KpiCardsSection',
    'ConsultationsTable',
    'QuickActions',
    'ChartsSection'
]
