# Welleazy MIS Dashboard - Technical Documentation

## 1. Project Overview

The **Welleazy MIS Dashboard** is a comprehensive executive reporting tool designed to aggregate, process, and visualize data from the Welleazy CRM. It provides real-time insights into case statuses, turnaround times (TAT), operational efficiency, and client performance.

Built with **Streamlit**, **Pandas**, and **Plotly**, the application processes raw Excel/CSV data to generate interactive metrics and downloadable reports.

## 2. Dashboard Tabs & Features

The dashboard is organized into 7 key tabs, each serving a specific analytical purpose:

### 📊 1. Overview

**Purpose:** High-level executive summary of project health.

- **Key Metrics:**
  - **Total Cases:** Total volume of cases in the uploaded dataset.
  - **Closure Rate:** Percentage of cases with a "Closed" status.
    - 🟢 Excellent: ≥ 90%
    - 🟡 Warning: 80-89%
    - 🔴 Critical: < 80%
  - **Avg TAT:** Average turnaround time for **all cases** with appointment dates.
    - **Formula:** `(Current date – Appointment date)` for all cases with valid appointment dates.
    - _Note: This calculation uses Calendar Days and includes all case statuses._
    - Target: ≤ 2.0 days.
  - **High TAT Cases:** Count of active cases exceeding the 3-day threshold.
- **Visualizations:** Case Status pie chart, Service Category distribution.

### 👥 2. Clients

**Purpose:** Analysis of volume and efficiency by client.

- **Metrics:**
  - **Received:** Total cases initiated by the client.
  - **Closed:** Total cases successfully closed.
  - **Closure Rate:** Efficiency score (`Closed / Received * 100`).
- **Features:** Top 10 Clients table and comparative bar charts.

### 🏥 3. Operations

**Purpose:** Geographic and Diagnostic Center (DC) performance.

- **Metrics:**
  - **City-wise Volume:** Number of cases per city.
  - **City-wise Closure:** Efficiency of operations in specific locations.

### ⏱️ 4. TAT MIS (Turnaround Time)

**Purpose:** Monitoring of active cases where the medical checkup is done but the report is still awaited.

- **Filter Logic:**
  - Status = `Medical Done - Report Awaited` (and variations).
- **Key Calculation:**
  - **Current TAT** = `(Current date – Appointment date)`
  - _Note: This calculation uses Calendar Days._
- **Alerts:** Highlights cases where TAT > 3 days.
- **Export:** Downloadable Excel report of all high-TAT cases.

### 📋 5. Pending

**Purpose:** Pipeline analysis of cases not yet closed or in the medical stage.

- **Filter Logic:**
  - Includes statuses like: `Fresh case`, `Call Later`, `Appointment Missed`, `Waiting for DC Confirmation`, etc.
- **Key Metrics:**
  - **Total Pending:** Count of all non-closed, non-TAT cases.
  - **Critical Cases:** "Fresh cases" or Escalations that require immediate attention.

### ✅ 6. Closure TAT

**Purpose:** Retrospective analysis of closed cases to measure true operational speed.

- **Metrics:**
  - **Closure TAT:** The time taken from Appointment to Report Submission.
    - **Formula:** `NETWORKDAYS(Appointment date, Case Completion date, 11) - 1`
    - _Note: Uses **Business Days** (Mon-Sat, excluding Sundays). Excludes specific Indian Holidays._
  - **Scheduled TAT:** Time from Case Receipt to Appointment Fixing.
    - **Formula:** `(Appointment fixed Date - Case received Date)`
    - **Formula:** `(Appointment fixed Date - Case received Date)`
    - **Note:** Uses Calendar Days.

  - **Column Headers Explanation (e.g., "2025-11 (TAT 0)"):**
    - These columns refer to the **Percentage of cases** completed within that specific number of days for that month.
    - **TAT 0**: Same-day completion (0 days).
    - **TAT 1**: Completed in 1 day.
    - **TAT 2**: Completed in 2 days.
    - **TAT 3**: Completed in 3 days **or more** (all cases >3 days are grouped here).

### 📅 7. Daily MIS

**Purpose:** Granular daily operational logs, bifurcated by service type.

- **Categories:**
  - **Drug Cases:** Services containing keywords like "drug", "urine", "alcohol", "toxicology".
  - **Non-Drug Cases:** Services containing keywords like "medical", "blood", "x-ray", "health".
