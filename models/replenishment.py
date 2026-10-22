"""Replenishment model: when to reorder a medicine and how much to order.

All quantities are in units, demand is per day, lead time and shelf life
are in days, and costs are in Rand.

Formulas:
    z               = inverse standard normal of the service level
    safety stock    = z * sigma_d * sqrt(L)
    reorder point   = d * L + safety stock
    EOQ             = sqrt(2 * D * S / H)
    orders per year = D / Q
    annual cost     = (D / Q) * S + (Q / 2) * H   [+ D * unit price]

    d = average daily demand          sigma_d = std. deviation of daily demand
    L = supplier lead time (days)     D = annual demand (units/year)
    S = cost per order (R)            H = holding cost (R per unit per year)
    Q = order quantity (units)

Assumptions:
    * Daily demand is roughly normal and independent from day to day.
    * Lead time is fixed.
    * Demand is steady enough for EOQ's constant-demand assumption.
    * Medicines expire, so the order is capped by shelf life.
"""

import math
from statistics import NormalDist

from models._validation import check_number

DAYS_PER_YEAR = 365


def z_score(service_level):
    """Return the z value for a cycle service level (e.g. 0.95 -> 1.645).

    Raises:
        ValueError: if service_level is not strictly between 0 and 1.

    Example:
        >>> round(z_score(0.95), 3)
        1.645
    """
    service_level = check_number("service_level", service_level)
    if not 0 < service_level < 1:
        raise ValueError(
            f"service_level must be between 0 and 1 (e.g. 0.95), got {service_level}"
        )
    return NormalDist().inv_cdf(service_level)


def safety_stock(daily_demand_std, lead_time_days, service_level=None, *, z=None):
    """Return the safety stock in units: z * sigma_d * sqrt(L).

    Give exactly one of service_level (e.g. 0.95) or z (e.g. 2.05).
    Returns an unrounded float; round only for display.

    Example:
        >>> round(safety_stock(4.5, 3, z=2.05), 2)
        15.98
    """
    daily_demand_std = check_number("daily_demand_std", daily_demand_std, minimum=0)
    lead_time_days = check_number("lead_time_days", lead_time_days, minimum=0)
    if (service_level is None) == (z is None):
        raise ValueError("give exactly one of service_level or z")
    if z is None:
        z = z_score(service_level)
    else:
        z = check_number("z", z, minimum=0)
    return z * daily_demand_std * math.sqrt(lead_time_days)


def reorder_point(avg_daily_demand, lead_time_days, safety_stock_units):
    """Return the reorder point in units: d * L + safety stock.

    Example:
        >>> reorder_point(8, 3, 16)
        40.0
    """
    avg_daily_demand = check_number("avg_daily_demand", avg_daily_demand, minimum=0)
    lead_time_days = check_number("lead_time_days", lead_time_days, minimum=0)
    safety_stock_units = check_number("safety_stock_units", safety_stock_units, minimum=0)
    return avg_daily_demand * lead_time_days + safety_stock_units


def calculate_eoq(annual_demand, order_cost, holding_cost):
    """Return the economic order quantity: sqrt(2 * D * S / H).

    Raises:
        ValueError: if holding_cost is 0 or negative.

    Example:
        >>> round(calculate_eoq(2920, 150, 6), 1)
        382.1
    """
    annual_demand = check_number("annual_demand", annual_demand, minimum=0)
    order_cost = check_number("order_cost", order_cost, minimum=0)
    holding_cost = check_number("holding_cost", holding_cost, strictly_positive=True)
    return math.sqrt(2 * annual_demand * order_cost / holding_cost)


def orders_per_year(annual_demand, order_quantity):
    """Return the number of orders per year: D / Q.

    Example:
        >>> orders_per_year(1000, 200)
        5.0
    """
    annual_demand = check_number("annual_demand", annual_demand, minimum=0)
    order_quantity = check_number("order_quantity", order_quantity, strictly_positive=True)
    return annual_demand / order_quantity


def total_annual_cost(annual_demand, order_quantity, order_cost, holding_cost,
                      unit_price=0):
    """Return total annual cost in Rand: (D/Q)*S + (Q/2)*H + D*unit_price.

    Example:
        >>> round(total_annual_cost(2920, 380, 150, 6), 2)
        2292.63
    """
    order_cost = check_number("order_cost", order_cost, minimum=0)
    holding_cost = check_number("holding_cost", holding_cost, minimum=0)
    unit_price = check_number("unit_price", unit_price, minimum=0)
    n_orders = orders_per_year(annual_demand, order_quantity)
    return (n_orders * order_cost
            + (float(order_quantity) / 2) * holding_cost
            + float(annual_demand) * unit_price)