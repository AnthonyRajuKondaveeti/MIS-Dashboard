"""
Veriright Data Normalization Module
Handles data cleaning, column standardization, and format normalization
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from veriright_config import VeriRightConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VeriRightNormalizer:
    """Normalizes Veriright data from various sources"""
    
    def __init__(self):
        self.config = VeriRightConfig()
    
    def normalize_dataframe(self, df, source_name="Unknown"):
        """
        Normalize a dataframe from any source
        
        Args:
            df: pandas DataFrame
            source_name: name of the source file for logging
            
        Returns:
            Normalized DataFrame
        """
        if df is None or df.empty:
            logger.warning(f"Empty dataframe received from {source_name}")
            return pd.DataFrame()
        
        logger.info(f"Normalizing data from {source_name}: {len(df)} rows, {len(df.columns)} columns")
        
        # Make a copy
        df = df.copy()
        
        # Step 1: Standardize column names
        df = self._standardize_columns(df)
        
        # Step 2: Parse and standardize dates
        df = self._standardize_dates(df)
        
        # Step 3: Clean string columns
        df = self._clean_string_columns(df)
        
        # Step 4: Filter out cancelled cases
        df = self._filter_cancelled_cases(df)
        
        logger.info(f"Normalization complete: {len(df)} rows after filtering")
        
        return df
    
    def _standardize_columns(self, df):
        """Standardize column names using config mappings"""
        # Create reverse mapping
        rename_map = {}
        
        for col in df.columns:
            if col in self.config.COLUMN_MAPPINGS:
                rename_map[col] = self.config.COLUMN_MAPPINGS[col]
        
        df = df.rename(columns=rename_map)
        
        # Handle duplicate columns by keeping first occurrence and coalescing values
        if df.columns.duplicated().any():
            # Get list of duplicate column names
            duplicate_cols = df.columns[df.columns.duplicated()].unique()
            
            for dup_col in duplicate_cols:
                # Get all columns with this name
                dup_mask = df.columns == dup_col
                dup_data = df.loc[:, dup_mask]
                
                # Coalesce: use first non-null value across duplicate columns
                df[dup_col] = dup_data.bfill(axis=1).iloc[:, 0]
                
                # Drop duplicate columns (keep first)
                df = df.loc[:, ~df.columns.duplicated(keep='first')]
        
        logger.info(f"Standardized {len(rename_map)} columns")
        return df
    
    def _standardize_dates(self, df):
        """Parse and standardize date columns"""
        for date_col in self.config.DATE_COLUMNS:
            if date_col in df.columns:
                # Use dayfirst=True to parse DD/MM/YYYY format correctly
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
                logger.info(f"Parsed {date_col}: {df[date_col].notna().sum()} valid dates")
        
        return df
    
    def _clean_string_columns(self, df):
        """Clean string columns (trim whitespace, handle nulls)"""
        string_columns = ['client_name', 'case_status', 'activity_type', 
                         'case_received_mode', 'customer_profile', 'mer_type']
        
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(['nan', 'None', ''], np.nan)
        
        # Normalize and clean case status values
        if 'case_status' in df.columns:
            df['case_status'] = df['case_status'].apply(self._normalize_status)
        
        # Normalize client names to handle spelling variations
        if 'client_name' in df.columns:
            df['client_name'] = df['client_name'].apply(
                lambda x: self.config.normalize_client_name(x) if pd.notna(x) else x
            )
        
        # Derive client names for HDFC Life based on Branch and Case Type
        df = self._derive_hdfc_client_names(df)
        
        return df
    
    def _normalize_status(self, status):
        """
        Normalize and clean case status values
        Maps error messages and variations to standard status categories
        """
        if pd.isna(status) or status == 'nan':
            return 'Status Unknown'
        
        status_str = str(status).strip().lower()
        
        # Handle empty or null-like values
        if not status_str or status_str in ['', 'none', 'null', 'n/a']:
            return 'Status Unknown'
        
        # Map error messages to standard categories
        error_patterns = {
            'Technical Error - Data Issue': [
                'no data found', 'not data found', 'no data found showing',
                'data not found', 'no data available',
                'saral form not showing', 'form not showing',
                'doc not fetched properly', 'document not fetched',
                'pdf not opening', 'pdf not available',
                'doc not reflecting', 'document not reflecting',
                'error', 'errror', 'system error'
            ],
            'Pending - Customer Action Required': [
                'customer not responding', 'customer unavailable',
                'we can\'t close this case because customer nam',
                'customer name mismatch', 'customer details pending',
                'waiting for customer', 'customer follow-up required'
            ],
            'Pending - Document Issue': [
                'document not clear', 'doc not clear',
                'document quality issue', 'unclear document',
                'document mismatch', 'document not matching'
            ]
        }
        
        # Check against error patterns
        for standard_status, patterns in error_patterns.items():
            for pattern in patterns:
                if pattern in status_str:
                    return standard_status
        
        # Standardize common status values (proper case)
        status_standardization = {
            'closed': 'Closed',
            'completed': 'Completed',
            'in progress': 'In Progress',
            'pending': 'Pending',
            'assigned': 'Assigned',
            'scheduled': 'Scheduled',
            'cancelled': 'Cancelled',
            'on hold': 'On Hold',
            'verification completed': 'Verification Completed',
            'report submitted': 'Report Submitted',
            'medical done': 'Medical Done',
            'report awaited': 'Report Awaited',
            'medical done-report awaited': 'Medical Done - Report Awaited',
            'closed - submitted to insurance': 'Closed - Submitted to Insurance',
            'vcheck completed – qc pending': 'Vcheck Completed - QC Pending',
            'successfully completed': 'Successfully Completed'
        }
        
        # Check for exact match (case-insensitive)
        for key, standard_value in status_standardization.items():
            if status_str == key:
                return standard_value
        
        # Check for partial match (for cases like "case closed" -> "Closed")
        for key, standard_value in status_standardization.items():
            if key in status_str:
                return standard_value
        
        # If no match found, return title case version of original
        return status.strip().title()
    
    def _filter_cancelled_cases(self, df):
        """Remove cancelled cases from the dataset"""
        if 'case_status' not in df.columns:
            return df
        
        initial_count = len(df)
        
        # Normalize status and check if cancelled
        df['_is_cancelled'] = df['case_status'].apply(
            lambda x: self.config.is_cancelled_status(x)
        )
        
        df = df[~df['_is_cancelled']].copy()
        df = df.drop(columns=['_is_cancelled'])
        
        filtered_count = initial_count - len(df)
        if filtered_count > 0:
            logger.info(f"Filtered out {filtered_count} cancelled cases")
        
        return df
    
    def _derive_hdfc_client_names(self, df):
        """Derive specific client names for HDFC Life based on Branch and Case Type columns"""
        if 'client_name' not in df.columns:
            return df
        
        # Check if this is HDFC Life data
        hdfc_mask = df['client_name'].str.contains('HDFC Life', case=False, na=False)
        
        if not hdfc_mask.any():
            return df
        
        # Check for Branch column
        if 'Branch' in df.columns:
            # HDFC Life + Branch = "Manual" → HDFC ITR manual
            manual_mask = hdfc_mask & (df['Branch'].astype(str).str.strip().str.lower() == 'manual')
            df.loc[manual_mask, 'client_name'] = 'HDFC ITR manual'
            
            # HDFC Life + Branch = "Non Assisted" → HDFC Auto
            non_assisted_mask = hdfc_mask & (df['Branch'].astype(str).str.strip().str.lower().isin(['non assisted', 'non-assisted', 'nonassisted']))
            df.loc[non_assisted_mask, 'client_name'] = 'HDFC Auto'
            
            logger.info(f"Derived {manual_mask.sum()} HDFC ITR manual cases")
            logger.info(f"Derived {non_assisted_mask.sum()} HDFC Auto cases")
        
        # Check for Case Type or Class Type column
        case_type_col = None
        for col in df.columns:
            if col.lower() in ['case type', 'class type', 'casetype', 'classtype']:
                case_type_col = col
                break
        
        if case_type_col:
            # HDFC Life + Case Type = "Video check" → HDFC Life Vcheck
            vcheck_mask = hdfc_mask & (df[case_type_col].astype(str).str.strip().str.lower().str.contains('video check|video-check|videocheck', case=False, na=False))
            df.loc[vcheck_mask, 'client_name'] = 'HDFC Life Vcheck'
            
            logger.info(f"Derived {vcheck_mask.sum()} HDFC Life Vcheck cases")
        
        return df
    
    def merge_multiple_sources(self, dataframes_dict):
        """
        Merge data from multiple sources
        
        Args:
            dataframes_dict: Dictionary with source_name: dataframe pairs
            
        Returns:
            Merged and normalized DataFrame
        """
        normalized_dfs = []
        
        for source_name, df in dataframes_dict.items():
            normalized_df = self.normalize_dataframe(df, source_name)
            if not normalized_df.empty:
                normalized_df['data_source'] = source_name
                normalized_dfs.append(normalized_df)
        
        if not normalized_dfs:
            logger.warning("No data to merge")
            return pd.DataFrame()
        
        merged_df = pd.concat(normalized_dfs, ignore_index=True)
        
        # Remove duplicates if any
        initial_rows = len(merged_df)
        merged_df = merged_df.drop_duplicates()
        
        if initial_rows > len(merged_df):
            logger.info(f"Removed {initial_rows - len(merged_df)} duplicate rows")
        
        logger.info(f"Merged data: {len(merged_df)} total rows from {len(normalized_dfs)} sources")
        
        return merged_df


def load_and_normalize_veriright_data(file_paths):
    """
    Load and normalize Veriright data from multiple Excel files
    
    Args:
        file_paths: List of file paths or dict with name: path pairs
        
    Returns:
        Normalized DataFrame
    """
    normalizer = VeriRightNormalizer()
    
    # Convert list to dict if needed
    if isinstance(file_paths, list):
        file_paths = {f"File_{i+1}": path for i, path in enumerate(file_paths)}
    
    # Load all files
    dataframes = {}
    for name, path in file_paths.items():
        try:
            df = pd.read_excel(path)
            dataframes[name] = df
            logger.info(f"Loaded {name}: {len(df)} rows")
        except Exception as e:
            logger.error(f"Failed to load {name} from {path}: {e}")
    
    # Merge and normalize
    normalized_data = normalizer.merge_multiple_sources(dataframes)
    
    return normalized_data
