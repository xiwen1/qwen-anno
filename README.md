# Waymo E2E Dataset Processing Pipeline

A comprehensive Python pipeline for extracting data from the Waymo end-to-end driving dataset at 1Hz frequency, processing images and trajectories, and generating Chain-of-Thought (CoT) annotations using Vision Language Models (VLM) following the Poutine paper approach.

## Overview

This pipeline processes Waymo E2E dataset frames to:
1. Extract 3 front-facing camera images (FRONT_LEFT, FRONT, FRONT_RIGHT)
2. Downsample images to height=512 maintaining aspect ratio
3. Extract past trajectory (4 seconds at 4Hz = 16 points)
4. Extract future trajectory (5 seconds at 4Hz = 20 points)
5. Extract ego vehicle status (velocity, speed, intent)
6. Call VLM API with formatted prompts to generate CoT annotations
7. Save structured JSON results with metadata

## Features

- **1Hz Sampling**: Automatically samples every 10th frame from 10Hz dataset
- **Dual Image Modes**:
  - Separate mode: Three separate base64-encoded images
  - Concatenated mode: Single horizontally-concatenated image
- **Robust Error Handling**: Graceful handling of corrupted frames and API failures
- **Checkpoint System**: Resume processing from any point
- **Retry Logic**: Exponential backoff for API calls
- **Progress Tracking**: Real-time progress with time estimates
- **Comprehensive Logging**: Detailed logs for debugging

## Project Structure

```
/root/qwen-anno/
├── waymo_e2e_processor.py          # Main entry point
├── config.yaml                      # Configuration file
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── input_prompt.txt                 # VLM prompt template
├── test.py                          # VLM API caller (existing)
│
├── src/                             # Source code modules
│   ├── __init__.py
│   ├── config.py                    # Configuration system
│   ├── dataset_loader.py            # Dataset loading and sampling
│   ├── image_processor.py           # Image extraction and processing
│   ├── trajectory_extractor.py      # Trajectory extraction
│   ├── prompt_builder.py            # Prompt formatting
│   ├── vlm_client.py                # VLM API client with retry logic
│   ├── output_handler.py            # Result saving and checkpointing
│   └── utils.py                     # Utility functions
│
├── output/                          # Output directory (created at runtime)
│   ├── results/                     # Individual frame results (JSON files)
│   ├── checkpoint.json              # Processing checkpoint
│   ├── processing.log               # Processing log
│   └── summary.json                 # Summary statistics
│
└── waymo-open-dataset/              # Waymo SDK (existing)
    └── ...
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export ONE_API_KEY_KEWEI="your_api_key_here"
```

Or set it in your shell profile for persistence.

## Configuration

Edit `config.yaml` to configure the pipeline:

```yaml
# Dataset path (required)
dataset:
  path: "/path/to/waymo/dataset/training.tfrecord*"
  sampling_frequency_hz: 1

# Image processing settings
image_processing:
  target_height: 512
  input_mode: "separate"  # or "concatenated"
  jpeg_quality: 90

# VLM API settings
vlm_api:
  model_name: "gemini-2.5-flash"  # or "gpt-4o-20241120"
  api_key_env_var: "ONE_API_KEY_KEWEI"
  max_retries: 3
  retry_delay_seconds: 2.0
  timeout_seconds: 60

# Processing settings
processing:
  checkpoint_interval: 10
  max_frames: null  # null = process all frames

# Output settings
output:
  output_dir: "./output"
```

## Usage

### Basic Usage

```bash
python waymo_e2e_processor.py --config config.yaml
```

### Override Configuration

```bash
python waymo_e2e_processor.py \
    --config config.yaml \
    --dataset-path /path/to/dataset \
    --output-dir ./output \
    --model-name gemini-2.5-flash \
    --max-frames 100
```

### Resume from Checkpoint

```bash
python waymo_e2e_processor.py --config config.yaml --resume
```

### Change Logging Level

```bash
python waymo_e2e_processor.py --config config.yaml --log-level DEBUG
```

### Command-Line Options

