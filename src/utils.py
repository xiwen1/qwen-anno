"""Utility functions for the pipeline."""

import logging
import sys
from pathlib import Path


def setup_logging(log_file: str, level: str = "INFO", console_output: bool = True,
                  file_output: bool = True):
    """
    Setup logging configuration.

    Args:
        log_file: Path to log file
        level: Logging level
        console_output: Whether to output to console
        file_output: Whether to output to file
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level))

    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if file_output:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def validate_config(config) -> bool:
    """
    Validate configuration.

    Args:
        config: Configuration object

    Returns:
        True if valid, raises exception otherwise
    """
    return config.validate()


def format_time(seconds: float) -> str:
    """
    Format time in seconds to human-readable format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def estimate_remaining_time(processed: int, total: int, elapsed_seconds: float) -> str:
    """
    Estimate remaining processing time.

    Args:
        processed: Number of processed frames
        total: Total number of frames
        elapsed_seconds: Elapsed time in seconds

    Returns:
        Estimated remaining time as formatted string
    """
    if processed == 0:
        return "Unknown"

    avg_time_per_frame = elapsed_seconds / processed
    remaining_frames = total - processed
    remaining_seconds = avg_time_per_frame * remaining_frames

    return format_time(remaining_seconds)
