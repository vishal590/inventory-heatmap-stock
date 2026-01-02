import os
import json
from pathlib import Path
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st


def get_snowflake_session():
    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    except Exception:
        pass
    
    try:
        import streamlit as st
        from snowflake.snowpark import Session
        
        connection_parameters = None
        
        if "snowflake" in st.secrets:
            connection_parameters = {
                "account": st.secrets["snowflake"]["account"],
                "user": st.secrets["snowflake"]["user"],
                "password": st.secrets["snowflake"]["password"],
                "warehouse": st.secrets["snowflake"].get("warehouse", "COMPUTE_WH"),
                "database": st.secrets["snowflake"].get("database", "AI_GOOD"),
                "schema": st.secrets["snowflake"].get("schema", "PUBLIC"),
                "role": st.secrets["snowflake"].get("role", "ACCOUNTADMIN")
            }
        elif "connections" in st.secrets and "snowflake" in st.secrets["connections"]:
            conn = st.secrets["connections"]["snowflake"]
            connection_parameters = {
                "account": conn["account"],
                "user": conn["user"],
                "password": conn["password"],
                "warehouse": conn.get("warehouse", "COMPUTE_WH"),
                "database": conn.get("database", "AI_GOOD"),
                "schema": conn.get("schema", "PUBLIC"),
                "role": conn.get("role", "ACCOUNTADMIN")
            }
        
        if connection_parameters:
            session = Session.builder.configs(connection_parameters).create()
            session.sql("SELECT 1").collect()
            return session
    except Exception as e:
        import streamlit as st
        if hasattr(st, 'session_state') and 'connection_error' not in st.session_state:
            st.session_state.connection_error = str(e)
        pass
    
    try:
        import os
        from snowflake.snowpark import Session
        
        if os.getenv("SNOWFLAKE_ACCOUNT"):
            connection_parameters = {
                "account": os.getenv("SNOWFLAKE_ACCOUNT"),
                "user": os.getenv("SNOWFLAKE_USER"),
                "password": os.getenv("SNOWFLAKE_PASSWORD"),
                "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
                "database": os.getenv("SNOWFLAKE_DATABASE", "AI_GOOD"),
                "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
                "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
            }
            session = Session.builder.configs(connection_parameters).create()
            session.sql("SELECT 1").collect()
            return session
    except Exception:
        pass
    
        return None


def get_snowflake_user(session):
    if not session:
        return 'local_user'
    
    try:
        result = session.sql("SELECT CURRENT_USER() AS user").collect()
        if result and len(result) > 0:
            return result[0]["USER"]
    except Exception:
        pass
    
    try:
        if hasattr(session, 'get_current_user'):
            return session.get_current_user()
    except Exception:
        pass
    
    try:
        result = session.sql("SELECT CURRENT_USER()").collect()
        if result:
            return str(result[0][0])
    except Exception:
        pass
    
    return 'unknown_user'


def log_action(
    session,
    action_type: str,
    location: str = None,
    item: str = None,
    priority: str = None,
    days_of_cover: float = None,
    suggested_reorder: float = None,
    action_details: dict = None,
    user_id: str = None,
    status: str = "PENDING"
):
    if not session:
        return False, "No Snowflake session available"
    
    try:
        test_query = session.sql("SELECT COUNT(*) FROM action_logs LIMIT 1")
        test_query.collect()
    except Exception as e:
        return False, f"action_logs table not accessible: {str(e)}"
    
    try:
        if not user_id:
            user_id = get_snowflake_user(session)
        
        safe_user_id = str(user_id).replace("'", "''")
        safe_action_type = str(action_type).replace("'", "''")
        safe_location = str(location).replace("'", "''") if location else None
        safe_item = str(item).replace("'", "''") if item else None
        safe_priority = str(priority).replace("'", "''") if priority else None
        safe_status = str(status).replace("'", "''")
        
        if action_details:
            details_json = json.dumps(action_details)
            details_json_escaped = details_json.replace("'", "''").replace("\\", "\\\\")
            details_sql = f"PARSE_JSON('{details_json_escaped}')"
        else:
            details_sql = "NULL"
        
        insert_query = f"""
        INSERT INTO action_logs (
            user_id, action_type, location, item, priority,
            days_of_cover, suggested_reorder, action_details, status
        )
        SELECT 
            '{safe_user_id}', '{safe_action_type}',
            {f"'{safe_location}'" if safe_location else "NULL"},
            {f"'{safe_item}'" if safe_item else "NULL"},
            {f"'{safe_priority}'" if safe_priority else "NULL"},
            {days_of_cover if days_of_cover is not None else "NULL"},
            {suggested_reorder if suggested_reorder is not None else "NULL"},
            {details_sql},
            '{safe_status}'
        """
        
        session.sql(insert_query).collect()
        return True, None
    except Exception as e:
        return False, f"Insert failed: {str(e)}"


def load_action_logs(session, limit: int = 100, user_id: str = None):
    if not session:
        return pd.DataFrame()
    
    try:
        df = session.table("action_logs")
        if user_id:
            df = df.filter(df["user_id"] == user_id)
        result_df = df.order_by("action_timestamp", ascending=False).limit(limit).to_pandas()
        if not result_df.empty:
            result_df.columns = result_df.columns.str.lower()
        return result_df
    except Exception:
        try:
            df = session.table("recent_actions_v")
            if user_id:
                df = df.filter(df["user_id"] == user_id)
            result_df = df.to_pandas()
            if not result_df.empty:
                result_df.columns = result_df.columns.str.lower()
            return result_df
        except Exception:
            return pd.DataFrame()


@st.cache_data(ttl=60)
def load_daily_data():
    session = get_snowflake_session()
    if session:
        df = session.table("STOCK_DAILY").to_pandas()
        if not df.empty:
            df.columns = df.columns.str.lower()
        return df
    csv_path = Path("data/sample_stock.csv")
    if csv_path.exists():
        return pd.read_csv(csv_path, parse_dates=["date"])
    return pd.DataFrame()


def estimate_demand_with_snowpark(session, location: str, item: str) -> float:
    if not session:
        return None
    
    try:
        safe_location = location.replace("'", "''")
        safe_item = item.replace("'", "''")
        query = f"""
            WITH historical_data AS (
                SELECT 
                    date,
                    issued,
                    ROW_NUMBER() OVER (ORDER BY date) AS day_num
                FROM stock_daily
                WHERE location = '{safe_location}' AND item = '{safe_item}'
                ORDER BY date DESC
                LIMIT 14
            ),
            trend_analysis AS (
                SELECT 
                    AVG(issued) AS avg_issued,
                    (COUNT(*) * SUM(day_num * issued) - SUM(day_num) * SUM(issued)) / 
                    NULLIF(COUNT(*) * SUM(day_num * day_num) - SUM(day_num) * SUM(day_num), 0) AS trend_slope
                FROM historical_data
            )
            SELECT 
                avg_issued + COALESCE(trend_slope * 7, 0) AS forecasted_daily_demand
            FROM trend_analysis
        """
        result = session.sql(query).collect()
        
        if result and len(result) > 0:
            forecast = result[0][0]
            return float(forecast) if forecast is not None and forecast > 0 else None
    except Exception:
        pass
    return None


