#!/usr/bin/env python3
"""
Compare results from different pipeline runs.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

def load_results(results_dir: str) -> Dict[str, Dict[str, Any]]:
    """Load all result JSON files into a dictionary."""
    results = {}
    results_path = Path(results_dir)

    if not results_path.exists():
        print(f"Results directory not found: {results_dir}")
        return results

    for json_file in sorted(results_path.glob("*.json")):
        try:
            with open(json_file, 'r') as f:
                result = json.load(f)
                frame_name = result.get("metadata", {}).get("frame_name", json_file.stem)
                results[frame_name] = result
        except Exception as e:
            print(f"Warning: Failed to load {json_file}: {e}")

    return results

def compare_results(results1: Dict, results2: Dict) -> Dict[str, Any]:
    """Compare two sets of results."""
    comparison = {
        "total_frames_run1": len(results1),
        "total_frames_run2": len(results2),
        "common_frames": 0,
        "only_in_run1": 0,
        "only_in_run2": 0,
        "differences": [],
    }

    frames1 = set(results1.keys())
    frames2 = set(results2.keys())

    common_frames = frames1 & frames2
    only_in_run1 = frames1 - frames2
    only_in_run2 = frames2 - frames1

    comparison["common_frames"] = len(common_frames)
    comparison["only_in_run1"] = len(only_in_run1)
    comparison["only_in_run2"] = len(only_in_run2)

    # Compare common frames
    for frame_name in sorted(common_frames):
        result1 = results1[frame_name]
        result2 = results2[frame_name]

        # Compare VLM responses
        vlm1 = result1.get("vlm_response", {})
        vlm2 = result2.get("vlm_response", {})

        if vlm1 != vlm2:
            diff = {
                "frame": frame_name,
                "differences": [],
            }

            # Compare critical objects
            if vlm1.get("critical_objects") != vlm2.get("critical_objects"):
                diff["differences"].append("critical_objects")

            # Compare explanation
            if vlm1.get("explanation") != vlm2.get("explanation"):
                diff["differences"].append("explanation")

            # Compare meta_behaviour
            if vlm1.get("meta_behaviour") != vlm2.get("meta_behaviour"):
                diff["differences"].append("meta_behaviour")

            if diff["differences"]:
                comparison["differences"].append(diff)

    return comparison

def print_comparison_report(comparison: Dict[str, Any]):
    """Print comparison report."""
    print("\n" + "=" * 70)
    print("RESULTS COMPARISON REPORT")
    print("=" * 70)

    print(f"\nRun 1 frames: {comparison['total_frames_run1']}")
    print(f"Run 2 frames: {comparison['total_frames_run2']}")
    print(f"Common frames: {comparison['common_frames']}")
    print(f"Only in Run 1: {comparison['only_in_run1']}")
    print(f"Only in Run 2: {comparison['only_in_run2']}")

    if comparison["differences"]:
        print(f"\n" + "-" * 70)
        print(f"DIFFERENCES FOUND: {len(comparison['differences'])} frames")
        print("-" * 70)

        for diff in comparison["differences"][:10]:
            print(f"\nFrame: {diff['frame']}")
            print(f"  Differences: {', '.join(diff['differences'])}")

        if len(comparison["differences"]) > 10:
            print(f"\n... and {len(comparison['differences']) - 10} more frames with differences")
    else:
        print("\n✓ No differences found in common frames")

    print("\n" + "=" * 70 + "\n")

def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python compare_results.py <results_dir1> <results_dir2>")
        print("\nExample:")
        print("  python compare_results.py ./output1/results ./output2/results")
        return 1

    results_dir1 = sys.argv[1]
    results_dir2 = sys.argv[2]

    print(f"Loading results from: {results_dir1}")
    results1 = load_results(results_dir1)
    print(f"Loaded {len(results1)} results")

    print(f"\nLoading results from: {results_dir2}")
    results2 = load_results(results_dir2)
    print(f"Loaded {len(results2)} results")

    if not results1 or not results2:
        print("No results to compare")
        return 1

    print("\nComparing results...")
    comparison = compare_results(results1, results2)
    print_comparison_report(comparison)

    return 0

if __name__ == "__main__":
    sys.exit(main())
