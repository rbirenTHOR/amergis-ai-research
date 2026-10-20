#!/usr/bin/env python3
"""Independently recalculate the illustrative pilot model; no network or file writes.

This validates arithmetic and the stated bounds, not actual wages, quotations,
contract enforceability, clinician availability or a viable bid price.
"""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import copy
import json

D = Decimal
ROOT = Path(__file__).resolve().parent
DOCUMENT = json.loads((ROOT / "economics.json").read_text())


def q(value, ratio=False):
    return value.quantize(D("0.0001" if ratio else "0.01"), rounding=ROUND_HALF_UP)


def validate(x, clinicians):
    assert isinstance(clinicians, int) and 1 <= clinicians <= 3
    assert all(D(str(v)).is_finite() and D(str(v)) >= 0 for v in x.values())
    assert x["paid_hours"] > 0 and x["pay_rate"] > 0
    assert 0 < x["billable_hour_equivalents"] <= x["paid_hours"]
    for k in ("employer_burden_fraction", "backup_allowance_fraction", "insurance_upfront_fraction", "admin_cash_fraction", "cash_contingency_fraction"):
        assert 0 <= x[k] <= 1, k
    assert 0 <= x["target_operating_margin"] < 1
    assert x["invoice_cycle_days"] + x["invoice_submission_lag_days"] <= 30
    assert x["bill_rate_equivalent"] > 0


def calculate(inputs, clinicians):
    validate(inputs, clinicians)
    x = {k: D(str(v)) for k, v in inputs.items()}
    n = D(clinicians)
    h = n * x["paid_hours"]
    b = n * x["billable_hour_equivalents"]
    wages = h * x["pay_rate"]
    taxes_and_benefits = wages * x["employer_burden_fraction"]
    loaded = wages + taxes_and_benefits
    cover = loaded * x["backup_allowance_fraction"]
    travel = n * x["travel_per_clinician"]
    seats = n * x["software_seat_per_clinician"]
    maintenance = n * x["credential_maintenance_per_clinician"]
    direct = loaded + cover + travel + seats + maintenance
    premium = x["annual_insurance_first"] + (n - 1) * x["annual_insurance_additional"]
    admin_hours = x["admin_hours_first"] + (n - 1) * x["admin_hours_additional"]
    admin = admin_hours * x["admin_loaded_rate"]
    overhead = premium / 12 + admin + x["shared_software_monthly"]
    all_cost = direct + overhead
    revenue = b * x["bill_rate_equivalent"]
    profit = revenue - all_cost
    nonpay = travel + seats + maintenance + overhead
    pay_at_margin = (revenue * (1 - x["target_operating_margin"]) - nonpay) / (
        h * (1 + x["employer_burden_fraction"]) * (1 + x["backup_allowance_fraction"])
    )
    setup = sum((
        x["entity_legal_setup"], x["technology_configuration_setup"],
        x["bid_preparation_hours"] * x["admin_loaded_rate"],
        x["backup_recruit_clearance_setup"],
        n * x["recruit_clearance_setup_per_clinician"],
        n * x["hardware_setup_per_clinician"],
    ))
    paid_premium = premium * x["insurance_upfront_fraction"]
    monthly_premium_payment = (premium - paid_premium) / 12
    monthly_cash = direct + x["shared_software_monthly"] + admin * x["admin_cash_fraction"] + monthly_premium_payment
    first_cash_days = sum(x[k] for k in ("invoice_cycle_days", "invoice_submission_lag_days", "approval_delay_days", "payment_after_approval_days"))
    funding_days = first_cash_days + x["extra_cash_cushion_days"]
    reserve = monthly_cash * funding_days / 30
    contingency = (setup + paid_premium + reserve) * x["cash_contingency_fraction"]
    funding = setup + paid_premium + reserve + contingency
    values = {
        "clinicians": n, "paid_hours_total": h, "billable_hour_equivalents_total": b,
        "billable_to_paid_ratio": b / h, "revenue": revenue,
        "gross_pay": wages, "employer_burden": taxes_and_benefits, "loaded_pay": loaded,
        "backup_allowance": cover, "travel": travel, "software_seats": seats,
        "credential_maintenance": maintenance, "direct_delivery_cost": direct,
        "contribution_before_shared_overhead": revenue - direct,
        "annual_insurance": premium, "insurance_monthly_allocation": premium / 12,
        "human_admin_hours": admin_hours, "human_admin_cost": admin,
        "shared_overhead": overhead, "total_operating_cost": all_cost,
        "operating_profit_before_tax_startup_and_financing": profit,
        "operating_margin_fraction": profit / revenue,
        "break_even_rate_equivalent": all_cost / b,
        "rate_equivalent_for_target_margin": all_cost / (b * (1 - x["target_operating_margin"])),
        "break_even_billable_to_paid_ratio": all_cost / (h * x["bill_rate_equivalent"]),
        "max_pay_rate_for_target_margin": pay_at_margin,
        "setup_cost": setup, "insurance_upfront_cash": paid_premium,
        "insurance_monthly_cash_remaining": monthly_premium_payment,
        "monthly_cash_outflow": monthly_cash,
        "days_to_first_cash_assumption": first_cash_days, "funding_days": funding_days,
        "working_capital_cash_reserve": reserve, "cash_contingency": contingency,
        "startup_funding_target": funding, "operating_profit_per_clinician": profit / n,
    }
    return {k: q(v, k.endswith("_ratio") or k == "operating_margin_fraction") for k, v in values.items()}


