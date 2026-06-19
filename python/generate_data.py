"""
generate_data.py
Generates synthetic banking data for the Customer Intelligence Platform.
Output: 1,000 customers and ~150,000 transactions across 24 months.
Run from the project root: python python/generate_data.py
"""

import logging
import random
import warnings
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Reproducibility ────────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker("en_GB")
Faker.seed(SEED)

# ── Portfolio Configuration ────────────────────────────────────────────────────
N_CUSTOMERS   = 1_000
N_MONTHS      = 24
SNAPSHOT_DATE = date(2024, 1, 31)
START_DATE    = date(2022, 2, 1)   # 24 months before snapshot

SEGMENT_COUNTS = {
    "VIP":     80,
    "Growth":  150,
    "Regular": 450,
    "At-Risk": 180,
    "Dormant": 140,
}
TOP_VIP_N = 10   # First N VIP customers are super-clients (drive concentration)

REGIONS = ["London", "Manchester", "Birmingham", "Leeds", "Edinburgh", "Bristol"]

CUSTOMER_TYPE_BY_SEGMENT = {
    "VIP":     ["Corporate", "SME"],
    "Growth":  ["SME", "Retail"],
    "Regular": ["Retail", "SME"],
    "At-Risk": ["Retail"],
    "Dormant": ["Retail"],
}

PRODUCTS = ["P001", "P002", "P003", "P004", "P005"]

# ── Per-tier behavioural parameters ───────────────────────────────────────────
# Tier key: "VIP_TOP" for top 10 VIP, else segment name.

PRODUCT_COUNT_BY_TIER = {
    "VIP_TOP":  (4, 5),
    "VIP":      (3, 4),
    "Growth":   (2, 3),
    "Regular":  (1, 3),
    "At-Risk":  (1, 2),
    "Dormant":  (1, 1),
}

TXN_COUNT_BY_TIER = {           # Monthly transaction count range
    "VIP_TOP":  (18, 40),
    "VIP":      (12, 28),
    "Growth":   ( 7, 15),
    "Regular":  ( 3,  8),
    "At-Risk":  ( 2,  6),
    "Dormant":  ( 0,  2),
}

TXN_VALUE_BY_TIER = {           # Individual transaction value (£) — customer's amount
    "VIP_TOP":  (8_000,  80_000),
    "VIP":      (1_500,  20_000),
    "Growth":   (  400,   6_000),
    "Regular":  (   80,   2_000),
    "At-Risk":  (   40,     800),
    "Dormant":  (   20,     300),
}

FEE_REVENUE_BY_TIER = {         # Bank's fee income per transaction (£)
    "VIP_TOP":  (120, 380),     # avg ~£250 → ~£90K/yr for top 10 combined
    "VIP":      ( 12,  28),     # avg ~£20
    "Growth":   (  6,  16),     # avg ~£11
    "Regular":  (  3,  14),     # avg ~£8.5
    "At-Risk":  (  1,   8),     # avg ~£4.5
    "Dormant":  (  0,   4),     # avg ~£2
}

CHANNEL_WEIGHTS_BY_TIER = {     # [Branch, Online, Mobile]
    "VIP_TOP":  [0.10, 0.45, 0.45],
    "VIP":      [0.10, 0.45, 0.45],
    "Growth":   [0.15, 0.45, 0.40],
    "Regular":  [0.30, 0.40, 0.30],
    "At-Risk":  [0.50, 0.30, 0.20],
    "Dormant":  [0.60, 0.25, 0.15],
}

TXN_TYPES = ["Credit", "Debit", "Transfer", "Payment", "Withdrawal"]


# ── Helpers ────────────────────────────────────────────────────────────────────

def month_sequence(start: date, n: int) -> list:
    """Return list of n month-start dates beginning at start."""
    months, d = [], start.replace(day=1)
    for _ in range(n):
        months.append(d)
        d = date(d.year + (d.month == 12), (d.month % 12) + 1, 1)
    return months


def days_in_month(d: date) -> int:
    next_m = date(d.year + (d.month == 12), (d.month % 12) + 1, 1)
    return (next_m - date(d.year, d.month, 1)).days


def get_tier(segment: str, is_top_vip: bool) -> str:
    return "VIP_TOP" if is_top_vip else segment


# ── Reference data ─────────────────────────────────────────────────────────────

