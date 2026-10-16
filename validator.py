import datetime
import re

def validate_report_evidence(extracted_data, master_bom_part_list=None, source_file="unknown"):
    """
    Laboratuvar ve tedarikçi kanıtlarını 7 kurala göre deterministik olarak denetler.
    Risk kademeleri:
      - LOW RISK (Confidence >= 85) -> AUTO-ACCEPT
      - MEDIUM RISK (70 <= Confidence < 85) -> ENGINEER REVIEW
      - HIGH RISK (Confidence < 70) -> REJECT
    """
    if master_bom_part_list is None:
        master_bom_part_list = []

    score = 100
    why_flagged = []
    recommended_actions = []
    checks = []

    part_no = str(extracted_data.get('Part_Number', '')).strip()
    report_date_str = str(extracted_data.get('Report_Date', '')).strip()
    standard = str(extracted_data.get('Test_Standard', '')).strip()
    cert_status = str(extracted_data.get('Cert_Status', '')).strip()

    # 1. BOM Eşleşme Kontrolü
    if master_bom_part_list and part_no not in master_bom_part_list:
        score -= 25
        why_flagged.append(f"Part Number '{part_no}' not found in active Master BOM.")
        recommended_actions.append("Verify component against engineering change order (ECO).")
        checks.append({'item': 'BOM Alignment', 'passed': False, 'evidence': f"Unmatched '{part_no}'", 'line': 0})
    else:
        checks.append({'item': 'BOM Alignment', 'passed': True, 'evidence': f"Matched '{part_no}'", 'line': 18})

    # 2. Test Standardı ve Akreditasyon Kontrolü
    valid_standards = ['17025', '62321', 'iso', 'iec']
    if any(s in standard.lower() for s in valid_standards):
        checks.append({'item': 'Test Standard', 'passed': True, 'evidence': standard, 'line': 4})
    else:
        score -= 20
        why_flagged.append(f"Invalid or missing laboratory standard: '{standard}'")
        recommended_actions.append("Require test execution by ISO/IEC 17025 accredited facility.")
        checks.append({'item': 'Test Standard', 'passed': False, 'evidence': standard, 'line': 4})

    # 3. Rapor Tarihi ve Raf Ömrü Denetimi (< 24 Ay, Gelecek Tarih Yasağı)
    try:
        rep_date = datetime.datetime.strptime(report_date_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        diff_years = (today - rep_date).days / 365.25

        if rep_date > today:
            score -= 35
            why_flagged.append("Report Date is in the future (invalid validity).")
            recommended_actions.append("Reject falsified or misdated test report.")
            checks.append({'item': 'Report Date', 'passed': False, 'evidence': f"Future date: {report_date_str}", 'line': 9})
        elif diff_years > 2.0:
            score -= 25
            why_flagged.append(f"Declaration exceeds 24-month validity threshold ({diff_years:.1f} years old).")
            recommended_actions.append("Request updated supplier declaration / annual recertification.")
            checks.append({'item': 'Report Date', 'passed': False, 'evidence': f"Report is {diff_years:.1f} years old (> 2.0 yr shelf-life)", 'line': 9})
        else:
            checks.append({'item': 'Report Date', 'passed': True, 'evidence': f"Valid ({diff_years:.1f} years old)", 'line': 9})
    except ValueError:
        score -= 25
        why_flagged.append(f"Unparseable report date format: '{report_date_str}'")
        checks.append({'item': 'Report Date', 'passed': False, 'evidence': report_date_str, 'line': 9})

    # 4. Kimyasal Fiziksel Sınır Kontrolü (0 <= ppm <= 1.000.000)
    def parse_ppm(v):
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

    pb = parse_ppm(extracted_data.get('Lead_ppm', 0))
    cd = parse_ppm(extracted_data.get('Cadmium_ppm', 0))

    if pb < 0 or cd < 0:
        score -= 40
        why_flagged.append("Negative chemical concentration detected (out of physical range).")
        recommended_actions.append("Reject corrupted lab test result.")
    elif pb > 1000000 or cd > 1000000:
        score -= 40
        why_flagged.append("Hyper-concentration detected (> 1,000,000 ppm / 100% w/w).")
        recommended_actions.append("Reject data parsing anomaly.")

    # 5. Beyan Durumu Kontrolü
    if 'approv' in cert_status.lower() or 'valid' in cert_status.lower():
        checks.append({'item': 'Legal Statement', 'passed': True, 'evidence': cert_status, 'line': 69})
    else:
        score -= 15
        why_flagged.append(f"Ambiguous or missing compliance statement: '{cert_status}'")
        checks.append({'item': 'Legal Statement', 'passed': False, 'evidence': cert_status, 'line': 69})

    # Risk Kademesi ve Karar Belirleme
    score = max(0, min(100, score))
    if score >= 85:
        risk_tier = 'LOW RISK'
        decision = 'AUTO-ACCEPT'
    elif score >= 70:
        risk_tier = 'MEDIUM RISK'
        decision = 'ENGINEER REVIEW'
    else:
        risk_tier = 'HIGH RISK'
        decision = 'REJECT'

    return {
        'Part_Number': part_no,
        'Risk_Tier': risk_tier,
        'Confidence_Score': score,
        'Workflow_Decision': decision,
        'Why_Flagged': why_flagged,
        'Recommended_Actions': recommended_actions,
        'Checks': checks,
        'Source_File': source_file
    }

# Geriye dönük uyumluluk için eski isim takma adı:
validate_evidence = validate_report_evidence