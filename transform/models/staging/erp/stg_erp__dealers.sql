with source as (
    select * from {{ source('erp', 'raw_dealers') }}
),

renamed as (
    select
        cast(dealer_id as string) as dealer_id,
        trim(dealer_name) as dealer_name,
        trim(city) as city,
        trim(province) as province,
        trim(tier) as workshop_tier
    from source
)

select * from renamed