import math

import pytest

from models.replenishment import (
    STATUS_LOW,
    STATUS_REORDER,
    STATUS_SUFFICIENT,
    calculate_eoq,
    days_of_stock,
    effective_threshold,
    orders_per_year,
    percentage_threshold,
    recommended_order_quantity,
    reorder_point,
    reorder_status,
    safety_stock,
    total_annual_cost,
    z_score,
)


@pytest.mark.parametrize("level, expected", [
    (0.50, 0.000),
    (0.90, 1.282),
    (0.95, 1.645),
    (0.98, 2.054),
    (0.99, 2.326),
])
def test_z_score_matches_z_table(level, expected):
    """Check z values against the z-table, e.g. 95% gives 1.645."""
    assert z_score(level) == pytest.approx(expected, abs=0.001)


@pytest.mark.parametrize("bad", [0, 1, -0.1, 1.5, 95])
def test_z_score_rejects_levels_outside_0_1(bad):
    """Check that service levels outside 0 to 1 (such as 95) are rejected."""
    with pytest.raises(ValueError):
        z_score(bad)


def test_safety_stock_95_percent_hand_calculation():
    """Check SS = 1.645 x 10 x sqrt(4) = 32.9 units."""
    assert safety_stock(10, 4, 0.95) == pytest.approx(32.9, abs=0.01)


def test_safety_stock_metformin_with_table_z():
    """Check the alerts page: SS = 2.05 x 4.5 x sqrt(3) = 15.98, shown as 16."""
    ss = safety_stock(4.5, 3, z=2.05)  # Metformin safety stock in units
    assert ss == pytest.approx(15.979, abs=0.001)
    assert round(ss) == 16


def test_safety_stock_metformin_with_exact_98_percent():
    """Check that the exact 98% z (2.0537) still rounds to 16 units."""
    assert round(safety_stock(4.5, 3, 0.98)) == 16


def test_safety_stock_is_zero_with_no_variability():
    """Check that demand with no variation needs no safety stock."""
    assert safety_stock(0, 5, 0.95) == 0


def test_safety_stock_is_zero_with_no_lead_time():
    """Check that a lead time of 0 days needs no safety stock."""
    assert safety_stock(4.5, 0, 0.95) == 0


def test_safety_stock_needs_exactly_one_of_level_or_z():
    """Check that giving neither or both of service level and z is rejected."""
    with pytest.raises(ValueError):
        safety_stock(4.5, 3)
    with pytest.raises(ValueError):
        safety_stock(4.5, 3, 0.95, z=1.645)


@pytest.mark.parametrize("std, lead", [(-1, 3), (4.5, -2)])
def test_safety_stock_rejects_negatives(std, lead):
    """Check that a negative standard deviation or lead time is rejected."""
    with pytest.raises(ValueError):
        safety_stock(std, lead, 0.95)


def test_safety_stock_rejects_text():
    """Check that text instead of a number is rejected."""
    with pytest.raises(TypeError):
        safety_stock("4.5", 3, 0.95)


def test_reorder_point_95_percent_example():
    """Check ROP = 50 x 4 + 32.9 = 232.9 units."""
    ss = safety_stock(10, 4, 0.95)  # safety stock for the 95% example
    assert reorder_point(50, 4, ss) == pytest.approx(232.9, abs=0.01)


def test_reorder_point_metformin():
    """Check the alerts page: ROP = 8 x 3 + 16 = 40 units."""
    assert reorder_point(8, 3, 16) == 40


def test_reorder_point_zero_demand_is_just_safety_stock():
    """Check that with no demand the reorder point equals the safety stock."""
    assert reorder_point(0, 5, 12) == 12


def test_reorder_point_rejects_negative_demand():
    """Check that negative demand is rejected."""
    with pytest.raises(ValueError):
        reorder_point(-8, 3, 16)


def test_eoq_textbook_example():
    """Check EOQ = sqrt(2 x 1000 x 10 / 0.5) = 200 units."""
    assert calculate_eoq(1000, 10, 0.5) == pytest.approx(200)


