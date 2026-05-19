import pandas as pd
import numpy as np
import random
import uuid
import io
from datetime import datetime, timedelta
from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import DefaultAzureCredential

# ── Config ────────────────────────────────────────────────────────────
STORAGE_ACCOUNT = "walmartdata"
TODAY           = datetime.today().strftime("%Y-%m-%d")

random.seed(42)
np.random.seed(42)

# ── Master data ───────────────────────────────────────────────────────
STORES = [
    {"store_id": "WMART-MUM-042", "city": "Mumbai",    "region": "West",  "size": "Large"},
    {"store_id": "WMART-DEL-018", "city": "Delhi",     "region": "North", "size": "Large"},
    {"store_id": "WMART-BLR-031", "city": "Bengaluru", "region": "South", "size": "Medium"},
    {"store_id": "WMART-CHN-009", "city": "Chennai",   "region": "South", "size": "Medium"},
    {"store_id": "WMART-HYD-024", "city": "Hyderabad", "region": "South", "size": "Small"},
    {"store_id": "WMART-KOL-015", "city": "Kolkata",   "region": "East",  "size": "Medium"},
]

PRODUCTS = [
    {"sku": "SKU-DAIRY-001", "name": "Amul Gold Milk 1L",        "category": "Dairy",     "supplier_id": "SUP-AMUL-001",    "cost": 52.00,  "price": 68.00},
    {"sku": "SKU-DAIRY-002", "name": "Amul Butter 500g",         "category": "Dairy",     "supplier_id": "SUP-AMUL-001",    "cost": 210.00, "price": 260.00},
    {"sku": "SKU-DAIRY-003", "name": "Mother Dairy Curd 400g",   "category": "Dairy",     "supplier_id": "SUP-AMUL-001",    "cost": 38.00,  "price": 52.00},
    {"sku": "SKU-GROC-001",  "name": "Fortune Sunflower Oil 1L", "category": "Grocery",   "supplier_id": "SUP-ADANI-002",   "cost": 112.00, "price": 145.00},
    {"sku": "SKU-GROC-002",  "name": "India Gate Basmati 5kg",   "category": "Grocery",   "supplier_id": "SUP-KRBL-003",    "cost": 380.00, "price": 499.00},
    {"sku": "SKU-GROC-003",  "name": "Tata Salt 1kg",            "category": "Grocery",   "supplier_id": "SUP-TATA-011",    "cost": 18.00,  "price": 28.00},
    {"sku": "SKU-BVGR-001",  "name": "Coca-Cola 2L",             "category": "Beverages", "supplier_id": "SUP-COKE-004",    "cost": 68.00,  "price": 95.00},
    {"sku": "SKU-BVGR-002",  "name": "Red Bull 250ml",           "category": "Beverages", "supplier_id": "SUP-REDBULL-005", "cost": 95.00,  "price": 135.00},
    {"sku": "SKU-BVGR-003",  "name": "Bisleri Water 1L",         "category": "Beverages", "supplier_id": "SUP-BISLERI-012", "cost": 12.00,  "price": 20.00},
    {"sku": "SKU-SNCK-001",  "name": "Lays Classic 100g",        "category": "Snacks",    "supplier_id": "SUP-PEPSICO-006", "cost": 18.00,  "price": 30.00},
    {"sku": "SKU-SNCK-002",  "name": "Kurkure Masala 90g",       "category": "Snacks",    "supplier_id": "SUP-PEPSICO-006", "cost": 15.00,  "price": 25.00},
    {"sku": "SKU-CARE-001",  "name": "Colgate MaxFresh 150g",    "category": "Personal",  "supplier_id": "SUP-COLGATE-007", "cost": 78.00,  "price": 110.00},
    {"sku": "SKU-CARE-002",  "name": "Dove Soap 100g",           "category": "Personal",  "supplier_id": "SUP-HUL-008",     "cost": 42.00,  "price": 65.00},
    {"sku": "SKU-CLNG-001",  "name": "Surf Excel 1kg",           "category": "Cleaning",  "supplier_id": "SUP-HUL-008",     "cost": 168.00, "price": 220.00},
    {"sku": "SKU-CLNG-002",  "name": "Vim Dishwash Gel 500ml",   "category": "Cleaning",  "supplier_id": "SUP-HUL-008",     "cost": 65.00,  "price": 95.00},
    {"sku": "SKU-ELEC-001",  "name": "boAt Rockerz 450",         "category": "Electr.",   "supplier_id": "SUP-BOAT-009",    "cost": 850.00, "price": 1299.00},
    {"sku": "SKU-APRL-001",  "name": "Jockey Men T-Shirt",       "category": "Apparel",   "supplier_id": "SUP-JOCKEY-010",  "cost": 280.00, "price": 499.00},
]

