
import sys
import os
import pandas as pd
import logging

# Add project root to path
sys.path.append(r'd:\Downloads\Welleazy MIS')

from welleazy_pipeline import WelleazyMISPipeline
from welleazy_config import MISConfig
from welleazy_daily_mis import DailyMISGenerator
from welleazy_normalization import DataNormalizer

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_logic():
    print("Starting Verification...")
    
    # 1. Load Data
    csv_path = r'd:\Downloads\Welleazy MIS\welleazy.csv'
    if not os.path.exists(csv_path):
        print(f"Error: File not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows.")

    # 2. Normalize Data (Test Service Logic)
    normalizer = DataNormalizer(df)
    df_clean = normalizer.normalize()
    
    # Check Service Categories
    drug_cases = df_clean[df_clean['service_category'] == 'Drug']
    non_drug = df_clean[df_clean['service_category'] == 'Non-Drug']
    
    print(f"Drug Cases: {len(drug_cases)}")
    print(f"Non-Drug Cases: {len(non_drug)}")
    
    # Sample check
    print("\nSample Drug Services:")
    print(drug_cases['service'].unique()[:5])
    print("\nSample Non-Drug Services:")
    print(non_drug['service'].unique()[:5])
    
    # 3. Test Daily MIS Logic
    print("\nGenerating Daily MIS Report...")
    daily_gen = DailyMISGenerator(df_clean)
    
    # Bifurcate
    # We need to manually call the internal method or simulate the pipeline flow
    # The pipeline calls generate_daily_mis -> which calls _bifurcate_drug_non_drug
    
    # We'll test _generate_service_specific_report directly
    # Need to ensure 'service_type' column exists which is created in pipeline/normalization usually? 
    # Wait, normalization creates 'service_category'. 
    # welleazy_daily_mis.py line 348 in valid code uses df['service_type'] == service_name?
    # Let's check my edit. My edit removed _bifurcate in favor of _generate? No, I edited _generate.
    # _bifurcate calls _generate.
    
    # We need to simulate the dataframe state passed to _generate_service_specific_report
    # DailyMISGenerator.generate_report usually does date filtering first.
    
    # Let's just run the full pipeline for simplicity on this file
    # pipeline = WelleazyMISPipeline() # Removed to avoid init errors
    try:
        # Load and process
        # pipeline.df = df_clean # Already normalized
        
        # We need to inject the dataframe into the generator
        # DailyMISGenerator usually takes the full df in generate_report(df, date_from, date_to)
        
        # Test 1: Drug Report
        drug_df = df_clean[df_clean['service_category'] == 'Drug'].copy()
        drug_report = daily_gen._generate_service_specific_report(drug_df, 'Drug')
        
        print("\nDrug Report Columns:")
        print(drug_report.columns.tolist())
        print("\nDrug Report Head:")
        print(drug_report.head().to_string())
        
        # Test 2: Non-Drug Report
        non_drug_df = df_clean[df_clean['service_category'] == 'Non-Drug'].copy()
        nd_report = daily_gen._generate_service_specific_report(non_drug_df, 'Non-Drug')
        
        print("\nNon-Drug Report Head:")
        print(nd_report.head().to_string())
        
    except Exception as e:
        print(f"Error running logic: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_logic()
