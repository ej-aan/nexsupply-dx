with suppliers as (
    select * from {{ ref('stg_erp__suppliers') }}
)

select
    supplier_id,
    supplier_name,
    country_origin,
    supplier_sla_rating
from suppliers