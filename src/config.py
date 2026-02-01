"""Configuration system for Waymo E2E dataset processing pipeline."""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class DatasetConfig:
    """Dataset configuration."""
    path: str
    sampling_frequency_hz: int = 1


@dataclass
class ImageProcessingConfig:
    """Image processing configuration."""
    target_height: int = 512
    cameras: list = field(default_factory=lambda: ["FRONT_LEFT", "FRONT", "FRONT_RIGHT"])
    input_mode: str = "separate"  # "separate" or "concatenated"
    jpeg_quality: int = 90


@dataclass
class TrajectoryConfig:
    """Trajectory configuration."""
    past_duration_seconds: int = 4
    past_frequency_hz: int = 4
    future_duration_seconds: int = 5
    future_frequency_hz: int = 4


@dataclass
class VLMAPIConfig:
    """VLM API configuration."""
    model_name: str = "gemini-2.5-flash"
    api_key_env_var: str = "ONE_API_KEY_KEWEI"
    system_prompt: str = "You are an expert labeller of driving scenarios."
    prompt_template_path: str = "./input_prompt.txt"
    max_retries: int = 3
    retry_delay_seconds: float = 2.0
    timeout_seconds: int = 60


@dataclass
class ProcessingConfig:
    """Processing configuration."""
    batch_size: int = 1
    checkpoint_interval: int = 10
    max_workers: int = 1
    max_frames: Optional[int] = None


@dataclass
class OutputConfig:
    """Output configuration."""
    output_dir: str = "./output"
    run_name: Optional[str] = None
    results_subdir: str = "results"
    checkpoint_file: str = "checkpoint.json"
    log_file: str = "processing.log"
    save_images: bool = False


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_output: bool = True
    file_output: bool = True


@dataclass
class WaymoE2EConfig:
    """Main configuration for Waymo E2E processing pipeline."""
    dataset: DatasetConfig
    image_processing: ImageProcessingConfig
    trajectory: TrajectoryConfig
    vlm_api: VLMAPIConfig
    processing: ProcessingConfig
    output: OutputConfig
    logging: LoggingConfig

    @classmethod
    def from_yaml(cls, config_path: str) -> "WaymoE2EConfig":
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)

        return cls(
            dataset=DatasetConfig(**config_dict.get('dataset', {})),
            image_processing=ImageProcessingConfig(**config_dict.get('image_processing', {})),
            trajectory=TrajectoryConfig(**config_dict.get('trajectory', {})),
            vlm_api=VLMAPIConfig(**config_dict.get('vlm_api', {})),
            processing=ProcessingConfig(**config_dict.get('processing', {})),
            output=OutputConfig(**config_dict.get('output', {})),
            logging=LoggingConfig(**config_dict.get('logging', {})),
        )

    def validate(self) -> bool:
        """Validate configuration parameters."""
        errors = []

        # Validate dataset path
        if not self.dataset.path:
            errors.append("dataset.path is required")

        # Validate image processing
        if self.image_processing.target_height <= 0:
            errors.append("image_processing.target_height must be positive")

        if self.image_processing.input_mode not in ["separate", "concatenated"]:
            errors.append("image_processing.input_mode must be 'separate' or 'concatenated'")

        # Validate trajectory
        if self.trajectory.past_frequency_hz <= 0:
            errors.append("trajectory.past_frequency_hz must be positive")

        if self.trajectory.future_frequency_hz <= 0:
            errors.append("trajectory.future_frequency_hz must be positive")

        # Validate VLM API
        api_key = os.getenv(self.vlm_api.api_key_env_var)
        if not api_key:
            errors.append(f"Environment variable {self.vlm_api.api_key_env_var} not set")

        if not os.path.exists(self.vlm_api.prompt_template_path):
            errors.append(f"Prompt template not found: {self.vlm_api.prompt_template_path}")

        # Validate processing
        if self.processing.checkpoint_interval <= 0:
            errors.append("processing.checkpoint_interval must be positive")

        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(errors))

        return True

    def get_api_key(self) -> str:
        """Get API key from environment variable."""
        api_key = os.getenv(self.vlm_api.api_key_env_var)
        if not api_key:
            raise ValueError(f"Environment variable {self.vlm_api.api_key_env_var} not set")
        return api_key

    def get_run_dir(self) -> Path:
        """Get the run directory path."""
        from datetime import datetime

        output_path = Path(self.output.output_dir)

        # Generate run name if not specified
        if self.output.run_name:
            run_name = self.output.run_name
        else:
            run_name = datetime.now().strftime("run_%Y%m%d_%H%M%S")

        return output_path / run_name

    def setup_output_dirs(self):
        """Create output directories."""
        run_dir = self.get_run_dir()
        run_dir.mkdir(parents=True, exist_ok=True)

        results_path = run_dir / self.output.results_subdir
        results_path.mkdir(parents=True, exist_ok=True)
