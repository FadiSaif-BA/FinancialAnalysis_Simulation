"""
Financial Data Automation & Predictive Analytics Suite
======================================================
Parsons Simulation: Optimizing the Cash Conversion Cycle

One-click execution script for automated financial analysis.
Connects to SQL Server, extracts data, runs analysis, and generates reports.
"""
from src.data_engine import ParsonsDataEngine
from src.data_cleaning import DataCleaner
from src.dso_analysis import DSOAnalyzer
from src.wip_analysis import WIPAnalyzer
from src.risk_scoring import RiskScorer
from src.predictive_analytics import PredictiveAnalyzer
from src.visualizations import FinancialVisualizer
from src.report_generator import ReportGenerator

import sys
import os
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

import config


def print_header():
    """Print application header."""
    print("\n" + "=" * 70)
    print("📊 FINANCIAL DATA AUTOMATION & PREDICTIVE ANALYTICS SUITE")
    print("   Parsons Simulation - Cash Conversion Cycle Optimization")
    print("=" * 70)
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Server: {config.SERVER}")
    print(f"   Database: {config.DATABASE}")
    print("=" * 70 + "\n")


def run_analysis():
    """Execute the complete financial analysis pipeline."""

    # Initialize components
    engine = ParsonsDataEngine()
    cleaner = DataCleaner()
    reporter = ReportGenerator()
    visualizer = FinancialVisualizer()
    
    # Step 1: Test connection
    print("[1/7] Testing database connection...")
    if not engine.test_connection():
        print("❌ Database connection failed!")
        print("   Please check server and database settings in config.py")
        return False
    print("✅ Connection successful!\n")
    
    # Step 2: Extract data
    print("[2/7] Extracting data from SQL Server...")
    try:
        raw_data = engine.extract_all()
        print(f"   Invoices: {len(raw_data['invoices']):,} records")
        print(f"   Clients: {len(raw_data['clients']):,} records")
        print(f"   Projects: {len(raw_data['projects']):,} records")
        print(f"   Unbilled Work: {len(raw_data['unbilled_work']):,} entries")
        print("✅ Extraction complete!\n")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False
    
    # Step 3: Clean data
    print("[3/7] Cleaning and transforming data...")
    cleaned_data = cleaner.clean_all(raw_data)
    print("✅ Data cleaning complete!\n")
    
    # Step 4: Run DSO Analysis
    print("[4/7] Running DSO and Aging Analysis...")
    dso_analyzer = DSOAnalyzer(cleaned_data['invoices'])
    dso_report = dso_analyzer.get_dso_health_report()
    aging_summary = dso_analyzer.get_aging_summary()
    dso_trend = dso_analyzer.calculate_dso_trend()
    print(f"   DSO: {dso_report['dso']} days")
    print(f"   Health Score: {dso_report['health_score']}")
    print("✅ DSO Analysis complete!\n")
    
    # Step 5: Run WIP Analysis
    print("[5/7] Running WIP Leakage Analysis...")
    wip_analyzer = WIPAnalyzer(cleaned_data['wip_summary'], cleaned_data['invoices'])
    wip_report = wip_analyzer.get_wip_health_report()
    wip_by_project = wip_analyzer.get_wip_by_project()
    stale_wip = wip_analyzer.identify_stale_wip()
    print(f"   Total WIP: ${wip_report['total_wip_value']:,.2f}")
    print(f"   Leakage Coefficient: {wip_report['leakage_percentage']:.1f}%")
    print("✅ WIP Analysis complete!\n")
    
    # Step 6: Run Risk Scoring
    print("[6/8] Running Client Risk Analysis...")
    risk_scorer = RiskScorer(cleaned_data['invoices'])
    risk_report = risk_scorer.get_risk_health_report()
    graded_clients = risk_scorer.grade_clients()
    grade_distribution = risk_scorer.get_risk_distribution()
    top_risk = risk_scorer.get_top_risk_projects()
    print(f"   Clients Graded: {risk_report['total_clients_graded']}")
    print(f"   Portfolio Grade: {risk_report['portfolio_grade']}")
    print("✅ Risk Analysis complete!\n")
    
    # Step 7: Run Predictive Analytics
    print("[7/8] Running Predictive Analytics...")
    predictor = PredictiveAnalyzer(cleaned_data['invoices'])
    trend_data = predictor.calculate_moving_average(period='ME')  # Monthly trend
    forecast_data = predictor.forecast_monthly_inflow(periods_ahead=6)  # Monthly forecast
    at_risk_clients = predictor.predict_at_risk_clients()
    trend_insights = predictor.get_trend_insights()
    print(f"   Trend Direction: {trend_insights.get('trend_direction', 'N/A')}")
    print(f"   At-Risk Clients: {trend_insights.get('at_risk_count', 0)}")
    print("✅ Predictive Analytics complete!\n")
    
    # Step 8: Generate Reports and Visualizations
    print("[8/8] Generating reports and visualizations...")
    
    # Console report
    health_report = reporter.generate_health_report(dso_report, wip_report, risk_report)
    print(health_report)
    
    # Export files
    ar_path = reporter.export_ar_snapshot(cleaned_data['invoices'])
    print(f"   📄 AR Snapshot: {ar_path}")
    
    risk_path = reporter.export_risk_report(graded_clients, grade_distribution, top_risk)
    print(f"   📄 Risk Report: {risk_path}")
    
    wip_path = reporter.export_wip_report(wip_by_project, stale_wip)
    print(f"   📄 WIP Report: {wip_path}")
    
    summary_path = reporter.export_executive_summary(dso_report, wip_report, risk_report)
    print(f"   📄 Executive Summary: {summary_path}")
    
    # Generate visualizations
    reports_dir = config.REPORTS_DIR
    timestamp = datetime.now().strftime(config.DATE_FORMAT)
    
    # Core visualizations
    visualizer.plot_aging_buckets(aging_summary, 
                                   save_path=os.path.join(reports_dir, f'aging_chart_{timestamp}.png'))
    visualizer.plot_dso_trend(dso_trend,
                               save_path=os.path.join(reports_dir, f'dso_trend_{timestamp}.png'))
    visualizer.plot_wip_leakage(wip_by_project,
                                 save_path=os.path.join(reports_dir, f'wip_leakage_{timestamp}.png'))
    visualizer.plot_client_grades(grade_distribution,
                                   save_path=os.path.join(reports_dir, f'risk_grades_{timestamp}.png'))
    
    # Predictive Analytics visualizations
    visualizer.plot_trend_with_bars(trend_data,
                                     save_path=os.path.join(reports_dir, f'trend_analysis_{timestamp}.png'))
    visualizer.plot_forecast_combined(forecast_data,
                                       save_path=os.path.join(reports_dir, f'forecast_bars_{timestamp}.png'))
    visualizer.plot_forecast_line(forecast_data,
                                   save_path=os.path.join(reports_dir, f'forecast_line_{timestamp}.png'))
    visualizer.plot_predictive_dashboard(trend_data, forecast_data, at_risk_clients,
                                          save_path=os.path.join(reports_dir, f'predictive_dashboard_{timestamp}.png'))
    
    print(f"   📊 Visualizations saved to {reports_dir}/")
    print(f"      - aging_chart_{timestamp}.png")
    print(f"      - dso_trend_{timestamp}.png")
    print(f"      - wip_leakage_{timestamp}.png")
    print(f"      - risk_grades_{timestamp}.png")
    print(f"      - trend_analysis_{timestamp}.png")
    print(f"      - forecast_bars_{timestamp}.png")
    print(f"      - forecast_line_{timestamp}.png")
    print(f"      - predictive_dashboard_{timestamp}.png")
    
    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 70 + "\n")
    
    return True


if __name__ == "__main__":
    print_header()
    
    success = run_analysis()
    
    if success:
        print("All reports generated successfully.")
    else:
        print("Analysis encountered errors. Check configuration and try again.")
        sys.exit(1)