def test_eoq_metformin():
    """Check the alerts page: EOQ = sqrt(2 x 2920 x 150 / 6) = 382.1 units."""
    assert calculate_eoq(2920, 150, 6) == pytest.approx(382.10, abs=0.01)


def test_eoq_zero_demand_is_zero():
    """Check that no demand gives an EOQ of 0."""
    assert calculate_eoq(0, 150, 6) == 0


def test_eoq_rejects_zero_holding_cost():
    """Check that a holding cost of 0 is rejected (EOQ would divide by 0)."""
    with pytest.raises(ValueError):
        calculate_eoq(1000, 10, 0)


def test_eoq_rejects_infinity_and_nan():
    """Check that infinity and NaN are rejected."""
    with pytest.raises(ValueError):
        calculate_eoq(math.inf, 10, 1)
    with pytest.raises(ValueError):
        calculate_eoq(math.nan, 10, 1)


def test_orders_per_year_textbook_example():
    """Check 1000 / 200 = 5 orders per year."""
    assert orders_per_year(1000, 200) == 5


def test_orders_per_year_rejects_zero_quantity():
    """Check that an order quantity of 0 is rejected."""
    with pytest.raises(ValueError):
        orders_per_year(1000, 0)


def test_total_annual_cost_textbook_example():
    """Check cost = 5 x 10 + 200 / 2 x 0.5 = 50 + 50 = R100."""
    assert total_annual_cost(1000, 200, 10, 0.5) == pytest.approx(100)


def test_total_annual_cost_with_purchase_price():
    """Check cost = 100 + 1000 x R2 = R2100 when the unit price is included."""
    assert total_annual_cost(1000, 200, 10, 0.5, unit_price=2) == pytest.approx(2100)


def test_eoq_gives_lowest_cost_and_equal_cost_split():
    """Check that the EOQ is cheaper than 20% less or more, and ordering cost equals holding cost."""
    q = calculate_eoq(1000, 10, 0.5)  # economic order quantity
    best = total_annual_cost(1000, q, 10, 0.5)  # total cost at the EOQ
    assert best < total_annual_cost(1000, q * 0.8, 10, 0.5)
    assert best < total_annual_cost(1000, q * 1.2, 10, 0.5)
    assert orders_per_year(1000, q) * 10 == pytest.approx(q / 2 * 0.5)


def test_total_annual_cost_metformin():
    """Check cost = 2920 / 380 x 150 + 380 / 2 x 6 = 1152.63 + 1140 = R2292.63."""
    assert total_annual_cost(2920, 380, 150, 6) == pytest.approx(2292.63, abs=0.01)


def test_recommended_quantity_metformin_matches_alerts_page():
    """Check the alerts page: EOQ 382.1 rounds to 380, cap 8 x 180 - 18 = 1422, order 380."""
    r = recommended_order_quantity(8, 18, 150, 6, shelf_life_days=180, pack_size=10)  # Metformin order working
    assert r["annual_demand"] == 2920
    assert r["eoq"] == pytest.approx(382.10, abs=0.01)
    assert r["eoq_rounded"] == 380
    assert r["expiry_cap"] == 1422
    assert r["capped"] is False
    assert r["order_quantity"] == 380


def test_recommended_quantity_is_capped_by_expiry():
    """Check a slow mover: EOQ 140 is cut to the cap 1 x 60 - 10 = 50 units."""
    r = recommended_order_quantity(1, 10, 150, 6, shelf_life_days=60, pack_size=10)  # slow-moving product order working
    assert r["eoq_rounded"] == 140
    assert r["expiry_cap"] == 50
    assert r["capped"] is True
    assert r["order_quantity"] == 50


def test_recommended_quantity_cap_rounds_down_to_whole_packs():
    """Check that a cap of 1 x 60 - 15 = 45 rounds down to 40 units."""
    r = recommended_order_quantity(1, 15, 150, 6, shelf_life_days=60, pack_size=10)  # order working with a cap of 45
    assert r["order_quantity"] == 40


