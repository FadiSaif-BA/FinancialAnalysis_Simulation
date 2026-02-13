"""
Data Cleaning Module
====================
Utilities for cleaning and transforming raw financial data.
Handles null values, type conversions, and calculated fields.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class DataCleaner:
    """
    Data cleaning and transformation utilities for financial data.
    """
    
    @staticmethod
    def clean_invoices(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare invoice data for analysis.
        
        Handles:
        - Date column parsing
        - Null value handling
        - Type conversions
        - Calculated field additions
        
        Args:
            df: Raw invoices DataFrame
            
        Returns:
            Cleaned DataFrame with proper types and calculated fields
        """
        df = df.copy()
        
        # Parse date columns
        date_columns = ['InvoiceDate', 'DueDate', 'PaidDate']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Ensure numeric columns
        numeric_columns = ['InvoiceAmount', 'DaysOverdue', 'DaysToCollect', 
                          'PaymentTerms', 'CreditLimit']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Fill missing DaysOverdue for non-overdue items
        if 'DaysOverdue' in df.columns:
            df['DaysOverdue'] = df['DaysOverdue'].fillna(0)
        
        # Standardize status values
        if 'Status' in df.columns:
            df['Status'] = df['Status'].str.strip().str.title()
        
        # Add calculated fields
        df = DataCleaner.add_calculated_fields(df)
        
        return df
    
    @staticmethod
    def clean_clients(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize client data.
        
        Args:
            df: Raw clients DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        
        # Standardize client names
        if 'ClientName' in df.columns:
            df['ClientName'] = df['ClientName'].str.strip().str.title()
        
        # Ensure numeric columns
        if 'CreditLimit' in df.columns:
            df['CreditLimit'] = pd.to_numeric(df['CreditLimit'], errors='coerce').fillna(0)
        
        if 'PaymentTerms' in df.columns:
            df['PaymentTerms'] = pd.to_numeric(df['PaymentTerms'], errors='coerce').fillna(30)
        
        return df
    
    @staticmethod
    def clean_projects(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize project data.
        
        Args:
            df: Raw projects DataFrame
            
        Returns:
            Cleaned DataFrame with standardized categories
        """
        df = df.copy()
        
        # Parse date columns
        date_columns = ['StartDate', 'EndDate']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Standardize categorical columns
        if 'Sector' in df.columns:
            df['Sector'] = df['Sector'].str.strip().str.title()
        
        if 'Region' in df.columns:
            df['Region'] = df['Region'].str.strip().str.upper()
        
        # Ensure budget is numeric
        if 'Budget' in df.columns:
            df['Budget'] = pd.to_numeric(df['Budget'], errors='coerce').fillna(0)
        
        return df
    
    @staticmethod
    def clean_unbilled_work(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean WIP/unbilled work data.
        
        Args:
            df: Raw unbilled work DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        
        # Parse date column
        if 'LogDate' in df.columns:
            df['LogDate'] = pd.to_datetime(df['LogDate'], errors='coerce')
        
        # Ensure numeric values
        if 'EstimatedValue' in df.columns:
            df['EstimatedValue'] = pd.to_numeric(df['EstimatedValue'], errors='coerce').fillna(0)
        
        if 'DaysSinceLogged' in df.columns:
            df['DaysSinceLogged'] = pd.to_numeric(df['DaysSinceLogged'], errors='coerce').fillna(0)
        
        return df
    
    @staticmethod
    def add_calculated_fields(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add calculated fields to invoice data.
        
        Adds:
        - AgingBucket: Category based on days overdue
        - IsOverdue: Boolean flag
        - MonthYear: Period for time-series analysis
        - Quarter: Fiscal quarter
        - PaymentVariance: Difference from terms
        
        Args:
            df: Invoice DataFrame
            
        Returns:
            DataFrame with additional calculated columns
        """
        df = df.copy()
        
        # Aging Bucket calculation
        if 'DaysOverdue' in df.columns:
            df['AgingBucket'] = pd.cut(
                df['DaysOverdue'],
                bins=config.AGING_BUCKETS,
                labels=config.BUCKET_LABELS,
                include_lowest=True,
                right=True
            )
            
            # Handle negative values (not yet due)
            mask_not_due = df['DaysOverdue'] <= 0
            df.loc[mask_not_due, 'AgingBucket'] = config.BUCKET_LABELS[0]
        
        # Overdue flag
        if 'Status' in df.columns:
            df['IsOverdue'] = df['Status'].str.lower() == 'overdue'
        elif 'DaysOverdue' in df.columns:
            df['IsOverdue'] = df['DaysOverdue'] > 0
        
        # Time period columns for analysis
        if 'InvoiceDate' in df.columns:
            df['MonthYear'] = df['InvoiceDate'].dt.to_period('M')
            df['Quarter'] = df['InvoiceDate'].dt.to_period('Q')
            df['Year'] = df['InvoiceDate'].dt.year
        
        # Payment variance (actual days vs terms)
        if 'DaysToCollect' in df.columns and 'PaymentTerms' in df.columns:
            df['PaymentVariance'] = df['DaysToCollect'] - df['PaymentTerms']
        
        return df
    
    @staticmethod
    def clean_all(data: dict) -> dict:
        """
        Clean all data in the extraction dictionary.
        
        Args:
            data: Dictionary from ParsonsDataEngine.extract_all()
            
        Returns:
            Dictionary with all DataFrames cleaned
        """
        cleaned = {}
        
        if 'invoices' in data:
            cleaned['invoices'] = DataCleaner.clean_invoices(data['invoices'])
        
        if 'clients' in data:
            cleaned['clients'] = DataCleaner.clean_clients(data['clients'])
        
        if 'projects' in data:
            cleaned['projects'] = DataCleaner.clean_projects(data['projects'])
        
        if 'unbilled_work' in data:
            cleaned['unbilled_work'] = DataCleaner.clean_unbilled_work(data['unbilled_work'])
        
        if 'wip_summary' in data:
            cleaned['wip_summary'] = DataCleaner.clean_unbilled_work(data['wip_summary'])
        
        return cleaned
    
    @staticmethod
    def validate_data_quality(df: pd.DataFrame, name: str = 'DataFrame') -> dict:
        """
        Perform data quality checks and return a report.
        
        Args:
            df: DataFrame to validate
            name: Name for reporting
            
        Returns:
            Dictionary with quality metrics
        """
        report = {
            'name': name,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'null_counts': df.isnull().sum().to_dict(),
            'null_percentage': (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
            'duplicate_rows': df.duplicated().sum(),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
        }
        
        return report


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("DATA CLEANING MODULE - DEMONSTRATION")
    print("=" * 60)
    
    # Create sample data for demonstration
    sample_invoices = pd.DataFrame({
        'InvoiceID': [1, 2, 3],
        'InvoiceAmount': ['1000.50', '2500.00', '750.25'],
        'InvoiceDate': ['2024-01-15', '2024-02-20', '2024-03-10'],
        'DueDate': ['2024-02-15', '2024-03-20', '2024-04-10'],
        'DaysOverdue': [45, -5, 10],
        'Status': ['overdue', 'pending', 'overdue'],
        'PaymentTerms': [30, 30, 30]
    })
    
    print("\nOriginal Data:")
    print(sample_invoices)
    print(f"\nData Types:\n{sample_invoices.dtypes}")
    
    cleaned = DataCleaner.clean_invoices(sample_invoices)
    
    print("\n" + "=" * 60)
    print("Cleaned Data:")
    print(cleaned)
    print(f"\nData Types:\n{cleaned.dtypes}")
    print(f"\nNew Columns Added: {set(cleaned.columns) - set(sample_invoices.columns)}")