SUPPLIERS = [
    {"supplier_id": "SUP-AMUL-001",    "name": "Amul Dairy Cooperative",  "contact": "amul@supply.in",    "lead_days": 2,  "city": "Anand"},
    {"supplier_id": "SUP-ADANI-002",   "name": "Adani Wilmar Ltd",        "contact": "adani@supply.in",   "lead_days": 3,  "city": "Ahmedabad"},
    {"supplier_id": "SUP-KRBL-003",    "name": "KRBL Limited",            "contact": "krbl@supply.in",    "lead_days": 4,  "city": "Delhi"},
    {"supplier_id": "SUP-COKE-004",    "name": "Coca-Cola India Pvt Ltd", "contact": "coke@supply.in",    "lead_days": 2,  "city": "Gurugram"},
    {"supplier_id": "SUP-REDBULL-005", "name": "Red Bull India",          "contact": "rb@supply.in",      "lead_days": 5,  "city": "Mumbai"},
    {"supplier_id": "SUP-PEPSICO-006", "name": "PepsiCo India Holdings",  "contact": "pepsi@supply.in",   "lead_days": 3,  "city": "Gurugram"},
    {"supplier_id": "SUP-COLGATE-007", "name": "Colgate-Palmolive India", "contact": "colgate@supply.in", "lead_days": 3,  "city": "Mumbai"},
    {"supplier_id": "SUP-HUL-008",     "name": "Hindustan Unilever Ltd",  "contact": "hul@supply.in",     "lead_days": 2,  "city": "Mumbai"},
    {"supplier_id": "SUP-BOAT-009",    "name": "Imagine Marketing Pvt",   "contact": "boat@supply.in",    "lead_days": 7,  "city": "Delhi"},
    {"supplier_id": "SUP-JOCKEY-010",  "name": "Page Industries Ltd",     "contact": "jockey@supply.in",  "lead_days": 5,  "city": "Bengaluru"},
    {"supplier_id": "SUP-TATA-011",    "name": "Tata Consumer Products",  "contact": "tata@supply.in",    "lead_days": 3,  "city": "Kolkata"},
    {"supplier_id": "SUP-BISLERI-012", "name": "Bisleri International",   "contact": "bis@supply.in",     "lead_days": 2,  "city": "Mumbai"},
]

# ── ADLS client ───────────────────────────────────────────────────────
def get_adls_client():
    credential = DefaultAzureCredential()
    return DataLakeServiceClient(
        account_url=f"https://{STORAGE_ACCOUNT}.dfs.core.windows.net",
        credential=credential
    )

def upload_parquet(client, df: pd.DataFrame, bronze_path: str):
    fs  = client.get_file_system_client("bronze")
    f   = fs.get_file_client(bronze_path)
    buf = io.BytesIO()
    df.to_parquet(buf, index=False, engine="pyarrow")
    buf.seek(0)
    f.upload_data(buf.read(), overwrite=True)
    print(f"    Uploaded → bronze/{bronze_path}  ({len(df):,} rows)")

