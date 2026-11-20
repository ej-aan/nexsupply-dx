with source as (
    select * from {{ source('erp', 'raw_suppliers') }}
),

renamed as (
    select
        cast(supplier_id as string) as supplier_id,
        trim(supplier_name) as supplier_name,
        trim(country_origin) as country_origin,
        cast(sla_rating as int64) as supplier_sla_rating
    from source
)

select * from renamed