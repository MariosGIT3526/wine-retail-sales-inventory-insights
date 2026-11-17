-- Grain: item x supplier x month. Units: cases.
-- supplier_key is the supplier ON THAT MONTH'S RECORD, so supplier concentration over time uses
-- the supplier at the time, not the item's current supplier.
select
    s.month_start,
    s.item_code                                  as item_key,
    md5(s.supplier_name)                         as supplier_key,
    s.retail_sales_cases,
    s.retail_transfers_cases,
    s.warehouse_sales_cases,
    -- H3 helper: positive = more shipped to stores than they sold that month
    coalesce(s.retail_transfers_cases, 0) - coalesce(s.retail_sales_cases, 0) as transfer_minus_sales_cases
from {{ ref('stg_sales') }} s
where s.item_type is null
   or s.item_type in ({% for t in var('product_item_types') %}'{{ t }}'{{ ", " if not loop.last }}{% endfor %})
