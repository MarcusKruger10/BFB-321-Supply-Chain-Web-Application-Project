
import pytest

from models.demand import (
    average_daily_demand,
    demand_standard_deviation,
    moving_average_forecast,
    exponential_smoothing,
    mae,
    rmse,
    wape,
    backtest,
)


def test_average_daily_demand():
    """Checks that average daily demand is calculated correctly."""
    demand = [10, 20, 30]  # Daily demand observations
    assert average_daily_demand(demand) == 20


def test_zero_demand():
    """Checks that zero demand produces zero demand statistics."""
    demand = [0, 0, 0, 0]  # Days with no demand

    assert average_daily_demand(demand) == 0
    assert demand_standard_deviation(demand) == 0
    assert moving_average_forecast(demand, window=3) == 0


def test_standard_deviation():
    """Checks that constant demand has zero standard deviation."""
    demand = [10, 10, 10]  # Identical daily demand values

    assert demand_standard_deviation(demand) == 0


def test_moving_average():
    """Checks the moving-average demand forecast."""
    demand = [10, 20, 30, 40]  # Historical demand observations

    result = moving_average_forecast(
        demand, window=3
    )  # Forecast using the last three days

    assert result == 30


def test_exponential_smoothing():
    """Checks the exponential smoothing forecast calculation."""
    demand = [10, 20, 30]  # Historical demand observations

    result = exponential_smoothing(
        demand, alpha=0.5
    )  # Forecast with smoothing weight of 0.5

    assert result == pytest.approx(22.5)


def test_mae():
    """Checks the mean absolute forecasting error."""
    actual = [10, 20, 30]  # Actual demand values
    predicted = [12, 18, 33]  # Forecasted demand values

    assert mae(actual, predicted) == pytest.approx(7 / 3)


def test_rmse():
    """Checks the root mean squared forecasting error."""
    actual = [10, 20]  # Actual demand values
    predicted = [12, 18]  # Forecasted demand values

    assert rmse(actual, predicted) == 2


def test_wape():
    """Checks the weighted absolute percentage error."""
    actual = [10, 20]  # Actual demand values
    predicted = [12, 18]  # Forecasted demand values

    assert wape(actual, predicted) == pytest.approx(13.3333333)


def test_wape_zero_demand():
    """Checks WAPE when actual demand is zero."""
    assert wape([0, 0], [0, 0]) == 0
    assert wape([0, 0], [1, 2]) is None


def test_backtest():
    """Checks forecasts and accuracy metrics against historical demand."""
    demand = [10, 20, 30, 40, 50]  # Historical daily demand

    result = backtest(
        demand, window=3
    )  # Historical forecast results and accuracy measures

    assert result["actual"] == [40, 50]
    assert result["predicted"] == [20, 30]
    assert result["mae"] == 20
    assert result["rmse"] == 20
    assert result["wape"] == pytest.approx(44.4444444)


def test_invalid_demand():
    """Checks that empty or negative demand data is rejected."""
    with pytest.raises(ValueError):
        average_daily_demand([])

    with pytest.raises(ValueError):
        average_daily_demand([10, -5, 20])


def test_insufficient_history():
    """Checks that forecasts reject insufficient historical data."""
    with pytest.raises(ValueError):
        moving_average_forecast([10, 20], window=3)

    with pytest.raises(ValueError):
        backtest([10, 20, 30], window=3)
