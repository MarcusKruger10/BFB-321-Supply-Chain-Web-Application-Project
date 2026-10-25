import math
from statistics import NormalDist

from models._validation import check_number

DAYS_PER_YEAR = 365  # days used to turn daily demand into annual demand

STATUS_SUFFICIENT = "Sufficient"  # status when stock is well above the threshold
STATUS_LOW = "Low"  # status when stock will reach the threshold within a few days
STATUS_REORDER = "Reorder Needed"  # status when stock is at or below the threshold


def z_score(service_level):
    """Return the z value for a service level, e.g. 0.95 gives 1.645."""
    service_level = check_number("service_level", service_level)  # chance of not running out, between 0 and 1
    if not 0 < service_level < 1:
        raise ValueError(
            f"service_level must be between 0 and 1 (e.g. 0.95), got {service_level}"
        )
    return NormalDist().inv_cdf(service_level)


def safety_stock(daily_demand_std, lead_time_days, service_level=None, *, z=None):
    """Return the safety stock in units: z x demand std x square root of lead time."""
    daily_demand_std = check_number("daily_demand_std", daily_demand_std, minimum=0)  # standard deviation of daily demand (units/day)
    lead_time_days = check_number("lead_time_days", lead_time_days, minimum=0)  # days between ordering and receiving stock
    if (service_level is None) == (z is None):
        raise ValueError("give exactly one of service_level or z")
    if z is None:
        z = z_score(service_level)  # z value worked out from the service level
    else:
        z = check_number("z", z, minimum=0)  # z value given directly, e.g. from a z-table
    return z * daily_demand_std * math.sqrt(lead_time_days)


def reorder_point(avg_daily_demand, lead_time_days, safety_stock_units):
    """Return the stock level at which a new order should be placed."""
    avg_daily_demand = check_number("avg_daily_demand", avg_daily_demand, minimum=0)  # average units used per day
    lead_time_days = check_number("lead_time_days", lead_time_days, minimum=0)  # days between ordering and receiving stock
    safety_stock_units = check_number("safety_stock_units", safety_stock_units, minimum=0)  # extra buffer stock in units
    return avg_daily_demand * lead_time_days + safety_stock_units


def calculate_eoq(annual_demand, order_cost, holding_cost):
    """Return the economic order quantity: square root of (2 x D x S / H)."""
    annual_demand = check_number("annual_demand", annual_demand, minimum=0)  # units used per year (D)
    order_cost = check_number("order_cost", order_cost, minimum=0)  # cost of placing one order in Rand (S)
    holding_cost = check_number("holding_cost", holding_cost, strictly_positive=True)  # cost of holding one unit for a year in Rand (H)
    return math.sqrt(2 * annual_demand * order_cost / holding_cost)


def orders_per_year(annual_demand, order_quantity):
    """Return how many orders are placed per year: D / Q."""
    annual_demand = check_number("annual_demand", annual_demand, minimum=0)  # units used per year (D)
    order_quantity = check_number("order_quantity", order_quantity, strictly_positive=True)  # units in each order (Q)
    return annual_demand / order_quantity


def total_annual_cost(annual_demand, order_quantity, order_cost, holding_cost,
                      unit_price=0):
    """Return the total yearly inventory cost in Rand for an order quantity."""
    order_cost = check_number("order_cost", order_cost, minimum=0)  # cost of placing one order in Rand (S)
    holding_cost = check_number("holding_cost", holding_cost, minimum=0)  # cost of holding one unit for a year in Rand (H)
    unit_price = check_number("unit_price", unit_price, minimum=0)  # purchase price of one unit in Rand
    n_orders = orders_per_year(annual_demand, order_quantity)  # number of orders per year
    return (n_orders * order_cost
            + (float(order_quantity) / 2) * holding_cost
            + float(annual_demand) * unit_price)


def _round_to_pack(quantity, pack_size, mode):
    """Round a quantity to whole packs, either to the nearest pack or down."""
    packs = quantity / pack_size  # quantity expressed as a number of packs
    packs = math.floor(packs) if mode == "down" else math.floor(packs + 0.5)  # whole number of packs after rounding
    return int(packs * pack_size)


