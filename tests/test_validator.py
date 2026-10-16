import datetime
import pytest
from validator import (validate_report_evidence)

MOCK_BOM = ['MTR-SUB-01', 'MTR-SUB-11']

def test_valid_lab_report_auto_accept():
    """Tüm koşulları sağlayan geçerli ve yeni laboratuvar raporu AUTO-ACCEPT almalıdır."""
    data = {
        'Part_Number': 'MTR-SUB-11',
        'Report_Date': datetime.date.today().strftime('%Y-%m-%d'),
        'Test_Standard': 'ISO/IEC 17025 Certified Test Facility',
        'Lead_ppm': 15.0,
        'Cadmium_ppm': 2.0,
        'Mercury_ppm': 0.0,
        'Cert_Status': 'Approved and fully compliant'
    }
    result = validate_report_evidence(data, MOCK_BOM, source_file="test.txt")
    assert result['Workflow_Decision'] == 'AUTO-ACCEPT'
    assert result['Confidence_Score'] >= 85
    assert result['Risk_Tier'] == 'LOW RISK'

def test_future_dated_report_rejected_or_flagged():
    """Gelecek tarihli laboratuvar raporu güven skoru düşürülmeli ve incelemeye alınmalıdır."""
    future_date = (datetime.date.today() + datetime.timedelta(days=365)).strftime('%Y-%m-%d')
    data = {
        'Part_Number': 'MTR-SUB-11',
        'Report_Date': future_date,
        'Test_Standard': 'ISO/IEC 17025',
        'Lead_ppm': 10.0,
        'Cadmium_ppm': 1.0,
        'Cert_Status': 'Approved'
    }
    result = validate_report_evidence(data, MOCK_BOM)
    assert result['Workflow_Decision'] in ['ENGINEER REVIEW', 'REJECT']
    assert any('future' in str(w).lower() or 'validity' in str(w).lower() for w in result['Why_Flagged'])

def test_expired_evidence_triggers_review():
    """24 aydan eski rapor Master BOM'u doğrudan güncelleyemez; ENGINEER REVIEW kuyruğuna gitmelidir."""
    data = {
        'Part_Number': 'MTR-SUB-11',
        'Report_Date': '2021-01-01',
        'Test_Standard': 'ISO/IEC 17025',
        'Lead_ppm': 18.0,
        'Cadmium_ppm': 2.0,
        'Cert_Status': 'Approved'
    }
    result = validate_report_evidence(data, MOCK_BOM)
    assert result['Workflow_Decision'] == 'ENGINEER REVIEW'
    assert result['Risk_Tier'] == 'MEDIUM RISK'
    assert any('threshold' in str(w).lower() or 'years old' in str(w).lower() for w in result['Why_Flagged'])

def test_negative_ppm_triggers_rejection():
    """Negatif kimyasal konsantrasyon fiziksel olarak imkansızdır; REJECT tetiklemelidir."""
    data = {
        'Part_Number': 'MTR-SUB-11',
        'Report_Date': datetime.date.today().strftime('%Y-%m-%d'),
        'Test_Standard': 'ISO/IEC 17025',
        'Lead_ppm': -1.0,
        'Cadmium_ppm': 2.0,
        'Cert_Status': 'Approved'
    }
    result = validate_report_evidence(data, MOCK_BOM)
    assert result['Workflow_Decision'] == 'REJECT' or result['Confidence_Score'] < 70
    assert any('concentration' in str(w).lower() or 'range' in str(w).lower() for w in result['Why_Flagged'])

def test_hyper_concentration_above_1m_ppm_rejected():
    """1.000.000 ppm (%100)'den büyük değerler veri bozulmasıdır; kabul edilemez."""
    data = {
        'Part_Number': 'MTR-SUB-11',
        'Report_Date': datetime.date.today().strftime('%Y-%m-%d'),
        'Test_Standard': 'ISO/IEC 17025',
        'Lead_ppm': 1500000.0,
        'Cadmium_ppm': 0.0,
        'Cert_Status': 'Approved'
    }
    result = validate_report_evidence(data, MOCK_BOM)
    assert result['Workflow_Decision'] == 'REJECT' or result['Confidence_Score'] < 70

def test_missing_part_number_in_bom():
    """BOM'da olmayan yabancı parça kodları Master veriye sızamaz."""
    data = {
        'Part_Number': 'MTR-UNKNOWN-99',
        'Report_Date': datetime.date.today().strftime('%Y-%m-%d'),
        'Test_Standard': 'ISO/IEC 17025',
        'Lead_ppm': 10.0,
        'Cadmium_ppm': 0.0,
        'Cert_Status': 'Approved'
    }
    result = validate_report_evidence(data, MOCK_BOM)
    assert result['Workflow_Decision'] != 'AUTO-ACCEPT'
    assert any('BOM' in str(w) for w in result['Why_Flagged'])