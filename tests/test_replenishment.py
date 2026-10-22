"""Tests for models/replenishment.py.

Expected values are worked out by hand (shown in each test) so the code is
checked against the formulas, not against itself.
"""

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


# ---------------------------------------------------------------- z-score

@pytest.mark.parametrize("level, expected", [
    (0.50, 0.000),
    (0.90, 1.282),
    (0.95, 1.645),   # z-table value for 95%
    (0.98, 2.054),
    (0.99, 2.326),
])
def test_z_score_matches_z_table(level, expected):
    assert z_score(level) == pytest.approx(expected, abs=0.001)


@pytest.mark.parametrize("bad", [0, 1, -0.1, 1.5, 95])
def test_z_score_rejects_levels_outside_0_1(bad):
    with pytest.raises(ValueError):
        z_score(bad)


# ---------------------------------------------------------- safety stock

def test_safety_stock_95_percent_hand_calculation():
    # z = 1.645, sigma = 10 units/day, L = 4 days
    # SS = 1.645 * 10 * sqrt(4) = 1.645 * 10 * 2 = 32.9 units
    assert safety_stock(10, 4, 0.95) == pytest.approx(32.9, abs=0.01)


def test_safety_stock_metformin_with_table_z():
    # Alerts page: z = 2.05, sigma = 4.5, L = 3
    # SS = 2.05 * 4.5 * 1.7321 = 15.98 -> displayed as 16
    ss = safety_stock(4.5, 3, z=2.05)
    assert ss == pytest.approx(15.979, abs=0.001)
    assert round(ss) == 16


def test_safety_stock_metformin_with_exact_98_percent():
    # Exact z for 98% is 2.0537 -> SS = 16.01, still 16 on screen
    assert round(safety_stock(4.5, 3, 0.98)) == 16


def test_safety_stock_is_zero_with_no_variability():
    assert safety_stock(0, 5, 0.95) == 0


def test_safety_stock_is_zero_with_no_lead_time():
    assert safety_stock(4.5, 0, 0.95) == 0


def test_safety_stock_needs_exactly_one_of_level_or_z():
    with pytest.raises(ValueError):
        safety_stock(4.5, 3)
    with pytest.raises(ValueError):
        safety_stock(4.5, 3, 0.95, z=1.645)


@pytest.mark.parametrize("std, lead", [(-1, 3), (4.5, -2)])
def test_safety_stock_rejects_negatives(std, lead):
    with pytest.raises(ValueError):
        safety_stock(std, lead, 0.95)


def test_safety_stock_rejects_text():
    with pytest.raises(TypeError):
        safety_stock("4.5", 3, 0.95)


# ---------------------------------------------------------- reorder point

def test_reorder_point_95_percent_example():
    # d = 50/day, L = 4, SS = 32.9  ->  ROP = 50*4 + 32.9 = 232.9
    ss = safety_stock(10, 4, 0.95)
    assert reorder_point(50, 4, ss) == pytest.approx(232.9, abs=0.01)


def test_reorder_point_metformin():
    # d = 8, L = 3, SS = 16 -> ROP = 24 + 16 = 40
    assert reorder_point(8, 3, 16) == 40


def test_reorder_point_zero_demand_is_just_safety_stock():
    assert reorder_point(0, 5, 12) == 12


def test_reorder_point_rejects_negative_demand():
    with pytest.raises(ValueError):
        reorder_point(-8, 3, 16)


# --------------------------------------------------------------------- EOQ

def test_eoq_textbook_example():
    # D = 1000, S = R10, H = R0.50 -> sqrt(2*1000*10/0.5) = sqrt(40000) = 200
    assert calculate_eoq(1000, 10, 0.5) == pytest.approx(200)


def test_eoq_metformin():
    # D = 8 * 365 = 2920, S = R150, H = R6
    # sqrt(2*2920*150/6) = sqrt(146000) = 382.10
    assert calculate_eoq(2920, 150, 6) == pytest.approx(382.10, abs=0.01)


def test_eoq_zero_demand_is_zero():
    assert calculate_eoq(0, 150, 6) == 0


def test_eoq_rejects_zero_holding_cost():
    with pytest.raises(ValueError):
        calculate_eoq(1000, 10, 0)


def test_eoq_rejects_infinity_and_nan():
    with pytest.raises(ValueError):
        calculate_eoq(math.inf, 10, 1)
    with pytest.raises(ValueError):
        calculate_eoq(math.nan, 10, 1)


# --------------------------------------------------- orders and annual cost

def test_orders_per_year_textbook_example():
    # 1000 / 200 = 5 orders
    assert orders_per_year(1000, 200) == 5


def test_orders_per_year_rejects_zero_quantity():
    with pytest.raises(ValueError):
        orders_per_year(1000, 0)


def test_total_annual_cost_textbook_example():
    # ordering = 5 * 10 = 50; holding = 200/2 * 0.5 = 50; total = 100
    assert total_annual_cost(1000, 200, 10, 0.5) == pytest.approx(100)


def test_total_annual_cost_with_purchase_price():
    # 100 + 1000 * R2 = 2100
    assert total_annual_cost(1000, 200, 10, 0.5, unit_price=2) == pytest.approx(2100)


