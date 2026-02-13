"""
Visualizations Module
=====================
Professional financial visualizations using matplotlib and seaborn.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Optional, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def format_currency(value, pos=None):
    """Consistent currency formatter for all charts."""
    if abs(value) >= 1_000_000_000:
        return f'${value/1_000_000_000:.1f}B'
    elif abs(value) >= 1_000_000:
        return f'${value/1_000_000:.1f}M'
    elif abs(value) >= 1_000:
        return f'${value/1_000:.0f}K'
    else:
        return f'${value:.0f}'


class FinancialVisualizer:
    """Professional visualization suite for financial analytics."""
    
    def __init__(self, figsize: Tuple[int, int] = (12, 6)):
        self.figsize = figsize
        self.dpi = config.FIGURE_DPI
        self.currency_formatter = plt.FuncFormatter(format_currency)
        try:
            plt.style.use(config.CHART_STYLE)
        except:
            plt.style.use('seaborn-v0_8-whitegrid')

    
    def plot_aging_buckets(self, aging_summary: pd.DataFrame, 
                           save_path: Optional[str] = None) -> plt.Figure:
        """Create bar chart for aging bucket distribution."""
        fig, ax = plt.subplots(figsize=self.figsize)
        
        bucket_order = config.BUCKET_LABELS
        aging_summary = aging_summary.set_index('AgingBucket').reindex(bucket_order).reset_index()
        
        bars = ax.bar(aging_summary['AgingBucket'], aging_summary['Amount'], 
                      color=config.AGING_COLORS, edgecolor='white')
        
        ax.set_title('AR Amount by Aging Bucket', fontsize=14, fontweight='bold')
        ax.set_xlabel('Aging Bucket')
        ax.set_ylabel('Amount ($)')
        ax.tick_params(axis='x', rotation=15)
        
        for bar, val in zip(bars, aging_summary['Amount']):
            if val > 0:
                ax.annotate(f'${val:,.0f}', 
                           xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                           ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        return fig
    
    def plot_dso_trend(self, trend_data: pd.DataFrame,
                       save_path: Optional[str] = None) -> plt.Figure:
        """Create line chart with DSO trend."""
        fig, ax = plt.subplots(figsize=self.figsize)
        
        ax.plot(trend_data['Period'], trend_data['DSO'], 
                marker='o', linewidth=2, color=config.COLOR_PALETTE['primary'], label='DSO')
        
        if 'MovingAverage' in trend_data.columns:
            ax.plot(trend_data['Period'], trend_data['MovingAverage'],
                   linestyle='--', linewidth=2.5, 
                   color=config.COLOR_PALETTE['warning'], label='Moving Average')
        
        ax.axhline(y=30, color='gray', linestyle=':', alpha=0.7, label='30-Day Target')
        ax.set_title('DSO Trend Analysis', fontsize=14, fontweight='bold')
        ax.set_xlabel('Period')
        ax.set_ylabel('Days Sales Outstanding')
        ax.legend()
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        return fig
    
    def plot_wip_leakage(self, wip_data: pd.DataFrame, top_n: int = 10,
                         save_path: Optional[str] = None) -> plt.Figure:
        """Create horizontal bar chart for WIP by project."""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        plot_data = wip_data.nlargest(top_n, 'UnbilledValue').sort_values('UnbilledValue')
        
        bars = ax.barh(plot_data['ProjectName'], plot_data['UnbilledValue'],
                      color=config.COLOR_PALETTE['danger'], height=0.7)
        
        ax.set_title('Work-in-Progress Leakage Analysis', fontsize=14, fontweight='bold')
        ax.set_xlabel('Unbilled Value ($)')
        
        for bar in bars:
            width = bar.get_width()
            ax.annotate(f'${width:,.0f}', xy=(width, bar.get_y() + bar.get_height()/2),
                       xytext=(5, 0), textcoords='offset points', ha='left', va='center')
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        return fig
    
    def plot_client_grades(self, grade_distribution: pd.DataFrame,
                           save_path: Optional[str] = None) -> plt.Figure:
        """Create pie chart for client risk grades."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        plot_data = grade_distribution[grade_distribution['ClientCount'] > 0]
        if len(plot_data) == 0:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center')
            return fig
        
        colors = [config.RISK_GRADE_COLORS.get(g, 'gray') for g in plot_data['Grade']]
        ax.pie(plot_data['ClientCount'], labels=plot_data['Grade'],
               colors=colors, autopct='%1.0f%%', startangle=90,
               wedgeprops=dict(width=0.6))
        ax.set_title('Client Risk Grade Distribution', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        return fig
    
    def plot_forecast(self, forecast_data: pd.DataFrame,
                      save_path: Optional[str] = None) -> plt.Figure:
        """Create forecast chart with confidence bands."""
        fig, ax = plt.subplots(figsize=self.figsize)
        
        historical = forecast_data[forecast_data['Type'] == 'Historical']
        future = forecast_data[forecast_data['Type'] == 'Forecast']
        
        if len(historical) > 0:
            ax.plot(range(len(historical)), historical['Forecast'],
                   marker='o', linewidth=2, color=config.COLOR_PALETTE['primary'], label='Historical')
        
        if len(future) > 0:
            future_x = range(len(historical), len(historical) + len(future))
            ax.plot(future_x, future['Forecast'], marker='s', linewidth=2,
                   color=config.COLOR_PALETTE['warning'], label='Forecast')
            ax.fill_between(future_x, future['CI_Lower'], future['CI_Upper'],
                          alpha=0.2, color=config.COLOR_PALETTE['warning'])
        
        ax.set_title('Quarterly Cash Inflow Forecast', fontsize=14, fontweight='bold')
        ax.set_xlabel('Period')
        ax.set_ylabel('Cash Inflow ($)')
        ax.legend()
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        return fig
    
    def plot_trend_with_bars(self, trend_data: pd.DataFrame,
                              save_path: Optional[str] = None) -> plt.Figure:
        """
        Create combined chart: bars for values + line for moving average.
        Perfect for predictive analytics visualization.
        """
        fig, ax = plt.subplots(figsize=(14, 7))
        
        x = range(len(trend_data))
        
        # Bar chart for actual values
        bars = ax.bar(x, trend_data['Value'], 
                     color=config.COLOR_PALETTE['secondary'], 
                     alpha=0.7, label='Quarterly Value', width=0.6)
        
        # Line chart for moving average
        if 'MovingAverage' in trend_data.columns:
            ax.plot(x, trend_data['MovingAverage'], 
                   marker='o', linewidth=3, markersize=8,
                   color=config.COLOR_PALETTE['danger'], 
                   label='Moving Average')
        
        # Trend indicators
        if 'Trend' in trend_data.columns:
            for i, (val, trend) in enumerate(zip(trend_data['Value'], trend_data['Trend'])):
                if pd.notna(trend):
                    arrow = '↑' if trend == 'Up' else '↓'
                    color = 'green' if trend == 'Up' else 'red'
                    ax.annotate(arrow, xy=(i, val), 
                               xytext=(0, 10), textcoords='offset points',
                               ha='center', fontsize=14, color=color, fontweight='bold')
        
        ax.set_title('Cash Flow Trend Analysis', fontsize=16, fontweight='bold')
        ax.set_xlabel('Period', fontsize=12)
        ax.set_ylabel('Amount ($)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(trend_data['Period'], rotation=45, ha='right')
        ax.legend(loc='upper right', fontsize=11)
        ax.grid(axis='y', alpha=0.3)
        
        # Format y-axis with consistent currency formatting
        ax.yaxis.set_major_formatter(self.currency_formatter)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        return fig
    
    def plot_forecast_combined(self, forecast_data: pd.DataFrame,
                                save_path: Optional[str] = None) -> plt.Figure:
        """
        Enhanced forecast chart with consistent bar visualization.
        Historical and forecast both shown as bars with different colors.
        Confidence interval shown as error bars on forecast.
        """
        fig, ax = plt.subplots(figsize=(14, 7))
        
        historical = forecast_data[forecast_data['Type'] == 'Historical'].copy()
        future = forecast_data[forecast_data['Type'] == 'Forecast'].copy()
        
        n_hist = len(historical)
        n_future = len(future)
        
        # Historical as bars
        if n_hist > 0:
            hist_x = range(n_hist)
            ax.bar(hist_x, historical['Forecast'], 
                  color=config.COLOR_PALETTE['primary'], 
                  alpha=0.85, label='Historical', width=0.7)
        
        # Forecast as bars with error bars for confidence interval
        if n_future > 0:
            future_x = range(n_hist, n_hist + n_future)
            forecast_values = future['Forecast'].values
            ci_lower = future['CI_Lower'].clip(lower=0).values
            ci_upper = future['CI_Upper'].values
            
            # Calculate error bar sizes
            yerr_lower = forecast_values - ci_lower
            yerr_upper = ci_upper - forecast_values
            
            ax.bar(future_x, forecast_values, 
                  color=config.COLOR_PALETTE['warning'], 
                  alpha=0.85, label='Forecast', width=0.7,
                  yerr=[yerr_lower, yerr_upper],
                  capsize=5, error_kw={'elinewidth': 2, 'capthick': 2, 'alpha': 0.7})
        
        # Labels
        all_labels = list(historical['Period']) + list(future['Period'])
        ax.set_xticks(range(len(all_labels)))
        ax.set_xticklabels(all_labels, rotation=45, ha='right')
        
        # Vertical line separating historical from forecast
        if n_hist > 0 and n_future > 0:
            ax.axvline(x=n_hist - 0.5, color='gray', linestyle='--', linewidth=2, alpha=0.5)
            ax.text(n_hist + 0.2, ax.get_ylim()[1] * 0.95, 'Forecast', 
                   fontsize=11, color='gray', va='top', fontweight='bold')
        
        ax.set_title('Quarterly Cash Inflow: Historical vs Forecast', fontsize=16, fontweight='bold')
        ax.set_xlabel('Period', fontsize=12)
        ax.set_ylabel('Cash Inflow ($)', fontsize=12)
        ax.legend(loc='upper left', fontsize=11)
        ax.grid(axis='y', alpha=0.3)
        ax.yaxis.set_major_formatter(self.currency_formatter)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        return fig
    
    def plot_forecast_line(self, forecast_data: pd.DataFrame,
                            save_path: Optional[str] = None) -> plt.Figure:
        """
        Forecast chart using consistent LINE chart for all data.
        Historical and forecast shown as continuous line with markers.
        Confidence interval shown as shaded region.
        """
        fig, ax = plt.subplots(figsize=(14, 7))
        
        historical = forecast_data[forecast_data['Type'] == 'Historical'].copy()
        future = forecast_data[forecast_data['Type'] == 'Forecast'].copy()
        
        n_hist = len(historical)
        n_future = len(future)
        
        # Historical as line
        if n_hist > 0:
            hist_x = list(range(n_hist))
            ax.plot(hist_x, historical['Forecast'], 
                   marker='o', linewidth=2.5, markersize=8,
                   color=config.COLOR_PALETTE['primary'], 
                   label='Historical')
        
        # Forecast as line with confidence interval
        if n_future > 0:
            # Connect historical to forecast with a line segment
            future_x = list(range(n_hist - 1, n_hist + n_future)) if n_hist > 0 else list(range(n_future))
            
            # Include last historical point for continuity
            if n_hist > 0:
                forecast_line = [historical['Forecast'].iloc[-1]] + list(future['Forecast'])
                ci_lower = [historical['Forecast'].iloc[-1]] + list(future['CI_Lower'].clip(lower=0))
                ci_upper = [historical['Forecast'].iloc[-1]] + list(future['CI_Upper'])
            else:
                forecast_line = list(future['Forecast'])
                ci_lower = list(future['CI_Lower'].clip(lower=0))
                ci_upper = list(future['CI_Upper'])
            
            ax.plot(future_x, forecast_line, 
                   marker='D', linewidth=2.5, markersize=8,
                   color=config.COLOR_PALETTE['warning'], 
                   label='Forecast')
            
            # Confidence interval as shaded region
            ax.fill_between(future_x, ci_lower, ci_upper,
                          alpha=0.25, color=config.COLOR_PALETTE['warning'],
                          label='95% Confidence Interval')
        
        # Labels
        all_labels = list(historical['Period']) + list(future['Period'])
        ax.set_xticks(range(len(all_labels)))
        ax.set_xticklabels(all_labels, rotation=45, ha='right')
        
        # Vertical line separating historical from forecast
        if n_hist > 0 and n_future > 0:
            ax.axvline(x=n_hist - 0.5, color='gray', linestyle='--', linewidth=2, alpha=0.5)
            ax.text(n_hist + 0.2, ax.get_ylim()[1] * 0.95, 'Forecast', 
                   fontsize=11, color='gray', va='top', fontweight='bold')
        
        ax.set_title('Quarterly Cash Inflow: Trend & Forecast', fontsize=16, fontweight='bold')
        ax.set_xlabel('Period', fontsize=12)
        ax.set_ylabel('Cash Inflow ($)', fontsize=12)
        ax.legend(loc='upper left', fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_formatter(self.currency_formatter)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        return fig
    
    def plot_predictive_dashboard(self, trend_data: pd.DataFrame,
                                   forecast_data: pd.DataFrame,
                                   at_risk_clients: pd.DataFrame = None,
                                   save_path: Optional[str] = None) -> plt.Figure:
        """
        Create a 2x2 dashboard for predictive analytics.
        Shows: Trend, Forecast, At-Risk Clients, Summary Stats.
        """
        fig = plt.figure(figsize=(16, 12))
        
        # 1. Trend with Moving Average (top-left)
        ax1 = fig.add_subplot(2, 2, 1)
        if len(trend_data) > 0:
            x = range(len(trend_data))
            ax1.bar(x, trend_data['Value'], color=config.COLOR_PALETTE['secondary'], alpha=0.7, width=0.6)
            if 'MovingAverage' in trend_data.columns:
                ax1.plot(x, trend_data['MovingAverage'], marker='o', linewidth=2.5, 
                        color=config.COLOR_PALETTE['danger'], label='MA')
            ax1.set_xticks(x)
            ax1.set_xticklabels(trend_data['Period'], rotation=45, ha='right', fontsize=9)
            ax1.set_title('Quarterly Trend & Moving Average', fontweight='bold')
            ax1.legend()
            ax1.grid(axis='y', alpha=0.3)
        
        # 2. Forecast Chart (top-right)
        ax2 = fig.add_subplot(2, 2, 2)
        historical = forecast_data[forecast_data['Type'] == 'Historical']
        future = forecast_data[forecast_data['Type'] == 'Forecast']
        if len(historical) > 0:
            ax2.bar(range(len(historical)), historical['Forecast'], 
                   color=config.COLOR_PALETTE['primary'], alpha=0.8, label='Historical')
        if len(future) > 0:
            future_x = range(len(historical), len(historical) + len(future))
            ax2.plot(future_x, future['Forecast'], marker='D', linewidth=2.5,
                    color=config.COLOR_PALETTE['warning'], label='Forecast')
            ax2.fill_between(future_x, future['CI_Lower'].clip(lower=0), future['CI_Upper'],
                           alpha=0.2, color=config.COLOR_PALETTE['warning'])
        ax2.set_title('Cash Inflow Forecast', fontweight='bold')
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)
        
        # 3. At-Risk Clients (bottom-left)
        ax3 = fig.add_subplot(2, 2, 3)
        if at_risk_clients is not None and len(at_risk_clients) > 0:
            risk_data = at_risk_clients.head(10)
            colors = ['#ff6b6b' if r == 'High' else '#ffd93d' for r in risk_data['RiskLevel']]
            ax3.barh(risk_data['ClientName'], risk_data['RiskProbability'] * 100, color=colors)
            ax3.set_xlabel('Risk Probability (%)')
            ax3.set_title('Top At-Risk Clients', fontweight='bold')
        else:
            ax3.text(0.5, 0.5, 'No At-Risk Clients\nIdentified', 
                    ha='center', va='center', fontsize=14, transform=ax3.transAxes)
            ax3.set_title('At-Risk Clients', fontweight='bold')
        
        # 4. Summary Statistics (bottom-right)
        ax4 = fig.add_subplot(2, 2, 4)
        ax4.axis('off')
        
        # Calculate summary stats
        if len(trend_data) > 0:
            latest_val = trend_data['Value'].iloc[-1] if 'Value' in trend_data.columns else 0
            avg_val = trend_data['Value'].mean() if 'Value' in trend_data.columns else 0
            trend_dir = trend_data['Trend'].iloc[-1] if 'Trend' in trend_data.columns else 'N/A'
        else:
            latest_val, avg_val, trend_dir = 0, 0, 'N/A'
        
        n_forecast = len(future) if len(future) > 0 else 0
        n_at_risk = len(at_risk_clients) if at_risk_clients is not None else 0
        
        summary_text = f"""
        PREDICTIVE ANALYTICS SUMMARY
        {'='*40}
        
        📊 Latest Quarter Value:  ${latest_val:,.0f}
        📈 Average Quarterly:     ${avg_val:,.0f}
        🔄 Current Trend:         {trend_dir}
        
        🔮 Forecast Periods:      {n_forecast}
        ⚠️ At-Risk Clients:       {n_at_risk}
        
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        ax4.text(0.1, 0.5, summary_text, transform=ax4.transAxes, fontsize=12,
                verticalalignment='center', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6'))
        
        plt.suptitle('Financial Predictive Analytics Dashboard', fontsize=18, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
        return fig