- **Reports:**
  - **Client Report Structure:** Mimics Excel VLOOKUP logic. For each month, it displays 3 columns:
    - `[Month]_Received`: Based on Case Entry Date.
    - `[Month]_Closed`: Based on Report Upload Date (merged via Client Name).
    - `[Month]_Closure%`: `(Closed / Received) * 100`.
  - **Bifurcation:** Separate sheets for **Drug Cases** and **Non-Drug Cases**, both following the same 3-column monthly structure.

---

## 3. Technical Glossary & Calculations

### Status Normalization

To ensure data consistency, the system "normalizes" status values (e.g., converts `Medical Done-Report Awaited` and `Medicals Done - Report Awaited` to a single standard value).

### Service Categorization

Services are automatically classified based on keyword matching defined in `welleazy_config.py`:

- **Drug Keywords:** `drug, urine drug, substance, toxicology, alcohol, cannabis, narcotic, drug test, drug screen`
- **Non-Drug Keywords:** `medical, physical, health, checkup, exam, blood test, x-ray, ecg, vaccination, fitness`

### Turnaround Time (TAT) Methodologies

| Metric                   | Formula                                           | Type              | Logic Location                                   |
| :----------------------- | :------------------------------------------------ | :---------------- | :----------------------------------------------- |
| **Overview Avg TAT**     | `(Current date – Appointment date)`               | Calendar Days     | `welleazy_streamlit_app.py` (calc_kpis function) |
| **Active TAT (TAT MIS)** | `(Current date – Appointment date)`               | Calendar Days     | `welleazy_tat_mis.py`                            |
| **Closure TAT**          | `NETWORKDAYS(Appt Date, Completion Date, 11) - 1` | **Business Days** | `welleazy_closure_tat_mis.py`                    |
| **Scheduled TAT**        | `(Appt Fixed Date - Case Received Date)`          | Calendar Days     | `welleazy_closure_tat_mis.py`                    |

    *   **Overview Avg TAT:** Calculated for **all cases** with valid appointment dates, regardless of status.
    *   **Active TAT (TAT MIS):** Calculated only for cases with status = "Medical Done - Report Awaited" (and variations).
    *   **Holidays:** Specific Indian holidays defined in `welleazy_closure_tat_mis.py` are excluded.
    *   **Business Days:** **Monday to Saturday** (Sunday is the only weekend day). This aligns with `NETWORKDAYS.INTL(..., 11)`.

### Business Rules & Thresholds

- **High TAT Threshold:** > 3 days (Configurable in `MISConfig.TAT_THRESHOLD`).
- **Lookback Period:**
  - Closure TAT Report: Last 2 months.
  - Daily MIS Report: Last 3 months.
- **TAT Capping:** For reporting purposes, TAT values sometimes capped at specific maximums (legacy requirement, currently set to max cap of 3 in configuration if enabled).

---

## 4. Setup & Configuration

### Prerequisites

- Python 3.8+
- Pandas, Streamlit, Plotly, Openpyxl, Requests

### Installation

```bash
pip install -r welleazy_requirements.txt
```

### Running the Application

```bash
streamlit run welleazy_streamlit_app.py
```

### Data Input Options

The system supports **two methods** for loading data:

#### Option 1: File Upload (Excel/CSV)

Upload Excel (`.xlsx`) or CSV files through the Streamlit interface. The logic automatically maps your raw column names to system headers.

#### Option 2: API Integration

When no file is uploaded, click the **"🌐 Load Data from API"** button to fetch data directly from:

```
http://api.welleazy.com/PhysicalMedicalMISReport
```

- **Method:** GET
- **Authentication:** None required
- **Format:** JSON or CSV response

The API integration allows real-time data loading without manual file uploads, making it ideal for automated reporting workflows.

### Required Data Columns

Key columns looked for include:

- `Client Name`
- `Case ID/TA Code`
- `Appointment Date`
- `Case Status`
- `Service`
- `Report Upload Date`

_(See `welleazy_config.py` for the full column mapping list)_

---

## 5. Backend Calculation Logic - Deep Dive

This section provides a detailed, step-by-step explanation of how each MIS report is calculated in the backend.

---

### 5.1 TAT MIS (Turnaround Time Report)

