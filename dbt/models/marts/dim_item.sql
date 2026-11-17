-- Current state of every item (SCD type 1). History: snapshots.snap_item_attributes (SCD type 2).
select
    item_code                         as item_key,
    item_name,
    item_type,
    coalesce(item_type, 'UNKNOWN') in ({% for t in var('product_item_types') %}'{{ t }}'{{ ", " if not loop.last }}{% endfor %})
                                      as is_product,
    subcategory,
    size,
    current_price,
    md5(latest_sales_supplier)        as current_supplier_key,
    latest_sales_supplier             as current_supplier_name,
    latest_purchase_vendor            as current_purchase_vendor,
    in_inventory,
    in_sales,
    in_purchases,
    last_inventory_date,
    last_sales_month,
    last_purchase_month
from {{ ref('int_item_attributes') }}
