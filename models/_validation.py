import math
from numbers import Real


def check_number(name, value, *, minimum=None, strictly_positive=False):
    """Check that a value is a valid number and return it as a float."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    value = float(value)  # the input converted to a decimal number
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value}")
    if strictly_positive and value <= 0:
        raise ValueError(f"{name} must be greater than 0, got {value}")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {value}")
    return value


def check_series(name, values, *, min_length=1):
    """Check that a list holds only non-negative numbers and return it as floats."""
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{name} must be a list of numbers")
    if len(values) < min_length:
        raise ValueError(
            f"{name} needs at least {min_length} value(s), got {len(values)}"
        )
    return [check_number(f"{name}[{i}]", v, minimum=0) for i, v in enumerate(values)]