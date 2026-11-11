import pytest
from water_utility_billing import calculate_water_bill, check_meter_tampering


def acct(usage, active=True, commercial=False, waiver=False):
    return {"is_active": active, "is_commercial": commercial,
            "has_leak_waiver": waiver, "usage_blocks": usage}


# ---------- calculate_water_bill: validation ----------
def test_single_active_residential():
    r = calculate_water_bill([acct([30])], 10.0)
    assert r == {"total_billed": 55.0, "status": "NORMAL"}


def test_invalid_accounts_not_list():
    with pytest.raises(ValueError):
        calculate_water_bill("not a list", 10.0)


def test_invalid_accounts_none():
    with pytest.raises(ValueError):
        calculate_water_bill(None, 10.0)


def test_invalid_negative_base_fee():
    with pytest.raises(ValueError):
        calculate_water_bill([acct([30])], -1.0)


def test_zero_base_fee_is_valid():
    assert calculate_water_bill([acct([10])], 0.0)["total_billed"] == 15.0


# ---------- active / inactive / empty ----------
def test_inactive_account_skipped():
    r = calculate_water_bill([acct([30], active=False)], 10.0)
    assert r == {"total_billed": 0.0, "status": "NO_ACTIVITY"}


def test_missing_is_active_key_defaults_inactive():
    r = calculate_water_bill([{"usage_blocks": [30]}], 10.0)
    assert r["status"] == "NO_ACTIVITY"


def test_empty_accounts_list():
    assert calculate_water_bill([], 10.0) == {"total_billed": 0.0, "status": "NO_ACTIVITY"}


def test_active_account_with_no_usage_blocks():
    # inner for-loop never runs; only base fee billed
    assert calculate_water_bill([acct([])], 10.0)["total_billed"] == 10.0


# ---------- usage tiers ----------
def test_low_tier_boundary_50():
    # 50 is NOT > 50 -> 1.5 rate: 10 + 75 = 85
    assert calculate_water_bill([acct([50])], 10.0)["total_billed"] == 85.0


def test_mid_tier_51():
    # 10 + 51*2.5 = 137.5
    assert calculate_water_bill([acct([51])], 10.0)["total_billed"] == 137.5


def test_mid_tier_boundary_100():
    # 100 is NOT > 100 -> 2.5 rate: 10 + 250 = 260
    r = calculate_water_bill([acct([100])], 10.0)
    assert r["total_billed"] == 260.0
    assert r["status"] == "NORMAL"  # no flag raised at exactly 100


def test_zero_and_negative_usage_flagged():
    # 0 and -5 skipped: 10 + 20*1.5 = 40
    assert calculate_water_bill([acct([0, -5, 20])], 10.0)["total_billed"] == 40.0


def test_commercial_high_usage_no_break():
    # commercial: 10 + 150*3.5 + 20*1.5 = 565 (loop continues after >100)
    assert calculate_water_bill([acct([150, 20], commercial=True)], 10.0)["total_billed"] == 565.0


def test_residential_high_usage_breaks():
    # 10 + 150*4.5 = 685; trailing 20 ignored due to break
    assert calculate_water_bill([acct([150, 20])], 10.0)["total_billed"] == 685.0


# ---------- leak waiver ----------
def test_waiver_above_threshold():
    # 10 + 80*2.5 = 210 -> 160
    assert calculate_water_bill([acct([80], waiver=True)], 10.0)["total_billed"] == 160.0


def test_waiver_exactly_200_not_applied():
    # 10 + 76*2.5 = 200 -> NOT > 200, no deduction
    assert calculate_water_bill([acct([76], waiver=True)], 10.0)["total_billed"] == 200.0


def test_waiver_below_threshold_not_applied():
    assert calculate_water_bill([acct([30], waiver=True)], 10.0)["total_billed"] == 55.0


def test_large_bill_without_waiver_keeps_full_amount():
    assert calculate_water_bill([acct([80])], 10.0)["total_billed"] == 210.0


# ---------- status ----------
def test_excessive_flags_six():
    r = calculate_water_bill([acct([0]) for _ in range(6)], 10.0)
    assert r["status"] == "EXCESSIVE_FLAGS"
    assert r["total_billed"] == 60.0


def test_five_flags_is_still_normal():
    r = calculate_water_bill([acct([0]) for _ in range(5)], 10.0)
    assert r["status"] == "NORMAL"


def test_excessive_flags_takes_priority_over_no_activity():
    r = calculate_water_bill([acct([0]) for _ in range(6)], 0.0)
    assert r == {"total_billed": 0.0, "status": "EXCESSIVE_FLAGS"}


def test_multiple_accounts_total():
    r = calculate_water_bill([acct([30]), acct([30], active=False), acct([60], commercial=True)], 10.0)
    assert r["total_billed"] == 55.0 + 160.0  # 10 + 60*2.5 = 160


# ---------- check_meter_tampering ----------
def test_no_data_empty_list():
    assert check_meter_tampering([]) == "NO_DATA"


def test_no_data_none():
    assert check_meter_tampering(None) == "NO_DATA"


def test_tamper_two_consecutive_negatives():
    assert check_meter_tampering([[5, -1, -2]]) == "TAMPER_SUSPECTED"


def test_tamper_found_in_second_meter():
    assert check_meter_tampering([[1, 2, 3], [-1, -1]]) == "TAMPER_SUSPECTED"


def test_single_negative_is_clear():
    assert check_meter_tampering([[5, -1]]) == "CLEAR"


def test_negative_counter_resets_on_positive():
    assert check_meter_tampering([[-1, 3, -2, 4, -3]]) == "CLEAR"


def test_zero_delta_resets_counter():
    assert check_meter_tampering([[-1, 0, -1]]) == "CLEAR"


def test_all_positive_clear():
    assert check_meter_tampering([[1, 2, 3], [4, 5]]) == "CLEAR"


def test_meter_with_no_readings():
    assert check_meter_tampering([[]]) == "CLEAR"