**File:** `welleazy_tat_mis.py`  
**Class:** `TATMISGenerator`

#### Purpose

Monitor active cases where medical checkups are complete but reports are still pending. Identify cases exceeding the 3-day TAT threshold.

#### Calculation Steps

**Step 1: Data Filtering**

```python
# Filter by status (case-insensitive matching)
target_statuses = [
    'Medical Done - Report Awaited',
    'Medical Done-Report Awaited',
    'Medicals Done - Report Awaited',
    'Medicals Done-Report Awaited'
]
filtered_df = df[df['case_status'].str.lower().isin([s.lower() for s in target_statuses])]
```

**Step 2: TAT Calculation**

```python
# Formula: Current Date - Appointment Date (Calendar Days)
current_date = pd.Timestamp.now().normalize()
df['tat_days'] = (current_date - df['appointment_date']).dt.days

# Handle negative TATs (future appointments)
df['tat_days'] = df['tat_days'].clip(lower=0)
```

**Step 3: Sorting**

```python
# Sort by TAT descending (highest TAT first)
report = df.sort_values('tat_days', ascending=False)
```

**Step 4: High TAT Flagging**

```python
# Flag cases where TAT > 3 days
df['high_tat'] = df['tat_days'] > 3  # MISConfig.TAT_THRESHOLD
```

**Step 5: Column Selection**

```python
# Keep only relevant columns for the report
columns = [
    'client_name',
    'customer_name',
    'case_id',
    'appointment_date',
    'tat_days',
    'high_tat',
    'case_status',
    'dc_name',
    'dc_city'
]
report = df[columns]
```

#### Excel Export Logic

- High TAT rows (TAT > 3) are highlighted with **red background** (`FFC7CE`)
- Headers have **blue background** (`366092`) with white bold text
- Columns are auto-sized for readability

---

### 5.2 Pending Case MIS

**File:** `welleazy_pending_mis.py`  
**Class:** `PendingCaseMISGenerator`

#### Purpose

Track cases that are not yet closed or in the medical stage. Identify critical cases requiring immediate attention.

#### Calculation Steps

**Step 1: Status Filtering**

```python
# Filter for pending statuses
pending_statuses = [
    'Appointment Missed',
    'Appointment Missed - Reschedule Appointment',
    'Call-later',
    'Call Later',
    'Call Later - Customer Not Responding',
    'Call Later - Customer phone switched off',
    'Call Later - Customer asked to call back',
    'Fresh case',
    'Fresh Case',
    'Waiting for DC confirmation',
    'Waiting for DC Confirmation',
    'Appointment Confirmed',
    'Escalated to Co - Customer Not Co-operating',
    'Escalated to Co - Customer Not Interested',
    'Escalated to Co - Max attempts done for the case',
    'Escalated to Co - Wrong/Incomplete Contact Details',
    'Escalated to Co - Other TPA Completed',
    'Escalated to Co - Unable to find DC/Hopsitals',
    'Raised To Network Team- Relevant Network Required',
    'Appointment Related - Partial Medicals pending'
]

filtered_df = df[df['case_status'].str.lower().isin([s.lower() for s in pending_statuses])]
```

**Step 2: Date Preparation**

```python
# Extract month-year from case received date
df['month_year'] = df['case_received_date'].dt.to_period('M').astype(str)
df['month_year'].fillna('Unknown', inplace=True)
```

**Step 3: Pivot Table Creation**

```python
# Structure: Case Status (rows) × Month-Year (columns)
pivot = pd.pivot_table(
    df,
    values='case_id',          # Count of cases
    index='case_status',        # Rows = Status
    columns='month_year',       # Columns = Received Month
    aggfunc='count',            # Count function
    fill_value=0
)
```

**Step 4: Add Totals**

```python
# Add total column (sum across months)
pivot['Total'] = pivot.sum(axis=1)

# Add total row (sum across statuses)
pivot.loc['Total'] = pivot.sum(axis=0)
```

#### Highlighting Logic

```python
# Critical statuses to highlight (Yellow: FFEB9C)
critical_statuses = [
    'Fresh case',
    'Fresh Case',
    'Waiting for DC confirmation',
    'Waiting for DC Confirmation',
    'Appointment Confirmed',
    'Escalated to Co - Customer Not Co-operating',
    'Escalated to Co - Customer Not Interested'
]

# Rows matching these statuses get yellow highlighting
```

