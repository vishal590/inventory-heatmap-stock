-- Snowflake setup for Inventory Heatmap & Stock-Out Alerts
-- Creates table, seeds sample rows (same as data/sample_stock.csv), and defines a metrics view.

-- Optional: set your context before running
-- use role SYSADMIN;
-- use warehouse COMPUTE_WH;
-- create database if not exists AI_GOOD;
-- use database AI_GOOD;
-- create schema if not exists PUBLIC;
-- use schema PUBLIC;

create or replace table stock_daily (
  date date,
  location string,
  item string,
  opening_stock number,
  received number,
  issued number,
  closing_stock number,
  lead_time_days number
);

-- Seed sample data
truncate table stock_daily;
insert into stock_daily (date, location, item, opening_stock, received, issued, closing_stock, lead_time_days) values
  ('2025-12-27','Central','Amoxicillin',120,30,40,110,5),
  ('2025-12-28','Central','Amoxicillin',110,20,35,95,5),
  ('2025-12-29','Central','Amoxicillin',95,0,30,65,5),
  ('2025-12-30','Central','Amoxicillin',65,0,28,37,5),
  ('2025-12-31','Central','Amoxicillin',37,50,32,55,5),
  ('2026-01-01','Central','Amoxicillin',55,0,25,30,5),
  ('2025-12-27','East','ORS',200,0,60,140,4),
  ('2025-12-28','East','ORS',140,50,70,120,4),
  ('2025-12-29','East','ORS',120,0,60,60,4),
  ('2025-12-30','East','ORS',60,0,55,5,4),
  ('2025-12-31','East','ORS',5,50,40,15,4),
  ('2026-01-01','East','ORS',15,0,10,5,4),
  ('2025-12-27','West','PPE Kits',80,40,20,100,7),
  ('2025-12-28','West','PPE Kits',100,0,25,75,7),
  ('2025-12-29','West','PPE Kits',75,0,20,55,7),
  ('2025-12-30','West','PPE Kits',55,0,18,37,7),
  ('2025-12-31','West','PPE Kits',37,0,12,25,7),
  ('2026-01-01','West','PPE Kits',25,30,15,40,7);

-- Metrics view (latest snapshot per item/location)
create or replace view inventory_metrics_v as
with usage as (
  select
    date,
    location,
    item,
    closing_stock,
    lead_time_days,
    avg(issued) over (
      partition by location, item
      order by date
      rows between 6 preceding and current row
    ) as avg_daily_issue
  from stock_daily
),
scored as (
  select
    date,
    location,
    item,
    closing_stock,
    lead_time_days,
    coalesce(avg_daily_issue, 0) as avg_daily_issue,
    case when avg_daily_issue is null or avg_daily_issue = 0 then null
         else closing_stock / avg_daily_issue end as days_of_cover,
    row_number() over (partition by location, item order by date desc) as rn
  from usage
)
select
  date,
  location,
  item,
  closing_stock,
  avg_daily_issue,
  days_of_cover,
  lead_time_days,
  case
    when days_of_cover is null then 'unknown'
    when days_of_cover < 2 then 'red'
    when days_of_cover <= 5 then 'orange'
    else 'green'
  end as status,
  greatest(0, (5 * coalesce(avg_daily_issue, 0)) - closing_stock) as suggested_reorder
from scored
where rn = 1;

-- Convenience at-risk view
create or replace view inventory_at_risk_v as
select *
from inventory_metrics_v
where days_of_cover is null or days_of_cover <= 5;
