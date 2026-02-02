#!/usr/bin/env python3
"""
Utility script to analyze and verify frame extraction order.
"""

import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any


def load_processing_order(json_file: Path) -> Dict[str, Any]:
    """Load processing order from JSON file."""
    with open(json_file, 'r') as f:
        return json.load(f)


def analyze_scene_distribution(data: Dict[str, Any]) -> Dict[str, int]:
    """Analyze scene distribution in processed frames."""
    scene_counts = Counter(
        item['scene_id'] for item in data['frame_metadata']
    )
    return dict(scene_counts)


def analyze_frame_id_patterns(data: Dict[str, Any]) -> Dict[str, List[int]]:
    """Analyze frame ID patterns within each scene."""
    scene_frames = defaultdict(list)
    for item in data['frame_metadata']:
        scene_id = item['scene_id']
        frame_id = int(item['frame_id'])
        scene_frames[scene_id].append(frame_id)
    return dict(scene_frames)


def check_ordering_consistency(json_file_1: Path, json_file_2: Path) -> bool:
    """Check if two processing order files are identical."""
    data1 = load_processing_order(json_file_1)
    data2 = load_processing_order(json_file_2)

    frames1 = data1['processing_order']
    frames2 = data2['processing_order']

    if len(frames1) != len(frames2):
        print(f"❌ Different number of frames: {len(frames1)} vs {len(frames2)}")
        return False

    mismatches = []
    for i, (f1, f2) in enumerate(zip(frames1, frames2)):
        if f1 != f2:
            mismatches.append((i, f1, f2))

    if mismatches:
        print(f"❌ Order mismatch at {len(mismatches)} positions:")
        for idx, f1, f2 in mismatches[:5]:  # Show first 5 mismatches
            print(f"   Position {idx}: {f1} vs {f2}")
        if len(mismatches) > 5:
            print(f"   ... and {len(mismatches) - 5} more")
        return False

    print("✅ Processing order is identical!")
    return True


def print_statistics(data: Dict[str, Any]):
    """Print statistics about the processing order."""
    metadata = data['frame_metadata']
    total_frames = len(metadata)

    print(f"\n📊 Processing Statistics")
    print(f"{'=' * 50}")
    print(f"Total frames processed: {total_frames}")
    print(f"Timestamp: {data['timestamp']}")

    # Scene distribution
    print(f"\n🎬 Scene Distribution")
    print(f"{'=' * 50}")
    scene_dist = analyze_scene_distribution(data)
    for scene_id, count in sorted(scene_dist.items(), key=lambda x: x[1], reverse=True):
        print(f"  {scene_id}: {count} frames")

    # Frame ID statistics
    print(f"\n📈 Frame ID Statistics per Scene")
    print(f"{'=' * 50}")
    frame_patterns = analyze_frame_id_patterns(data)
    for scene_id, frame_ids in sorted(frame_patterns.items())[:10]:
        frame_ids_sorted = sorted(frame_ids)
        print(f"  {scene_id}:")
        print(f"    Min frame ID: {min(frame_ids_sorted)}")
        print(f"    Max frame ID: {max(frame_ids_sorted)}")
        print(f"    Frame count: {len(frame_ids_sorted)}")
        if len(frame_ids_sorted) > 1:
            intervals = [frame_ids_sorted[i+1] - frame_ids_sorted[i]
                        for i in range(len(frame_ids_sorted)-1)]
            avg_interval = sum(intervals) / len(intervals)
            print(f"    Avg frame interval: {avg_interval:.1f}")

    if len(frame_patterns) > 10:
        print(f"  ... and {len(frame_patterns) - 10} more scenes")


def compare_two_runs(json_file_1: Path, json_file_2: Path):
    """Compare two processing runs."""
    print(f"\n🔍 Comparing two processing runs")
    print(f"{'=' * 50}")
    print(f"File 1: {json_file_1}")
    print(f"File 2: {json_file_2}")

    is_consistent = check_ordering_consistency(json_file_1, json_file_2)

    if is_consistent:
        print("\n✅ The processing order is reproducible and consistent!")
    else:
        print("\n⚠️  The processing order differs between runs.")
        print("   This may indicate non-deterministic behavior.")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze and verify frame extraction order"
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Path to processing_order.json file"
    )
    parser.add_argument(
        "--compare",
        type=Path,
        help="Compare with another processing_order.json file"
    )

    args = parser.parse_args()

    if not args.file.exists():
        print(f"❌ File not found: {args.file}")
        return

    data = load_processing_order(args.file)

    # Print statistics
    print_statistics(data)

    # Compare if requested
    if args.compare:
        if not args.compare.exists():
            print(f"\n❌ Comparison file not found: {args.compare}")
            return
        compare_two_runs(args.file, args.compare)


if __name__ == "__main__":
    main()
