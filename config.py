"""
Financial Analysis Configuration
================================
Centralized configuration for database connection and analysis parameters.
"""

# =============================================================================
# DATABASE CONNECTION SETTINGS
# =============================================================================
SERVER = 'DESKTOP-UCV0E2C'
DATABASE = 'ParsonsFinanceSim'
DRIVER = 'SQL Server'

# Connection string template
def get_connection_string():
    return (
        f'DRIVER={{{DRIVER}}};'
        f'SERVER={SERVER};'
        f'DATABASE={DATABASE};'
        f'Trusted_Connection=yes;'
    )

# =============================================================================
# AGING BUCKET CONFIGURATION
# =============================================================================
# Define the boundaries for aging buckets (in days)
AGING_BUCKETS = [0, 30, 60, 90, float('inf')]
BUCKET_LABELS = ['Current (0-30)', '31-60 Days', '61-90 Days', '90+ Days (Toxic)']

# =============================================================================
# CLIENT RISK GRADING THRESHOLDS
# =============================================================================
# Based on average days variance from contractual terms
RISK_GRADE_THRESHOLDS = {
    'A': 10,      # Excellent: ≤10 days variance
    'B': 20,      # Good: 11-20 days variance
    'C': 40,      # Watch: 21-40 days variance
    'D': 60,      # At Risk: 41-60 days variance
    'F': float('inf')  # Default Risk: 61+ days variance
}

RISK_GRADE_DESCRIPTIONS = {
    'A': 'Excellent - Consistent early/on-time payments',
    'B': 'Good - Minor delays, low risk',
    'C': 'Watch - Moderate delays, needs monitoring',
    'D': 'At Risk - Significant delays, escalation needed',
    'F': 'Default Risk - Chronic late payments, collection action required'
}

# =============================================================================
# PREDICTIVE ANALYTICS SETTINGS
# =============================================================================
FORECAST_PERIODS = 4  # Quarters to forecast ahead
CONFIDENCE_INTERVAL = 0.95  # 95% confidence interval
MOVING_AVERAGE_WINDOW = 3  # Months for moving average calculation

# =============================================================================
# WIP ANALYSIS SETTINGS
# =============================================================================
STALE_WIP_THRESHOLD_DAYS = 60  # Days before WIP is considered "stale"
LEAKAGE_WARNING_THRESHOLD = 0.15  # 15% leakage coefficient triggers warning

# =============================================================================
# REPORT OUTPUT SETTINGS
# =============================================================================
REPORTS_DIR = 'reports'
DATE_FORMAT = '%Y%m%d_%H%M'  # Format for timestamped files

# Report file prefixes
AR_SNAPSHOT_PREFIX = 'AR_Snapshot'
RISK_REPORT_PREFIX = 'Risk_Report'
WIP_REPORT_PREFIX = 'WIP_Leakage_Report'
EXECUTIVE_SUMMARY_PREFIX = 'Executive_Summary'

# =============================================================================
# VISUALIZATION SETTINGS
# =============================================================================
CHART_STYLE = 'seaborn-v0_8-whitegrid'
FIGURE_DPI = 100
COLOR_PALETTE = {
    'current': '#2ecc71',      # Green
    'warning': '#f39c12',      # Orange
    'danger': '#e74c3c',       # Red
    'severe': '#8e44ad',       # Purple
    'primary': '#3498db',      # Blue
    'secondary': '#95a5a6'     # Gray
}

# Colors for aging buckets
AGING_COLORS = ['#2ecc71', '#f39c12', '#e74c3c', '#8e44ad']

# Colors for risk grades
RISK_GRADE_COLORS = {
    'A': '#27ae60',
    'B': '#2ecc71',
    'C': '#f39c12',
    'D': '#e67e22',
    'F': '#c0392b'
}
