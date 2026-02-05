"""
VeriRight Report Generators
Generates specific reports as per documentation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
from veriright_config import VeriRightConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SUDReportGenerator:
    """Star Union Dai-ichi Life Insurance MIS Report"""
    
    def __init__(self, data):
        self.data = data.copy() if data is not None else pd.DataFrame()
        self.config = VeriRightConfig()
    
    def generate(self):
        """Generate SUD pivot table report"""
        if self.data.empty:
            return pd.DataFrame()
        
        # Filter for SUD client
        sud_data = self.data[
            self.data['client_name'].str.contains('Star Union', case=False, na=False)
        ].copy()
        
        if sud_data.empty:
            logger.warning("No SUD data found")
            return pd.DataFrame()
        
        # Create a simple status count
        status_counts = sud_data['case_status'].value_counts().reset_index()
        status_counts.columns = ['Case Status', 'Count']
        
        # Add total row
        total_row = pd.DataFrame({
            'Case Status': ['Grand Total'],
            'Count': [status_counts['Count'].sum()]
        })
        pivot = pd.concat([status_counts, total_row], ignore_index=True)
        
        return pivot


class SBIReportGenerator:
    """SBI Life MIS Report"""
    
    def __init__(self, data):
        self.data = data.copy() if data is not None else pd.DataFrame()
        self.config = VeriRightConfig()
    
    def generate(self):
        """Generate SBI report with LOT and pivot tables"""
        if self.data.empty:
            return {}
        
        # Filter for SBI Life
        sbi_filter = self.data['client_name'].str.contains('SBI', case=False, na=False)
        
        # Add Video KYC filter if activity_type column exists
        if 'activity_type' in self.data.columns:
            activity_filter = self.data['activity_type'].str.contains('Video KYC|VKYC', case=False, na=False)
            sbi_data = self.data[sbi_filter & activity_filter].copy()
        else:
            # If no activity_type column, just filter by client name
            sbi_data = self.data[sbi_filter].copy()
        
        if sbi_data.empty:
            logger.warning("No SBI data found")
            return {}
        
        # Create a simple status count instead of pivot
        status_counts = sbi_data['case_status'].value_counts().reset_index()
        status_counts.columns = ['Case Status', 'Count']
        
        # Add total row
        total_row = pd.DataFrame({
            'Case Status': ['Total'],
            'Count': [status_counts['Count'].sum()]
        })
        pivot1 = pd.concat([status_counts, total_row], ignore_index=True)
        
        # Pivot 2: Would need Clear/Adverse/Not cooperating field
        # This requires external SBI Status file integration
        
        return {
            'status_pivot': pivot1,
            'note': 'LOT and Clear/Adverse fields require SBI Status file integration'
        }


class HDFCVcheckReportGenerator:
    """HDFC Life Vcheck MIS Report"""
    
    def __init__(self, data):
        self.data = data.copy() if data is not None else pd.DataFrame()
        self.config = VeriRightConfig()
    
    def generate(self):
        """Generate HDFC Vcheck pivot table"""
        if self.data.empty:
            return pd.DataFrame()
        
        # Filter for HDFC Life Vcheck (already classified in normalization)
        hdfc_data = self.data[
            self.data['client_name'].str.contains('HDFC Life Vcheck', case=False, na=False)
        ].copy()
        
        if hdfc_data.empty:
            logger.warning("No HDFC VKYC data found")
            return pd.DataFrame()
        
        # ENHANCED FIX: Use completion date as fallback for HDFC Vcheck rows with missing received dates
        initial_count = len(hdfc_data)
        
        # Count rows with missing received dates
        missing_received = hdfc_data['case_received_date'].isna().sum()
        
        # For rows with missing received date, try using completion date as fallback
        if 'case_completion_date' in hdfc_data.columns and missing_received > 0:
            fallback_mask = hdfc_data['case_received_date'].isna() & hdfc_data['case_completion_date'].notna()
            fallback_count = fallback_mask.sum()
            
            if fallback_count > 0:
                hdfc_data.loc[fallback_mask, 'case_received_date'] = hdfc_data.loc[fallback_mask, 'case_completion_date']
                logger.warning(f"Used completion date as fallback for {fallback_count} HDFC Vcheck rows with missing Case Received Date")
        
        # Now filter out rows that still don't have a date
        hdfc_data = hdfc_data[hdfc_data['case_received_date'].notna()].copy()
        excluded_count = initial_count - len(hdfc_data)
        
        if excluded_count > 0:
            logger.warning(f"Excluded {excluded_count} HDFC Vcheck rows with missing dates (both received and completion)")
        
        if hdfc_data.empty:
            logger.error("No HDFC Vcheck rows with valid dates found")
            return pd.DataFrame()
        
        # Extract month from case_received_date (valid dates only)
        hdfc_data['Month'] = hdfc_data['case_received_date'].dt.to_period('M').astype(str)
        
        # Create status counts by month using crosstab
        pivot = pd.crosstab(
            hdfc_data['case_status'],
            hdfc_data['Month'],
            margins=True,
            margins_name='Total'
        )
        pivot.index.name = 'Case Status'
        
        return pivot


class HDFCITRReportGenerator:
    """HDFC ITR Manual MIS Report"""
    
    def __init__(self, data):
        self.data = data.copy() if data is not None else pd.DataFrame()
        self.config = VeriRightConfig()
    
    def generate(self):
        """Generate HDFC ITR report - shows Manual (Assisted) and Non-Assisted (Auto) separately"""
        if self.data.empty:
            return {}
        
        # Filter for HDFC ITR manual (Branch=Manual)
        manual_data = self.data[
            self.data['client_name'].str.contains('HDFC ITR manual', case=False, na=False)
        ].copy()
        
        # Filter for HDFC Auto (Branch=Non Assisted)
        auto_data = self.data[
            self.data['client_name'].str.contains('HDFC Auto', case=False, na=False)
        ].copy()
        
        if manual_data.empty and auto_data.empty:
            logger.warning("No HDFC ITR or HDFC Auto data found")
            return {}
        
        # Remove duplicates by application number if present
        if 'application_number' in manual_data.columns:
            manual_data = manual_data.drop_duplicates(subset=['application_number'], keep='first')
        if 'application_number' in auto_data.columns:
            auto_data = auto_data.drop_duplicates(subset=['application_number'], keep='first')
        
        # Create status counts for Manual (Assisted)
        if not manual_data.empty:
            status_counts_manual = manual_data['case_status'].value_counts().reset_index()
            status_counts_manual.columns = ['Case Status', 'Count']
            total_manual = pd.DataFrame({
                'Case Status': ['Total'],
                'Count': [status_counts_manual['Count'].sum()]
            })
            pivot_manual = pd.concat([status_counts_manual, total_manual], ignore_index=True)
        else:
            pivot_manual = pd.DataFrame()
        
        # Create status counts for Auto (Non-Assisted)
        if not auto_data.empty:
            status_counts_auto = auto_data['case_status'].value_counts().reset_index()
            status_counts_auto.columns = ['Case Status', 'Count']
            total_auto = pd.DataFrame({
                'Case Status': ['Total'],
                'Count': [status_counts_auto['Count'].sum()]
            })
            pivot_auto = pd.concat([status_counts_auto, total_auto], ignore_index=True)
        else:
            pivot_auto = pd.DataFrame()
        
        # Combine all data
        all_data = pd.concat([manual_data, auto_data], ignore_index=True)
        
        return {
            'assisted': pivot_manual,
            'non_assisted': pivot_auto,
            'all_data': all_data
        }


class OverallMISReportGenerator:
    """Overall VeriRight MIS Report (EOD MON-FRI)"""
    
    def __init__(self, data):
        self.data = data.copy() if data is not None else pd.DataFrame()
        self.config = VeriRightConfig()
    
    def generate(self):
        """Generate overall MIS report with client-wise breakdown"""
        if self.data.empty:
            return {}
        
        # Use filtered data as-is (respects user's date filter selection)
        df = self.data.copy()
        
        if df.empty:
            return {}
        
        # FIX: Remove duplicate columns if present
        df = df.loc[:, ~df.columns.duplicated()]
        
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
            logger.warning(f"Excluded {excluded_count} rows with missing dates (both received and completion) from Overall MIS")
        
        if df.empty:
            logger.error("No rows with valid dates found - cannot generate Overall MIS")
            return {}
        
        # Extract month from valid dates only
        df['Month'] = df['case_received_date'].dt.strftime('%b')
        df['Month_Sort'] = df['case_received_date'].dt.month
        
        # Step 7: Client-wise Total Received and Closed breakdown
        client_reports = []
        
        for client in sorted(df['client_name'].dropna().unique()):
            client_data = df[df['client_name'] == client]
            
            # Get unique months
            months = client_data.groupby(['Month', 'Month_Sort']).size().reset_index()
            months = months.sort_values('Month_Sort')
            
            for _, month_row in months.iterrows():
                month_name = month_row['Month']
                month_data = client_data[client_data['Month'] == month_name]
                
                # Total received in this month
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
                        (client_data['case_completion_date'].dt.strftime('%b') == month_name) &
                        (client_data['case_completion_date'].notna())
                    ]
                    closure_date_cases = len(completion_month_data)
                
                # Calculate closure percentage
                closure_pct = (closed_count / total_received * 100) if total_received > 0 else 0
                
                # Get target
                target = self.config.get_client_target(client)
                
                client_reports.append({
                    'Client name': client,
                    'Month': month_name,
                    'Total case received': total_received,
                    'Closed case': closed_count,
                    '% As per Close': f"{int(round(closure_pct))}%",
                    'Closure Date case': closure_date_cases,
                    'Targets': target if target else ''
                })
        
        report_df = pd.DataFrame(client_reports)
        
        # Status distribution by month using crosstab
        pivot = pd.crosstab(
            df['case_status'],
            df['Month'],
            margins=True,
            margins_name='Grand Total'
        )
        pivot.index.name = 'Case Status'
        
        # Client-wise pivot (for step 6 - individual client tables)
        client_pivots = {}
        for client in sorted(df['client_name'].dropna().unique()):
            client_data = df[df['client_name'] == client]
            client_pivot = pd.crosstab(
                client_data['case_status'],
                client_data['Month'],
                margins=True,
                margins_name='Total'
            )
            client_pivot.index.name = 'Case Status'
            client_pivots[client] = client_pivot
        
        return {
            'client_summary': report_df,
            'status_pivot': pivot,
            'client_pivots': client_pivots,
            'raw_data': df
        }


class ClosedListReportGenerator:
    """Closed List Report from CRM"""
    
    def __init__(self, data):
        self.data = data.copy() if data is not None else pd.DataFrame()
        self.config = VeriRightConfig()
    
    def generate(self):
        """Generate closed list pivot report"""
        if self.data.empty:
            return pd.DataFrame()
        
        # Filter closed cases
        closed_data = self.data[
            self.data['case_status'].apply(lambda x: self.config.is_closed_status(x))
        ].copy()
        
        if closed_data.empty:
            return pd.DataFrame()
        
        # Check required columns
        required_cols = ['customer_profile', 'case_completion_date', 'mer_type', 'insurance_company']
        if not all(col in closed_data.columns for col in required_cols):
            logger.warning("Missing required columns for closed list report")
            return pd.DataFrame()
        
        # Extract month
        closed_data['Completion_Month'] = closed_data['case_completion_date'].dt.to_period('M').astype(str)
        
        # Pivot: Customer Profile (Values) x Completion Date (Rows) x MER Type & Insurance (Columns)
        pivot = pd.pivot_table(
            closed_data,
            values='customer_profile',
            index='Completion_Month',
            columns=['mer_type', 'insurance_company'],
            aggfunc='count',
            fill_value=0,
            margins=True,
            margins_name='Total'
        )
        
        return pivot
