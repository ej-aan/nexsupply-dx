import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# 1. SETUP AUTENTIKASI DENGAN GOOGLE CLOUD
KEY_PATH = os.path.join(os.path.dirname(__file__), "..", "credentials", "gcp_key.json")
if not os.path.exists(KEY_PATH):
    raise FileNotFoundError(f"❌ Berkas kunci tidak ditemukan di: {KEY_PATH}")

credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

PROJECT_ID = client.project
DATASET_ID = "nexsupply_raw"
DATASET_REF = f"{PROJECT_ID}.{DATASET_ID}"

print(f"🔗 Terhubung ke Google Cloud Project: {PROJECT_ID}")

# 2. BUAT DATASET DI BIGQUERY JIKA BELUM ADA
dataset = bigquery.Dataset(DATASET_REF)
dataset.location = "asia-southeast2"  # Region Jakarta (Super cepat!)
try:
    client.create_dataset(dataset, exists_ok=True)
    print(f"📦 Dataset BigQuery '{DATASET_REF}' siap digunakan.")
except Exception as e:
    # Fallback ke US jika region Jakarta dibatasi pada akun sandbox tertentu
    dataset.location = "US"
    client.create_dataset(dataset, exists_ok=True)
    print(f"📦 Dataset BigQuery '{DATASET_REF}' siap di region US.")

# 3. GENERATE MASTER DATA: DEALERS
print("\n🏭 [1/5] Membuat data Master Dealers (Bengkel Resmi)...")
dealers_data = [
    ("DLR-01", "NexAuto Cilandak", "Jakarta Selatan", "DKI Jakarta", "Tier-1"),
    ("DLR-02", "NexAuto Salemba", "Jakarta Pusat", "DKI Jakarta", "Tier-1"),
    ("DLR-03", "NexAuto BSD City", "Tangerang Selatan", "Banten", "Tier-1"),
    ("DLR-04", "NexAuto Surabaya Kertajaya", "Surabaya", "Jawa Timur", "Tier-1"),
    ("DLR-05", "NexAuto Surabaya HR Muhammad", "Surabaya", "Jawa Timur", "Tier-1"),
    ("DLR-06", "NexAuto Bandung Pasteur", "Bandung", "Jawa Barat", "Tier-1"),
    ("DLR-07", "NexAuto Semarang Pandanaran", "Semarang", "Jawa Tengah", "Tier-2"),
    ("DLR-08", "NexAuto Medan Amplas", "Medan", "Sumatera Utara", "Tier-2"),
    ("DLR-09", "NexAuto Makassar Urip", "Makassar", "Sulawesi Selatan", "Tier-2"),
    ("DLR-10", "NexAuto Balikpapan Sudirman", "Balikpapan", "Kalimantan Timur", "Tier-2"),
]
df_dealers = pd.DataFrame(dealers_data, columns=["dealer_id", "dealer_name", "city", "province", "tier"])

# 4. GENERATE MASTER DATA: SUPPLIERS
print("🏭 [2/5] Membuat data Master OEM Suppliers...")
suppliers_data = [
    ("SUP-01", "PT Filtrexa Komponen Indonesia", "Indonesia", 95),
    ("SUP-02", "PT Drivora Powertrain Indonesia", "Indonesia", 92),
    ("SUP-03", "PT Brakelin Indonesia", "Indonesia", 88),
    ("SUP-04", "PT Suspenta Indonesia", "Indonesia", 85),
    ("SUP-05", "PT Voltara Energi Indonesia", "Indonesia", 90),
    ("SUP-06", "Kaizora Chemical Co., Ltd.", "Japan", 98),
    ("SUP-07", "Tsubara Filter Co., Ltd.", "Japan", 97),
]
df_suppliers = pd.DataFrame(suppliers_data, columns=["supplier_id", "supplier_name", "country_origin", "sla_rating"])

# 5. GENERATE MASTER DATA: SPARE PARTS CATALOG
print("🔩 [3/5] Membuat Katalog Suku Cadang (Spare Parts)...")
parts_data = [
    ("SKU-001", "Oil Filter Element", "Fast Moving", 45000, 3),
    ("SKU-002", "Brake Pad Front Set", "Fast Moving", 450000, 5),
    ("SKU-003", "Brake Shoe Rear", "Fast Moving", 320000, 5),
    ("SKU-004", "Iridium Spark Plug", "Fast Moving", 110000, 4),
    ("SKU-005", "Air Cleaner Filter", "Fast Moving", 85000, 3),
    ("SKU-006", "Battery MF 55D23L", "Critical", 1250000, 4),
    ("SKU-007", "Shock Absorber Front", "Critical", 850000, 7),
    ("SKU-008", "Shock Absorber Rear", "Critical", 650000, 7),
    ("SKU-009", "Timing Belt Kit", "Medium Moving", 750000, 10),
    ("SKU-010", "Water Pump Assembly", "Critical", 920000, 12),
    ("SKU-011", "Radiator Coolant Super Long Life", "Fast Moving", 135000, 3),
    ("SKU-012", "Clutch Disc Assembly", "Medium Moving", 850000, 8),
]
df_parts = pd.DataFrame(parts_data, columns=["part_sku", "part_name", "category", "unit_cost_idr", "target_lead_time_days"])