# ─────────────────────────────────────────────────────────────────────
# GENERATOR 1 — Daily inventory snapshot
# Simulates what SAP/ERP dumps every night for each store × product
# ─────────────────────────────────────────────────────────────────────
def generate_inventory(run_date: str) -> pd.DataFrame:
    rows = []
    for store in STORES:
        for product in PRODUCTS:
            opening  = random.randint(50, 500)
            sold     = random.randint(10, min(opening, 150))
            received = random.randint(0, 200) if random.random() > 0.4 else 0
            closing  = opening - sold + received
            reorder  = random.randint(80, 120)

            rows.append({
                "snapshot_date":   run_date,
                "store_id":        store["store_id"],
                "store_city":      store["city"],
                "store_region":    store["region"],
                "store_size":      store["size"],
                "sku":             product["sku"],
                "product_name":    product["name"],
                "category":        product["category"],
                "supplier_id":     product["supplier_id"],
                "opening_stock":   opening,
                "units_sold":      sold,
                "units_received":  received,
                "closing_stock":   closing,
                "reorder_point":   reorder,
                "reorder_qty":     200,
                "cost_price":      product["cost"],
                "selling_price":   product["price"],
                "gross_margin_pct": round((product["price"] - product["cost"]) / product["price"] * 100, 2),
                "stock_status":    "LOW" if closing < reorder else "ADEQUATE",
                "warehouse_id":    f"WH-{store['region'][0]}-01",
                "ingest_date":     run_date,
                "source_system":   "ERP_SAP",
            })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────
# GENERATOR 2 — Supplier purchase orders
# Simulates daily PO feed from procurement system
# ─────────────────────────────────────────────────────────────────────
def generate_supplier_orders(run_date: str) -> pd.DataFrame:
    rows = []
    run_dt = datetime.strptime(run_date, "%Y-%m-%d")

    for supplier in SUPPLIERS:
        # Each supplier sends 3-8 orders per day
        supplier_products = [p for p in PRODUCTS if p["supplier_id"] == supplier["supplier_id"]]
        if not supplier_products:
            supplier_products = PRODUCTS[:2]

        for _ in range(random.randint(3, 8)):
            product  = random.choice(supplier_products)
            qty      = random.randint(100, 1000)
            unit_cost = round(product["cost"] * random.uniform(0.95, 1.05), 2)  # slight variance
            status   = random.choices(
                ["CONFIRMED", "PENDING", "DISPATCHED", "DELIVERED"],
                weights=[40, 20, 25, 15]
            )[0]

            rows.append({
                "order_id":           f"PO-{uuid.uuid4().hex[:8].upper()}",
                "order_date":         run_date,
                "supplier_id":        supplier["supplier_id"],
                "supplier_name":      supplier["name"],
                "supplier_city":      supplier["city"],
                "supplier_contact":   supplier["contact"],
                "sku":                product["sku"],
                "product_name":       product["name"],
                "category":           product["category"],
                "ordered_qty":        qty,
                "unit_cost":          unit_cost,
                "total_cost":         round(qty * unit_cost, 2),
                "lead_time_days":     supplier["lead_days"],
                "expected_delivery":  (run_dt + timedelta(days=supplier["lead_days"])).strftime("%Y-%m-%d"),
                "destination_wh":     random.choice(["WH-W-01","WH-N-01","WH-S-01","WH-E-01"]),
                "status":             status,
                "ingest_date":        run_date,
                "source_system":      "PROCUREMENT_SYSTEM",
            })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────
