# Manual exports

CSV files downloaded by hand from the Montgomery County open data portal ("Export" button).
Kept unmodified as the original source. `extract/backfill_from_csv.py` turns them into landing files.

| File | Original name | Dataset | Contents |
|---|---|---|---|
| `sales_export_2026-10-08.csv` | `export.csv` | Warehouse and Retail Sales (`v76h-r7br`) | Item × month sales |
| `purchases_export_2026-10-08.csv` | `export (1).csv` | Product Purchases by DLC (`kpfd-c5d5`) | September 2026 PO lines |
| `inventory_export_2026-10-08.csv` | `export (2).csv` | ABS Store Inventory and Sale Items (`ib5t-5ncy`) | Inventory snapshot as of download date |
| `licensees_export_2026-10-23.csv` | `export (3).csv` | Licensee list | Licensed bars, restaurants, shops |

Dates in the filenames are the download dates (file modified time).