# 6. GENERATE TRANSACTION DATA: PURCHASE ORDERS & SHIPMENTS (10.000 Records)
print("📦 [4/5] Membuat 10.000 riwayat transaksi pesanan & logistik...")
np.random.seed(42)
n_orders = 10000

start_date = datetime(2025, 1, 1)
order_dates = [start_date + timedelta(days=int(np.random.randint(0, 365))) for _ in range(n_orders)]

po_ids = [f"PO-2025-{10000 + i}" for i in range(n_orders)]
order_dealers = np.random.choice(df_dealers["dealer_id"], size=n_orders)
order_parts = np.random.choice(df_parts["part_sku"], size=n_orders)

# Tentukan supplier berdasarkan jenis suku cadang
sku_to_supplier = {
    "SKU-001": "SUP-01", "SKU-004": "SUP-01",
    "SKU-002": "SUP-03", "SKU-003": "SUP-03",
    "SKU-007": "SUP-04", "SKU-008": "SUP-04",
    "SKU-006": "SUP-05",
    "SKU-009": "SUP-02", "SKU-010": "SUP-02", "SKU-012": "SUP-02",
    "SKU-005": "SUP-07", "SKU-011": "SUP-06"
}
order_suppliers = [sku_to_supplier[sku] for sku in order_parts]

# Jumlah pesanan
quantities_ordered = np.random.choice([10, 20, 50, 100, 200], size=n_orders, p=[0.3, 0.3, 0.2, 0.15, 0.05])

# Expected Delivery Date (Berdasarkan target lead time + buffer)
sku_target_days = dict(zip(df_parts["part_sku"], df_parts["target_lead_time_days"]))
expected_dates = [
    od + timedelta(days=int(sku_target_days[sku] + np.random.choice([0, 1, 2])))
    for od, sku in zip(order_dates, order_parts)
]

df_orders = pd.DataFrame({
    "po_id": po_ids,
    "dealer_id": order_dealers,
    "part_sku": order_parts,
    "supplier_id": order_suppliers,
    "order_date": [d.strftime("%Y-%m-%d") for d in order_dates],
    "expected_delivery_date": [d.strftime("%Y-%m-%d") for d in expected_dates],
    "quantity_ordered": quantities_ordered
})

# Logistik & Pengiriman Riil
carriers = ["Kirimex Logistics", "Arunaline Freight", "Nusaway Express", "Lintasra Logistics"]
actual_lead_times = []
quantities_delivered = []
transit_statuses = []

for od, ed, qty in zip(order_dates, expected_dates, quantities_ordered):
    # Simulasi keterlambatan realistis:
    # 75% tepat waktu, 25% terlambat karena bottleneck rute
    is_delayed = np.random.rand() < 0.25
    delay_days = np.random.randint(1, 8) if is_delayed else 0
    
    target_days = (ed - od).days
    actual_days = max(1, target_days + delay_days - np.random.choice([0, 1]))
    actual_lead_times.append(actual_days)
    
    # In-Full delivery: 85% barang lengkap, 15% kekurangan stok (shortage)
    is_shortage = np.random.rand() < 0.15
    delivered_qty = int(qty * np.random.uniform(0.7, 0.95)) if is_shortage else qty
    quantities_delivered.append(delivered_qty)
    transit_statuses.append("DELIVERED")

actual_delivery_dates = [
    od + timedelta(days=int(alt))
    for od, alt in zip(order_dates, actual_lead_times)
]

df_shipments = pd.DataFrame({
    "shipment_id": [f"SHP-2025-{10000 + i}" for i in range(n_orders)],
    "po_id": po_ids,
    "carrier_name": np.random.choice(carriers, size=n_orders),
    "actual_delivery_date": [d.strftime("%Y-%m-%d") for d in actual_delivery_dates],
    "quantity_delivered": quantities_delivered,
    "transit_status": transit_statuses
})

# 7. UPLOAD KE GOOGLE BIGQUERY
print("\n☁️ [5/5] Mengunggah tabel ke Google BigQuery...")

def upload_to_bq(df, table_name):
    table_ref = f"{DATASET_REF}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE"  # Timpa jika sudah ada agar selalu fresh
    )
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()  # Tunggu upload selesai
    print(f"  ✅ Sukses: {table_ref} ({len(df):,} baris)")

upload_to_bq(df_dealers, "raw_dealers")
upload_to_bq(df_suppliers, "raw_suppliers")
upload_to_bq(df_parts, "raw_parts")
upload_to_bq(df_orders, "raw_purchase_orders")
upload_to_bq(df_shipments, "raw_shipments")

print("\n🎉 SELAMAT! Seluruh data mentah rantai pasok berhasil mendarat di Google BigQuery Cloud!")