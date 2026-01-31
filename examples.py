#!/usr/bin/env python3
"""
Example script showing how to use the pipeline programmatically.
"""

from src.config import WaymoE2EConfig
from src.dataset_loader import WaymoE2EDatasetLoader
from src.image_processor import ImageProcessor
from src.trajectory_extractor import TrajectoryExtractor
from src.prompt_builder import PromptBuilder
from src.vlm_client import VLMClient
from src.output_handler import OutputHandler
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """Example: Basic pipeline usage."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Pipeline Usage")
    print("=" * 60)

    # Load configuration
    config = WaymoE2EConfig.from_yaml("config.yaml")
    config.validate()

    # Initialize components
    dataset_loader = WaymoE2EDatasetLoader(
        config.dataset.path,
        config.dataset.sampling_frequency_hz
    )

    image_processor = ImageProcessor(
        config.image_processing.target_height,
        config.image_processing.input_mode
    )

    trajectory_extractor = TrajectoryExtractor()

    # Get first frame
    frame_iterator = dataset_loader.get_frame_iterator(max_frames=1)
    for frame in frame_iterator:
        print(f"Frame name: {frame.frame.context.name}")
        print(f"Timestamp: {frame.frame.timestamp_micros}")

        # Extract images
        images = image_processor.process_images(frame)
        print(f"Images extracted: {len(images) if images else 0}")

        # Extract trajectories
        trajectories = trajectory_extractor.extract_all(frame)
        print(f"Past trajectory points: {len(trajectories['past_trajectory'])}")
        print(f"Future trajectory points: {len(trajectories['future_trajectory'])}")
        print(f"Ego status: {trajectories['ego_status']}")


def example_image_modes():
    """Example: Different image processing modes."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Image Processing Modes")
    print("=" * 60)

    config = WaymoE2EConfig.from_yaml("config.yaml")
    dataset_loader = WaymoE2EDatasetLoader(config.dataset.path, 1)

    # Get first frame
    frame_iterator = dataset_loader.get_frame_iterator(max_frames=1)
    for frame in frame_iterator:
        # Mode 1: Separate images
        print("\nMode 1: Separate Images")
        processor_separate = ImageProcessor(512, "separate")
        images_separate = processor_separate.process_images(frame)
        if images_separate:
            print(f"  Number of images: {len(images_separate)}")
            print(f"  Image 1 size: {len(images_separate[0])} bytes (base64)")

        # Mode 2: Concatenated image
        print("\nMode 2: Concatenated Image")
        processor_concat = ImageProcessor(512, "concatenated")
        images_concat = processor_concat.process_images(frame)
        if images_concat:
            print(f"  Number of images: {len(images_concat)}")
            print(f"  Concatenated image size: {len(images_concat[0])} bytes (base64)")


def example_trajectory_extraction():
    """Example: Trajectory extraction and formatting."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Trajectory Extraction")
    print("=" * 60)

    config = WaymoE2EConfig.from_yaml("config.yaml")
    dataset_loader = WaymoE2EDatasetLoader(config.dataset.path, 1)
    trajectory_extractor = TrajectoryExtractor()

    # Get first frame
    frame_iterator = dataset_loader.get_frame_iterator(max_frames=1)
    for frame in frame_iterator:
        trajectories = trajectory_extractor.extract_all(frame)

        print("\nPast Trajectory (first 3 points):")
        for i, point in enumerate(trajectories['past_trajectory'][:3]):
            print(f"  Point {i}: x={point[0]:.2f}, y={point[1]:.2f}, z={point[2]:.2f}")

        print("\nFuture Trajectory (first 3 points):")
        for i, point in enumerate(trajectories['future_trajectory'][:3]):
            print(f"  Point {i}: x={point[0]:.2f}, y={point[1]:.2f}, z={point[2]:.2f}")

        print("\nEgo Status:")
        ego_status = trajectories['ego_status']
        print(f"  Velocity: vx={ego_status['velocity'][0]:.2f}, vy={ego_status['velocity'][1]:.2f}")
        print(f"  Speed: {ego_status['speed']:.2f} m/s")
        print(f"  Intent: {ego_status['intent']}")


def example_prompt_building():
    """Example: Prompt building."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Prompt Building")
    print("=" * 60)

    config = WaymoE2EConfig.from_yaml("config.yaml")
    dataset_loader = WaymoE2EDatasetLoader(config.dataset.path, 1)
    trajectory_extractor = TrajectoryExtractor()
    prompt_builder = PromptBuilder(config.vlm_api.prompt_template_path)

    # Get first frame
    frame_iterator = dataset_loader.get_frame_iterator(max_frames=1)
    for frame in frame_iterator:
        trajectories = trajectory_extractor.extract_all(frame)
        prompt = prompt_builder.build_prompt(trajectories)

        print("\nGenerated Prompt (first 500 characters):")
        print(prompt[:500] + "...")


def example_output_handling():
    """Example: Output handling and checkpointing."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Output Handling")
    print("=" * 60)

    config = WaymoE2EConfig.from_yaml("config.yaml")
    output_handler = OutputHandler(
        config.output.output_dir,
        config.output.results_subdir
    )

    # Example result
    example_result = {
        "frame_name": "segment-example_timestamp-001",
        "timestamp_micros": 1234567890,
        "model_name": "gemini-2.5-flash",
    }

    example_input = {
        "past_trajectory": [[0, 0, 0], [1, 1, 0]],
        "future_trajectory": [[2, 2, 0], [3, 3, 0]],
        "ego_status": {"velocity": [1, 0], "speed": 1.0, "intent": "GO_STRAIGHT"},
    }

    example_vlm_response = {
        "critical_objects": {
            "nearby_vehicle": "yes",
            "pedestrian": "no",
            "cyclist": "no",
            "construction": "no",
            "traffic_element": "no",
            "weather_condition": "no",
            "road_hazard": "no",
            "emergency_vehicle": "no",
            "animal": "no",
            "special_vehicle": "no",
            "conflicting_vehicle": "no",
            "door_opening_vehicle": "no",
        },
        "explanation": "The ego vehicle follows a nearby vehicle at constant speed.",
        "meta_behaviour": {"speed": "keep", "command": "lane_follow"},
    }

    # Save result
    output_handler.save_result(
        example_result["frame_name"],
        example_result,
        example_input,
        example_vlm_response
    )

    print("✓ Result saved")

    # Save checkpoint
    processed_frames = {"segment-example_timestamp-001"}
    output_handler.save_checkpoint(processed_frames)
    print("✓ Checkpoint saved")

    # Load checkpoint
    loaded_frames = output_handler.load_checkpoint()
    print(f"✓ Checkpoint loaded: {len(loaded_frames)} frames")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("WAYMO E2E PIPELINE - USAGE EXAMPLES")
    print("=" * 60)

    try:
        example_basic_usage()
        example_image_modes()
        example_trajectory_extraction()
        example_prompt_building()
        example_output_handling()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
