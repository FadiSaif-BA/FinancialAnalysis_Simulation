"""
Risk Scoring Module
===================
Client risk grading based on payment behavior and variance analysis.
Assigns grades A-F based on historical payment patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class RiskScorer:
    """
    Client Risk Scoring and Grading System.
    
    Risk Grade Thresholds (based on average days variance from contractual terms):
    - A: ≤10 days (Excellent)
    - B: 11-20 days (Good)
    - C: 21-40 days (Watch)
    - D: 41-60 days (At Risk)
    - F: 61+ days (Default Risk)
    
    Payment Variance = Actual Days to Pay - Contractual Terms
    """
    
    def __init__(self, invoices_df: pd.DataFrame):
        """
        Initialize Risk Scorer with invoice data.
        
        Args:
            invoices_df: Cleaned invoices DataFrame with payment history
        """
        self.df = invoices_df.copy()
        self._validate_and_prepare_data()
    
    def _validate_and_prepare_data(self):
        """Ensure required columns exist and prepare data."""
        # Calculate DaysToCollect if not present
        if 'DaysToCollect' not in self.df.columns:
            if 'PaidDate' in self.df.columns and 'InvoiceDate' in self.df.columns:
                self.df['InvoiceDate'] = pd.to_datetime(self.df['InvoiceDate'])
                self.df['PaidDate'] = pd.to_datetime(self.df['PaidDate'])
                self.df['DaysToCollect'] = (self.df['PaidDate'] - self.df['InvoiceDate']).dt.days
        
        # Calculate PaymentVariance if not present
        if 'PaymentVariance' not in self.df.columns:
            if 'DaysToCollect' in self.df.columns and 'PaymentTerms' in self.df.columns:
                self.df['PaymentVariance'] = self.df['DaysToCollect'] - self.df['PaymentTerms']
    
    def calculate_payment_variance(self) -> pd.DataFrame:
        """
        Calculate payment variance for each invoice.
        
        Variance = Actual Days to Pay - Contractual Terms
        
        Returns:
            DataFrame with variance calculations
        """
        df = self.df.copy()
        
        # Only include paid invoices for variance calculation
        paid_df = df[df['Status'].str.lower() == 'paid'].copy()
        
        if len(paid_df) == 0:
            return pd.DataFrame(columns=['InvoiceID', 'ClientName', 'PaymentVariance'])
        
        result = paid_df[['InvoiceID', 'ClientName', 'InvoiceAmount', 
                          'PaymentTerms', 'DaysToCollect', 'PaymentVariance']].copy()
        
        # Classify variance
        result['VarianceCategory'] = pd.cut(
            result['PaymentVariance'],
            bins=[-float('inf'), 0, 10, 30, 60, float('inf')],
            labels=['Early/On-Time', 'Slightly Late', 'Late', 'Very Late', 'Severely Late']
        )
        
        return result.sort_values('PaymentVariance', ascending=False)
    
    def grade_clients(self) -> pd.DataFrame:
        """
        Assign risk grades (A-F) to each client.
        
        Returns:
            DataFrame with ClientName, AvgVariance, Grade, GradeDescription
        """
        # Get paid invoices with variance data
        paid_df = self.df[
            (self.df['Status'].str.lower() == 'paid') & 
            (self.df['PaymentVariance'].notna())
        ].copy()
        
        if len(paid_df) == 0:
            # If no paid invoices, grade based on overdue status
            return self._grade_by_overdue_status()
        
        # Calculate average variance per client
        client_stats = paid_df.groupby('ClientName', as_index=False).agg({
            'PaymentVariance': ['mean', 'std', 'count'],
            'InvoiceAmount': 'sum'
        })
        
        client_stats.columns = ['ClientName', 'AvgVariance', 'StdVariance', 
                                'InvoiceCount', 'TotalValue']
        
        # Assign grades
        client_stats['Grade'] = client_stats['AvgVariance'].apply(self._assign_grade)
        client_stats['GradeDescription'] = client_stats['Grade'].map(config.RISK_GRADE_DESCRIPTIONS)
        
        # Calculate risk score (0-100)
        max_variance = client_stats['AvgVariance'].max()
        if max_variance > 0:
            client_stats['RiskScore'] = (client_stats['AvgVariance'] / max_variance * 100).clip(0, 100).round(1)
        else:
            client_stats['RiskScore'] = 0
        
        return client_stats.sort_values('AvgVariance', ascending=False)
    
    def _grade_by_overdue_status(self) -> pd.DataFrame:
        """
        Grade clients based on current overdue amount when no payment history.
        """
        client_stats = self.df.groupby('ClientName', as_index=False).agg({
            'InvoiceAmount': 'sum',
            'DaysOverdue': 'mean'
        })
        client_stats.columns = ['ClientName', 'TotalValue', 'AvgDaysOverdue']
        
        client_stats['AvgVariance'] = client_stats['AvgDaysOverdue']
        client_stats['Grade'] = client_stats['AvgVariance'].apply(self._assign_grade)
        client_stats['GradeDescription'] = client_stats['Grade'].map(config.RISK_GRADE_DESCRIPTIONS)
        client_stats['RiskScore'] = (client_stats['AvgVariance'] / 90 * 100).clip(0, 100).round(1)
        
        return client_stats.sort_values('AvgVariance', ascending=False)
    
    def _assign_grade(self, avg_variance: float) -> str:
        """
        Assign letter grade based on average variance.
        
        Args:
            avg_variance: Average days variance from terms
            
        Returns:
            Grade letter (A, B, C, D, or F)
        """
        if pd.isna(avg_variance):
            return 'N/A'
        
        for grade, threshold in config.RISK_GRADE_THRESHOLDS.items():
            if avg_variance <= threshold:
                return grade
        
        return 'F'
    
    def get_top_risk_projects(self, n: int = 10) -> pd.DataFrame:
        """
        Get top N projects by risk level.
        
        Args:
            n: Number of projects to return
            
        Returns:
            DataFrame with highest-risk projects
        """
        # Calculate risk at project level
        project_risk = self.df.groupby('ProjectName', as_index=False).agg({
            'InvoiceAmount': 'sum',
            'DaysOverdue': 'max',
            'PaymentVariance': 'mean'
        })
        project_risk.columns = ['ProjectName', 'TotalValue', 'MaxDaysOverdue', 'AvgVariance']
        
        # Composite risk score
        project_risk['RiskScore'] = (
            project_risk['MaxDaysOverdue'].fillna(0) * 0.5 +
            project_risk['AvgVariance'].fillna(0) * 0.5
        ).clip(0, 100)
        
        project_risk['Grade'] = project_risk['RiskScore'].apply(
            lambda x: self._assign_grade(x) if pd.notna(x) else 'N/A'
        )
        
        return project_risk.nlargest(n, 'RiskScore')
    
    def get_risk_distribution(self) -> pd.DataFrame:
        """
        Get distribution of clients across risk grades.
        
        Returns:
            DataFrame with Grade, Count, TotalValue, Percentage
        """
        graded_clients = self.grade_clients()
        
        distribution = graded_clients.groupby('Grade', as_index=False).agg({
            'ClientName': 'count',
            'TotalValue': 'sum'
        })
        distribution.columns = ['Grade', 'ClientCount', 'TotalValue']
        
        total_value = distribution['TotalValue'].sum()
        distribution['ValuePercentage'] = (distribution['TotalValue'] / total_value * 100).round(1)
        
        # Ensure all grades are represented
        all_grades = pd.DataFrame({'Grade': list(config.RISK_GRADE_THRESHOLDS.keys())})
        distribution = all_grades.merge(distribution, on='Grade', how='left').fillna(0)
        distribution['GradeDescription'] = distribution['Grade'].map(config.RISK_GRADE_DESCRIPTIONS)
        
        return distribution
    
    def get_risk_health_report(self) -> Dict:
        """
        Generate comprehensive risk health report.
        
        Returns:
            Dictionary with risk metrics and analysis
        """
        graded_clients = self.grade_clients()
        distribution = self.get_risk_distribution()
        top_risk = self.get_top_risk_projects()
        
        # Calculate high-risk exposure
        high_risk_clients = graded_clients[graded_clients['Grade'].isin(['D', 'F'])]
        high_risk_value = high_risk_clients['TotalValue'].sum() if len(high_risk_clients) > 0 else 0
        total_value = graded_clients['TotalValue'].sum()
        
        report = {
            'total_clients_graded': len(graded_clients),
            'grade_distribution': distribution.to_dict('records'),
            'high_risk_client_count': len(high_risk_clients),
            'high_risk_value': high_risk_value,
            'high_risk_percentage': (high_risk_value / total_value * 100) if total_value > 0 else 0,
            'top_risk_projects': top_risk.head(5).to_dict('records'),
            'average_variance': graded_clients['AvgVariance'].mean() if len(graded_clients) > 0 else 0,
            'portfolio_grade': self._calculate_portfolio_grade(graded_clients)
        }
        
        return report
    
    def _calculate_portfolio_grade(self, graded_clients: pd.DataFrame) -> str:
        """
        Calculate overall portfolio grade based on value-weighted client grades.
        """
        if len(graded_clients) == 0:
            return 'N/A'
        
        grade_values = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'F': 4, 'N/A': 2}
        
        total_value = graded_clients['TotalValue'].sum()
        if total_value == 0:
            return 'N/A'
        
        weighted_score = sum(
            grade_values.get(row['Grade'], 2) * row['TotalValue']
            for _, row in graded_clients.iterrows()
        ) / total_value
        
        if weighted_score <= 0.5:
            return 'A'
        elif weighted_score <= 1.5:
            return 'B'
        elif weighted_score <= 2.5:
            return 'C'
        elif weighted_score <= 3.5:
            return 'D'
        else:
            return 'F'
    
    def get_watch_list(self, grade_threshold: str = 'C') -> pd.DataFrame:
        """
        Get list of clients that need monitoring.
        
        Args:
            grade_threshold: Minimum grade to include (C, D, or F)
            
        Returns:
            DataFrame with clients requiring attention
        """
        graded = self.grade_clients()
        
        grades_to_watch = {'C': ['C', 'D', 'F'], 'D': ['D', 'F'], 'F': ['F']}
        watch_grades = grades_to_watch.get(grade_threshold, ['C', 'D', 'F'])
        
        watch_list = graded[graded['Grade'].isin(watch_grades)].copy()
        watch_list['ActionRequired'] = watch_list['Grade'].map({
            'C': 'Monitor closely',
            'D': 'Escalate to management',
            'F': 'Collection action required'
        })
        
        return watch_list.sort_values('RiskScore', ascending=False)


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("RISK SCORING MODULE - DEMONSTRATION")
    print("=" * 60)
    
    # Create sample data
    sample_data = pd.DataFrame({
        'InvoiceID': range(1, 16),
        'ClientName': ['Client A'] * 5 + ['Client B'] * 5 + ['Client C'] * 5,
        'ProjectName': ['Project 1'] * 5 + ['Project 2'] * 5 + ['Project 3'] * 5,
        'InvoiceAmount': [10000, 15000, 20000, 8000, 12000] * 3,
        'Status': ['Paid'] * 12 + ['Overdue'] * 3,
        'PaymentTerms': [30] * 15,
        'DaysToCollect': [25, 28, 32, 35, 30,  # Client A - Good
                          45, 52, 60, 55, 48,  # Client B - Watch
                          75, 82, 90, None, None],  # Client C - At Risk
        'DaysOverdue': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 45, 60, 75]
    })
    
    # Calculate variance
    sample_data['PaymentVariance'] = sample_data['DaysToCollect'] - sample_data['PaymentTerms']
    
    scorer = RiskScorer(sample_data)
    
    print("\nClient Grades:")
    print(scorer.grade_clients()[['ClientName', 'AvgVariance', 'Grade', 'RiskScore']])
    
    print("\nGrade Distribution:")
    print(scorer.get_risk_distribution()[['Grade', 'ClientCount', 'ValuePercentage']])
    
    print("\nRisk Health Report:")
    report = scorer.get_risk_health_report()
    print(f"  Clients Graded: {report['total_clients_graded']}")
    print(f"  High-Risk Clients: {report['high_risk_client_count']}")
    print(f"  High-Risk Value: ${report['high_risk_value']:,.2f}")
    print(f"  Portfolio Grade: {report['portfolio_grade']}")
    
    print("\nWatch List:")
    print(scorer.get_watch_list()[['ClientName', 'Grade', 'ActionRequired']])
