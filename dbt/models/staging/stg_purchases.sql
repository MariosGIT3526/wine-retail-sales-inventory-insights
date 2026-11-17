-- One row per purchase-order line as published. Quantity is CASES.
-- The source can repeat an item within a month (see data-quality log #5); fct_purchases_monthly aggregates.
with source as (
    select * from {{ source('raw', 'purchases') }}
)

select
    to_date(trim(calendar_month) || ' ' || {{ parse_number('calendar_year') }}::int, 'FMMonth YYYY') as month_start,
    {{ clean_code('item') }}                           as item_code,
    coalesce({{ clean_name('vendor_name') }}, 'UNKNOWN') as vendor_name,
    {{ clean_name('inventory_category') }}             as purchase_category,
    trim(item_description)                             as item_description,
    {{ parse_number('quantity') }}                     as quantity_cases,
    trim(transaction_source_type_name)                 as transaction_type,
    _file_name                                         as file_name,
    nullif(_source_updated_at, '')::timestamptz        as source_updated_at,
    _extract_method                                    as extract_method
from source
