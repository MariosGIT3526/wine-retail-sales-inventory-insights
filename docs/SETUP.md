# Setup guide (first time)

Do these in order. Parts 1–3 get the daily snapshots running **today**. Part 4 (the database) can come
later: the workflow skips the database steps until its secrets exist.

| Part | What | Time |
|---|---|---|
| 1 | Get a Socrata app token | 5 min |
| 2 | Put the code on GitHub | 15 min |
| 3 | Turn on the daily job | 10 min |
| 4 | Create the Supabase Postgres database | 15 min |
| 5 | Save the CSVs you already downloaded | 10 min |
| 6 | Run things on your own computer (optional) | 20 min |

---

## Part 1 — Socrata app token

The county's portal limits how fast anonymous scripts can pull data. A free app token raises the limit.

1. Go to **data.montgomerycountymd.gov** and click **Sign In** (top right) → **Sign up**. Create an account and confirm your email.
2. Click your name (top right) → **My Profile** → **Developer Settings** (or **Edit Profile → Developer Settings**).
3. Click **Create New App Token**. Name: `abs-wine-pipeline`. Description: anything. Save.
4. Copy the **App Token** (the shorter value). You don't need the "Secret Token".

Keep it somewhere safe for Part 3.

---

## Part 2 — Put the code on GitHub

**Make the repo public.** Public repos get unlimited free GitHub Actions minutes, and recruiters can see it.

1. Sign in at **github.com** (account `MariosGIT3526`).
2. Click **+** (top right) → **New repository**.
   - Name: `abs-wine-pipeline`
   - Public
   - **Don't** add a README, .gitignore or license (the project already has them).
   - Click **Create repository**.
3. Install **GitHub Desktop** (desktop.github.com) and sign in with your GitHub account.
4. In GitHub Desktop: **File → Clone repository** → pick `abs-wine-pipeline` → choose a folder (e.g. `Documents\GitHub`) → **Clone**.
5. Unzip the project and copy **everything inside** the `abs-wine-pipeline` folder into the cloned folder.
   - On Windows, turn on **View → Show → Hidden items** first so you can see the `.github` folder and copy it too. The daily job lives in `.github/workflows/`; without it nothing runs.
6. Back in GitHub Desktop you'll see the files listed. Bottom-left summary: `Initial project`. Click **Commit to main**, then **Push origin**.
7. Refresh your repo page on github.com. You should see folders `.github`, `dbt`, `docs`, `extract`, `landing`, …

---

## Part 3 — Turn on the daily job (GitHub Actions)

**What GitHub Actions is:** GitHub rents you a fresh Linux computer, runs the steps in
`.github/workflows/daily_pipeline.yml` on it, then throws the computer away. The schedule line
(`cron: "37 14 * * *"`) means "every day at 14:37 UTC" (6:37 AM Pacific in winter, 7:37 AM in summer).
Because the computer is thrown away, anything worth keeping has to be saved somewhere. That's why the
job commits the new data files back into your repo.

### 3a. Add the secret

Secrets are passwords GitHub stores encrypted and hands to the job. They never show in logs or code.

1. On your repo page: **Settings** (tab) → left menu **Secrets and variables → Actions**.
2. Click **New repository secret**.
   - Name: `SOCRATA_APP_TOKEN`
   - Secret: the app token from Part 1
   - **Add secret**

### 3b. Let the job save files

1. **Settings → Actions → General**.
2. Scroll to **Workflow permissions** → choose **Read and write permissions** → **Save**.

### 3c. Run it once by hand

1. Click the **Actions** tab. If it asks, click **I understand my workflows, go ahead and enable them**.
2. Left side: **daily-pipeline** → right side: **Run workflow** → **Run workflow** (green).
3. Click the run that appears. Each step shows a ✓ when done. Expected:
   - *Extract from Socrata* ✓ (logs show rows fetched for inventory, purchases, sales)
   - *Commit landing files* ✓
   - *Load into Postgres*, *dbt source freshness*, *dbt build* show as **skipped**. That's correct until Part 4.
4. Go to the **Code** tab → `landing/inventory/`. You should see `inventory_YYYY-MM-DD.csv.gz`, plus a new
   commit from **github-actions[bot]** named `data: landing snapshot …`.

From now on it runs every day by itself. **Your inventory history starts on this date.** Write it down
for the README's limitations section.