# GENERATOR 3 — CRM / loyalty customer profiles
# Simulates weekly CRM export — runs only on Mondays
# ─────────────────────────────────────────────────────────────────────
def generate_crm_profiles(run_date: str, num_customers: int = 2000) -> pd.DataFrame:
    cities     = [s["city"] for s in STORES]
    tiers      = ["Bronze", "Silver", "Gold", "Platinum"]
    categories = ["Dairy", "Grocery", "Beverages", "Snacks", "Electronics", "Apparel"]
    rows       = []

    for i in range(num_customers):
        join_dt       = datetime.today() - timedelta(days=random.randint(30, 1825))
        last_purchase = join_dt + timedelta(days=random.randint(1, 365))
        tier          = random.choices(tiers, weights=[50, 30, 15, 5])[0]
        lifetime      = round(random.uniform(500, 250000), 2)

        rows.append({
            "customer_id":          f"CUST-{7000000 + i}",
            "full_name":            f"Customer_{7000000 + i}",
            "email":                f"customer{7000000 + i}@email.com",
            "phone":                f"+91-{random.randint(7000000000, 9999999999)}",
            "city":                 random.choice(cities),
            "loyalty_tier":         tier,
            "loyalty_points":       random.randint(0, 50000),
            "join_date":            join_dt.strftime("%Y-%m-%d"),
            "last_purchase_date":   last_purchase.strftime("%Y-%m-%d"),
            "total_lifetime_spend": lifetime,
            "avg_basket_size":      round(lifetime / random.randint(5, 200), 2),
            "preferred_category":   random.choice(categories),
            "preferred_store_id":   random.choice(STORES)["store_id"],
            "is_active":            random.choices([True, False], weights=[80, 20])[0],
            "ingest_date":          run_date,
            "source_system":        "CRM_SALESFORCE",
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────
# MAIN — orchestrates all three generators
# ─────────────────────────────────────────────────────────────────────
def run_all(run_date: str = TODAY):
    print(f"\n{'='*55}")
    print(f"  Walmart Batch Data Generator")
    print(f"  Run date : {run_date}")
    print(f"{'='*55}\n")

    client = get_adls_client()

    # 1. Inventory snapshot — runs every day
    print("[1/3] Generating inventory snapshots...")
    inv_df = generate_inventory(run_date)
    print(f"    Rows     : {len(inv_df):,}")
    print(f"    Stores   : {inv_df['store_id'].nunique()}")
    print(f"    SKUs     : {inv_df['sku'].nunique()}")
    print(f"    LOW stock: {(inv_df['stock_status']=='LOW').sum()} items")
    upload_parquet(
        client, inv_df,
        f"batch/inventory/date={run_date}/inventory_snapshot.parquet"
    )

    # 2. Supplier orders — runs every day
    print("\n[2/3] Generating supplier orders...")
    sup_df = generate_supplier_orders(run_date)
    print(f"    Rows      : {len(sup_df):,}")
    print(f"    Suppliers : {sup_df['supplier_id'].nunique()}")
    print(f"    Total PO value : ₹{sup_df['total_cost'].sum():,.2f}")
    upload_parquet(
        client, sup_df,
        f"batch/supplier_orders/date={run_date}/supplier_orders.parquet"
    )

    # 3. CRM profiles — runs only on Mondays (weekly refresh)
    weekday = datetime.strptime(run_date, "%Y-%m-%d").weekday()
    if weekday == 0:
        print("\n[3/3] Generating CRM profiles (Monday refresh)...")
        crm_df = generate_crm_profiles(run_date, num_customers=2000)
        print(f"    Rows        : {len(crm_df):,}")
        print(f"    Active      : {crm_df['is_active'].sum():,}")
        print(f"    Tiers       : {crm_df['loyalty_tier'].value_counts().to_dict()}")
        upload_parquet(
            client, crm_df,
            f"batch/crm_profiles/date={run_date}/crm_profiles.parquet"
        )
    else:
        day_name = datetime.strptime(run_date, "%Y-%m-%d").strftime("%A")
        print(f"\n[3/3] CRM profiles skipped — today is {day_name} (runs Mondays only)")

    print(f"\n{'='*55}")
    print("  All generators complete!")
    print(f"  Check: Portal → walmartdatalake → bronze container")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    run_all()
 
#if __name__ == "__main__":
    # Temporarily pass a Monday date to test CRM generation
    #run_all(run_date="2024-05-20")   # 2024-05-20 was a Monday