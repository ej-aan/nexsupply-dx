with fulfillment as (
    select * from {{ ref('int_order_fulfillment_calculated') }}
)

select
    -- Surrogate Key unik untuk setiap baris fakta
    to_hex(md5(concat(po_id, '-', shipment_id))) as fulfillment_key,
    
    -- Foreign Keys (Menghubungkan ke Tabel Dimensi)
    po_id,
    shipment_id,
    dealer_id,
    supplier_id,
    part_sku,
    carrier_name,
    
    -- Dimensi Tanggal
    order_date,
    expected_delivery_date,
    actual_delivery_date,
    
    -- Metrik Kuantitatif Rantai Pasok
    quantity_ordered,
    quantity_delivered,
    shortage_quantity,
    actual_lead_time_days,
    target_lead_time_days,
    delay_days,
    
    -- Metrik Finansial
    unit_cost_idr,
    total_order_value_idr,
    delayed_capital_risk_idr,
    
    -- Indikator Performa Utama (KPI)
    is_on_time,
    is_in_full,
    is_otif

from fulfillment