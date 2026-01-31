#!/usr/bin/env python3
"""
Clean up and archive old results.
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta

def get_directory_size(path: Path) -> int:
    """Get total size of directory in bytes."""
    total = 0
    for entry in path.rglob('*'):
        if entry.is_file():
            total += entry.stat().st_size
    return total

def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def archive_results(output_dir: str, archive_name: str = None):
    """Archive results directory."""
    output_path = Path(output_dir)
    results_path = output_path / "results"

    if not results_path.exists():
        print("No results directory found")
        return False

    size = get_directory_size(results_path)
    print(f"Results directory size: {format_size(size)}")

    if archive_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"results_archive_{timestamp}.tar.gz"

    archive_path = output_path / archive_name

    print(f"Archiving to: {archive_path}")

    try:
        shutil.make_archive(
            str(archive_path.with_suffix('')),
            'gztar',
            results_path.parent,
            results_path.name
        )
        print(f"✓ Archive created: {archive_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to create archive: {e}")
        return False

def cleanup_results(output_dir: str, keep_results: bool = False):
    """Clean up results directory."""
    output_path = Path(output_dir)
    results_path = output_path / "results"

    if not results_path.exists():
        print("No results directory found")
        return False

    size = get_directory_size(results_path)
    print(f"Removing {format_size(size)} of results...")

    try:
        shutil.rmtree(results_path)
        print("✓ Results directory cleaned")

        # Keep checkpoint for resume
        if keep_results:
            results_path.mkdir(parents=True, exist_ok=True)
            print("✓ Empty results directory created for resume")

        return True
    except Exception as e:
        print(f"✗ Failed to clean results: {e}")
        return False

def cleanup_old_results(output_dir: str, days: int = 7):
    """Clean up results older than N days."""
    output_path = Path(output_dir)
    results_path = output_path / "results"

    if not results_path.exists():
        print("No results directory found")
        return

    cutoff_time = datetime.now() - timedelta(days=days)
    removed_count = 0
    removed_size = 0

    for json_file in results_path.glob("*.json"):
        file_time = datetime.fromtimestamp(json_file.stat().st_mtime)
        if file_time < cutoff_time:
            removed_size += json_file.stat().st_size
            json_file.unlink()
            removed_count += 1

    print(f"Removed {removed_count} files ({format_size(removed_size)})")

def print_cleanup_stats(output_dir: str):
    """Print cleanup statistics."""
    output_path = Path(output_dir)

    print("\n" + "=" * 70)
    print("CLEANUP STATISTICS")
    print("=" * 70 + "\n")

    # Results directory
    results_path = output_path / "results"
    if results_path.exists():
        size = get_directory_size(results_path)
        file_count = len(list(results_path.glob("*.json")))
        print(f"Results directory:")
        print(f"  Files: {file_count}")
        print(f"  Size: {format_size(size)}")

    # Checkpoint
    checkpoint_path = output_path / "checkpoint.json"
    if checkpoint_path.exists():
        with open(checkpoint_path, 'r') as f:
            checkpoint = json.load(f)
        print(f"\nCheckpoint:")
        print(f"  Processed frames: {checkpoint.get('total_processed', 0)}")
        print(f"  Last updated: {checkpoint.get('last_updated', 'N/A')}")

    # Log file
    log_path = output_path / "processing.log"
    if log_path.exists():
        size = log_path.stat().st_size
        print(f"\nLog file:")
        print(f"  Size: {format_size(size)}")

    print("\n" + "=" * 70 + "\n")

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Clean up and archive results")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    parser.add_argument("--archive", action="store_true", help="Archive results")
    parser.add_argument("--archive-name", help="Archive file name")
    parser.add_argument("--cleanup", action="store_true", help="Clean up results")
    parser.add_argument("--cleanup-old", type=int, help="Clean up results older than N days")
    parser.add_argument("--keep-checkpoint", action="store_true", help="Keep checkpoint for resume")
    parser.add_argument("--stats", action="store_true", help="Show cleanup statistics")

    args = parser.parse_args()

    if not any([args.archive, args.cleanup, args.cleanup_old, args.stats]):
        print_cleanup_stats(args.output_dir)
        return 0

    if args.stats:
        print_cleanup_stats(args.output_dir)

    if args.archive:
        archive_results(args.output_dir, args.archive_name)

    if args.cleanup:
        cleanup_results(args.output_dir, args.keep_checkpoint)

    if args.cleanup_old:
        cleanup_old_results(args.output_dir, args.cleanup_old)

    return 0

if __name__ == "__main__":
    sys.exit(main())
