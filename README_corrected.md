# Engineering Compliance Decision Engine (ECDE)

> **Deterministic, Auditable & Rule-Governed Engineering Compliance Decision-Support Platform**  
> *Prototype scope: EU RoHS, REACH SVHC/SCIP assessment, selected US California Proposition 65 screening, and China RoHS-related assessment.*

---

## 1. Executive Problem Statement

Hardware manufacturers must evaluate supplier evidence, material composition, product configuration, and market-specific requirements before placing electro-mechanical products on the market. These workflows can be difficult to audit when evidence is incomplete, unstructured, outdated, or disconnected from the relevant bill of materials (BOM).

Common engineering challenges include:

- **Evidence integrity and unverified extraction:** Third-party laboratory reports and supplier declarations may be incorporated into compliance workflows without consistently checking traceability, laboratory competence, evidence freshness, or physical plausibility.
- **Article-level SVHC assessment:** Using the total mass of a complex product can obscure the concentration of a substance in a distinct article. ECDE models article-level assessment in line with the interpretation reflected in CJEU Case C-106/14.
- **Defensible decision records:** Simple pass/fail scripts may not preserve the evidence, rule version, reason for a decision, reviewer action, and resulting BOM revision needed for later review.

ECDE is a prototype engineering decision-support tool. It does not independently certify products or replace qualified regulatory review.

---

## 2. System Architecture & Workflow

The engine is designed around deterministic rule execution and traceable evidence provenance. Document extraction may be automated, but extracted values should be validated before they are used in downstream decisions.

```text
[Supplier Documentation]
  Lab reports / material declarations / supplier statements
                         |
                         v
+---------------------------------------------+
| 1. Evidence Extraction                      |
| doc_parser.py                                |
| Extracted values, source references, dates   |
+----------------------+----------------------+
                       |
                       v
+---------------------------------------------+
| 2. Evidence Integrity Gate                  |
| validator.py                                 |
| Configurable freshness policy, required      |
| fields, source checks, physical bounds        |
+----------------------+----------------------+
                       |
                       v
+---------------------------------------------+
| Evidence Quality Triage                     |
| Configurable internal score / decision rules |
+----------------------+----------------------+
                       |
           +-----------+-----------+
           |                       |
           v                       v
   Eligible for next step      Review / reject
           |                       |
           |                 +-----+----------------+
           |                 | 3. HITL Governance  |
           |                 | review_manager.py   |
           |                 +-----+----------------+
           |                       |
           +-----------+-----------+
                       |
                       v
+---------------------------------------------+
| 4. Regional Rules Assessment                 |
| EU RoHS / configured US screening /          |
| China RoHS-related checks                    |
+----------------------+----------------------+
                       |
                       v
+---------------------------------------------+
| 5. REACH SVHC / SCIP Applicability           |
| Article-level concentration assessment      |
+----------------------+----------------------+
                       |
                       v
+---------------------------------------------+
| 6. Outputs & Audit Dossier                  |
| Audit report / review log / sourcing impact  |
+---------------------------------------------+
```

### Evidence-quality triage

The project uses configurable internal score bands to route records for processing, review, or rejection. These scores represent **evidence quality / workflow triage**, not a probability of legal compliance. A high evidence score does not by itself establish that a product complies with every applicable requirement.

Any automatic acceptance behavior must be limited to the explicitly configured workflow and should be reviewed before production use. A failed mandatory integrity check should not be overridden solely by a high numeric score.

The 24-month evidence-freshness window, where enabled, is an **internal policy setting**, not a universal RoHS or REACH legal requirement.

---

## 3. Core Engineering Differentiators

### A. Article-level REACH / SCIP assessment

ECDE is designed to prevent product-level mass calculations from obscuring SVHC concentrations in relevant articles. For example, in a 2.47 kg brushless DC motor assembly, a distinct 100 g brass balancing ring containing 3.2% lead must not be assessed by dividing the lead mass by the mass of the entire motor when determining the concentration in that article.

The data model preserves article-level assessment consistent with the interpretation reflected in CJEU Case C-106/14. The actual applicability of REACH or SCIP obligations depends on the substance, article, concentration, supply-chain role, market, and applicable rules. The software output is an assessment aid, not a legal determination.

### B. Human-in-the-Loop (HITL) Review and Waiver Governance

ECDE routes borderline, incomplete, or otherwise flagged records to a human review workflow. The reviewer record is designed to capture:

- Review ID and part number
- Reviewer identity (`Engineer_ID`)
- Evidence references and identified issue
- Technical justification and waiver rationale, where applicable
- Decision and timestamp
- Resulting BOM revision, where a revision is authorized

An authorized engineer or designated compliance reviewer should provide the required decision and rationale. The decision is recorded in the audit log; the log should not be described as tamper-proof or permanently sealed unless the implementation provides and verifies those controls.

### C. Supplier alternative and sourcing impact

Where configured, ECDE can identify catalog alternatives and calculate estimated cost impact. A cost match alone does not establish engineering equivalence. Before an alternative is approved, the relevant dimensions, material, performance, interfaces, safety requirements, qualification status, availability, and change-control requirements must be reviewed.

---

## 4. Regulatory Rule Configuration and Scope

