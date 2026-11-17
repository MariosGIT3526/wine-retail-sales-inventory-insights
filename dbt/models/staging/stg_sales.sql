-- One row per item per month. Quantities are CASES (per the county's data dictionary).
with source as (
    select * from {{ source('raw', 'sales') }}
)

select
    make_date({{ parse_number('calendar_year') }}::int, {{ parse_number('cal_month_num') }}::int, 1) as month_start,
    {{ clean_code('item_code') }}                     as item_code,
    coalesce({{ clean_name('supplier') }}, 'UNKNOWN') as supplier_name,
    trim(item_description)                            as item_description,
    {{ clean_name('item_type') }}                     as item_type,
    {{ parse_number('rtl_sales') }}                   as retail_sales_cases,
    {{ parse_number('rtl_transfers') }}               as retail_transfers_cases,
    {{ parse_number('whs_sales') }}                   as warehouse_sales_cases,
    nullif(_source_updated_at, '')::timestamptz       as source_updated_at,
    _extract_method                                   as extract_method
from source
