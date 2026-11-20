with orders as (
    select * from {{ ref('stg_erp__purchase_orders') }}
),

shipments as (
    select * from {{ ref('stg_erp__shipments') }}
),

parts as (
    select * from {{ ref('stg_erp__parts') }}
),

joined as (
    select
        orders.po_id,
        shipments.shipment_id,
        orders.dealer_id,
        orders.supplier_id,
        orders.part_sku,
        shipments.carrier_name,
        orders.order_date,
        orders.expected_delivery_date,
        shipments.actual_delivery_date,
        orders.quantity_ordered,
        shipments.quantity_delivered,
        parts.unit_cost_idr,
        
        -- Perhitungan Lead Time & Keterlambatan (Dalam Hari)
        date_diff(shipments.actual_delivery_date, orders.order_date, day) as actual_lead_time_days,
        date_diff(orders.expected_delivery_date, orders.order_date, day) as target_lead_time_days,
        date_diff(shipments.actual_delivery_date, orders.expected_delivery_date, day) as delay_days,
        
        -- Perhitungan Selisih Jumlah Barang
        (orders.quantity_ordered - shipments.quantity_delivered) as shortage_quantity,
        
        -- Perhitungan Nilai Finansial
        (orders.quantity_ordered * parts.unit_cost_idr) as total_order_value_idr,
        
        -- 1. Evaluasi On-Time (Tepat Waktu jika tgl tiba <= tgl estimasi)
        case 
            when shipments.actual_delivery_date <= orders.expected_delivery_date then 1 
            else 0 
        end as is_on_time,
        
        -- 2. Evaluasi In-Full (Lengkap jika jumlah tiba >= jumlah pesan)
        case 
            when shipments.quantity_delivered >= orders.quantity_ordered then 1 
            else 0 
        end as is_in_full

    from orders
    inner join shipments 
        on orders.po_id = shipments.po_id
    inner join parts 
        on orders.part_sku = parts.part_sku
),

final as (
    select
        *,
        -- 3. Evaluasi OTIF (Lolos HANYA JIKA Tepat Waktu DAN Lengkap Sekaligus!)
        case 
            when is_on_time = 1 and is_in_full = 1 then 1 
            else 0 
        end as is_otif,
        
        -- Nilai Finansial yang Tertahan/Berisiko akibat Keterlambatan
        case 
            when is_on_time = 0 then total_order_value_idr 
            else 0 
        end as delayed_capital_risk_idr

    from joined
)

select * from final