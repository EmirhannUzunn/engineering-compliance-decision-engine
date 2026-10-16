import pytest
from compliance_rules import RULE_REGISTER

def evaluate_rohs(pb_ppm, cd_ppm, material="Steel", jurisdiction="EU"):
    reasons = []
    status = "PASS"
    rule_ids = []

    if cd_ppm > 100.0:
        status = "FAIL"
        reasons.append("ROHS_CD_LIMIT_EXCEEDED")
        rule_ids.append("ROHS_CD_LIMIT")

    pb_limit = 800.0 if jurisdiction == "US-CA" else 1000.0

    if pb_ppm > pb_limit:
        if jurisdiction == "EU" and any(k in material.lower() for k in ['brass', 'copper', 'bronze']) and pb_ppm <= 40000.0:
            status = "PASS_WITH_EXEMPTION"
            rule_ids.append("ROHS_EXEMPTION_6C")
        else:
            status = "FAIL"
            reasons.append("ROHS_PB_LIMIT_EXCEEDED")
            rule_ids.append("PROP65_PB_STRICT" if jurisdiction == "US-CA" else "ROHS_PB_LIMIT")

    return {
        "status": status,
        "reasons": reasons,
        "rule_ids": rule_ids
    }

def test_rohs_compliant_steel():
    res = evaluate_rohs(pb_ppm=150.0, cd_ppm=10.0, material="Carbon Steel", jurisdiction="EU")
    assert res["status"] == "PASS"
    assert len(res["reasons"]) == 0

def test_rohs_cadmium_failure():
    res = evaluate_rohs(pb_ppm=50.0, cd_ppm=120.0, material="Zinc Plated Screw", jurisdiction="EU")
    assert res["status"] == "FAIL"
    assert "ROHS_CD_LIMIT_EXCEEDED" in res["reasons"]
    assert "ROHS_CD_LIMIT" in res["rule_ids"]

def test_rohs_exemption_6c_brass():
    """Pirinç parçada 32.000 ppm Pb, RoHS Muafiyeti 6(c) ile AB'de geçerlidir."""
    res = evaluate_rohs(pb_ppm=32000.0, cd_ppm=20.0, material="Machined Brass Alloy CuZn39Pb3", jurisdiction="EU")
    assert res["status"] == "PASS_WITH_EXEMPTION"
    assert "ROHS_EXEMPTION_6C" in res["rule_ids"]

def test_prop65_strict_pb_fails_in_california_but_passes_eu():
    """850 ppm Kurşun içeren parça, AB'de geçerken Kaliforniya Prop 65 sınırında (800 ppm) FAIL almalıdır."""
    eu_res = evaluate_rohs(pb_ppm=850.0, cd_ppm=5.0, material="Aluminum", jurisdiction="EU")
    assert eu_res["status"] == "PASS"

    us_res = evaluate_rohs(pb_ppm=850.0, cd_ppm=5.0, material="Aluminum", jurisdiction="US-CA")
    assert us_res["status"] == "FAIL"
    assert "PROP65_PB_STRICT" in us_res["rule_ids"]