```
--config CONFIG              Path to configuration file (default: config.yaml)
--dataset-path PATH          Override dataset path
--output-dir DIR             Override output directory
--model-name MODEL           Override VLM model name
--max-frames N               Process only N frames
--resume                     Resume from checkpoint
--log-level LEVEL            Logging level (DEBUG, INFO, WARNING, ERROR)
```

## Image Processing Modes

### Mode 1: Separate Images

Three separate base64-encoded images are sent to the VLM:
- Each image is downsampled to height=512
- Images are sent as separate frames in the VLM API call
- Useful for models that handle multiple images natively

Configuration:
```yaml
image_processing:
  input_mode: "separate"
```

### Mode 2: Concatenated Image

Three images are concatenated horizontally (left-center-right) into one image:
- Each image is downsampled to height=512
- Images are concatenated along the width axis
- Single concatenated image is sent to VLM
- Useful for models that work better with single images

Configuration:
```yaml
image_processing:
  input_mode: "concatenated"
```

## Output Format

### Result JSON Structure

Each processed frame generates a JSON file in `output/results/`:

```json
{
    "metadata": {
        "frame_name": "segment-xxx_timestamp-xxx",
        "timestamp_micros": 1234567890,
        "processing_timestamp": "2026-01-31T12:00:00Z",
        "model_name": "gemini-2.5-flash",
        "image_mode": "separate"
    },
    "input_data": {
        "past_trajectory": [
            [0.0, 0.0, 0.0],
            [1.2, 0.1, 0.0],
            ...  // 16 points total
        ],
        "future_trajectory": [
            [1.5, 0.2, 0.0],
            [2.8, 0.3, 0.0],
            ...  // 20 points total
        ],
        "ego_status": {
            "velocity": [5.2, 0.1],
            "speed": 5.21,
            "intent": "GO_STRAIGHT"
        },
        "images_included": ["front_left", "front", "front_right"]
    },
    "vlm_response": {
        "critical_objects": {
            "nearby_vehicle": "yes",
            "pedestrian": "no",
            "cyclist": "no",
            "construction": "no",
            "traffic_element": "yes",
            "weather_condition": "no",
            "road_hazard": "no",
            "emergency_vehicle": "no",
            "animal": "no",
            "special_vehicle": "no",
            "conflicting_vehicle": "no",
            "door_opening_vehicle": "no"
        },
        "explanation": "The ego vehicle maintains steady speed while following nearby vehicles...",
        "meta_behaviour": {
            "speed": "keep",
            "command": "lane_follow"
        }
    }
}
```

### Checkpoint File

`output/checkpoint.json` tracks processed frames for resume capability:

```json
{
    "last_updated": "2026-01-31T12:00:00Z",
    "total_processed": 1523,
    "processed_frames": [
        "segment-xxx_timestamp-001",
        "segment-xxx_timestamp-002",
        ...
    ]
}
```

### Summary File

`output/summary.json` contains processing statistics:

```json
{
    "timestamp": "2026-01-31T12:00:00Z",
    "total_frames": 1523,
    "processed_frames": 1500,
    "skipped_frames": 20,
    "failed_frames": 3,
    "success_rate": 0.985
}
```

## Data Structures

### Trajectory Format

- **Past Trajectory**: 4 seconds at 4Hz = 16 points
  - Format: `[[x1, y1, z1], [x2, y2, z2], ..., [x16, y16, z16]]`
  - Coordinate system: +x=forward, +y=left, +z=up
  - Origin: middle of ego vehicle's rear axle

- **Future Trajectory**: 5 seconds at 4Hz = 20 points
  - Same format and coordinate system as past trajectory

### Ego Status

```python
{
    "velocity": [vel_x, vel_y],  # m/s
    "speed": 5.21,               # m/s (magnitude)
    "intent": "GO_STRAIGHT"      # UNKNOWN, GO_STRAIGHT, GO_LEFT, GO_RIGHT
}
```

### Intent Values

- `UNKNOWN` (0): Unknown intent
- `GO_STRAIGHT` (1): Continue straight
- `GO_LEFT` (2): Turn left
- `GO_RIGHT` (3): Turn right

