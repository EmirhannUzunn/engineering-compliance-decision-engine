import os
import time
import datetime
import pandas as pd
from tabulate import tabulate
from validator import validate_report_evidence
from reach_config import SCIP_CONFIG, SVHC_CANDIDATE_LIST

INPUT_EXCEL = "raw_master_bom_1000.xlsx"
OUTPUT_EXCEL = "ECDE_1000_COMPLIANCE_AUDIT_REPORT.xlsx"


def run_batch_excel_audit():
    print("=" * 80)
    print("      ENGINEERING COMPLIANCE DECISION ENGINE - 1,000-PART EXCEL PIPELINE       ")
    print("               [BATCH INGESTION, AUDIT & MULTI-TAB EXPORT]                     ")
    print("=" * 80)

    if not os.path.exists(INPUT_EXCEL):
        print(f"[ERROR] '{INPUT_EXCEL}' not found. Please run 'generate_1000_excel.py' first.")
        return

    start_time = time.time()
    print(f"\n>>> [1/4] Reading '{INPUT_EXCEL}' into memory...")
    df = pd.read_excel(INPUT_EXCEL)
    total_parts = len(df)
    bom_parts = df['Part_Number'].tolist()

    print(f">>> Successfully loaded {total_parts} components.")
    print(f">>> [2/4] Executing Vectorized Integrity Gate & Compliance Engine...")

    master_rows = []
    review_queue = []
    scip_dossier = []
    sourcing_actions = []

    counts = {
        'auto_accept': 0,
        'engineer_review': 0,
        'reject': 0,
        'eu_pass': 0,
        'us_pass': 0,
        'scip_mandatory': 0
    }

    for idx, row in df.iterrows():
        row_dict = row.to_dict()

        # 1. Integrity Gate & Validation Check
        v_res = validate_report_evidence(row_dict, bom_parts, source_file=INPUT_EXCEL)
        v_decision = v_res['Workflow_Decision']
        v_score = v_res['Confidence_Score']
        v_tier = v_res['Risk_Tier']
        v_flags = "; ".join(v_res['Why_Flagged'])

        pb = float(row.get('Lead_ppm', 0))
        cd = float(row.get('Cadmium_ppm', 0))
        mat = str(row.get('Material', ''))
        part_no = row['Part_Number']
        part_name = row['Part_Name']
        qty = float(row['Quantity'])
        cost = float(row['Unit_Cost_USD'])
        weight = float(row['Weight_g'])

        # Sayım Güncellemesi
        if v_decision == 'AUTO-ACCEPT':
            counts['auto_accept'] += 1
        elif v_decision == 'ENGINEER REVIEW':
            counts['engineer_review'] += 1
            review_queue.append({
                'Review_ID': f"REV-BATCH-{idx + 1:04d}",
                'Part_Number': part_no,
                'Part_Name': part_name,
                'Risk_Tier': v_tier,
                'Confidence_Score': v_score,
                'Risk_Rationale': v_flags,
                'Report_Date': row.get('Report_Date'),
                'Test_Standard': row.get('Test_Standard'),
                'Lead_ppm': pb,
                'Recommended_Action': "; ".join(v_res['Recommended_Actions'])
            })
        else:
            counts['reject'] += 1

        # 2. Bölgesel Regülasyon Değerlendirmesi
        # Bozuk veriler doğrudan elenir
        is_data_clean = (0 <= pb <= 1000000 and cd >= 0)

        eu_verdict = "FAIL"
        us_verdict = "FAIL"

        if is_data_clean:
            # EU RoHS
            if cd <= 100:
                if pb <= 1000:
                    eu_verdict = "PASS"
                    counts['eu_pass'] += 1
                elif 'brass' in mat.lower() and pb <= 40000:
                    eu_verdict = "PASS (Exemption 6c)"
                    counts['eu_pass'] += 1

            # US Prop 65
            if cd <= 100 and pb <= 800:
                us_verdict = "PASS"
                counts['us_pass'] += 1
            else:
                us_verdict = "WARNING_LABEL_REQUIRED (Pb > 800 ppm)"

        # 3. CJEU C-106/14 ECHA SCIP Artikel Değerlendirmesi
        scip_duty = "EXEMPT"
        if is_data_clean:
            conc_pct = pb / 10000.0  # % w/w
            if conc_pct > SCIP_CONFIG['threshold_weight_percent']:
                scip_duty = "MANDATORY"
                counts['scip_mandatory'] += 1

                scip_dossier.append({
                    'Article_Identifier': part_no,
                    'Article_Name': part_name,
                    'Sub_Assembly': row['Sub_Assembly'],
                    'Material_Category': mat,
                    'Candidate_Substance': 'Lead',
                    'Concentration_PPM': pb,
                    'Concentration_%w/w': f"{conc_pct:.2f}%",
                    'Concentration_Range': "≥ 1.0% w/w" if conc_pct >= 1.0 else "≥ 0.1% and < 1.0% w/w",
                    'Safe_Use_Instructions': SVHC_CANDIDATE_LIST['Lead']['safe_use_instructions'],
                    'Legal_Trigger': 'WFD Directive 2008/98/EC Art. 9(1)(i)'
                })

        # Sourcing Aksiyonları (RoHS FAIL veya Prop 65 uyarısı alanlar)
        if eu_verdict == "FAIL" or "WARNING" in us_verdict:
            sourcing_actions.append({
                'Part_Number': part_no,
                'Part_Name': part_name,
                'Material': mat,
                'Issue': f"EU: {eu_verdict} | US: {us_verdict}",
                'Current_Unit_Cost': cost,
                'Est_Compliant_Alternative_Cost': round(cost * 1.15, 2),  # %15 primli kurşunsuz muadil
                'Cost_Delta_USD': round(cost * 0.15, 2),
                'Total_Batch_Impact_USD': round(cost * 0.15 * qty, 2),
                'Action_Required': 'Engage Procurement for Low-Lead Alloy Re-quote'
            })

        # Master BOM Kaydı
        master_rows.append({
            'Part_Number': part_no,
            'Part_Name': part_name,
            'Sub_Assembly': row['Sub_Assembly'],
            'Material': mat,
            'Quantity': qty,
            'Weight_g': weight,
            'Total_Weight_g': round(qty * weight, 2),
            'Unit_Cost_USD': cost,
            'Ext_Cost_USD': round(qty * cost, 2),
            'Lead_ppm': pb,
            'Cadmium_ppm': cd,
            'Report_Date': row.get('Report_Date'),
            'Integrity_Decision': v_decision,
            'Integrity_Confidence': v_score,
            'Integrity_Flags': v_flags,
            'EU_RoHS_Verdict': eu_verdict,
            'US_Prop65_Verdict': us_verdict,
            'SCIP_Obligation': scip_duty
        })

    elapsed = time.time() - start_time
    print(f"\n>>> [3/4] Batch audit completed in {elapsed:.2f} seconds ({total_parts / elapsed:.0f} parts/sec).")

    # 4. Sekmeli Excel Dosyasını Oluştur
    print(f">>> [4/4] Writing multi-tab audit workbook to '{OUTPUT_EXCEL}'...")

    master_df = pd.DataFrame(master_rows)
    review_df = pd.DataFrame(review_queue)
    scip_df = pd.DataFrame(scip_dossier)
    sourcing_df = pd.DataFrame(sourcing_actions)

    total_weight_kg = master_df['Total_Weight_g'].sum() / 1000.0
    total_cost_usd = master_df['Ext_Cost_USD'].sum()

    exec_summary_data = [
        {"Metric": "Total Hardware Components Evaluated", "Value": total_parts, "Unit": "Parts"},
        {"Metric": "Execution Processing Time", "Value": f"{elapsed:.2f}", "Unit": "Seconds"},
        {"Metric": "Throughput Speed", "Value": f"{total_parts / elapsed:.0f}", "Unit": "Parts/Second"},
        {"Metric": "Total Assembly Mass", "Value": f"{total_weight_kg:.2f}", "Unit": "kg"},
        {"Metric": "Baseline Total BOM Cost", "Value": f"${total_cost_usd:,.2f}", "Unit": "USD"},
        {"Metric": "----------------------------------------", "Value": "------------------", "Unit": "------"},
        {"Metric": "Integrity Gate: AUTO-ACCEPT (Clean Data)", "Value": counts['auto_accept'],
         "Unit": f"{counts['auto_accept'] / total_parts * 100:.1f}%"},
        {"Metric": "Integrity Gate: ENGINEER REVIEW (HITL Queue)", "Value": counts['engineer_review'],
         "Unit": f"{counts['engineer_review'] / total_parts * 100:.1f}%"},
        {"Metric": "Integrity Gate: REJECT (Invalid / Falsified)", "Value": counts['reject'],
         "Unit": f"{counts['reject'] / total_parts * 100:.1f}%"},
        {"Metric": "----------------------------------------", "Value": "------------------", "Unit": "------"},
        {"Metric": "Market Clearance: EU RoHS 2.0 (with 6c)", "Value": counts['eu_pass'],
         "Unit": f"{counts['eu_pass'] / total_parts * 100:.1f}%"},
        {"Metric": "Market Clearance: US Prop 65 Safe Harbor", "Value": counts['us_pass'],
         "Unit": f"{counts['us_pass'] / total_parts * 100:.1f}%"},
        {"Metric": "Regulatory Trigger: ECHA SCIP Mandatory", "Value": counts['scip_mandatory'],
         "Unit": f"{counts['scip_mandatory'] / total_parts * 100:.1f}% Articles"}
    ]
    summary_df = pd.DataFrame(exec_summary_data)

    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        summary_df.to_excel(writer, sheet_name='Executive_Summary', index=False)
        master_df.to_excel(writer, sheet_name='Master_Audited_BOM', index=False)
        review_df.to_excel(writer, sheet_name='Engineer_Review_Queue', index=False)
        scip_df.to_excel(writer, sheet_name='ECHA_SCIP_Dossier', index=False)
        sourcing_df.to_excel(writer, sheet_name='Sourcing_Delta_Analysis', index=False)

    print("\n" + "=" * 80)
    print(f" >>> SUCCESS: Multi-tab Compliance Audit Workbook generated:")
    print(f" >>> File Location: '{OUTPUT_EXCEL}'")
    print("=" * 80)

    # Terminal Özeti
    print("\n--- EXECUTIVE DASHBOARD SUMMARY ---")
    print(tabulate(summary_df, headers='keys', tablefmt='psql', showindex=False))


if __name__ == "__main__":
    run_batch_excel_audit()