def compute_metrics_from_df(df: pd.DataFrame, session=None) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["location", "item", "date"])
    
    df["avg_daily_issue"] = (
        df.groupby(["location", "item"])["issued"]
        .transform(lambda s: s.rolling(7, min_periods=1).mean())
        .round(2)
    )
    
    df["ml_forecasted_demand"] = None
    if session:
        for (loc, itm), group_df in df.groupby(["location", "item"]):
            ml_demand = estimate_demand_with_snowpark(session, loc, itm)
            if ml_demand is not None and ml_demand > 0:
                df.loc[(df["location"] == loc) & (df["item"] == itm), "ml_forecasted_demand"] = round(ml_demand, 2)
        
        df["estimated_daily_demand"] = df["ml_forecasted_demand"].fillna(df["avg_daily_issue"])
    else:
        df["estimated_daily_demand"] = df["avg_daily_issue"]
    df["days_of_cover"] = df["closing_stock"] / df["estimated_daily_demand"].replace(0, pd.NA)
    status_cut = pd.cut(
        df["days_of_cover"],
        bins=[-float("inf"), 2, 5, float("inf")],
        labels=["red", "orange", "green"],
    )
    df["status"] = status_cut.astype(str)
    df.loc[df["days_of_cover"].isna() | (df["status"] == "nan"), "status"] = "unknown"
    df["suggested_reorder"] = (
        (5 * df["estimated_daily_demand"].fillna(0) - df["closing_stock"])
        .clip(lower=0)
        .round(0)
    )
    df["urgency_score"] = df["days_of_cover"] - df["lead_time_days"]
    
    def calculate_priority(row):
        if pd.isna(row["days_of_cover"]) or pd.isna(row["lead_time_days"]):
            return "Unknown"
        if row["days_of_cover"] <= 0:
            return "Critical"
        if row["urgency_score"] <= 0:
            return "High"
        elif row["days_of_cover"] < 2:
            return "High"
        elif row["days_of_cover"] <= row["lead_time_days"] + 1:
            return "High"
        elif row["days_of_cover"] <= 5:
            return "Medium"
        else:
            return "Low"
    
    df["priority"] = df.apply(calculate_priority, axis=1)
    
    df["potential_waste"] = (
        (df["closing_stock"] - (30 * df["estimated_daily_demand"].fillna(0)))
        .clip(lower=0)
        .round(0)
    )
    
    df["optimal_stock"] = (
        (5 + df["lead_time_days"]) * df["estimated_daily_demand"].fillna(0)
    ).round(0)
    
    latest_idx = df.groupby(["location", "item"])["date"].idxmax()
    return df.loc[latest_idx].reset_index(drop=True)


@st.cache_data(ttl=60)
def load_metrics():
    session = get_snowflake_session()
    if session:
        try:
            metrics_df = session.table("INVENTORY_METRICS_DT").to_pandas()
            if not metrics_df.empty:
                metrics_df.columns = metrics_df.columns.str.lower()
                numeric_cols = ["closing_stock", "avg_daily_issue", "days_of_cover", "lead_time_days", "suggested_reorder", "urgency_score", "potential_waste", "optimal_stock"]
                for col in numeric_cols:
                    if col in metrics_df.columns:
                        metrics_df[col] = pd.to_numeric(metrics_df[col], errors="coerce")
                if "ml_forecasted_demand" not in metrics_df.columns:
                    metrics_df["ml_forecasted_demand"] = None
                    for _, row in metrics_df.iterrows():
                        ml_demand = estimate_demand_with_snowpark(session, row["location"], row["item"])
                        if ml_demand is not None and ml_demand > 0:
                            metrics_df.loc[metrics_df.index == row.name, "ml_forecasted_demand"] = round(ml_demand, 2)
                    if "estimated_daily_demand" not in metrics_df.columns:
                        metrics_df["estimated_daily_demand"] = metrics_df["ml_forecasted_demand"].fillna(
                            metrics_df.get("avg_daily_issue", 0)
                        )
            return metrics_df
        except Exception:
            try:
                metrics_df = session.table("INVENTORY_METRICS_V").to_pandas()
                if not metrics_df.empty:
                    metrics_df.columns = metrics_df.columns.str.lower()
                    numeric_cols = ["closing_stock", "avg_daily_issue", "days_of_cover", "lead_time_days", "suggested_reorder", "urgency_score", "potential_waste", "optimal_stock"]
                    for col in numeric_cols:
                        if col in metrics_df.columns:
                            metrics_df[col] = pd.to_numeric(metrics_df[col], errors="coerce")
                    if "ml_forecasted_demand" not in metrics_df.columns:
                        metrics_df["ml_forecasted_demand"] = None
                        for _, row in metrics_df.iterrows():
                            ml_demand = estimate_demand_with_snowpark(session, row["location"], row["item"])
                            if ml_demand is not None and ml_demand > 0:
                                metrics_df.loc[metrics_df.index == row.name, "ml_forecasted_demand"] = round(ml_demand, 2)
                        if "estimated_daily_demand" not in metrics_df.columns:
                            metrics_df["estimated_daily_demand"] = metrics_df["ml_forecasted_demand"].fillna(
                                metrics_df.get("avg_daily_issue", 0)
                            )
                return metrics_df
            except Exception:
                pass
    return compute_metrics_from_df(load_daily_data(), session)


