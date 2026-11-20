with source as (
    select * from {{ source('erp', 'raw_parts') }}
),

renamed as (
    select
        cast(part_sku as string) as part_sku,
        trim(part_name) as part_name,
        trim(category) as part_category,
        cast(unit_cost_idr as numeric) as unit_cost_idr,
        cast(target_lead_time_days as int64) as target_lead_time_days
    from source
)

select * from renamed