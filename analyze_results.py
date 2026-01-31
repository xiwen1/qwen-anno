#!/usr/bin/env python3
"""
Script to analyze and summarize processing results.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

def load_results(results_dir: str) -> List[Dict[str, Any]]:
    """Load all result JSON files."""
    results = []
    results_path = Path(results_dir)

    if not results_path.exists():
        print(f"Results directory not found: {results_dir}")
        return results

    for json_file in results_path.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                result = json.load(f)
                results.append(result)
        except Exception as e:
            print(f"Failed to load {json_file}: {e}")

    return results

def analyze_critical_objects(results: List[Dict]) -> Dict[str, int]:
    """Analyze critical objects distribution."""
    object_counts = defaultdict(int)
    total_frames = len(results)

    for result in results:
        critical_objects = result.get("vlm_response", {}).get("critical_objects", {})
        for obj_class, value in critical_objects.items():
            if value == "yes":
                object_counts[obj_class] += 1

    # Convert to percentages
    object_percentages = {
        obj: (count / total_frames * 100) if total_frames > 0 else 0
        for obj, count in object_counts.items()
    }

    return object_percentages

def analyze_behaviors(results: List[Dict]) -> Dict[str, Dict[str, int]]:
    """Analyze speed and command distributions."""
    speeds = defaultdict(int)
    commands = defaultdict(int)

    for result in results:
        meta_behaviour = result.get("vlm_response", {}).get("meta_behaviour", {})
        speed = meta_behaviour.get("speed", "unknown")
        command = meta_behaviour.get("command", "unknown")

        speeds[speed] += 1
        commands[command] += 1

    return {
        "speeds": dict(speeds),
        "commands": dict(commands)
    }

def analyze_intents(results: List[Dict]) -> Dict[str, int]:
    """Analyze ego intent distribution."""
    intents = defaultdict(int)

    for result in results:
        ego_status = result.get("input_data", {}).get("ego_status", {})
        intent = ego_status.get("intent", "unknown")
        intents[intent] += 1

    return dict(intents)

def print_report(results: List[Dict]):
    """Print analysis report."""
    if not results:
        print("No results to analyze")
        return

    total_frames = len(results)

    print("\n" + "=" * 70)
    print("WAYMO E2E PROCESSING RESULTS ANALYSIS")
    print("=" * 70)

    print(f"\nTotal frames processed: {total_frames}")

    # Critical objects analysis
    print("\n" + "-" * 70)
    print("CRITICAL OBJECTS DISTRIBUTION")
    print("-" * 70)

    object_percentages = analyze_critical_objects(results)
    for obj_class in sorted(object_percentages.keys()):
        percentage = object_percentages[obj_class]
        bar_length = int(percentage / 2)
        bar = "█" * bar_length
        print(f"{obj_class:25} {percentage:6.1f}% {bar}")

    # Behavior analysis
    print("\n" + "-" * 70)
    print("BEHAVIOR DISTRIBUTION")
    print("-" * 70)

    behaviors = analyze_behaviors(results)

    print("\nSpeed:")
    for speed, count in sorted(behaviors["speeds"].items()):
        percentage = (count / total_frames * 100) if total_frames > 0 else 0
        print(f"  {speed:15} {count:5} ({percentage:5.1f}%)")

    print("\nCommand:")
    for command, count in sorted(behaviors["commands"].items()):
        percentage = (count / total_frames * 100) if total_frames > 0 else 0
        print(f"  {command:20} {count:5} ({percentage:5.1f}%)")

    # Intent analysis
    print("\n" + "-" * 70)
    print("EGO INTENT DISTRIBUTION")
    print("-" * 70)

    intents = analyze_intents(results)
    for intent, count in sorted(intents.items()):
        percentage = (count / total_frames * 100) if total_frames > 0 else 0
        print(f"  {intent:15} {count:5} ({percentage:5.1f}%)")

    # Speed statistics
    print("\n" + "-" * 70)
    print("EGO SPEED STATISTICS")
    print("-" * 70)

    speeds = []
    for result in results:
        ego_status = result.get("input_data", {}).get("ego_status", {})
        speed = ego_status.get("speed", 0)
        speeds.append(speed)

    if speeds:
        import statistics
        print(f"  Mean speed:     {statistics.mean(speeds):.2f} m/s")
        print(f"  Median speed:   {statistics.median(speeds):.2f} m/s")
        print(f"  Min speed:      {min(speeds):.2f} m/s")
        print(f"  Max speed:      {max(speeds):.2f} m/s")
        print(f"  Std deviation:  {statistics.stdev(speeds):.2f} m/s" if len(speeds) > 1 else "")

    print("\n" + "=" * 70 + "\n")

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        results_dir = "./output/results"
    else:
        results_dir = sys.argv[1]

    print(f"Loading results from: {results_dir}")
    results = load_results(results_dir)

    if results:
        print(f"Loaded {len(results)} results")
        print_report(results)
    else:
        print("No results found")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
