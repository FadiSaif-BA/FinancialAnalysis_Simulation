"""
WIP Analysis Module
===================
Work-in-Progress (WIP) Leakage analysis.
Identifies unbilled work and calculates leakage coefficient.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class WIPAnalyzer:
    """
    Analyzer for Work-in-Progress and Revenue Leakage.
    
    Leakage Coefficient: Lc = Σ(Unbilled Value) / Σ(Unbilled Value + Invoiced Value)
    
    A high leakage coefficient indicates that work is being performed
    but not converted to revenue (billing delays).
    """
    
    def __init__(self, wip_df: pd.DataFrame, invoices_df: Optional[pd.DataFrame] = None):
        """
        Initialize WIP Analyzer.
        
        Args:
            wip_df: Unbilled work DataFrame (from extract_wip_leakage or extract_unbilled_work)
            invoices_df: Optional invoices DataFrame for leakage coefficient calculation
        """
        self.wip_df = wip_df.copy()
        self.invoices_df = invoices_df.copy() if invoices_df is not None else None
        self._validate_data()
    
    def _validate_data(self):
        """Ensure required columns exist."""
        wip_cols = ['ProjectName', 'UnbilledValue'] if 'UnbilledValue' in self.wip_df.columns else ['ProjectName', 'EstimatedValue']
        
        # Standardize column name
        if 'EstimatedValue' in self.wip_df.columns and 'UnbilledValue' not in self.wip_df.columns:
            self.wip_df['UnbilledValue'] = self.wip_df['EstimatedValue']
    
    def calculate_leakage_coefficient(self) -> float:
        """
        Calculate the overall Leakage Coefficient.
        
        Lc = Σ(Unbilled Value) / Σ(Unbilled Value + Invoiced Value)
        
        Returns:
            Leakage coefficient (0.0 to 1.0)
        """
        total_unbilled = self.wip_df['UnbilledValue'].sum()
        
        if self.invoices_df is not None:
            total_invoiced = self.invoices_df['InvoiceAmount'].sum()
        else:
            # If no invoice data, estimate based on typical ratios
            total_invoiced = total_unbilled * 5  # Assume 5:1 ratio as baseline
        
        total_value = total_unbilled + total_invoiced
        
        if total_value == 0:
            return 0.0
        
        leakage = total_unbilled / total_value
        return round(leakage, 4)
    
    def calculate_leakage_by_project(self) -> pd.DataFrame:
        """
        Calculate leakage coefficient for each project.
        
        Returns:
            DataFrame with ProjectName, UnbilledValue, InvoicedValue, LeakageCoefficient
        """
        wip_by_project = self.wip_df.groupby('ProjectName', as_index=False).agg({
            'UnbilledValue': 'sum'
        })
        
        if self.invoices_df is not None and 'ProjectName' in self.invoices_df.columns:
            invoiced_by_project = self.invoices_df.groupby('ProjectName', as_index=False).agg({
                'InvoiceAmount': 'sum'
            })
            invoiced_by_project.columns = ['ProjectName', 'InvoicedValue']
            
            result = wip_by_project.merge(invoiced_by_project, on='ProjectName', how='left')
            result['InvoicedValue'] = result['InvoicedValue'].fillna(0)
        else:
            result = wip_by_project.copy()
            result['InvoicedValue'] = 0
        
        result['TotalValue'] = result['UnbilledValue'] + result['InvoicedValue']
        result['LeakageCoefficient'] = np.where(
            result['TotalValue'] > 0,
            result['UnbilledValue'] / result['TotalValue'],
            0
        )
        
        result = result.sort_values('LeakageCoefficient', ascending=False)
        
        return result
    
    def identify_stale_wip(self, days_threshold: int = None) -> pd.DataFrame:
        """
        Identify projects with stale unbilled work.
        
        Args:
            days_threshold: Days since logged to consider stale (default from config)
            
        Returns:
            DataFrame with stale WIP entries
        """
        threshold = days_threshold or config.STALE_WIP_THRESHOLD_DAYS
        
        df = self.wip_df.copy()
        
        # Check for days since logged column
        if 'DaysSinceLogged' in df.columns:
            stale = df[df['DaysSinceLogged'] > threshold].copy()
        elif 'OldestEntry' in df.columns:
            df['DaysSinceOldest'] = (datetime.now() - pd.to_datetime(df['OldestEntry'])).dt.days
            stale = df[df['DaysSinceOldest'] > threshold].copy()
        elif 'LogDate' in df.columns:
            df['DaysSinceLogged'] = (datetime.now() - pd.to_datetime(df['LogDate'])).dt.days
            stale = df[df['DaysSinceLogged'] > threshold].copy()
        else:
            # If no date info, return all WIP as potentially stale
            stale = df.copy()
            stale['DaysSinceLogged'] = 'Unknown'
        
        return stale.sort_values('UnbilledValue', ascending=False)
    
    def get_wip_by_project(self) -> pd.DataFrame:
        """
        Get WIP breakdown by project with summary stats.
        
        Returns:
            DataFrame with project-level WIP summary
        """
        if 'ProjectName' in self.wip_df.columns:
            summary = self.wip_df.groupby('ProjectName', as_index=False).agg({
                'UnbilledValue': 'sum'
            })
        else:
            summary = self.wip_df.copy()
        
        # Calculate percentage of total
        total_wip = summary['UnbilledValue'].sum()
        summary['PercentageOfTotal'] = (summary['UnbilledValue'] / total_wip * 100).round(2)
        
        # Add risk flag based on threshold
        summary['RiskFlag'] = summary['UnbilledValue'] > summary['UnbilledValue'].quantile(0.75)
        
        return summary.sort_values('UnbilledValue', ascending=False)
    
    def get_wip_by_sector(self) -> pd.DataFrame:
        """
        Get WIP breakdown by sector/industry.
        
        Returns:
            DataFrame with sector-level WIP summary
        """
        if 'Sector' not in self.wip_df.columns:
            return pd.DataFrame({'Message': ['Sector data not available']})
        
        summary = self.wip_df.groupby('Sector', as_index=False).agg({
            'UnbilledValue': 'sum',
            'ProjectName': 'nunique'
        })
        summary.columns = ['Sector', 'UnbilledValue', 'ProjectCount']
        
        total_wip = summary['UnbilledValue'].sum()
        summary['PercentageOfTotal'] = (summary['UnbilledValue'] / total_wip * 100).round(2)
        
        return summary.sort_values('UnbilledValue', ascending=False)
    
    def get_wip_health_report(self) -> Dict:
        """
        Generate comprehensive WIP health report.
        
        Returns:
            Dictionary with key WIP metrics
        """
        total_wip = self.wip_df['UnbilledValue'].sum()
        stale_wip = self.identify_stale_wip()
        stale_value = stale_wip['UnbilledValue'].sum()
        leakage = self.calculate_leakage_coefficient()
        
        # Determine health status
        if leakage > 0.25:
            health_status = 'Critical'
        elif leakage > config.LEAKAGE_WARNING_THRESHOLD:
            health_status = 'Warning'
        elif leakage > 0.05:
            health_status = 'Monitor'
        else:
            health_status = 'Healthy'
        
        report = {
            'total_wip_value': total_wip,
            'leakage_coefficient': leakage,
            'leakage_percentage': leakage * 100,
            'stale_wip_value': stale_value,
            'stale_wip_percentage': (stale_value / total_wip * 100) if total_wip > 0 else 0,
            'project_count': self.wip_df['ProjectName'].nunique(),
            'top_wip_projects': self.get_wip_by_project().head(5).to_dict('records'),
            'health_status': health_status
        }
        
        return report
    
    def get_action_items(self) -> List[Dict]:
        """
        Generate prioritized action items for WIP reduction.
        
        Returns:
            List of action items with priority and details
        """
        actions = []
        
        # Check for stale WIP
        stale = self.identify_stale_wip()
        if len(stale) > 0:
            actions.append({
                'priority': 'High',
                'category': 'Stale WIP',
                'action': f'Review {len(stale)} projects with stale unbilled work',
                'value_at_risk': stale['UnbilledValue'].sum(),
                'projects': stale['ProjectName'].head(5).tolist()
            })
        
        # Check overall leakage
        leakage = self.calculate_leakage_coefficient()
        if leakage > config.LEAKAGE_WARNING_THRESHOLD:
            actions.append({
                'priority': 'High',
                'category': 'Revenue Leakage',
                'action': f'Leakage coefficient at {leakage:.1%} - review billing processes',
                'value_at_risk': self.wip_df['UnbilledValue'].sum(),
                'projects': None
            })
        
        # Check for high-value unbilled projects
        top_projects = self.get_wip_by_project().head(3)
        if len(top_projects) > 0:
            actions.append({
                'priority': 'Medium',
                'category': 'High-Value WIP',
                'action': 'Prioritize billing for top unbilled projects',
                'value_at_risk': top_projects['UnbilledValue'].sum(),
                'projects': top_projects['ProjectName'].tolist()
            })
        
        return actions


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("WIP ANALYSIS MODULE - DEMONSTRATION")
    print("=" * 60)
    
    # Create sample WIP data
    sample_wip = pd.DataFrame({
        'ProjectName': ['Alpha Project', 'Beta Project', 'Gamma Project', 
                        'Delta Project', 'Epsilon Project'],
        'UnbilledValue': [50000, 125000, 30000, 200000, 15000],
        'Sector': ['Transport', 'Energy', 'Transport', 'Infrastructure', 'Energy'],
        'DaysSinceLogged': [25, 75, 45, 120, 10]
    })
    
    # Create sample invoice data
    sample_invoices = pd.DataFrame({
        'ProjectName': ['Alpha Project', 'Beta Project', 'Gamma Project', 
                        'Delta Project', 'Epsilon Project'] * 3,
        'InvoiceAmount': [100000, 200000, 150000, 300000, 50000] * 3
    })
    
    analyzer = WIPAnalyzer(sample_wip, sample_invoices)
    
    print(f"\nLeakage Coefficient: {analyzer.calculate_leakage_coefficient():.2%}")
    
    print("\nWIP by Project:")
    print(analyzer.get_wip_by_project())
    
    print("\nStale WIP (60+ days):")
    print(analyzer.identify_stale_wip())
    
    print("\nWIP Health Report:")
    report = analyzer.get_wip_health_report()
    print(f"  Total WIP: ${report['total_wip_value']:,.2f}")
    print(f"  Leakage: {report['leakage_percentage']:.1f}%")
    print(f"  Stale WIP: ${report['stale_wip_value']:,.2f}")
    print(f"  Health Status: {report['health_status']}")
    
    print("\nAction Items:")
    for action in analyzer.get_action_items():
        print(f"  [{action['priority']}] {action['action']}")
