import os
import datetime
import pandas as pd
from tabulate import tabulate

QUEUE_FILE = 'engineer_review_queue.csv'
AUDIT_LOG_FILE = 'audit_resolution_log.csv'
BOM_FILE = 'motor_bom.csv'
REJECTED_FILE = 'rejected_declarations.csv'


def display_banner():
    print("=" * 80)
    print("      ENGINEERING COMPLIANCE DECISION ENGINE - HUMAN REVIEW MANAGER      ")
    print("                [AUDIT RESOLUTION & WAIVER GOVERNANCE]                  ")
    print("=" * 80)


def load_queue():
    if not os.path.exists(QUEUE_FILE):
        return pd.DataFrame()
    try:
        df = pd.read_csv(QUEUE_FILE)
        return df
    except Exception:
        return pd.DataFrame()


def log_audit_resolution(resolution_record):
    """Kararı asla silinemez denetim kütüğüne (audit trail) kaydeder."""
    df_new = pd.DataFrame([resolution_record])
    if not os.path.exists(AUDIT_LOG_FILE):
        df_new.to_csv(AUDIT_LOG_FILE, index=False, encoding='utf-8-sig')
    else:
        df_new.to_csv(AUDIT_LOG_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')


def process_review():
    display_banner()
    queue = load_queue()

    if queue.empty:
        print("\n[INFO] No pending compliance items in the review queue. All clear!")
        return

    print(f"\n[PENDING REVIEWS: {len(queue)} ITEMS FOUND]")
    summary_cols = ['review_id', 'part_number', 'risk_tier', 'confidence_score', 'risk_reason']
    available_cols = [c for c in summary_cols if c in queue.columns]
    print(tabulate(queue[available_cols], headers='keys', tablefmt='psql', showindex=True))

    item_idx_str = input("\nSelect index to audit & resolve [or 'q' to quit]: ").strip()
    if item_idx_str.lower() == 'q':
        return

    try:
        idx = int(item_idx_str)
        item = queue.iloc[idx]
    except (ValueError, IndexError):
        print("[ERROR] Invalid index selected.")
        return

    print("\n" + "-" * 80)
    print(f"DOSSIER DETAILS | REVIEW ID: {item.get('review_id')}")
    print("-" * 80)
    print(f"Target Part Number    : {item.get('part_number')}")
    print(f"Risk Tier             : {item.get('risk_tier')} (Confidence: {item.get('confidence_score')}/100)")
    print(f"Risk Rationale        : {item.get('risk_reason')}")
    print(f"Evidence Reference    : {item.get('evidence_reference')}")
    print(f"Source Document       : {item.get('source_file')}")
    print(f"Candidate Chemistry   : Pb: {item.get('lead_ppm')} ppm | Cd: {item.get('cadmium_ppm')} ppm")
    print(f"Recommended Action    : {item.get('recommended_action')}")
    print("-" * 80)

    print("\nSELECT FORMAL ENGINEERING DECISION:")
    print("  [1] APPROVE WITH WAIVER   -> Authorize deviation, document waiver, update Master BOM")
    print("  [2] REJECT DECLARATION    -> Decline document, log rejection, trigger procurement escalation")
    print("  [3] REQUEST NEW EVIDENCE  -> Keep on hold, request updated third-party laboratory test")
    print("  [4] CANCEL / EXIT")

    choice = input("\nEnter decision [1-4]: ").strip()

    if choice == "1":
        decision = "APPROVE"
        engineer_id = input("\nEnter Certified Engineer ID (e.g., ENG-4402): ").strip()
        while not engineer_id:
            engineer_id = input("Engineer ID is mandatory. Enter ID: ").strip()

        engineer_comment = input("Enter Technical Justification / Review Comment: ").strip()
        waiver_reason = input(
            "Enter Formal Waiver Rationale (e.g., Low mechanical friction, non-accessible sub-assembly): ").strip()
        bom_rev = input("Target Approved BOM Revision (Default: REV-B): ").strip() or "REV-B"

        resolution = {
            'review_id': item.get('review_id'),
            'part_number': item.get('part_number'),
            'risk_reason': item.get('risk_reason'),
            'evidence_reference': item.get('evidence_reference'),
            'engineer_comment': engineer_comment,
            'decision': decision,
            'waiver_reason': waiver_reason,
            'engineer_id': engineer_id,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'approved_bom_revision': bom_rev
        }

        # 1. Audit Log'a yaz
        log_audit_resolution(resolution)

        # 2. Master BOM'u güncelle (Waiver ile onaylandı)
        try:
            bom_df = pd.read_csv(BOM_FILE)
            mask = bom_df['Part_Number'] == item.get('part_number')
            if mask.any():
                bom_df.loc[mask, 'Lead_ppm'] = item.get('lead_ppm')
                bom_df.loc[mask, 'Cadmium_ppm'] = item.get('cadmium_ppm')
                bom_df.loc[mask, 'Cert_Status'] = f"Waiver Approved ({engineer_id})"
                bom_df.to_csv(BOM_FILE, index=False, encoding='utf-8-sig')
                print(f"\n>>> [SUCCESS] Master BOM updated with Authorized Waiver under {bom_rev}.")
        except Exception as e:
            print(f"[ERROR] Failed to update Master BOM: {e}")

    elif choice == "2":
        decision = "REJECT"
        engineer_id = input("\nEnter Certified Engineer ID: ").strip()
        engineer_comment = input("Enter Rejection Rationale for Procurement: ").strip()

        resolution = {
            'review_id': item.get('review_id'),
            'part_number': item.get('part_number'),
            'risk_reason': item.get('risk_reason'),
            'evidence_reference': item.get('evidence_reference'),
            'engineer_comment': engineer_comment,
            'decision': decision,
            'waiver_reason': "NONE (REJECTED)",
            'engineer_id': engineer_id,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'approved_bom_revision': "N/A"
        }
        log_audit_resolution(resolution)

        # Rejected CSV dosyasına kaydet
        rej_df = pd.DataFrame([{
            'part_number': item.get('part_number'),
            'rejection_reason': item.get('risk_reason'),
            'engineer_id': engineer_id,
            'comment': engineer_comment,
            'source_file': item.get('source_file'),
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        if not os.path.exists(REJECTED_FILE):
            rej_df.to_csv(REJECTED_FILE, index=False, encoding='utf-8-sig')
        else:
            rej_df.to_csv(REJECTED_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')

        print(f"\n>>> [REJECTED] Document permanently declined and logged.")

    elif choice == "3":
        decision = "REQUEST_NEW_EVIDENCE"
        engineer_id = input("\nEnter Certified Engineer ID: ").strip()
        engineer_comment = input("Specify Required Laboratory Testing Details: ").strip()

        resolution = {
            'review_id': item.get('review_id'),
            'part_number': item.get('part_number'),
            'risk_reason': item.get('risk_reason'),
            'evidence_reference': item.get('evidence_reference'),
            'engineer_comment': engineer_comment,
            'decision': decision,
            'waiver_reason': "PENDING RE-CERTIFICATION",
            'engineer_id': engineer_id,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'approved_bom_revision': "HOLD"
        }
        log_audit_resolution(resolution)
        print(f"\n>>> [STATUS: ON HOLD] Escalated to Supplier Quality for renewed evidence.")

    else:
        print("[ABORTED] No action taken.")
        return

    # Çözümlenen satırı kuyruktan kaldır
    updated_queue = queue.drop(index=idx)
    updated_queue.to_csv(QUEUE_FILE, index=False, encoding='utf-8-sig')
    print(f"[QUEUE UPDATED] Item removed from active queue. Resolution permanently archived in '{AUDIT_LOG_FILE}'.")


if __name__ == "__main__":
    process_review()