**If a run fails:** click it, then the red ✗ step, and read the last lines. Common causes:
- `403` on push → step 3b wasn't saved.
- `429 Too Many Requests` → the token secret is missing or misspelled (the name must match exactly).
- After a failed **load** step: rerun with **Run workflow → force = true**, so the sales file is pulled again.

GitHub emails you when a scheduled run fails, so you'll know.

---

## Part 4 — Supabase (free hosted Postgres)

1. Go to **supabase.com** → **Start your project** → sign in with GitHub.
2. **New project**:
   - Name: `abs-wine`
   - Database password: click **Generate a password** and **save it in a password manager now**. You'll need it, and Supabase won't show it again.
   - Region: **West US (North California)** (closest to you; any US region works).
   - Plan: Free → **Create new project**. Wait ~2 minutes.
3. At the top of the project page click **Connect**. Under **Connection string**, choose the **Session pooler** tab.
   - Use **Session pooler**, *not* "Direct connection" and *not* "Transaction pooler". Direct connection is IPv6-only, and GitHub's runners can't reach it. Transaction pooler breaks some features dbt and `COPY` rely on.
4. Click **View parameters** (or read them out of the URI). You need:

   | Parameter | Looks like | GitHub secret name |
   |---|---|---|
   | host | `aws-0-us-west-1.pooler.supabase.com` | `PGHOST` |
   | port | `5432` | `PGPORT` |
   | user | `postgres.abcdefghijklmnop` (includes the project ref) | `PGUSER` |
   | database | `postgres` | `PGDATABASE` |
   | password | the one you saved | `PGPASSWORD` |

5. Add each one as a repository secret (Part 3a), using exactly those names.
6. **Actions → daily-pipeline → Run workflow** with **force = true** (the first load needs every file). This time all steps should run:
   - *Load into Postgres* creates `raw.inventory`, `raw.purchases`, `raw.sales`.
   - *dbt build* creates the `staging`, `intermediate`, `marts`, `snapshots` and `seeds` schemas and runs every test.
7. In Supabase: **Table Editor** → schema dropdown → `marts` → open `fct_sales_monthly` to see rows.

**Free-tier limits to know:**
- **Paused after 7 days without activity.** The daily job counts as activity, so this won't happen while it runs.
- **500 MB database.** About 7,000 inventory rows a day adds up. Check **Settings → Usage** monthly. If it gets close, delete old rows from `raw.inventory`. The full history stays safe in `landing/` and can be reloaded at any time.

---

## Part 5 — Save the CSVs you already downloaded

Your September purchases export and early-October inventory export are the **only copies left anywhere**,
because the county has already overwritten both. Add them to the history:

```powershell
# in the repo folder, after Part 6 step 1-2 (Python installed)
python extract/backfill_from_csv.py purchases data/manual_exports/purchases_export_2026-10-08.csv
python extract/backfill_from_csv.py inventory data/manual_exports/inventory_export_2026-10-08.csv --snapshot-date 2026-10-08
```

The original exports are kept in `data/manual_exports/` (see the README there).
Then commit and push the two new files in `landing/` with GitHub Desktop. The next daily run loads them.
They're tagged `manual_export` (data-quality log #14).

---

## Part 6 — Run locally (optional, for development)

You'll want this when you write new dbt models. Commands are for Windows PowerShell.

1. Install **Python 3.12** from python.org. On the first installer screen, tick **Add python.exe to PATH**.
2. Open PowerShell in the repo folder (GitHub Desktop → **Repository → Open in Command Prompt/Terminal**) and run:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   If PowerShell blocks the activate script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.
3. Copy `.env.example` to `.env` and fill in your values. `.env` is ignored by git, so it never gets uploaded.
4. Load `.env` into the current PowerShell window (do this each new window):
   ```powershell
   Get-Content .env | ForEach-Object { if ($_ -match '^\s*([^#][^=]*)=(.*)$') { Set-Item "env:$($matches[1].Trim())" $matches[2] } }
   ```
5. Run the pipeline pieces:
   ```powershell
   python extract/extract.py          # pull from the county
   python extract/load.py             # load landing files into Supabase
   cd dbt
   dbt debug                          # checks the connection - should end with "All checks passed!"
   dbt source freshness
   dbt build                          # models + snapshots + seeds + tests
   ```

If you pull locally **and** the daily job also runs, you can create a git conflict on `landing/_state.json`.
Click **Fetch origin / Pull** in GitHub Desktop before you commit.
