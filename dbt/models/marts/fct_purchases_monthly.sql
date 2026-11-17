-- Grain: item x vendor x month. Units: cases.
-- Repeated lines for the same item/vendor/month are summed; source_line_count keeps the evidence.
select
    month_start,
    item_code              as item_key,
    md5(vendor_name)       as supplier_key,
    sum(quantity_cases)    as purchased_cases,
    count(*)               as source_line_count,
    bool_or(quantity_cases < 0) as has_negative_line
from {{ ref('stg_purchases') }}
group by month_start, item_code, md5(vendor_name)