---

### 5.3 Closure TAT MIS

**File:** `welleazy_closure_tat_mis.py`  
**Class:** `ClosureTATMISGenerator`

#### Purpose

Retrospective analysis of closed cases to measure operational efficiency. Generates two reports: **Closure TAT** and **Scheduled TAT**.

#### Calculation Steps

**Step 1: Date & Status Filtering**

```python
# Filter for last 2 months
cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=2)

# Filter for closed statuses
closed_statuses = [
    'Closed',
    'Closed - Reports Submitted',
    'Closed - Reports submitted',
    'Closed Reports Submitted',
    'Closed-Reports Submitted',
    'Closed Reports-Submitted'
]

# Apply both filters
filtered_df = df[
    (df['case_completion_date'] >= cutoff_date) &
    (df['case_status'].normalize().isin(closed_statuses.normalize()))
]
```

**Step 2: Closure TAT Calculation (Business Days)**

```python
# Formula: NETWORKDAYS(Appointment Date, Case Completion Date, 11) - 1
# Where 11 = Sunday-only weekend (Mon-Sat are working days)

def calculate_networkdays(start_date, end_date):
    """
    Calculate working days between two dates
    - Excludes: Sundays only
    - Excludes: Indian public holidays (defined list)
    - Returns: Number of working days
    """

    # Define Indian holidays
    indian_holidays = [
        '2024-01-26',  # Republic Day
        '2024-08-15',  # Independence Day
        '2024-10-02',  # Gandhi Jayanti
        '2024-12-25',  # Christmas
        # ... (full list in code)
    ]

    # weekmask: Mon Tue Wed Thu Fri Sat Sun
    #           1   1   1   1   1   1   0
    weekmask = [1, 1, 1, 1, 1, 1, 0]

    # Use numpy's busday_count with custom weekmask
    working_days = np.busday_count(
        start_date.date(),
        end_date.date(),
        weekmask=weekmask,
        holidays=indian_holidays
    )

    return working_days - 1  # Subtract 1 as per Excel formula

# Apply to all rows
df['closure_tat'] = df.apply(
    lambda row: calculate_networkdays(
        row['appointment_date'],
        row['case_completion_date']
    ),
    axis=1
)
```

**Step 3: Scheduled TAT Calculation (Calendar Days)**

```python
# Formula: Appointment Fixed Date - Case Received Date
df['scheduled_tat'] = (
    df['appointment_fixed_date'] - df['case_received_date']
).dt.days
```

**Step 4: TAT Value Cleaning**

```python
# Rule 1: Convert negative TATs to 0
df['closure_tat'] = df['closure_tat'].clip(lower=0)
df['scheduled_tat'] = df['scheduled_tat'].clip(lower=0)

# Rule 2: Cap TATs >= 3 to exactly 3
max_tat = 3  # MISConfig.TAT_MAX_CAP
df['closure_tat'] = df['closure_tat'].apply(lambda x: max_tat if x >= max_tat else x)
df['scheduled_tat'] = df['scheduled_tat'].apply(lambda x: max_tat if x >= max_tat else x)

# Rule 3: Fill NaN with 0 and convert to int
df['closure_tat'].fillna(0, inplace=True)
df['scheduled_tat'].fillna(0, inplace=True)
df['closure_tat'] = df['closure_tat'].astype(int)
df['scheduled_tat'] = df['scheduled_tat'].astype(int)
```

**Step 5: Pivot Table Creation (Closure TAT)**

```python
# Extract month from case completion date
df['completion_month'] = df['case_completion_date'].dt.to_period('M').astype(str)

# Structure: Client Name (rows) × (Month, TAT Bucket) (columns)
pivot = pd.pivot_table(
    df,
    values='case_id',                              # Count of cases
    index='client_name',                            # Rows = Client
    columns=['completion_month', 'closure_tat'],   # Columns = Month × TAT
    aggfunc='count',                                # Count function
    fill_value=0
)

# Result structure:
# Client Name | 2025-11 (TAT 0) | 2025-11 (TAT 1) | 2025-11 (TAT 2) | 2025-11 (TAT 3) | ...
```

**Step 6: Percentage Calculation**