def main():
    assert DOCUMENT["status"] == "planning_model_not_bid_quote"
    keys = {r["key"] for r in DOCUMENT["input_definitions"]}
    source_ids = {s["id"] for s in DOCUMENT["sources"]}
    assert len(source_ids) == len(DOCUMENT["sources"])
    for context in DOCUMENT["verified_pay_context"]:
        assert set(context["source_ids"]) <= source_ids
        assert all(next(s for s in DOCUMENT["sources"] if s["id"] == sid)["kind"].startswith("primary_") for sid in context["source_ids"])
    for field in DOCUMENT["input_definitions"]:
        assert field["provenance_kind"] in ("analyst_estimate", "quote_required")
        assert field["unit"] and field["note"]
    checks = 0
    for scenario in DOCUMENT["scenarios"]:
        assert set(scenario["inputs"]) == keys
        assert [r["clinicians"] for r in scenario["results"]] == [1, 2, 3]
        previous_funding = D(0)
        previous_profit = D(0)
        for stored in scenario["results"]:
            expected = calculate(scenario["inputs"], stored["clinicians"])
            expected["incremental_funding_vs_previous_scale"] = expected["startup_funding_target"] - previous_funding
            expected["incremental_monthly_profit_vs_previous_scale"] = expected["operating_profit_before_tax_startup_and_financing"] - previous_profit
            assert set(expected) == set(stored), (scenario["id"], set(expected) ^ set(stored))
            for key, value in expected.items():
                assert D(str(stored[key])) == value, (scenario["id"], stored["clinicians"], key, stored[key], value)
                checks += 1
            previous_funding = expected["startup_funding_target"]
            previous_profit = expected["operating_profit_before_tax_startup_and_financing"]
    base = DOCUMENT["scenarios"][0]["inputs"]
    for row in DOCUMENT["sensitivity"]["rows"]:
        variant = {**base, "pay_rate": row["pay_rate"], "billable_hour_equivalents": row["billable_hour_equivalents"]}
        assert D(str(row["billable_hour_equivalents"])) == D(str(base["paid_hours"])) * D(str(row["billable_to_paid_ratio"]))
        result = calculate(variant, 1)
        for key, result_key in (("operating_profit", "operating_profit_before_tax_startup_and_financing"), ("break_even_rate_equivalent", "break_even_rate_equivalent"), ("target_margin_rate_equivalent", "rate_equivalent_for_target_margin")):
            assert D(str(row[key])) == result[result_key]
            checks += 1

    # Meaningful invariants: no insurance double count; unpaid owner labor is
    # financing, not profit; collection delays change liquidity, not earnings.
    b = calculate(base, 1)
    installment = calculate({**base, "insurance_upfront_fraction": 0}, 1)
    assert installment["total_operating_cost"] == b["total_operating_cost"]
    assert installment["monthly_cash_outflow"] - b["monthly_cash_outflow"] == b["insurance_monthly_allocation"]
    owner_financed = calculate({**base, "admin_cash_fraction": 0}, 1)
    assert owner_financed["operating_profit_before_tax_startup_and_financing"] == b["operating_profit_before_tax_startup_and_financing"]
    assert b["monthly_cash_outflow"] - owner_financed["monthly_cash_outflow"] == b["human_admin_cost"]
    delay = calculate({**base, "payment_after_approval_days": 60}, 1)
    assert delay["operating_profit_before_tax_startup_and_financing"] == b["operating_profit_before_tax_startup_and_financing"]
    assert delay["working_capital_cash_reserve"] - b["working_capital_cash_reserve"] == b["monthly_cash_outflow"]
    assert calculate(DOCUMENT["scenarios"][2]["inputs"], 1)["break_even_billable_to_paid_ratio"] > 1
    for bad in ({"billable_hour_equivalents": 141}, {"target_operating_margin": 1}, {"invoice_submission_lag_days": 3}, {"insurance_upfront_fraction": 1.1}):
        try:
            calculate({**base, **bad}, 1)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"Invalid inputs accepted: {bad}")
    print(json.dumps({"status": "pass", "scenario_scale_cases": 9, "sensitivity_cases": 12, "numeric_assertions": checks, "edge_invariants": "insurance, owner financing, collection timing, bounds", "scope": "planning arithmetic only"}))


if __name__ == "__main__":
    main()
