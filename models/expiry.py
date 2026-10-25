
from datetime import date, datetime


def _parse_date(value):
    """Converts a date string or date object into a valid date."""
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:  # Invalid date conversion error
            raise ValueError("Date must use YYYY-MM-DD.") from exc

    raise ValueError("Date must be a date or YYYY-MM-DD string.")


def _validate_quantity(quantity):
    """Checks that a stock quantity is valid and non-negative."""
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
    """Classifies stock as expired, expiring soon, or fresh."""
    expiry = _parse_date(expiry_date)  # Batch expiry date
    current_date = (
        _parse_date(today) if today is not None else date.today()
    )  # Current date used for classification

    # warning_days: Number of days before expiry to flag stock

    if not isinstance(warning_days, int) or warning_days < 0:
        raise ValueError("Warning days must be a non-negative integer.")

    days_remaining = (expiry - current_date).days  # Days until expiry

    if days_remaining < 0:
        return "expired"

    if days_remaining <= warning_days:
        return "expiring_soon"

    return "fresh"


def allocate_fefo(batches, requested_quantity, today=None):
    """Allocates available stock in earliest-expiry-first order."""
    requested_quantity = _validate_quantity(
        requested_quantity
    )  # Number of units requested

    current_date = (
        _parse_date(today) if today is not None else date.today()
    )  # Date used to check batch expiry

    valid_batches = []  # Available batches that have not expired

    for batch in batches:  # Individual inventory batch
        batch_id = batch["batch_id"]  # Unique batch identifier
        expiry = _parse_date(batch["expiry_date"])  # Batch expiry date
        quantity = _validate_quantity(
            batch["quantity"]
        )  # Available units in the batch

        if expiry >= current_date and quantity > 0:
            valid_batches.append({
                "batch_id": batch_id,
                "expiry_date": expiry,
                "quantity": quantity,
            })

    valid_batches.sort(
        key=lambda batch: (
            batch["expiry_date"],
            str(batch["batch_id"])
        )
    )  # Sort batches by earliest expiry date

    remaining = requested_quantity  # Units still needing allocation
    allocations = []  # List of stock allocated from each batch

    for batch in valid_batches:  # Available batch in FEFO order
        if remaining <= 0:
            break

        allocated = min(
            batch["quantity"], remaining
        )  # Units allocated from current batch

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
    """Calculates expired stock and quantities approaching expiry."""
    current_date = (
        _parse_date(today) if today is not None else date.today()
    )  # Date used for expiry assessment

    # warning_days: Number of days used to identify expiry risk

    summary = {
        "expired_quantity": 0,
        "expiring_soon_quantity": 0,
        "fresh_quantity": 0,
        "total_quantity": 0,
    }  # Total stock quantities grouped by expiry status

    category_keys = {
        "expired": "expired_quantity",
        "expiring_soon": "expiring_soon_quantity",
        "fresh": "fresh_quantity",
    }  # Maps expiry classifications to summary fields

    for batch in batches:  # Individual inventory batch
        quantity = _validate_quantity(
            batch["quantity"]
        )  # Number of units in the batch

        category = classify_batch(
            batch["expiry_date"],
            today=current_date,
            warning_days=warning_days,
        )  # Expiry classification of current batch

        summary[category_keys[category]] += quantity
        summary["total_quantity"] += quantity

    at_risk = (
        summary["expired_quantity"]
        + summary["expiring_soon_quantity"]
    )  # Units that are expired or approaching expiry

    summary["at_risk_quantity"] = at_risk

    if summary["total_quantity"] == 0:
        summary["at_risk_percentage"] = 0.0
    else:
        summary["at_risk_percentage"] = (
            at_risk / summary["total_quantity"]
        ) * 100

    return summary
