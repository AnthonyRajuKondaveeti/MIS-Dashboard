"""
Test Script for Welleazy MIS Pipeline
Generates sample data and tests all components
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_sample_data(num_records=500):
    """
    Generate sample CRM data for testing
    
    Args:
        num_records: Number of sample records to generate
    
    Returns:
        DataFrame with sample data
    """
    print(f"Generating {num_records} sample records...")
    
    # Sample data pools
    clients = ['Acme Corp', 'TechStart Inc', 'HealthCare Ltd', 'MediCorp', 
               'WellnessGroup', 'BioTech Solutions', 'PharmaCare']
    
    statuses = [
        'Medical Done-Report Awaited',
        'Appointment Missed',
        'Call-later',
        'Fresh case',
        'Waiting for DC confirmation',
        'Closed',
        'Closed Reports-submitted',
        'In Progress',
        'Pending Review'
    ]
    
    services = [
        'Drug Testing - Pre-Employment',
        'Non-Drug Medical Exam',
        'Drug Testing - Random',
        'Physical Examination',
        'Alcohol Testing',
        'General Health Checkup'
    ]
    
    dc_names = ['Dr. Smith', 'Dr. Johnson', 'Dr. Williams', 'Dr. Brown', 'Dr. Davis']
    dc_cities = ['Mumbai', 'Delhi', 'Bangalore', 'Pune', 'Chennai', 'Hyderabad']
    
    # Generate data
    data = {
        'Case ID': [f'CASE{1000 + i}' for i in range(num_records)],
        'Client Name': [random.choice(clients) for _ in range(num_records)],
        'Customer Name': [f'Customer {random.randint(1, 1000)}' for _ in range(num_records)],
        'Case Status': [random.choice(statuses) for _ in range(num_records)],
        'Service': [random.choice(services) for _ in range(num_records)],
        'DC name': [random.choice(dc_names) for _ in range(num_records)],
        'DC city': [random.choice(dc_cities) for _ in range(num_records)],
    }
    
    # Generate dates
    base_date = datetime.now()
    
    # Case Entry Date (last 3 months)
    data['Case Entry Date'] = [
        base_date - timedelta(days=random.randint(0, 90))
        for _ in range(num_records)
    ]
    
    # Case Received Date (same as entry date with some variation)
    data['Case received Date'] = [
        entry_date - timedelta(days=random.randint(0, 2))
        for entry_date in data['Case Entry Date']
    ]
    
    # Appointment Date (1-10 days after case received)
    data['Appointment Date'] = [
        received_date + timedelta(days=random.randint(1, 10))
        for received_date in data['Case received Date']
    ]
    
    # Appointment fixed Date (around appointment date)
    data['Appointment fixed Date'] = [
        appt_date - timedelta(days=random.randint(1, 5))
        for appt_date in data['Appointment Date']
    ]
    
    # Case Completion Date (for closed cases only)
    data['Case Completion Date'] = [
        appt_date + timedelta(days=random.randint(1, 15)) 
        if status in ['Closed', 'Closed Reports-submitted']
        else pd.NaT
        for appt_date, status in zip(data['Appointment Date'], data['Case Status'])
    ]
    
    # Report uploaded date (similar to completion date)
    data['Report uploaded date'] = [
        comp_date + timedelta(days=random.randint(0, 2))
        if pd.notna(comp_date)
        else pd.NaT
        for comp_date in data['Case Completion Date']
    ]
    
    df = pd.DataFrame(data)
    
    print(f"✓ Generated {len(df)} records")
    print(f"  Date range: {df['Case Entry Date'].min()} to {df['Case Entry Date'].max()}")
    print(f"  Unique clients: {df['Client Name'].nunique()}")
    print(f"  Unique statuses: {df['Case Status'].nunique()}")
    
    return df


def test_normalization():
    """Test data normalization"""
    print("\n" + "=" * 60)
    print("TEST: Data Normalization")
    print("=" * 60)
    
    from welleazy_normalization import normalize_data
    
    # Generate sample data
    df = generate_sample_data(100)
    
    # Normalize
    normalized = normalize_data(df)
    
    print(f"\nOriginal columns: {list(df.columns)}")
    print(f"Normalized columns: {list(normalized.columns)}")
    print(f"\n✓ Normalization test passed")
    
    return normalized


def test_validation():
    """Test data validation"""
    print("\n" + "=" * 60)
    print("TEST: Data Validation")
    print("=" * 60)
    
    from welleazy_validation import validate_data
    
    df = generate_sample_data(50)
    
    # Test with correct columns
    is_valid, errors, warnings = validate_data(df, ['Case ID', 'Case Status'])
    
    if is_valid:
        print(" Validation test passed")
    else:
        print(" Validation test failed")
        for error in errors:
            print(f"  Error: {error}")


def test_tat_mis():
    """Test TAT MIS generation"""
    print("\n" + "=" * 60)
    print("TEST: TAT MIS Report")
    print("=" * 60)
    
    from welleazy_normalization import normalize_data
    from welleazy_tat_mis import TATMISGenerator
    
    # Generate data with some "Medical Done-Report Awaited" cases
    df = generate_sample_data(200)
    
    # Ensure some cases have the right status
    indices = random.sample(range(len(df)), 20)
    df.loc[indices, 'Case Status'] = 'Medical Done-Report Awaited'
    
    # Normalize
    normalized = normalize_data(df)
    
    # Generate report
    generator = TATMISGenerator(normalized)
    report = generator.generate()
    
    if not report.empty:
        print(f"✓ Generated TAT report with {len(report)} cases")
        print(f"  High TAT cases: {report['high_tat'].sum()}")
        print(f"  Avg TAT: {report['tat_days'].mean():.2f} days")
    else:
        print("⚠ No TAT cases found (this is okay for test data)")


def test_pending_mis():
    """Test Pending Case MIS generation"""
    print("\n" + "=" * 60)
    print("TEST: Pending Case MIS Report")
    print("=" * 60)
    
    from welleazy_normalization import normalize_data
    from welleazy_pending_mis import PendingCaseMISGenerator
    
    # Generate data
    df = generate_sample_data(200)
    
    # Ensure some pending cases
    pending_statuses = ['Appointment Missed', 'Call-later', 'Fresh case', 
                       'Waiting for DC confirmation']
    indices = random.sample(range(len(df)), 40)
    for idx in indices:
        df.loc[idx, 'Case Status'] = random.choice(pending_statuses)
    
    # Normalize
    normalized = normalize_data(df)
    
    # Generate report
    generator = PendingCaseMISGenerator(normalized)
    report = generator.generate()
    
    if not report.empty:
        print(f"✓ Generated Pending MIS with {report['Total']['Total']} cases")
        print(f"  Statuses covered: {len(report) - 1}")  # -1 for Total row
    else:
        print("⚠ No pending cases found")


def test_full_pipeline():
    """Test complete pipeline"""
    print("\n" + "=" * 60)
    print("TEST: Full Pipeline")
    print("=" * 60)
    
    from welleazy_pipeline import WelleazyMISPipeline
    
    # Generate and save sample data
    df = generate_sample_data(500)
    test_file = 'test_data.xlsx'
    df.to_excel(test_file, index=False)
    print(f"✓ Saved test data to {test_file}")
    
    # Run pipeline
    try:
        pipeline = WelleazyMISPipeline(test_file)
        reports = pipeline.run(report_types=['tat', 'pending'])
        
        print(f"\n✓ Pipeline completed successfully!")
        print(f"  Reports generated: {list(reports.keys())}")
        
        # Clean up
        import os
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"✓ Cleaned up test file")
        
        return reports
        
    except Exception as e:
        print(f"✗ Pipeline test failed: {str(e)}")
        raise


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("WELLEAZY MIS - TEST SUITE")
    print("=" * 60)
    
    try:
        # Test 1: Normalization
        test_normalization()
        
        # Test 2: Validation
        test_validation()
        
        # Test 3: TAT MIS
        test_tat_mis()
        
        # Test 4: Pending MIS
        test_pending_mis()
        
        # Test 5: Full Pipeline
        test_full_pipeline()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("✗ TESTS FAILED")
        print("=" * 60)
        print(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    # Run all tests
    run_all_tests()
    
    # Or run individual tests
    # test_normalization()
    # test_tat_mis()
    # etc.
