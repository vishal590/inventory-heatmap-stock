# Inventory Heatmap & Stock-Out Alerts

> **AI for Good Hackathon** - YourStory/Snowflake  
> A Snowflake-based solution for real-time inventory health monitoring and early stock-out prevention

## 🎯 Problem & Solution

**Problem:** Hospitals, public distribution systems, and NGOs struggle to keep medicines, food, and other essentials available in the right place at the right time. Data on sales/usage, inventory, and purchase orders often lives in separate systems, so teams spot stock issues only when shelves are already empty or over-full.

**Solution:** A single view of stock health that:
- ✅ Shows a **heatmap by location and item**
- ✅ **Warns early** about items likely to run out within a few days
- ✅ **Suggests sensible reorder quantities** or priority lists
- ✅ Provides **easy export** that procurement or field teams can act on

**Impact:** Helps reduce waste and avoid stock-outs of critical supplies.

## 🏗️ Architecture

### Tech Stack (Snowflake)
- **Worksheets/SQL** - Data modeling and analytics
- **Dynamic Tables** - Auto-refresh calculations
- **Streams & Tasks** - Scheduling and automation
- **Streamlit** - Interactive dashboard
- **Optional:** Snowpark (demand estimate), Unistore (action logs)

### Data Flow
```
stock_daily (table)
    ↓
Dynamic Tables (auto-refresh)
    ↓
Streamlit Dashboard
    ↓
Export & Alerts
```

## 📊 Features

### 1. Stock Health Heatmap
- Location × Item visualization
- Color-coded status (Red/Orange/Green)
- Interactive tooltips with key metrics

### 2. Early Warning System
- Configurable risk threshold (days of cover)
- At-risk items table
- Real-time alerts for critical items

### 3. Reorder Suggestions
- Calculated reorder quantities based on:
  - Average daily issue rate
  - Current closing stock
  - Target days of cover (default: 5 days)

### 4. Data Export
- CSV export for at-risk items
- Ready for procurement teams
- Includes all key metrics

### 5. Trend Analysis
- Closing stock trends over time
- Per item/location visualization
- Historical data insights

## 🚀 Getting Started

