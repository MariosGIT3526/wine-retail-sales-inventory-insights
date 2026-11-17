-- One row per item code seen in ANY source, with its most recent attributes from each.
-- 5,941 codes changed supplier/description over time (data-quality log #4): the current value lives
-- here, the history in snapshots.snap_item_attributes and in fct_sales_monthly.supplier_key.
with latest_inventory as (
    select distinct on (item_code)
        item_code, item_description, subcategory, size, price, snapshot_date
    from {{ ref('stg_inventory') }}
    order by item_code, snapshot_date desc
),

latest_sales as (
    select distinct on (item_code)
        item_code, item_description, item_type, supplier_name, month_start
    from {{ ref('stg_sales') }}
    order by item_code, month_start desc, retail_sales_cases desc nulls last
),

latest_purchase as (
    select distinct on (item_code)
        item_code, item_description, purchase_category, vendor_name, month_start
    from {{ ref('stg_purchases') }}
    order by item_code, month_start desc, quantity_cases desc nulls last
),

all_codes as (
    select item_code from latest_inventory
    union select item_code from latest_sales
    union select item_code from latest_purchase
)

select
    c.item_code,
    coalesce(i.item_description, s.item_description, p.item_description) as item_name,
    -- item_type comes from sales; purchases use slightly different labels (KEG vs KEGS)
    coalesce(s.item_type, case p.purchase_category when 'KEG' then 'KEGS' else p.purchase_category end) as item_type,
    i.subcategory,
    i.size,
    i.price                                as current_price,
    s.supplier_name                        as latest_sales_supplier,
    p.vendor_name                          as latest_purchase_vendor,
    i.item_code is not null                as in_inventory,
    s.item_code is not null                as in_sales,
    p.item_code is not null                as in_purchases,
    i.snapshot_date                        as last_inventory_date,
    s.month_start                          as last_sales_month,
    p.month_start                          as last_purchase_month
from all_codes c
left join latest_inventory i using (item_code)
left join latest_sales     s using (item_code)
left join latest_purchase  p using (item_code)
