import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


def get_snowflake_session():
    """
    Returns a Snowflake Snowpark session if running inside Snowflake Streamlit.
    Falls back to None when running locally.
    """
    try:
        from snowflake.snowpark.context import get_active_session

        return get_active_session()
    except Exception:
        return None


@st.cache_data
def load_daily_data():
    session = get_snowflake_session()
    if session:
        return session.table("STOCK_DAILY").to_pandas()
    # local fallback from sample CSV
    csv_path = Path("data/sample_stock.csv")
    if csv_path.exists():
        return pd.read_csv(csv_path, parse_dates=["date"])
    return pd.DataFrame()


def compute_metrics_from_df(df: pd.DataFrame) -> pd.DataFrame:
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
    df["days_of_cover"] = df["closing_stock"] / df["avg_daily_issue"].replace(0, pd.NA)
    df["status"] = pd.cut(
        df["days_of_cover"],
        bins=[-float("inf"), 2, 5, float("inf")],
        labels=["red", "orange", "green"],
    )
    df.loc[df["days_of_cover"].isna(), "status"] = "unknown"
    df["suggested_reorder"] = (
        (5 * df["avg_daily_issue"].fillna(0) - df["closing_stock"])
        .clip(lower=0)
        .round(0)
    )
    latest_idx = df.groupby(["location", "item"])["date"].idxmax()
    return df.loc[latest_idx].reset_index(drop=True)


@st.cache_data
def load_metrics():
    session = get_snowflake_session()
    if session:
        return session.table("INVENTORY_METRICS_V").to_pandas()
    return compute_metrics_from_df(load_daily_data())


def build_heatmap(df: pd.DataFrame):
    if df.empty:
        return None
    status_scale = alt.Scale(
        domain=["red", "orange", "green", "unknown"],
        range=["#d73027", "#fc8d59", "#1a9850", "#bdbdbd"],
    )
    chart = (
        alt.Chart(df)
        .mark_rect()
        .encode(
            x=alt.X("item:N", title="Item"),
            y=alt.Y("location:N", title="Location"),
            color=alt.Color("status:N", scale=status_scale, title="Status"),
            tooltip=[
                "location",
                "item",
                alt.Tooltip("closing_stock:Q", title="Closing"),
                alt.Tooltip("avg_daily_issue:Q", title="Avg daily issue"),
                alt.Tooltip("days_of_cover:Q", title="Days of cover"),
                alt.Tooltip("suggested_reorder:Q", title="Suggested reorder"),
            ],
        )
    )
    return chart


def main():
    st.set_page_config(page_title="Inventory Heatmap & Stock-Out Alerts", layout="wide")
    st.title("Inventory Heatmap & Stock-Out Alerts")
    st.caption("Snowflake + Streamlit prototype (free-tier friendly)")

    daily_df = load_daily_data()
    metrics_df = load_metrics()

    if metrics_df.empty:
        st.error("No data found. Load sample CSV or connect to Snowflake and rerun.")
        return

    locations = sorted(metrics_df["location"].unique())
    items = sorted(metrics_df["item"].unique())

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

    heatmap = build_heatmap(filtered)
    if heatmap:
        st.subheader("Stock Health Heatmap")
        st.altair_chart(heatmap, use_container_width=True)

    at_risk = filtered[
        (filtered["days_of_cover"].isna()) | (filtered["days_of_cover"] <= risk_days)
    ].sort_values(["days_of_cover", "location", "item"])

    st.subheader("At-Risk Items")
    st.dataframe(
        at_risk,
        use_container_width=True,
        hide_index=True,
        column_config={
            "days_of_cover": st.column_config.NumberColumn(format="%.1f"),
            "avg_daily_issue": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    csv_export = at_risk.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Export at-risk CSV", data=csv_export, file_name="at_risk.csv", mime="text/csv"
    )

    st.subheader("Trends (closing stock)")
    trend_item = st.selectbox("Select item", items)
    trend_location = st.selectbox("Select location", locations)
    trend_df = daily_df[
        (daily_df["item"] == trend_item) & (daily_df["location"] == trend_location)
    ].sort_values("date")
    if trend_df.empty:
        st.info("No trend data for this selection.")
    else:
        trend_chart = (
            alt.Chart(trend_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("closing_stock:Q", title="Closing stock"),
                tooltip=["date:T", "closing_stock:Q", "issued:Q", "received:Q"],
            )
        )
        st.altair_chart(trend_chart, use_container_width=True)

    st.caption(
        "Data source: Snowflake views (inventory_metrics_v, stock_daily). "
        "Fallback uses local data/sample_stock.csv when not connected."
    )


if __name__ == "__main__":
    main()
