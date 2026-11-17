-- Periodic snapshot fact. Grain: item x day. One row per item per day the county published inventory.
-- Incremental: each run processes the latest day (it may have been re-pulled) plus any day not yet
-- in the table (e.g. an older manual-export backfill loaded later).
{{ config(
    materialized='incremental',
    unique_key=['snapshot_date', 'item_key'],
    incremental_strategy='delete+insert'
) }}

select
    snapshot_date,
    item_code                                          as item_key,
    on_hand_qty,
    price,
    sale_price,
    sale_end_date,
    (sale_price is not null and (sale_end_date is null or sale_end_date >= snapshot_date)) as is_on_sale,
    on_hand_qty * price                                as on_hand_retail_value,
    on_hand_qty = 0                                    as is_zero_stock,
    extract_method
from {{ ref('stg_inventory') }}
{% if is_incremental() %}
where snapshot_date >= (select coalesce(max(snapshot_date), '1900-01-01'::date) from {{ this }})
   or snapshot_date not in (select distinct snapshot_date from {{ this }})
{% endif %}
