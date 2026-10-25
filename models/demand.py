
import math
from statistics import mean, pstdev


def _validate_demand(values):
    """Checks that demand data contains valid non-negative numbers."""
    values = list(values)  # Historical demand values

    if not values:
        raise ValueError("Demand data cannot be empty.")

    for value in values:  # Individual demand value
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
    """Calculates the average number of units demanded per day."""
    values = _validate_demand(demand)  # Validated daily demand data
    return mean(values)


def demand_standard_deviation(demand):
    """Calculates how much daily demand varies from its average."""
    values = _validate_demand(demand)  # Validated daily demand data
    return pstdev(values)


def moving_average_forecast(demand, window=3):
    """Predicts future demand using the average of recent days."""
    values = _validate_demand(demand)  # Historical daily demand
    # window: Number of recent days used for forecasting

    if not isinstance(window, int) or isinstance(window, bool):
        raise ValueError("Window must be an integer.")

    if window < 1 or window > len(values):
        raise ValueError("Window must be between 1 and data length.")

    return mean(values[-window:])


def exponential_smoothing(demand, alpha=0.3):
    """Forecasts demand by weighting recent observations more heavily."""
    values = _validate_demand(demand)  # Historical demand observations
    # alpha: Weight assigned to the latest demand observation

    if (
        isinstance(alpha, bool)
        or not isinstance(alpha, (int, float))
        or not math.isfinite(alpha)
        or not 0 < alpha <= 1
    ):
        raise ValueError("Alpha must be greater than 0 and at most 1.")

    forecast = float(values[0])  # Initial demand forecast

    for actual in values[1:]:  # Actual demand for each following day
        forecast = alpha * actual + (1 - alpha) * forecast

    return forecast


def _validate_forecast_pairs(actual, predicted):
    """Checks that actual and forecasted demand values are valid."""
    actual = _validate_demand(actual)  # Actual demand observations
    predicted = _validate_demand(predicted)  # Predicted demand observations

    if len(actual) != len(predicted):
        raise ValueError(
            "Actual and predicted series must have equal lengths."
        )

    return actual, predicted


def mae(actual, predicted):
    """Calculates the mean absolute error of demand forecasts."""
    actual, predicted = _validate_forecast_pairs(
        actual, predicted
    )  # Validated actual and forecast values

    return mean(
        abs(a - p) for a, p in zip(actual, predicted)
    )  # a: Actual demand; p: Predicted demand


def rmse(actual, predicted):
    """Calculates the root mean squared error of forecasts."""
    actual, predicted = _validate_forecast_pairs(
        actual, predicted
    )  # Validated actual and forecast values

    squared_errors = [
        (a - p) ** 2 for a, p in zip(actual, predicted)
    ]  # Squared differences between actual and predicted demand

    return math.sqrt(mean(squared_errors))


def wape(actual, predicted):
    """Calculates forecast error as a percentage of total demand."""
    actual, predicted = _validate_forecast_pairs(
        actual, predicted
    )  # Validated actual and forecast values

    total_actual = sum(actual)  # Total actual demand

    total_error = sum(
        abs(a - p) for a, p in zip(actual, predicted)
    )  # Total absolute forecasting error

    if total_actual == 0:
        return 0.0 if total_error == 0 else None

    return (total_error / total_actual) * 100


def backtest(demand, window=3):
    """Tests moving-average forecasts against historical demand."""
    values = _validate_demand(demand)  # Historical demand observations
    # window: Number of previous days used for each forecast

    if not isinstance(window, int) or isinstance(window, bool):
        raise ValueError("Window must be an integer.")

    if window < 1 or window >= len(values):
        raise ValueError(
            "Window must be at least 1 and smaller than data length."
        )

    actual = []  # Actual demand values used for comparison
    predicted = []  # Forecasted demand values

    for index in range(window, len(values)):  # Current day position
        forecast = moving_average_forecast(
            values[index - window:index],
            window=window
        )  # Forecast based on previous days

        actual.append(values[index])
        predicted.append(forecast)

    return {
        "actual": actual,
        "predicted": predicted,
        "mae": mae(actual, predicted),
        "rmse": rmse(actual, predicted),
        "wape": wape(actual, predicted),
    }
