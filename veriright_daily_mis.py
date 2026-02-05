"""
Veriright Daily MIS Generator
Creates client-wise MIS reports similar to the provided format
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
from veriright_config import VeriRightConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VeriRightDailyMISGenerator:
    """Generate Daily MIS reports for Veriright"""
    
    def __init__(self, normalized_data):
        """
        Initialize generator
        
        Args:
            normalized_data: Normalized pandas DataFrame
        """
        self.data = normalized_data.copy() if normalized_data is not None else pd.DataFrame()
        self.config = VeriRightConfig()
        self.reports = {}
    
    def generate(self):
        """
        Generate all MIS reports
        
        Returns:
            Dictionary containing different report DataFrames
        """
        if self.data.empty:
            logger.warning("No data available for MIS generation")
            return {}
        
        try:
            # Generate client-wise monthly report (main report)
            self.reports['client_monthly'] = self._generate_client_monthly_report()
            
            # Generate summary statistics
            self.reports['summary'] = self._generate_summary()
            
            # Generate case status breakdown
            self.reports['status_breakdown'] = self._generate_status_breakdown()
            
            logger.info("Successfully generated all VeriRight MIS reports")
            return self.reports
            
        except Exception as e:
            logger.error(f"Error generating VeriRight MIS: {e}", exc_info=True)
            return {'error': str(e)}
    
    def _generate_client_monthly_report(self):
        """
        Generate client-wise monthly report matching the image format
        
        Format:
        Client name | Month | Total case received | closed case | % As per Close | 
        Closure Date case | Targets-December
        """
        # Use all available data (no date filtering - user filters applied upstream)
        df = self.data.copy()
        
        if df.empty:
            logger.warning("No data available")
            return pd.DataFrame()
        
        # ENHANCED FIX: Use completion date as fallback when received date is missing
        # This is critical for HDFC ITR/Auto data where ~60% of rows have blank received dates
        initial_count = len(df)
        
        # Count rows with missing received dates
        missing_received = df['case_received_date'].isna().sum()
        
        # For rows with missing received date, try using completion date as fallback
        if 'case_completion_date' in df.columns and missing_received > 0:
            fallback_mask = df['case_received_date'].isna() & df['case_completion_date'].notna()
            fallback_count = fallback_mask.sum()
            
            if fallback_count > 0:
                df.loc[fallback_mask, 'case_received_date'] = df.loc[fallback_mask, 'case_completion_date']
                logger.warning(f"Used completion date as fallback for {fallback_count} rows with missing Case Received Date")
        
        # Now filter out rows that still don't have a date
        df = df[df['case_received_date'].notna()].copy()
        excluded_count = initial_count - len(df)
        
        if excluded_count > 0:
            logger.warning(f"Excluded {excluded_count} rows with missing dates (both received and completion) from Daily MIS")
        
        if df.empty:
            logger.error("No rows with valid dates found - cannot generate Daily MIS")
            return pd.DataFrame()
        
        # Extract month from valid dates only
        df['month'] = df['case_received_date'].dt.strftime('%B')
        df['month_num'] = df['case_received_date'].dt.month
        
        # Group by client and month
        results = []
        
        # Get unique clients
        clients = df['client_name'].dropna().unique()
        
        for client in sorted(clients):
            client_data = df[df['client_name'] == client]
            
            # Get unique months for this client
            months = client_data.groupby(['month', 'month_num']).size().reset_index()
            months = months.sort_values('month_num')
            
            for _, month_row in months.iterrows():
                month_name = month_row['month']
                month_data = client_data[client_data['month'] == month_name]
                
                # Total cases received
                total_received = len(month_data)
                
                # Closed cases: Consider closed if EITHER status is closed OR completion date exists
                def is_case_closed(row):
                    # Check if status indicates closed
                    status_closed = self.config.is_closed_status(row['case_status'])
                    
                    # Check if completion date is filled (case actually completed)
                    completion_date_exists = False
                    if 'case_completion_date' in row.index:
                        completion_date_exists = pd.notna(row['case_completion_date'])
                    
                    # A case is closed if either condition is true
                    return status_closed or completion_date_exists
                
                closed_count = sum(month_data.apply(is_case_closed, axis=1))
                
                # Closure Date case: Cases closed in this month by completion date
                closure_date_cases = 0
                if 'case_completion_date' in client_data.columns:
                    # Filter cases where completion date falls in this month
                    completion_month_data = client_data[
                        (client_data['case_completion_date'].dt.strftime('%B') == month_name) &
                        (client_data['case_completion_date'].notna())
                    ]
                    closure_date_cases = len(completion_month_data)
                
                # Closure percentage
                closure_pct = (closed_count / total_received * 100) if total_received > 0 else 0
                
                # Get target
                target = self.config.get_client_target(client)
                
                results.append({
                    'Client name': client,
                    'Month': month_name,
                    'Total case received': total_received,
                    'closed case': closed_count,
                    '% As per Close': f"{closure_pct:.1f}%",
                    'Closure Date case': closure_date_cases,
                    'Targets': target if target else ''
                })
        
        report_df = pd.DataFrame(results)
        
        # Sort by client name and month
        month_order = ['August', 'September', 'October', 'November', 'December', 
                      'January', 'February', 'March', 'April', 'May', 'June', 'July']
        report_df['month_sort'] = report_df['Month'].map(
            {month: i for i, month in enumerate(month_order)}
        )
        report_df = report_df.sort_values(['Client name', 'month_sort'])
        report_df = report_df.drop(columns=['month_sort'])
        
        logger.info(f"Generated client monthly report: {len(report_df)} rows")
        return report_df
    
    def _generate_summary(self):
        """Generate summary statistics"""
        df = self.data
        
        total_cases = len(df)
        
        # Count closed cases: Consider closed if EITHER status is closed OR completion date exists
        def is_case_closed(row):
            # Check if status indicates closed
            status_closed = self.config.is_closed_status(row['case_status'])
            
            # Check if completion date is filled (case actually completed)
            completion_date_exists = False
            if 'case_completion_date' in row.index:
                completion_date_exists = pd.notna(row['case_completion_date'])
            
            # A case is closed if either condition is true
            return status_closed or completion_date_exists
        
        closed_cases = sum(df.apply(is_case_closed, axis=1))
        pending_cases = total_cases - closed_cases
        closure_rate = (closed_cases / total_cases * 100) if total_cases > 0 else 0
        
        summary = {
            'Total Cases': total_cases,
            'Closed Cases': closed_cases,
            'Pending Cases': pending_cases,
            'Closure Rate': f"{closure_rate:.1f}%"
        }
        
        return pd.DataFrame([summary])
    
    def _generate_status_breakdown(self):
        """Generate case status breakdown"""
        if 'case_status' not in self.data.columns:
            return pd.DataFrame()
        
        status_counts = self.data['case_status'].value_counts().reset_index()
        status_counts.columns = ['Case Status', 'Count']
        
        # Add percentage
        total = status_counts['Count'].sum()
        status_counts['Percentage'] = (status_counts['Count'] / total * 100).round(1)
        status_counts['Percentage'] = status_counts['Percentage'].astype(str) + '%'
        
        return status_counts
    
    def export_to_excel(self, output_path):
        """Export all reports to Excel file"""
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                if 'client_monthly' in self.reports and not self.reports['client_monthly'].empty:
                    self.reports['client_monthly'].to_excel(
                        writer, sheet_name='Client Monthly Report', index=False
                    )
                
                if 'summary' in self.reports and not self.reports['summary'].empty:
                    self.reports['summary'].to_excel(
                        writer, sheet_name='Summary', index=False
                    )
                
                if 'status_breakdown' in self.reports and not self.reports['status_breakdown'].empty:
                    self.reports['status_breakdown'].to_excel(
                        writer, sheet_name='Status Breakdown', index=False
                    )
            
            logger.info(f"Exported VeriRight MIS to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export to Excel: {e}")
            return False
