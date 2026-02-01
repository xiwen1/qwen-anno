"""Output handler for saving results and managing checkpoints."""

import json
import logging
import base64
from pathlib import Path
from typing import Dict, Any, Set, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class OutputHandler:
    """Handler for saving results and managing checkpoints."""

    def __init__(self, output_dir: str, results_subdir: str = "results",
                 checkpoint_file: str = "checkpoint.json", save_images: bool = False):
        """
        Initialize output handler.

        Args:
            output_dir: Base output directory
            results_subdir: Subdirectory for individual frame results
            checkpoint_file: Checkpoint file name
            save_images: Whether to save images to disk
        """
        self.output_dir = Path(output_dir)
        self.results_dir = self.output_dir / results_subdir
        self.images_dir = self.output_dir / "images"
        self.checkpoint_path = self.output_dir / checkpoint_file
        self.save_images = save_images

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        if self.save_images:
            self.images_dir.mkdir(parents=True, exist_ok=True)

    def _save_images(self, frame_name: str, images_base64: List[str],
                     image_names: List[str]) -> List[str]:
        """
        Save base64 encoded images to disk.

        Args:
            frame_name: Unique frame identifier
            images_base64: List of base64 encoded images
            image_names: List of image names (e.g., ["front_left", "front", "front_right"])

        Returns:
            List of relative paths to saved images
        """
        frame_images_dir = self.images_dir / frame_name
        frame_images_dir.mkdir(parents=True, exist_ok=True)

        image_paths = []
        for img_base64, img_name in zip(images_base64, image_names):
            try:
                # Decode base64 to bytes
                img_bytes = base64.b64decode(img_base64)

                # Save image
                img_filename = f"{img_name}.jpg"
                img_path = frame_images_dir / img_filename
                with open(img_path, 'wb') as f:
                    f.write(img_bytes)

                # Store relative path from output_dir
                relative_path = f"images/{frame_name}/{img_filename}"
                image_paths.append(relative_path)

            except Exception as e:
                logger.warning(f"Failed to save image {img_name} for frame {frame_name}: {e}")
                image_paths.append(None)

        return image_paths

    def save_result(self, frame_name: str, metadata: Dict[str, Any],
                    input_data: Dict[str, Any], vlm_response: Dict[str, Any],
                    token_usage: Optional[Dict[str, int]] = None,
                    images_base64: Optional[List[str]] = None,
                    image_names: Optional[List[str]] = None):
        """
        Save processing result for a frame.

        Args:
            frame_name: Unique frame identifier
            metadata: Frame metadata
            input_data: Input data (trajectories, ego status)
            vlm_response: VLM response
            token_usage: Token usage statistics
            images_base64: Optional list of base64 encoded images to save
            image_names: Optional list of image names corresponding to images_base64
        """
        result = {
            "metadata": {
                "frame_name": frame_name,
                "processing_timestamp": datetime.now().isoformat(),
                **metadata
            },
            "input_data": input_data,
            "vlm_response": vlm_response,
        }

        if token_usage:
            result["token_usage"] = token_usage

        # Save images if enabled
        if self.save_images and images_base64 and image_names:
            image_paths = self._save_images(frame_name, images_base64, image_names)
            result["image_paths"] = image_paths

        # Generate output filename
        output_file = self.results_dir / f"{frame_name}.json"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved result to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save result to {output_file}: {e}")
            raise

    def load_checkpoint(self) -> Set[str]:
        """
        Load processed frame names from checkpoint.

        Returns:
            Set of processed frame names
        """
        if not self.checkpoint_path.exists():
            return set()

        try:
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            processed_frames = set(checkpoint.get("processed_frames", []))
            logger.info(f"Loaded checkpoint with {len(processed_frames)} processed frames")
            return processed_frames
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return set()

    def save_checkpoint(self, processed_frames: Set[str]):
        """
        Save checkpoint of processed frames.

        Args:
            processed_frames: Set of processed frame names
        """
        checkpoint = {
            "last_updated": datetime.now().isoformat(),
            "total_processed": len(processed_frames),
            "processed_frames": sorted(list(processed_frames))
        }

        try:
            # Write to temporary file first, then rename (atomic operation)
            temp_path = self.checkpoint_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, indent=2)
            temp_path.replace(self.checkpoint_path)
            logger.debug(f"Saved checkpoint with {len(processed_frames)} frames")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise

    def generate_summary(self, total_frames: int, processed_frames: int,
                        skipped_frames: int, failed_frames: int) -> Dict[str, Any]:
        """
        Generate processing summary.

        Args:
            total_frames: Total frames in dataset
            processed_frames: Successfully processed frames
            skipped_frames: Skipped frames
            failed_frames: Failed frames

        Returns:
            Summary dictionary
        """
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_frames": total_frames,
            "processed_frames": processed_frames,
            "skipped_frames": skipped_frames,
            "failed_frames": failed_frames,
            "success_rate": processed_frames / total_frames if total_frames > 0 else 0.0,
        }

        # Save summary
        summary_path = self.output_dir / "summary.json"
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            logger.info(f"Saved summary to {summary_path}")
        except Exception as e:
            logger.warning(f"Failed to save summary: {e}")

        return summary