```python
# For each month, calculate percentage distribution
# Formula: (Individual TAT Count / Total for Month) × 100

for month in months:
    # Get all TAT buckets for this month
    month_data = pivot[month]  # e.g., TAT 0, 1, 2, 3

    # Calculate total cases per client for this month
    month_totals = month_data.sum(axis=1)

    # Calculate percentage for each TAT bucket
    for tat in [0, 1, 2, 3]:
        pivot[(month, tat)] = (month_data[tat] / month_totals) * 100
        pivot[(month, tat)] = pivot[(month, tat)].round(2)

# Example Result:
# Client Name | 2025-11 (TAT 0) | 2025-11 (TAT 1) | 2025-11 (TAT 2) | 2025-11 (TAT 3)
# ABC Corp     |     25.50%      |     40.30%      |     20.10%      |     14.10%
# XYZ Ltd      |     30.00%      |     35.00%      |     25.00%      |     10.00%
```

**Step 7: Scheduled TAT Pivot (Same Logic)**

```python
# Same structure as Closure TAT, but using 'scheduled_tat' column
pivot_scheduled = pd.pivot_table(
    df,
    values='case_id',
    index='client_name',
    columns=['completion_month', 'scheduled_tat'],
    aggfunc='count',
    fill_value=0
)

# Apply same percentage calculation
```

#### Key Differences: Closure vs Scheduled TAT

| Aspect         | Closure TAT                                 | Scheduled TAT                               |
| -------------- | ------------------------------------------- | ------------------------------------------- |
| **Date Range** | Appointment Date → Case Completion Date     | Case Received Date → Appointment Fixed Date |
| **Day Type**   | **Business Days** (Mon-Sat, excl. holidays) | **Calendar Days** (all days)                |
| **Formula**    | `NETWORKDAYS(..., 11) - 1`                  | Simple date difference                      |
| **Purpose**    | Measure report generation speed             | Measure appointment scheduling speed        |

---

### 5.4 Daily MIS

**File:** `welleazy_daily_mis.py`  
**Class:** `DailyMISGenerator`

#### Purpose

Generate comprehensive daily operational reports with Drug/Non-Drug bifurcation, showing received vs closed cases by month.

#### Calculation Steps

**Step 1: Date Filtering**

```python
# Filter last 3 months based on case entry date
cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=3)
filtered_df = df[df['case_entry_date'] >= cutoff_date]
```

**Step 2: Service Categorization**

```python
# Categorize each service as Drug or Non-Drug
def categorize_service(service_name):
    drug_keywords = ['drug', 'urine drug', 'substance', 'toxicology', 'alcohol',
                     'cannabis', 'narcotic', 'drug test', 'drug screen']

    service_lower = str(service_name).lower()

    # Check if any drug keyword is in service name
    for keyword in drug_keywords:
        if keyword in service_lower:
            return 'Drug'

    # Otherwise, it's Non-Drug
    return 'Non-Drug'

df['service_type'] = df['service'].apply(categorize_service)
```

**Step 3: Case Status Report (Service Breakdown)**

```python
# Extract month from case entry date
df['entry_month'] = df['case_entry_date'].dt.to_period('M').astype(str)

# Structure: Case Status (rows) × (Month, Service Type) (columns)
pivot = pd.pivot_table(
    df,
    values='case_id',
    index='case_status',                      # Rows = Status
    columns=['entry_month', 'service_type'],  # Columns = Month × Service
    aggfunc='count',
    fill_value=0
)

# Add totals
pivot.loc['Total'] = pivot.sum(axis=0)

# Result structure:
# Status                      | 2025-11 (Drug) | 2025-11 (Non-Drug) | 2025-12 (Drug) | ...
# Closed - Reports Submitted  |      150       |        2500        |      160       | ...
# Medical Done - Report Await |       5        |         20         |       3        | ...
```

**Step 4: Client Received Report**

```python
# Structure: Client Name (rows) × Month (columns)
client_received = pd.pivot_table(
    df,
    values='case_id',
    index='client_name',     # Rows = Client
    columns='entry_month',   # Columns = Month
    aggfunc='count',
    fill_value=0
)

# Remove 'Welleazy Demo' if exists (test data)
if 'Welleazy Demo' in client_received.index:
    client_received = client_received.drop('Welleazy Demo')

# Result structure:
# Client Name | 2025-10 | 2025-11 | 2025-12
# ABC Corp    |   250   |   300   |   280
# XYZ Ltd     |   150   |   180   |   160
```

