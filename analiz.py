import sys
import re
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
from regulations_config import REGULATORY_PROFILES

def clean_numeric(val):
    """Metin içindeki $, noktalı virgül (;;;), boşluk ve yabancı karakterleri temizleyip float sayıya çevirir."""
    def extract_num(v):
        if pd.isna(v):
            return 0.0
        s = str(v).strip()
        match = re.search(r'[-+]?\d*\.?\d+', s)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return 0.0
        return 0.0

    if isinstance(val, pd.Series):
        return val.apply(extract_num)
    return extract_num(val)

def run_compliance_analysis(target_region="GLOBAL"):
    bom_file = 'motor_bom.csv'
    catalog_file = 'supplier_catalog.csv'

    df = pd.read_csv(bom_file)
    cat_df = pd.read_csv(catalog_file)

    # Başlıklardaki gizli boşlukları ve noktalı virgülleri temizle
    df.columns = df.columns.astype(str).str.replace(';', '').str.strip()
    cat_df.columns = cat_df.columns.astype(str).str.replace(';', '').str.strip()

    # 1. Esnek Sütun Eşleştirme - Master BOM
    weight_col = next((c for c in df.columns if 'weight' in c.lower() or 'mass' in c.lower()), None)
    cost_col = next((c for c in df.columns if 'cost' in c.lower() or 'price' in c.lower()), None)
    qty_col = next((c for c in df.columns if 'qty' in c.lower() or 'quantity' in c.lower()), None)

    if not weight_col or not cost_col or not qty_col:
        raise KeyError(f"Master BOM sütun hatası! Mevcut sütunlar: {list(df.columns)}")

    # BOM Sayısal Değerleri Temizle
    df[cost_col] = clean_numeric(df[cost_col])
    df[weight_col] = clean_numeric(df[weight_col])
    df[qty_col] = clean_numeric(df[qty_col])

    # 2. Sütun Eşleştirme - Supplier Catalog
    cat_cost_col = 'Unit_Cost_USD' if 'Unit_Cost_USD' in cat_df.columns else next((c for c in cat_df.columns if 'cost' in c.lower() or 'price' in c.lower()), None)
    cat_target_name_col = 'Target_Part_Name' if 'Target_Part_Name' in cat_df.columns else cat_df.columns[1]
    alt_part_col = 'Alt_Part_Number' if 'Alt_Part_Number' in cat_df.columns else cat_df.columns[0]
    supplier_col = 'Supplier' if 'Supplier' in cat_df.columns else cat_df.columns[2]

    # 3. Kütle ve Maliyet Dağılımı
    df['Extended_Weight_g'] = df[qty_col] * df[weight_col]
    df['Extended_Cost_USD'] = df[qty_col] * df[cost_col]

    total_mass_kg = df['Extended_Weight_g'].sum() / 1000.0
    total_cost_usd = df['Extended_Cost_USD'].sum()

    sub_summary = df.groupby('Sub_Assembly').agg(
        Total_Weight_g=('Extended_Weight_g', 'sum'),
        Weight_Share_Pct=('Extended_Weight_g', lambda x: (x.sum() / (total_mass_kg * 1000)) * 100),
        Total_Cost_USD=('Extended_Cost_USD', 'sum'),
        Cost_Share_Pct=('Extended_Cost_USD', lambda x: (x.sum() / total_cost_usd) * 100)
    ).round(2)

    regions_to_check = [target_region] if target_region in REGULATORY_PROFILES else list(REGULATORY_PROFILES.keys())

    print("=" * 80)
    print(f"MULTI-REGION COMPLIANCE & SOURCING ENGINE | TARGET: {target_region}")
    print(f"Total Mass: {total_mass_kg:.2f} kg | Baseline BOM Cost: ${total_cost_usd:.2f}")
    print("=" * 80)

    print("\n--- SUB-ASSEMBLY DISTRIBUTION ---")
    print(tabulate(sub_summary, headers='keys', tablefmt='psql'))

    regional_violations = {reg: [] for reg in regions_to_check}

    # 4. Seçilen Bölgelere Göre Uyum Denetimi
    for reg_key in regions_to_check:
        profile = REGULATORY_PROFILES[reg_key]
        limits = profile['limits_ppm']
        exemptions = profile.get('exemptions_supported', {})

        for _, row in df.iterrows():
            part = row['Part_Number']
            name = row['Part_Name']
            sub = row['Sub_Assembly']
            supp = row['Supplier']
            mat = str(row['Material'])
            pb = clean_numeric(row['Lead_ppm'])
            cd = clean_numeric(row['Cadmium_ppm'])
            hg = clean_numeric(row['Mercury_ppm'])
            cert = str(row['Cert_Status']).strip()

            reasons = []

            if cert != 'Valid':
                reasons.append(f"Missing Declaration ({cert})")

            if cd > limits['Cadmium']:
                reasons.append(f"Cadmium ({cd:.0f} ppm > {limits['Cadmium']})")

            if hg > limits['Mercury']:
                reasons.append(f"Mercury ({hg:.0f} ppm > {limits['Mercury']})")

            if pb > limits['Lead']:
                has_exemption = False
                for ex_name, ex_rule in exemptions.items():
                    if ex_rule['material'].lower() in mat.lower() and pb <= ex_rule['max_ppm']:
                        has_exemption = True
                        break
                if not has_exemption:
                    reasons.append(f"Lead ({pb:.0f} ppm > {limits['Lead']})")

            if reasons:
                regional_violations[reg_key].append({
                    'Part_Number': part,
                    'Part_Name': name,
                    'Sub_Assembly': sub,
                    'Supplier': supp,
                    'Reasons': "; ".join(reasons)
                })

    # 5. Global Market Clearance Passport Özeti
    print("\n" + "=" * 80)
    print("                 GLOBAL MARKET CLEARANCE PASSPORT")
    print("=" * 80)
    for reg_key, flagged in regional_violations.items():
        status = "PASSED" if len(flagged) == 0 else f"FLAGGED ({len(flagged)} Risks)"
        mark = REGULATORY_PROFILES[reg_key]['mandatory_mark']
        print(f"[*] {REGULATORY_PROFILES[reg_key]['region_name']:<42} -> [{status}]")
        print(f"    Mandatory Label / Mark: {mark}")

    all_flagged_parts = set()
    for reg_key in regions_to_check:
        for item in regional_violations[reg_key]:
            all_flagged_parts.add(item['Part_Number'])

    flagged_df = df[df['Part_Number'].isin(all_flagged_parts)].copy()
    flagged_df.to_csv('supplier_action_list.csv', index=False)
    print(f"\n[INFO] {len(all_flagged_parts)} unique flagged items exported to 'supplier_action_list.csv'.")

    # 6. Sourcing Optimization
    print("\n" + "=" * 80)
    print("                SOURCING OPTIMIZATION & REPLACEMENT MATRIX")
    print("=" * 80)

    total_delta = 0.0
    for part in all_flagged_parts:
        row = df[df['Part_Number'] == part].iloc[0]
        part_name = str(row['Part_Name']).strip()

        # Eşleşmeyi parça adı üzerinden ara
        alts = cat_df[cat_df[cat_target_name_col].astype(str).str.strip().str.lower() == part_name.lower()]

        if not alts.empty and cat_cost_col:
            # Fiyatları temizleyerek en ucuz alternatifi seç
            alts_clean = alts.copy()
            alts_clean['clean_cost'] = alts_clean[cat_cost_col].apply(clean_numeric)
            best_alt = alts_clean.sort_values(by='clean_cost').iloc[0]

            alt_price = clean_numeric(best_alt[cat_cost_col])
            current_price = clean_numeric(row[cost_col])
            qty = int(clean_numeric(row[qty_col]))

            unit_delta = alt_price - current_price
            ext_delta = unit_delta * qty
            total_delta += ext_delta

            unit_sign = "+" if unit_delta >= 0 else "-"
            ext_sign = "+" if ext_delta >= 0 else "-"

            pb_disp = clean_numeric(best_alt.get('Lead_ppm', 0))
            cd_disp = clean_numeric(best_alt.get('Cadmium_ppm', 0))

            print(f"[*] Resolving: {part} | {part_name}")
            print(f"    -> RECOMMENDED REPLACEMENT : {best_alt[alt_part_col]} ({best_alt[supplier_col]})")
            print(f"    -> Chemistry Profile       : Pb: {pb_disp:.1f} ppm | Cd: {cd_disp:.1f} ppm")
            print(f"    -> Unit Cost Impact        : ${alt_price:.2f} (Delta: {unit_sign}${abs(unit_delta):.2f})")
            print(f"    -> Extended BOM Impact     : {ext_sign}${abs(ext_delta):.2f} for Qty {qty}")
            print("-" * 60)
        else:
            print(f"[*] Unresolved: {part} | {part_name} -> No pre-qualified alternative catalog entry.")
            print("-" * 60)

    tot_sign = "+" if total_delta >= 0 else "-"
    projected_bom_cost = total_cost_usd + total_delta
    print(f"\n[EXECUTIVE SUMMARY] Target Region: {target_region}")
    print(f"Total BOM Delta to Achieve Clearance: {tot_sign}${abs(total_delta):.2f}")
    print(f"New Projected BOM Cost: ${projected_bom_cost:.2f}")

    # 7. Dağılım Grafiği
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    sub_summary['Total_Weight_g'].plot(kind='pie', ax=ax1, autopct='%1.1f%%', startangle=140, cmap='Set2')
    ax1.set_title(f'Sub-Assembly Mass Distribution (Total: {total_mass_kg:.2f} kg)')
    ax1.set_ylabel('')

    sub_summary['Total_Cost_USD'].plot(kind='bar', ax=ax2, color='#2b5c8f', edgecolor='black')
    ax2.set_title('Sub-Assembly Cost Breakdown ($USD)')
    ax2.set_ylabel('Cost ($USD)')
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('motor_analysis_chart.png', dpi=300)
    print("\n[INFO] 'motor_analysis_chart.png' generated successfully.")

if __name__ == "__main__":
    region_arg = sys.argv[1] if len(sys.argv) > 1 else "GLOBAL"
    run_compliance_analysis(region_arg)