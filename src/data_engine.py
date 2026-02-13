"""
Data Engine Module
==================
SQL Server data extraction for the Parsons Finance Simulation database.
Provides high-performance ETL from SQL to pandas DataFrames.
"""

import pyodbc
import pandas as pd
from datetime import datetime
from typing import Optional, Dict
import sys
import os

# Add parent directory for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class ParsonsDataEngine:
    """
    Data extraction engine for ParsonsFinanceSim database.
    
    Provides methods to extract data from:
    - Invoices (core fact table)
    - Clients (dimension table)
    - Projects (dimension table)
    - UnbilledWork (WIP tracking)
    """
    
    def __init__(self, server: str = None, database: str = None):
        """
        Initialize the data engine with connection parameters.
        
        Args:
            server: SQL Server instance name (defaults to config.SERVER)
            database: Database name (defaults to config.DATABASE)
        """
        self.server = server or config.SERVER
        self.database = database or config.DATABASE
        self.conn_str = config.get_connection_string()
        self._connection = None
        
    def get_connection(self) -> pyodbc.Connection:
        """
        Establishes and returns a SQL Server connection.
        
        Returns:
            pyodbc.Connection: Active database connection
        """
        return pyodbc.connect(self.conn_str)
    
    def test_connection(self) -> bool:
        """
        Test if the database connection can be established.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def extract_invoices(self) -> pd.DataFrame:
        """
        Extracts full invoices data with client and project joins.
        
        Returns:
            DataFrame with columns:
            - InvoiceID, ClientID, ClientName, ProjectID, ProjectName
            - InvoiceAmount, InvoiceDate, DueDate, PaidDate, Status
            - DaysOverdue (calculated)
        """
        query = """
        SELECT 
            i.InvoiceID,
            i.ClientID,
            c.ClientName,
            c.PaymentTerms,
            c.CreditLimit,
            i.ProjectID,
            p.ProjectName,
            p.Sector,
            p.Region,
            i.InvoiceAmount,
            i.InvoiceDate,
            i.DueDate,
            i.PaidDate,
            i.Status,
            DATEDIFF(day, i.DueDate, GETDATE()) as DaysOverdue,
            CASE 
                WHEN i.PaidDate IS NOT NULL 
                THEN DATEDIFF(day, i.InvoiceDate, i.PaidDate)
                ELSE NULL 
            END as DaysToCollect
        FROM Invoices i
        JOIN Clients c ON i.ClientID = c.ClientID
        JOIN Projects p ON i.ProjectID = p.ProjectID
        ORDER BY i.InvoiceDate DESC
        """
        with self.get_connection() as conn:
            return pd.read_sql(query, conn)
    
    def extract_clients(self) -> pd.DataFrame:
        """
        Extracts client master data with credit terms and limits.
        
        Returns:
            DataFrame with ClientID, ClientName, PaymentTerms, CreditLimit
        """
        query = """
        SELECT 
            ClientID,
            ClientName,
            PaymentTerms,
            CreditLimit,
            Industry,
            ContactEmail
        FROM Clients
        ORDER BY ClientName
        """
        with self.get_connection() as conn:
            return pd.read_sql(query, conn)
    
    def extract_projects(self) -> pd.DataFrame:
        """
        Extracts project details with sector and region breakdown.
        
        Returns:
            DataFrame with ProjectID, ProjectName, Sector, Region, StartDate, Budget
        """
        query = """
        SELECT 
            ProjectID,
            ProjectName,
            Sector,
            Region,
            ClientID,
            StartDate,
            EndDate,
            Budget,
            Status as ProjectStatus
        FROM Projects
        ORDER BY ProjectName
        """
        with self.get_connection() as conn:
            return pd.read_sql(query, conn)
    
    def extract_unbilled_work(self) -> pd.DataFrame:
        """
        Extracts work-in-progress data for WIP leakage analysis.
        
        Returns:
            DataFrame with WorkID, ProjectID, ProjectName, EstimatedValue, LogDate
        """
        query = """
        SELECT 
            u.WorkID,
            u.ProjectID,
            p.ProjectName,
            p.Sector,
            p.Region,
            u.EstimatedValue,
            u.LogDate,
            u.Description,
            DATEDIFF(day, u.LogDate, GETDATE()) as DaysSinceLogged
        FROM UnbilledWork u
        JOIN Projects p ON u.ProjectID = p.ProjectID
        ORDER BY u.LogDate DESC
        """
        with self.get_connection() as conn:
            return pd.read_sql(query, conn)
    
    def extract_ar_report(self) -> pd.DataFrame:
        """
        Extracts the full Accounts Receivable and Aging status.
        Legacy method for backwards compatibility.
        
        Returns:
            DataFrame with AR data including DaysOverdue
        """
        return self.extract_invoices()
    
    def extract_wip_leakage(self) -> pd.DataFrame:
        """
        Extracts aggregated WIP by project for leakage analysis.
        Legacy method for backwards compatibility.
        
        Returns:
            DataFrame with ProjectName and UnbilledValue
        """
        query = """
        SELECT 
            p.ProjectID,
            p.ProjectName, 
            p.Sector,
            SUM(u.EstimatedValue) as UnbilledValue,
            COUNT(u.WorkID) as UnbilledItems,
            MIN(u.LogDate) as OldestEntry,
            MAX(u.LogDate) as NewestEntry
        FROM UnbilledWork u
        JOIN Projects p ON u.ProjectID = p.ProjectID
        GROUP BY p.ProjectID, p.ProjectName, p.Sector
        HAVING SUM(u.EstimatedValue) > 0
        ORDER BY UnbilledValue DESC
        """
        with self.get_connection() as conn:
            return pd.read_sql(query, conn)
    
    def extract_all(self) -> Dict[str, pd.DataFrame]:
        """
        One-call extraction of all data from the database.
        
        Returns:
            Dictionary with keys: 'invoices', 'clients', 'projects', 'unbilled_work', 'wip_summary'
        """
        print(f"[{datetime.now()}] Starting live extraction from {self.database}...")
        
        data = {
            'invoices': self.extract_invoices(),
            'clients': self.extract_clients(),
            'projects': self.extract_projects(),
            'unbilled_work': self.extract_unbilled_work(),
            'wip_summary': self.extract_wip_leakage()
        }
        
        total_records = sum(len(df) for df in data.values())
        print(f"[{datetime.now()}] Extraction complete. Total records: {total_records:,}")
        
        return data
    
    def get_summary_stats(self) -> Dict:
        """
        Get quick summary statistics from the database.
        
        Returns:
            Dictionary with table counts and key metrics
        """
        queries = {
            'total_invoices': "SELECT COUNT(*) FROM Invoices",
            'total_clients': "SELECT COUNT(*) FROM Clients",
            'total_projects': "SELECT COUNT(*) FROM Projects",
            'total_unbilled': "SELECT COUNT(*) FROM UnbilledWork",
            'total_ar_value': "SELECT SUM(InvoiceAmount) FROM Invoices WHERE Status != 'Paid'",
            'total_overdue': "SELECT SUM(InvoiceAmount) FROM Invoices WHERE Status = 'Overdue'"
        }
        
        stats = {}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for key, query in queries.items():
                cursor.execute(query)
                result = cursor.fetchone()[0]
                stats[key] = result if result else 0
                
        return stats


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================
if __name__ == "__main__":
    engine = ParsonsDataEngine()
    
    print("=" * 60)
    print("PARSONS DATA ENGINE - CONNECTION TEST")
    print("=" * 60)
    
    if engine.test_connection():
        print("✓ Connection successful!")
        
        # Get summary stats
        stats = engine.get_summary_stats()
        print(f"\nDatabase Summary:")
        print(f"  - Invoices: {stats['total_invoices']:,}")
        print(f"  - Clients: {stats['total_clients']:,}")
        print(f"  - Projects: {stats['total_projects']:,}")
        print(f"  - Unbilled Work Entries: {stats['total_unbilled']:,}")
        print(f"  - Total AR Value: ${stats['total_ar_value']:,.2f}")
        print(f"  - Total Overdue: ${stats['total_overdue']:,.2f}")
    else:
        print("✗ Connection failed. Check server and database settings.")
