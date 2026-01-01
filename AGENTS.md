# Agent Instructions

## Context
- Hackathon: AI for Good (YourStory/Snowflake).
- Track: Inventory Heatmap & Stock-Out Alerts (solo, 3 days remaining).
- Goal: Snowflake + Streamlit app for stock health, alerts, reorder suggestions; all free-tier.

## Current Assets
- Deck: docs/presentations/Prototype Submission Deck _ AI for Good Hackathon.pptx (fill with screenshots/links).
- No code committed yet; plan to add SQL, Streamlit app, sample CSV.

## Working Plan
1) Data: Prepare small CSV; load into Snowflake table.
2) SQL: Compute avg_daily_issue, days_of_cover, status flags, suggested reorder. Create views.
3) Streamlit: Filters, heatmap, at-risk table, export, trend chart, optional AI summary.
4) Polish: Screenshots, links (prototype/GitHub/demo video), PPT update.
5) Submit before Jan 4, 2026 11:59 PM IST.

## Constraints
- Solo. Free tier only (no paid services).
- Keep data small to conserve credits.

## Quick Answers for Submission
- Idea: Stock health dashboard with early alerts and reorder guidance in Snowflake/Streamlit.
- Problem: Late visibility into inventory causes stock-outs/waste.
- Impact: Ensures critical supplies availability; reduces waste.
- Tech stack: Snowflake (SQL, optional Dynamic Tables/Streams & Tasks), Streamlit, optional Snowpark/AI SQL.
