#!/usr/bin/env python3
"""
Validation script to check pipeline setup and configuration.
"""

import os
import sys
import json
from pathlib import Path

def check_environment():
    """Check environment setup."""
    print("=" * 60)
    print("ENVIRONMENT CHECK")
    print("=" * 60)

    # Check Python version
    print(f"Python version: {sys.version}")

    # Check API key
    api_key = os.getenv("ONE_API_KEY_KEWEI")
    if api_key:
        print(f"✓ API key found (ONE_API_KEY_KEWEI)")
    else:
        print("✗ API key not found (ONE_API_KEY_KEWEI)")
        return False

    return True

def check_dependencies():
    """Check required dependencies."""
    print("\n" + "=" * 60)
    print("DEPENDENCIES CHECK")
    print("=" * 60)

    dependencies = [
        "tensorflow",
        "cv2",
        "numpy",
        "yaml",
        "openai",
        "tqdm",
    ]

    all_ok = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep}")
        except ImportError:
            print(f"✗ {dep} (not installed)")
            all_ok = False

    return all_ok

def check_files():
    """Check required files."""
    print("\n" + "=" * 60)
    print("FILES CHECK")
    print("=" * 60)

    required_files = [
        "config.yaml",
        "input_prompt.txt",
        "test.py",
        "waymo_e2e_processor.py",
        "src/config.py",
        "src/dataset_loader.py",
        "src/image_processor.py",
        "src/trajectory_extractor.py",
        "src/prompt_builder.py",
        "src/vlm_client.py",
        "src/output_handler.py",
        "src/utils.py",
    ]

    all_ok = True
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} (not found)")
            all_ok = False

    return all_ok

def check_configuration():
    """Check configuration file."""
    print("\n" + "=" * 60)
    print("CONFIGURATION CHECK")
    print("=" * 60)

    try:
        import yaml
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)

        # Check required sections
        required_sections = ["dataset", "image_processing", "vlm_api", "output"]
        for section in required_sections:
            if section in config:
                print(f"✓ {section} section found")
            else:
                print(f"✗ {section} section missing")
                return False

        # Check dataset path
        dataset_path = config.get("dataset", {}).get("path")
        if dataset_path and dataset_path != "/path/to/waymo/dataset/training.tfrecord*":
            print(f"✓ Dataset path configured: {dataset_path}")
        else:
            print(f"⚠ Dataset path not configured or using default placeholder")

        return True
    except Exception as e:
        print(f"✗ Configuration check failed: {e}")
        return False

def check_waymo_dataset():
    """Check Waymo dataset availability."""
    print("\n" + "=" * 60)
    print("WAYMO DATASET CHECK")
    print("=" * 60)

    try:
        from waymo_open_dataset.protos import end_to_end_driving_data_pb2
        print("✓ Waymo E2E dataset proto available")
        return True
    except ImportError as e:
        print(f"✗ Waymo dataset not available: {e}")
        return False

def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("WAYMO E2E PIPELINE VALIDATION")
    print("=" * 60 + "\n")

    checks = [
        ("Environment", check_environment),
        ("Dependencies", check_dependencies),
        ("Files", check_files),
        ("Configuration", check_configuration),
        ("Waymo Dataset", check_waymo_dataset),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n✗ {name} check failed with error: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")

    all_ok = all(results.values())

    print("\n" + "=" * 60)
    if all_ok:
        print("✓ All checks passed! Pipeline is ready to use.")
        print("\nNext steps:")
        print("1. Configure dataset path in config.yaml")
        print("2. Run: python waymo_e2e_processor.py --config config.yaml")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Set API key: export ONE_API_KEY_KEWEI='your_key'")
        print("- Update config.yaml with correct dataset path")
    print("=" * 60 + "\n")

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
