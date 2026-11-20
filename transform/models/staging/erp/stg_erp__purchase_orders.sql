with source as (
    select * from {{ source('erp', 'raw_purchase_orders') }}
),

renamed as (
    select
        cast(po_id as string) as po_id,
        cast(dealer_id as string) as dealer_id,
        cast(part_sku as string) as part_sku,
        cast(supplier_id as string) as supplier_id,
        cast(order_date as date) as order_date,
        cast(expected_delivery_date as date) as expected_delivery_date,
        cast(quantity_ordered as int64) as quantity_ordered
    from source
)

select * from renamed