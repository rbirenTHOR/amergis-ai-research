#!/usr/bin/env python3
"""Validate synthetic fixture consistency; this does not test a staffing product."""

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from pathlib import Path
import re
import sys


CENT = Decimal("0.01")
REQUIRED_SCENARIO_FIELDS = {
    "id", "title", "category", "actor", "prerequisites", "inputs",
    "expected_state_or_action", "expected_states", "forbidden_outcomes",
    "accountable_owner", "acceptance_checks", "future_test_type", "status",
}
REQUIRED_CATEGORIES = {
    "consent", "duplicates", "credential_evidence", "credential_expiry",
    "assistant_scope_supervision", "submission_approval", "scheduling_overlap",
    "school_calendar_closure", "scheduling_race", "missed_session_makeup", "provider_absence",
    "financial_arithmetic", "time_amendment", "payroll_billing_separation",
    "retry_idempotency", "vendor_outage_reconciliation", "tenant_isolation",
    "financial_exact_payload_approval", "untrusted_document_instruction",
    "emergency_routing", "override_authority",
    "screening_authorization_review", "conflicting_district_rules",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decimal_string(value, label, nonnegative=True):
    require(isinstance(value, str), f"{label}: a Decimal string is required")
    require(re.fullmatch(r"-?\d+(?:\.\d+)?", value) is not None,
            f"{label}: invalid decimal format")
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"{label}: invalid Decimal") from error
    require(result.is_finite(), f"{label}: must be finite")
    require(not nonnegative or result >= 0, f"{label}: must be nonnegative")
    return result


def rounded_product(record, hours_key, rate_key):
    return (decimal_string(record[hours_key], hours_key)
            * decimal_string(record[rate_key], rate_key)).quantize(
                CENT, rounding=ROUND_HALF_UP)


def assert_money(expected, key, calculated, fixture_id):
    require(key in expected, f"{fixture_id}: missing expected {key}")
    value = decimal_string(expected[key], f"{fixture_id}.{key}", nonnegative=False)
    require(re.fullmatch(r"-?\d+\.\d{2}", expected[key]) is not None,
            f"{fixture_id}.{key}: expected money must have exactly two decimals")
    require(value == calculated,
            f"{fixture_id}.{key}: stored {value} != independently calculated {calculated}")


def instant(value):
    parsed = datetime.fromisoformat(value)
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None,
            f"Timestamp requires explicit offset: {value}")
    return parsed.astimezone(timezone.utc)


