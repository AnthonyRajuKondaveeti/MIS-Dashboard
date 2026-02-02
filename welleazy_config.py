"""
Welleazy MIS Configuration - UPDATED FOR YOUR ACTUAL CSV COLUMNS
REPLACE welleazy_config.py with this updated version
"""

from datetime import datetime
from typing import Dict, List
import pandas as pd
import re

class MISConfig:
    """Central configuration for Welleazy MIS"""
    
    # TAT Thresholds
    TAT_THRESHOLD = 3  # Days
    TAT_MAX_CAP = 3    # Cap TAT at this value for reporting
    
    # Case Status Filters
    STATUS_FILTERS = {
        'tat_mis': [
            'Medical Done - Report Awaited',
            'Medical Done-Report Awaited',
            'Medicals Done - Report Awaited',
            'Medicals Done-Report Awaited'
        ],
        'pending_mis': [
            'Appointment Missed - Reschedule Appointment',
            'Call Later - Customer asked to call back',
            'Call Later - Customer Not Responding',
            'Call Later - Customer phone switched off',
            'Fresh Case',
            'Fresh case',
            'Waiting for DC confirmation',
            'Waiting for DC Confirmation',
            'Appointment Related - Partial Medicals pending'
        ],
        'closed_cases': [
            'Closed',
            'Closed - Reports Submitted',
            'Closed - Reports submitted',
            'Closed Reports Submitted',
            'Closed-Reports Submitted',
            'Closed Reports-Submitted'
        ]
    }
    
    # Highlight Status (for Pending MIS)
    HIGHLIGHT_STATUSES = [
        'Fresh case',
        'Fresh Case',
        'Waiting for DC confirmation',
        'Waiting for DC Confirmation',
        'Appointment Confirmed',
        'Escalated to Co - Customer Not Co-operating',
        'Escalated to Co - Customer Not Interested'
    ]
    
    # Column Name Mappings (YOUR ACTUAL CSV -> Standardized)
    COLUMN_MAPPINGS = {
        # Basic Info
        'Client Name': 'client_name',
        'Customer Name': 'customer_name',
        'Case ID/TA Code': 'case_id',
        
        # Dates - YOUR ACTUAL COLUMN NAMES FROM CSV
        'Appointment Date': 'appointment_date',
        'Case Entry Date': 'case_entry_date',
        'Case Completion Date': 'case_completion_date',
        'Appointment Fixed Date': 'appointment_fixed_date',
        'Case Received Date': 'case_received_date',
        'Report Upload Date': 'report_upload_date',
        'Case Follow Up Date': 'case_follow_up_date',
        'Last Action Date': 'last_action_date',
        'QC Report Date': 'qc_report_date',
        'Case Effective Date': 'case_effective_date',
        
        # Status
        'Case Status': 'case_status',
        
        # DC Info
        'DC Name': 'dc_name',
        'DC City': 'dc_city',
        'DC ID': 'dc_id',
        'DC Mobile No': 'dc_mobile',
        'DC EmailId': 'dc_email',
        'DC Address': 'dc_address',
        
        # Service
        'Service': 'service',
        'Package Name': 'package_name',
        'Package Code': 'package_code',
        
        # Customer Info
        'Customer Mobile No.': 'customer_mobile',
        'Customer Email Id': 'customer_email',
        'Customer Address': 'customer_address',
        'Customer PinCode': 'customer_pincode',
        
        # Location
        'City': 'city',
        'State': 'state',
        'Zone': 'zone',
        'Tier': 'tier',
        
        # TAT columns (already calculated in your CSV)
        'Appointment Scheduled TAT': 'appointment_scheduled_tat',
        'Appointment Closure TAT': 'appointment_closure_tat',
        'QC Closure TAT': 'qc_closure_tat',
        'Case Completion TAT': 'case_completion_tat',
        
        # Additional fields
        'Case Owner Name': 'case_owner',
        'Case Added By Name': 'case_added_by',
        'Assigned Agent Name': 'assigned_agent',
        'Gender': 'gender',
        'Application No./Proposal No.': 'application_no',
        'Branch Name': 'branch_name',
        'Company Name': 'company_name',
        'Client Code': 'client_code',
    }
    
    # Required Columns for Each MIS Type
    REQUIRED_COLUMNS = {
        'tat_mis': [
            'client_name', 'customer_name', 'case_id',
            'appointment_date', 'case_status', 'dc_name', 'dc_city'
        ],
        'pending_mis': [
            'case_status', 'case_received_date'
        ],
        'closure_tat_mis': [
            'client_name', 'appointment_date', 'case_completion_date',
            'appointment_fixed_date', 'case_received_date'
        ],
        'daily_mis': [
            'case_entry_date', 'case_status', 'client_name',
            'report_upload_date', 'service'
        ]
    }
    
    # Service Categories - ENHANCED BASED ON YOUR DATA
    SERVICE_CATEGORIES = {
        'drug': 'Drug',
        'non_drug': 'Non-Drug'
    }
    
    # Service Keywords for Classification
    # IMPORTANT: Update these based on actual service names in your CSV
    # Run the test script first to see what service names you have
    DRUG_SERVICE_KEYWORDS = [
        'urine',
        'drug',
        'drug test',
        'drug testing',
        'drug screen',
        'drug screening',
        'drug related',
        'substance',
        'substance test',
        'toxicology',
        'alcohol',
        'alcohol test',
        'cannabis',
        'narcotic',
        'opioid',
        'amphetamine',
        'cocaine',
        'marijuana',
        'benzodiazepine',
        'barbiturate',
        'methamphetamine',
        'thc',
        'urine drug screen',
        'uds',
        '5 panel',
        '10 panel',
        'panel drug',
    ]
    
    NON_DRUG_SERVICE_KEYWORDS = [
        'medical',
        'medical exam',
        'medical examination',
        'physical',
        'physical exam',
        'physical examination',
        'health',
        'health checkup',
        'health check',
        'checkup',
        'blood',
        'blood test',
        'x-ray',
        'xray',
        'ecg',
        'ekg',
        'echo',
        'ultrasound',
        'vaccination',
        'vaccine',
        'immunization',
        'fitness',
        'fitness test',
        'audiometry',
        'vision',
        'eye test',
        'chest x-ray',
        'cbc',
        'lipid',
        'thyroid',
        'glucose',
        'diabetes',
        'liver function',
        'kidney function',
        'non-drug',
    ]
    
    # Date Formats - Supporting multiple formats from your CSV
    DATE_FORMATS = [
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%d-%b-%Y',
        '%Y-%m-%d %H:%M:%S',
        '%d-%m-%Y %H:%M:%S',
        '%m/%d/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M:%S',
    ]
    
    # Lookback Periods
    LOOKBACK_MONTHS = {
        'closure_tat': 2,
        'daily_mis': 3
    }
    
    # Output Settings
    OUTPUT_DIR = 'output'
    DATA_DIR = 'data'
    
    @classmethod
    def get_status_filter(cls, mis_type: str) -> List[str]:
        """Get status filter for specific MIS type"""
        return cls.STATUS_FILTERS.get(mis_type, [])
    
    @classmethod
    def get_required_columns(cls, mis_type: str) -> List[str]:
        """Get required columns for specific MIS type"""
        return cls.REQUIRED_COLUMNS.get(mis_type, [])
    
    @classmethod
    def normalize_column_name(cls, col: str) -> str:
        """Convert CSV column name to standardized name"""
        # First check exact match
        if col in cls.COLUMN_MAPPINGS:
            return cls.COLUMN_MAPPINGS[col]
        
        # Fallback: convert to lowercase with underscores
        normalized = col.lower().strip()
        normalized = re.sub(r'\s+', '_', normalized)
        normalized = re.sub(r'[/\.\-]+', '_', normalized)
        return normalized
    
    @classmethod
    def normalize_status_value(cls, status: str) -> str:
        """Normalize case status for consistent matching"""
        if pd.isna(status):
            return ''
        
        normalized = str(status).strip().lower()
        normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces to single
        normalized = re.sub(r'[-––—]+', '-', normalized)  # Normalize dashes
        return normalized
    
    @classmethod
    def categorize_service(cls, service: str) -> str:
        """
        Categorize service into Drug or Non-Drug
        
        Logic:
        1. Check if any DRUG keyword exists -> Drug
        2. Check if any NON-DRUG keyword exists -> Non-Drug
        3. Default to Non-Drug
        """
        if pd.isna(service) or service == '':
            return 'Unknown'
        
        service_lower = str(service).lower().strip()
        
        # Check for Drug keywords first (higher priority)
        for keyword in cls.DRUG_SERVICE_KEYWORDS:
            if keyword.lower() in service_lower:
                return cls.SERVICE_CATEGORIES['drug']
        
        # Then check for Non-Drug keywords
        for keyword in cls.NON_DRUG_SERVICE_KEYWORDS:
            if keyword.lower() in service_lower:
                return cls.SERVICE_CATEGORIES['non_drug']
        
        # Default to Non-Drug (most medical services are non-drug)
        return cls.SERVICE_CATEGORIES['non_drug']
    
    @classmethod
    def get_service_breakdown(cls, df: pd.DataFrame) -> dict:
        """
        Analyze service categorization in the dataframe
        
        Returns:
            Dictionary with service breakdown statistics
        """
        if 'service' not in df.columns:
            return {}
        
        df_temp = df.copy()
        df_temp['service_category'] = df_temp['service'].apply(cls.categorize_service)
        
        breakdown = {
            'total_services': df['service'].nunique(),
            'drug_count': (df_temp['service_category'] == 'Drug').sum(),
            'non_drug_count': (df_temp['service_category'] == 'Non-Drug').sum(),
            'unknown_count': (df_temp['service_category'] == 'Unknown').sum(),
            'by_service': df_temp.groupby(['service', 'service_category']).size().to_dict()
        }
        
        return breakdown