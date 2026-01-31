#!/usr/bin/env python3
"""
Monitor running pipeline processes and display statistics.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

def get_checkpoint_info(checkpoint_path: str) -> dict:
    """Get information from checkpoint file."""
    try:
        with open(checkpoint_path, 'r') as f:
            checkpoint = json.load(f)
        return checkpoint
    except:
        return None

def get_log_tail(log_path: str, lines: int = 20) -> list:
    """Get last N lines from log file."""
    try:
        with open(log_path, 'r') as f:
            all_lines = f.readlines()
        return all_lines[-lines:]
    except:
        return []

def get_output_stats(output_dir: str) -> dict:
    """Get statistics about output files."""
    results_dir = Path(output_dir) / "results"
    if not results_dir.exists():
        return {"total_files": 0, "total_size_mb": 0}

    files = list(results_dir.glob("*.json"))
    total_size = sum(f.stat().st_size for f in files)

    return {
        "total_files": len(files),
        "total_size_mb": total_size / (1024 * 1024),
    }

def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(text.center(70))
    print("=" * 70)

def print_section(text):
    """Print formatted section."""
    print("\n" + "-" * 70)
    print(text)
    print("-" * 70)

def monitor_pipeline(output_dir: str = "./output", interval: int = 5):
    """Monitor pipeline in real-time."""
    checkpoint_path = Path(output_dir) / "checkpoint.json"
    log_path = Path(output_dir) / "processing.log"

    print_header("WAYMO E2E PIPELINE MONITOR")
    print(f"\nMonitoring: {output_dir}")
    print(f"Update interval: {interval} seconds")
    print("Press Ctrl+C to exit\n")

    try:
        while True:
            # Clear screen (works on Unix-like systems)
            os.system("clear" if os.name == "posix" else "cls")

            print_header("WAYMO E2E PIPELINE MONITOR")
            print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            # Checkpoint info
            print_section("PROCESSING STATUS")
            checkpoint = get_checkpoint_info(str(checkpoint_path))

            if checkpoint:
                print(f"Total processed: {checkpoint.get('total_processed', 0)} frames")
                print(f"Last updated: {checkpoint.get('last_updated', 'N/A')}")
            else:
                print("No checkpoint found - processing may not have started")

            # Output stats
            print_section("OUTPUT STATISTICS")
            stats = get_output_stats(output_dir)
            print(f"Result files: {stats['total_files']}")
            print(f"Total size: {stats['total_size_mb']:.2f} MB")

            # Recent log entries
            print_section("RECENT LOG ENTRIES (last 10)")
            log_lines = get_log_tail(str(log_path), 10)
            if log_lines:
                for line in log_lines:
                    print(line.rstrip())
            else:
                print("No log entries found")

            print("\n" + "-" * 70)
            print(f"Refreshing in {interval} seconds... (Ctrl+C to exit)")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        return 0

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor Waymo E2E pipeline")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    parser.add_argument("--interval", type=int, default=5, help="Update interval in seconds")

    args = parser.parse_args()

    return monitor_pipeline(args.output_dir, args.interval)

if __name__ == "__main__":
    sys.exit(main())
