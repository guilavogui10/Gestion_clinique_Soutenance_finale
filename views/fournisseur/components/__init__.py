"""
Composants modulaires pour l'interface Fournisseur
"""
from .kpi_cards import KpiCardsSection
from .fournisseurs_table import FournisseursTable
from .quick_actions import QuickActions
from .charts_section import ChartsSection

__all__ = [
    'KpiCardsSection',
    'FournisseursTable',
    'QuickActions',
    'ChartsSection'
]
