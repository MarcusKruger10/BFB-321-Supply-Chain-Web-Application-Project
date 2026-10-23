
"""Unit tests for FEFO allocation and expiry management."""

import pytest

from models.expiry import (
    allocate_fefo,
    classify_batch,
    expiry_risk,
)


TEST_DATE = "2026-10-23"


def sample_batches():
    """Return fresh test data for each test."""
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
    result = classify_batch(
        "2026-10-15",
        today=TEST_DATE,
    )

    assert result == "expired"


def test_expiring_soon():
    result = classify_batch(
        "2026-10-30",
        today=TEST_DATE,
        warning_days=30,
    )

    assert result == "expiring_soon"


def test_fresh_batch():
    result = classify_batch(
        "2026-12-15",
        today=TEST_DATE,
    )

    assert result == "fresh"


def test_expiry_date_today():
    result = classify_batch(
        TEST_DATE,
        today=TEST_DATE,
    )

    assert result == "expiring_soon"


def test_fefo_allocation():
    result = allocate_fefo(
        sample_batches(),
        requested_quantity=40,
        today=TEST_DATE,
    )

    assert result["allocated_quantity"] == 40
    assert result["unfulfilled_quantity"] == 0

    allocations = result["allocations"]

    assert allocations[0]["batch_id"] == "B"
    assert allocations[0]["allocated_quantity"] == 30

    assert allocations[1]["batch_id"] == "C"
    assert allocations[1]["allocated_quantity"] == 10


def test_expired_batches_excluded():
    result = allocate_fefo(
        sample_batches(),
        requested_quantity=10,
        today=TEST_DATE,
    )

    allocated_ids = [
        batch["batch_id"]
        for batch in result["allocations"]
    ]

    assert "A" not in allocated_ids


def test_request_larger_than_available_stock():
    result = allocate_fefo(
        sample_batches(),
        requested_quantity=100,
        today=TEST_DATE,
    )

    # Only 80 units are usable; 20 units have expired.
    assert result["allocated_quantity"] == 80
    assert result["unfulfilled_quantity"] == 20


def test_zero_requested_quantity():
    result = allocate_fefo(
        sample_batches(),
        requested_quantity=0,
        today=TEST_DATE,
    )

    assert result["allocated_quantity"] == 0
    assert result["allocations"] == []


def test_all_stock_expired():
    batches = [
        {
            "batch_id": "OLD",
            "expiry_date": "2026-01-01",
            "quantity": 50,
        }
    ]

    result = allocate_fefo(
        batches,
        requested_quantity=10,
        today=TEST_DATE,
    )

    assert result["allocated_quantity"] == 0
    assert result["unfulfilled_quantity"] == 10


def test_expiry_risk():
    result = expiry_risk(
        sample_batches(),
        today=TEST_DATE,
        warning_days=30,
    )

    assert result["expired_quantity"] == 20
    assert result["expiring_soon_quantity"] == 30
    assert result["fresh_quantity"] == 50
    assert result["total_quantity"] == 100
    assert result["at_risk_quantity"] == 50
    assert result["at_risk_percentage"] == 50


def test_empty_inventory():
    result = expiry_risk([], today=TEST_DATE)

    assert result["total_quantity"] == 0
    assert result["at_risk_percentage"] == 0


def test_negative_stock_rejected():
    batches = [
        {
            "batch_id": "INVALID",
            "expiry_date": "2026-12-01",
            "quantity": -10,
        }
    ]

    with pytest.raises(ValueError):
        allocate_fefo(batches, 5, today=TEST_DATE)


def test_fefo_does_not_modify_inventory():
    batches = sample_batches()

    allocate_fefo(batches, 40, today=TEST_DATE)

    assert batches[1]["quantity"] == 30
    assert batches[2]["quantity"] == 50