**Step 5: Closure Data Generation** ⚠️ **CRITICAL FIX APPLIED**

```python
# FIXED: Use case_entry_date (not report_upload_date) to match received logic
# This ensures Closed ≤ Received always

cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=3)

# Filter for closed cases entered in last 3 months
closed_statuses = ['Closed', 'Closed - Reports Submitted', ...]
closure_df = df[
    (df['case_entry_date'] >= cutoff_date) &              # FIXED: was report_upload_date
    (df['case_status'].normalize().isin(closed_statuses))
]

# Extract month from case_entry_date
closure_df['entry_month'] = closure_df['case_entry_date'].dt.to_period('M').astype(str)

# Structure: Client Name (rows) × (Month, Service Type) (columns)
closure_pivot = pd.pivot_table(
    closure_df,
    values='case_id',
    index='client_name',
    columns=['entry_month', 'service_type'],
    aggfunc='count',
    fill_value=0
)

# Result structure:
# Client Name | 2025-11 (Drug) | 2025-11 (Non-Drug) | 2025-12 (Drug) | ...
# ABC Corp    |      120       |        2300        |      140       | ...
# XYZ Ltd     |       80       |         850        |       75       | ...
```

**Step 6: VLOOKUP Merge Logic**

```python
# For each month, create 3 columns: Received, Closed, Closure%
# This mimics Excel VLOOKUP behavior

result = pd.DataFrame(index=client_received.index)

for month in months:
    # Get received count for this month
    received_count = client_received[month]

    # Get closed count from closure data (VLOOKUP equivalent)
    if month in closure_pivot.columns.get_level_values(0):
        # Sum Drug + Non-Drug for this month
        month_data = closure_pivot[month]
        closed_count = month_data.sum(axis=1)  # Sum across service types

        # Reindex to match client_received (handles missing clients)
        closed_count = closed_count.reindex(client_received.index, fill_value=0)
    else:
        # No closure data for this month
        closed_count = pd.Series(0, index=client_received.index)

    # Calculate percentage
    percentage = (closed_count / received_count * 100).fillna(0).round(2)

    # Add 3 columns for this month
    result[f'{month}_Received'] = received_count
    result[f'{month}_Closed'] = closed_count.astype(int)
    result[f'{month}_Closure%'] = percentage

# Result structure:
# Client Name | 2025-11_Received | 2025-11_Closed | 2025-11_Closure% | 2025-12_Received | ...
# ABC Corp    |       300        |      280       |      93.33%      |       280        | ...
# XYZ Ltd     |       180        |      165       |      91.67%      |       160        | ...
```

**Step 7: Drug/Non-Drug Bifurcation**

```python
# Create separate reports for Drug and Non-Drug services
drug_df = df[df['service_type'] == 'Drug']
non_drug_df = df[df['service_type'] == 'Non-Drug']

# For each service type, generate same structure:
# - Received (by entry month)
# - Closed (by entry month)  ← FIXED: uses entry month, not upload month
# - Closure%

# Drug Report
drug_report = generate_service_specific_report(drug_df, 'Drug')

# Non-Drug Report
non_drug_report = generate_service_specific_report(non_drug_df, 'Non-Drug')
```

#### Why the Fix Was Necessary

**Problem Before Fix:**

```python
# Old logic (WRONG):
received = cases where case_entry_date in last 3 months
closed = cases where report_upload_date in last 3 months

# This caused: Closed > Received (impossible!)
# Example: Case entered 6 months ago, report uploaded recently
#   → Counted in CLOSED, but NOT in RECEIVED
```

**Solution After Fix:**

```python
# New logic (CORRECT):
received = cases where case_entry_date in last 3 months
closed = cases (among received) where status = Closed

# Both use same cohort: cases entered in last 3 months
# This ensures: Closed ≤ Received (always true)
```

#### Excel Export Structure

The Daily MIS generates an Excel file with 4 sheets:

1. **Case Status**: Status breakdown by month and service type
2. **Client Report**: Combined report with Received, Closed, Closure% for all services
3. **Drug Cases**: Same structure as Client Report, filtered for Drug services only
4. **Non-Drug Cases**: Same structure as Client Report, filtered for Non-Drug services only

Each sheet includes:

