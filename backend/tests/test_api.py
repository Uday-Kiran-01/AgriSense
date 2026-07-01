"""Smoke tests for AgriSense API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["name"] == "AgriSense AI"


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_list_farmers():
    resp = client.get("/api/farmers")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) > 0  # Seeded demo data


def test_get_farmer():
    resp = client.get("/api/farmers/1")
    assert resp.status_code == 200
    data = resp.json()
    assert "full_name" in data
    assert "state" in data


def test_farmer_not_found():
    resp = client.get("/api/farmers/99999")
    assert resp.status_code == 404


def test_farmer_financials():
    resp = client.get("/api/farmers/1/financials")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_farmer_loans():
    resp = client.get("/api/farmers/1/loans")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_external_data():
    resp = client.get("/api/external-data?region=Skane&commodity=WHEAT")
    assert resp.status_code == 200
    assert "weather" in resp.json() or "commodity" in resp.json()


def test_financial_analysis():
    resp = client.get("/api/farmers/1/financial-analysis")
    assert resp.status_code == 200
    assert "ratios" in resp.json()


def test_bank_applications():
    resp = client.get("/api/bank/applications")
    assert resp.status_code == 200
    assert "applications" in resp.json()
