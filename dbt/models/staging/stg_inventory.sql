-- One row per item per snapshot day. Quantity unit is NOT documented by the county
-- (data-quality log #7: likely bottles, while sales/purchases are cases).
with source as (
    select * from {{ source('raw', 'inventory') }}
)

select
    _snapshot_date::date                   as snapshot_date,
    {{ clean_code('code') }}               as item_code,
    {{ clean_name('category') }}           as subcategory,
    trim(description)                      as item_description,
    upper(trim(size))                      as size,
    {{ parse_number('totalinventory') }}   as on_hand_qty,
    {{ parse_number('price') }}            as price,
    {{ parse_number('saleprice') }}        as sale_price,
    {{ parse_date('saleenddate') }}        as sale_end_date,
    nullif(_source_updated_at, '')::timestamptz as source_updated_at,
    _extract_method                        as extract_method
from source