def test_recommended_quantity_zero_when_stock_already_covers_shelf_life():
    """Check that nothing is ordered when current stock already lasts the shelf life."""
    r = recommended_order_quantity(1, 100, 150, 6, shelf_life_days=60)  # order working with too much stock
    assert r["expiry_cap"] == 0
    assert r["order_quantity"] == 0


def test_recommended_quantity_zero_demand():
    """Check that nothing is ordered when there is no demand."""
    r = recommended_order_quantity(0, 20, 150, 6, shelf_life_days=180, pack_size=10)  # order working with no demand
    assert r["order_quantity"] == 0


def test_recommended_quantity_at_least_one_pack():
    """Check that a tiny EOQ (4.27) still orders one full pack of 10."""
    r = recommended_order_quantity(0.001, 0, 150, 6, pack_size=10)  # order working with very low demand
    assert r["order_quantity"] == 10


def test_recommended_quantity_without_shelf_life_has_no_cap():
    """Check that no expiry cap is applied when no shelf life is given."""
    r = recommended_order_quantity(8, 18, 150, 6)  # order working without a shelf life
    assert r["expiry_cap"] is None
    assert r["order_quantity"] == 382


@pytest.mark.parametrize("pack", [0, -10, 2.5, True])
def test_recommended_quantity_rejects_bad_pack_size(pack):
    """Check that pack sizes that are not whole numbers of 1 or more are rejected."""
    with pytest.raises(ValueError):
        recommended_order_quantity(8, 18, 150, 6, pack_size=pack)


def test_status_matches_dashboard_rows():
    """Check the status of all five products on the dashboard."""
    assert reorder_status(240, 120, 20) == STATUS_SUFFICIENT
    assert reorder_status(60, 50, 5) == STATUS_LOW
    assert reorder_status(18, 40, 8) == STATUS_REORDER
    assert reorder_status(310, 150, 11.4) == STATUS_SUFFICIENT
    assert reorder_status(85, 45, 2.9) == STATUS_SUFFICIENT


def test_status_exactly_at_reorder_point_needs_reorder():
    """Check that stock exactly at the reorder point needs a reorder."""
    assert reorder_status(40, 40, 8) == STATUS_REORDER


def test_status_boundary_of_warning_window():
    """Check (64 - 40) / 8 = 3 days is Low and (65 - 40) / 8 = 3.1 days is Sufficient."""
    assert reorder_status(64, 40, 8) == STATUS_LOW
    assert reorder_status(65, 40, 8) == STATUS_SUFFICIENT


def test_status_zero_demand_above_reorder_point_is_sufficient():
    """Check that with no demand, stock above the threshold is Sufficient."""
    assert reorder_status(41, 40, 0) == STATUS_SUFFICIENT


def test_status_zero_stock():
    """Check that zero stock needs a reorder."""
    assert reorder_status(0, 40, 8) == STATUS_REORDER


def test_percentage_threshold_25_percent():
    """Check the proposal example: 25% of 200 units = 50 units."""
    assert percentage_threshold(200, 25) == 50


def test_percentage_threshold_rejects_over_100():
    """Check that a percentage above 100 is rejected."""
    with pytest.raises(ValueError):
        percentage_threshold(200, 125)


def test_pharmacist_override_replaces_calculated_reorder_point():
    """Check that an override of 55 replaces the ROP of 40 and changes the status."""
    assert effective_threshold(40) == 40
    assert effective_threshold(40, 55) == 55
    assert reorder_status(50, effective_threshold(40), 8) == STATUS_LOW
    assert reorder_status(50, effective_threshold(40, 55), 8) == STATUS_REORDER


def test_override_of_zero_is_respected():
    """Check that an override of 0 is used and not ignored."""
    assert effective_threshold(40, 0) == 0


def test_days_of_stock():
    """Check 18 / 8 = 2.25 days, and endless stock when demand is 0."""
    assert days_of_stock(18, 8) == 2.25
    assert days_of_stock(18, 0) == math.inf