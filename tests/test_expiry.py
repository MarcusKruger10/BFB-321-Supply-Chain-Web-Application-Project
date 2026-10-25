
import pytest

from models.expiry import (
    allocate_fefo,
    classify_batch,
    expiry_risk,
)


TEST_DATE = "2026-10-23"  # Fixed date used for expiry testing


def sample_batches():
    """Creates sample medicine batches for expiry and FEFO tests."""
    return [
        {
            "batch_id": "A",
            "expiry_date": "2026-10-15",
            "quantity": 20,
        },
        {
            "batch_id": "B",
            "expiry_date": "2026-10-30",
            "quantity": 30,
        },
        {
            "batch_id": "C",
            "expiry_date": "2026-12-15",
            "quantity": 50,
        },
    ]


def test_expired_batch():
    """Checks that a batch past its expiry date is classified as expired."""
    result = classify_batch(
        "2026-10-15",
        today=TEST_DATE,
    )  # Expiry classification

    assert result == "expired"


def test_expiring_soon():
    """Checks that a batch nearing expiry is classified correctly."""
    result = classify_batch(
        "2026-10-30",
        today=TEST_DATE,
        warning_days=30,
    )  # Expiry classification within the warning period

    assert result == "expiring_soon"


def test_fresh_batch():
    """Checks that a batch outside the warning period is fresh."""
    result = classify_batch(
        "2026-12-15",
        today=TEST_DATE,
    )  # Expiry classification of a fresh batch

    assert result == "fresh"


def test_expiry_date_today():
    """Checks the classification of stock expiring today."""
    result = classify_batch(
        TEST_DATE,
        today=TEST_DATE,
    )  # Status of a batch expiring today

    assert result == "expiring_soon"


def test_fefo_allocation():
    """Checks that stock is allocated by earliest valid expiry date."""
    result = allocate_fefo(
        sample_batches(),
        requested_quantity=40,
        today=TEST_DATE,
    )  # FEFO allocation result for 40 requested units

    assert result["allocated_quantity"] == 40
    assert result["unfulfilled_quantity"] == 0

    allocations = result["allocations"]  # Units allocated from each batch

    assert allocations[0]["batch_id"] == "B"
    assert allocations[0]["allocated_quantity"] == 30

    assert allocations[1]["batch_id"] == "C"
    assert allocations[1]["allocated_quantity"] == 10


def test_expired_batches_excluded():
    """Checks that expired batches are excluded from allocation."""
    result = allocate_fefo(
        sample_batches(),
        requested_quantity=10,
        today=TEST_DATE,
    )  # FEFO allocation excluding expired stock

    allocated_ids = [
        batch["batch_id"] for batch in result["allocations"]
    ]  # Identifiers of batches selected for allocation

    assert "A" not in allocated_ids


def test_request_larger_than_available_stock():
    """Checks unfulfilled demand when requested stock exceeds supply."""
    result = allocate_fefo(
        sample_batches(),
        requested_quantity=100,
        today=TEST_DATE,
    )  # Allocation result for demand above usable stock

    assert result["allocated_quantity"] == 80
    assert result["unfulfilled_quantity"] == 20


def test_zero_requested_quantity():
    """Checks that requesting zero units produces no allocation."""
    result = allocate_fefo(
        sample_batches(),
        requested_quantity=0,
        today=TEST_DATE,
    )  # Allocation result when no units are requested

    assert result["allocated_quantity"] == 0
    assert result["allocations"] == []


def test_all_stock_expired():
    """Checks that no stock is allocated when all batches have expired."""
    batches = [
        {
            "batch_id": "OLD",
            "expiry_date": "2026-01-01",
            "quantity": 50,
        }
    ]  # Inventory containing only expired stock

    result = allocate_fefo(
        batches,
        requested_quantity=10,
        today=TEST_DATE,
    )  # Allocation attempt using expired inventory

    assert result["allocated_quantity"] == 0
    assert result["unfulfilled_quantity"] == 10


def test_expiry_risk():
    """Checks expired, expiring-soon, and fresh stock quantities."""
    result = expiry_risk(
        sample_batches(),
        today=TEST_DATE,
        warning_days=30,
    )  # Summary of inventory expiry risk

    assert result["expired_quantity"] == 20
    assert result["expiring_soon_quantity"] == 30
    assert result["fresh_quantity"] == 50
    assert result["total_quantity"] == 100
    assert result["at_risk_quantity"] == 50
    assert result["at_risk_percentage"] == 50


def test_empty_inventory():
    """Checks that empty inventory produces zero expiry risk."""
    result = expiry_risk(
        [], today=TEST_DATE
    )  # Expiry summary for empty stock

    assert result["total_quantity"] == 0
    assert result["at_risk_percentage"] == 0


def test_negative_stock_rejected():
    """Checks that negative batch quantities are rejected."""
    batches = [
        {
            "batch_id": "INVALID",
            "expiry_date": "2026-12-01",
            "quantity": -10,
        }
    ]  # Invalid batch with negative stock quantity

    with pytest.raises(ValueError):
        allocate_fefo(batches, 5, today=TEST_DATE)


def test_fefo_does_not_modify_inventory():
    """Checks that FEFO allocation does not change original stock data."""
    batches = sample_batches()  # Original inventory batch records

    allocate_fefo(batches, 40, today=TEST_DATE)

    assert batches[1]["quantity"] == 30
    assert batches[2]["quantity"] == 50
