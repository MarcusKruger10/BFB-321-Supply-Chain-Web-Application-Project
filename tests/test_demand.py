
"""Unit tests for demand forecasting."""

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
    demand = [10, 20, 30]
    assert average_daily_demand(demand) == 20


def test_zero_demand():
    demand = [0, 0, 0, 0]

    assert average_daily_demand(demand) == 0
    assert demand_standard_deviation(demand) == 0
    assert moving_average_forecast(demand, window=3) == 0


def test_standard_deviation():
    demand = [10, 10, 10]

    assert demand_standard_deviation(demand) == 0


def test_moving_average():
    demand = [10, 20, 30, 40]

    result = moving_average_forecast(demand, window=3)

    assert result == 30


def test_exponential_smoothing():
    demand = [10, 20, 30]

    result = exponential_smoothing(demand, alpha=0.5)

    assert result == pytest.approx(22.5)


def test_mae():
    actual = [10, 20, 30]
    predicted = [12, 18, 33]

    assert mae(actual, predicted) == pytest.approx(7 / 3)


def test_rmse():
    actual = [10, 20]
    predicted = [12, 18]

    assert rmse(actual, predicted) == 2


def test_wape():
    actual = [10, 20]
    predicted = [12, 18]

    assert wape(actual, predicted) == pytest.approx(13.3333333)


def test_wape_zero_demand():
    assert wape([0, 0], [0, 0]) == 0
    assert wape([0, 0], [1, 2]) is None


def test_backtest():
    demand = [10, 20, 30, 40, 50]

    result = backtest(demand, window=3)

    assert result["actual"] == [40, 50]
    assert result["predicted"] == [20, 30]
    assert result["mae"] == 20
    assert result["rmse"] == 20
    assert result["wape"] == pytest.approx(44.4444444)


def test_invalid_demand():
    with pytest.raises(ValueError):
        average_daily_demand([])

    with pytest.raises(ValueError):
        average_daily_demand([10, -5, 20])


def test_insufficient_history():
    with pytest.raises(ValueError):
        moving_average_forecast([10, 20], window=3)

    with pytest.raises(ValueError):
        backtest([10, 20, 30], window=3)
