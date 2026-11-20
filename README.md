# NexSupply-DX: Spare-Parts Delivery Analytics with BigQuery and dbt

An analytics engineering project that measures how reliably spare parts reach car workshops: on time, in full, and at what cost when they don't. Synthetic data is loaded into Google BigQuery, modelled with dbt into a star schema, tested, and visualised in Looker Studio.

> All data and company names in this project are fictional. See [The data](#the-data).

## Business problem

Authorised car workshops depend on spare parts arriving on time and in full. When a part arrives late or short, a customer's car waits and service revenue is lost. A logistics operations manager needs to know how often deliveries fail, and whether the failures come from particular carriers or suppliers.

NexSupply-DX measures this with **OTIF (On-Time In-Full)**, a standard supply-chain KPI: the share of orders that arrive both by the promised date and in the full quantity. It also tracks on-time and in-full rates separately, delay days, shortages, and the value of orders that arrived late.

## Architecture

```
Python script (ingestion/generate_and_load.py)
        |  generates synthetic data and loads it
        v
BigQuery dataset: nexsupply_raw        5 raw tables, loaded as-is
        |
        |  dbt run  (all steps below run as SQL inside BigQuery)
        v
Staging views (stg_erp__*)              clean types, trim text, rename columns
        v
Intermediate view (int_order_fulfillment_calculated)
                                        join orders, shipments and parts;
                                        calculate lead times, delays and OTIF flags
        v
Mart tables (fct_ and dim_)             star schema, stored as tables
        |
        |  dbt test  (16 data quality tests)
        v
Looker Studio dashboard                 connected directly to the mart tables
```

This is an **ELT** pipeline: the data is loaded into the warehouse first, and dbt transforms it there with SQL. Staging and intermediate models are views; marts are tables so the dashboard queries them quickly. These settings live in `transform/dbt_project.yml`.

## The data

All data is synthetic, and all company names are fictional. Real supply-chain data is confidential, so a Python script generates 10,000 spare-part orders and their shipments for 2025, along with master data for 10 dealers, 7 suppliers, 12 parts and 4 carriers.

The simulation makes about **25% of shipments late** (by 1 to 7 days) and about **15% short** (70 to 95% of the ordered quantity). A fixed random seed (`np.random.seed(42)`) makes every run produce identical data, so anyone can reproduce the results.

| Raw table | Contents |
| --- | --- |
| `raw_dealers` | Workshop locations, city, province, tier |
| `raw_suppliers` | Supplier name, country, promised SLA rating |
| `raw_parts` | Part catalogue, category, unit cost, target lead time |
| `raw_purchase_orders` | Order date, expected delivery date, quantity ordered |
| `raw_shipments` | Carrier, actual delivery date, quantity delivered |

## Data model and KPIs

The mart layer is a star schema.

- **`fct_order_fulfillment`**: one row per order and its shipment. Keys to dealer, supplier and part; carrier; order, expected and actual delivery dates; quantities; lead times; delay days; order value; and the KPI flags below.
- **`dim_dealers`**, **`dim_suppliers`**, **`dim_parts`**: descriptive attributes for slicing the facts.

| KPI | Definition |
| --- | --- |
| On-time flag | 1 if the actual delivery date is on or before the expected date, else 0 |
| In-full flag | 1 if the quantity delivered is at least the quantity ordered, else 0 |
| OTIF flag | 1 only if both flags above are 1, else 0 |
| OTIF % | Average of the OTIF flag across orders (share of orders passing both checks) |
| Delay days | Actual delivery date minus expected delivery date (negative means early) |
| Shortage quantity | Quantity ordered minus quantity delivered |
| Delayed capital risk | Total order value of orders that arrived late |

## Data quality

`dbt test` runs 16 tests, all passing:

- `unique` and `not_null` on every dimension key and on the fact table's surrogate key
- `not_null` on the fact table's dealer, supplier and part keys, and on unit cost
- `relationships` tests confirming every fact row links to an existing dealer, supplier and part
- `accepted_values` confirming the OTIF flag is only ever 0 or 1

## Dashboard

![Dashboard screenshot](docs/dashboard.png)

Live dashboard: [https://datastudio.google.com/reporting/e5f41b4d-070e-440b-89a2-2821b05801d6]

The dashboard shows five KPI cards (OTIF %, on-time %, in-full %, total order value, delayed capital risk), monthly OTIF, on-time % by carrier, in-full % against SLA by supplier, and a table of the most delayed orders, with a date filter.

**Results on the full year** (synthetic data, so these demonstrate the pipeline rather than real-world insight):

- OTIF is **65.5%**: on-time 77.7%, in-full 84.4%. This matches what the simulation settings predict, which confirms the calculations are correct.
- **Every supplier delivers below its SLA promise.** The supplier promising 98 delivers about 84% in full.
- About **Rp 51.7 billion of Rp 236.4 billion** in order value (22%) arrived late.
- Carriers differ by only a few points (about 75 to 79% on time). With random generation that's expected noise, not a real performance difference.

## How to run it

Requirements: Python 3.10+, a Google Cloud project with BigQuery enabled, and a service account key with BigQuery access. Credentials are **not** included in this repository.

1. Create and activate a virtual environment, then install the dependencies:
   ```
   python -m venv .venv
   .venv\Scripts\activate        # Windows; on macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Save your service account key as `credentials/gcp_key.json`.
3. In `transform/profiles.yml`, set `project` to your own Google Cloud project ID.
4. Generate and load the raw data:
   ```
   python ingestion/generate_and_load.py
   ```
5. Build and test the models:
   ```
   cd transform
   dbt run
   dbt test
   ```

Note: in BigQuery's free sandbox, tables expire after 60 days. Rerun steps 4 and 5 to rebuild them.

## Limitations and what I learned

**Limitations**

- The data is synthetic and comes from a single generated source, so it is cleaner than real-world data. Real pipelines combine many sources, where duplicates, conflicting records and the lack of a single source of truth can produce misleading insights. Staging and tests become much more important there.
- Delays and shortages are random, so the project cannot show real patterns or root causes. It demonstrates the pipeline, the model and the KPIs.
- There is no scheduler: the pipeline is run by hand. A production version would use an orchestrator.
- There is no inventory or parts-usage data, so the project measures delivery performance, not stock levels.

**What I learned**

- Loading data from Python into BigQuery, and why an ELT approach lets dbt transform data where it already sits.
- Structuring dbt models in layers (staging, intermediate, marts) so that cleaning, business logic and serving each happen in one place.
- Defining a KPI at the right grain: OTIF must be decided per order first, then averaged, or the result is inflated.
- Writing data quality tests (unique, not_null, relationships, accepted_values) to keep the warehouse consistent.
- Building a Looker Studio dashboard on BigQuery, and checking that its numbers match the SQL results.

## Tech stack

Python (pandas, NumPy) · Google BigQuery · dbt Core · Looker Studio · Git
