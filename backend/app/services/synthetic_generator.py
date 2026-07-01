"""
Synthetic Agricultural Portfolio Generator
Generates 2500+ realistic Swedish farming businesses for ML training.

Creates diverse PROFILES - not random numbers. Each profile represents
a distinct type of agricultural business with realistic financial,
operational, and environmental characteristics.

Profiles (the model learns - we don't hardcode rules):
  1. Young Farmer - new entrant, small farm, no credit history
  2. Established - experienced, multiple loans, strong repayment
  3. Expansion - large farm, high debt, weather-sensitive
  4. Conservative - low debt, moderate size, stable income
  5. Diversified - mixed crops, multiple income streams
  6. Struggling - weather-hit, declining revenue, repayment issues
  7. Organic - premium prices, higher costs, niche market
  8. Tenant - leased land, lower assets, variable costs

GDPR: ALL DATA IS SYNTHETIC. No real PII.

Design principle:
  Validation layer → checks if data is usable
  Financial formulas → compute objective metrics (DSCR, DTI, LTV)
  Machine learning → LEARNS risk patterns from data
  Gemini → explains predictions in human language
"""
import json
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session

from ..models import (
    Farmer, ExistingLoan, FinancialRecord,
    OperationalData,
)
from ..logger import get_logger

logger = get_logger(__name__)

# ---- Swedish Agricultural Statistics (2023-2024 reference) ----
# Farm size distribution (hectares) - most Swedish grain farms
FARM_SIZE_DIST = {
    "small": (10, 30, 0.25),     # min, max, probability
    "medium": (30, 80, 0.45),
    "large": (80, 200, 0.20),
    "xlarge": (200, 500, 0.10),
}

# Revenue per hectare for grain (SEK) - varies by region, weather, crop
REVENUE_PER_HA_MEAN = 16500   # SEK/ha (wheat ~6t/ha × 2.50 kr/kg = 15000, barley ~5t × 2.10 = 10500)
REVENUE_PER_HA_STD = 3500

# Operating expenses as % of revenue
OPEX_RATIO_MEAN = 0.52
OPEX_RATIO_STD = 0.08

# Interest rate distribution (Swedish agricultural loans)
INTEREST_RATES = {
    "farm_loan": (3.5, 6.5),
    "tractor_loan": (4.0, 7.5),
    "equipment_loan": (4.5, 8.0),
    "credit_line": (5.0, 9.0),
    "mortgage": (3.0, 5.5),
}

# UC Score distribution (bell curve, Swedish credit scores 300-900)
UC_SCORE_MEAN = 620
UC_SCORE_STD = 110

# Loan-to-Asset ratio for farm loans
LTV_FARM_MEAN = 0.55
LTV_FARM_STD = 0.15

# Swedish first names (common agricultural regions)
MALE_FIRST_NAMES = [
    "Erik", "Lars", "Anders", "Johan", "Karl", "Nils", "Per", "Mats", "Stefan",
    "Magnus", "Henrik", "Fredrik", "Oskar", "Gustav", "Emil", "Axel", "Viktor",
    "Olof", "Sven", "Hans", "Bengt", "Jan", "Daniel", "Mikael", "Tomas",
]

FEMALE_FIRST_NAMES = [
    "Anna", "Maria", "Eva", "Karin", "Kristina", "Lena", "Sara", "Emma", "Hanna",
    "Ingrid", "Sofia", "Elin", "Ida", "Astrid", "Greta", "Lisa", "Maja", "Klara",
    "Josefin", "Lovisa", "Britta", "Ulla", "Annika", "Malin", "Petra",
]

LAST_NAMES = [
    "Johansson", "Andersson", "Karlsson", "Nilsson", "Eriksson", "Larsson",
    "Olsson", "Persson", "Svensson", "Gustafsson", "Pettersson", "Jonsson",
    "Hansson", "Bengtsson", "Jansson", "Lindberg", "Lindstrom", "Lundberg",
    "Bergstrom", "Sandberg", "Forsberg", "Sjoberg", "Wallin", "Holmberg",
    "Blomqvist", "Norberg", "Ekstrom", "Strandberg", "Nystrom", "Dahlberg",
]

