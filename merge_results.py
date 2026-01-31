#!/usr/bin/env python3
"""
Merge results from multiple pipeline runs.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

def load_results(results_dir: str) -> List[Dict[str, Any]]:
    """Load all result JSON files from a directory."""
    results = []
    results_path = Path(results_dir)

    if not results_path.exists():
        print(f"Results directory not found: {results_dir}")
        return results

    for json_file in sorted(results_path.glob("*.json")):
        try:
            with open(json_file, 'r') as f:
                result = json.load(f)
                results.append(result)
        except Exception as e:
            print(f"Warning: Failed to load {json_file}: {e}")

    return results

def merge_results(results_dirs: List[str], output_dir: str):
    """Merge results from multiple directories."""
    print(f"Merging results from {len(results_dirs)} directories...\n")

    all_results = []
    total_frames = 0

    for results_dir in results_dirs:
        print(f"Loading from: {results_dir}")
        results = load_results(results_dir)
        all_results.extend(results)
        total_frames += len(results)
        print(f"  Loaded {len(results)} results")

    print(f"\nTotal results loaded: {total_frames}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save merged results
    print(f"\nSaving merged results to: {output_dir}")

    for i, result in enumerate(all_results):
        frame_name = result.get("metadata", {}).get("frame_name", f"frame_{i:06d}")
        output_file = output_path / f"{frame_name}.json"

        try:
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save {output_file}: {e}")

    print(f"✓ Saved {len(all_results)} merged results")

    # Generate merged summary
    print("\nGenerating merged summary...")

    summary = {
        "total_frames": total_frames,
        "source_directories": results_dirs,
        "merged_output_directory": output_dir,
    }

    summary_file = output_path / "merged_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"✓ Saved summary to {summary_file}")

def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python merge_results.py <output_dir> <results_dir1> [results_dir2] ...")
        print("\nExample:")
        print("  python merge_results.py ./merged_output ./output1/results ./output2/results")
        return 1

    output_dir = sys.argv[1]
    results_dirs = sys.argv[2:]

    try:
        merge_results(results_dirs, output_dir)
        print("\n✓ Merge completed successfully!")
        return 0
    except Exception as e:
        print(f"\n✗ Merge failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
