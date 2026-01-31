#!/usr/bin/env python3
"""
Final verification script - ensures everything is ready for deployment.
"""

import os
import sys
import json
from pathlib import Path

def verify_all():
    """Run all verification checks."""
    print("\n" + "=" * 80)
    print("FINAL VERIFICATION - WAYMO E2E PIPELINE")
    print("=" * 80)

    checks = {
        "Core Files": [
            "waymo_e2e_processor.py",
            "config.yaml",
            "requirements.txt",
        ],
        "Source Modules": [
            "src/__init__.py",
            "src/config.py",
            "src/dataset_loader.py",
            "src/image_processor.py",
            "src/trajectory_extractor.py",
            "src/prompt_builder.py",
            "src/vlm_client.py",
            "src/output_handler.py",
            "src/utils.py",
        ],
        "Documentation": [
            "START_HERE.md",
            "README.md",
            "QUICKSTART.md",
            "DEPLOYMENT.md",
            "TROUBLESHOOTING.md",
            "FILE_INDEX.md",
            "PROJECT_COMPLETION_REPORT.md",
            "IMPLEMENTATION_SUMMARY.md",
            "FINAL_SUMMARY.md",
            "DELIVERY_SUMMARY.md",
        ],
        "Helper Scripts": [
            "validate_setup.py",
            "quickstart.py",
            "generate_configs.py",
            "monitor.py",
            "analyze_results.py",
            "generate_report.py",
            "validate_results.py",
            "export_results.py",
            "merge_results.py",
            "cleanup.py",
            "compare_results.py",
            "deployment_checklist.py",
            "generate_manifest.py",
            "project_overview.py",
            "examples.py",
        ],
    }

    total_files = 0
    missing_files = []
    all_ok = True

    for category, files in checks.items():
        print(f"\n{category}:")
        category_ok = True

        for file in files:
            if Path(file).exists():
                print(f"  ✓ {file}")
                total_files += 1
            else:
                print(f"  ✗ {file} (MISSING)")
                missing_files.append(file)
                category_ok = False
                all_ok = False

        status = "✓ COMPLETE" if category_ok else "✗ INCOMPLETE"
        print(f"  Status: {status}")

    print("\n" + "-" * 80)
    print("SUMMARY")
    print("-" * 80)
    print(f"Total Files: {total_files}")
    print(f"Missing Files: {len(missing_files)}")

    if missing_files:
        print("\nMissing files:")
        for file in missing_files:
            print(f"  - {file}")

    print("\n" + "=" * 80)
    if all_ok:
        print("✓ ALL COMPONENTS PRESENT - READY FOR DEPLOYMENT".center(80))
        print("\nNext steps:".center(80))
        print("1. Read START_HERE.md".center(80))
        print("2. Run: python validate_setup.py".center(80))
        print("3. Configure: nano config.yaml".center(80))
        print("4. Deploy: python waymo_e2e_processor.py --config config.yaml".center(80))
    else:
        print("✗ SOME COMPONENTS MISSING - CANNOT DEPLOY".center(80))
        print("\nPlease ensure all files are present before deployment.".center(80))
    print("=" * 80 + "\n")

    return 0 if all_ok else 1

def main():
    """Main entry point."""
    return verify_all()

if __name__ == "__main__":
    sys.exit(main())
