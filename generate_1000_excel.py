import pandas as pd
import numpy as np
import datetime
import random


def generate_1000_part_excel():
    print("=" * 75)
    print("   GENERATING 1,000-ROW INDUSTRIAL COMPLEX BOM EXCEL FILE (.XLSX)   ")
    print("=" * 75)

    sub_assemblies = [
        "Rotor Sub-Assembly", "Stator Sub-Assembly", "Inverter Power Board",
        "Thermal & Structural Housing", "Planetary Gearbox Stage",
        "Feedback & Encoders", "Structural Fasteners", "Wire Harness & Terminals"
    ]

    materials = [
        "Machined Brass Alloy CuZn39Pb3", "Structural Steel S355JR", "Stainless Steel AISI 316",
        "Electrical Steel M400-50A", "High-Conductivity Copper CW004A", "Cast Aluminum AlSi10Mg",
        "PVC Cable Jacket Compound", "Silicone Elastomer Compound", "FR4 Multilayer PCB",
        "NdFeB Magnet Grade N48H", "Polyacetal POM-H", "FKM Fluoroelastomer"
    ]

    records = []
    today = datetime.date.today()

    for i in range(1, 1001):
        p_id = f"PRT-IND-{i:04d}"
        sub = random.choice(sub_assemblies)
        mat = random.choice(materials)
        qty = random.choice([1, 2, 4, 6, 8, 12, 16])
        unit_cost = round(random.uniform(0.35, 65.0), 2)
        weight_g = round(random.uniform(1.2, 420.0), 2)

        # Endüstriyel Senaryo Dağılımı (1000 parça için)
        dice = random.random()

        if dice < 0.70:
            # %70 Temiz, ISO 17025 Laboratuvar Raporlu, Uyumlu Parçalar
            pb_ppm = round(random.uniform(2.0, 75.0), 1)
            cd_ppm = round(random.uniform(0.0, 8.0), 1)
            cert_status = "Approved & Fully Valid"
            test_std = "IEC 62321:2013 ICP-OES"
            rep_date = (today - datetime.timedelta(days=random.randint(20, 250))).strftime("%Y-%m-%d")

        elif dice < 0.80:
            # %10 RoHS Exemption 6(c) Pirinç Parçalar (Pb: 25.000 - 36.000 ppm) -> SCIP Zorunlu!
            mat = "Machined Brass Alloy CuZn39Pb3"
            pb_ppm = round(random.uniform(24000.0, 36000.0), 1)
            cd_ppm = round(random.uniform(5.0, 25.0), 1)
            cert_status = "Exempt (RoHS 6c)"
            test_std = "ISO/IEC 17025 Accredited Laboratory"
            rep_date = (today - datetime.timedelta(days=random.randint(30, 350))).strftime("%Y-%m-%d")

        elif dice < 0.88:
            # %8 US California Prop 65 Tuzağı (850 - 980 ppm Pb -> EU RoHS geçer, US Prop 65 FAIL)
            pb_ppm = round(random.uniform(830.0, 980.0), 1)
            cd_ppm = round(random.uniform(0.0, 12.0), 1)
            cert_status = "Approved"
            test_std = "IEC 62321 ED.2"
            rep_date = (today - datetime.timedelta(days=random.randint(60, 300))).strftime("%Y-%m-%d")

        elif dice < 0.94:
            # %6 Süresi Dolmuş Evrak (3.5 - 5 yıl eski) -> Mühendis İnceleme Kuyruğu (HITL)
            pb_ppm = round(random.uniform(15.0, 60.0), 1)
            cd_ppm = 2.0
            cert_status = "Pending Annual Recertification"
            test_std = "ISO/IEC 17025"
            rep_date = (today - datetime.timedelta(days=random.randint(1100, 1800))).strftime("%Y-%m-%d")

        elif dice < 0.97:
            # %3 Sahte / Gelecek Tarihli Evrak -> DOĞRUDAN RET (REJECT)
            pb_ppm = 25.0
            cd_ppm = 1.0
            cert_status = "Approved"
            test_std = "ISO/IEC 17025"
            rep_date = (today + datetime.timedelta(days=random.randint(60, 300))).strftime("%Y-%m-%d")

        else:
            # %3 Fiziksel / Kimyasal Bozulma (Negatif veya > 1.000.000 ppm) -> REJECT
            pb_ppm = -15.0 if random.random() < 0.5 else 1450000.0
            cd_ppm = 0.0
            cert_status = "Corrupted Entry"
            test_std = "Unverified In-house QC"
            rep_date = today.strftime("%Y-%m-%d")

        records.append({
            "Part_Number": p_id,
            "Part_Name": f"Component_{mat.split()[0]}_{p_id}",
            "Sub_Assembly": sub,
            "Material": mat,
            "Quantity": qty,
            "Weight_g": weight_g,
            "Unit_Cost_USD": unit_cost,
            "Lead_ppm": pb_ppm,
            "Cadmium_ppm": cd_ppm,
            "Report_Date": rep_date,
            "Test_Standard": test_std,
            "Cert_Status": cert_status
        })

    raw_excel_file = "raw_master_bom_1000.xlsx"
    df = pd.DataFrame(records)
    df.to_excel(raw_excel_file, index=False)
    print(f"\n>>> [SUCCESS] 1,000-Row Raw BOM created: '{raw_excel_file}'")


if __name__ == "__main__":
    generate_1000_part_excel()