def build_relationship_managers() -> pd.DataFrame:
    grades = ["Associate", "Senior Associate", "Manager"]
    teams  = ["Corporate Banking", "SME Banking", "Retail Banking"]
    rows = [
        {
            "rm_id":    f"RM{i+1:03d}",
            "rm_name":  fake.name(),
            "rm_grade": random.choice(grades),
            "team":     random.choice(teams),
        }
        for i in range(10)
    ]
    return pd.DataFrame(rows)


def build_products() -> pd.DataFrame:
    return pd.DataFrame([
        {"product_id": "P001", "product_name": "Business Current Account", "product_category": "Payments",    "is_core_product": 1},
        {"product_id": "P002", "product_name": "Fixed Term Deposit",        "product_category": "Deposits",    "is_core_product": 1},
        {"product_id": "P003", "product_name": "Business Loan",             "product_category": "Lending",     "is_core_product": 1},
        {"product_id": "P004", "product_name": "Business Credit Card",      "product_category": "Payments",    "is_core_product": 0},
        {"product_id": "P005", "product_name": "Investment Portfolio",      "product_category": "Investments", "is_core_product": 0},
    ])


# ── Customer generation ────────────────────────────────────────────────────────

def build_customers(rm_ids: list) -> pd.DataFrame:
    rows = []
    vip_counter = 0
    cust_num    = 1

    for segment, count in SEGMENT_COUNTS.items():
        for _ in range(count):
            is_top_vip = segment == "VIP" and vip_counter < TOP_VIP_N
            if segment == "VIP":
                vip_counter += 1

            ctype   = random.choice(CUSTOMER_TYPE_BY_SEGMENT[segment])
            onboard = SNAPSHOT_DATE - timedelta(days=random.randint(180, 1_825))

            rows.append({
                "customer_id":          f"CUST{cust_num:05d}",
                "customer_name":        fake.company() if ctype in ("Corporate", "SME") else fake.name(),
                "customer_type":        ctype,
                "onboarding_date":      onboard.isoformat(),
                "relationship_manager": random.choice(rm_ids),
                "region":               random.choice(REGIONS),
                "is_active":            0 if segment == "Dormant" else 1,
                "_segment":             segment,
                "_is_top_vip":          is_top_vip,
            })
            cust_num += 1

    return pd.DataFrame(rows)


# ── Transaction generation ─────────────────────────────────────────────────────

def build_transactions(customers_df: pd.DataFrame) -> pd.DataFrame:
    months  = month_sequence(START_DATE, N_MONTHS)
    n_months = len(months)
    records  = []
    txn_num  = 1

    for _, cust in customers_df.iterrows():
        segment    = cust["_segment"]
        is_top_vip = cust["_is_top_vip"]
        tier       = get_tier(segment, is_top_vip)
        cid        = cust["customer_id"]

        n_prod      = random.randint(*PRODUCT_COUNT_BY_TIER[tier])
        cust_prods  = random.sample(PRODUCTS, n_prod)

        for month_idx, mdate in enumerate(months):
            months_from_end = n_months - 1 - month_idx
            base = random.randint(*TXN_COUNT_BY_TIER[tier])

            # ── Segment-specific activity patterns ──────────────────────────

            if segment == "Dormant":
                # Fully inactive for the last 3 months
                if months_from_end < 3:
                    continue
                base = min(base, 1)

            elif segment == "At-Risk":
                # Gradual decline over the last 6 months: 100% → 40%
                if months_from_end < 6:
                    factor = 0.40 + (months_from_end / 6) * 0.60
                    base   = max(0, int(base * factor))

            elif segment == "Growth" and months_from_end > 18:
                # Lower activity in early months (simulates growth ramp-up)
                base = max(1, int(base * 0.55))

            if base == 0:
                continue

            dim = days_in_month(mdate)
            for _ in range(base):
                txn_date = date(mdate.year, mdate.month, random.randint(1, dim))
                product  = random.choice(cust_prods)
                channel  = random.choices(
                    ["Branch", "Online", "Mobile"],
                    weights=CHANNEL_WEIGHTS_BY_TIER[tier],
                )[0]

                records.append({
                    "transaction_id":    f"TXN{txn_num:08d}",
                    "customer_id":       cid,
                    "product_id":        product,
                    "transaction_date":  txn_date.isoformat(),
                    "transaction_type":  random.choice(TXN_TYPES),
                    "channel":           channel,
                    "transaction_value": round(random.uniform(*TXN_VALUE_BY_TIER[tier]),  2),
                    "fee_revenue":       round(random.uniform(*FEE_REVENUE_BY_TIER[tier]), 2),
                })
                txn_num += 1

    return pd.DataFrame(records)


