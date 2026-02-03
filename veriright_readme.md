# VeriRight MIS System

## Overview

VeriRight MIS is integrated into the unified MIS dashboard alongside Welleazy. It provides client-wise monthly performance reports matching the standard VeriRight format.

## Features

- ✅ Multi-file Excel upload (HDFC Life, SBI Life, etc.)
- ✅ Automatic column mapping and normalization
- ✅ **Intelligent status cleanup and categorization**
- ✅ Client-wise monthly performance reports
- ✅ Visual dashboards with KPIs
- ✅ Conditional formatting for closure rates
- ✅ Excel export functionality
- ✅ Case status breakdown
- ✅ Monthly trend analysis

## 🧹 Data Quality Features

### Automatic Status Normalization

The system automatically cleans and standardizes messy status values:

**Error Messages → Standard Categories:**

- `no data found`, `not data found`, `error`, `doc not reflecting`, `pdf not opening`
  → **"Technical Error - Data Issue"**
- `customer not responding`, `customer unavailable`, `customer name mismatch`
  → **"Pending - Customer Action Required"**
- `document not clear`, `doc not clear`, `document quality issue`
  → **"Pending - Document Issue"**

**Standardized Status Values:**

- All variations normalized to proper case (e.g., `IN PROGRESS` → `In Progress`)
- Handles typos and spelling variations (e.g., `errror` → `Technical Error - Data Issue`)
- Consistent formatting across all reports

## Required Excel Columns

Your uploaded Excel files should contain these columns:

- **Client Name** (or variations: "Client")
- **Activity Type**
- **Case Rec'd Date** (or variations: "Case Recd Date", "Received Date")
- **Case status** (or variations: "Case Status", "Status")
- **Case Rec'd Mode** (or variations: "Case Recd Mode", "Mode")
- **Case Completion Date** (or variations: "Completion Date")

## How to Use

### 1. Start the Application

```bash
streamlit run welleazy_streamlit_app.py
```

### 2. Select VeriRight System

- In the sidebar, click the **VeriRight** radio button
- The interface will switch to VeriRight mode

### 3. Upload Data Files

- Click "Upload Data Files" in the sidebar
- Select multiple files (HDFC Life, SBI Life, etc.)
- Supported formats: Excel (.xlsx, .xls) or CSV (.csv)
- All files will be merged and processed together

### 4. Process Data

- Click the "🚀 Process Data" button
- Wait for the data normalization to complete
- You'll see a success message with the total records loaded

### 5. Explore Reports

**Client Performance Tab:**

- Summary KPIs (Total Cases, Closed, Pending, Closure Rate)
- Client-wise monthly performance table (matching standard format)
- Closure rate bar chart
- Cases by client pie chart
- Download client report as Excel

**Detailed Reports Tab:**

- Case status breakdown with charts
- Monthly case trend line chart
- Raw data explorer with download option

## Report Format

The main report follows this format:

| Client name | Month | Total case received | Closed case | % As per Close | Closure Date case | Targets-December |
| ----------- | ----- | ------------------- | ----------- | -------------- | ----------------- | ---------------- |
| Client A    | Oct   | 100                 | 85          | 85%            | 15                | 100              |
| Client A    | Nov   | 120                 | 95          | 79%            | 18                | 100              |

### Columns Explained:

- **Client name**: Client identifier
- **Month**: Month name (extracted from Case Received Date)
- **Total case received**: Cases received in that month
- **Closed case**: Cases closed (from those received in that month)
- **% As per Close**: Closure percentage
- **Closure Date case**: Cases completed in that month (by completion date)
- **Targets-December**: Monthly target (if configured)

---

## 📊 Detailed Calculation Methodology

### 1. **Total Case Received**

```
Formula: COUNT(All cases where Case Received Date falls in the specific month)

Logic:
- Extract month from "Case Rec'd Date" column
- Group cases by Client Name and Month
- Count total records for each group

Example:
If HDFC Life has 1,956 cases received in October 2023
→ Total case received = 1,956
```

### 2. **Closed Case**

```
Formula: COUNT(Cases that are either status-closed OR have completion date)

Dual Logic (OR condition):
A. Status-based closure: Case Status ∈ ['Closed', 'Completed', 'Verification Completed']
   OR
B. Completion-based closure: Case Completion Date is NOT NULL (exists)

A case is considered CLOSED if EITHER condition A OR condition B is TRUE.

Example:
From 1,956 cases received in October:
- 1,200 have status = "Closed"
- 195 have completion date filled but status = "In Progress"
→ Closed case = 1,395 (both groups combined)
```

**Why Dual Logic?**

- Some cases may have completion dates but status not updated
- Some cases may have status updated but completion date pending
- This ensures accurate closure counting

### 3. **% As per Close (Closure Percentage)**

```
Formula: (Closed case / Total case received) × 100

Calculation:
- Uses the "Closed case" count (with dual logic)
- Divided by "Total case received"
- Rounded to 1 decimal place

Example:
Closed case = 1,395
Total case received = 1,956
→ % As per Close = (1,395 / 1,956) × 100 = 71.3%
```

**Color Coding:**

- 🟢 **Green**: ≥ 90% (Excellent performance)
- 🟡 **Yellow**: 80-89% (Good performance)
- 🔴 **Red**: < 80% (Needs attention)

### 4. **Closure Date Case**

```
Formula: COUNT(Cases where Completion Date falls in the specific month)

Logic:
- Filter cases by Case Completion Date (not Case Received Date)
- Extract month from "Case Completion Date"
- Count cases completed in that specific month
- Includes cases received in ANY month (not just current month)

Example:
Cases completed in October (regardless of when received):
- 500 cases received in Sept and completed in Oct
- 972 cases received in Oct and completed in Oct
→ Closure Date case = 1,472
```

