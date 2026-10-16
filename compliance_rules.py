"""
Regulatory Rule Register & Traceability Engine
Governs all chemical thresholds, exemption rules, and reporting duties.
"""

RULE_REGISTER = {
    "ROHS_PB_LIMIT": {
        "rule_id": "ROHS_PB_LIMIT",
        "rule_version": "v2.1",
        "jurisdiction": "EU",
        "source": "Directive 2011/65/EU Annex II (RoHS 2.0)",
        "effective_date": "2019-07-22",
        "threshold": "1000 ppm (0.1% w/w)",
        "verified_at": "2026-10-04"
    },
    "ROHS_CD_LIMIT": {
        "rule_id": "ROHS_CD_LIMIT",
        "rule_version": "v2.0",
        "jurisdiction": "EU",
        "source": "Directive 2011/65/EU Annex II",
        "effective_date": "2013-01-02",
        "threshold": "100 ppm (0.01% w/w)",
        "verified_at": "2026-10-04"
    },
    "ROHS_EXEMPTION_6C": {
        "rule_id": "ROHS_EXEMPTION_6C",
        "rule_version": "v3.0",
        "jurisdiction": "EU",
        "source": "Directive 2011/65/EU Annex III Exemption 6(c)",
        "effective_date": "2021-07-21",
        "threshold": "40000 ppm (4.0% w/w in copper alloys)",
        "verified_at": "2026-10-04"
    },
    "PROP65_PB_STRICT": {
        "rule_id": "PROP65_PB_STRICT",
        "rule_version": "v1.2",
        "jurisdiction": "US-CA",
        "source": "California Proposition 65 Safe Harbor Warning Level",
        "effective_date": "2018-08-30",
        "threshold": "800 ppm (Actionable threshold)",
        "verified_at": "2026-10-04"
    },
    "CHINA_ROHS_EFUP": {
        "rule_id": "CHINA_ROHS_EFUP",
        "rule_version": "v2.0",
        "jurisdiction": "CN",
        "source": "MIIT Order No. 32 / SJ/T 11364",
        "effective_date": "2016-07-01",
        "threshold": "GB/T 26572 / 20-Year EFUP Label",
        "verified_at": "2026-10-04"
    },
    "SCIP_SVHC_THRESHOLD": {
        "rule_id": "SCIP_SVHC_THRESHOLD",
        "rule_version": "v6.10",
        "jurisdiction": "EU",
        "source": "Waste Framework Directive 2008/98/EC Art. 9(1)(i) / REACH Art. 33 / CJEU C-106/14",
        "effective_date": "2021-01-05",
        "threshold": "> 0.1% w/w at Article Level",
        "verified_at": "2026-10-04"
    },
    "EVIDENCE_SHELF_LIFE": {
        "rule_id": "EVIDENCE_SHELF_LIFE",
        "rule_version": "v1.0",
        "jurisdiction": "INTERNAL_QA",
        "source": "Corporate Hardware Quality Standard ISO/IEC 17025 Section 7.8",
        "effective_date": "2024-01-01",
        "threshold": "Max 24 Months validity",
        "verified_at": "2026-10-04"
    }
}