- **Blue header** (`366092`) with white bold text
- **Gray background** (`E7E6E6`) for percentage columns
- **Bold client names** in the first column
- **Auto-sized columns** for readability
- **Borders** around all cells

---

## 6. Data Normalization & Preprocessing

**File:** `welleazy_normalization.py`  
**Class:** `DataNormalizer`

Before any calculations, raw data goes through normalization:

### Step 1: Column Name Standardization

```python
# Map raw CSV column names to system names
COLUMN_MAPPINGS = {
    'Client Name': 'client_name',
    'Customer Name': 'customer_name',
    'Case ID/TA Code': 'case_id',
    'Appointment Date': 'appointment_date',
    'Case Entry Date': 'case_entry_date',
    'Case Status': 'case_status',
    # ... (full list in config)
}

# Apply mappings
df.rename(columns=COLUMN_MAPPINGS, inplace=True)
```

### Step 2: Whitespace Cleaning

```python
# Remove leading/trailing spaces from all string columns
for col in string_columns:
    df[col] = df[col].str.strip()

# Normalize internal spacing in case_status
df['case_status'] = df['case_status'].str.replace(r'\s+', ' ', regex=True)
```

### Step 3: Date Parsing

```python
# Try multiple date formats
DATE_FORMATS = [
    '%Y-%m-%d',
    '%d-%m-%Y',
    '%m/%d/%Y',
    '%d/%m/%Y',
    '%Y/%m/%d',
    '%d-%b-%Y',
    '%Y-%m-%d %H:%M:%S',
    '%d-%m-%Y %H:%M:%S'
]

# Parse each date column
for col in date_columns:
    df[col] = pd.to_datetime(df[col], errors='coerce')

    # If many failed, try specific formats
    for date_format in DATE_FORMATS:
        temp = pd.to_datetime(df[col], format=date_format, errors='coerce')
        if temp.isna().sum() < df[col].isna().sum():
            df[col] = temp
            break
```

### Step 4: Status Normalization

```python
# Standardize case status values for consistent matching
def normalize_status_value(status):
    if pd.isna(status):
        return ''

    normalized = str(status).strip().lower()
    normalized = re.sub(r'\s+', ' ', normalized)      # Multiple spaces → single
    normalized = re.sub(r'[-–—]+', '-', normalized)   # Normalize dashes

    return normalized

# Apply to all status comparisons
```

### Step 5: Service Categorization

```python
# Categorize each service into Drug or Non-Drug
def categorize_service(service):
    if pd.isna(service):
        return 'Unknown'

    service_lower = str(service).lower().strip()

    # Check Drug keywords
    drug_keywords = ['drug', 'urine drug', 'substance', 'toxicology', ...]
    for keyword in drug_keywords:
        if keyword in service_lower:
            return 'Drug'

    # Check Non-Drug keywords
    non_drug_keywords = ['medical', 'physical', 'health', 'checkup', ...]
    for keyword in non_drug_keywords:
        if keyword in service_lower:
            return 'Non-Drug'

    # Default to Non-Drug
    return 'Non-Drug'

df['service_category'] = df['service'].apply(categorize_service)
```

---

## 7. Configuration & Thresholds

**File:** `welleazy_config.py`  
**Class:** `MISConfig`

All business rules, thresholds, and mappings are centralized:

### TAT Thresholds

```python
TAT_THRESHOLD = 3  # Days - Cases exceeding this are flagged
TAT_MAX_CAP = 3    # Cap TAT at this value for percentage calculations
```

### Lookback Periods

```python
LOOKBACK_MONTHS = {
    'closure_tat': 2,   # Closure TAT analyzes last 2 months
    'daily_mis': 3      # Daily MIS analyzes last 3 months
}
```

### Status Filters

```python
STATUS_FILTERS = {
    'tat_mis': [
        'Medical Done - Report Awaited',
        'Medical Done-Report Awaited',
        'Medicals Done - Report Awaited',
        'Medicals Done-Report Awaited'
    ],
    'pending_mis': [
        'Appointment Missed',
        'Call-later',
        'Call Later',
        'Fresh case',
        'Waiting for DC confirmation',
        # ... (full list)
    ],
    'closed_cases': [
        'Closed',
        'Closed - Reports Submitted',
        'Closed Reports Submitted',
        # ... (variations)
    ]
}
```

