"""
Veriright MIS Configuration
Column mappings and business logic for Veriright data processing
"""

class VeriRightConfig:
    """Configuration for Veriright MIS system"""
    
    # Standard column names (internal representation)
    STANDARD_COLUMNS = {
        'client_name': 'client_name',
        'activity_type': 'activity_type',
        'case_received_date': 'case_received_date',
        'case_status': 'case_status',
        'case_received_mode': 'case_received_mode',
        'case_completion_date': 'case_completion_date',
        'customer_profile': 'customer_profile',
        'mer_type': 'mer_type',
        'insurance_company': 'insurance_company',
        'application_number': 'application_number',
        'total_calls': 'total_calls'
    }
    
    # Column mappings from various source formats
    COLUMN_MAPPINGS = {
        # Standard format
        'Client Name': 'client_name',
        'Insurer Name': 'client_name',  # Alternative column name
        'Insurance Company': 'client_name',  # Another alternative
        'Activity Type': 'activity_type',
        'Case Rec`d Date': 'case_received_date',
        'Case Recd Date': 'case_received_date',
        "Case Rec'd Date": 'case_received_date',
        'Case status': 'case_status',
        'Case Status': 'case_status',
        'Case Rec`d Mode': 'case_received_mode',
        'Case Recd Mode': 'case_received_mode',
        "Case Rec'd Mode": 'case_received_mode',
        'Case Completion Date': 'case_completion_date',
        'Case Completetion Date': 'case_completion_date',  # Typo in actual files
        'KYC Completion Date': 'case_completion_date',  # HDFC uses this
        'MER Completion Date': 'case_completion_date',  # SUD uses this
        'Activity Completion Date': 'case_completion_date',
        
        # Alternative names
        'Client': 'client_name',
        'Insurer': 'client_name',
        'Status': 'case_status',
        'Received Date': 'case_received_date',
        'Completion Date': 'case_completion_date',
        'Mode': 'case_received_mode',
        
        # Closed list format
        'Customer Profile': 'customer_profile',
        'MER Type': 'mer_type',
        'Insurance Company': 'insurance_company',
        
        # Additional fields
        'Application Number': 'application_number',
        'Total call': 'total_calls',
        'Total Call': 'total_calls',
    }
    
    # Date columns that need parsing
    DATE_COLUMNS = [
        'case_received_date',
        'case_completion_date'
    ]
    
    # Status filters
    STATUS_FILTERS = {
        'exclude_cancelled': [
            'Cancelled', 
            'Cancelled Cases', 
            'Cancel',
            'Cancelled by Insurance Company',
            'Cancelled by insurance company',
            'Cancelled by insurance Company'
        ],
        'closed_cases': [
            'Closed',
            'Case Closed',
            'Completed',
            'Verification Completed',
            'Report Submitted',
            'Successfully Completed',
            'Closed - Submitted to Insurance',
            'Closed - submitted to insurance',
            'Vcheck Completed - QC Pending',
            'Vcheck completed – QC Pending'
        ],
        'pending_cases': [
            'Pending',
            'In Progress',
            'Assigned',
            'Scheduled',
            'Report Awaited',
            'Medical Done - Report Awaited',
            'Medical Done-Report Awaited',
            'On Hold',
            'Pending - Customer Action Required',
            'Pending - Document Issue'
        ],
        'error_cases': [
            'Technical Error - Data Issue',
            'Status Unknown',
            'Error',
            'System Error'
        ]
    }
    
    # Report-specific configurations
    REPORT_CONFIGS = {
        'SUD': {
            'client_name': 'Star Union Dai-ichi Life Ins',
            'report_format': 'VMS Format',
            'date_range': 'last_3_months'
        },
        'SBI': {
            'client_name': 'SBI Life',
            'report_format': 'VMS Format',
            'activity_type': 'Video KYC',
            'date_range': 'Jan 2025 onwards'
        },
        'HDFC_VCHECK': {
            'client_name': 'HDFC Life',
            'report_format': 'IC Format',
            'activity_type': 'VKYC',
            'date_range': 'April onwards'
        },
        'HDFC_ITR': {
            'client_name': 'HDFC ITR',
            'report_format': 'VMS Format',
            'date_range': 'April onwards',
            'mode_mapping': {
                'Manual': 'Assisted',
                'Bulk upload': 'Non-Assisted'
            }
        },
        'OVERALL_MIS': {
            'clients': [
                'Star Union Dai-ichi Life Ins',
                'Canara HSBC',
                'SBI Life',
                'HDFC Life'
            ],
            'date_range': 'last_3_months'
        }
    }
    
    # Client targets
    CLIENT_TARGETS = {
        'Canara HSBC LI Company Limited': 100,
        'HDFC Life Vcheck': 2300,
        'HDFC ITR manual': 100,
        'HDFC Auto': 500,  # Set default target
        'SBI Life': 1000,
        'Star Union Dai-ichi Life Ins': 200
    }
    
    # Client name normalization map (handles spelling variations)
    CLIENT_NAME_NORMALIZATION = {
        # Normalize variations to standard names
        'hdfc life vcheck': 'HDFC Life Vcheck',
        'hdfc vcheck': 'HDFC Life Vcheck',
        'hdfc itr manual': 'HDFC ITR manual',
        'hdfc itr': 'HDFC ITR manual',
        'hdfc auto': 'HDFC Auto',
        'sbi life': 'SBI Life',
        'sbi': 'SBI Life',
        'canara hsbc li company limited': 'Canara HSBC LI Company Limited',
        'canara hsbc': 'Canara HSBC LI Company Limited',
        'star union dai-ichi life ins': 'Star Union Dai-ichi Life Ins',
        'star union': 'Star Union Dai-ichi Life Ins',
        'sud': 'Star Union Dai-ichi Life Ins'
    }
    
    @classmethod
    def get_status_filter(cls, filter_name):
        """Get status filter by name"""
        return cls.STATUS_FILTERS.get(filter_name, [])
    
    @classmethod
    def normalize_status_value(cls, status):
        """Normalize status values for comparison"""
        if pd.isna(status):
            return ''
        return str(status).strip().lower()
    
    @classmethod
    def is_closed_status(cls, status):
        """Check if a status is considered closed"""
        normalized = cls.normalize_status_value(status)
        closed_statuses = [cls.normalize_status_value(s) for s in cls.STATUS_FILTERS['closed_cases']]
        return normalized in closed_statuses
    
    @classmethod
    def is_cancelled_status(cls, status):
        """Check if a status is cancelled"""
        normalized = cls.normalize_status_value(status)
        cancelled_statuses = [cls.normalize_status_value(s) for s in cls.STATUS_FILTERS['exclude_cancelled']]
        return normalized in cancelled_statuses
    
    @classmethod
    def normalize_client_name(cls, client_name):
        """Normalize client name to handle spelling variations"""
        if pd.isna(client_name):
            return None
        
        # Convert to string and clean
        name = str(client_name).strip()
        name_lower = name.lower()
        
        # Check if there's a normalized version
        if name_lower in cls.CLIENT_NAME_NORMALIZATION:
            return cls.CLIENT_NAME_NORMALIZATION[name_lower]
        
        # Return original if no mapping found
        return name
    
    @classmethod
    def get_client_target(cls, client_name):
        """Get target for a specific client"""
        # Normalize client name first
        normalized = cls.normalize_client_name(client_name)
        return cls.CLIENT_TARGETS.get(normalized, None)
    
    @classmethod
    def get_report_config(cls, report_type):
        """Get configuration for a specific report type"""
        return cls.REPORT_CONFIGS.get(report_type, {})


# Required import
import pandas as pd