def check(data):
    require("not implemented or executed" in data["status"],
            "The pack must clearly distinguish specifications from executed product tests")
    scenarios = data["scenarios"]
    require(18 <= len(scenarios) <= 26, "Expected 18–26 scenarios")
    ids = [scenario["id"] for scenario in scenarios]
    require(len(ids) == len(set(ids)), "Scenario IDs must be unique")
    require(ids == [f"SC{index:02}" for index in range(1, len(scenarios) + 1)],
            "Scenario IDs must be stable sequential SCxx identifiers")
    require(REQUIRED_CATEGORIES <= {scenario["category"] for scenario in scenarios},
            "A required coverage category is missing")
    by_id = {scenario["id"]: scenario for scenario in scenarios}
    for scenario in scenarios:
        scenario_id = scenario["id"]
        require(REQUIRED_SCENARIO_FIELDS <= scenario.keys(),
                f"{scenario_id}: missing required scenario fields")
        for key in ("title", "category", "actor", "accountable_owner", "future_test_type"):
            require(isinstance(scenario[key], str) and scenario[key].strip(),
                    f"{scenario_id}: {key} must be a nonempty string")
        for key in ("prerequisites", "expected_state_or_action", "forbidden_outcomes", "acceptance_checks"):
            require(isinstance(scenario[key], list) and scenario[key]
                    and all(isinstance(item, str) and item.strip() for item in scenario[key]),
                    f"{scenario_id}: {key} must contain nonempty statements")
        require(isinstance(scenario["inputs"], dict) and scenario["inputs"],
                f"{scenario_id}: inputs must be a nonempty object")
        require(isinstance(scenario["expected_states"], list),
                f"{scenario_id}: expected_states must be a list")
        for state in scenario["expected_states"]:
            require(re.fullmatch(r"DS-SM0[1-9]", state.get("model_id", "")) is not None,
                    f"{scenario_id}: expected state requires a domain-model ID")
            require(isinstance(state.get("state"), str) and state["state"],
                    f"{scenario_id}: expected state requires a label")
        require(scenario["status"] == "specified_not_executed",
                f"{scenario_id}: must not imply that a future product test passed")

    fixtures = data["arithmetic_fixtures"]
    require(3 <= len(fixtures) <= 4, "Expected 3–4 arithmetic fixtures")
    fixture_ids = {fixture["id"] for fixture in fixtures}
    require(len(fixture_ids) == len(fixtures), "Arithmetic fixture IDs must be unique")
    require(data["arithmetic_policy"]["synthetic"] is True, "Artificial arithmetic label required")
    arithmetic_results = []
    for fixture in fixtures:
        fixture_id = fixture["id"]
        require(fixture["synthetic"] is True, f"{fixture_id}: artificial label required")
        require(fixture["chosen_rules"], f"{fixture_id}: chosen calculation rules required")
        require(fixture["scenario_ids"] and set(fixture["scenario_ids"]) <= set(ids),
                f"{fixture_id}: invalid scenario reference")
        pay = rounded_product(fixture, "pay_hours", "pay_rate")
        bill = rounded_product(fixture, "bill_hours", "bill_rate")
        expected = fixture["expected"]
        computed = {
            "pay_preparation_amount": pay,
            "bill_draft_amount": bill,
            "arithmetic_rate_difference": bill - pay,
        }
        if "prior" in fixture:
            prior = fixture["prior"]
            prior_pay = rounded_product(prior, "pay_hours", "pay_rate")
            prior_bill = rounded_product(prior, "bill_hours", "bill_rate")
            assert_money(prior, "expected_pay_amount", prior_pay, fixture_id + ".prior")
            assert_money(prior, "expected_bill_amount", prior_bill, fixture_id + ".prior")
            computed.update(pay_adjustment=pay - prior_pay, bill_adjustment=bill - prior_bill)
        if "disputed_invoice_amount" in expected:
            computed.update(disputed_invoice_amount=bill, pay_amount_after_invoice_dispute=pay)
        if "pending_bill_hours" in fixture:
            pending = rounded_product(fixture, "pending_bill_hours", "bill_rate")
            computed.update(pending_bill_amount=pending,
                            potential_bill_total_if_pending_accepted=bill + pending)
        require(set(expected) == set(computed),
                f"{fixture_id}: expected amounts include unchecked or missing fields")
        for key, value in computed.items():
            assert_money(expected, key, value, fixture_id)
        for scenario_id in fixture["scenario_ids"]:
            require(by_id[scenario_id]["inputs"].get("arithmetic_fixture_id") == fixture_id,
                    f"{fixture_id}: scenario backlink does not agree")
        arithmetic_results.append({"id": fixture_id, "result": "stored_amounts_consistent",
                                   "computed": {key: str(value) for key, value in computed.items()}})
    for scenario in scenarios:
        fixture_ref = scenario["inputs"].get("arithmetic_fixture_id")
        require(fixture_ref is None or fixture_ref in fixture_ids,
                f"{scenario['id']}: unknown arithmetic fixture")

    overlap = by_id["SC09"]["inputs"]
    overlap_seconds = (min(instant(overlap["existing_end"]), instant(overlap["new_end"]))
                       - max(instant(overlap["existing_start"]), instant(overlap["new_start"]))).total_seconds()
    require(overlap_seconds == 1800, "SC09 explicit timestamps must overlap by 30 minutes")
    dst = by_id["SC09"]["inputs"]["duration_example"]
    dst_minutes = (instant(dst["end"]) - instant(dst["start"])).total_seconds() / 60
    require(dst_minutes == dst["expected_elapsed_minutes"] == 240,
            "SC09 duration edge case must be 240 minutes")
    expiry = by_id["SC06"]["inputs"]
    require(instant(expiry["shift_start"]) < instant(expiry["credential_valid_until"])
            < instant(expiry["shift_end"]), "SC06 credential must expire during the work block")
    time_breakdown = by_id["SC17"]["inputs"]
    worked_minutes = sum(time_breakdown[key] for key in
                         ("direct_service_minutes", "documentation_minutes", "travel_minutes"))
    fin04 = next(fixture for fixture in fixtures if fixture["id"] == "FIN04")
    require(worked_minutes == time_breakdown["worked_minutes"] == 465,
            "SC17 artificial work categories must sum to 465 minutes")
    require(Decimal(worked_minutes) == Decimal(fin04["pay_hours"]) * Decimal(60),
            "SC17 worked minutes must match FIN04 owner-classified pay hours")
    group = time_breakdown["group_session_unit_example"]
    require(group["expected_provider_service_minutes"] == group["elapsed_session_minutes"],
            "SC17 group service duration must not multiply by attendance count")
    require(group["attending_student_count"] > 1,
            "SC17 group-service example must include multiple synthetic attendance references")

    metrics = data["metrics"]
    require(len(metrics) == 8, "Expected eight proposed metrics")
    require(len({metric["id"] for metric in metrics}) == len(metrics), "Metric IDs must be unique")
    for metric in metrics:
        for key in ("name", "numerator", "denominator", "unit", "owner", "threshold_status", "caveat"):
            require(isinstance(metric[key], str) and metric[key], f"{metric['id']}: missing {key}")
        require(metric["threshold"] is None, f"{metric['id']}: owner-set threshold must remain pending")
        require(set(metric["measurement_labels"]) == {"synthetic", "live"},
                f"{metric['id']}: synthetic/live measurement labels required")
        require(all(isinstance(label, str) and label for label in metric["measurement_labels"].values()),
                f"{metric['id']}: measurement label cannot be empty")

    return {
        "result": "PASS: synthetic fixture consistency only",
        "scenario_count": len(scenarios),
        "arithmetic_fixture_count": len(fixtures),
        "metric_count": len(metrics),
        "checks_performed": [
            "Required scenario fields, stable IDs, coverage categories and fixture references",
            "Independent Decimal calculation of every stored expected financial amount",
            "Explicit-offset overlap, elapsed duration and credential-expiry interval arithmetic",
            "Artificial worked-minute breakdown and group-duration fixture consistency",
            "Pending thresholds and separate synthetic/live measurement descriptions",
        ],
        "arithmetic_results": arithmetic_results,
        "future_product_acceptance_tests": "NOT IMPLEMENTED OR EXECUTED",
        "vendor_or_live_validation": "NONE",
        "limitation": "A pass establishes internally consistent research fixtures; it does not establish product behavior, real integration compatibility, provider clearance, school service compliance, autonomy or live performance.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path,
                        default=Path(__file__).with_name("scenarios.json"))
    args = parser.parse_args()
    try:
        data = json.loads(args.path.read_text(encoding="utf-8"))
        report = check(data)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"result": "FAIL: synthetic fixture consistency",
                          "error": str(error),
                          "future_product_acceptance_tests": "NOT IMPLEMENTED OR EXECUTED"}, indent=2))
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