### Highlight Statuses (for Pending MIS)

```python
HIGHLIGHT_STATUSES = [
    'Fresh case',
    'Fresh Case',
    'Waiting for DC confirmation',
    'Waiting for DC Confirmation',
    'Appointment Confirmed',
    'Escalated to Co - Customer Not Co-operating',
    'Escalated to Co - Customer Not Interested'
]
```

---

## 8. Performance Optimizations

### 8.1 Status Counting Optimization

**Before (Slow):**

```python
# Counted each status individually - O(n) for each status
for status in unique_statuses:
    count = (df['case_status'] == status).sum()  # Scans entire dataset
```

**After (Fast):**

```python
# Use value_counts() - O(n) once for all statuses
status_counts = df['case_status'].value_counts(dropna=True)
# Show only top 10 to avoid log spam
for status, count in status_counts.head(10).items():
    logger.info(f"  '{status}' ({count} records)")
```

### 8.2 Large CSV Handling

```python
# Read CSV with optimized settings
df = pd.read_csv(filepath, low_memory=False)  # Prevents dtype warnings
```

### 8.3 Date Parsing

```python
# Use pandas' optimized date parsing
df['date_col'] = pd.to_datetime(df['date_col'], errors='coerce')
# Falls back to dateutil only if needed
```

---

## 9. Error Handling & Data Quality

### Validation Checks

```python
# 1. Check for duplicate case IDs
duplicates = df['case_id'].duplicated().sum()
if duplicates > 0:
    logger.warning(f"Found {duplicates} duplicate case IDs")

# 2. Check for future dates
future_dates = (df['case_follow_up_date'] > pd.Timestamp.now()).sum()
if future_dates > 0:
    logger.warning(f"Found {future_dates} future dates in case_follow_up_date")

# 3. Check for missing critical columns
required_columns = ['case_status', 'case_entry_date', 'client_name']
missing = [col for col in required_columns if col not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")
```

### Handling Missing Data

```python
# For string columns
df['client_name'].fillna('Unknown', inplace=True)

# For date columns
# Keep NaN as is - will be filtered out in specific MIS logic

# For numeric columns
df['tat_days'].fillna(0, inplace=True)
```

### Edge Cases

```python
# 1. Negative TAT (future appointments)
df['tat_days'] = df['tat_days'].clip(lower=0)

# 2. Division by zero in percentages
percentage = (closed / received).fillna(0) * 100

# 3. Missing clients in closure data
closed_count = closed_count.reindex(received.index, fill_value=0)
```

---

## 10. Summary of Key Formulas

| Report          | Metric        | Formula                                                            | Day Type           |
| --------------- | ------------- | ------------------------------------------------------------------ | ------------------ |
| **TAT MIS**     | Current TAT   | `Current Date - Appointment Date`                                  | Calendar           |
| **Closure TAT** | Closure TAT   | `NETWORKDAYS(Appt Date, Completion Date, 11) - 1`                  | Business (Mon-Sat) |
| **Closure TAT** | Scheduled TAT | `Appt Fixed Date - Case Received Date`                             | Calendar           |
| **Daily MIS**   | Received      | Count where `case_entry_date` in last 3 months                     | -                  |
| **Daily MIS**   | Closed        | Count where `case_entry_date` in last 3 months AND status = Closed | -                  |
| **Daily MIS**   | Closure %     | `(Closed / Received) × 100`                                        | -                  |
| **Pending MIS** | -             | Pivot count by status and month                                    | -                  |

---

## 11. File Structure & Dependencies

```
welleazy_project/
├── welleazy_config.py           # Central configuration
├── welleazy_normalization.py    # Data preprocessing
├── welleazy_validation.py       # Data quality checks
├── welleazy_tat_mis.py          # TAT MIS logic
├── welleazy_pending_mis.py      # Pending Case MIS logic
├── welleazy_closure_tat_mis.py  # Closure TAT MIS logic
├── welleazy_daily_mis.py        # Daily MIS logic
├── welleazy_pipeline.py         # Orchestrator
├── welleazy_streamlit_app.py   # UI/Dashboard
└── welleazy_requirements.txt    # Dependencies
```

**Dependency Flow:**

```
Raw Data → Normalization → Validation → MIS Generators → Reports → UI
                ↓
           Config (shared by all)
```