**Key Difference from "Closed Case":**

- **Closed Case**: Cases received in Month X and marked closed (by status or completion)
- **Closure Date Case**: Cases actually completed in Month X (by completion date), regardless of when received

### 5. **Targets**

```
Formula: Predefined constant per client

Logic:
- Retrieved from CLIENT_TARGETS configuration
- Set manually based on business requirements
- Does NOT auto-calculate

Example:
VeriRightConfig.CLIENT_TARGETS = {
    'HDFC Life Vcheck': 2300,
    'SBI Life': 1000,
    'Star Union Dai-ichi Life Ins': 200
}
→ HDFC Life shows Target = 2,300 for all months
```

---

## 🔍 Overall MIS Calculation Flow

### Step-by-Step Process:

**Step 1: Data Loading & Merging**

```
- Load multiple Excel/CSV files
- Merge all data into single DataFrame
- Track source file for each record
```

**Step 2: Column Normalization**

```
- Map variant column names to standard names:
  "Case Recd Date" → "case_received_date"
  "Case Status" → "case_status"
  "Client" → "client_name"
  etc.
```

**Step 3: Date Parsing**

```
- Convert all date columns to datetime format
- Extract month and year components
- Handle invalid date formats gracefully
```

**Step 4: Status Categorization**

```
- Classify each status as: Closed, Pending, or Cancelled
- Apply status filters from configuration
- Handle case variations (uppercase, lowercase, spaces)
```

**Step 5: Monthly Grouping**

```
For each Client:
  For each Month:
    - Filter cases received in that month
    - Apply closure logic (dual check)
    - Calculate metrics
    - Retrieve target
    - Append to results
```

**Step 6: Report Generation**

```
- Create DataFrame from results
- Sort by Client Name, then Month
- Format percentages with 1 decimal
- Apply conditional formatting for closure rates
```

---

## 📈 Example Calculation Walkthrough

**Sample Data: HDFC Life - October 2023**

**Raw Data:**

- 1,956 cases received in October
- 1,200 cases with status = "Closed"
- 195 cases with completion date but status = "In Progress"
- 1,472 cases have completion date in October
- Target = 2,300

**Calculations:**

1. **Total case received** = 1,956 ✓
2. **Closed case** = 1,200 (status closed) + 195 (completion exists) = 1,395 ✓
3. **% As per Close** = (1,395 / 1,956) × 100 = 71.3% 🔴
4. **Closure Date case** = 1,472 ✓
   (Includes cases received in Sept but completed in Oct)
5. **Targets** = 2,300 ✓

**Final Row:**
| HDFC Life | Oct | 1,956 | 1,395 | 71.3% 🔴 | 1,472 | 2,300 |

---

## 🎯 Performance Interpretation

### Closure Rate Analysis:

- **71.3%** indicates that of 1,956 cases received in October, 1,395 are closed
- Falls below 80% threshold → Red alert
- Gap to target: 2,300 - 1,956 = 344 cases short of target volume

### Closure Date vs Closed Case:

- **Closed case** (1,395): Cases received in Oct and now closed
- **Closure Date case** (1,472): Total cases completed in Oct (any receive date)
- Higher closure date count suggests backlog clearance

### Recommendations when Closure < 80%:

1. Review pending cases from that month
2. Identify bottlenecks in verification process
3. Allocate additional resources
4. Follow up on cases stuck in specific statuses

## Configuration

### Client Targets

Edit `veriright_config.py` to set targets:

```python
CLIENT_TARGETS = {
    'Canara HSBC LI Company Limited': 100,
    'HDFC Life Vcheck': 2300,
    'HDFC ITR manual': 100,
    'SBI Life': 1000,
    'Star Union Dai-ichi Life Ins': 200
}
```

### Status Filters

Configure which statuses are considered closed/pending:

```python
STATUS_FILTERS = {
    'exclude_cancelled': ['Cancelled', 'Cancelled Cases'],
    'closed_cases': ['Closed', 'Completed', 'Verification Completed'],
    'pending_cases': ['Pending', 'In Progress', 'Assigned']
}
```

## Color Coding

- 🟢 **Green (Excellent)**: Closure rate ≥ 90%
- 🟡 **Yellow (Good)**: Closure rate ≥ 80%
- 🔴 **Red (Alert)**: Closure rate < 80%

## Files Structure

```
veriright_config.py          # Configuration and mappings
veriright_normalization.py   # Data cleaning and normalization
veriright_daily_mis.py       # Report generation
veriright_pipeline.py        # Data pipeline orchestration
welleazy_streamlit_app.py    # Main dashboard (unified)
```

## Switching Between Systems

- Use the radio button in the sidebar
- Data from both systems is kept in separate session states
- No need to re-upload data when switching back

## Troubleshooting

### "No data could be processed"

- Check that your Excel files contain the required columns
- Verify column names match the expected format
- Ensure date columns have valid date values

### "Error processing VeriRight data"

- Check the error message for details
- Verify Excel files are not corrupted
- Ensure files are in .xlsx or .xls format

### Empty reports

- Check date filters if implemented
- Verify data is present in uploaded files
- Ensure cases have proper status values

### Messy or inconsistent status values

✅ **Automatically handled!** The system now:

- Cleans up error messages into standard categories
- Normalizes case variations and typos
- Groups similar statuses for clearer reporting
- See the "Data Quality Features" section above for details

## Download Options

1. **Client Report**: Full monthly report with all clients
2. **Raw Data**: Normalized and merged data from all sources

## Notes

- Cancelled cases are automatically filtered out
- Closure calculation uses received date, not completion date
- Last 3 months of data are included by default
- Multiple files are merged automatically with source tracking