def recommended_order_quantity(avg_daily_demand, stock_on_hand, order_cost,
                               holding_cost, shelf_life_days=None, pack_size=1):
    """Return the suggested order quantity and each step used to calculate it."""
    avg_daily_demand = check_number("avg_daily_demand", avg_daily_demand, minimum=0)  # average units used per day
    stock_on_hand = check_number("stock_on_hand", stock_on_hand, minimum=0)  # units currently in stock
    if isinstance(pack_size, bool) or not isinstance(pack_size, int) or pack_size < 1:
        raise ValueError(f"pack_size must be a whole number >= 1, got {pack_size!r}")

    annual_demand = avg_daily_demand * DAYS_PER_YEAR  # units used per year
    eoq = calculate_eoq(annual_demand, order_cost, holding_cost)  # unrounded economic order quantity

    if annual_demand == 0:
        eoq_rounded = 0  # no demand, so nothing to order
    else:
        eoq_rounded = max(pack_size, _round_to_pack(eoq, pack_size, "nearest"))  # EOQ rounded to whole packs, at least one pack

    order_quantity = eoq_rounded  # final order, before the expiry check
    expiry_cap = None  # most units that can be used before expiry (None if no shelf life given)
    capped = False  # True if the expiry cap reduced the order
    if shelf_life_days is not None:
        shelf_life_days = check_number("shelf_life_days", shelf_life_days,
                                       strictly_positive=True)  # days new stock lasts before it expires
        expiry_cap = max(0.0, avg_daily_demand * shelf_life_days - stock_on_hand)  # units that can be sold before new stock expires
        if order_quantity > expiry_cap:
            order_quantity = _round_to_pack(expiry_cap, pack_size, "down")  # order cut back to the expiry cap
            capped = True

    return {
        "annual_demand": annual_demand,
        "eoq": eoq,
        "eoq_rounded": eoq_rounded,
        "expiry_cap": expiry_cap,
        "capped": capped,
        "order_quantity": int(order_quantity),
    }


def percentage_threshold(target_stock, percent=25):
    """Return a threshold set as a percentage of a product's normal stock level."""
    target_stock = check_number("target_stock", target_stock, minimum=0)  # product's normal stock level in units
    percent = check_number("percent", percent, minimum=0)  # threshold as a percentage, 0 to 100
    if percent > 100:
        raise ValueError(f"percent must be between 0 and 100, got {percent}")
    return target_stock * percent / 100


def effective_threshold(calculated_reorder_point, pharmacist_override=None):
    """Return the pharmacist's threshold if one is set, otherwise the calculated one."""
    calculated_reorder_point = check_number(
        "calculated_reorder_point", calculated_reorder_point, minimum=0)  # reorder point worked out by the system
    if pharmacist_override is None:
        return calculated_reorder_point
    return check_number("pharmacist_override", pharmacist_override, minimum=0)


def days_of_stock(stock_on_hand, avg_daily_demand):
    """Return how many days the current stock will last at average demand."""
    stock_on_hand = check_number("stock_on_hand", stock_on_hand, minimum=0)  # units currently in stock
    avg_daily_demand = check_number("avg_daily_demand", avg_daily_demand, minimum=0)  # average units used per day
    if avg_daily_demand == 0:
        return math.inf
    return stock_on_hand / avg_daily_demand


def reorder_status(stock_on_hand, reorder_point_units, avg_daily_demand,
                   warning_days=3):
    """Return the dashboard status: Reorder Needed, Low or Sufficient."""
    stock_on_hand = check_number("stock_on_hand", stock_on_hand, minimum=0)  # units currently in stock
    reorder_point_units = check_number("reorder_point_units", reorder_point_units, minimum=0)  # threshold in units
    avg_daily_demand = check_number("avg_daily_demand", avg_daily_demand, minimum=0)  # average units used per day
    warning_days = check_number("warning_days", warning_days, minimum=0)  # days of warning before stock reaches the threshold

    if stock_on_hand <= reorder_point_units:
        return STATUS_REORDER
    if avg_daily_demand > 0:
        days_to_reorder = (stock_on_hand - reorder_point_units) / avg_daily_demand  # days until stock falls to the threshold
        if days_to_reorder <= warning_days:
            return STATUS_LOW
    return STATUS_SUFFICIENT