The following are modeled areas, not a claim that every possible obligation is implemented or legally validated:

- **EU RoHS:** Directive 2011/65/EU and applicable amendments, substance restrictions, and any relevant, valid exemptions. Exemption applicability must be assessed against its exact scope and validity.
- **REACH SVHC / SCIP:** Candidate List status, relevant article identity, concentration information, and configured SCIP applicability checks. SCIP is an ECHA database obligation under the Waste Framework Directive framework; it is not a customs declaration.
- **California Proposition 65:** Exposure-based screening and configured internal rules. An internal lead screening value such as 800 ppm must be clearly labeled as an **internal heuristic**, not a universal Proposition 65 legal limit. Proposition 65 assessments may depend on exposure, route, and applicable safe-harbor levels.
- **China RoHS:** Configurable checks related to applicable substance restrictions and marking requirements. EFUP marking must be determined from the applicable product requirements; 20 years must not be treated as a universal value for every product.

Regulatory rules should be stored with, at minimum, a rule ID, jurisdiction, source reference, effective date or version, verification date, and implementation status. Rules and thresholds must be independently checked against the applicable legislation and guidance before production use.

### Laboratory and test-method checks

ISO/IEC 17025 concerns laboratory competence and accreditation. IEC 62321 is a series of test methods used to determine certain substances in electrotechnical products; it is not an accreditation scheme. Where relevant, the workflow should check whether the laboratory's accreditation scope covers the reported method and activity.

---

## 5. Verification & Synthetic Testing

The project includes a Pytest suite intended to cover boundary conditions, data-parsing anomalies, review governance, and false-accept risks. The following output reflects the test run recorded during development; rerun the suite to confirm the current repository state.

```text
$ pytest -v
=============================== test session starts ===============================
tests/test_reach_scip.py::test_svhc_article_concentration_not_diluted_by_product_mass PASSED
tests/test_reach_scip.py::test_svhc_below_threshold_is_exempt PASSED
tests/test_review_manager.py::test_hitl_reject_does_not_mutate_bom PASSED
tests/test_review_manager.py::test_hitl_approve_updates_bom_revision_and_status PASSED
tests/test_review_manager.py::test_sourcing_unresolved_when_catalog_lacks_alternative PASSED
tests/test_rohs_engine.py::test_rohs_compliant_steel PASSED
tests/test_rohs_engine.py::test_rohs_cadmium_failure PASSED
tests/test_rohs_engine.py::test_rohs_exemption_6c_brass PASSED
tests/test_rohs_engine.py::test_internal_prop65_lead_screening_rule_triggers PASSED
tests/test_validator.py::test_valid_lab_report_auto_accept PASSED
tests/test_validator.py::test_future_dated_report_rejected_or_flagged PASSED
tests/test_validator.py::test_expired_evidence_triggers_review PASSED
tests/test_validator.py::test_negative_ppm_triggers_rejection PASSED
tests/test_validator.py::test_hyper_concentration_above_1m_ppm_rejected PASSED
tests/test_validator.py::test_missing_part_number_in_bom PASSED

=============================== 15 passed in 0.62s ===============================
```

The suite should be expanded as the implementation grows. Passing tests demonstrate that the tested cases behaved as expected; they do not prove full regulatory coverage, legal correctness, or production readiness.

### Synthetic batch-processing benchmark

During development, the engine was benchmarked against a 1,000-part synthetic industrial-drive BOM.

- **Processing time:** Approximately 1,000 synthetic parts evaluated in under 1 second in the local test environment.
- **Integrity checks:** The benchmark scenario included future-dated reports, unaccredited laboratory evidence, and physically invalid concentration values.
- **Reporting:** The prototype generated a five-tab executive workbook (`ECDE_1000_COMPLIANCE_AUDIT_REPORT.xlsx`).

These are development-environment results, not a general scalability guarantee. Benchmark results should be reproducible with the dataset, environment, and procedure documented.

---

## 6. Example Outputs

The project is designed to generate artifacts such as:

- `ENGINEERING_COMPLIANCE_AUDIT_DOSSIER.md`
- `ECDE_1000_COMPLIANCE_AUDIT_REPORT.xlsx`
- Supplier action lists and sourcing cost-impact summaries
- Human-review and audit-resolution logs

Generated outputs should retain the applicable BOM revision, evidence references, rule-set version, execution timestamp, and reviewer decisions where relevant. Do not publish confidential supplier reports or proprietary company data in a public repository; use synthetic or properly anonymized examples.

---

## 7. Limitations and Regulatory Disclaimer

ECDE is a prototype engineering decision-support tool for structured evidence evaluation, configurable rule execution, and audit-trail generation. It is **not** a legal opinion, official declaration of conformity, third-party certification, or substitute for qualified regulatory and engineering review.

Regulatory rules and thresholds may change and may depend on product type, material, article identity, intended market, exemptions, exposure, and effective dates. Before production use, each rule must be independently verified against authoritative sources and documented with its scope and version. Test results alone do not establish legal compliance.

---

## 8. Author & Maintainer

**Mechanical Engineering Student — Gebze Technical University (GTU)**

Focus areas: Systems Engineering, Regulatory Compliance, Evidence Validation, and Deterministic Quality Automation.
