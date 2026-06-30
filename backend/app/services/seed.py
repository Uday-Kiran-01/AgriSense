"""
Mock data seeder — populates the database with synthetic Swedish demo data.

GDPR NOTICE: All data in this seeder is SYNTHETIC and FICTIONAL.
No real personal data is used. Names, addresses, and financial figures
are generated for demonstration purposes only.
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
    Seed the database with synthetic Swedish demo data.

    Creates: 1 farmer (fictional), financial records for 3 years, 3 loans,
             1 operational data row, weather/commodity data in SEK,
             a prediction, and a decision memo.

    All data is synthetic. No real PII.
    """
    logger.info("Seeding synthetic Swedish demo data...")

    # --- Farmer (GDPR: synthetic identity, no real PII) ---
    farmer = Farmer(
        full_name="Erik Johansson",
        email="erik.johansson@example.se",
        phone="+46-70-1234567",
        address="Gardsvagen 12, 274 93 Skurup",
        state="Skane lan",
        district="Skurup",
        cibil_score=685,  # UC score equivalent
        years_in_farming=18,
    )
    db.add(farmer)
    db.flush()
    fid = farmer.id
    logger.info(f"  Farmer: {farmer.full_name} (id={fid}) [SYNTHETIC]")

    # --- Documents ---
    docs = [
        Document(farmer_id=fid, filename="balansrakning_2024.pdf", document_type="financial_statement",
                 sub_type="balance_sheet", file_path="data/samples/balansrakning_2024.pdf",
                 description="Balansrakning rakenskapsar 2024"),
        Document(farmer_id=fid, filename="resultatrakning_2024.pdf", document_type="financial_statement",
                 sub_type="income_statement", file_path="data/samples/resultatrakning_2024.pdf",
                 description="Resultatrakning rakenskapsar 2024"),
        Document(farmer_id=fid, filename="bankutdrag_2024.pdf", document_type="bank_statement",
                 sub_type="current_account", file_path="data/samples/bankutdrag_2024.pdf",
                 description="Bankutdrag Swedbank jan-jun 2024"),
        Document(farmer_id=fid, filename="jordbrukskredit_avtal.pdf", document_type="loan_doc",
                 sub_type="farm_loan", file_path="data/samples/jordbrukskredit_avtal.pdf",
                 description="Jordbrukskredit Landshypotek"),
        Document(farmer_id=fid, filename="traktor_lan.pdf", document_type="loan_doc",
                 sub_type="tractor_loan", file_path="data/samples/traktor_lan.pdf",
                 description="Traktorlan Swedbank Finans"),
        Document(farmer_id=fid, filename="lagfart_fastighet.pdf", document_type="land_record",
                 sub_type="ownership", file_path="data/samples/lagfart_fastighet.pdf",
                 description="Lagfart — fastighetsbevis"),
        Document(farmer_id=fid, filename="skorde_rapport_2024.pdf", document_type="farm_doc",
                 sub_type="production", file_path="data/samples/skorde_rapport_2024.pdf",
                 description="Skorderapport 2024 — vete & korn"),
        Document(farmer_id=fid, filename="forsakringsbrev.pdf", document_type="insurance",
                 sub_type="crop_insurance", file_path="data/samples/forsakringsbrev.pdf",
                 description="Forsakringsbrev — skordeskadeskydd Lansforsakringar"),
    ]
    db.add_all(docs)
    logger.info(f"  Documents: {len(docs)} uploaded [SYNTHETIC]")

    # --- Existing Loans (Swedish banks, SEK, realistic rates & amortering) ---
    loans = [
        ExistingLoan(
            farmer_id=fid, loan_type="farm_loan", lender="Landshypotek Ekonomisk Forening",
            original_amount=2500000, outstanding_balance=1600000,
            monthly_emi=18500, interest_rate=4.85,
            start_date=datetime(2021, 3, 1), end_date=datetime(2031, 3, 1),
            months_remaining=57, on_time_payments=63, total_payments_due=63,
        ),
        ExistingLoan(
            farmer_id=fid, loan_type="tractor_loan", lender="Swedbank Finans",
            original_amount=850000, outstanding_balance=440000,
            monthly_emi=6200, interest_rate=5.25,
            start_date=datetime(2022, 9, 1), end_date=datetime(2027, 9, 1),
            months_remaining=15, on_time_payments=45, total_payments_due=45,
        ),
        ExistingLoan(
            farmer_id=fid, loan_type="credit_line", lender="Swedbank",
            original_amount=400000, outstanding_balance=180000,
            monthly_emi=3500, interest_rate=6.95,
            start_date=datetime(2023, 6, 1), end_date=datetime(2026, 6, 1),
            months_remaining=12, on_time_payments=30, total_payments_due=36,
        ),
    ]
    db.add_all(loans)
    logger.info(f"  Loans: {len(loans)} existing loans [SYNTHETIC]")

    # --- Financial Records (3 years, SEK, Swedish scale, 50ha grain farm) ---
    financials = [
        FinancialRecord(
            farmer_id=fid, year=2022,
            revenue=720000, operating_expenses=395000, interest_expense=105000,
            depreciation=85000, net_income=135000,
            total_assets=7200000, current_assets=580000, fixed_assets=6620000,
            total_liabilities=3100000, current_liabilities=340000, long_term_debt=2760000,
            equity=4100000, operating_cash_flow=240000, free_cash_flow=155000,
            source_document="balansrakning_2022.pdf",
        ),
        FinancialRecord(
            farmer_id=fid, year=2023,
            revenue=785000, operating_expenses=410000, interest_expense=98000,
            depreciation=85000, net_income=192000,
            total_assets=7400000, current_assets=620000, fixed_assets=6780000,
            total_liabilities=2850000, current_liabilities=310000, long_term_debt=2540000,
            equity=4550000, operating_cash_flow=295000, free_cash_flow=210000,
            source_document="balansrakning_2023.pdf",
        ),
        FinancialRecord(
            farmer_id=fid, year=2024,
            revenue=880000, operating_expenses=435000, interest_expense=92000,
            depreciation=85000, net_income=268000,
            total_assets=7550000, current_assets=650000, fixed_assets=6900000,
            total_liabilities=2600000, current_liabilities=290000, long_term_debt=2310000,
            equity=4950000, operating_cash_flow=370000, free_cash_flow=285000,
            source_document="balansrakning_2024.pdf",
        ),
    ]
    db.add_all(financials)
    logger.info(f"  Financial Records: {len(financials)} years of data [SYNTHETIC]")

    # --- Operational Data (Swedish grain farm) ---
    operational = OperationalData(
        farmer_id=fid, season="annual",
        farm_size_acres=50.0,  # hectares (field kept for schema compat, display as ha in UI)
        land_ownership="owned",
        land_value_estimate=5200000,
        crop_type="Hostvete & Varkorn", crop_yield_kg=290000,
        expected_price_per_kg=2.50,
        machinery_value=1800000, has_tractor=True,
        has_irrigation=False, has_insurance=True,
        annual_production_kg=290000,
        source_document="skorde_rapport_2024.pdf",
    )
    db.add(operational)
    logger.info(f"  Operational: {operational.crop_type}, {operational.farm_size_acres} ha [SYNTHETIC]")

    # --- External Data (Swedish weather + EU commodity prices) ---
    external = [
        ExternalData(
            data_type="weather", data_date=date.today(),
            region="Skane-Skurup",
            rainfall_mm=620.0, temperature_celsius=8.2,
            drought_index=0.25, flood_risk="low",
            source="mock_smhi", is_mock=True,
        ),
        ExternalData(
            data_type="commodity", data_date=date.today(),
            commodity_name="Milling Wheat", commodity_price=2.48,
            price_unit="SEK/kg", price_change_pct=-1.8,
            source="mock_jordbruksverket", is_mock=True,
        ),
        ExternalData(
            data_type="commodity", data_date=date.today(),
            commodity_name="Diesel", fuel_price=22.50,
            fertilizer_price=6800.0,
            source="mock", is_mock=True,
        ),
        ExternalData(
            data_type="government", data_date=date.today(),
            subsidy_name="EU CAP Direct Payment (Gardsstod)", subsidy_amount=115000.0,
            source="mock_jordbruksverket", is_mock=True,
        ),
    ]
    db.add_all(external)
    logger.info(f"  External Data: {len(external)} records [SYNTHETIC]")

    # --- Prediction ---
    feature_importance = json.dumps({
        "debt_to_income": 0.26,
        "dscr": 0.24,
        "operating_margin": 0.16,
        "rainfall_deviation": 0.11,
        "commodity_price_trend": 0.09,
        "repayment_history": 0.08,
        "loan_to_value": 0.06,
    })
    input_features = json.dumps({
        "debt_to_income": 0.385, "dscr": 1.32,
        "operating_margin": 0.305, "working_capital": 360000,
        "loan_to_value": 0.294, "asset_coverage": 2.90,
        "repayment_ratio": 0.958,
    })

    prediction = Prediction(
        farmer_id=fid,
        credit_risk_score=0.28,
        repayment_probability=0.89,
        debt_capacity=750000,
        model_confidence=0.86,
        model_version="v1.0.0",
        feature_importance_json=feature_importance,
        financial_health_risk="low",
        environmental_risk="low",
        market_risk="medium",
        overall_financing_risk="low",
        input_features_json=input_features,
    )
    db.add(prediction)
    logger.info(f"  Prediction: risk={prediction.credit_risk_score}, "
                f"repay_prob={prediction.repayment_probability} [SYNTHETIC]")

    # --- Decision Memo (placeholder, Gemini will fill this) ---
    memo = DecisionMemo(
        farmer_id=fid,
        financial_summary="Annual revenue 880 000 kr with consistent growth over 3 years. "
                          "Net income 268 000 kr (30.5% margin). Strong asset base of 7.55M kr.",
        existing_loans_summary="3 active loans totaling 2.22M kr outstanding. "
                               "Monthly amortering obligation 28 200 kr. 95.8% on-time payment history.",
        external_risks_summary="Low environmental risk with stable precipitation in Skane. "
                               "Wheat prices at 2.48 kr/kg (-1.8% YoY). Diesel at 22.50 kr/L. "
                               "EU CAP direct payment of 115 000 kr/yr provides income floor.",
        recommendation="REKOMMENDERAS for additional financing up to 750 000 kr. "
                       "Adequate DSCR of 1.32x, manageable Debt-to-Income of 38.5%, "
                       "substantial land collateral (5.2M kr), and CAP payment stability support this.",
        supporting_evidence="DSCR 1.32x (above 1.25x threshold), "
                           "Debt-to-Income 38.5%, Loan-to-Value 29.4%, "
                           "UC Score 685, 18 years farming experience, "
                           "EU CAP direct payment provides stable base income.",
        generated_by="mock",
        confidence_level="high",
    )
    db.add(memo)
    logger.info(f"  Decision Memo: {memo.generated_by} [SYNTHETIC]")

    db.commit()
    logger.info("Synthetic Swedish demo data seeded successfully!")
    return farmer
