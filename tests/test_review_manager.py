import pytest
import pandas as pd

def apply_hitl_decision(part_row, decision, engineer_id, waiver_reason=""):
    updated_row = part_row.copy()
    audit_log = {}

    if decision == "REJECT":
        audit_log = {
            "part_number": part_row["Part_Number"],
            "decision": "REJECT",
            "engineer_id": engineer_id,
            "bom_action": "NO_CHANGE"
        }
        return updated_row, audit_log

    elif decision == "APPROVE":
        updated_row["Cert_Status"] = f"Waiver Approved ({engineer_id})"
        updated_row["BOM_Revision"] = "REV-B"
        audit_log = {
            "part_number": part_row["Part_Number"],
            "decision": "APPROVE",
            "waiver_reason": waiver_reason,
            "engineer_id": engineer_id,
            "bom_action": "BOM_UPDATED"
        }
        return updated_row, audit_log

def match_supplier_replacement(part_name, catalog_df):
    alts = catalog_df[catalog_df['Target_Part_Name'].str.lower() == part_name.lower()]
    if alts.empty:
        return {"status": "UNRESOLVED", "replacement": None}
    best = alts.sort_values(by='Unit_Cost_USD').iloc[0]
    return {"status": "RESOLVED", "replacement": best['Alt_Part_Number']}

def test_hitl_reject_does_not_mutate_bom():
    initial_row = {"Part_Number": "MTR-SUB-11", "Cert_Status": "Pending", "BOM_Revision": "REV-A"}
    updated_row, log = apply_hitl_decision(initial_row, decision="REJECT", engineer_id="ENG-101")

    assert updated_row["Cert_Status"] == "Pending"
    assert updated_row["BOM_Revision"] == "REV-A"
    assert log["bom_action"] == "NO_CHANGE"

def test_hitl_approve_updates_bom_revision_and_status():
    initial_row = {"Part_Number": "MTR-SUB-11", "Cert_Status": "Pending", "BOM_Revision": "REV-A"}
    updated_row, log = apply_hitl_decision(
        initial_row, decision="APPROVE", engineer_id="ENG-101", waiver_reason="Zero mechanical wear"
    )

    assert "Waiver Approved (ENG-101)" in updated_row["Cert_Status"]
    assert updated_row["BOM_Revision"] == "REV-B"
    assert log["bom_action"] == "BOM_UPDATED"
    assert log["waiver_reason"] == "Zero mechanical wear"

def test_sourcing_unresolved_when_catalog_lacks_alternative():
    mock_catalog = pd.DataFrame([
        {"Alt_Part_Number": "ALT-BRG-608", "Target_Part_Name": "Rear Bearing 608-2RS", "Unit_Cost_USD": 3.75}
    ])
    result = match_supplier_replacement("Neodymium Magnet N42SH", mock_catalog)
    assert result["status"] == "UNRESOLVED"
    assert result["replacement"] is None