# Swedish agricultural regions (lan)
REGIONS = [
    ("Skane", "Skurup"), ("Skane", "Lund"), ("Skane", "Kristianstad"),
    ("Skane", "Trelleborg"), ("Skane", "Ystad"), ("Skane", "Sjobo"),
    ("Vastra Gotaland", "Skovde"), ("Vastra Gotaland", "Lidkoping"),
    ("Vastra Gotaland", "Falkoping"), ("Vastra Gotaland", "Vanersborg"),
    ("Ostergotland", "Linkoping"), ("Ostergotland", "Motala"),
    ("Ostergotland", "Mjolby"), ("Ostergotland", "Vadstena"),
    ("Uppsala", "Enkoping"), ("Uppsala", "Tierp"), ("Uppsala", "Osthammar"),
    ("Sodermanland", "Eskilstuna"), ("Sodermanland", "Nykoping"),
    ("Sodermanland", "Flen"), ("Orebro", "Kumla"), ("Orebro", "Hallsberg"),
    ("Stockholm", "Norrtalje"), ("Stockholm", "Sodertalje"),
    ("Kalmar", "Vastervik"), ("Kalmar", "Oskarshamn"),
    ("Halland", "Falkenberg"), ("Halland", "Varberg"),
    ("Gotland", "Visby"), ("Vastmanland", "Vasteras"),
]

# Crop types (Swedish grain focus)
CROPS = [
    "Hostvete", "Varvete", "Varkorn", "Havre", "Hostraps",
    "Hostvete & Varkorn", "Havre & Varkorn", "Hostvete & Hostraps",
    "Varvete", "Radgras", "Hostvete & Havre",
]

# Swedish banks active in agricultural lending
LENDERS = [
    "Landshypotek", "Swedbank", "SEB", "Nordea",
    "Handelsbanken", "Lansforsakringar Bank",
]


def _clamp(value, low, high):
    return max(low, min(high, value))