def test_eoq_gives_lowest_cost_and_equal_cost_split():
    q = calculate_eoq(1000, 10, 0.5)
    best = total_annual_cost(1000, q, 10, 0.5)
    assert best < total_annual_cost(1000, q * 0.8, 10, 0.5)
    assert best < total_annual_cost(1000, q * 1.2, 10, 0.5)
    # At the EOQ, ordering cost equals holding cost
    assert orders_per_year(1000, q) * 10 == pytest.approx(q / 2 * 0.5)


def test_total_annual_cost_metformin():
    # 2920/380 * 150 = 1152.63; 380/2 * 6 = 1140; total 2292.63
    assert total_annual_cost(2920, 380, 150, 6) == pytest.approx(2292.63, abs=0.01)


# ------------------------------------------------ recommended order quantity

def test_recommended_quantity_metformin_matches_alerts_page():
    r = recommended_order_quantity(8, 18, 150, 6, shelf_life_days=180, pack_size=10)
    assert r["annual_demand"] == 2920
    assert r["eoq"] == pytest.approx(382.10, abs=0.01)
    assert r["eoq_rounded"] == 380          # nearest 10
    assert r["expiry_cap"] == 1422          # 8*180 - 18
    assert r["capped"] is False
    assert r["order_quantity"] == 380


def test_recommended_quantity_is_capped_by_expiry():
    # Slow mover: d = 1/day, 60 days shelf life, 10 in stock
    # EOQ = sqrt(2*365*150/6) = 135.1 -> 140 (packs of 10)
    # cap = 1*60 - 10 = 50 -> order 50
    r = recommended_order_quantity(1, 10, 150, 6, shelf_life_days=60, pack_size=10)
    assert r["eoq_rounded"] == 140
    assert r["expiry_cap"] == 50
    assert r["capped"] is True
    assert r["order_quantity"] == 50


def test_recommended_quantity_cap_rounds_down_to_whole_packs():
    # cap = 1*60 - 15 = 45 -> 40 (never order stock that would expire)
    r = recommended_order_quantity(1, 15, 150, 6, shelf_life_days=60, pack_size=10)
    assert r["order_quantity"] == 40


def test_recommended_quantity_zero_when_stock_already_covers_shelf_life():
    r = recommended_order_quantity(1, 100, 150, 6, shelf_life_days=60)
    assert r["expiry_cap"] == 0
    assert r["order_quantity"] == 0


def test_recommended_quantity_zero_demand():
    r = recommended_order_quantity(0, 20, 150, 6, shelf_life_days=180, pack_size=10)
    assert r["order_quantity"] == 0


def test_recommended_quantity_at_least_one_pack():
    # D = 0.365, EOQ = sqrt(2*0.365*150/6) = 4.27 -> rounds to 0 packs,
    # but a non-zero demand still orders one full pack of 10
    r = recommended_order_quantity(0.001, 0, 150, 6, pack_size=10)
    assert r["order_quantity"] == 10


def test_recommended_quantity_without_shelf_life_has_no_cap():
    r = recommended_order_quantity(8, 18, 150, 6)
    assert r["expiry_cap"] is None
    assert r["order_quantity"] == 382


@pytest.mark.parametrize("pack", [0, -10, 2.5, True])
def test_recommended_quantity_rejects_bad_pack_size(pack):
    with pytest.raises(ValueError):
        recommended_order_quantity(8, 18, 150, 6, pack_size=pack)


# ---------------------------------------------------------- reorder status

def test_status_matches_dashboard_rows():
    assert reorder_status(240, 120, 20) == STATUS_SUFFICIENT    # Amoxicillin
    assert reorder_status(60, 50, 5) == STATUS_LOW              # Paracetamol
    assert reorder_status(18, 40, 8) == STATUS_REORDER          # Metformin
    assert reorder_status(310, 150, 11.4) == STATUS_SUFFICIENT  # Ibuprofen
    assert reorder_status(85, 45, 2.9) == STATUS_SUFFICIENT     # Cetirizine


def test_status_exactly_at_reorder_point_needs_reorder():
    assert reorder_status(40, 40, 8) == STATUS_REORDER


def test_status_boundary_of_warning_window():
    # (64 - 40) / 8 = 3 days -> Low; (65 - 40) / 8 = 3.1 days -> Sufficient
    assert reorder_status(64, 40, 8) == STATUS_LOW
    assert reorder_status(65, 40, 8) == STATUS_SUFFICIENT


def test_status_zero_demand_above_reorder_point_is_sufficient():
    assert reorder_status(41, 40, 0) == STATUS_SUFFICIENT


def test_status_zero_stock():
    assert reorder_status(0, 40, 8) == STATUS_REORDER


# --------------------------------------------- configurable threshold (Obj. 2)

def test_percentage_threshold_25_percent():
    # Proposal example: 25% of a 200-unit normal level = 50 units
    assert percentage_threshold(200, 25) == 50


def test_percentage_threshold_rejects_over_100():
    with pytest.raises(ValueError):
        percentage_threshold(200, 125)


def test_pharmacist_override_replaces_calculated_reorder_point():
    assert effective_threshold(40) == 40
    assert effective_threshold(40, 55) == 55
    # Raising the threshold changes stock of 50 from Low to Reorder Needed
    assert reorder_status(50, effective_threshold(40), 8) == STATUS_LOW
    assert reorder_status(50, effective_threshold(40, 55), 8) == STATUS_REORDER


def test_override_of_zero_is_respected():
    assert effective_threshold(40, 0) == 0


def test_days_of_stock():
    assert days_of_stock(18, 8) == 2.25
    assert days_of_stock(18, 0) == math.inf