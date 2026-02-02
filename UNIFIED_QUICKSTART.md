# Unified MIS Dashboard - Quick Start Guide

## 🚀 Getting Started

### Prerequisites
Install required packages:
```bash
pip install -r welleazy_requirements.txt
```

### Launch the Dashboard
```bash
streamlit run welleazy_streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📊 Using the Dashboard

### System Selection
At the top of the sidebar, you'll see two options:
- **Welleazy**: Healthcare case management MIS
- **VeriRight**: Client performance MIS

Click to switch between systems. Each maintains its own data and state.

---

## 🏥 Welleazy Mode

### Upload Data
1. Click "Upload CRM Data" in the sidebar
2. Select your CSV/Excel file
3. Click "🚀 Process Data"

### Available Tabs
1. **Overview**: Executive dashboard with KPIs and trends
2. **Clients**: Client-wise performance metrics
3. **Operations**: DC performance by location
4. **TAT MIS**: Turnaround time analysis
5. **Pending**: Pending cases report
6. **Closure TAT**: Closure and scheduled TAT breakdown
7. **Daily MIS**: Comprehensive daily reports

### Features
- Date range filters
- Client selection filters
- Interactive charts
- Excel export for all reports
- Real-time KPI calculations

---

## 🎯 VeriRight Mode

### Upload Data
1. Click "Upload Data Files" in the sidebar
2. Select **multiple** files (HDFC Life, SBI Life, etc.)
3. Supported formats: Excel (.xlsx, .xls) or CSV (.csv)
4. Click "🚀 Process Data"

### Available Tabs
1. **📊 Client Performance**: 
   - Summary KPIs
   - Client-wise monthly report (matching standard format)
   - Closure rate charts
   - Volume distribution

2. **📈 Detailed Reports**:
   - Case status breakdown
   - Monthly trends
   - Raw data explorer

### Report Format
The main report matches this structure:

| Client name | Month | Total case received | Closed case | % As per Close | Closure Date case | Targets |
|------------|-------|---------------------|-------------|----------------|-------------------|---------|
| HDFC Life  | Oct   | 1956                | 1395        | 71%            | 1472              | 2300    |

### Color Indicators
- 🟢 **Green**: ≥ 90% closure rate
- 🟡 **Yellow**: 80-89% closure rate
- 🔴 **Red**: < 80% closure rate

---

## 📥 Downloads

### Welleazy
Each tab has its own download button:
- TAT Report (Excel)
- Pending Report (Excel)
- Closure TAT Report (Excel)
- Daily MIS (Excel with multiple sheets)

### VeriRight
- Client Monthly Report (Excel)
- Raw Data (Excel)

---

## 🔄 Switching Between Systems

You can freely switch between Welleazy and VeriRight using the sidebar radio buttons. Your uploaded data remains loaded for both systems, so you don't need to re-upload when switching back.

---

## 💡 Tips

### For Welleazy
- Use date filters to focus on specific periods
- Filter by specific clients for targeted analysis
- Check "High TAT Calculation Details" expander for methodology
- Download reports before applying new filters

### For VeriRight
- Upload all client files at once for a complete view
- The system automatically merges and normalizes data
- Cancelled cases are filtered out automatically
- Reports show last 3 months by default

---

## 🎨 Dashboard Features

### Responsive Design
- Works on desktop and tablets
- Dark/light mode support
- Clean, professional interface

### Real-time Updates
- KPIs calculate instantly
- Charts update automatically
- No manual refresh needed

### Data Quality
- Automatic date parsing
- Status normalization
- Duplicate removal
- Missing value handling

---

## 📂 File Structure

```
welleazy_streamlit_app.py       # Main unified dashboard
├── Welleazy Files
│   ├── welleazy_config.py
│   ├── welleazy_normalization.py
│   ├── welleazy_pipeline.py
│   ├── welleazy_daily_mis.py
│   ├── welleazy_tat_mis.py
│   ├── welleazy_pending_mis.py
│   └── welleazy_closure_tat_mis.py
└── VeriRight Files
    ├── veriright_config.py
    ├── veriright_normalization.py
    ├── veriright_pipeline.py
    └── veriright_daily_mis.py
```

---

## 🛠️ Customization

### Update Client Targets (VeriRight)
Edit `veriright_config.py`:
```python
CLIENT_TARGETS = {
    'Your Client Name': 500,
    'Another Client': 1000
}
```

### Update Status Filters
Edit respective config files to adjust which statuses count as closed/pending.

---

## ❓ Troubleshooting

### Dashboard not loading?
- Ensure all dependencies are installed
- Check that you're in the correct directory
- Try: `streamlit run welleazy_streamlit_app.py --server.port 8502`

### Data not processing?
- Verify file format (Excel/CSV)
- Check that required columns exist
- Look at terminal for error messages

### Charts not displaying?
- Clear browser cache
- Refresh the page
- Check browser console for JavaScript errors

---

## 🤝 Support

For issues:
1. Check error messages in terminal
2. Verify data format matches requirements
3. Review respective README files for detailed documentation

---

## 🎉 You're All Set!

Select your system, upload your data, and start exploring your MIS reports!
