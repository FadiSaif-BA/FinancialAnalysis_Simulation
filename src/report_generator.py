"""
Report Generator Module
=======================
Automated report creation and export utilities.
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class ReportGenerator:
    """Automated financial report generation and export."""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or config.REPORTS_DIR
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp for filenames."""
        return datetime.now().strftime(config.DATE_FORMAT)
    
    def generate_health_report(self, dso_report: Dict, wip_report: Dict, 
                                risk_report: Dict) -> str:
        """Generate console health report summary."""
        report = []
        report.append("=" * 60)
        report.append("FINANCIAL HEALTH CHECK")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        # DSO Section
        report.append("\n📊 ACCOUNTS RECEIVABLE")
        report.append(f"  DSO: {dso_report.get('dso', 'N/A')} days")
        report.append(f"  Total AR: ${dso_report.get('total_ar', 0):,.2f}")
        report.append(f"  Total Overdue: ${dso_report.get('total_overdue', 0):,.2f}")
        report.append(f"  Toxic Debt (90+): ${dso_report.get('toxic_debt_amount', 0):,.2f}")
        report.append(f"  Health Score: {dso_report.get('health_score', 'N/A')}")
        
        # WIP Section
        report.append("\n🔧 WORK-IN-PROGRESS")
        report.append(f"  Total WIP Value: ${wip_report.get('total_wip_value', 0):,.2f}")
        report.append(f"  Leakage Coefficient: {wip_report.get('leakage_percentage', 0):.1f}%")
        report.append(f"  Stale WIP: ${wip_report.get('stale_wip_value', 0):,.2f}")
        report.append(f"  WIP Status: {wip_report.get('health_status', 'N/A')}")
        
        # Risk Section
        report.append("\n⚠️ CLIENT RISK")
        report.append(f"  Clients Graded: {risk_report.get('total_clients_graded', 0)}")
        report.append(f"  High-Risk Clients: {risk_report.get('high_risk_client_count', 0)}")
        report.append(f"  High-Risk Exposure: ${risk_report.get('high_risk_value', 0):,.2f}")
        report.append(f"  Portfolio Grade: {risk_report.get('portfolio_grade', 'N/A')}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def export_ar_snapshot(self, df: pd.DataFrame, prefix: str = None) -> str:
        """Export AR snapshot to CSV with timestamp."""
        prefix = prefix or config.AR_SNAPSHOT_PREFIX
        filename = f"{prefix}_{self._get_timestamp()}.csv"
        filepath = os.path.join(self.output_dir, filename)
        df.to_csv(filepath, index=False)
        return filepath
    
    def export_risk_report(self, graded_clients: pd.DataFrame, 
                           distribution: pd.DataFrame,
                           top_risk: pd.DataFrame) -> str:
        """Export risk report to Excel with multiple sheets."""
        filename = f"{config.RISK_REPORT_PREFIX}_{self._get_timestamp()}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            graded_clients.to_excel(writer, sheet_name='Client Grades', index=False)
            distribution.to_excel(writer, sheet_name='Grade Distribution', index=False)
            top_risk.to_excel(writer, sheet_name='Top Risk Projects', index=False)
        
        return filepath
    
    def export_wip_report(self, wip_summary: pd.DataFrame,
                          stale_wip: pd.DataFrame) -> str:
        """Export WIP report to Excel."""
        filename = f"{config.WIP_REPORT_PREFIX}_{self._get_timestamp()}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            wip_summary.to_excel(writer, sheet_name='WIP Summary', index=False)
            stale_wip.to_excel(writer, sheet_name='Stale WIP', index=False)
        
        return filepath
    
    def export_executive_summary(self, dso_report: Dict, wip_report: Dict,
                                  risk_report: Dict) -> str:
        """Export executive summary to text file."""
        filename = f"{config.EXECUTIVE_SUMMARY_PREFIX}_{self._get_timestamp()}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        content = self.generate_health_report(dso_report, wip_report, risk_report)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath


if __name__ == "__main__":
    print("Report Generator Module - Ready")
    generator = ReportGenerator()
    print(f"Output directory: {os.path.abspath(generator.output_dir)}")
