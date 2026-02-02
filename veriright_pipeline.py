"""
Veriright Data Pipeline
Orchestrates data loading, normalization, and processing
"""

import pandas as pd
import logging
from pathlib import Path
from veriright_normalization import VeriRightNormalizer
from veriright_config import VeriRightConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VeriRightPipeline:
    """Main pipeline for processing Veriright data"""
    
    def __init__(self):
        self.normalizer = VeriRightNormalizer()
        self.config = VeriRightConfig()
        self.normalized_data = None
    
    def load_from_files(self, file_paths):
        """
        Load data from Excel files
        
        Args:
            file_paths: Dictionary with {name: path} or list of paths
            
        Returns:
            Normalized DataFrame
        """
        if not file_paths:
            logger.error("No file paths provided")
            return None
        
        # Convert list to dict if needed
        if isinstance(file_paths, list):
            file_paths = {f"Source_{i+1}": path for i, path in enumerate(file_paths)}
        
        dataframes = {}
        
        for name, path in file_paths.items():
            try:
                if not Path(path).exists():
                    logger.error(f"File not found: {path}")
                    continue
                
                # Read file based on extension
                if path.lower().endswith('.csv'):
                    df = pd.read_csv(path)
                else:
                    df = pd.read_excel(path)
                dataframes[name] = df
                logger.info(f"Loaded {name}: {len(df)} rows, {len(df.columns)} columns")
                
            except Exception as e:
                logger.error(f"Failed to load {name} from {path}: {e}")
        
        if not dataframes:
            logger.error("No data loaded from files")
            return None
        
        # Normalize and merge
        self.normalized_data = self.normalizer.merge_multiple_sources(dataframes)
        
        if self.normalized_data is not None and not self.normalized_data.empty:
            logger.info(f"Pipeline complete: {len(self.normalized_data)} total rows")
            self._log_data_summary()
        
        return self.normalized_data
    
    def load_from_dataframes(self, dataframes_dict):
        """
        Load data from pre-loaded DataFrames
        
        Args:
            dataframes_dict: Dictionary with {name: dataframe}
            
        Returns:
            Normalized DataFrame
        """
        self.normalized_data = self.normalizer.merge_multiple_sources(dataframes_dict)
        
        if self.normalized_data is not None and not self.normalized_data.empty:
            logger.info(f"Pipeline complete: {len(self.normalized_data)} total rows")
            self._log_data_summary()
        
        return self.normalized_data
    
    def get_normalized_data(self):
        """Get the normalized data"""
        return self.normalized_data
    
    def _log_data_summary(self):
        """Log summary of processed data"""
        if self.normalized_data is None or self.normalized_data.empty:
            return
        
        df = self.normalized_data
        
        logger.info("=== Data Summary ===")
        logger.info(f"Total rows: {len(df)}")
        logger.info(f"Columns: {', '.join(df.columns)}")
        
        if 'client_name' in df.columns:
            logger.info(f"Unique clients: {df['client_name'].nunique()}")
        
        if 'case_status' in df.columns:
            logger.info(f"Unique statuses: {df['case_status'].nunique()}")
        
        if 'case_received_date' in df.columns:
            date_range = f"{df['case_received_date'].min()} to {df['case_received_date'].max()}"
            logger.info(f"Date range: {date_range}")
        
        logger.info("===================")


def run_veriright_pipeline(file_paths):
    """
    Convenience function to run the complete pipeline
    
    Args:
        file_paths: Dictionary or list of file paths
        
    Returns:
        Normalized DataFrame
    """
    pipeline = VeriRightPipeline()
    return pipeline.load_from_files(file_paths)
