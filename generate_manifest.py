#!/usr/bin/env python3
"""
Generate project manifest and verify installation completeness.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def generate_manifest():
    """Generate project manifest."""
    manifest = {
        "project": "Waymo E2E Dataset Processing Pipeline",
        "version": "1.0.0",
        "generated": datetime.now().isoformat(),
        "components": {
            "core_pipeline": {
                "files": [
                    "waymo_e2e_processor.py",
                    "config.yaml",
                    "requirements.txt",
                ],
                "description": "Main pipeline and configuration"
            },
            "source_modules": {
                "files": [
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
                "description": "Core processing modules"
            },
            "documentation": {
                "files": [
                    "README.md",
                    "QUICKSTART.md",
                    "DEPLOYMENT.md",
                    "TROUBLESHOOTING.md",
                    "FILE_INDEX.md",
                    "PROJECT_COMPLETION_REPORT.md",
                ],
                "description": "Comprehensive documentation"
            },
            "helper_scripts": {
                "files": [
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
                    "examples.py",
                ],
                "description": "Utility scripts for common tasks"
            },
            "existing_files": {
                "files": [
                    "test.py",
                    "input_prompt.txt",
                    "waymo-open-dataset/",
                ],
                "description": "Existing files (not modified)"
            }
        },
        "statistics": {
            "total_files": 0,
            "total_lines_of_code": 0,
            "total_documentation_lines": 0,
        }
    }

    # Count files and lines
    total_files = 0
    total_code_lines = 0
    total_doc_lines = 0

    for component, data in manifest["components"].items():
        if component == "existing_files":
            continue
        for file in data["files"]:
            path = Path(file)
            if path.exists():
                total_files += 1
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                    if file.endswith('.md'):
                        total_doc_lines += lines
                    else:
                        total_code_lines += lines

    manifest["statistics"]["total_files"] = total_files
    manifest["statistics"]["total_lines_of_code"] = total_code_lines
    manifest["statistics"]["total_documentation_lines"] = total_doc_lines

    return manifest

def verify_installation():
    """Verify installation completeness."""
    manifest = generate_manifest()

    print("\n" + "=" * 70)
    print("PROJECT MANIFEST AND VERIFICATION")
    print("=" * 70)

    print(f"\nProject: {manifest['project']}")
    print(f"Version: {manifest['version']}")
    print(f"Generated: {manifest['generated']}")

    print("\n" + "-" * 70)
    print("COMPONENTS")
    print("-" * 70)

    all_ok = True
    for component, data in manifest["components"].items():
        print(f"\n{component.replace('_', ' ').title()}:")
        print(f"  Description: {data['description']}")
        print(f"  Files: {len(data['files'])}")

        missing = []
        for file in data["files"]:
            if not Path(file).exists():
                missing.append(file)
                all_ok = False

        if missing:
            print(f"  Status: ✗ INCOMPLETE")
            for file in missing:
                print(f"    - Missing: {file}")
        else:
            print(f"  Status: ✓ COMPLETE")

    print("\n" + "-" * 70)
    print("STATISTICS")
    print("-" * 70)

    stats = manifest["statistics"]
    print(f"\nTotal files: {stats['total_files']}")
    print(f"Total lines of code: {stats['total_lines_of_code']:,}")
    print(f"Total documentation lines: {stats['total_documentation_lines']:,}")
    print(f"Total lines: {stats['total_lines_of_code'] + stats['total_documentation_lines']:,}")

    print("\n" + "=" * 70)
    if all_ok:
        print("✓ INSTALLATION COMPLETE".center(70))
    else:
        print("✗ INSTALLATION INCOMPLETE".center(70))
    print("=" * 70 + "\n")

    # Save manifest
    manifest_file = "project_manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest saved to: {manifest_file}\n")

    return 0 if all_ok else 1

def main():
    """Main entry point."""
    return verify_installation()

if __name__ == "__main__":
    sys.exit(main())
