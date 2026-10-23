
"""Demand analysis and forecasting for the BFB321 inventory application.

This module contains standalone supply chain calculations.
It does not depend on Flask or the database.
"""

import math
from statistics import mean, pstdev


def _validate_demand(values):
    """Validate a non-empty sequence of non-negative demand values."""
    values = list(values)

    if not values:
        raise ValueError("Demand data cannot be empty.")

    for value in values:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(
                "Demand values must be finite, non-negative numbers."
            )

    return values


def average_daily_demand(demand):
    """Calculate average demand per day.

    Formula: total demand / number of days.

    Assumes one observation per day, including zero-demand days.
    """
    values = _validate_demand(demand)
    return mean(values)


def demand_standard_deviation(demand):
    """Calculate population standard deviation of daily demand.

    Uses the population formula, dividing variance by N.
    A constant-demand series has a standard deviation of zero.
    """
    values = _validate_demand(demand)
    return pstdev(values)


def moving_average_forecast(demand, window=3):
    """Forecast the next day's demand using a moving average.

    Args:
        demand: Historical daily demand, oldest to newest.
        window: Number of recent days to average.

    Returns:
        Forecast quantity for the next day.
    """
    values = _validate_demand(demand)

    if not isinstance(window, int) or isinstance(window, bool):
        raise ValueError("Window must be an integer.")

    if window < 1 or window > len(values):
        raise ValueError("Window must be between 1 and data length.")

    return mean(values[-window:])


def exponential_smoothing(demand, alpha=0.3):
    """Forecast next-day demand using simple exponential smoothing.

    Formula: F(t+1) = alpha * D(t) + (1-alpha) * F(t).

    Initial forecast is the first observed demand.
    Alpha must be greater than zero and at most one.
    """
    values = _validate_demand(demand)

    if (
        isinstance(alpha, bool)
        or not isinstance(alpha, (int, float))
        or not math.isfinite(alpha)
        or not 0 < alpha <= 1
    ):
        raise ValueError("Alpha must be greater than 0 and at most 1.")

    forecast = float(values[0])

    for actual in values[1:]:
        forecast = alpha * actual + (1 - alpha) * forecast

    return forecast


def _validate_forecast_pairs(actual, predicted):
    """Validate actual and predicted observations."""
    actual = _validate_demand(actual)
    predicted = _validate_demand(predicted)

    if len(actual) != len(predicted):
        raise ValueError(
            "Actual and predicted series must have equal lengths."
        )

    return actual, predicted


def mae(actual, predicted):
    """Calculate Mean Absolute Error (MAE)."""
    actual, predicted = _validate_forecast_pairs(actual, predicted)

    return mean(
        abs(a - p) for a, p in zip(actual, predicted)
    )


def rmse(actual, predicted):
    """Calculate Root Mean Squared Error (RMSE)."""
    actual, predicted = _validate_forecast_pairs(actual, predicted)

    squared_errors = [
        (a - p) ** 2 for a, p in zip(actual, predicted)
    ]

    return math.sqrt(mean(squared_errors))


def wape(actual, predicted):
    """Calculate Weighted Absolute Percentage Error.

    Returns WAPE as a percentage from 0 upwards.
    If total actual demand is zero, returns 0 only when
    all forecasts are also zero; otherwise returns None.
    """
    actual, predicted = _validate_forecast_pairs(actual, predicted)

    total_actual = sum(actual)
    total_error = sum(
        abs(a - p) for a, p in zip(actual, predicted)
    )

    if total_actual == 0:
        return 0.0 if total_error == 0 else None

    return (total_error / total_actual) * 100


def backtest(demand, window=3):
    """Backtest a moving-average forecast on historical demand.

    Uses each preceding window of observations to predict
    the following day. No future observations are used.

    Returns actual values, forecasts and accuracy metrics.
    """
    values = _validate_demand(demand)

    if not isinstance(window, int) or isinstance(window, bool):
        raise ValueError("Window must be an integer.")

    if window < 1 or window >= len(values):
        raise ValueError(
            "Window must be at least 1 and smaller than data length."
        )

    actual = []
    predicted = []

    for index in range(window, len(values)):
        forecast = moving_average_forecast(
            values[index - window:index],
            window=window
        )

        actual.append(values[index])
        predicted.append(forecast)

    return {
        "actual": actual,
        "predicted": predicted,
        "mae": mae(actual, predicted),
        "rmse": rmse(actual, predicted),
        "wape": wape(actual, predicted),
    }
