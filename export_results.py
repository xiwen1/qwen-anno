#!/usr/bin/env python3
"""
Export results to various formats for analysis and visualization.
"""

import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any

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

def export_to_csv(results: List[Dict], output_file: str):
    """Export results to CSV format."""
    if not results:
        print("No results to export")
        return

    # Prepare data
    rows = []
    for result in results:
        metadata = result.get("metadata", {})
        input_data = result.get("input_data", {})
        vlm_response = result.get("vlm_response", {})
        ego_status = input_data.get("ego_status", {})

        row = {
            "frame_name": metadata.get("frame_name", ""),
            "timestamp_micros": metadata.get("timestamp_micros", ""),
            "model_name": metadata.get("model_name", ""),
            "image_mode": metadata.get("image_mode", ""),
            "ego_velocity_x": ego_status.get("velocity", [0, 0])[0],
            "ego_velocity_y": ego_status.get("velocity", [0, 0])[1],
            "ego_speed": ego_status.get("speed", 0),
            "ego_intent": ego_status.get("intent", ""),
            "explanation": vlm_response.get("explanation", ""),
            "speed_command": vlm_response.get("meta_behaviour", {}).get("speed", ""),
            "driving_command": vlm_response.get("meta_behaviour", {}).get("command", ""),
        }

        # Add critical objects
        critical_objects = vlm_response.get("critical_objects", {})
        for obj_class, value in critical_objects.items():
            row[f"critical_{obj_class}"] = value

        rows.append(row)

    # Write CSV
    if rows:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        print(f"✓ Exported {len(rows)} results to {output_file}")

def export_to_jsonl(results: List[Dict], output_file: str):
    """Export results to JSONL format (one JSON per line)."""
    with open(output_file, 'w') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')

    print(f"✓ Exported {len(results)} results to {output_file}")

def export_summary_stats(results: List[Dict], output_file: str):
    """Export summary statistics."""
    from collections import defaultdict

    stats = {
        "total_frames": len(results),
        "critical_objects": defaultdict(int),
        "speeds": defaultdict(int),
        "commands": defaultdict(int),
        "intents": defaultdict(int),
    }

    for result in results:
        vlm_response = result.get("vlm_response", {})
        input_data = result.get("input_data", {})

        # Count critical objects
        critical_objects = vlm_response.get("critical_objects", {})
        for obj_class, value in critical_objects.items():
            if value == "yes":
                stats["critical_objects"][obj_class] += 1

        # Count behaviors
        meta_behaviour = vlm_response.get("meta_behaviour", {})
        speed = meta_behaviour.get("speed", "unknown")
        command = meta_behaviour.get("command", "unknown")
        stats["speeds"][speed] += 1
        stats["commands"][command] += 1

        # Count intents
        ego_status = input_data.get("ego_status", {})
        intent = ego_status.get("intent", "unknown")
        stats["intents"][intent] += 1

    # Convert defaultdicts to regular dicts
    stats["critical_objects"] = dict(stats["critical_objects"])
    stats["speeds"] = dict(stats["speeds"])
    stats["commands"] = dict(stats["commands"])
    stats["intents"] = dict(stats["intents"])

    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"✓ Exported summary statistics to {output_file}")

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Export pipeline results to various formats")
    parser.add_argument("results_dir", help="Results directory")
    parser.add_argument("--format", choices=["csv", "jsonl", "stats", "all"], default="all",
                        help="Export format")
    parser.add_argument("--output-dir", default="./exports", help="Output directory")

    args = parser.parse_args()

    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load results
    print(f"Loading results from: {args.results_dir}")
    results = load_results(args.results_dir)

    if not results:
        print("No results found")
        return 1

    print(f"Loaded {len(results)} results\n")

    # Export
    if args.format in ["csv", "all"]:
        export_to_csv(results, str(output_path / "results.csv"))

    if args.format in ["jsonl", "all"]:
        export_to_jsonl(results, str(output_path / "results.jsonl"))

    if args.format in ["stats", "all"]:
        export_summary_stats(results, str(output_path / "summary_stats.json"))

    print(f"\n✓ Export completed to: {args.output_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
