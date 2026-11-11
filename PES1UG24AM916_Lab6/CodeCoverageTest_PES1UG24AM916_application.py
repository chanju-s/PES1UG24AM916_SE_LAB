import pytest
from water_utility_billing import calculate_water_bill, check_meter_tampering


def acct(usage, active=True, commercial=False, waiver=False):
    return {"is_active": active, "is_commercial": commercial,
            "has_leak_waiver": waiver, "usage_blocks": usage}


# ---------- calculate_water_bill ----------
def test_single_active_residential():
    r = calculate_water_bill([acct([30])], 10.0)
    assert r == {"total_billed": 55.0, "status": "NORMAL"}


def test_invalid_accounts_type():
    with pytest.raises(ValueError):
        calculate_water_bill("not a list", 10.0)


def test_inactive_account_skipped():
    r = calculate_water_bill([acct([30], active=False)], 10.0)
    assert r["total_billed"] == 0.0
    assert r["status"] == "NO_ACTIVITY"


def test_mid_tier_usage():
    # 10 + 75*2.5 = 197.5
    assert calculate_water_bill([acct([75])], 10.0)["total_billed"] == 197.5


def test_zero_and_negative_usage_flagged():
    # 10 + 20*1.5 = 40 (0 and -5 skipped)
    r = calculate_water_bill([acct([0, -5, 20])], 10.0)
    assert r["total_billed"] == 40.0


def test_commercial_high_usage():
    # 10 + 150*3.5 = 535
    assert calculate_water_bill([acct([150], commercial=True)], 10.0)["total_billed"] == 535.0


def test_residential_high_usage_breaks():
    # 10 + 150*4.5 = 685; the trailing 20 is ignored because of break
    assert calculate_water_bill([acct([150, 20])], 10.0)["total_billed"] == 685.0


def test_leak_waiver_applied():
    # 10 + 80*2.5 = 210 -> 210 - 50 = 160
    assert calculate_water_bill([acct([80], waiver=True)], 10.0)["total_billed"] == 160.0


def test_excessive_flags():
    r = calculate_water_bill([acct([0]) for _ in range(6)], 10.0)
    assert r["status"] == "EXCESSIVE_FLAGS"


# ---------- check_meter_tampering ----------
def test_no_data():
    assert check_meter_tampering([]) == "NO_DATA"


def test_tamper_suspected():
    assert check_meter_tampering([[5, -1, -2]]) == "TAMPER_SUSPECTED"


def test_clear_with_reset():
    assert check_meter_tampering([[5, -1, 3, -2, 4]]) == "CLEAR"
