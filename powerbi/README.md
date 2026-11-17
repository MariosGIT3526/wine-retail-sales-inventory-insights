# Power BI layer

Coming after the dbt marts are live. Plan:

1. **Get Data → PostgreSQL database.** Use the Supabase *Session pooler* host. Database: `postgres`. Import the `marts` schema tables only.
2. Relationships: `dim_date[date_day]`, `dim_item[item_key]` and `dim_supplier[supplier_key]` → each fact, one-to-many, single direction.
3. Move the existing Power Query cleaning and the Wine ABC DAX table out of the report. They're now `stg_*` models and `mart_item_abc`.
4. **Row-level security (dynamic):** import `seeds.rls_category_access`, relate it to `dim_item[item_type]`, and add a role with the DAX filter
   `[user_email] = USERPRINCIPALNAME()` on that table. Test with **Modeling → View as**.
   It's by item type because the source data has no store column (data-quality log #11).
