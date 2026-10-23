
"""Expiry management and FEFO stock allocation for BFB321."""

from datetime import date, datetime


def _parse_date(value):
    """Accept a date object or an ISO date string (YYYY-MM-DD)."""
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Date must use YYYY-MM-DD.") from exc

    raise ValueError("Date must be a date or YYYY-MM-DD string.")


def _validate_quantity(quantity):
    """Ensure stock quantity is a finite non-negative number."""
    import math

    if (
        isinstance(quantity, bool)
        or not isinstance(quantity, (int, float))
        or not math.isfinite(quantity)
        or quantity < 0
    ):
        raise ValueError("Quantity must be non-negative and finite.")

    return quantity


def classify_batch(expiry_date, today=None, warning_days=30):
    """Classify a medicine batch by its expiry date.

    Returns:
        expired: Date is before today.
        expiring_soon: Date is within warning_days, including today.
        fresh: Date is beyond the warning period.
    """
    expiry = _parse_date(expiry_date)
    current_date = _parse_date(today) if today is not None else date.today()

    if not isinstance(warning_days, int) or warning_days < 0:
        raise ValueError("Warning days must be a non-negative integer.")

    days_remaining = (expiry - current_date).days

    if days_remaining < 0:
        return "expired"

    if days_remaining <= warning_days:
        return "expiring_soon"

    return "fresh"


def allocate_fefo(batches, requested_quantity, today=None):
    """Allocate stock from the earliest unexpired batches first.

    Each batch is a dictionary containing:
        batch_id, expiry_date, quantity

    Expired batches are excluded from allocation.
    The input batch records are not modified.

    Returns a dictionary containing allocations and the
    quantity that could not be fulfilled.
    """
    requested_quantity = _validate_quantity(requested_quantity)
    current_date = _parse_date(today) if today is not None else date.today()

    valid_batches = []

    for batch in batches:
        batch_id = batch["batch_id"]
        expiry = _parse_date(batch["expiry_date"])
        quantity = _validate_quantity(batch["quantity"])

        if expiry >= current_date and quantity > 0:
            valid_batches.append({
                "batch_id": batch_id,
                "expiry_date": expiry,
                "quantity": quantity,
            })

    valid_batches.sort(
        key=lambda batch: (batch["expiry_date"], str(batch["batch_id"]))
    )

    remaining = requested_quantity
    allocations = []

    for batch in valid_batches:
        if remaining <= 0:
            break

        allocated = min(batch["quantity"], remaining)

        allocations.append({
            "batch_id": batch["batch_id"],
            "expiry_date": batch["expiry_date"].isoformat(),
            "allocated_quantity": allocated,
        })

        remaining -= allocated

    return {
        "requested_quantity": requested_quantity,
        "allocated_quantity": requested_quantity - remaining,
        "unfulfilled_quantity": remaining,
        "allocations": allocations,
    }


def expiry_risk(batches, today=None, warning_days=30):
    """Summarise stock quantities according to expiry risk.

    Returns quantities for expired, expiring-soon and fresh
    stock, plus the overall quantity and at-risk percentage.

    At-risk stock includes expired and expiring-soon batches.
    """
    current_date = _parse_date(today) if today is not None else date.today()

    summary = {
        "expired_quantity": 0,
        "expiring_soon_quantity": 0,
        "fresh_quantity": 0,
        "total_quantity": 0,
    }

    category_keys = {
        "expired": "expired_quantity",
        "expiring_soon": "expiring_soon_quantity",
        "fresh": "fresh_quantity",
    }

    for batch in batches:
        quantity = _validate_quantity(batch["quantity"])

        category = classify_batch(
            batch["expiry_date"],
            today=current_date,
            warning_days=warning_days,
        )

        summary[category_keys[category]] += quantity
        summary["total_quantity"] += quantity

    at_risk = (
        summary["expired_quantity"]
        + summary["expiring_soon_quantity"]
    )

    summary["at_risk_quantity"] = at_risk

    if summary["total_quantity"] == 0:
        summary["at_risk_percentage"] = 0.0
    else:
        summary["at_risk_percentage"] = (
            at_risk / summary["total_quantity"]
        ) * 100

    return summary
