"""
Predictive Analytics Module
===========================
Time-series forecasting and predictive risk modeling.
Includes moving averages, cohort analysis, and cash flow forecasting.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from scipy import stats
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class PredictiveAnalyzer:
    """
    Predictive Analytics for Financial Forecasting.
    
    Features:
    - Moving Average calculations for trend smoothing
    - Quarterly cash flow forecasting with confidence intervals
    - Client cohort analysis based on payment behavior
    - At-risk client prediction
    """
    
    def __init__(self, invoices_df: pd.DataFrame):
        """
        Initialize Predictive Analyzer with invoice data.
        
        Args:
            invoices_df: Cleaned invoices DataFrame with date columns
        """
        self.df = invoices_df.copy()
        self._prepare_time_series_data()
    
    def _prepare_time_series_data(self):
        """Prepare data for time series analysis."""
        if 'InvoiceDate' in self.df.columns:
            self.df['InvoiceDate'] = pd.to_datetime(self.df['InvoiceDate'])
            self.df['YearMonth'] = self.df['InvoiceDate'].dt.to_period('M')
            self.df['Quarter'] = self.df['InvoiceDate'].dt.to_period('Q')
            self.df['Year'] = self.df['InvoiceDate'].dt.year
    
    def calculate_moving_average(self, column: str = 'InvoiceAmount', 
                                  window: int = None,
                                  period: str = 'M') -> pd.DataFrame:
        """
        Calculate moving average for a given column over time.
        
        Args:
            column: Column to calculate MA for
            window: Window size for MA (default from config)
            period: Time period - 'M' for monthly, 'Q' for quarterly
            
        Returns:
            DataFrame with Period, Value, and MovingAverage columns
        """
        window = window or config.MOVING_AVERAGE_WINDOW
        
        # Aggregate by period
        if period == 'ME':
            period_col = 'YearMonth'
        else:
            period_col = 'Quarter'
        
        if period_col not in self.df.columns:
            raise ValueError(f"Period column {period_col} not found")
        
        time_series = self.df.groupby(period_col, as_index=False).agg({
            column: 'sum',
            'InvoiceID': 'count'
        })
        time_series.columns = ['Period', 'Value', 'Count']
        
        # Calculate moving average
        time_series['MovingAverage'] = time_series['Value'].rolling(
            window=window, min_periods=1
        ).mean()
        
        # Calculate trend direction
        time_series['Trend'] = time_series['MovingAverage'].diff().apply(
            lambda x: 'Up' if x > 0 else ('Down' if x < 0 else 'Flat')
        )
        
        time_series['Period'] = time_series['Period'].astype(str)
        
        return time_series
    
    def forecast_quarterly_inflow(self, periods_ahead: int = None) -> pd.DataFrame:
        """
        Forecast quarterly cash inflow using linear regression.
        
        Args:
            periods_ahead: Number of quarters to forecast
            
        Returns:
            DataFrame with forecasted values and confidence intervals
        """
        periods_ahead = periods_ahead or config.FORECAST_PERIODS
        
        # Aggregate by quarter
        quarterly = self.df.groupby('Quarter', as_index=False).agg({
            'InvoiceAmount': 'sum'
        })
        quarterly.columns = ['Quarter', 'CashInflow']
        quarterly['Quarter'] = quarterly['Quarter'].astype(str)
        quarterly = quarterly.sort_values('Quarter')
        
        # Create numeric index for regression
        quarterly['PeriodIndex'] = range(len(quarterly))
        
        if len(quarterly) < 3:
            return pd.DataFrame({'Message': ['Insufficient data for forecasting']})
        
        # Linear regression
        X = quarterly['PeriodIndex'].values
        y = quarterly['CashInflow'].values
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
        
        # Calculate historical standard deviation for realistic CI
        y_std = np.std(y)
        y_mean = np.mean(y)
        
        # Generate forecasts
        last_index = quarterly['PeriodIndex'].max()
        forecast_indices = range(int(last_index) + 1, int(last_index) + periods_ahead + 1)
        
        forecasts = []
        for i, idx in enumerate(forecast_indices):
            predicted = intercept + slope * idx
            
            # Use a reasonable confidence interval based on historical variance
            # CI widens slightly for each period ahead
            ci_width = y_std * (1 + 0.1 * i) * config.CONFIDENCE_INTERVAL
            ci_lower = predicted - ci_width
            ci_upper = predicted + ci_width
            
            forecasts.append({
                'Period': f'Q{idx - last_index} Ahead',
                'Forecast': max(0, predicted),
                'CI_Lower': max(0, ci_lower),
                'CI_Upper': max(0, ci_upper),
                'Type': 'Forecast'
            })
        
        # Combine historical and forecast
        historical = quarterly[['Quarter', 'CashInflow']].copy()
        historical.columns = ['Period', 'Forecast']
        historical['CI_Lower'] = historical['Forecast']
        historical['CI_Upper'] = historical['Forecast']
        historical['Type'] = 'Historical'
        
        forecast_df = pd.concat([historical, pd.DataFrame(forecasts)], ignore_index=True)
        forecast_df['R_Squared'] = r_value ** 2
        
        return forecast_df
    
    def forecast_monthly_inflow(self, periods_ahead: int = 6) -> pd.DataFrame:
        """
        Forecast monthly cash inflow using linear regression.
        
        Args:
            periods_ahead: Number of months to forecast (default 6)
            
        Returns:
            DataFrame with forecasted values and confidence intervals
        """
        # Aggregate by month
        monthly = self.df.groupby('YearMonth', as_index=False).agg({
            'InvoiceAmount': 'sum'
        })
        monthly.columns = ['YearMonth', 'CashInflow']
        monthly['YearMonth'] = monthly['YearMonth'].astype(str)
        monthly = monthly.sort_values('YearMonth')
        
        # Create numeric index for regression
        monthly['PeriodIndex'] = range(len(monthly))
        
        if len(monthly) < 3:
            return pd.DataFrame({'Message': ['Insufficient data for forecasting']})
        
        # Linear regression
        X = monthly['PeriodIndex'].values
        y = monthly['CashInflow'].values
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
        
        # Calculate historical standard deviation for realistic CI
        y_std = np.std(y)
        
        # Generate forecasts
        last_index = monthly['PeriodIndex'].max()
        forecast_indices = range(int(last_index) + 1, int(last_index) + periods_ahead + 1)
        
        forecasts = []
        for i, idx in enumerate(forecast_indices):
            predicted = intercept + slope * idx
            
            # Use a reasonable confidence interval based on historical variance
            # CI widens slightly for each period ahead
            ci_width = y_std * (1 + 0.05 * i) * config.CONFIDENCE_INTERVAL
            ci_lower = predicted - ci_width
            ci_upper = predicted + ci_width
            
            forecasts.append({
                'Period': f'M+{idx - last_index}',
                'Forecast': max(0, predicted),
                'CI_Lower': max(0, ci_lower),
                'CI_Upper': max(0, ci_upper),
                'Type': 'Forecast'
            })
        
        # Combine historical and forecast
        historical = monthly[['YearMonth', 'CashInflow']].copy()
        historical.columns = ['Period', 'Forecast']
        historical['CI_Lower'] = historical['Forecast']
        historical['CI_Upper'] = historical['Forecast']
        historical['Type'] = 'Historical'
        
        forecast_df = pd.concat([historical, pd.DataFrame(forecasts)], ignore_index=True)
        forecast_df['R_Squared'] = r_value ** 2
        
        return forecast_df
    
    def cohort_analysis(self) -> pd.DataFrame:
        """
        Analyze client cohorts based on payment behavior patterns.
        
        Returns:
            DataFrame with cohort assignments and characteristics
        """
        # Calculate client-level metrics
        if 'PaymentVariance' not in self.df.columns:
            if 'DaysToCollect' in self.df.columns and 'PaymentTerms' in self.df.columns:
                self.df['PaymentVariance'] = self.df['DaysToCollect'] - self.df['PaymentTerms']
        
        client_metrics = self.df.groupby('ClientName', as_index=False).agg({
            'InvoiceAmount': ['sum', 'mean', 'count'],
            'PaymentVariance': 'mean',
            'DaysOverdue': 'mean'
        })
        client_metrics.columns = ['ClientName', 'TotalValue', 'AvgInvoice', 
                                   'InvoiceCount', 'AvgVariance', 'AvgDaysOverdue']
        
        # Fill NAs
        client_metrics = client_metrics.fillna(0)
        
        # Define cohorts based on behavior
        def assign_cohort(row):
            variance = row['AvgVariance']
            value = row['TotalValue']
            median_value = client_metrics['TotalValue'].median()
            
            if variance <= 0:
                behavior = 'Early Payer'
            elif variance <= 10:
                behavior = 'On-Time Payer'
            elif variance <= 30:
                behavior = 'Slow Payer'
            else:
                behavior = 'Problem Payer'
            
            size = 'High Value' if value >= median_value else 'Low Value'
            
            return f'{size} - {behavior}'
        
        client_metrics['Cohort'] = client_metrics.apply(assign_cohort, axis=1)
        
        # Calculate cohort summaries
        cohort_summary = client_metrics.groupby('Cohort', as_index=False).agg({
            'ClientName': 'count',
            'TotalValue': 'sum',
            'AvgVariance': 'mean'
        })
        cohort_summary.columns = ['Cohort', 'ClientCount', 'TotalValue', 'AvgVariance']
        
        return client_metrics, cohort_summary
    
    def predict_at_risk_clients(self, threshold_days: int = 30) -> pd.DataFrame:
        """
        Predict which clients are likely to violate payment terms next period.
        
        Uses historical variance trends to identify deteriorating payment behavior.
        
        Args:
            threshold_days: Days of expected delay to flag as at-risk
            
        Returns:
            DataFrame with at-risk clients and probability scores
        """
        # Get recent payment behavior (last 3 months)
        if 'InvoiceDate' in self.df.columns:
            cutoff_date = self.df['InvoiceDate'].max() - timedelta(days=90)
            recent_df = self.df[self.df['InvoiceDate'] >= cutoff_date]
        else:
            recent_df = self.df.tail(int(len(self.df) * 0.3))
        
        # Calculate recent variance
        recent_metrics = recent_df.groupby('ClientName', as_index=False).agg({
            'PaymentVariance': ['mean', 'std'],
            'DaysOverdue': 'mean',
            'InvoiceAmount': 'sum'
        })
        recent_metrics.columns = ['ClientName', 'RecentAvgVariance', 'VarianceStd', 
                                   'RecentAvgOverdue', 'RecentValue']
        
        # Calculate historical variance
        historical_metrics = self.df.groupby('ClientName', as_index=False).agg({
            'PaymentVariance': 'mean'
        })
        historical_metrics.columns = ['ClientName', 'HistoricalAvgVariance']
        
        # Merge and calculate trend
        risk_df = recent_metrics.merge(historical_metrics, on='ClientName', how='left')
        risk_df = risk_df.fillna(0)
        
        # Calculate trend (positive = deteriorating)
        risk_df['VarianceTrend'] = risk_df['RecentAvgVariance'] - risk_df['HistoricalAvgVariance']
        
        # Risk probability score
        risk_df['RiskProbability'] = (
            risk_df['RecentAvgVariance'].clip(0, 100) / 100 * 0.4 +
            risk_df['VarianceTrend'].clip(0, 50) / 50 * 0.3 +
            risk_df['RecentAvgOverdue'].clip(0, 90) / 90 * 0.3
        ).clip(0, 1)
        
        # Flag at-risk
        risk_df['AtRisk'] = (
            (risk_df['RecentAvgVariance'] > threshold_days) | 
            (risk_df['VarianceTrend'] > 15)
        )
        
        risk_df['RiskLevel'] = pd.cut(
            risk_df['RiskProbability'],
            bins=[0, 0.25, 0.5, 0.75, 1.0],
            labels=['Low', 'Medium', 'High', 'Critical']
        )
        
        return risk_df.sort_values('RiskProbability', ascending=False)
    
    def get_trend_insights(self) -> Dict:
        """
        Generate trend insights and recommendations.
        
        Returns:
            Dictionary with trend analysis and insights
        """
        ma_data = self.calculate_moving_average()
        forecast_data = self.forecast_quarterly_inflow()
        at_risk = self.predict_at_risk_clients()
        client_metrics, cohort_summary = self.cohort_analysis()
        
        # Determine overall trend
        if len(ma_data) >= 3:
            recent_ma = ma_data['MovingAverage'].tail(3).tolist()
            if recent_ma[-1] > recent_ma[0]:
                trend_direction = 'Improving'
            elif recent_ma[-1] < recent_ma[0]:
                trend_direction = 'Declining'
            else:
                trend_direction = 'Stable'
        else:
            trend_direction = 'Insufficient Data'
        
        insights = {
            'trend_direction': trend_direction,
            'moving_average_current': ma_data['MovingAverage'].iloc[-1] if len(ma_data) > 0 else 0,
            'forecast_next_quarter': forecast_data[forecast_data['Type'] == 'Forecast']['Forecast'].iloc[0] if len(forecast_data[forecast_data['Type'] == 'Forecast']) > 0 else 0,
            'r_squared': forecast_data['R_Squared'].iloc[0] if 'R_Squared' in forecast_data.columns else 0,
            'at_risk_clients': len(at_risk[at_risk['AtRisk'] == True]),
            'high_risk_clients': len(at_risk[at_risk['RiskLevel'] == 'Critical']),
            'cohort_breakdown': cohort_summary.to_dict('records') if len(cohort_summary) > 0 else [],
            'recommendations': self._generate_recommendations(trend_direction, at_risk, cohort_summary)
        }
        
        return insights
    
    def _generate_recommendations(self, trend: str, at_risk: pd.DataFrame, 
                                   cohorts: pd.DataFrame) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        if trend == 'Declining':
            recommendations.append("Cash flow trend is declining - review collection processes")
        
        high_risk_count = len(at_risk[at_risk['RiskLevel'].isin(['High', 'Critical'])])
        if high_risk_count > 0:
            recommendations.append(f"Monitor {high_risk_count} high-risk clients for potential payment issues")
        
        if len(cohorts) > 0:
            problem_cohorts = cohorts[cohorts['Cohort'].str.contains('Problem')]
            if len(problem_cohorts) > 0:
                recommendations.append("Consider credit limit adjustments for Problem Payer cohort")
        
        if not recommendations:
            recommendations.append("Portfolio performance is healthy - maintain current practices")
        
        return recommendations


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("PREDICTIVE ANALYTICS MODULE - DEMONSTRATION")
    print("=" * 60)
    
    # Create sample time series data
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=24, freq='ME')
    sample_data = pd.DataFrame({
        'InvoiceID': range(1, 241),
        'ClientName': np.random.choice(['Client A', 'Client B', 'Client C'], 240),
        'InvoiceAmount': np.random.uniform(5000, 50000, 240),
        'InvoiceDate': np.random.choice(dates, 240),
        'PaymentTerms': 30,
        'DaysToCollect': np.random.randint(20, 60, 240),
        'DaysOverdue': np.random.randint(0, 45, 240),
        'Status': np.random.choice(['Paid', 'Pending', 'Overdue'], 240, p=[0.7, 0.2, 0.1])
    })
    sample_data['PaymentVariance'] = sample_data['DaysToCollect'] - sample_data['PaymentTerms']
    
    analyzer = PredictiveAnalyzer(sample_data)
    
    print("\nMoving Average Trend:")
    ma = analyzer.calculate_moving_average()
    print(ma.tail(6)[['Period', 'Value', 'MovingAverage', 'Trend']])
    
    print("\nQuarterly Forecast:")
    forecast = analyzer.forecast_quarterly_inflow(4)
    print(forecast[['Period', 'Forecast', 'CI_Lower', 'CI_Upper', 'Type']].tail(6))
    
    print("\nAt-Risk Clients:")
    at_risk = analyzer.predict_at_risk_clients()
    print(at_risk[at_risk['AtRisk']][['ClientName', 'RiskProbability', 'RiskLevel']])
    
    print("\nTrend Insights:")
    insights = analyzer.get_trend_insights()
    print(f"  Trend Direction: {insights['trend_direction']}")
    print(f"  At-Risk Clients: {insights['at_risk_clients']}")
    print(f"  Recommendations:")
    for rec in insights['recommendations']:
        print(f"    - {rec}")
