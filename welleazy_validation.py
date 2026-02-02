"""
Data Validation Layer
Ensures data quality before processing
"""

import pandas as pd
from typing import List, Dict, Tuple
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataValidator:
    """Validates data quality and completeness"""
    
    def __init__(self, df: pd.DataFrame, required_columns: List[str]):
        self.df = df
        self.required_columns = required_columns
        self.errors = []
        self.warnings = []
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validation checks
        Returns: (is_valid, errors, warnings)
        """
        self._check_required_columns()
        self._check_empty_dataframe()
        self._check_duplicates()
        self._check_null_values()
        self._check_date_validity()
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _check_required_columns(self):
        """Check if all required columns are present"""
        missing = set(self.required_columns) - set(self.df.columns)
        if missing:
            self.errors.append(f"Missing required columns: {missing}")
    
    def _check_empty_dataframe(self):
        """Check if dataframe is empty"""
        if self.df.empty:
            self.errors.append("DataFrame is empty")
    
    def _check_duplicates(self):
        """Check for duplicate case IDs"""
        if 'case_id' in self.df.columns:
            dupes = self.df[self.df.duplicated(subset=['case_id'], keep=False)]
            if not dupes.empty:
                self.warnings.append(
                    f"Found {len(dupes)} duplicate case IDs"
                )
    
    def _check_null_values(self):
        """Check for null values in critical columns"""
        critical_cols = [col for col in self.required_columns 
                        if col in self.df.columns]
        
        for col in critical_cols:
            null_count = self.df[col].isna().sum()
            if null_count > 0:
                null_pct = (null_count / len(self.df)) * 100
                if null_pct > 50:
                    self.errors.append(
                        f"Column '{col}' has {null_pct:.1f}% null values"
                    )
                else:
                    self.warnings.append(
                        f"Column '{col}' has {null_count} null values"
                    )
    
    def _check_date_validity(self):
        """Check if date columns have valid dates"""
        date_cols = [col for col in self.df.columns 
                    if 'date' in col.lower()]
        
        for col in date_cols:
            if col in self.df.columns:
                try:
                    # Check if dates are in reasonable range
                    valid_dates = pd.to_datetime(self.df[col], errors='coerce')
                    
                    # Check for future dates
                    future_dates = valid_dates > pd.Timestamp.now()
                    if future_dates.any():
                        self.warnings.append(
                            f"Column '{col}' has {future_dates.sum()} future dates"
                        )
                    
                    # Check for very old dates (before 2000)
                    old_dates = valid_dates < pd.Timestamp('2000-01-01')
                    if old_dates.any():
                        self.warnings.append(
                            f"Column '{col}' has {old_dates.sum()} dates before 2000"
                        )
                except Exception as e:
                    self.warnings.append(
                        f"Could not validate dates in column '{col}': {str(e)}"
                    )
    
    def log_results(self):
        """Log validation results"""
        if self.errors:
            logger.error(f"Validation failed with {len(self.errors)} errors:")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        if self.warnings:
            logger.warning(f"Validation completed with {len(self.warnings)} warnings:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            logger.info("✓ Validation passed with no issues")


def validate_data(df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function to validate dataframe
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
    
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = DataValidator(df, required_columns)
    is_valid, errors, warnings = validator.validate()
    validator.log_results()
    return is_valid, errors, warnings