def generate_synthetic_farmers(n_farmers: int = 2500, seed: int = 42) -> list[dict]:
    """
    Generate n synthetic Swedish farmers with realistic correlations.

    Returns list of dicts ready for database insertion.
    """
    rng = np.random.default_rng(seed)
    farmers = []

    for i in range(n_farmers):
        # Gender (more male farmers historically, but changing)
        is_male = rng.random() < 0.72
        first = rng.choice(MALE_FIRST_NAMES if is_male else FEMALE_FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        region, district = REGIONS[i % len(REGIONS)]

        # Years in farming (correlated with age)
        years_farming = int(rng.normal(22, 10))
        years_farming = _clamp(years_farming, 3, 45)

        # UC Score (bell curve, clipped)
        uc_score = int(rng.normal(UC_SCORE_MEAN, UC_SCORE_STD))
        uc_score = _clamp(uc_score, 350, 890)

        # Farm size - pick from distribution
        size_choice = rng.choice(
            ["small", "medium", "large", "xlarge"],
            p=[FARM_SIZE_DIST[k][2] for k in ["small", "medium", "large", "xlarge"]],
        )
        min_ha, max_ha, _ = FARM_SIZE_DIST[size_choice]
        farm_ha = round(rng.uniform(min_ha, max_ha), 1)

        # Revenue per ha varies - bigger farms slightly more efficient
        efficiency_bonus = 1.0 + (farm_ha - 30) * 0.001 if farm_ha > 30 else 1.0
        rev_per_ha = rng.normal(REVENUE_PER_HA_MEAN * efficiency_bonus, REVENUE_PER_HA_STD)
        rev_per_ha = max(8000, rev_per_ha)

        # Crop & yield
        crop = rng.choice(CROPS)
        total_production = round(farm_ha * rng.uniform(5.0, 7.5) * 1000)  # kg
        price_per_kg = round(rng.uniform(1.80, 3.20), 2)

        # Land value (25,000 - 180,000 kr/ha depending on region)
        land_value_per_ha = rng.uniform(40000, 120000) if "Skane" in region else rng.uniform(25000, 80000)
        land_value = round(farm_ha * land_value_per_ha)

        # Machinery value (correlated with farm size)
        machinery = round(farm_ha * rng.uniform(15000, 45000))

        # Ownership
        ownership = rng.choice(["owned", "owned", "owned", "mixed", "leased"])

        # Insurance
        has_insurance = rng.random() < 0.78
        has_tractor = farm_ha > 15 or rng.random() < 0.6
        has_irrigation = rng.random() < 0.15  # less common in Sweden

        # Generate 3 years of financial records with trend
        base_revenue = round(farm_ha * rev_per_ha)

        financial_years = []
        for year_offset in range(3):
            year = 2024 - (2 - year_offset)
            # Revenue trend: slight growth with noise
            trend = 1.0 + (year_offset - 1) * rng.uniform(-0.03, 0.08)
            revenue = round(base_revenue * trend * rng.uniform(0.88, 1.12))

            opex_ratio = rng.normal(OPEX_RATIO_MEAN, OPEX_RATIO_STD)
            opex_ratio = _clamp(opex_ratio, 0.35, 0.72)
            operating_expenses = round(revenue * opex_ratio)

            depreciation = round(farm_ha * rng.uniform(1200, 2200))

            # Loan generation happens below, interest expense calculated after
            interest_expense = 0  # placeholder - filled after loans generated

            gross = revenue - operating_expenses - depreciation
            net_income = round(gross * rng.uniform(0.75, 0.95))

            # Balance sheet
            fixed_assets = round(farm_ha * land_value_per_ha + machinery * rng.uniform(0.9, 1.1))
            current_assets = round(revenue * rng.uniform(0.15, 0.35))
            total_assets = fixed_assets + current_assets

            total_liabilities = round(total_assets * rng.uniform(0.15, 0.55))
            current_liabilities = round(total_liabilities * rng.uniform(0.08, 0.25))
            long_term_debt = total_liabilities - current_liabilities
            equity = total_assets - total_liabilities

            operating_cf = round(revenue * rng.uniform(0.30, 0.50))
            free_cf = round(operating_cf * rng.uniform(0.65, 0.90))

            financial_years.append({
                "year": year,
                "revenue": revenue,
                "operating_expenses": operating_expenses,
                "interest_expense": interest_expense,
                "depreciation": depreciation,
                "net_income": net_income,
                "total_assets": total_assets,
                "current_assets": current_assets,
                "fixed_assets": fixed_assets,
                "total_liabilities": total_liabilities,
                "current_liabilities": current_liabilities,
                "long_term_debt": long_term_debt,
                "equity": equity,
                "operating_cash_flow": operating_cf,
                "free_cash_flow": free_cf,
            })

        # Generate 1-4 loans
        n_loans = int(rng.choice([1, 2, 3, 4], p=[0.15, 0.40, 0.30, 0.15]))
        loan_types = rng.choice(
            ["farm_loan", "tractor_loan", "equipment_loan", "credit_line", "mortgage"],
            size=n_loans, replace=False,
            p=[0.35, 0.22, 0.15, 0.18, 0.10],
        )

        loans = []
        total_annual_service = 0
        for lt in loan_types:
            rate = round(rng.uniform(*INTEREST_RATES[lt]), 2)
            tenure_months = rng.choice([36, 48, 60, 84, 120, 180, 240])

            if lt == "farm_loan":
                amount = round(total_assets * rng.uniform(0.15, 0.50))
            elif lt == "mortgage":
                amount = round(total_assets * rng.uniform(0.10, 0.35))
            elif lt == "tractor_loan":
                amount = round(rng.uniform(300000, 1200000))
            elif lt == "equipment_loan":
                amount = round(rng.uniform(100000, 600000))
            else:  # credit_line
                amount = round(rng.uniform(50000, 500000))

            outstanding = round(amount * rng.uniform(0.15, 0.85))

            # EMI using annuity formula (approximate)
            monthly_rate = rate / 100 / 12
            if monthly_rate > 0:
                emi = amount * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
            else:
                emi = amount / tenure_months
            emi = round(emi)

            total_payments = tenure_months
            on_time = int(total_payments * rng.uniform(0.75, 1.0))

            months_remaining = int(tenure_months * rng.uniform(0.05, 0.85))

            total_annual_service += emi * 12

            start_date = datetime(2024 - rng.integers(1, 15), rng.integers(1, 13), 1)
            end_date = datetime(
                start_date.year + tenure_months // 12,
                (start_date.month + tenure_months % 12 - 1) % 12 + 1,
                1,
            )

            loans.append({
                "loan_type": lt,
                "lender": rng.choice(LENDERS),
                "original_amount": amount,
                "outstanding_balance": outstanding,
                "monthly_emi": emi,
                "interest_rate": rate,
                "start_date": start_date,
                "end_date": end_date,
                "months_remaining": months_remaining,
                "on_time_payments": on_time,
                "total_payments_due": total_payments,
            })

        # Backfill interest expense in financial records
        for fy in financial_years:
            fy["interest_expense"] = round(total_annual_service * rng.uniform(0.55, 0.75))
            # Recalculate net income with proper interest
            fy["net_income"] = fy["revenue"] - fy["operating_expenses"] - fy["interest_expense"] - fy["depreciation"]

        # Phone number (synthetic Swedish format)
        phone = f"+46-{rng.choice(['70','73','76'])}-{rng.integers(100000,999999)}"

        farmers.append({
            "full_name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}{rng.integers(1000,99999)}@example.se",
            "phone": phone,
            "address": f"Lantbruksvagen {rng.integers(1,200)}, {rng.integers(10000,99999)} {district}",
            "state": region,
            "district": district,
            "cibil_score": uc_score,
            "years_in_farming": years_farming,
            "farm_size_ha": farm_ha,
            "crop_type": crop,
            "total_production_kg": total_production,
            "price_per_kg": price_per_kg,
            "land_value": land_value,
            "machinery_value": machinery,
            "land_ownership": ownership,
            "has_tractor": has_tractor,
            "has_irrigation": has_irrigation,
            "has_insurance": has_insurance,
            "financial_records": financial_years,
            "loans": loans,
        })

    logger.info(f"Generated {len(farmers)} synthetic Swedish farmers")
    return farmers


def seed_bulk_farmers(db: Session, n_farmers: int = 2500) -> int:
    """
    Generate and insert n synthetic farmers into the database.
    Also generates their financial records, loans, and operational data.

    Returns total number of rows inserted.
    """
    logger.info(f"Generating {n_farmers} synthetic Swedish farmers...")

    farmers_data = generate_synthetic_farmers(n_farmers=n_farmers)
    total_rows = 0

    # Batch insert in chunks of 100 for performance
    chunk_size = 100

    for chunk_start in range(0, n_farmers, chunk_size):
        chunk = farmers_data[chunk_start:chunk_start + chunk_size]

        for fdata in chunk:
            # Insert farmer
            farmer = Farmer(
                full_name=fdata["full_name"],
                email=fdata["email"],
                phone=fdata["phone"],
                address=fdata["address"],
                state=fdata["state"],
                district=fdata["district"],
                cibil_score=fdata["cibil_score"],
                years_in_farming=fdata["years_in_farming"],
            )
            db.add(farmer)
            db.flush()
            fid = farmer.id
            total_rows += 1

            # Insert operational data
            ops = OperationalData(
                farmer_id=fid,
                season="annual",
                farm_size_acres=fdata["farm_size_ha"],
                land_ownership=fdata["land_ownership"],
                land_value_estimate=fdata["land_value"],
                crop_type=fdata["crop_type"],
                crop_yield_kg=fdata["total_production_kg"],
                expected_price_per_kg=fdata["price_per_kg"],
                machinery_value=fdata["machinery_value"],
                has_tractor=fdata["has_tractor"],
                has_irrigation=fdata["has_irrigation"],
                has_insurance=fdata["has_insurance"],
                annual_production_kg=fdata["total_production_kg"],
                source_document="synthetic_generator",
            )
            db.add(ops)
            total_rows += 1

            # Insert financial records (3 years each)
            for fy in fdata["financial_records"]:
                fr = FinancialRecord(
                    farmer_id=fid,
                    year=fy["year"],
                    revenue=fy["revenue"],
                    operating_expenses=fy["operating_expenses"],
                    interest_expense=fy["interest_expense"],
                    depreciation=fy["depreciation"],
                    net_income=fy["net_income"],
                    total_assets=fy["total_assets"],
                    current_assets=fy["current_assets"],
                    fixed_assets=fy["fixed_assets"],
                    total_liabilities=fy["total_liabilities"],
                    current_liabilities=fy["current_liabilities"],
                    long_term_debt=fy["long_term_debt"],
                    equity=fy["equity"],
                    operating_cash_flow=fy["operating_cash_flow"],
                    free_cash_flow=fy["free_cash_flow"],
                    source_document="synthetic_generator",
                )
                db.add(fr)
                total_rows += 1

            # Insert loans
            for loan_data in fdata["loans"]:
                loan = ExistingLoan(
                    farmer_id=fid,
                    loan_type=loan_data["loan_type"],
                    lender=loan_data["lender"],
                    original_amount=loan_data["original_amount"],
                    outstanding_balance=loan_data["outstanding_balance"],
                    monthly_emi=loan_data["monthly_emi"],
                    interest_rate=loan_data["interest_rate"],
                    start_date=loan_data["start_date"],
                    end_date=loan_data["end_date"],
                    months_remaining=loan_data["months_remaining"],
                    on_time_payments=loan_data["on_time_payments"],
                    total_payments_due=loan_data["total_payments_due"],
                )
                db.add(loan)
                total_rows += 1

        db.commit()
        pct = min(100, (chunk_start + chunk_size) / n_farmers * 100)
        logger.info(f"  Progress: {pct:.0f}% ({chunk_start + len(chunk)}/{n_farmers} farmers, "
                    f"{total_rows} total rows)")

    logger.info(f"Bulk seed complete: {n_farmers} farmers, {total_rows} total rows")
    return total_rows


# ===========================================================================
# Farmer Profiles - Realistic Agricultural Business Archetypes
# ===========================================================================
# Each profile encodes a distinct risk pattern that the ML model must LEARN.
# We do NOT hardcode "if no loans → medium confidence". The model discovers it.

FARMER_PROFILES = {
    "young_farmer": {
        "label": "Young Farmer (New Entrant)",
        "pct": 0.12,
        "default_probability": 0.12,  # Probabilistic - not every young farmer defaults
        "years_farming": (2, 8),
        "farm_ha": (10, 40),
        "land_ownership": "leased",
        "uc_score": (400, 620),
        "n_loans": (0, 1),
        "repayment_quality": (0.70, 0.90),
        "revenue_per_ha": (0.85, 1.05),
        "has_insurance": 0.55,
        "has_tractor": 0.50,
        "note": "Thin/none credit file. Small farm. Model must learn from financials.",
    },
    "established": {
        "label": "Established Grain Farmer",
        "pct": 0.30,
        "default_probability": 0.05,
        "years_farming": (12, 35),
        "farm_ha": (40, 150),
        "land_ownership": "owned",
        "uc_score": (620, 800),
        "n_loans": (2, 4),
        "repayment_quality": (0.90, 1.0),
        "revenue_per_ha": (0.95, 1.20),
        "has_insurance": 0.90,
        "has_tractor": 0.95,
        "note": "Core portfolio. Strong history. Model should find these low-risk.",
    },
    "expansion": {
        "label": "Aggressive Expansion",
        "pct": 0.15,
        "default_probability": 0.18,
        "years_farming": (8, 20),
        "farm_ha": (80, 300),
        "land_ownership": "mixed",
        "uc_score": (550, 720),
        "n_loans": (3, 6),
        "repayment_quality": (0.75, 0.95),
        "revenue_per_ha": (0.80, 1.10),
        "has_insurance": 0.75,
        "has_tractor": 0.95,
        "note": "High debt, large scale. Weather-sensitive. Mixed outcomes.",
    },
    "conservative": {
        "label": "Conservative Smallholder",
        "pct": 0.18,
        "default_probability": 0.04,
        "years_farming": (10, 30),
        "farm_ha": (15, 50),
        "land_ownership": "owned",
        "uc_score": (650, 850),
        "n_loans": (0, 2),
        "repayment_quality": (0.92, 1.0),
        "revenue_per_ha": (0.90, 1.10),
        "has_insurance": 0.80,
        "has_tractor": 0.70,
        "note": "Low debt, stable. Some have no loans. Model learns: low debt + stable = low risk.",
    },
    "diversified": {
        "label": "Diversified Mixed Farm",
        "pct": 0.10,
        "default_probability": 0.07,
        "years_farming": (5, 25),
        "farm_ha": (30, 100),
        "land_ownership": "mixed",
        "uc_score": (600, 780),
        "n_loans": (1, 3),
        "repayment_quality": (0.85, 0.98),
        "revenue_per_ha": (1.0, 1.35),
        "has_insurance": 0.85,
        "has_tractor": 0.85,
        "note": "Multiple income streams. Higher revenue/ha. Premium niche possible.",
    },
    "struggling": {
        "label": "Weather-Hit / Struggling",
        "pct": 0.08,
        "default_probability": 0.45,
        "years_farming": (5, 30),
        "farm_ha": (20, 80),
        "land_ownership": "mixed",
        "uc_score": (380, 580),
        "n_loans": (1, 4),
        "repayment_quality": (0.50, 0.78),
        "revenue_per_ha": (0.55, 0.85),
        "has_insurance": 0.40,
        "has_tractor": 0.65,
        "note": "Declining revenue, missed payments. Model must learn: this pattern = high risk.",
    },
    "organic_premium": {
        "label": "Organic / Premium Producer",
        "pct": 0.05,
        "default_probability": 0.06,
        "years_farming": (5, 20),
        "farm_ha": (15, 60),
        "land_ownership": "owned",
        "uc_score": (600, 780),
        "n_loans": (1, 2),
        "repayment_quality": (0.88, 1.0),
        "revenue_per_ha": (1.20, 1.60),
        "has_insurance": 0.70,
        "has_tractor": 0.60,
        "note": "Higher revenue/ha but higher costs. Niche premium. Small but profitable.",
    },
    "tenant_farmer": {
        "label": "Tenant / Leased-Land Farmer",
        "pct": 0.02,
        "default_probability": 0.15,
        "years_farming": (3, 15),
        "farm_ha": (20, 80),
        "land_ownership": "leased",
        "uc_score": (450, 650),
        "n_loans": (0, 2),
        "repayment_quality": (0.70, 0.90),
        "revenue_per_ha": (0.80, 1.05),
        "has_insurance": 0.50,
        "has_tractor": 0.55,
        "note": "No land collateral. Lower assets. Model must learn: leased = different risk.",
    },
}

