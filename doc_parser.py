import re
import uuid
import datetime
import pandas as pd
from validator import validate_report_evidence

REPORT_PATH = 'supplier_report_MTR11.txt'
BOM_PATH = 'motor_bom.csv'


def parse_with_line_evidence(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    extracted = {
        'Part_Number': 'Unknown',
        'Lead_ppm': 0,
        'Cadmium_ppm': 0,
        'Test_Standard': 'Unknown',
        'Report_Date': '2020-01-01',
        'Cert_Status': 'Missing',
        'Evidence_Part': {},
        'Evidence_Pb': {},
        'Evidence_Cd': {},
        'Evidence_Standard': {},
        'Evidence_Date': {},
        'Evidence_Statement': {}
    }

    # Satır satır tarayarak tam satır numaralarını ve kanıt metinlerini yakala
    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        # Part Number Match
        if extracted['Part_Number'] == 'Unknown':
            m = re.search(r'MTR-SUB-\d{2}', line)
            if m:
                extracted['Part_Number'] = m.group(0)
                extracted['Evidence_Part'] = {'line': idx, 'text': line}

        # Standard Match
        if extracted['Test_Standard'] == 'Unknown':
            m = re.search(r'(IEC\s*62321(?:-\d+)?|EN\s*50581|ISO\s*17025|ISO/IEC\s*17025)', line)
            if m:
                extracted['Test_Standard'] = m.group(0)
                extracted['Evidence_Standard'] = {'line': idx, 'text': line}

        # Date Match
        m_date = re.search(r'\b(20\d{2}-\d{2}-\d{2})\b', line)
        if m_date and ('DATE' in line.upper() or 'SUBMISSION' in line.upper() or 'ISSUANCE' in line.upper()):
            extracted['Report_Date'] = m_date.group(1)
            extracted['Evidence_Date'] = {'line': idx, 'text': line}

        # Cadmium (Cd)
        if 'CADMIUM' in line.upper() and ('MG/KG' in line.upper() or 'PPM' in line.upper()):
            m_cd = re.search(r'(\d+)\s*(?:mg/kg|ppm)', line, re.IGNORECASE)
            if m_cd:
                extracted['Cadmium_ppm'] = int(m_cd.group(1))
                extracted['Evidence_Cd'] = {'line': idx, 'text': line}

        # Lead (Pb)
        if 'LEAD' in line.upper() and ('PPM' in line.upper() or 'MG/KG' in line.upper()):
            m_pb = re.search(r'(\d+)\s*(?:ppm|mg/kg)', line, re.IGNORECASE)
            if m_pb:
                extracted['Lead_ppm'] = int(m_pb.group(1))
                extracted['Evidence_Pb'] = {'line': idx, 'text': line}

        # Statement check
        if any(w in line.lower() for w in ['comply', 'complies', 'approved', 'pass']) and 'STATUS' in line.upper():
            extracted['Cert_Status'] = 'Valid'
            extracted['Evidence_Statement'] = {'line': idx, 'text': line}

    return extracted


def run_extraction_pipeline():
    # 1. Execute Extraction
    extracted_data = parse_with_line_evidence(REPORT_PATH)

    # Master BOM parça listesini oku
    try:
        bom_df = pd.read_csv(BOM_PATH)
        bom_parts = bom_df['Part_Number'].tolist()
    except FileNotFoundError:
        bom_parts = []

    # 2. Run Evidence-Based Engineering Validation Gate
    audit = validate_report_evidence(
        extracted_data,
        master_bom_part_list=bom_parts,
        source_file=REPORT_PATH
    )

    # 3. Print Executive Audit Dossier
    print("=" * 75)
    print(f"PART: {audit['Part_Number']}")
    print("=" * 75)
    print("───────────────────────────────────────────────────────────────────────────")
    print(f"VALIDATION AUDIT TRAIL | RISK TIER: {audit['Risk_Tier']}")
    print("───────────────────────────────────────────────────────────────────────────")
    for c in audit['Checks']:
        icon = "[PASS]" if c.get('passed') else "[FLAG]"
        line_ref = f"[Line {c['line']}]" if c.get('line') else "[General]"
        print(f"  {icon} {c['item']:<35} {line_ref:>10}")
        if c.get('evidence'):
            print(f"         Evidence: \"{c['evidence']}\"")

    print("───────────────────────────────────────────────────────────────────────────")
    print(f"WORKFLOW VERDICT : {audit['Workflow_Decision']}")
    print(f"CONFIDENCE SCORE : {audit['Confidence_Score']}/100")
    print("───────────────────────────────────────────────────────────────────────────")

    if audit['Why_Flagged']:
        print("\nWHY WAS THIS FLAGGED?")
        for idx, r in enumerate(audit['Why_Flagged'], 1):
            print(f"  {idx}. {r}")

    if audit['Recommended_Actions']:
        print("\nRECOMMENDED ACTIONS:")
        for idx, a in enumerate(audit['Recommended_Actions'], 1):
            print(f"  -> {a}")

    # 4. Multi-Tier Workflow Routing
    if audit['Workflow_Decision'] == 'AUTO-ACCEPT':
        df = pd.read_csv(BOM_PATH)
        mask = df['Part_Number'] == audit['Part_Number']
        df.loc[mask, 'Lead_ppm'] = extracted_data['Lead_ppm']
        df.loc[mask, 'Cadmium_ppm'] = extracted_data['Cadmium_ppm']
        df.loc[mask, 'Cert_Status'] = extracted_data['Cert_Status']
        df.to_csv(BOM_PATH, index=False, encoding='utf-8-sig')
        print(f"\n>>> [WORKFLOW: LOW RISK] Auto-Accepted. Master BOM updated.")

    elif audit['Workflow_Decision'] == 'ENGINEER REVIEW':
        review_id = f"REV-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

        ev_refs = []
        for c in audit.get('Checks', []):
            if not c.get('passed') or 'Report Date' in c.get('item', ''):
                line_str = f"Line {c['line']}" if c.get('line') else "N/A"
                ev_refs.append(f"{c['item']} [{line_str}]: {c['evidence']}")

        row = {
            'review_id': [review_id],
            'part_number': [audit.get('Part_Number', 'MTR-SUB-11')],
            'risk_tier': [audit.get('Risk_Tier', 'MEDIUM RISK')],
            'confidence_score': [audit.get('Confidence_Score', 75)],
            'risk_reason': ["; ".join(audit.get('Why_Flagged', []))],
            'evidence_reference': [" | ".join(ev_refs)],
            'recommended_action': ["; ".join(audit.get('Recommended_Actions', []))],
            'source_file': [audit.get('Source_File', REPORT_PATH)],
            'lead_ppm': [extracted_data.get('Lead_ppm', 0)],
            'cadmium_ppm': [extracted_data.get('Cadmium_ppm', 0)],
            'cert_status': [extracted_data.get('Cert_Status', 'Pending')],
            'timestamp': [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        }

        q_file = 'engineer_review_queue.csv'
        try:
            existing_q = pd.read_csv(q_file)
            if 'part_number' in existing_q.columns and audit.get('Part_Number') not in existing_q['part_number'].values:
                updated_q = pd.concat([existing_q, pd.DataFrame(row)], ignore_index=True)
                updated_q.to_csv(q_file, index=False, encoding='utf-8-sig')
            elif 'part_number' not in existing_q.columns:
                pd.DataFrame(row).to_csv(q_file, index=False, encoding='utf-8-sig')
        except (FileNotFoundError, pd.errors.EmptyDataError):
            pd.DataFrame(row).to_csv(q_file, index=False, encoding='utf-8-sig')

        print(f"\n>>> [WORKFLOW: MEDIUM RISK] Master BOM untouched. Assigned [{review_id}].")
        print(f">>> Routed to 'engineer_review_queue.csv' for Human-in-the-Loop decision.")

    else:  # REJECT
        row = {
            'Part_Number': [audit['Part_Number']],
            'Risk_Tier': [audit['Risk_Tier']],
            'Reasons': ["; ".join(audit['Why_Flagged'])],
            'Source_File': [audit['Source_File']],
            'Timestamp': [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        }
        pd.DataFrame(row).to_csv('rejected_declarations.csv', mode='a', index=False, header=True)
        print(f"\n>>> [WORKFLOW: HIGH RISK] Document outright REJECTED. Logged in 'rejected_declarations.csv'.")


if __name__ == "__main__":
    run_extraction_pipeline()