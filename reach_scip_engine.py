import os
import pandas as pd
from tabulate import tabulate
from reach_config import SVHC_CANDIDATE_LIST, SCIP_CONFIG

BOM_FILE = 'motor_bom.csv'
SCIP_DOSSIER_CSV = 'echa_scip_dossier.csv'


def clean_numeric(val):
    import re
    if pd.isna(val):
        return 0.0
    s = str(val).strip()
    m = re.search(r'[-+]?\d*\.?\d+', s)
    return float(m.group(0)) if m else 0.0


def run_reach_scip_assessment():
    print("=" * 85)
    print("      REACH SVHC ARTICLE ASSESSMENT & ECHA SCIP DOSSIER ENGINE (WFD Art. 9)     ")
    print("   [LEGAL PRINCIPLE: CJEU C-106/14 - 'ONCE AN ARTICLE, ALWAYS AN ARTICLE']     ")
    print("=" * 85)

    if not os.path.exists(BOM_FILE):
        print(f"[ERROR] '{BOM_FILE}' not found.")
        return

    df = pd.read_csv(BOM_FILE)
    df.columns = df.columns.astype(str).str.strip()

    scip_dossier_records = []
    assessment_summary = []

    for _, row in df.iterrows():
        part_no = row['Part_Number']
        part_name = row['Part_Name']
        sub_assembly = row['Sub_Assembly']
        material = str(row.get('Material', 'Unknown'))

        # Her parça bağımsız bir "Artikel (Article as such)"dir.
        # Konsantrasyon doğrudan bu artiklein kendi kimyasal içeriğinde hesaplanır.
        pb_ppm = clean_numeric(row.get('Lead_ppm', 0))

        # Konsantrasyon kontrolü (% w/w)
        pb_weight_pct = pb_ppm / 10000.0  # 10,000 ppm = %1.0 | 1000 ppm = %0.1

        svhc_detected = False
        substance_info = None

        # Kurşun SVHC değerlendirmesi
        if pb_ppm > SCIP_CONFIG['threshold_ppm']:
            svhc_detected = True
            substance_info = SVHC_CANDIDATE_LIST["Lead"]
            substance_name = "Lead"
            conc_ppm = pb_ppm
            conc_pct = pb_weight_pct

        # Raporlama ve SCIP Uygulanabilirlik Tablosu
        if svhc_detected:
            scip_required = "MANDATORY"
            # Konsantrasyon aralığı (ECHA SCIP Standardı)
            if 0.1 <= conc_pct < 1.0:
                conc_range = "≥ 0.1% w/w and < 1.0% w/w"
            elif 1.0 <= conc_pct < 10.0:
                conc_range = "≥ 1.0% w/w and < 10.0% w/w"
            else:
                conc_range = "≥ 10.0% w/w"

            # Resmi ECHA SCIP Veri Paketi Kaydı
            scip_dossier_records.append({
                'Article_Identifier': part_no,
                'Article_Name': part_name,
                'Sub_Assembly_Context': sub_assembly,
                'Article_Category_CN': SCIP_CONFIG['complex_object_cn_code'],
                'Material_Category': material,
                'Candidate_Substance': substance_name,
                'EC_Number': substance_info['ec_number'],
                'CAS_Number': substance_info['cas_number'],
                'Reason_for_Inclusion': substance_info['reason_for_inclusion'],
                'Concentration_PPM': f"{conc_ppm:.0f}",
                'Concentration_Range': conc_range,
                'Safe_Use_Instructions': substance_info['safe_use_instructions'],
                'SCIP_Duty_Trigger': 'WFD Art. 9(1)(i) / REACH Art. 33(1)'
            })

            assessment_summary.append({
                'Part_Number': part_no,
                'Article_Name': part_name,
                'Substance': substance_name,
                'Conc_%w/w': f"{conc_pct:.2f}%",
                'Article_Threshold': "> 0.1% w/w",
                'SCIP_Obligation': scip_required
            })
        else:
            assessment_summary.append({
                'Part_Number': part_no,
                'Article_Name': part_name,
                'Substance': "None > 0.1%",
                'Conc_%w/w': f"{pb_weight_pct:.4f}%",
                'Article_Threshold': "≤ 0.1% w/w",
                'SCIP_Obligation': "EXEMPT"
            })

    # Terminal Çıktısı
    print("\n--- ARTICLE-LEVEL REACH SVHC SCREENING MATRIX ---")
    summary_df = pd.DataFrame(assessment_summary)
    print(tabulate(summary_df, headers='keys', tablefmt='psql', showindex=False))

    print("\n" + "=" * 85)
    print("                     ECHA SCIP NOTIFICATION APPLICABILITY")
    print("=" * 85)
    total_articles = len(df)
    mandatory_scip = len(scip_dossier_records)

    print(f"Total Evaluated Component Articles : {total_articles}")
    print(f"Articles Requiring SCIP Submission : {mandatory_scip}")
    print(
        f"Parent Complex Object CN Code      : {SCIP_CONFIG['complex_object_cn_code']} ({SCIP_CONFIG['complex_object_name']})")

    if mandatory_scip > 0:
        dossier_df = pd.DataFrame(scip_dossier_records)
        dossier_df.to_csv(SCIP_DOSSIER_CSV, index=False, encoding='utf-8-sig')
        print(f"\n[INFO] Official ECHA SCIP Dossier Dataset exported to '{SCIP_DOSSIER_CSV}'.")
        print("\n--- SAMPLE SCIP DOSSIER FIELDS (First 2 Articles) ---")
        preview_cols = ['Article_Identifier', 'Article_Name', 'Candidate_Substance', 'Concentration_Range',
                        'Safe_Use_Instructions']
        print(tabulate(dossier_df[preview_cols].head(2), headers='keys', tablefmt='psql', showindex=False))
    else:
        print("\n[INFO] No articles exceed 0.1% w/w. ECHA SCIP submission is NOT triggered.")


if __name__ == "__main__":
    run_reach_scip_assessment()