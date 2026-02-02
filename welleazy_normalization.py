"""
Data Normalization Layer
Cleans and standardizes raw CRM data
"""

import pandas as pd
from datetime import datetime
from typing import Optional
import logging
from welleazy_config import MISConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataNormalizer:
    """Normalizes raw CRM data into standardized format"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.original_shape = df.shape
    
    def normalize(self) -> pd.DataFrame:
        """
        Run all normalization steps
        Returns: Normalized DataFrame
        """
        logger.info(f"Starting normalization. Original shape: {self.original_shape}")
        
        self._standardize_column_names()
        self._clean_whitespace()
        self._parse_dates()
        self._handle_null_values()
        self._standardize_case_status()
        self._categorize_services()
        
        logger.info(f"Normalization complete. Final shape: {self.df.shape}")
        return self.df
    
    def _standardize_column_names(self):
        """Rename columns to standardized names"""
        rename_map = {}
        for col in self.df.columns:
            normalized = MISConfig.normalize_column_name(col)
            if normalized != col:
                rename_map[col] = normalized
        
        if rename_map:
            self.df.rename(columns=rename_map, inplace=True)
            logger.info(f"Renamed {len(rename_map)} columns")
    
    def _clean_whitespace(self):
        """Remove leading/trailing whitespace from string columns"""
        # Get string columns safely
        try:
            string_cols = self.df.select_dtypes(include=['object']).columns
        except Exception as e:
            logger.warning(f"Could not select object columns: {e}")
            string_cols = []
        
        for col in string_cols:
            try:
                # Verify column exists and contains string data
                if col in self.df.columns:
                    # Only apply string operations if the column actually has string methods
                    sample = self.df[col].iloc[0] if len(self.df) > 0 else None
                    if isinstance(sample, str) or pd.isna(sample):
                        self.df[col] = self.df[col].astype(str).str.strip()
                        # Replace 'nan' string back to NaN
                        self.df[col] = self.df[col].replace('nan', pd.NA)
            except Exception as e:
                logger.warning(f"Could not clean column '{col}': {e}")
                pass
        
        # Extra cleaning for case_status - normalize spacing and characters
        if 'case_status' in self.df.columns:
            try:
                self.df['case_status'] = self.df['case_status'].astype(str).str.replace(r'\s+', ' ', regex=True)
                self.df['case_status'] = self.df['case_status'].str.strip()
                self.df['case_status'] = self.df['case_status'].replace('nan', pd.NA)
            except Exception as e:
                logger.warning(f"Could not clean case_status: {e}")
        
        logger.info(f"Cleaned whitespace from {len(string_cols)} columns")
    
    def _parse_dates(self):
        """Parse date columns into datetime format"""
        date_cols = [col for col in self.df.columns if 'date' in col.lower()]
        
        for col in date_cols:
            if col in self.df.columns:
                self.df[col] = self._parse_date_column(self.df[col])
                logger.info(f"Parsed dates for column: {col}")
    
    def _parse_date_column(self, series: pd.Series) -> pd.Series:
        """Parse a single date column trying multiple formats"""
        # First try pandas auto-detection
        parsed = pd.to_datetime(series, errors='coerce')
        
        # If too many failed, try specific formats
        if parsed.isna().sum() > len(series) * 0.1:  # More than 10% failed
            for date_format in MISConfig.DATE_FORMATS:
                try:
                    temp = pd.to_datetime(series, format=date_format, errors='coerce')
                    if temp.isna().sum() < parsed.isna().sum():
                        parsed = temp
                except:
                    continue
        
        return parsed
    
    def _handle_null_values(self):
        """Handle null values appropriately"""
        # For string columns, replace NaN with empty string or 'Unknown'
        string_cols = self.df.select_dtypes(include=['object']).columns
        for col in string_cols:
            if col in ['client_name', 'dc_name', 'dc_city']:
                self.df[col].fillna('Unknown', inplace=True)
            else:
                self.df[col].fillna('', inplace=True)
        
        # For date columns, keep NaN as is (will be handled in MIS logic)
        # For numeric columns, keep NaN as is
    
    def _standardize_case_status(self):
        """Standardize case status values"""
        if 'case_status' in self.df.columns:
            # Remove extra whitespace and standardize casing
            self.df['case_status'] = (
                self.df['case_status']
                .str.strip()
                .str.title()  # Capitalize first letter of each word
            )
            
            # Log unique statuses - OPTIMIZED using value_counts()
            status_counts = self.df['case_status'].value_counts(dropna=True)
            logger.info(f"Found {len(status_counts)} unique case statuses")
            logger.info("=" * 60)
            logger.info("DEBUG: TOP 10 CASE STATUS VALUES IN YOUR DATA:")
            for status, count in status_counts.head(10).items():
                logger.info(f"  '{status}' ({count} records)")
            logger.info("=" * 60)
    
    def _categorize_services(self):
        """Categorize services into Drug/Non-Drug"""
        if 'service' in self.df.columns:
            # Create standardized service category
            self.df['service_category'] = self.df['service'].apply(
                self._categorize_service
            )
            logger.info("Categorized services into Drug/Non-Drug")
    
    def _categorize_service(self, service: str) -> str:
        """Categorize a single service into Drug or Non-Drug"""
        if pd.isna(service) or service == '':
            return 'Unknown'
        
        service_lower = str(service).lower().strip()
        
        # Strict User Requirement: Only "urine" in service name is Drug
        if 'urine' in service_lower:
            return MISConfig.SERVICE_CATEGORIES['drug']
        else:
            return MISConfig.SERVICE_CATEGORIES['non_drug']


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience function to normalize data
    
    Args:
        df: Raw DataFrame from CRM
    
    Returns:
        Normalized DataFrame
    """
    normalizer = DataNormalizer(df)
    return normalizer.normalize()