### Prerequisites
- **Snowflake Account**: Sign up for a free trial at [snowflake.com](https://signup.snowflake.com/) (no credit card required)
- **Python 3.8+**: For local development
- **Git**: To clone the repository

---

## 📋 Step-by-Step Setup Guide

### Option 1: Run Locally (Quick Demo)

This option uses the sample CSV data and doesn't require Snowflake connection.

#### Step 1: Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/inventory-heatmap-stock-alerts.git
cd inventory-heatmap-stock-alerts
```

#### Step 2: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python -m venv .venv
source .venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Run the Application
```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

**Note:** Without Snowflake connection, the app uses `data/sample_stock.csv` as fallback data.

---

### Option 2: Full Setup with Snowflake

This option connects to Snowflake and uses Dynamic Tables, Streams & Tasks.

#### Step 1: Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/inventory-heatmap-stock-alerts.git
cd inventory-heatmap-stock-alerts
```

#### Step 2: Set Up Snowflake

1. **Log in to Snowflake Snowsight**
   - Go to [app.snowflake.com](https://app.snowflake.com)
   - Sign in with your account

2. **Create Database and Schema**
   - Open a new SQL Worksheet in Snowsight
   - Run the following:
   ```sql
   USE ROLE ACCOUNTADMIN;
   USE WAREHOUSE COMPUTE_WH;
   CREATE DATABASE IF NOT EXISTS AI_GOOD;
   USE DATABASE AI_GOOD;
   CREATE SCHEMA IF NOT EXISTS PUBLIC;
   USE SCHEMA PUBLIC;
   ```

3. **Run Initial Setup SQL**
   - In Snowsight, open `sql/setup.sql` from the cloned repository
   - Copy the entire contents
   - Paste into Snowsight SQL Worksheet
   - Click "Run" or press Ctrl+Enter
   - This creates:
     - `stock_daily` table with sample data
     - `inventory_metrics_v` view
     - `inventory_at_risk_v` view

4. **Add Dynamic Tables (Recommended)**
   - Open `sql/dynamic_tables.sql` from the repository
   - Copy and run in Snowsight
   - This creates auto-refreshing Dynamic Tables:
     - `inventory_metrics_dt`
     - `inventory_at_risk_dt`

5. **Add Streams & Tasks (Optional)**
   - Open `sql/streams_tasks.sql` from the repository
   - Copy and run in Snowsight
   - This sets up:
     - Stream for change detection
     - Tasks for automation

#### Step 3: Set Up Local Environment

1. **Create Virtual Environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Mac/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

#### Step 4: Run the Application Locally

```bash
streamlit run app.py
```

The app will:
- Try to connect to Snowflake if running in Snowflake Streamlit
- Fall back to CSV data if running locally without connection
- Display the dashboard at `http://localhost:8501`

---

### Option 3: Deploy in Snowflake Streamlit

Run the app directly in Snowflake (no local setup needed).

#### Step 1: Complete Snowflake Setup
Follow **Step 2** from Option 2 above to set up tables, views, and Dynamic Tables.

#### Step 2: Create Streamlit App in Snowsight

1. In Snowsight, click **"Streamlit"** in the left sidebar
2. Click **"Create"** or **"+ Add new"** → **"Streamlit App"**
3. Name it: `Inventory Heatmap Dashboard`
4. Set context:
   - Database: `AI_GOOD`
   - Schema: `PUBLIC`
   - Warehouse: `COMPUTE_WH`

#### Step 3: Add Code

1. Open `app.py` from the cloned repository
2. Copy the entire contents
3. Paste into the Streamlit editor in Snowsight
4. Click **"Save"** and **"Run"**

The app will run directly in Snowflake and use your Snowflake data.

---

## 🔍 Verifying the Setup

### Check Snowflake Setup

Run these queries in Snowsight to verify:

```sql
-- Check if table exists and has data
SELECT COUNT(*) FROM stock_daily;
-- Should return: 18 (sample rows)

-- Check metrics view
SELECT * FROM inventory_metrics_v;
-- Should show 3 rows (one per location-item combination)

-- Check Dynamic Tables (if created)
SELECT * FROM inventory_metrics_dt;
```

### Check Local Setup

1. Run the app: `streamlit run app.py`
2. You should see:
   - Dashboard title: "Inventory Heatmap & Stock-Out Alerts"
   - Filters for locations and items
   - Heatmap visualization
   - At-risk items table
   - Trend charts

---

## 📝 Usage Instructions

### Using the Dashboard

1. **Filter Data**
   - Use the location and item filters to focus on specific areas
   - Adjust the "At-risk threshold" slider to change sensitivity

2. **View Heatmap**
   - Color-coded status:
     - 🔴 Red: < 2 days of cover
     - 🟠 Orange: 2-5 days of cover
     - 🟢 Green: > 5 days of cover
   - Hover over cells for detailed metrics

3. **Check At-Risk Items**
   - Table shows items with low stock
   - Includes suggested reorder quantities
   - Sort by days of cover to prioritize

4. **Export Data**
   - Click "Export at-risk CSV" button
   - Download CSV file for procurement teams

5. **View Trends**
   - Select item and location from dropdowns
   - See closing stock trends over time

### Adding New Data

To add new stock data in Snowflake:

```sql
INSERT INTO stock_daily (date, location, item, opening_stock, received, issued, closing_stock, lead_time_days)
VALUES 
  ('2026-01-02', 'Central', 'Amoxicillin', 30, 0, 25, 5, 5);
```

If using Dynamic Tables, they will auto-refresh within 1 minute.

---

## 🐛 Troubleshooting

### Local App Not Starting
- **Error**: `streamlit: command not found`
  - **Solution**: Use `python -m streamlit run app.py` instead

### Snowflake Connection Issues
- **Error**: "No data found"
  - **Solution**: Verify tables exist and have data in Snowflake
  - Check database/schema context is correct

### Dynamic Tables Not Refreshing
- **Solution**: 
  - Check warehouse is running: `ALTER WAREHOUSE COMPUTE_WH RESUME;`
  - Verify TARGET_LAG is set correctly
  - Check for errors: `SELECT * FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())`

### Tasks Not Running
- **Solution**: 
  - Tasks are created in SUSPENDED state
  - Resume them: `ALTER TASK <task_name> RESUME;`
  - Check task status: `SHOW TASKS;`

## 📁 Project Structure

```
ai_good/
├── app.py                 # Streamlit dashboard application
├── requirements.txt       # Python dependencies
├── data/
│   └── sample_stock.csv  # Sample dataset
├── sql/
│   ├── setup.sql         # Initial setup (tables, views, data)
│   ├── dynamic_tables.sql  # Dynamic Tables for auto-refresh
│   ├── streams_tasks.sql    # Streams & Tasks for automation
│   └── README.md         # SQL setup documentation
└── docs/
    └── README.md         # Detailed documentation
```

## 📈 Key Metrics Calculated

- **avg_daily_issue**: 7-day rolling average of items issued
- **days_of_cover**: `closing_stock / avg_daily_issue`
- **status**: 
  - 🔴 Red: < 2 days
  - 🟠 Orange: 2-5 days
  - 🟢 Green: > 5 days
- **suggested_reorder**: `MAX(0, (5 * avg_daily_issue) - closing_stock)`

## 🔧 Configuration

### Dynamic Tables
- Refresh interval: 1 minute (configurable)
- Auto-updates when source data changes

### Streams & Tasks
- **Stream**: Detects changes in `stock_daily` table
- **Task 1**: Logs changes every minute
- **Task 2**: Checks for critical items every 5 minutes

## 📸 Screenshots

*Add screenshots of:*
- Main dashboard with heatmap
- At-risk items table
- Trend charts
- Export functionality

## 🎥 Demo Video

*Link to demo video showing:*
- App features in action
- Problem statement alignment
- Impact demonstration

## 🤝 Contributing

This is a hackathon submission. For questions or feedback, please open an issue.

## 📝 License

This project is part of the AI for Good Hackathon submission.

## 🙏 Acknowledgments

- YourStory & Snowflake for organizing the hackathon
- Snowflake for providing free trial access
- Streamlit for the dashboard framework

## 📧 Contact

For questions about this project, please reach out via GitHub issues.

---

**Built for AI for Good Hackathon 2025** | **Track: Inventory Heatmap & Stock-Out Alerts**

