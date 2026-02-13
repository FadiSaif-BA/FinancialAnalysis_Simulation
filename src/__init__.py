"""
Financial Analysis Source Package
=================================
Modules for data extraction, cleaning, analysis, and reporting.
"""

from .data_engine import ParsonsDataEngine
from .data_cleaning import DataCleaner
from .dso_analysis import DSOAnalyzer
from .wip_analysis import WIPAnalyzer
from .risk_scoring import RiskScorer
from .predictive_analytics import PredictiveAnalyzer
from .visualizations import FinancialVisualizer
from .report_generator import ReportGenerator

__all__ = [
    'ParsonsDataEngine',
    'DataCleaner',
    'DSOAnalyzer',
    'WIPAnalyzer',
    'RiskScorer',
    'PredictiveAnalyzer',
    'FinancialVisualizer',
    'ReportGenerator'
]

__version__ = '1.0.0'
