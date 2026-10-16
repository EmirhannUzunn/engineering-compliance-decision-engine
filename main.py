import subprocess
import sys


def main():
    print("=" * 70)
    print("   ENGINEERING COMPLIANCE DECISION ENGINE (ECDE) - ORCHESTRATOR    ")
    print("=" * 70)

    print("\nSelect Operational Mode:")
    print("  [1] Run Multi-Regional Audit Pipeline (EU RoHS, US TSCA/Prop65, China)")
    print("  [2] Open Human Review & Waiver Manager (Audit Resolution Queue)")
    print("  [3] Run REACH SVHC Article Assessment & Generate ECHA SCIP Dossier")
    print("  [4] Generate Official Engineering Compliance Audit Dossier (Full Audit Report)")

    op_choice = input("\nEnter mode [1-4] (Default: 1): ").strip()

    if op_choice == "2":
        subprocess.run(["python", "review_manager.py"], check=True)
        return
    elif op_choice == "3":
        subprocess.run(["python", "reach_scip_engine.py"], check=True)
        return
    elif op_choice == "4":
        subprocess.run(["python", "export_dossier.py"], check=True)
        return

    print("\nSelect Target Export Market / Regulatory Standard:")
    print("  [1] European Union (EU)   -> RoHS 2.0 + Exemption 6(c)")
    print("  [2] United States (US)    -> TSCA + California Prop 65 (Strict Pb)")
    print("  [3] China (MIIT)          -> China RoHS (SJ/T 11364 & EFUP)")
    print("  [4] GLOBAL CLEARANCE      -> Audit against ALL regions simultaneously")

    choice = input("\nEnter choice [1-4] (Default: 4 - GLOBAL): ").strip()
    market_map = {"1": "EU", "2": "US", "3": "CHINA", "4": "GLOBAL"}
    target_market = market_map.get(choice, "GLOBAL")

    print(f"\n>>> Selected Evaluation Scope: [{target_market}]")

    print("\n>>> [1/2] Ingesting Unstructured Supplier Documentation & Verification Gate...")
    subprocess.run(["python", "doc_parser.py"], check=True)

    print(f"\n>>> [2/2] Running Multi-Regional Compliance Engine for [{target_market}]...")
    subprocess.run(["python", "analiz.py", target_market], check=True)

    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE: Global Clearance Passport & Audit Generated  ")
    print("=" * 70)


if __name__ == "__main__":
    main()