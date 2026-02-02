
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from veriright_daily_mis import VeriRightDailyMISGenerator

def test_veriright_pivots():
    print("Testing VeriRight Pivot Generation...")
    
    # Create sample data
    data = {
        'case_id': range(1, 11),
        'client_name': [
            'HDFC Life', 'SBI Life', 'HDFC Life', 'HDFC Life', 'Canara HSBC',
            'HDFC Life', 'SBI Life', 'HDFC Life', 'HDFC Life', 'Star Union'
        ],
        'case_status': [
            'Closed', 'Pending', 'Closed', 'Closed', 'Closed',
            'Pending', 'Closed', 'Closed', 'Pending', 'Closed'
        ],
        'case_received_date': [datetime.now() - timedelta(days=x) for x in range(10)],
        'case_completion_date': [datetime.now()] * 10,
        'case_received_mode': ['Assisted', 'Non-Assisted'] * 5,
        'customer_profile': ['Salaried', 'Self-Employed'] * 5,
        'mer_type': ['Digital', 'Physical'] * 5,
        'insurance_company': ['HDFC', 'SBI'] * 5
    }
    
    df = pd.DataFrame(data)
    
    # Initialize generator
    gen = VeriRightDailyMISGenerator(df)
    reports = gen.generate()
    
    # Verify Closed List Pivot
    if 'closed_list_pivot' in reports:
        pivot = reports['closed_list_pivot']
        print(f"✅ Closed List Pivot Generated. Shape: {pivot.shape}")
        if not pivot.empty:
            print("   Closed List Pivot is not empty as expected.")
        else:
            print("   ❌ Closed List Pivot is empty!")
    else:
        print("❌ 'closed_list_pivot' key missing in reports")

    # Verify HDFC ITR Pivot
    if 'hdfc_itr_pivot' in reports:
        pivot = reports['hdfc_itr_pivot']
        print(f"✅ HDFC ITR Pivot Generated. Shape: {pivot.shape}")
        if not pivot.empty:
            print("   HDFC ITR Pivot is not empty as expected.")
        else:
             print("   ❌ HDFC ITR Pivot is empty!")
    else:
        print("❌ 'hdfc_itr_pivot' key missing in reports")

if __name__ == "__main__":
    test_veriright_pivots()
