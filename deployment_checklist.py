#!/usr/bin/env python3
"""
Pre-deployment checklist and verification script.
"""

import os
import sys
import json
from pathlib import Path

def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(text.center(70))
    print("=" * 70 + "\n")

def print_section(text):
    """Print formatted section."""
    print("\n" + "-" * 70)
    print(text)
    print("-" * 70)

def check_files():
    """Check all required files exist."""
    print_section("FILE VERIFICATION")

    required_files = [
        "waymo_e2e_processor.py",
        "config.yaml",
        "requirements.txt",
        "README.md",
        "QUICKSTART.md",
        "DEPLOYMENT.md",
        "FILE_INDEX.md",
        "PROJECT_COMPLETION_REPORT.md",
        "TROUBLESHOOTING.md",
        "src/config.py",
        "src/dataset_loader.py",
        "src/image_processor.py",
        "src/trajectory_extractor.py",
        "src/prompt_builder.py",
        "src/vlm_client.py",
        "src/output_handler.py",
        "src/utils.py",
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
        "examples.py",
    ]

    missing = []
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} (MISSING)")
            missing.append(file)

    return len(missing) == 0, missing

def check_configuration():
    """Check configuration file."""
    print_section("CONFIGURATION VERIFICATION")

    try:
        import yaml
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)

        required_sections = ["dataset", "image_processing", "vlm_api", "output"]
        all_ok = True

        for section in required_sections:
            if section in config:
                print(f"✓ {section} section found")
            else:
                print(f"✗ {section} section missing")
                all_ok = False

        # Check dataset path
        dataset_path = config.get("dataset", {}).get("path")
        if dataset_path and dataset_path != "/path/to/waymo/dataset/training.tfrecord*":
            print(f"✓ Dataset path configured: {dataset_path}")
        else:
            print(f"⚠ Dataset path not configured or using placeholder")

        return all_ok
    except Exception as e:
        print(f"✗ Configuration check failed: {e}")
        return False

def check_environment():
    """Check environment setup."""
    print_section("ENVIRONMENT VERIFICATION")

    api_key = os.getenv("ONE_API_KEY_KEWEI")
    if api_key:
        print(f"✓ API key set (ONE_API_KEY_KEWEI)")
        return True
    else:
        print(f"✗ API key not set (ONE_API_KEY_KEWEI)")
        print(f"  Set with: export ONE_API_KEY_KEWEI='your_key'")
        return False

def check_dependencies():
    """Check Python dependencies."""
    print_section("DEPENDENCY VERIFICATION")

    dependencies = [
        ("tensorflow", "TensorFlow"),
        ("cv2", "OpenCV"),
        ("numpy", "NumPy"),
        ("yaml", "PyYAML"),
        ("openai", "OpenAI"),
    ]

    all_ok = True
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} (not installed)")
            all_ok = False

    return all_ok

def check_waymo_dataset():
    """Check Waymo dataset SDK."""
    print_section("WAYMO DATASET SDK VERIFICATION")

    try:
        from waymo_open_dataset.protos import end_to_end_driving_data_pb2
        print("✓ Waymo E2E dataset proto available")
        return True
    except ImportError as e:
        print(f"✗ Waymo dataset not available: {e}")
        return False

def check_output_directory():
    """Check output directory."""
    print_section("OUTPUT DIRECTORY VERIFICATION")

    output_dir = Path("./output")
    if output_dir.exists():
        print(f"✓ Output directory exists: {output_dir}")
        results_dir = output_dir / "results"
        if results_dir.exists():
            file_count = len(list(results_dir.glob("*.json")))
            print(f"  Results files: {file_count}")
        return True
    else:
        print(f"⚠ Output directory does not exist (will be created at runtime)")
        return True

def generate_checklist():
    """Generate deployment checklist."""
    print_header("PRE-DEPLOYMENT CHECKLIST")

    checklist = [
        ("Files", check_files),
        ("Configuration", check_configuration),
        ("Environment", check_environment),
        ("Dependencies", check_dependencies),
        ("Waymo Dataset SDK", check_waymo_dataset),
        ("Output Directory", check_output_directory),
    ]

    results = {}
    for name, check_func in checklist:
        try:
            result = check_func()
            if isinstance(result, tuple):
                results[name] = result[0]
            else:
                results[name] = result
        except Exception as e:
            print(f"\n✗ {name} check failed: {e}")
            results[name] = False

    # Summary
    print_section("DEPLOYMENT READINESS SUMMARY")

    all_ok = all(results.values())

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:30} {status}")

    print("\n" + "=" * 70)

    if all_ok:
        print("✓ READY FOR DEPLOYMENT".center(70))
        print("\nNext steps:".center(70))
        print("1. Copy files to remote server".center(70))
        print("2. Install dependencies: pip install -r requirements.txt".center(70))
        print("3. Configure dataset path in config.yaml".center(70))
        print("4. Run: python waymo_e2e_processor.py --config config.yaml".center(70))
    else:
        print("✗ NOT READY FOR DEPLOYMENT".center(70))
        print("\nPlease fix the issues above before deploying.".center(70))

    print("=" * 70 + "\n")

    return 0 if all_ok else 1

def main():
    """Main entry point."""
    return generate_checklist()

if __name__ == "__main__":
    sys.exit(main())
