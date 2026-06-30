"""
Mock data seeder — populates the database with realistic sample data.
"""
import json
import random
from datetime import datetime, date, timedelta

from sqlalchemy.orm import Session

from ..models import (
    Farmer, Document, ExistingLoan, FinancialRecord,
    OperationalData, ExternalData, Prediction, DecisionMemo,
)
from ..logger import get_logger

logger = get_logger(__name__)


def seed_demo_data(db: Session, farmer_id: int | None = None):
    """
    Seed the database with realistic demo data for a single farmer.

    Creates: 1 farmer, financial records for 3 years, 3 loans,
             1 operational data row, weather/commodity data,
             a prediction, and a decision memo.
    """
    logger.info("Seeding demo data...")

    # --- Farmer ---
    farmer = Farmer(
        id=farmer_id or 1,
        full_name="Ramesh Patel",
        email="ramesh.patel@example.com",
        phone="+91-9876543210",
        address="Village Dharmapur, Tehsil Kheda",
        state="Gujarat",
        district="Kheda",
        cibil_score=720,
        years_in_farming=15,
    )
    db.add(farmer)
    db.flush()
    fid = farmer.id
    logger.info(f"  Farmer: {farmer.full_name} (id={fid})")

    # --- Documents ---
    docs = [
        Document(farmer_id=fid, filename="balance_sheet_2024.pdf", document_type="financial_statement",
                 sub_type="balance_sheet", file_path="data/samples/balance_sheet_2024.pdf",
                 description="Audited balance sheet FY 2023-24"),
        Document(farmer_id=fid, filename="income_statement_2024.pdf", document_type="financial_statement",
                 sub_type="income_statement", file_path="data/samples/income_statement_2024.pdf",
                 description="Income statement FY 2023-24"),
        Document(farmer_id=fid, filename="bank_statement_2024.pdf", document_type="bank_statement",
                 sub_type="current_account", file_path="data/samples/bank_statement_2024.pdf"),
        Document(farmer_id=fid, filename="farm_loan_agreement.pdf", document_type="loan_doc",
                 sub_type="farm_loan", file_path="data/samples/farm_loan_agreement.pdf"),
        Document(farmer_id=fid, filename="tractor_loan.pdf", document_type="loan_doc",
                 sub_type="tractor_loan", file_path="data/samples/tractor_loan.pdf"),
        Document(farmer_id=fid, filename="land_title_deed.pdf", document_type="land_record",
                 sub_type="ownership", file_path="data/samples/land_title_deed.pdf"),
        Document(farmer_id=fid, filename="crop_production_report.pdf", document_type="farm_doc",
                 sub_type="production", file_path="data/samples/crop_production_report.pdf"),
        Document(farmer_id=fid, filename="crop_insurance_policy.pdf", document_type="insurance",
                 sub_type="crop_insurance", file_path="data/samples/crop_insurance_policy.pdf"),
    ]
    db.add_all(docs)
    logger.info(f"  Documents: {len(docs)} uploaded")

    # --- Existing Loans ---
    loans = [
        ExistingLoan(
            farmer_id=fid, loan_type="farm_loan", lender="State Bank of India",
            original_amount=500000, outstanding_balance=320000,
            monthly_emi=12500, interest_rate=9.5,
            start_date=datetime(2022, 6, 1), end_date=datetime(2027, 6, 1),
            months_remaining=12, on_time_payments=24, total_payments_due=24,
        ),
        ExistingLoan(
            farmer_id=fid, loan_type="tractor_loan", lender="NABARD",
            original_amount=350000, outstanding_balance=180000,
            monthly_emi=8500, interest_rate=7.0,
            start_date=datetime(2023, 3, 1), end_date=datetime(2026, 3, 1),
            months_remaining=21, on_time_payments=15, total_payments_due=15,
        ),
        ExistingLoan(
            farmer_id=fid, loan_type="credit_line", lender="HDFC Bank",
            original_amount=100000, outstanding_balance=45000,
            monthly_emi=5000, interest_rate=12.0,
            start_date=datetime(2023, 10, 1), end_date=datetime(2025, 10, 1),
            months_remaining=4, on_time_payments=12, total_payments_due=15,
        ),
    ]
    db.add_all(loans)
    logger.info(f"  Loans: {len(loans)} existing loans")

    # --- Financial Records (3 years) ---
    financials = [
        FinancialRecord(
            farmer_id=fid, year=2022,
            revenue=850000, operating_expenses=420000, interest_expense=65000,
            depreciation=35000, net_income=330000,
            total_assets=2800000, current_assets=450000, fixed_assets=2350000,
            total_liabilities=1200000, current_liabilities=250000, long_term_debt=950000,
            equity=1600000, operating_cash_flow=380000, free_cash_flow=280000,
            source_document="balance_sheet_2022.pdf",
        ),
        FinancialRecord(
            farmer_id=fid, year=2023,
            revenue=920000, operating_expenses=460000, interest_expense=72000,
            depreciation=35000, net_income=353000,
            total_assets=2950000, current_assets=520000, fixed_assets=2430000,
            total_liabilities=1050000, current_liabilities=230000, long_term_debt=820000,
            equity=1900000, operating_cash_flow=410000, free_cash_flow=310000,
            source_document="balance_sheet_2023.pdf",
        ),
        FinancialRecord(
            farmer_id=fid, year=2024,
            revenue=980000, operating_expenses=490000, interest_expense=58000,
            depreciation=35000, net_income=397000,
            total_assets=3100000, current_assets=580000, fixed_assets=2520000,
            total_liabilities=880000, current_liabilities=210000, long_term_debt=670000,
            equity=2220000, operating_cash_flow=450000, free_cash_flow=360000,
            source_document="balance_sheet_2024.pdf",
        ),
    ]
    db.add_all(financials)
    logger.info(f"  Financial Records: {len(financials)} years of data")

    # --- Operational Data ---
    operational = OperationalData(
        farmer_id=fid, season="annual",
        farm_size_acres=12.5, land_ownership="owned",
        land_value_estimate=3750000,
        crop_type="Wheat", crop_yield_kg=28000,
        expected_price_per_kg=22.75,
        machinery_value=520000, has_tractor=True,
        has_irrigation=True, has_insurance=True,
        annual_production_kg=28000,
        source_document="crop_production_report.pdf",
    )
    db.add(operational)
    logger.info(f"  Operational: {operational.crop_type}, {operational.farm_size_acres} acres")

    # --- External Data (Weather + Commodity) ---
    external = [
        ExternalData(
            data_type="weather", data_date=date.today(),
            region="Gujarat-Kheda",
            rainfall_mm=850.0, temperature_celsius=28.5,
            drought_index=0.15, flood_risk="low",
            source="mock", is_mock=True,
        ),
        ExternalData(
            data_type="commodity", data_date=date.today(),
            commodity_name="Wheat", commodity_price=2275.0,
            price_unit="INR/quintal", price_change_pct=3.2,
            source="mock", is_mock=True,
        ),
        ExternalData(
            data_type="commodity", data_date=date.today(),
            commodity_name="Diesel", fuel_price=92.50,
            fertilizer_price=1450.0,
            source="mock", is_mock=True,
        ),
        ExternalData(
            data_type="government", data_date=date.today(),
            subsidy_name="PM-KISAN", subsidy_amount=6000.0,
            source="mock", is_mock=True,
        ),
    ]
    db.add_all(external)
    logger.info(f"  External Data: {len(external)} records")

    # --- Prediction ---
    feature_importance = json.dumps({
        "debt_to_income": 0.28,
        "dscr": 0.22,
        "operating_margin": 0.15,
        "rainfall_deviation": 0.12,
        "commodity_price_trend": 0.10,
        "repayment_history": 0.08,
        "loan_to_value": 0.05,
    })
    input_features = json.dumps({
        "debt_to_income": 0.42, "dscr": 1.85,
        "operating_margin": 0.405, "working_capital": 370000,
        "loan_to_value": 0.175, "asset_coverage": 2.52,
        "repayment_ratio": 0.96,
    })

    prediction = Prediction(
        farmer_id=fid,
        credit_risk_score=0.32,
        repayment_probability=0.88,
        debt_capacity=420000,
        model_confidence=0.85,
        model_version="v1.0.0",
        feature_importance_json=feature_importance,
        financial_health_risk="low",
        environmental_risk="medium",
        market_risk="medium",
        overall_financing_risk="low",
        input_features_json=input_features,
    )
    db.add(prediction)
    logger.info(f"  Prediction: risk={prediction.credit_risk_score}, "
                f"repay_prob={prediction.repayment_probability}")

    # --- Decision Memo (placeholder, Gemini will fill this) ---
    memo = DecisionMemo(
        farmer_id=fid,
        financial_summary="Annual revenue ₹9.8L with consistent growth over 3 years. "
                          "Net income ₹3.97L (40.5% margin). Strong asset base of ₹31L.",
        existing_loans_summary="3 active loans totaling ₹5.45L outstanding. "
                               "Monthly EMI obligation ₹26,000. 96% on-time payment history.",
        external_risks_summary="Moderate environmental risk due to slightly below-average rainfall. "
                               "Stable wheat prices with 3.2% YoY increase. Fuel prices elevated.",
        recommendation="RECOMMENDED for additional financing up to ₹4.2L. "
                       "Strong repayment track record, healthy DSCR of 1.85x, "
                       "and substantial land collateral support this recommendation.",
        supporting_evidence="DSCR 1.85x (well above 1.25x threshold), "
                           "Debt-to-Income 42%, Loan-to-Value 17.5%, "
                           "CIBIL 720, 15 years farming experience.",
        generated_by="mock",
        confidence_level="high",
    )
    db.add(memo)
    logger.info(f"  Decision Memo: {memo.generated_by}")

    db.commit()
    logger.info("Demo data seeded successfully!")
    return farmer
