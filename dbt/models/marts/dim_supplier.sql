select
    supplier_key,
    supplier_name,
    is_sales_supplier,
    is_purchase_vendor,
    case
        when is_sales_supplier and is_purchase_vendor then 'both'
        when is_sales_supplier then 'sales only'
        else 'purchases only'
    end as supplier_role,
    first_seen_month,
    last_seen_month
from {{ ref('int_suppliers') }}
