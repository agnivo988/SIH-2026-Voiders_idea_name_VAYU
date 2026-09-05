# VAYU

## Real-Time Indian Airfare Price Index

VAYU is an airfare data intelligence platform built for **Smart India Hackathon 2026**. It studies domestic Indian airfares at route, airline, and booking-window level, then turns those observations into an interpretable Airfare Price Index.

The project is designed around a simple question:

> How are domestic airfares changing, and what is driving that change?

VAYU combines a FastAPI data service, PostgreSQL/Supabase, a cleaning and index pipeline, and a Next.js dashboard. The dashboard is not driven by hardcoded numbers. Its KPIs and charts are fetched from the backend and calculated from stored fare observations.

> **Current prototype status:** the connected database contains a clearly labelled synthetic prototype dataset. The system is ready for approved data imports and permitted live-source adapters, but it does not claim that the current records are live government or airline data.

---

## Why This Matters

Airfare data is dynamic, fragmented, and difficult to compare over time. A fare can change because of:

- booking lead time
- route demand
- day of the week
- airline pricing behaviour
- taxes and airport charges
- limited seat availability
- seasonal travel patterns

Most public discussions focus on individual ticket prices. VAYU looks at the larger movement across a configurable basket of Indian domestic routes.

The platform is intended as an economic data prototype, not simply a flight-search scraper.

---

## What VAYU Does

- Stores fare observations in PostgreSQL or Supabase
- Supports route and airline master data
- Keeps base fare, taxes, airport charges, convenience fees, and other fees separate
- Validates and rejects invalid fare records
- Detects duplicates and configurable outliers
- Calculates representative route fares using medians
- Calculates a configurable composite Airfare Price Index
- Analyses booking lead time from T+1 through T+45
- Compares airline fare levels
- Ranks route volatility
- Finds short-term price surges
- Provides a flight comparison and lowest-observed-fare recommendation
- Exposes a documented REST API through FastAPI
- Includes a dedicated CPI/APIx calculation endpoint
- Shows data quality and source status
- Provides an ethical live-source adapter interface
- Supports CSV imports for large approved datasets
- Includes a responsive Next.js dashboard

---

## Product Name

**VAYU** is the user-facing name of the dashboard.

The index is referred to in the implementation as APIx, short for Airfare Price Index. It is a prototype index methodology, not a claim to reproduce the official Consumer Price Index.

---

## Architecture

```text
                 Approved data sources
                 Airline APIs / permitted feeds
                              |
                              v
                 +--------------------------+
                 | Source adapters           |
                 | CSV import / API / demo   |
                 +-------------+------------+
                               |
                               v
                 +--------------------------+
                 | Validation and cleaning   |
                 | Currency, fares, quality  |
                 +-------------+------------+
                               |
                               v
                 +--------------------------+
                 | PostgreSQL / Supabase     |
                 | Fare observations         |
                 | Routes and airlines      |
                 +-------------+------------+
                               |
                +--------------+--------------+
                |                             |
                v                             v
      +-------------------+          +-------------------+
      | Index and analytics|          | FastAPI REST API  |
      | CPI/APIx, lead time|          | OpenAPI / JSON    |
      | volatility, surges |          +---------+---------+
      +-------------------+                    |
                                               v
                                  +------------------------+
                                  | VAYU Next.js dashboard |
                                  +------------------------+
```

The repository is a small monorepo:

```text
.
├── backend/
│   ├── app/
│   │   ├── api/                  FastAPI route modules
│   │   ├── services/             Demo, cleaning, index, scraper services
│   │   ├── alembic/              Database migration files
│   │   ├── config.py             Environment-based settings
│   │   ├── database.py           SQLAlchemy engine and sessions
│   │   ├── models.py             Database models
│   │   └── main.py               FastAPI application
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/app/                  Next.js pages
│   ├── src/components/           Shared dashboard components
│   ├── src/lib/                  API client helpers
│   └── package.json
├── scripts/
│   ├── import_fares.py           Batch CSV importer
│   ├── create_prototype_csv.py   Reproducible prototype CSV generator
│   ├── load_prototype_data.py    Prototype data loader
│   ├── recalculate_index.py      Database-backed index recalculation
│   └── seed_database.py           Optional offline demo seeder
├── data/demo/                    Local demo data, ignored by Git
├── alembic.ini
├── docker-compose.yml
└── README.md
```

---

## Technology

### Backend

- Python 3.12+
- FastAPI
- SQLAlchemy 2
- Pydantic Settings
- PostgreSQL with Psycopg 3
- Alembic
- APScheduler
- HTTPX
- pytest