## Error Handling

### Frame-Level Errors (Skip Frame)

The pipeline gracefully handles:
- Corrupted TFRecord data
- Missing camera images
- Invalid trajectory data
- VLM API failures (after retries)

Skipped frames are logged and tracked in statistics.

### Fatal Errors (Stop Processing)

Processing stops on:
- Configuration errors
- Authentication failures (invalid API key)
- Disk full errors
- Unrecoverable API errors

### Retry Logic

VLM API calls use exponential backoff:
- Initial delay: 2 seconds
- Max retries: 3
- Backoff multiplier: 2x per retry
- Timeout: 60 seconds per call

## Performance

### Estimated Processing Time

- Image processing: ~0.1s per frame
- VLM API call: ~2-5s per frame
- Total per frame: ~3-6s
- For 10,000 frames: ~8-17 hours

### Optimization Tips

1. **Adjust checkpoint interval**: Increase for faster processing, decrease for more frequent saves
2. **Batch processing**: Process multiple shards in parallel on different machines
3. **Image quality**: Reduce JPEG quality to decrease file size (trade-off with quality)
4. **Model selection**: Use faster models for quicker processing

## Troubleshooting

### API Key Not Found

```
Error: Environment variable ONE_API_KEY_KEWEI not set
```

Solution:
```bash
export ONE_API_KEY_KEWEI="your_api_key_here"
```

### Dataset Path Not Found

```
Error: No files found matching pattern: /path/to/dataset
```

Solution: Verify the dataset path in `config.yaml` matches your actual dataset location.

### VLM API Failures

Check logs in `output/processing.log` for detailed error messages. Common issues:
- Rate limiting: Increase `retry_delay_seconds` in config
- Timeout: Increase `timeout_seconds` in config
- Authentication: Verify API key is correct

### Out of Memory

If processing large images:
1. Reduce `target_height` in config
2. Reduce `jpeg_quality` in config
3. Process fewer frames at a time

### Resume Not Working

If checkpoint file is corrupted:
1. Delete `output/checkpoint.json`
2. Run without `--resume` flag to start fresh
3. Or manually edit checkpoint file to remove problematic frames

## Development

### Project Structure

- **src/config.py**: Configuration loading and validation
- **src/dataset_loader.py**: TFRecord loading and 1Hz sampling
- **src/image_processor.py**: Image extraction and downsampling
- **src/trajectory_extractor.py**: Trajectory and ego status extraction
- **src/prompt_builder.py**: VLM prompt formatting
- **src/vlm_client.py**: VLM API client with retry logic
- **src/output_handler.py**: Result saving and checkpointing
- **src/utils.py**: Utility functions

### Adding Custom Processing

To add custom processing steps:

1. Create a new module in `src/`
2. Implement your processing logic
3. Integrate into `WaymoE2EPipeline.process_frame()` method
4. Update configuration if needed

### Testing

To test with a small subset:

```bash
python waymo_e2e_processor.py \
    --config config.yaml \
    --max-frames 10 \
    --log-level DEBUG
```

## References

- [Waymo Open Dataset](https://waymo.com/open)
- [Waymo E2E Driving Challenge](https://waymo.com/open/challenges/2025/e2e-driving/)
- [Poutine Paper](https://arxiv.org/abs/2406.00801)
- [Waymo Dataset GitHub](https://github.com/waymo-research/waymo-open-dataset)

## License

This pipeline uses the Waymo Open Dataset, which is licensed under the Apache License 2.0.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in `output/processing.log`
3. Verify configuration in `config.yaml`
4. Check Waymo Open Dataset documentation

## Notes

- The pipeline processes frames at 1Hz (every 10th frame from 10Hz dataset)
- All trajectories are in vehicle coordinate system (+x=forward, +y=left, +z=up)
- Images are downsampled to height=512 maintaining aspect ratio
- VLM responses are validated for required fields
- Checkpoint system enables resuming from any point
- All results are saved as JSON for easy processing
