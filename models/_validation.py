"""Small input checks shared by the model modules."""

import math
from numbers import Real


def check_number(name, value, *, minimum=None, strictly_positive=False):
    """Return ``value`` as a float after checking it is a sensible number.

    Raises:
        TypeError: if ``value`` is not a real number (bools are rejected too).
        ValueError: if it is NaN/infinite, not > 0 when ``strictly_positive``,
            or below ``minimum``.
    """
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value}")
    if strictly_positive and value <= 0:
        raise ValueError(f"{name} must be greater than 0, got {value}")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {value}")
    return value


def check_series(name, values, *, min_length=1):
    """Return ``values`` as a list of non-negative floats.

    Raises:
        TypeError: if ``values`` is not a list/tuple or holds non-numbers.
        ValueError: if it is too short or holds negative values.
    """
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{name} must be a list of numbers")
    if len(values) < min_length:
        raise ValueError(
            f"{name} needs at least {min_length} value(s), got {len(values)}"
        )
    return [check_number(f"{name}[{i}]", v, minimum=0) for i, v in enumerate(values)]