### Frontend

- Next.js App Router
- TypeScript
- Tailwind CSS
- Lucide icons
- Native SVG data visualisations

### Database

- Supabase PostgreSQL for the deployed prototype
- SQLite as the local fallback when no `.env` database URL is supplied

---

## Current Data Model

The main tables are:

- `routes`
- `airlines`
- `sources`
- `fare_quotes`
- `index_values`
- `route_index_values`
- `benchmark_values`
- `scrape_runs`

Each fare observation preserves its components:

```text
base_fare
+ taxes
+ airport_fee
+ convenience_fee
+ other_fees
= total_fare
```

A fare record also stores its route, airline, travel date, advance booking days, flight number, availability, collection timestamp, source, and quality flags.

---

## Local Setup

### Requirements

Install:

- Python 3.12 or newer
- Node.js 20 or newer
- npm
- A PostgreSQL/Supabase connection for real stored data

### 1. Clone the repository

```bash
git clone https://github.com/agnivo988/SIH-2026-Voiders.git
cd SIH-2026-Voiders
```

### 2. Install backend dependencies

```bash
python3 -m pip install -r backend/requirements.txt
```

### 3. Configure the backend

Create a local `.env` file in the repository root:

```bash
cp .env.example .env
```

For Supabase, set a pooler connection string:

```env
DATABASE_URL=postgresql://postgres.PROJECT_REF:URL_ENCODED_PASSWORD@POOLER_HOST:5432/postgres?sslmode=require
DEMO_MODE=false
ENABLE_LIVE_SCRAPING=false
FRONTEND_URL=http://localhost:3000
ADMIN_API_KEY=change-this-value
```

Use a URL-encoded password. For example:

```text
@  becomes  %40
#  becomes  %23
$  becomes  %24
```

Never commit `.env` or database credentials.

### 4. Apply the schema

```bash
alembic upgrade head
```

### 5. Start the backend

```bash
PYTHONPATH=backend uvicorn app.main:app --reload --app-dir backend
```

The API will be available at:

- http://localhost:8000
- http://localhost:8000/docs
- http://localhost:8000/api/health

### 6. Start the frontend

In another terminal:

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

Create `frontend/.env.local` if the API is not running on the default URL:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Open:

```text
http://localhost:3000
```

---

## Dashboard Pages

The VAYU dashboard contains:

- `/` - overview and current index
- `/cpi` - dedicated CPI/APIx calculation and methodology page
- `/routes` - configured route basket
- `/compare` - fare comparison and recommendation
- `/lead-time` - booking-window analysis
- `/airlines` - airline comparison
- `/volatility` - route volatility rankings
- `/data-quality` - data quality summary

The left navigation can be collapsed. All links are regular application routes and are available on desktop and mobile layouts.

---

## API Endpoints

### Health and index

```text
GET  /api/health
GET  /api/index/current
GET  /api/index/daily
GET  /api/cpi/current
POST /api/cpi/calculate
```

### Reference data

```text
GET /api/routes
GET /api/routes/{route_code}
GET /api/airlines
GET /api/sources
```

### Fare data and analysis

```text
GET /api/fares
GET /api/analytics/lead-time
GET /api/analytics/airlines
GET /api/analytics/volatility
GET /api/analytics/price-surge
GET /api/data-quality
```

### Flight comparison

```text
GET /api/recommendations?route=DEL-BOM&advance_days=7&limit=10
```

The recommendation endpoint ranks available stored observations by total fare. It is a decision-support result, not a booking guarantee. Users should verify the final fare and availability with the source before purchasing.

Interactive API documentation is available at `/docs` when the backend is running.

---

## APIx / CPI Methodology

The current prototype uses a configurable route basket and configurable route weights.

For each route and day:

```text
representative fare = median(usable fare observations)
```

For each route:

```text
price relative = current representative fare
                 / base-period representative fare
                 × 100
```

The composite index is:

```text
APIx = Σ(normalized route weight × route price relative)
```

The base period is the first seven available days in the stored dataset, with a base index of 100.

These are prototype weights for demonstration. They are not official NSO weights and the method does not claim to reproduce the official CPI methodology.

---

## Loading Real Data

For a large approved dataset, use the CSV importer. The importer works with Supabase/PostgreSQL and inserts records in batches.

Required CSV columns:

```text
route_code
airline_code
travel_date
advance_days
flight_number
fare_class
base_fare
taxes
airport_fee
convenience_fee
other_fees
total_fare
currency
available
collected_at
raw_reference
```

Import a file:

