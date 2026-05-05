# Netflix Security AE Portfolio — Project Brief

This file is read automatically at the start of every Claude Code session.
It keeps you and Claude aligned without needing to re-explain the project.

---

## Who I am

Data analyst background (spreadsheets + basic SQL). Recently left Netflix.
Actively job-searching for Analytics Engineer roles.
Goal: build this portfolio project to demonstrate AE skills on LinkedIn.
Learning style: need the WHY explained before the HOW. Excel analogies help.

---

## What we're building

A Netflix-style security analytics pipeline that detects:
- **Account Takeover (ATO)** — attacker brute-forces a user's password, eventually gets in
- **Credential Stuffing** — one IP blasts many different accounts rapidly
- **DDoS signals** — a few IPs send massive traffic volumes
- **Device ecosystem anomalies** — users with many untrusted/new devices

**Stack:**
- Python → generates synthetic data into DuckDB
- DuckDB → the database (single file, SQL-queryable)
- dbt Core → transforms raw data through 3 layers (staging → intermediate → marts)
- Evidence.dev → SQL-based dashboard (next phase, not built yet)

**Project folder:** `/Users/adamniebylski/Desktop/codecademy-git-test/Showcase_Projects/(CLICK-HERE)AnalyticsEngineeringPortfolio/`

**Virtual environment:** `source ~/ae-env/bin/activate`

---

## Architecture: the 3-layer model

```
raw data in DuckDB
      ↓
  staging/        clean + rename columns only, no aggregations (materialized as VIEW)
      ↓
  intermediate/   joins and aggregations, reusable building blocks (materialized as VIEW)
      ↓
  marts/          final business-facing tables for dashboards (materialized as TABLE)
```

Excel analogy: raw import tab → normalize tab → pivot tables → manager summary sheet.

---

## Key concepts explained so far

- **`dbt_project.yml`** — project config; sets layer materializations (view vs table)
- **`~/.dbt/profiles.yml`** — database connection config (path to DuckDB file)
- **`{{ ref() }}`** — dbt's way of linking models; builds the dependency graph (DAG)
- **`{{ source() }}`** — declares external/raw tables that dbt didn't create
- **`schema.yml`** — documents models and adds data quality tests (`unique`, `not_null`)
- **`dbt run`** — compiles and executes all SQL models
- **`dbt test`** — runs all data quality checks
- **`dbt build`** — run + test together, in dependency order

---

## Walkthrough progress

This project is being built as a front-to-end educational walkthrough.
Claude should explain WHY before showing code. One model at a time. Checkpoints at each layer.

### ✅ Completed
1. Understood `dbt_project.yml` and `profiles.yml`
2. Understood the 3-layer architecture and why it exists
3. Understood the data model design (3 raw tables, 3 attack patterns)
4. Built `data_generation/generate_data.py` — reads through phases A–E in the comments

### ⬜ Checkpoint 1 (user needs to do this)
Run the data generation script to populate DuckDB:
```bash
source ~/ae-env/bin/activate
cd "/Users/adamniebylski/Desktop/codecademy-git-test/Showcase_Projects/(CLICK-HERE)AnalyticsEngineeringPortfolio"
python data_generation/generate_data.py
```
Expected output: ~965 devices, ~11k login events, ~175k request logs.

### ⬜ Step 3 — Staging layer (next to build)
Files to create, in this order:
1. `netflix_security/models/staging/sources.yml` — declares raw tables as dbt sources
2. `netflix_security/models/staging/stg_login_events.sql`
3. `netflix_security/models/staging/stg_request_logs.sql`
4. `netflix_security/models/staging/stg_devices.sql`
5. `netflix_security/models/staging/schema.yml` — tests + docs for staging

Then run: `dbt run --select staging` (Checkpoint 2)

### ⬜ Step 4 — Intermediate layer
1. `int_user_login_summary.sql` — per-user failure rate, distinct IPs
2. `int_ip_request_summary.sql` — per-IP daily request volume
3. `int_device_fingerprint.sql` — devices enriched with login stats
4. `netflix_security/models/intermediate/schema.yml`

Then run: `dbt run --select intermediate` (Checkpoint 3)

### ⬜ Step 5 — Marts layer
1. `mart_ato_signals.sql`
2. `mart_credential_stuffing_signals.sql`
3. `mart_ddos_signals.sql`
4. `mart_device_ecosystem.sql`
5. `netflix_security/models/marts/schema.yml`

Then run: `dbt build` — runs all models + all 35 tests (Checkpoint 4)

### ⬜ Step 6 — Documentation
```bash
dbt docs generate && dbt docs serve
```
Opens a browser with the visual DAG (dependency graph). Key concept for AE interviews.

### ⬜ Step 7 — Evidence.dev dashboard (final phase)
SQL-based dashboard that deploys to a public URL for LinkedIn. Not started yet.

---

## Raw table schemas (for reference)

**raw_login_events**
| column | type | notes |
|---|---|---|
| event_id | VARCHAR | UUID primary key |
| user_id | INTEGER | 1–495 |
| ip_address | VARCHAR | IPv4 string |
| device_id | VARCHAR | UUID |
| event_timestamp | TIMESTAMP | within last 30 days |
| success | BOOLEAN | True = login succeeded |
| country_code | VARCHAR | 2-letter code |
| user_agent | VARCHAR | browser/app string |

**raw_request_logs**
| column | type | notes |
|---|---|---|
| request_id | VARCHAR | UUID primary key |
| ip_address | VARCHAR | |
| request_timestamp | TIMESTAMP | |
| endpoint | VARCHAR | e.g. /api/login |
| http_method | VARCHAR | GET or POST |
| status_code | INTEGER | 200, 404, 429, 503... |
| response_time_ms | INTEGER | milliseconds |
| user_agent | VARCHAR | |

**raw_devices**
| column | type | notes |
|---|---|---|
| device_id | VARCHAR | UUID |
| user_id | INTEGER | |
| device_type | VARCHAR | mobile/desktop/tablet/smart_tv |
| os | VARCHAR | iOS/Android/Windows/macOS/Linux |
| browser | VARCHAR | Chrome/Safari/Netflix App/etc. |
| first_seen_at | TIMESTAMP | |
| last_seen_at | TIMESTAMP | |
| is_trusted | BOOLEAN | first device per user = trusted |
