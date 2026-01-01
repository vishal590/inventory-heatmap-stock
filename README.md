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

## 🚀 Quick Start

### Prerequisites
- Snowflake account (free trial works)
- Python 3.8+ (for local development)
- Streamlit (for local demo)

### Snowflake Setup

1. **Create Database & Schema**
   ```sql
   USE ROLE ACCOUNTADMIN;
   USE WAREHOUSE COMPUTE_WH;
   CREATE DATABASE IF NOT EXISTS AI_GOOD;
   USE DATABASE AI_GOOD;
   CREATE SCHEMA IF NOT EXISTS PUBLIC;
   USE SCHEMA PUBLIC;
   ```

2. **Run Setup SQL**
   - Open `sql/setup.sql` in Snowsight
   - Run to create tables, views, and seed sample data

3. **Optional: Add Dynamic Tables** (for auto-refresh)
   - Run `sql/dynamic_tables.sql`
   - Converts views to Dynamic Tables

4. **Optional: Add Streams & Tasks** (for automation)
   - Run `sql/streams_tasks.sql`
   - Sets up change detection and scheduled tasks

### Local Development

1. **Clone Repository**
   ```bash
   git clone <your-repo-url>
   cd ai_good
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Streamlit App**
   ```bash
   streamlit run app.py
   ```
   - App runs on `http://localhost:8501`
   - Uses CSV fallback if not connected to Snowflake

### Streamlit in Snowflake

1. Create new Streamlit app in Snowsight
2. Copy contents of `app.py`
3. Set database context: `AI_GOOD.PUBLIC`
4. Ensure warehouse is active
5. Run the app

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