# ── Anomaly injection ──────────────────────────────────────────────────────────

def inject_anomalies(txn_df: pd.DataFrame, cust_df: pd.DataFrame) -> pd.DataFrame:
    """
    Seed realistic exception patterns so the monitoring layer has clear signals.
    Modifies a copy of txn_df.
    """
    txn_df = txn_df.copy()

    # 1. Activity Cliffs — 8 Regular/Growth customers: 70% drop from Jan 2024
    cliff_date = "2024-01-01"
    cliff_pool = cust_df[
        cust_df["_segment"].isin(["Regular", "Growth"])
    ]["customer_id"].tolist()
    cliff_custs = random.sample(cliff_pool, 8)

    for cid in cliff_custs:
        mask = (txn_df["customer_id"] == cid) & (txn_df["transaction_date"] >= cliff_date)
        drop = txn_df[mask].sample(frac=0.72, random_state=SEED)
        txn_df = txn_df.drop(drop.index)

    # 2. Revenue Decline — 5 non-top VIP customers: fee_revenue falls 75% from Oct 2023
    decline_date = "2023-10-01"
    vip_pool = cust_df[
        (cust_df["_segment"] == "VIP") & (~cust_df["_is_top_vip"])
    ]["customer_id"].tolist()
    decline_custs = random.sample(vip_pool, 5)

    for cid in decline_custs:
        mask = (txn_df["customer_id"] == cid) & (txn_df["transaction_date"] >= decline_date)
        txn_df.loc[mask, "fee_revenue"] = (txn_df.loc[mask, "fee_revenue"] * 0.25).round(2)

    log.info(
        f"  Anomalies injected: {len(cliff_custs)} activity cliffs, "
        f"{len(decline_custs)} revenue declines"
    )
    return txn_df, cliff_custs, decline_custs


# ── Summary reporting ──────────────────────────────────────────────────────────

def print_summary(customers_df: pd.DataFrame, txn_df: pd.DataFrame) -> None:
    total_rev  = txn_df["fee_revenue"].sum()
    top10_ids  = customers_df[customers_df["_is_top_vip"]]["customer_id"]
    top10_rev  = txn_df[txn_df["customer_id"].isin(top10_ids)]["fee_revenue"].sum()
    seg_counts = customers_df["_segment"].value_counts()

    log.info("")
    log.info("── Data Generation Complete ──────────────────────────────────")
    log.info(f"  Customers         : {len(customers_df):>8,}")
    log.info(f"  Transactions       : {len(txn_df):>8,}")
    log.info(f"  Total fee revenue  : £{total_rev:>10,.0f}")
    log.info(f"  Top 10 revenue     : £{top10_rev:>10,.0f}  ({top10_rev/total_rev*100:.1f}% of total)")
    log.info("")
    log.info("  Segment distribution:")
    for seg, cnt in seg_counts.items():
        log.info(f"    {seg:<10} : {cnt:>4} customers")
    log.info("─────────────────────────────────────────────────────────────")


# ── Entry point ────────────────────────────────────────────────────────────────

def generate(root: Path = None) -> None:
    """Generate synthetic reference, customer, and transaction CSVs under data/."""
    root = root or Path(__file__).parent.parent
    raw_dir = root / "data" / "raw"
    ref_dir = root / "data" / "reference"
    raw_dir.mkdir(parents=True, exist_ok=True)
    ref_dir.mkdir(parents=True, exist_ok=True)

    log.info("Generating reference data …")
    rms      = build_relationship_managers()
    products = build_products()
    rms.to_csv(ref_dir / "relationship_managers.csv", index=False)
    products.to_csv(ref_dir / "product_catalogue.csv", index=False)

    log.info("Generating customers …")
    customers_full = build_customers(rms["rm_id"].tolist())

    log.info("Generating transactions (30–60 seconds) …")
    txns = build_transactions(customers_full)
    txns, _, _ = inject_anomalies(txns, customers_full)

    # Strip internal generation columns before export
    customers_export = customers_full.drop(columns=["_segment", "_is_top_vip"])
    customers_export.to_csv(raw_dir / "customers.csv", index=False)
    txns.to_csv(raw_dir / "transactions.csv", index=False)

    print_summary(customers_full, txns)


def main() -> None:
    generate()


if __name__ == "__main__":
    main()
