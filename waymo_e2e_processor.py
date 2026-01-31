#!/usr/bin/env python3
"""
Waymo E2E Dataset Processing Pipeline

Extracts data from Waymo end-to-end driving dataset at 1Hz frequency,
processes images and trajectories, and generates Chain-of-Thought (CoT)
annotations using a Vision Language Model (VLM).
"""

import argparse
import logging
import time
import sys
from pathlib import Path
from typing import Optional

from src.config import WaymoE2EConfig
from src.dataset_loader import WaymoE2EDatasetLoader
from src.image_processor import ImageProcessor
from src.trajectory_extractor import TrajectoryExtractor
from src.prompt_builder import PromptBuilder
from src.vlm_client import VLMClient
from src.output_handler import OutputHandler
from src.utils import setup_logging, format_time, estimate_remaining_time

logger = logging.getLogger(__name__)


class WaymoE2EPipeline:
    """Main pipeline for processing Waymo E2E dataset."""

    def __init__(self, config: WaymoE2EConfig):
        """
        Initialize pipeline.

        Args:
            config: Configuration object
        """
        self.config = config

        # Initialize components
        self.dataset_loader = WaymoE2EDatasetLoader(
            config.dataset.path,
            config.dataset.sampling_frequency_hz
        )
        self.image_processor = ImageProcessor(
            config.image_processing.target_height,
            config.image_processing.input_mode,
            config.image_processing.jpeg_quality
        )
        self.trajectory_extractor = TrajectoryExtractor(
            config.trajectory.past_duration_seconds,
            config.trajectory.past_frequency_hz,
            config.trajectory.future_duration_seconds,
            config.trajectory.future_frequency_hz
        )
        self.prompt_builder = PromptBuilder(config.vlm_api.prompt_template_path)
        self.vlm_client = VLMClient(
            config.get_api_key(),
            config.vlm_api.model_name,
            config.vlm_api.max_retries,
            config.vlm_api.retry_delay_seconds,
            config.vlm_api.timeout_seconds
        )
        self.output_handler = OutputHandler(
            config.output.output_dir,
            config.output.results_subdir,
            config.output.checkpoint_file
        )

        # Statistics
        self.processed_frames = 0
        self.skipped_frames = 0
        self.failed_frames = 0
        self.start_time = None

    def process_frame(self, frame, frame_index: int) -> bool:
        """
        Process a single frame.

        Args:
            frame: E2EDFrame object
            frame_index: Frame index for logging

        Returns:
            True if successful, False otherwise
        """
        try:
            frame_name = frame.frame.context.name
            timestamp_micros = frame.frame.timestamp_micros

            logger.info(f"Processing frame {frame_index}: {frame_name}")

            # Extract images
            images_base64 = self.image_processor.process_images(frame)
            if not images_base64:
                logger.warning(f"Failed to extract images for frame {frame_name}")
                self.skipped_frames += 1
                return False

            # Extract trajectories and ego status
            try:
                trajectory_data = self.trajectory_extractor.extract_all(frame)
            except ValueError as e:
                logger.warning(f"Skipping frame {frame_name} (frame_index {frame_index}): {e}")
                self.skipped_frames += 1
                return False

            # Build prompt
            user_prompt = self.prompt_builder.build_prompt(trajectory_data)

            # Call VLM API
            vlm_response_text = self.vlm_client.call_vlm(
                system_prompt=self.config.vlm_api.system_prompt,
                user_prompt=user_prompt,
                video_frames_base64=images_base64
            )

            if not vlm_response_text:
                logger.warning(f"VLM API call failed for frame {frame_name}")
                self.failed_frames += 1
                return False

            # Parse VLM response
            vlm_response = self.vlm_client.parse_response(vlm_response_text)
            if not vlm_response:
                logger.warning(f"Failed to parse VLM response for frame {frame_name}")
                self.failed_frames += 1
                return False

            # Prepare metadata
            metadata = {
                "timestamp_micros": timestamp_micros,
                "model_name": self.config.vlm_api.model_name,
                "image_mode": self.config.image_processing.input_mode,
            }

            # Prepare input data
            input_data = {
                "past_trajectory": trajectory_data["past_trajectory"],
                "future_trajectory": trajectory_data["future_trajectory"],
                "ego_status": trajectory_data["ego_status"],
                "images_included": ["concatenated"] if self.config.image_processing.input_mode == "concatenated" else ["front_left", "front", "front_right"],
            }

            # Save result
            self.output_handler.save_result(
                frame_name,
                metadata,
                input_data,
                vlm_response
            )

            self.processed_frames += 1
            return True

        except Exception as e:
            logger.error(f"Error processing frame {frame_index}: {e}", exc_info=True)
            self.failed_frames += 1
            return False

    def run(self, resume: bool = False):
        """
        Run the pipeline.

        Args:
            resume: Whether to resume from checkpoint
        """
        logger.info("Starting Waymo E2E dataset processing pipeline")
        logger.info(f"Configuration: {self.config}")

        self.start_time = time.time()

        # Load checkpoint if resuming
        processed_frames_set = set()
        if resume:
            processed_frames_set = self.output_handler.load_checkpoint()
            logger.info(f"Resuming from checkpoint with {len(processed_frames_set)} processed frames")

        # Get frame iterator
        frame_iterator = self.dataset_loader.get_frame_iterator(
            self.config.processing.max_frames
        )

        frame_index = 0
        try:
            for frame in frame_iterator:
                frame_name = frame.frame.context.name

                # Skip if already processed
                if resume and frame_name in processed_frames_set:
                    logger.debug(f"Skipping already processed frame: {frame_name}")
                    frame_index += 1
                    continue

                # Process frame
                success = self.process_frame(frame, frame_index)

                if success:
                    processed_frames_set.add(frame_name)

                # Save checkpoint periodically
                if (frame_index + 1) % self.config.processing.checkpoint_interval == 0:
                    self.output_handler.save_checkpoint(processed_frames_set)
                    elapsed = time.time() - self.start_time
                    remaining = estimate_remaining_time(
                        self.processed_frames,
                        self.processed_frames + self.skipped_frames + self.failed_frames,
                        elapsed
                    )
                    logger.info(
                        f"Checkpoint saved. Processed: {self.processed_frames}, "
                        f"Skipped: {self.skipped_frames}, Failed: {self.failed_frames}, "
                        f"Elapsed: {format_time(elapsed)}, Remaining: {remaining}"
                    )

                frame_index += 1

        except KeyboardInterrupt:
            logger.info("Pipeline interrupted by user")
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
        finally:
            # Save final checkpoint
            self.output_handler.save_checkpoint(processed_frames_set)

            # Generate summary
            total_frames = self.processed_frames + self.skipped_frames + self.failed_frames
            summary = self.output_handler.generate_summary(
                total_frames,
                self.processed_frames,
                self.skipped_frames,
                self.failed_frames
            )

            elapsed = time.time() - self.start_time
            logger.info(f"Pipeline completed in {format_time(elapsed)}")
            logger.info(f"Summary: {summary}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Waymo E2E Dataset Processing Pipeline"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        help="Override dataset path from config"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Override output directory from config"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        help="Override model name from config"
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        help="Maximum number of frames to process"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = WaymoE2EConfig.from_yaml(args.config)
    except FileNotFoundError:
        print(f"Configuration file not found: {args.config}")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Override configuration with command-line arguments
    if args.dataset_path:
        config.dataset.path = args.dataset_path
    if args.output_dir:
        config.output.output_dir = args.output_dir
    if args.model_name:
        config.vlm_api.model_name = args.model_name
    if args.max_frames:
        config.processing.max_frames = args.max_frames

    # Setup logging
    log_file = Path(config.output.output_dir) / config.output.log_file
    setup_logging(
        str(log_file),
        args.log_level,
        config.logging.console_output,
        config.logging.file_output
    )

    # Validate configuration
    try:
        config.validate()
        config.setup_output_dirs()
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)

    # Run pipeline
    pipeline = WaymoE2EPipeline(config)
    pipeline.run(resume=args.resume)


if __name__ == "__main__":
    main()
