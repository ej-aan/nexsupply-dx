with parts as (
    select * from {{ ref('stg_erp__parts') }}
)

select
    part_sku,
    part_name,
    part_category,
    unit_cost_idr,
    target_lead_time_days
from parts