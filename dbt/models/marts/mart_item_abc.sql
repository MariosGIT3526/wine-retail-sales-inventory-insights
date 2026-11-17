-- ABC classification of items by average monthly COUNTY-STORE sales (cases) over a period.
-- Carries over the Power BI "Wine ABC" logic into SQL (window-function running total).
-- Rule: rank by average over months the item actually sold; needs >= min_months_sold months.
-- Change the period/item type with --vars, e.g.
--   dbt build -s mart_item_abc --vars '{abc_start: "2026-06-01", abc_end: "2026-08-01", abc_item_type: "WINE"}'
{% set abc_start = var('abc_start', '2026-06-01') %}
{% set abc_end = var('abc_end', '2026-08-01') %}
{% set abc_item_type = var('abc_item_type', 'WINE') %}
{% set min_months_sold = var('abc_min_months_sold', 2) %}

with item_sales as (
    select
        f.item_key,
        count(distinct f.month_start) filter (where f.retail_sales_cases > 0) as months_sold,
        sum(f.retail_sales_cases)                                            as period_cases
    from {{ ref('fct_sales_monthly') }} f
    join {{ ref('dim_item') }} i using (item_key)
    where f.month_start between '{{ abc_start }}'::date and '{{ abc_end }}'::date
      and i.item_type = '{{ abc_item_type }}'
    group by f.item_key
),

ranked as (
    select
        item_key,
        months_sold,
        period_cases,
        period_cases / months_sold                                                 as avg_monthly_cases,
        rank() over (order by period_cases / months_sold desc)                     as sales_rank,
        -- RANGE (the default) gives tied items the same running total, matching the Power BI version
        sum(period_cases / months_sold) over (order by period_cases / months_sold desc)
            / sum(period_cases / months_sold) over ()                              as cumulative_share
    from item_sales
    where months_sold >= {{ min_months_sold }}
)

select
    '{{ abc_start }}'::date  as period_start,
    '{{ abc_end }}'::date    as period_end,
    '{{ abc_item_type }}'    as item_type,
    item_key,
    months_sold,
    period_cases,
    avg_monthly_cases,
    sales_rank,
    cumulative_share,
    case
        when cumulative_share <= 0.80 then 'A'
        when cumulative_share <= 0.95 then 'B'
        else 'C'
    end as abc_class
from ranked
