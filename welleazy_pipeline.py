"""
Main MIS Pipeline Orchestrator
Coordinates the entire data processing flow
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import requests
import json

# Import all modules
from welleazy_config import MISConfig
from welleazy_validation import validate_data
from welleazy_normalization import normalize_data
from welleazy_tat_mis import generate_tat_mis, TATMISGenerator
from welleazy_pending_mis import generate_pending_mis, PendingCaseMISGenerator
from welleazy_closure_tat_mis import generate_closure_tat_mis, ClosureTATMISGenerator
from welleazy_daily_mis import generate_daily_mis, DailyMISGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WelleazyMISPipeline:
    """Main pipeline to process all MIS reports"""
    
    def __init__(self, data_path: str = None, api_endpoint: str = None):
        """
        Initialize pipeline
        
        Args:
            data_path: Path to raw CRM data (Excel file) - optional if api_endpoint is provided
            api_endpoint: API endpoint URL to fetch data from - optional if data_path is provided
        """
        if data_path is None and api_endpoint is None:
            raise ValueError("Either data_path or api_endpoint must be provided")
        
        self.data_path = data_path
        self.api_endpoint = api_endpoint
        self.raw_data = None
        self.normalized_data = None
        self.reports = {}
        
        # Create output directory
        Path(MISConfig.OUTPUT_DIR).mkdir(exist_ok=True)
    
    def run(self, report_types: list = None):
        """
        Run the complete MIS pipeline
        
        Args:
            report_types: List of report types to generate
                         Options: ['tat', 'pending', 'closure', 'daily']
                         If None, generates all reports
        """
        if report_types is None:
            report_types = ['tat', 'pending', 'closure', 'daily']
        
        logger.info("=" * 60)
        logger.info("Starting Welleazy MIS Pipeline")
        logger.info("=" * 60)
        
        try:
            # Step 1: Ingest Data
            self._ingest_data()
            
            # Step 2: Normalize Data
            self._normalize_data()
            
            # Step 3: Generate Reports
            if 'tat' in report_types:
                self._generate_tat_report()
            
            if 'pending' in report_types:
                self._generate_pending_report()
            
            if 'closure' in report_types:
                self._generate_closure_report()
            
            if 'daily' in report_types:
                self._generate_daily_report()
            
            # Step 4: Summary
            self._print_summary()
            
            logger.info("=" * 60)
            logger.info("Pipeline completed successfully!")
            logger.info("=" * 60)
            
            return self.reports
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            raise
    
    def _ingest_data(self):
        """Step 1: Ingest raw data from Excel, CSV, or API"""
        logger.info("\n[STEP 1] Ingesting data...")
        
        try:
            # Check if loading from API
            if self.api_endpoint:
                logger.info(f"Fetching data from API: {self.api_endpoint}")
                
                try:
                    response = requests.get(self.api_endpoint, timeout=30)
                    
                    # Log response details for debugging
                    logger.info(f"API Response Status: {response.status_code}")
                    
                    # Check for successful response
                    if response.status_code != 200:
                        error_msg = f"API returned status code {response.status_code}"
                        try:
                            error_detail = response.json()
                            error_msg += f". Details: {error_detail}"
                        except:
                            error_msg += f". Response: {response.text[:200]}"
                        
                        logger.error(error_msg)
                        raise requests.exceptions.HTTPError(error_msg)
                    
                    # Try to parse as JSON first
                    try:
                        data = response.json()
                        logger.info(f"API returned JSON data. Type: {type(data)}")
                        
                        # Convert JSON to DataFrame
                        if isinstance(data, list):
                            if len(data) == 0:
                                raise ValueError("API returned empty list")
                            self.raw_data = pd.DataFrame(data)
                        elif isinstance(data, dict):
                            # Check if data is nested in a key
                            if 'data' in data:
                                self.raw_data = pd.DataFrame(data['data'])
                            elif 'records' in data:
                                self.raw_data = pd.DataFrame(data['records'])
                            elif 'results' in data:
                                self.raw_data = pd.DataFrame(data['results'])
                            else:
                                # Try to convert the dict directly
                                self.raw_data = pd.DataFrame([data])
                        else:
                            raise ValueError(f"Unexpected JSON structure from API: {type(data)}")
                        
                        # Verify we got a DataFrame with proper structure
                        if not isinstance(self.raw_data, pd.DataFrame):
                            raise ValueError(f"Failed to create DataFrame. Got type: {type(self.raw_data)}")
                        
                        if len(self.raw_data) == 0:
                            raise ValueError("API returned data but DataFrame is empty")
                        
                        # Flatten any nested columns
                        for col in self.raw_data.columns:
                            # Check if column contains nested structures
                            if self.raw_data[col].dtype == 'object':
                                first_val = self.raw_data[col].iloc[0] if len(self.raw_data) > 0 else None
                                if isinstance(first_val, (dict, list)):
                                    logger.warning(f"Column '{col}' contains nested data, converting to string")
                                    self.raw_data[col] = self.raw_data[col].astype(str)
                        
                        logger.info(f"✓ Loaded {len(self.raw_data)} records from API: {self.api_endpoint}")
                        logger.info(f"  DataFrame shape: {self.raw_data.shape}")
                        logger.info(f"  Columns: {list(self.raw_data.columns[:10])}..." if len(self.raw_data.columns) > 10 else f"  Columns: {list(self.raw_data.columns)}")
                    except json.JSONDecodeError:
                        # If not JSON, try parsing as CSV
                        from io import StringIO
                        self.raw_data = pd.read_csv(StringIO(response.text), low_memory=False)
                        logger.info(f"✓ Loaded {len(self.raw_data)} records from API (CSV format): {self.api_endpoint}")
                
                except requests.exceptions.Timeout:
                    error_msg = "API request timed out after 30 seconds. The server may be slow or unavailable."
                    logger.error(error_msg)
                    raise requests.exceptions.RequestException(error_msg)
                    
                except requests.exceptions.ConnectionError:
                    error_msg = "Failed to connect to the API. Please check your internet connection and verify the API URL is correct."
                    logger.error(error_msg)
                    raise requests.exceptions.RequestException(error_msg)
            
            # Otherwise load from file
            elif self.data_path:
                # Check file extension to determine how to read it
                file_ext = Path(self.data_path).suffix.lower()
                
                if file_ext == '.csv':
                    # For large CSV files, use low_memory=False and optimize dtypes
                    logger.info("Reading CSV file (this may take a moment for large files)...")
                    self.raw_data = pd.read_csv(self.data_path, low_memory=False)
                    logger.info(f"✓ Loaded {len(self.raw_data)} records from CSV: {self.data_path}")
                elif file_ext in ['.xlsx', '.xls']:
                    self.raw_data = pd.read_excel(self.data_path)
                    logger.info(f"✓ Loaded {len(self.raw_data)} records from Excel: {self.data_path}")
                else:
                    raise ValueError(f"Unsupported file format: {file_ext}. Please use .csv, .xlsx, or .xls")
            
            logger.info(f"  Columns: {list(self.raw_data.columns)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data from API: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to load data: {str(e)}")
            raise
    
    def _normalize_data(self):
        """Step 2: Normalize and validate data"""
        logger.info("\n[STEP 2] Normalizing data...")
        
        # Normalize
        self.normalized_data = normalize_data(self.raw_data)
        
        logger.info(f"  Normalized columns: {list(self.normalized_data.columns)}")
        
        # Validate (basic check - specific validations happen in each report)
        # Only require case_status as it's needed for all reports
        is_valid, errors, warnings = validate_data(
            self.normalized_data,
            required_columns=['case_status']
        )
        
        if not is_valid:
            logger.error("Data validation failed. See errors above.")
            logger.error("Please ensure your data has at least a 'Case Status' column.")
            raise ValueError("Data validation failed")
        
        logger.info(f"✓ Normalized data ready: {len(self.normalized_data)} records")
    
    def _generate_tat_report(self):
        """Generate TAT MIS Report"""
        logger.info("\n[REPORT] Generating TAT MIS...")
        
        try:
            generator = TATMISGenerator(self.normalized_data)
            report = generator.generate()
            
            if not report.empty:
                # Export to Excel
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"{MISConfig.OUTPUT_DIR}/TAT_MIS_{timestamp}.xlsx"
                generator.export_to_excel(output_path)
                
                # Store report
                self.reports['tat'] = {
                    'data': report,
                    'summary': generator.get_summary(),
                    'file': output_path
                }
                
                logger.info(f"✓ TAT MIS exported to {output_path}")
            else:
                logger.warning("No TAT data to report (no cases with 'Medical Done-Report Awaited' status)")
                # Store empty report so UI knows it was generated
                self.reports['tat'] = {
                    'data': pd.DataFrame(),
                    'summary': {},
                    'file': None
                }
                
        except Exception as e:
            logger.error(f"Failed to generate TAT report: {str(e)}")
            raise
    
    def _generate_pending_report(self):
        """Generate Pending Case MIS Report"""
        logger.info("\n[REPORT] Generating Pending Case MIS...")
        
        try:
            generator = PendingCaseMISGenerator(self.normalized_data)
            report = generator.generate()
            
            if not report.empty:
                # Export to Excel
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"{MISConfig.OUTPUT_DIR}/Pending_MIS_{timestamp}.xlsx"
                generator.export_to_excel(output_path)
                
                # Store report
                self.reports['pending'] = {
                    'data': report,
                    'summary': generator.get_summary(),
                    'file': output_path
                }
                
                logger.info(f"✓ Pending MIS exported to {output_path}")
            else:
                logger.warning("No pending cases to report")
                # Store empty report so UI knows it was generated
                self.reports['pending'] = {
                    'data': pd.DataFrame(),
                    'summary': {},
                    'file': None
                }
                
        except Exception as e:
            logger.error(f"Failed to generate Pending report: {str(e)}")
            raise
    
    def _generate_closure_report(self):
        """Generate Closure TAT MIS Report"""
        logger.info("\n[REPORT] Generating Closure TAT MIS...")
        
        try:
            generator = ClosureTATMISGenerator(self.normalized_data)
            closure_report, scheduled_report = generator.generate()
            
            if not closure_report.empty:
                # Export to Excel
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"{MISConfig.OUTPUT_DIR}/Closure_TAT_MIS_{timestamp}.xlsx"
                generator.export_to_excel(output_path)
                
                # Store report
                self.reports['closure'] = {
                    'closure_data': closure_report,
                    'scheduled_data': scheduled_report,
                    'summary': generator.get_summary(),
                    'file': output_path
                }
                
                logger.info(f"✓ Closure TAT MIS exported to {output_path}")
            else:
                logger.warning("No closure data to report (no closed cases in last 2 months)")
                # Store empty report so UI knows it was generated
                self.reports['closure'] = {
                    'closure_data': pd.DataFrame(),
                    'scheduled_data': pd.DataFrame(),
                    'summary': {},
                    'file': None
                }
                
        except Exception as e:
            logger.error(f"Failed to generate Closure report: {str(e)}")
            raise
    
    def _generate_daily_report(self):
        """Generate Daily MIS Report"""
        logger.info("\n[REPORT] Generating Daily MIS...")
        
        try:
            generator = DailyMISGenerator(self.normalized_data)
            reports_dict = generator.generate()
            
            if reports_dict:
                # Export to Excel
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"{MISConfig.OUTPUT_DIR}/Daily_MIS_{timestamp}.xlsx"
                generator.export_to_excel(output_path)
                
                # Store report
                self.reports['daily'] = {
                    'data': reports_dict,
                    'file': output_path
                }
                
                logger.info(f"✓ Daily MIS exported to {output_path}")
            else:
                logger.warning("No daily data to report")
                
        except Exception as e:
            logger.error(f"Failed to generate Daily report: {str(e)}")
            raise
    
    def _print_summary(self):
        """Print pipeline execution summary"""
        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"Total records processed: {len(self.normalized_data)}")
        logger.info(f"Reports generated: {len(self.reports)}")
        
        for report_type, report_data in self.reports.items():
            logger.info(f"\n{report_type.upper()} Report:")
            logger.info(f"  Output: {report_data['file']}")
            
            if 'summary' in report_data:
                for key, value in report_data['summary'].items():
                    logger.info(f"  {key}: {value}")


def run_pipeline(data_path: str, report_types: list = None):
    """
    Convenience function to run the MIS pipeline
    
    Args:
        data_path: Path to raw CRM Excel file
        report_types: List of report types to generate (None = all)
    
    Returns:
        Dictionary of generated reports
    """
    pipeline = WelleazyMISPipeline(data_path)
    return pipeline.run(report_types)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <path_to_crm_data.xlsx>")
        sys.exit(1)
    
    data_file = sys.argv[1]
    run_pipeline(data_file)