```bash
PYTHONPATH=backend python3 scripts/import_fares.py fares.csv \
  --source "Approved Data Import" \
  --batch-size 5000
```

The importer:

- checks required columns
- validates positive fare values
- checks that total fare matches fare components
- resolves route and airline foreign keys
- inserts in batches
- skips records with an existing `raw_reference`
- records imported data as non-demo data unless `--demo` is supplied

After loading new observations, recalculate the index:

```bash
PYTHONPATH=backend python3 scripts/recalculate_index.py
```

### Optional prototype data

Synthetic data is never generated automatically when `DEMO_MODE=false`.

To create the reproducible prototype dataset explicitly:

```bash
DEMO_MODE=true PYTHONPATH=backend python3 scripts/load_prototype_data.py
```

The prototype loader creates a 30-day dataset across 10 routes, 5 airlines, and five advance windows. It is useful for demonstrations and testing only.

---

## Ethical Data Collection

VAYU is designed to use permitted sources responsibly.

The system does not:

- solve CAPTCHAs
- bypass bot detection
- defeat authentication
- use stolen credentials
- evade access controls
- ignore robots.txt or source restrictions
- send aggressive request traffic
- claim access to live data when only demo data exists

The live adapter supports conservative request delays, timeouts, retries, caching, and explicit blocked-source states. A source returning an access denial is treated as blocked and the pipeline continues without attempting to bypass it.

Live collection should only be enabled after the source owner has permitted the integration and supplied an approved API or public data contract.

---

## Supabase Deployment

1. Create a Supabase project.
2. Open **Connect** and select the **Session pooler** connection string.
3. URL-encode the database password.
4. Set `DATABASE_URL` in the backend deployment environment.
5. Run:

```bash
alembic upgrade head
```

6. Load approved data with `scripts/import_fares.py`.
7. Recalculate the index with `scripts/recalculate_index.py`.

The frontend does not connect directly to Supabase. It calls the FastAPI backend, which reads from PostgreSQL.

---

## Render Backend Deployment

Create a Render **Web Service** from the repository.

If the Render root directory is the repository root:

```text
Build command: pip install -r backend/requirements.txt
Start command: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend
```

If the Render root directory is `backend`:

```text
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set these environment variables in Render:

```env
DATABASE_URL=your_supabase_pooler_connection_string
DEMO_MODE=false
ENABLE_LIVE_SCRAPING=false
FRONTEND_URL=https://your-frontend-domain
ADMIN_API_KEY=your-strong-admin-key
```

Test after deployment:

```text
https://your-render-service.onrender.com/api/health
https://your-render-service.onrender.com/docs
```

The backend must bind to `0.0.0.0` and use Render's `$PORT` value. Do not use `--reload` in production.

---

## Vercel Frontend Deployment

Create a Vercel project from the same repository.

Set the frontend root directory to:

```text
frontend
```

Set the environment variable:

```env
NEXT_PUBLIC_API_URL=https://your-render-service.onrender.com
```

Deploy the frontend, then set the resulting Vercel URL as the backend's `FRONTEND_URL` value. This is required for browser CORS requests.

---

## Testing

Run backend tests:

```bash
PYTHONPATH=backend pytest -q backend/tests
```

Compile-check backend modules:

```bash
python3 -m compileall -q backend/app scripts
```

Build the frontend:

```bash
npm --prefix frontend run build
```

The test suite covers demo reproducibility, fare cleaning, index calculation, adapter behaviour, and blocked live-source behaviour.

---

## Docker

The repository includes Dockerfiles and a `docker-compose.yml` for local container development. The intended services are:

- PostgreSQL
- FastAPI backend
- Next.js frontend

For hosted deployment, Render and Vercel are the recommended split: Render for the API and Vercel for the Next.js application, with Supabase as the database.

---

## Prototype Limitations

The current SIH prototype should be evaluated with these boundaries in mind:

- the loaded dataset is synthetic and labelled accordingly
- prototype route weights are configurable, not official statistical weights
- live fare collection requires an approved source contract
- the recommendation ranks stored observations and does not book tickets
- benchmark comparison requires an imported benchmark dataset
- the current prototype focuses on domestic route-level intelligence

These limitations are deliberate. The architecture separates source adapters, cleaning, storage, analytics, and presentation so approved real data can replace the prototype import without rebuilding the platform.

---

## Team and Context

Built for **Smart India Hackathon 2026** as a working prototype for economic data intelligence in Indian domestic aviation.

VAYU's goal is to make airfare movement easier to observe, explain, validate, and consume through both a dashboard and an API.
