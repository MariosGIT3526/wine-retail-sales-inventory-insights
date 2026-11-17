-- Every supplier/vendor name after cleanup, with the role(s) it plays.
-- Sales list the SUPPLIER on the movement record; purchase orders list the VENDOR paid.
-- For ~1.2% of items these differ (distributor vs brand owner) - data-quality log #9.
with names as (
    select supplier_name as supplier_name, 'sales' as role, month_start from {{ ref('stg_sales') }}
    union all
    select vendor_name, 'purchases', month_start from {{ ref('stg_purchases') }}
)

select
    md5(supplier_name)                         as supplier_key,
    supplier_name,
    bool_or(role = 'sales')                    as is_sales_supplier,
    bool_or(role = 'purchases')                as is_purchase_vendor,
    min(month_start)                           as first_seen_month,
    max(month_start)                           as last_seen_month
from names
group by supplier_name
