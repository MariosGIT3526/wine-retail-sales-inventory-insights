-- Day-grain calendar. Monthly facts join on month_start (= the 1st of the month).
with days as (
    select d::date as date_day
    from generate_series('2017-01-01'::date, (current_date + interval '365 days')::date, interval '1 day') as d
),

sales_months as (select distinct month_start from {{ ref('stg_sales') }}),
purchase_months as (select distinct month_start from {{ ref('stg_purchases') }}),
inventory_days as (select distinct snapshot_date from {{ ref('stg_inventory') }})

select
    d.date_day,
    date_trunc('month', d.date_day)::date            as month_start,
    extract(year from d.date_day)::int               as year,
    extract(quarter from d.date_day)::int            as quarter,
    extract(month from d.date_day)::int              as month_num,
    to_char(d.date_day, 'Mon')                       as month_name,
    to_char(d.date_day, 'YYYY-MM')                   as year_month,
    extract(isodow from d.date_day)::int             as iso_day_of_week,
    d.date_day = date_trunc('month', d.date_day)::date as is_month_start,
    -- Gap flags: the sales history is missing whole months (data-quality log #3). Filter visuals on these.
    sm.month_start is not null                       as has_sales_data,
    pm.month_start is not null                       as has_purchase_data,
    i.snapshot_date is not null                      as has_inventory_snapshot
from days d
left join sales_months    sm on sm.month_start = date_trunc('month', d.date_day)::date
left join purchase_months pm on pm.month_start = date_trunc('month', d.date_day)::date
left join inventory_days  i  on i.snapshot_date = d.date_day