def generate_ai_summary(at_risk_df: pd.DataFrame, session) -> str:
    if at_risk_df.empty:
        return "✅ All items are well-stocked. No immediate action required."
    
    if session:
        try:
            critical_items = at_risk_df[at_risk_df["status"] == "red"]
            warning_items = at_risk_df[at_risk_df["status"] == "orange"]
            
            summary_data = []
            for _, row in at_risk_df.iterrows():
                summary_data.append(
                    f"{row['item']} at {row['location']}: {row['days_of_cover']:.1f} days of cover, "
                    f"suggested reorder: {int(row['suggested_reorder'])} units"
                )
            
            prompt = f"""Analyze this inventory situation and provide a concise, actionable summary for procurement teams:

Critical items (red status):
{chr(10).join([f"- {row['item']} at {row['location']}: Only {row['days_of_cover']:.1f} days left, reorder {int(row['suggested_reorder'])} units" 
               for _, row in critical_items.iterrows()]) if not critical_items.empty else "None"}

Warning items (orange status):
{chr(10).join([f"- {row['item']} at {row['location']}: {row['days_of_cover']:.1f} days left, reorder {int(row['suggested_reorder'])} units" 
               for _, row in warning_items.iterrows()]) if not warning_items.empty else "None"}

Provide a brief, professional summary highlighting priorities and recommended actions."""
            
            escaped_prompt = prompt.replace("'", "''")
            result = session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    'llama2-70b-chat',
                    ARRAY_CONSTRUCT(
                        OBJECT_CONSTRUCT('role', 'user', 'content', '{escaped_prompt}')
                    )
                ) AS summary
            """).collect()
            
            if result and len(result) > 0:
                return result[0]["SUMMARY"]
        except Exception:
            pass
    
    critical_count = len(at_risk_df[at_risk_df["status"] == "red"])
    warning_count = len(at_risk_df[at_risk_df["status"] == "orange"])
    
    summary_parts = []
    if critical_count > 0:
        summary_parts.append(f"🚨 **{critical_count} critical item(s)** require immediate attention")
        for _, row in at_risk_df[at_risk_df["status"] == "red"].iterrows():
            summary_parts.append(
                f"- **{row['item']}** at {row['location']}: Only {row['days_of_cover']:.1f} days remaining. "
                f"Recommended reorder: **{int(row['suggested_reorder'])} units**"
            )
    
    if warning_count > 0:
        summary_parts.append(f"\n⚠️ **{warning_count} item(s)** need attention soon")
        for _, row in at_risk_df[at_risk_df["status"] == "orange"].head(3).iterrows():
            summary_parts.append(
                f"- **{row['item']}** at {row['location']}: {row['days_of_cover']:.1f} days remaining. "
                f"Recommended reorder: **{int(row['suggested_reorder'])} units**"
            )
    
    return "\n".join(summary_parts) if summary_parts else "✅ All items are well-stocked."


def build_heatmap(df: pd.DataFrame):
    if df.empty:
        return None
    status_scale = alt.Scale(
        domain=["red", "orange", "green", "unknown"],
        range=["#d73027", "#fc8d59", "#1a9850", "#bdbdbd"],
    )
    
    tooltip_list = [
        "location",
        "item",
        alt.Tooltip("closing_stock:Q", title="Closing"),
        alt.Tooltip("days_of_cover:Q", title="Days of cover"),
        alt.Tooltip("suggested_reorder:Q", title="Suggested reorder"),
    ]
    
    if "ml_forecasted_demand" in df.columns:
        tooltip_list.append(alt.Tooltip("ml_forecasted_demand:Q", title="ML Forecast (AI)"))
    if "estimated_daily_demand" in df.columns:
        tooltip_list.append(alt.Tooltip("estimated_daily_demand:Q", title="Est. Demand"))
    elif "avg_daily_issue" in df.columns:
        tooltip_list.append(alt.Tooltip("avg_daily_issue:Q", title="Avg daily issue"))
    
    chart = (
        alt.Chart(df)
        .mark_rect()
        .encode(
            x=alt.X("item:N", title="Item"),
            y=alt.Y("location:N", title="Location"),
            color=alt.Color("status:N", scale=status_scale, title="Status"),
            tooltip=tooltip_list,
        )
    )
    return chart


def main():
    st.set_page_config(page_title="Inventory Heatmap & Stock-Out Alerts", layout="wide")
    st.title("Inventory Heatmap & Stock-Out Alerts")
    
    session = get_snowflake_session()
    if session:
        try:
            session.table("INVENTORY_METRICS_DT").to_pandas()
            st.caption("Snowflake + Streamlit (Dynamic Tables enabled - auto-refreshing)")
        except Exception:
            st.caption("Snowflake + Streamlit (connected - using views/tables)")
    else:
        st.caption("Snowflake + Streamlit prototype (running locally with sample data)")
        if hasattr(st, 'session_state') and 'connection_error' in st.session_state:
            with st.expander("🔍 Connection Debug Info", expanded=False):
                st.error(f"**Connection Error:** {st.session_state.connection_error}")
                st.info("**Common fixes:**\n1. Account might need region: Try `'getyhji.us-east-1'` instead of `'getyhji'`\n2. Verify credentials in `.streamlit/secrets.toml`\n3. Ensure warehouse is running: `ALTER WAREHOUSE COMPUTE_WH RESUME;`\n4. Check database exists: `USE DATABASE AI_GOOD;`")

    col_refresh1, col_refresh2, col_refresh3 = st.columns([1, 1, 10])
    with col_refresh1:
        if st.button("🔄 Refresh Data", help="Clear cache and reload data from Snowflake", type="secondary"):
            st.cache_data.clear()
            st.rerun()
    with col_refresh2:
        if session:
            st.caption("🟢 Live data")
        else:
            st.caption("⚪ Static data")

    daily_df = load_daily_data()
    metrics_df = load_metrics()

    if metrics_df.empty:
        st.error("No data found. Load sample CSV or connect to Snowflake and rerun.")
        return

    locations = sorted(metrics_df["location"].unique())
    items = sorted(metrics_df["item"].unique())
    
    if session:
        current_user = get_snowflake_user(session)
        st.sidebar.info(f"👤 **Logged in as**: {current_user}")
        st.sidebar.caption("Using Snowflake session authentication")
    else:
        st.sidebar.info("👤 **Mode**: Local (no authentication)")
        st.sidebar.caption("Connect to Snowflake for user tracking")
    
    with st.expander("➕ Add New Stock Data", expanded=False):
        tab1, tab2 = st.tabs(["📝 Manual Entry", "📤 Upload CSV"])
        
        with tab1:
            st.markdown("**Enter daily stock data for a location and item:**")
            
            input_col1, input_col2 = st.columns(2)
            with input_col1:
                input_date = st.date_input("Date", value=pd.Timestamp.now().date(), key="input_date")
                input_location = st.selectbox("Location", locations, key="input_location")
                input_item = st.selectbox("Item", items, key="input_item")
                input_lead_time = st.number_input("Lead Time (days)", min_value=0, value=5, step=1, key="input_lead_time")
            
            with input_col2:
                input_opening = st.number_input("Opening Stock", min_value=0, value=0, step=1, key="input_opening")
                input_received = st.number_input("Received", min_value=0, value=0, step=1, key="input_received")
                input_issued = st.number_input("Issued", min_value=0, value=0, step=1, key="input_issued")
                input_closing = st.number_input("Closing Stock", min_value=0, value=0, step=1, key="input_closing")
            
            if st.button("💾 Save Stock Data", type="primary", key="save_manual"):
                session = get_snowflake_session()
                if session:
                    try:
                        current_user = get_snowflake_user(session)
                        safe_location = input_location.replace("'", "''")
                        safe_item = input_item.replace("'", "''")
                        insert_query = f"""
                        INSERT INTO stock_daily (date, location, item, opening_stock, received, issued, closing_stock, lead_time_days)
                        VALUES ('{input_date}', '{safe_location}', '{safe_item}', {input_opening}, {input_received}, {input_issued}, {input_closing}, {input_lead_time})
                        """
                        session.sql(insert_query).collect()
                        
                        success, error = log_action(
                            session,
                            action_type="CREATE_PO",
                            location=input_location,
                            item=input_item,
                            action_details={
                                "source": "manual_input",
                                "date": str(input_date),
                                "opening_stock": int(input_opening),
                                "received": int(input_received),
                                "issued": int(input_issued),
                                "closing_stock": int(input_closing),
                                "entered_by": current_user
                            },
                            status="COMPLETED"
                        )
                        
                        st.success(f"✅ Stock data saved successfully for {input_item} at {input_location} on {input_date}!")
                        st.caption(f"📝 Saved by: {current_user}")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to save data: {str(e)}")
                else:
                    st.warning("⚠️ Cannot save data: Not connected to Snowflake. Connect to Snowflake to add new stock data.")
                    st.info("💡 **Alternative**: Update `data/sample_stock.csv` manually or connect to Snowflake to use the input form.")
        
        with tab2:
            st.markdown("**Upload CSV file with stock data:**")
            st.caption("CSV should have columns: date, location, item, opening_stock, received, issued, closing_stock, lead_time_days")
            
            uploaded_file = st.file_uploader("Choose CSV file", type="csv", key="upload_csv")
            if uploaded_file is not None:
                try:
                    upload_df = pd.read_csv(uploaded_file, parse_dates=["date"])
                    
                    required_cols = ["date", "location", "item", "opening_stock", "received", "issued", "closing_stock", "lead_time_days"]
                    if all(col in upload_df.columns for col in required_cols):
                        st.dataframe(upload_df.head(10), use_container_width=True)
                        st.caption(f"Preview: {len(upload_df)} rows ready to upload")
                        
                        if st.button("💾 Upload to Snowflake", type="primary", key="upload_btn"):
                            session = get_snowflake_session()
                            if session:
                                try:
                                    current_user = get_snowflake_user(session)
                                    for _, row in upload_df.iterrows():
                                        safe_location = str(row["location"]).replace("'", "''")
                                        safe_item = str(row["item"]).replace("'", "''")
                                        insert_query = f"""
                                        INSERT INTO stock_daily (date, location, item, opening_stock, received, issued, closing_stock, lead_time_days)
                                        VALUES ('{row["date"]}', '{safe_location}', '{safe_item}', {row["opening_stock"]}, {row["received"]}, {row["issued"]}, {row["closing_stock"]}, {row["lead_time_days"]})
                                        """
                                        session.sql(insert_query).collect()
                                    
                                    success, error = log_action(
                                        session,
                                        action_type="CREATE_PO",
                                        action_details={
                                            "source": "csv_upload",
                                            "rows_uploaded": len(upload_df),
                                            "uploaded_by": current_user,
                                            "file_name": uploaded_file.name if hasattr(uploaded_file, 'name') else "uploaded_file.csv"
                                        },
                                        status="COMPLETED"
                                    )
                                    
                                    st.success(f"✅ Successfully uploaded {len(upload_df)} rows to Snowflake!")
                                    st.caption(f"📝 Uploaded by: {current_user}")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Failed to upload data: {str(e)}")
                            else:
                                st.warning("⚠️ Cannot upload: Not connected to Snowflake. Connect to Snowflake to upload CSV data.")
                    else:
                        missing_cols = [col for col in required_cols if col not in upload_df.columns]
                        st.error(f"❌ CSV missing required columns: {', '.join(missing_cols)}")
                except Exception as e:
                        st.error(f"❌ Error reading CSV file: {str(e)}")

    st.subheader("📊 Overall Inventory Health")
    total_items = len(metrics_df)
    at_risk_count = len(metrics_df[
        (metrics_df["days_of_cover"].isna()) | (metrics_df["days_of_cover"] <= 5)
    ])
    critical_count = len(metrics_df[
        (metrics_df["days_of_cover"].notna()) & (metrics_df["days_of_cover"] < 2)
    ])
    healthy_count = total_items - at_risk_count
    health_percentage = (healthy_count / total_items * 100) if total_items > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Items", total_items, help="Total location-item combinations")
    with col2:
        st.metric("At-Risk Items", at_risk_count, 
                 delta=f"-{at_risk_count}" if at_risk_count > 0 else None,
                 delta_color="inverse",
                 help="Items with ≤5 days of cover")
    with col3:
        st.metric("Critical Items", critical_count,
                 delta=f"-{critical_count}" if critical_count > 0 else None,
                 delta_color="inverse",
                 help="Items with <2 days of cover")
    with col4:
        st.metric("Health Score", f"{health_percentage:.1f}%",
                 delta=f"{health_percentage:.1f}% healthy" if health_percentage >= 80 else None,
                 delta_color="normal" if health_percentage >= 80 else "off",
                 help="Percentage of items with adequate stock")
    
    st.subheader("🤖 AI-Powered Demand Forecast (Snowpark ML)")
    st.caption("Machine learning-based demand estimation using Snowpark. Uses linear regression on historical data to predict future demand.")
    
    session = get_snowflake_session()
    
    if not session:
        st.warning(
            "**Snowpark ML Not Available**: This feature requires a Snowflake connection.\n\n"
            "**To enable ML demand forecasting**:\n"
            "- Connect to Snowflake (run in Snowflake Streamlit or configure local connection)\n"
            "- ML forecasts use linear regression on historical data\n"
            "- Analyzes trends in the last 14 days to predict future demand\n"
            "- Currently using simple rolling average for demand estimation"
        )
    elif metrics_df.empty:
        st.info("No data available for ML demand forecasting.")
    else:
        ml_items = metrics_df[metrics_df["ml_forecasted_demand"].notna() & (metrics_df["ml_forecasted_demand"] > 0)]
        
        if not ml_items.empty:
            forecast_comparison = ml_items[["location", "item", "avg_daily_issue", "ml_forecasted_demand", "estimated_daily_demand"]].copy()
            forecast_comparison["avg_daily_issue"] = pd.to_numeric(forecast_comparison["avg_daily_issue"], errors="coerce").fillna(0)
            forecast_comparison["ml_forecasted_demand"] = pd.to_numeric(forecast_comparison["ml_forecasted_demand"], errors="coerce").fillna(0)
            forecast_comparison["estimated_daily_demand"] = pd.to_numeric(forecast_comparison["estimated_daily_demand"], errors="coerce").fillna(0)
            forecast_comparison["forecast_change"] = (
                ((forecast_comparison["ml_forecasted_demand"] - forecast_comparison["avg_daily_issue"]) / 
                 forecast_comparison["avg_daily_issue"].replace(0, pd.NA) * 100).round(1)
            )
            forecast_comparison.columns = ["Location", "Item", "Simple Avg", "ML Forecast", "Used Demand", "Change %"]
            
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(
                    forecast_comparison[["Location", "Item", "Simple Avg", "ML Forecast", "Change %"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Simple Avg": st.column_config.NumberColumn("Simple Avg (units/day)", format="%.2f"),
                        "ML Forecast": st.column_config.NumberColumn("ML Forecast (units/day)", format="%.2f"),
                        "Change %": st.column_config.NumberColumn("Change %", format="%.1f"),
                    }
                )
            with col2:
                st.success(
                    f"✅ **ML Forecast Active**: {len(ml_items)} items using AI-powered demand estimation.\n\n"
                    f"**How it works**:\n"
                    f"- Analyzes last 14 days of historical data\n"
                    f"- Uses linear regression to detect trends\n"
                    f"- Forecasts demand 7 days ahead with trend adjustment\n"
                    f"- More accurate than simple rolling average"
                )
        else:
            st.info(
                "**Snowpark ML Available**: ML-based demand forecasting is enabled.\n\n"
                "**Status**: ML forecasts will appear here once sufficient historical data is available for trend analysis.\n"
                "**Current method**: Using simple rolling average for demand estimation.\n\n"
                "**Requirements for ML forecast**:\n"
                "- At least 14 days of historical data per item/location\n"
                "- Data must show consumption patterns (issued quantities)\n"
                "- Trend analysis will automatically activate when data is sufficient"
            )
    
    if len(locations) > 1:
        st.subheader("📍 Location Health Summary")
        location_summary = metrics_df.groupby("location").agg({
            "days_of_cover": lambda x: len(x[(x.isna()) | (x <= 5)]),
            "status": lambda x: (x == "red").sum()
        }).reset_index()
        location_summary.columns = ["Location", "At-Risk Count", "Critical Count"]
        location_summary = location_summary.sort_values("Critical Count", ascending=False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(location_summary, use_container_width=True, hide_index=True)
        with col2:
            if not location_summary.empty:
                loc_chart = alt.Chart(location_summary).mark_bar().encode(
                    x=alt.X("Location:N", title="Location"),
                    y=alt.Y("At-Risk Count:Q", title="At-Risk Items"),
                    color=alt.Color("Critical Count:Q", scale=alt.Scale(scheme="reds"), title="Critical"),
                    tooltip=["Location", "At-Risk Count", "Critical Count"]
                )
                st.altair_chart(loc_chart, use_container_width=True)
    
    if len(items) > 1:
        st.subheader("📦 Item Health Summary")
        item_summary = metrics_df.groupby("item").agg({
            "days_of_cover": lambda x: len(x[(x.isna()) | (x <= 5)]),
            "status": lambda x: (x == "red").sum(),
            "suggested_reorder": "sum"
        }).reset_index()
        item_summary.columns = ["Item", "At-Risk Locations", "Critical Locations", "Total Reorder Needed"]
        item_summary = item_summary.sort_values("Critical Locations", ascending=False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(item_summary, use_container_width=True, hide_index=True)
        with col2:
            if not item_summary.empty:
                item_chart = alt.Chart(item_summary).mark_bar().encode(
                    x=alt.X("Item:N", title="Item"),
                    y=alt.Y("Critical Locations:Q", title="Critical Locations"),
                    color=alt.Color("Total Reorder Needed:Q", scale=alt.Scale(scheme="oranges"), title="Reorder Qty"),
                    tooltip=["Item", "At-Risk Locations", "Critical Locations", "Total Reorder Needed"]
                )
                st.altair_chart(item_chart, use_container_width=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        selected_locations = st.multiselect(
            "Locations", options=locations, default=locations
        )
    with col2:
        selected_items = st.multiselect("Items", options=items, default=items)
    with col3:
        risk_days = st.slider("At-risk threshold (days of cover)", 0.0, 10.0, 5.0, 0.5)

    filtered = metrics_df[
        metrics_df["location"].isin(selected_locations)
        & metrics_df["item"].isin(selected_items)
    ]
    
    quick_at_risk = filtered[
        (filtered["days_of_cover"].isna()) | (filtered["days_of_cover"] <= 2)
    ].copy()
    
    if not quick_at_risk.empty:
        st.subheader("⚡ Quick Actions Required")
        if "priority" not in quick_at_risk.columns:
            def calc_priority(row):
                days = row.get("days_of_cover", 0) if not pd.isna(row.get("days_of_cover")) else 0
                lead = row.get("lead_time_days", 0) if not pd.isna(row.get("lead_time_days")) else 0
                if pd.isna(row.get("days_of_cover")) or pd.isna(row.get("lead_time_days")):
                    return "Unknown"
                if days <= 0:
                    return "Critical"
                if (days - lead) <= 0:
                    return "High"
                return "High" if days < 2 else "Medium"
            quick_at_risk["priority"] = quick_at_risk.apply(calc_priority, axis=1)
        
        priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Unknown": 4}
        quick_at_risk["priority_order"] = quick_at_risk["priority"].map(priority_order).fillna(4)
        quick_at_risk = quick_at_risk.sort_values(["priority_order", "days_of_cover"]).head(5)
        
        for idx, row in quick_at_risk.iterrows():
            priority_icon = "🔴" if row.get("priority") == "Critical" else "🟠"
            st.info(
                f"{priority_icon} **{row['item']}** at **{row['location']}**: "
                f"Only {row.get('days_of_cover', 0):.1f} days remaining. "
                f"Reorder **{int(row.get('suggested_reorder', 0))} units** immediately."
            )

    heatmap = build_heatmap(filtered)
    if heatmap:
        st.subheader("Stock Health Heatmap")
        st.altair_chart(heatmap, use_container_width=True)

    at_risk = filtered[
        (filtered["days_of_cover"].isna()) | (filtered["days_of_cover"] <= risk_days)
    ].copy()
    
    if "priority" not in at_risk.columns:
        def calculate_priority(row):
            days_cover = row.get("days_of_cover", 0) if not pd.isna(row.get("days_of_cover")) else 0
            lead_time = row.get("lead_time_days", 0) if not pd.isna(row.get("lead_time_days")) else 0
            if pd.isna(row.get("days_of_cover")) or pd.isna(row.get("lead_time_days")):
                return "Unknown"
            urgency = days_cover - lead_time
            if days_cover <= 0:
                return "Critical"
            if urgency <= 0:
                return "High"
            elif days_cover < 2:
                return "High"
            elif days_cover <= lead_time + 1:
                return "High"
            elif days_cover <= 5:
                return "Medium"
            else:
                return "Low"
        at_risk["priority"] = at_risk.apply(calculate_priority, axis=1)
    
    if "urgency_score" not in at_risk.columns:
        at_risk["urgency_score"] = (
            at_risk["days_of_cover"].fillna(0) - at_risk["lead_time_days"].fillna(0)
        )
    
    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Unknown": 4}
    at_risk["priority_order"] = at_risk["priority"].map(priority_order).fillna(4)
    at_risk = at_risk.sort_values(["priority_order", "days_of_cover", "location", "item"]).drop(columns=["priority_order"])

    st.subheader("At-Risk Items (Prioritized)")
    
    if not at_risk.empty:
        priority_counts = at_risk["priority"].value_counts()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            critical = priority_counts.get("Critical", 0)
            st.metric("🔴 Critical", critical, delta=None)
        with col2:
            high = priority_counts.get("High", 0)
            st.metric("🟠 High Priority", high, delta=None)
        with col3:
            medium = priority_counts.get("Medium", 0)
            st.metric("🟡 Medium Priority", medium, delta=None)
        with col4:
            low = priority_counts.get("Low", 0)
            st.metric("🟢 Low Priority", low, delta=None)
    
    display_cols = ["priority", "location", "item", "days_of_cover", "lead_time_days", 
                    "urgency_score", "closing_stock", "suggested_reorder"]
    if "ml_forecasted_demand" in at_risk.columns:
        display_cols.append("ml_forecasted_demand")
    if "estimated_daily_demand" in at_risk.columns:
        display_cols.append("estimated_daily_demand")
    elif "avg_daily_issue" in at_risk.columns:
        display_cols.append("avg_daily_issue")
    display_cols = [col for col in display_cols if col in at_risk.columns]
    other_cols = [col for col in at_risk.columns if col not in display_cols]
    display_df = at_risk[display_cols + other_cols] if other_cols else at_risk[display_cols]
    
    column_config_dict = {
        "priority": st.column_config.TextColumn("Priority", width="small"),
        "days_of_cover": st.column_config.NumberColumn("Days Left", format="%.1f"),
        "lead_time_days": st.column_config.NumberColumn("Lead Time", format="%.0f"),
        "urgency_score": st.column_config.NumberColumn("Urgency Score", format="%.1f", 
            help="Days of cover minus lead time. Negative = critical"),
        "suggested_reorder": st.column_config.NumberColumn("Reorder Qty", format="%.0f"),
    }
    
    if "ml_forecasted_demand" in display_df.columns:
        column_config_dict["ml_forecasted_demand"] = st.column_config.NumberColumn(
            "ML Forecast", format="%.2f", help="AI-powered demand forecast (Snowpark ML)"
        )
    if "estimated_daily_demand" in display_df.columns:
        column_config_dict["estimated_daily_demand"] = st.column_config.NumberColumn(
            "Est. Demand", format="%.2f", help="Used demand (ML forecast if available, else simple avg)"
        )
    elif "avg_daily_issue" in display_df.columns:
        column_config_dict["avg_daily_issue"] = st.column_config.NumberColumn("Avg Daily Issue", format="%.2f")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=        column_config_dict,
    )
    if not filtered.empty and "potential_waste" in filtered.columns:
        total_waste = filtered["potential_waste"].sum()
        overstocked_items = len(filtered[filtered["potential_waste"] > 0])
        if total_waste > 0 or overstocked_items > 0:
            st.subheader("📊 Waste Reduction Insights")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Potential Waste (Units)", f"{int(total_waste):,}", 
                         help="Items with more than 30 days of stock")
            with col2:
                st.metric("Overstocked Items", overstocked_items,
                         help="Items that exceed optimal stock levels")
            
            if overstocked_items > 0:
                waste_df = filtered[filtered["potential_waste"] > 0].sort_values("potential_waste", ascending=False)
                with st.expander("View Overstocked Items"):
                    st.dataframe(
                        waste_df[["location", "item", "closing_stock", "optimal_stock", "potential_waste"]],
                        use_container_width=True,
                        hide_index=True,
                    )
    
    if not at_risk.empty:
        st.subheader("📋 Recommended Purchase Orders")
        st.caption("Consolidated purchase orders for procurement teams based on priority and location")
        
        po_recommendations = at_risk.groupby(["item", "location"]).agg({
            "suggested_reorder": "sum",
            "priority": lambda x: "High" if "Critical" in x.values or "High" in x.values else x.iloc[0],
            "days_of_cover": "min",
            "lead_time_days": "first"
        }).reset_index()
        po_recommendations = po_recommendations[po_recommendations["suggested_reorder"] > 0]
        po_recommendations = po_recommendations.sort_values(["priority", "days_of_cover"])
        
        if not po_recommendations.empty:
            priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Unknown": 4}
            po_recommendations["priority_order"] = po_recommendations["priority"].map(priority_order).fillna(4)
            po_recommendations = po_recommendations.sort_values(["priority_order", "days_of_cover"]).drop(columns=["priority_order"])
            
            st.dataframe(
                po_recommendations[["priority", "item", "location", "suggested_reorder", "days_of_cover", "lead_time_days"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "priority": st.column_config.TextColumn("Priority", width="small"),
                    "item": st.column_config.TextColumn("Item"),
                    "location": st.column_config.TextColumn("Location"),
                    "suggested_reorder": st.column_config.NumberColumn("Qty to Order", format="%.0f"),
                    "days_of_cover": st.column_config.NumberColumn("Days Left", format="%.1f"),
                    "lead_time_days": st.column_config.NumberColumn("Lead Time", format="%.0f"),
                },
            )
            
            po_export = po_recommendations[["priority", "item", "location", "suggested_reorder", "lead_time_days"]].to_csv(index=False).encode("utf-8")
            if st.download_button(
                "📥 Export Purchase Order Recommendations", 
                data=po_export, 
                file_name="purchase_orders.csv", 
                mime="text/csv",
                help="Download recommended purchase orders for procurement team"
            ):
                session = get_snowflake_session()
                if session:
                    for _, row in po_recommendations.iterrows():
                        success, error = log_action(
                            session,
                            action_type="EXPORT_CSV",
                            location=row.get("location"),
                            item=row.get("item"),
                            priority=row.get("priority"),
                            suggested_reorder=row.get("suggested_reorder"),
                            action_details={"export_type": "purchase_orders", "total_pos": len(po_recommendations)},
                            status="COMPLETED"
                        )
        else:
            st.info("No purchase orders needed at this time.")
    
    csv_export = at_risk.to_csv(index=False).encode("utf-8")
    if st.download_button(
        "📥 Export Priority List CSV", data=csv_export, file_name="at_risk_priority.csv", mime="text/csv"
    ):
        session = get_snowflake_session()
        if session and not at_risk.empty:
            for _, row in at_risk.head(10).iterrows():
                success, error = log_action(
                    session,
                    action_type="EXPORT_CSV",
                    location=row.get("location"),
                    item=row.get("item"),
                    priority=row.get("priority"),
                    days_of_cover=row.get("days_of_cover"),
                    suggested_reorder=row.get("suggested_reorder"),
                    action_details={"export_type": "priority_list", "total_items": len(at_risk)},
                    status="COMPLETED"
                )

    st.subheader("🤖 AI-Powered Summary")
    session = get_snowflake_session()
    with st.spinner("Generating insights..."):
        ai_summary = generate_ai_summary(at_risk, session)
    st.markdown(ai_summary)
    if session:
        st.caption("✨ Powered by Snowflake Cortex AI")
    else:
        st.caption("💡 Connect to Snowflake to enable AI-powered summaries with Cortex")

    st.subheader("📈 Trends & Historical Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        trend_item = st.selectbox("Select item", items)
    with col2:
        trend_location = st.selectbox("Select location", locations)
    
    trend_df = daily_df[
        (daily_df["item"] == trend_item) & (daily_df["location"] == trend_location)
    ].sort_values("date")
    
    if trend_df.empty:
        st.info("No trend data for this selection.")
    else:
        if len(trend_df) >= 2:
            latest_stock = trend_df.iloc[-1]["closing_stock"]
            previous_stock = trend_df.iloc[-2]["closing_stock"]
            stock_change = latest_stock - previous_stock
            change_pct = (stock_change / previous_stock * 100) if previous_stock > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Stock", int(latest_stock))
            with col2:
                st.metric("Previous Stock", int(previous_stock))
            with col3:
                st.metric("Change", f"{int(stock_change):+}", 
                         delta=f"{change_pct:+.1f}%",
                         delta_color="normal" if stock_change >= 0 else "inverse")
        
        trend_chart = (
            alt.Chart(trend_df)
            .mark_line(point=True, strokeWidth=2)
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("closing_stock:Q", title="Stock Level"),
                color=alt.value("#1f77b4"),
                tooltip=["date:T", "closing_stock:Q", "issued:Q", "received:Q", "opening_stock:Q"],
            )
        )
        
        received_chart = (
            alt.Chart(trend_df)
            .mark_bar(color="#2ca02c", opacity=0.6)
            .encode(
                x=alt.X("date:T"),
                y=alt.Y("received:Q", title="Quantity"),
            )
        )
        
        issued_chart = (
            alt.Chart(trend_df)
            .mark_bar(color="#d62728", opacity=0.6)
            .encode(
                x=alt.X("date:T"),
                y=alt.Y("issued:Q", title="Quantity"),
            )
        )
        
        combined_chart = alt.layer(trend_chart, received_chart, issued_chart).resolve_scale(
            y='independent'
        )
        st.altair_chart(combined_chart, use_container_width=True)
        
        if len(trend_df) >= 3:
            recent_avg = trend_df.tail(3)["closing_stock"].mean()
            earlier_avg = trend_df.head(3)["closing_stock"].mean()
            trend_direction = "📈 Improving" if recent_avg > earlier_avg else "📉 Declining"
            st.caption(f"Trend: {trend_direction} | Recent average: {recent_avg:.1f} | Earlier average: {earlier_avg:.1f}")

    session = get_snowflake_session()
    
    unistore_available = False
    if session:
        try:
            test_query = session.sql("SELECT COUNT(*) FROM action_logs LIMIT 1")
            test_query.collect()
            unistore_available = True
        except Exception:
            unistore_available = False
    
    if session and unistore_available:
        st.subheader("📋 Action Logs (Unistore)")
        st.caption("Track actions taken on inventory recommendations. Powered by Snowflake Unistore hybrid tables.")
        
        tab1, tab2, tab3 = st.tabs(["Recent Actions", "Action Summary", "Log New Action"])
        
        with tab1:
            current_user = get_snowflake_user(session)
            show_all_users = st.checkbox("Show all users' actions", value=True, help="Uncheck to see only your actions")
            
            filter_user = None if show_all_users else current_user
            action_logs_df = load_action_logs(session, limit=50, user_id=filter_user)
            
            if not action_logs_df.empty:
                display_logs = action_logs_df.copy()
                if "action_details" in display_logs.columns:
                    display_logs["action_details"] = display_logs["action_details"].apply(
                        lambda x: json.dumps(x) if isinstance(x, dict) else str(x) if x else ""
                    )
                
                columns_to_hide = ["action_id"]
                if show_all_users and "user_id" in display_logs.columns:
                    pass
                elif not show_all_users:
                    columns_to_hide.append("user_id")
                
                display_columns = [col for col in display_logs.columns if col not in columns_to_hide]
                display_logs = display_logs[display_columns]
                
                column_config = {
                    "action_timestamp": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss"),
                    "action_type": st.column_config.TextColumn("Action Type"),
                    "location": st.column_config.TextColumn("Location"),
                    "item": st.column_config.TextColumn("Item"),
                    "priority": st.column_config.TextColumn("Priority"),
                    "status": st.column_config.TextColumn("Status"),
                }
                
                if "user_id" in display_columns:
                    column_config["user_id"] = st.column_config.TextColumn("User", width="small")
                
                st.dataframe(
                    display_logs,
                    use_container_width=True,
                    hide_index=True,
                    column_config=column_config
                )
            else:
                if show_all_users:
                    st.info("No action logs found. Actions will be logged here when you interact with recommendations.")
                else:
                    st.info(f"No action logs found for user '{current_user}'. Actions will be logged here when you interact with recommendations.")
        
        with tab2:
            try:
                summary_df = session.table("action_summary_v").to_pandas()
                if not summary_df.empty:
                    summary_df.columns = summary_df.columns.str.lower()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.dataframe(summary_df, use_container_width=True, hide_index=True)
                    with col2:
                        total_actions = summary_df["action_count"].sum()
                        st.metric("Total Actions", total_actions)
                        st.metric("Action Types", len(summary_df))
                else:
                    st.info("No action summary available yet.")
            except Exception:
                st.info("Action summary view not available. Run sql/unistore_action_logs.sql to create it.")
        
        with tab3:
            st.markdown("**Manually log an action:**")
            col1, col2 = st.columns(2)
            with col1:
                manual_action_type = st.selectbox(
                    "Action Type",
                    ["EXPORT_CSV", "VIEW_DETAILS", "ACKNOWLEDGE_ALERT", "CREATE_PO", "DISMISS_ALERT"],
                    key="manual_action_type"
                )
                manual_location = st.selectbox("Location", locations, key="manual_location")
                manual_item = st.selectbox("Item", items, key="manual_item")
            with col2:
                manual_status = st.selectbox("Status", ["PENDING", "COMPLETED", "CANCELLED"], key="manual_status")
                manual_priority = st.selectbox(
                    "Priority",
                    ["Critical", "High", "Medium", "Low", "Unknown"],
                    key="manual_priority"
                )
            
            if st.button("📝 Log Action", type="primary"):
                item_row = metrics_df[
                    (metrics_df["location"] == manual_location) & (metrics_df["item"] == manual_item)
                ]
                if not item_row.empty:
                    row = item_row.iloc[0]
                    success, error = log_action(
                        session,
                        action_type=manual_action_type,
                        location=manual_location,
                        item=manual_item,
                        priority=manual_priority,
                        days_of_cover=row.get("days_of_cover"),
                        suggested_reorder=row.get("suggested_reorder"),
                        action_details={"source": "manual_log", "notes": "Manually logged action"},
                        status=manual_status
                    )
                    if success:
                        st.success(f"✅ Action logged successfully!")
                        st.cache_data.clear()
                    else:
                        st.error(f"❌ Failed to log action: {error if error else 'Unknown error'}")
                else:
                    st.warning("Item not found in metrics.")
    elif session and not unistore_available:
        st.subheader("📋 Action Logs (Unistore)")
        st.warning(
            "**Unistore Action Logging**: Snowflake connection detected, but Unistore table not found.\n\n"
            "**To enable action logging**:\n"
            "1. Open `sql/unistore_action_logs.sql` from the repository\n"
            "2. Copy and run the SQL script in Snowsight\n"
            "3. This will create the `action_logs` hybrid table and related views\n"
            "4. Refresh this page - actions will then be automatically logged\n\n"
            "**What you'll get**:\n"
            "- ✅ Track CSV exports (priority lists and purchase orders)\n"
            "- ✅ Log when alerts are acknowledged\n"
            "- ✅ Record purchase order creation\n"
            "- ✅ View action history and summaries\n"
            "- ✅ Manual action logging interface"
        )
    else:
        st.subheader("📋 Action Logs (Unistore)")
        st.info(
            "**Unistore Action Logging**: This feature requires a Snowflake connection.\n\n"
            "**To enable**:\n"
            "1. Connect to Snowflake (run in Snowflake Streamlit or configure local connection)\n"
            "2. Run `sql/unistore_action_logs.sql` in Snowsight to create the hybrid table\n"
            "3. Actions will be automatically logged when you interact with recommendations\n\n"
            "**Features**:\n"
            "- Track CSV exports\n"
            "- Log when alerts are acknowledged\n"
            "- Record purchase order creation\n"
            "- View action history and summaries\n"
            "- Manual action logging interface"
        )
    
    st.subheader("🔗 Data Integration Status")
    st.caption("This dashboard integrates data from multiple systems into a unified view:")
    
    session = get_snowflake_session()
    data_source = "Local CSV"
    data_source_details = "Using sample_stock.csv"
    if session:
        try:
            try:
                session.table("INVENTORY_METRICS_DT").to_pandas()
                data_source = "Snowflake Dynamic Table"
                data_source_details = "INVENTORY_METRICS_DT (auto-refreshes every 1 minute)"
            except Exception:
                try:
                    session.table("INVENTORY_METRICS_V").to_pandas()
                    data_source = "Snowflake View"
                    data_source_details = "INVENTORY_METRICS_V (refreshes on query)"
                except Exception:
                    data_source = "Snowflake (Direct)"
                    data_source_details = "Direct table access"
        except Exception:
            pass
    
    total_issued = daily_df["issued"].sum() if not daily_df.empty and "issued" in daily_df.columns else 0
    total_received = daily_df["received"].sum() if not daily_df.empty and "received" in daily_df.columns else 0
    total_opening = daily_df["opening_stock"].sum() if not daily_df.empty and "opening_stock" in daily_df.columns else 0
    total_closing = daily_df["closing_stock"].sum() if not daily_df.empty and "closing_stock" in daily_df.columns else 0
    unique_dates = daily_df["date"].nunique() if not daily_df.empty and "date" in daily_df.columns else 0
    date_range = ""
    if not daily_df.empty and "date" in daily_df.columns:
        min_date = daily_df["date"].min()
        max_date = daily_df["date"].max()
        date_range = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
    
    avg_consumption = metrics_df["avg_daily_issue"].mean() if not metrics_df.empty and "avg_daily_issue" in metrics_df.columns else 0
    total_lead_time = metrics_df["lead_time_days"].sum() if not metrics_df.empty and "lead_time_days" in metrics_df.columns else 0
    avg_lead_time = total_lead_time / len(metrics_df) if len(metrics_df) > 0 and total_lead_time > 0 else 0
    
    unique_locations = len(metrics_df["location"].unique()) if not metrics_df.empty and "location" in metrics_df.columns else 0
    unique_items = len(metrics_df["item"].unique()) if not metrics_df.empty and "item" in metrics_df.columns else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("📦 **Inventory System**")
        inventory_list = []
        if total_received > 0:
            inventory_list.append(f"• Total received: {int(total_received):,} units")
        if total_opening > 0:
            inventory_list.append(f"• Total opening stock: {int(total_opening):,} units")
        if total_closing > 0:
            inventory_list.append(f"• Total closing stock: {int(total_closing):,} units")
        inventory_list.append(f"• Current items tracked: {len(metrics_df)} location-item combinations")
        if unique_locations > 0:
            inventory_list.append(f"• Locations: {unique_locations}")
        if unique_items > 0:
            inventory_list.append(f"• Items: {unique_items}")
        if date_range:
            inventory_list.append(f"• Date range: {date_range}")
        inventory_list.append("• Daily stock levels (opening, received, issued, closing)")
        st.markdown("<br>".join(inventory_list), unsafe_allow_html=True)
    with col2:
        st.markdown("📊 **Usage/Sales System**")
        usage_list = []
        if total_issued > 0:
            usage_list.append(f"• Total issued: {int(total_issued):,} units")
        if unique_dates > 0:
            usage_list.append(f"• Days of data: {unique_dates}")
        if avg_consumption > 0:
            usage_list.append(f"• Avg consumption: {avg_consumption:.1f} units/day")
            usage_list.append("• Consumption patterns analyzed from issued quantities")
        else:
            usage_list.append("• Consumption patterns calculated from historical data")
        if not metrics_df.empty:
            items_with_usage = len(metrics_df[metrics_df["avg_daily_issue"] > 0]) if "avg_daily_issue" in metrics_df.columns else 0
            usage_list.append(f"• Items with usage data: {items_with_usage}")
        st.markdown("<br>".join(usage_list), unsafe_allow_html=True)
    with col3:
        st.markdown("📋 **Purchase Order System**")
        po_list = []
        if avg_lead_time > 0:
            po_list.append(f"• Avg lead time: {avg_lead_time:.1f} days")
        if len(at_risk) > 0:
            po_list.append(f"• Reorder recommendations: {len(at_risk)} items")
        else:
            po_list.append("• Reorder recommendations: 0 items (all well-stocked)")
        if not metrics_df.empty and "lead_time_days" in metrics_df.columns:
            items_with_lead_time = len(metrics_df[metrics_df["lead_time_days"].notna()])
            po_list.append(f"• Items with lead time data: {items_with_lead_time}")
        po_list.append("• Lead times factored into urgency calculations")
        st.markdown("<br>".join(po_list), unsafe_allow_html=True)
    
    if session:
        unified_msg = f"✅ **Unified View**: All {len(metrics_df)} location-item combinations consolidated in Snowflake for single-pane-of-glass visibility"
    else:
        unified_msg = f"✅ **Unified View**: All {len(metrics_df)} location-item combinations from local data (connect to Snowflake for real-time updates)"
    st.success(unified_msg)
    
    if session:
        caption_text = f"Data source: {data_source} ({data_source_details}). "
        if "Dynamic Table" in data_source:
            caption_text += "Auto-refreshes when source systems update."
        else:
            caption_text += "Refreshes on query. Consider using Dynamic Tables for auto-refresh."
    else:
        caption_text = f"Data source: {data_source} ({data_source_details}). Connect to Snowflake for real-time data and Dynamic Tables auto-refresh."
    
    st.caption(caption_text)


if __name__ == "__main__":
    main()
