#!/usr/bin/env python3
"""
Generate comprehensive processing reports.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

def load_results(results_dir: str) -> List[Dict[str, Any]]:
    """Load all result JSON files."""
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

def generate_report(results: List[Dict], output_file: str):
    """Generate comprehensive report."""
    if not results:
        print("No results to report")
        return

    total_frames = len(results)

    # Analyze data
    critical_objects = defaultdict(int)
    speeds = defaultdict(int)
    commands = defaultdict(int)
    intents = defaultdict(int)
    ego_speeds = []

    for result in results:
        vlm_response = result.get("vlm_response", {})
        input_data = result.get("input_data", {})

        # Critical objects
        for obj_class, value in vlm_response.get("critical_objects", {}).items():
            if value == "yes":
                critical_objects[obj_class] += 1

        # Behaviors
        meta_behaviour = vlm_response.get("meta_behaviour", {})
        speeds[meta_behaviour.get("speed", "unknown")] += 1
        commands[meta_behaviour.get("command", "unknown")] += 1

        # Intent
        ego_status = input_data.get("ego_status", {})
        intents[ego_status.get("intent", "unknown")] += 1
        ego_speeds.append(ego_status.get("speed", 0))

    # Generate report
    report = []
    report.append("=" * 80)
    report.append("WAYMO E2E PROCESSING REPORT")
    report.append("=" * 80)
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Results directory: {results_dir}")
    report.append(f"\n{'SUMMARY':^80}")
    report.append("-" * 80)
    report.append(f"Total frames processed: {total_frames}")

    # Critical objects
    report.append(f"\n{'CRITICAL OBJECTS DISTRIBUTION':^80}")
    report.append("-" * 80)
    for obj_class in sorted(critical_objects.keys()):
        count = critical_objects[obj_class]
        percentage = (count / total_frames * 100) if total_frames > 0 else 0
        bar_length = int(percentage / 2)
        bar = "█" * bar_length
        report.append(f"{obj_class:30} {count:5} ({percentage:5.1f}%) {bar}")

    # Speeds
    report.append(f"\n{'SPEED DISTRIBUTION':^80}")
    report.append("-" * 80)
    for speed in sorted(speeds.keys()):
        count = speeds[speed]
        percentage = (count / total_frames * 100) if total_frames > 0 else 0
        report.append(f"{speed:30} {count:5} ({percentage:5.1f}%)")

    # Commands
    report.append(f"\n{'COMMAND DISTRIBUTION':^80}")
    report.append("-" * 80)
    for command in sorted(commands.keys()):
        count = commands[command]
        percentage = (count / total_frames * 100) if total_frames > 0 else 0
        report.append(f"{command:30} {count:5} ({percentage:5.1f}%)")

    # Intents
    report.append(f"\n{'EGO INTENT DISTRIBUTION':^80}")
    report.append("-" * 80)
    for intent in sorted(intents.keys()):
        count = intents[intent]
        percentage = (count / total_frames * 100) if total_frames > 0 else 0
        report.append(f"{intent:30} {count:5} ({percentage:5.1f}%)")

    # Speed statistics
    if ego_speeds:
        import statistics
        report.append(f"\n{'EGO SPEED STATISTICS':^80}")
        report.append("-" * 80)
        report.append(f"Mean speed:        {statistics.mean(ego_speeds):8.2f} m/s")
        report.append(f"Median speed:      {statistics.median(ego_speeds):8.2f} m/s")
        report.append(f"Min speed:         {min(ego_speeds):8.2f} m/s")
        report.append(f"Max speed:         {max(ego_speeds):8.2f} m/s")
        if len(ego_speeds) > 1:
            report.append(f"Std deviation:     {statistics.stdev(ego_speeds):8.2f} m/s")

    report.append("\n" + "=" * 80 + "\n")

    # Write report
    report_text = "\n".join(report)

    with open(output_file, 'w') as f:
        f.write(report_text)

    print(report_text)
    print(f"✓ Report saved to {output_file}")

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        results_dir = "./output/results"
    else:
        results_dir = sys.argv[1]

    output_file = "processing_report.txt"
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    print(f"Loading results from: {results_dir}")
    results = load_results(results_dir)

    if not results:
        print("No results found")
        return 1

    print(f"Loaded {len(results)} results\n")

    generate_report(results, output_file)
    return 0

if __name__ == "__main__":
    sys.exit(main())
