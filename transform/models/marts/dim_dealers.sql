with dealers as (
    select * from {{ ref('stg_erp__dealers') }}
)

select
    dealer_id,
    dealer_name,
    city,
    province,
    workshop_tier
from dealers