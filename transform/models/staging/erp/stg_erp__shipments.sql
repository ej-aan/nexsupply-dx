with source as (
    select * from {{ source('erp', 'raw_shipments') }}
),

renamed as (
    select
        cast(shipment_id as string) as shipment_id,
        cast(po_id as string) as po_id,
        trim(carrier_name) as carrier_name,
        cast(actual_delivery_date as date) as actual_delivery_date,
        cast(quantity_delivered as int64) as quantity_delivered,
        trim(transit_status) as transit_status
    from source
)

select * from renamed