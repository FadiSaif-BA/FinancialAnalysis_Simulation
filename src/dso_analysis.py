"""
DSO Analysis Module
===================
Days Sales Outstanding (DSO) and Aging Bucket analysis.
Calculates key liquidity metrics and identifies toxic debt.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class DSOAnalyzer:
    """
    Analyzer for Days Sales Outstanding and Aging Bucket metrics.
    
    DSO Formula: (Average Accounts Receivable / Total Credit Sales) × Days in Period
    
    Aging Buckets:
    - Current (0-30 days)
    - 31-60 Days
    - 61-90 Days
    - 90+ Days (Toxic Debt)
    """
    
    def __init__(self, invoices_df: pd.DataFrame):
        """
        Initialize DSO Analyzer with invoice data.
        
        Args:
            invoices_df: Cleaned invoices DataFrame
        """
        self.df = invoices_df.copy()
        self._validate_data()
    
    def _validate_data(self):
        """Ensure required columns exist."""
        required_cols = ['InvoiceAmount', 'Status']
        missing = [col for col in required_cols if col not in self.df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
    
    def calculate_dso(self, period_days: int = 30) -> float:
        """
        Calculate Days Sales Outstanding.
        
        DSO = (Average AR / Total Credit Sales) × Days in Period
        
        Args:
            period_days: Number of days in the analysis period
            
        Returns:
            DSO value in days
        """
        # AR = Outstanding + Overdue invoices (not paid)
        ar_df = self.df[self.df['Status'].str.lower().isin(['pending', 'overdue', 'outstanding'])]
        average_ar = ar_df['InvoiceAmount'].mean() if len(ar_df) > 0 else 0
        
        # Total credit sales = All invoices
        total_sales = self.df['InvoiceAmount'].sum()
        
        if total_sales == 0:
            return 0.0
        
        dso = (average_ar / total_sales) * period_days * len(self.df)
        return round(dso, 2)
    
    def calculate_dso_trend(self, periods: int = 12) -> pd.DataFrame:
        """
        Calculate DSO trend over time periods.
        
        Args:
            periods: Number of periods to analyze
            
        Returns:
            DataFrame with Period and DSO columns
        """
        if 'MonthYear' not in self.df.columns and 'InvoiceDate' in self.df.columns:
            self.df['MonthYear'] = pd.to_datetime(self.df['InvoiceDate']).dt.to_period('M')
        
        trend_data = []
        
        for period in self.df['MonthYear'].dropna().unique()[-periods:]:
            period_df = self.df[self.df['MonthYear'] == period]
            
            ar_value = period_df[
                period_df['Status'].str.lower().isin(['pending', 'overdue', 'outstanding'])
            ]['InvoiceAmount'].sum()
            
            total_sales = period_df['InvoiceAmount'].sum()
            
            if total_sales > 0:
                dso = (ar_value / total_sales) * 30  # Monthly DSO
            else:
                dso = 0
            
            trend_data.append({
                'Period': str(period),
                'DSO': round(dso, 2),
                'AR_Value': ar_value,
                'Total_Sales': total_sales
            })
        
        return pd.DataFrame(trend_data)
    
    def calculate_aging_buckets(self) -> pd.DataFrame:
        """
        Assign invoices to aging buckets based on days overdue.
        
        Returns:
            DataFrame with AgingBucket column added
        """
        df = self.df.copy()
        
        if 'DaysOverdue' not in df.columns:
            if 'DueDate' in df.columns:
                df['DaysOverdue'] = (datetime.now() - pd.to_datetime(df['DueDate'])).dt.days
            else:
                raise ValueError("DaysOverdue or DueDate column required")
        
        # Assign buckets
        conditions = [
            df['DaysOverdue'] <= 30,
            (df['DaysOverdue'] > 30) & (df['DaysOverdue'] <= 60),
            (df['DaysOverdue'] > 60) & (df['DaysOverdue'] <= 90),
            df['DaysOverdue'] > 90
        ]
        
        choices = config.BUCKET_LABELS
        df['AgingBucket'] = np.select(conditions, choices, default=choices[0])
        
        return df
    
    def get_aging_summary(self) -> pd.DataFrame:
        """
        Get aggregated totals by aging bucket.
        
        Returns:
            DataFrame with Bucket, Count, Amount, Percentage columns
        """
        df = self.calculate_aging_buckets()
        
        # Only include unpaid invoices
        unpaid = df[df['Status'].str.lower().isin(['pending', 'overdue', 'outstanding'])]
        
        summary = unpaid.groupby('AgingBucket', observed=True).agg({
            'InvoiceID': 'count',
            'InvoiceAmount': 'sum'
        }).reset_index()
        
        summary.columns = ['AgingBucket', 'Count', 'Amount']
        
        total_amount = summary['Amount'].sum()
        summary['Percentage'] = (summary['Amount'] / total_amount * 100).round(2)
        
        # Ensure all buckets are represented
        all_buckets = pd.DataFrame({'AgingBucket': config.BUCKET_LABELS})
        summary = all_buckets.merge(summary, on='AgingBucket', how='left').fillna(0)
        
        return summary
    
    def identify_toxic_debt(self, days_threshold: int = 90) -> pd.DataFrame:
        """
        Identify invoices classified as toxic debt (90+ days overdue).
        
        Args:
            days_threshold: Days overdue to classify as toxic (default: 90)
            
        Returns:
            DataFrame with toxic debt invoices
        """
        df = self.df.copy()
        
        if 'DaysOverdue' not in df.columns:
            raise ValueError("DaysOverdue column required")
        
        toxic = df[
            (df['DaysOverdue'] > days_threshold) & 
            (df['Status'].str.lower().isin(['pending', 'overdue', 'outstanding']))
        ].copy()
        
        toxic = toxic.sort_values('DaysOverdue', ascending=False)
        
        return toxic
    
    def get_dso_health_report(self) -> Dict:
        """
        Generate a comprehensive DSO health report.
        
        Returns:
            Dictionary with key metrics and analysis
        """
        aging_summary = self.get_aging_summary()
        toxic_debt = self.identify_toxic_debt()
        
        report = {
            'dso': self.calculate_dso(),
            'total_ar': self.df[
                self.df['Status'].str.lower().isin(['pending', 'overdue', 'outstanding'])
            ]['InvoiceAmount'].sum(),
            'total_overdue': self.df[
                self.df['Status'].str.lower() == 'overdue'
            ]['InvoiceAmount'].sum(),
            'toxic_debt_amount': toxic_debt['InvoiceAmount'].sum() if len(toxic_debt) > 0 else 0,
            'toxic_debt_count': len(toxic_debt),
            'aging_breakdown': aging_summary.to_dict('records'),
            'health_score': self._calculate_health_score(aging_summary)
        }
        
        return report
    
    def _calculate_health_score(self, aging_summary: pd.DataFrame) -> str:
        """
        Calculate AR health score based on aging distribution.
        
        Returns:
            Health rating: Excellent, Good, Fair, Poor, Critical
        """
        if len(aging_summary) == 0:
            return 'N/A'
        
        total = aging_summary['Amount'].sum()
        if total == 0:
            return 'Excellent'
        
        # Calculate percentage in 90+ bucket
        toxic_pct = aging_summary[
            aging_summary['AgingBucket'] == config.BUCKET_LABELS[3]
        ]['Percentage'].sum()
        
        # Calculate percentage in 61-90 bucket
        warning_pct = aging_summary[
            aging_summary['AgingBucket'] == config.BUCKET_LABELS[2]
        ]['Percentage'].sum()
        
        if toxic_pct > 25:
            return 'Critical'
        elif toxic_pct > 15 or warning_pct > 25:
            return 'Poor'
        elif toxic_pct > 5 or warning_pct > 15:
            return 'Fair'
        elif toxic_pct > 0 or warning_pct > 5:
            return 'Good'
        else:
            return 'Excellent'


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("DSO ANALYSIS MODULE - DEMONSTRATION")
    print("=" * 60)
    
    # Create sample data
    sample_data = pd.DataFrame({
        'InvoiceID': range(1, 11),
        'ClientName': ['Client A'] * 5 + ['Client B'] * 5,
        'InvoiceAmount': [1000, 2500, 1500, 3000, 800, 1200, 2200, 900, 4000, 1800],
        'Status': ['Paid', 'Overdue', 'Pending', 'Overdue', 'Paid',
                   'Pending', 'Overdue', 'Paid', 'Overdue', 'Pending'],
        'DaysOverdue': [0, 45, 15, 95, 0, 25, 75, 0, 120, 35],
        'InvoiceDate': pd.date_range('2024-01-01', periods=10, freq='15D')
    })
    
    analyzer = DSOAnalyzer(sample_data)
    
    print(f"\nDSO: {analyzer.calculate_dso()} days")
    
    print("\nAging Summary:")
    print(analyzer.get_aging_summary())
    
    print("\nToxic Debt (90+ days):")
    toxic = analyzer.identify_toxic_debt()
    print(toxic[['InvoiceID', 'ClientName', 'InvoiceAmount', 'DaysOverdue']])
    
    print("\nHealth Report:")
    report = analyzer.get_dso_health_report()
    print(f"  Total AR: ${report['total_ar']:,.2f}")
    print(f"  Total Overdue: ${report['total_overdue']:,.2f}")
    print(f"  Toxic Debt: ${report['toxic_debt_amount']:,.2f}")
    print(f"  Health Score: {report['health_score']}")
