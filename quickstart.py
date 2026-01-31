#!/usr/bin/env python3
"""
Quick start guide and setup wizard for the Waymo E2E pipeline.
"""

import os
import sys
from pathlib import Path
import yaml

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

def setup_wizard():
    """Interactive setup wizard."""
    print_header("WAYMO E2E PIPELINE - QUICK START WIZARD")

    print("This wizard will help you set up the pipeline for your first run.\n")

    # Step 1: Check environment
    print_section("Step 1: Environment Setup")
    print("Setting up environment variables...\n")

    api_key = os.getenv("ONE_API_KEY_KEWEI")
    if api_key:
        print(f"✓ API key already set")
    else:
        print("⚠ API key not set. You need to set it before running the pipeline.")
        print("\nTo set the API key, run:")
        print("  export ONE_API_KEY_KEWEI='your_api_key_here'")
        print("\nOr add to ~/.bashrc or ~/.zshrc for persistence:")
        print("  echo 'export ONE_API_KEY_KEWEI=\"your_api_key_here\"' >> ~/.bashrc")

    # Step 2: Validate setup
    print_section("Step 2: Validate Setup")
    print("Running validation checks...\n")

    os.system("python validate_setup.py")

    # Step 3: Configure dataset
    print_section("Step 3: Configure Dataset Path")
    print("You need to configure the dataset path in config.yaml\n")

    dataset_path = input("Enter the path to your Waymo dataset (e.g., /path/to/training.tfrecord*): ").strip()

    if dataset_path:
        # Load and update config
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)

        config['dataset']['path'] = dataset_path

        with open("config.yaml", 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        print(f"✓ Dataset path updated: {dataset_path}")
    else:
        print("⚠ Dataset path not set. Update config.yaml manually.")

    # Step 4: Choose image mode
    print_section("Step 4: Choose Image Processing Mode")
    print("The pipeline supports two image processing modes:\n")
    print("1. Separate: Three separate base64-encoded images")
    print("2. Concatenated: Single horizontally-concatenated image\n")

    mode = input("Choose mode (1 or 2, default: 1): ").strip() or "1"

    if mode == "2":
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)
        config['image_processing']['input_mode'] = "concatenated"
        with open("config.yaml", 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        print("✓ Image mode set to: concatenated")
    else:
        print("✓ Image mode set to: separate")

    # Step 5: Choose VLM model
    print_section("Step 5: Choose VLM Model")
    print("Available models:\n")
    print("1. gemini-2.5-flash (fast, recommended)")
    print("2. gpt-4o-20241120 (powerful)")
    print("3. gemini-3-pro (advanced)\n")

    model_choice = input("Choose model (1, 2, or 3, default: 1): ").strip() or "1"

    models = {
        "1": "gemini-2.5-flash",
        "2": "gpt-4o-20241120",
        "3": "gemini-3-pro"
    }

    model = models.get(model_choice, "gemini-2.5-flash")

    with open("config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    config['vlm_api']['model_name'] = model
    with open("config.yaml", 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f"✓ VLM model set to: {model}")

    # Step 6: Test with sample data
    print_section("Step 6: Test with Sample Data")
    print("It's recommended to test with a small dataset first.\n")

    test = input("Run test with 10 frames? (y/n, default: y): ").strip().lower() or "y"

    if test == "y":
        print("\nRunning test with 10 frames...")
        os.system("python waymo_e2e_processor.py --config config.yaml --max-frames 10 --log-level INFO")
    else:
        print("Skipping test run.")

    # Summary
    print_header("SETUP COMPLETE")
    print("Your pipeline is now configured and ready to use!\n")
    print("Next steps:\n")
    print("1. Review the configuration in config.yaml")
    print("2. Run the full pipeline:")
    print("   python waymo_e2e_processor.py --config config.yaml")
    print("\n3. Monitor progress:")
    print("   tail -f output/processing.log")
    print("\n4. Analyze results:")
    print("   python analyze_results.py output/results")
    print("\nFor more information, see README.md and DEPLOYMENT.md\n")

def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python quickstart.py")
        print("\nThis script provides an interactive setup wizard for the pipeline.")
        return 0

    try:
        setup_wizard()
        return 0
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        return 1
    except Exception as e:
        print(f"\nError during setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
