# Data model (star schema)

> **Status: draft.** Built from the joins tested so far (item codes match across all three sources;
> 232 of 235 purchase vendors match a sales supplier exactly). Re-draw after the full API profiling pass.
> There is **no store dimension**: none of the three sources has a store column (data-quality log #11).

```mermaid
erDiagram
    dim_date ||--o{ fct_sales_monthly : "month_start = date_day"
    dim_date ||--o{ fct_purchases_monthly : "month_start = date_day"
    dim_date ||--o{ fct_inventory_daily : "snapshot_date = date_day"
    dim_item ||--o{ fct_sales_monthly : item_key
    dim_item ||--o{ fct_purchases_monthly : item_key
    dim_item ||--o{ fct_inventory_daily : item_key
    dim_item ||--o{ mart_item_abc : item_key
    dim_supplier ||--o{ fct_sales_monthly : supplier_key
    dim_supplier ||--o{ fct_purchases_monthly : supplier_key

    dim_date {
        date date_day PK
        date month_start
        int year
        int month_num
        bool has_sales_data
        bool has_inventory_snapshot
    }
    dim_item {
        text item_key PK
        text item_name
        text item_type
        text subcategory
        text size
        numeric current_price
        text current_supplier_key
    }
    dim_supplier {
        text supplier_key PK
        text supplier_name
        text supplier_role
    }
    fct_sales_monthly {
        date month_start FK
        text item_key FK
        text supplier_key FK
        numeric retail_sales_cases
        numeric retail_transfers_cases
        numeric warehouse_sales_cases
    }
    fct_purchases_monthly {
        date month_start FK
        text item_key FK
        text supplier_key FK
        numeric purchased_cases
        int source_line_count
    }
    fct_inventory_daily {
        date snapshot_date FK
        text item_key FK
        numeric on_hand_qty
        numeric price
        numeric sale_price
        numeric on_hand_retail_value
    }
    mart_item_abc {
        text item_key FK
        numeric avg_monthly_cases
        int sales_rank
        numeric cumulative_share
        text abc_class
    }
```

## Grain and units

| Table | Grain | Units | Type |
|---|---|---|---|
| `fct_sales_monthly` | item × supplier × month | cases | transaction (monthly) |
| `fct_purchases_monthly` | item × vendor × month | cases | transaction (monthly) |
| `fct_inventory_daily` | item × day | **undocumented** (log #7) | periodic snapshot |
| `snapshots.snap_item_attributes` | item × version | — | SCD type 2 |

Power BI connects to the `marts` schema only. Relationships are one-to-many, single direction, dimension → fact.
