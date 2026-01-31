"""Image processor for Waymo E2E dataset."""

import cv2
import numpy as np
import tensorflow as tf
import base64
import logging
from typing import List, Tuple, Optional
from waymo_open_dataset.protos import end_to_end_driving_data_pb2 as wod_e2ed_pb2

logger = logging.getLogger(__name__)

# Camera name mapping
CAMERA_NAME_MAP = {
    1: "FRONT",
    2: "FRONT_LEFT",
    3: "FRONT_RIGHT",
}


class ImageProcessor:
    """Processor for extracting and processing images from E2EDFrame."""

    def __init__(self, target_height: int = 512, input_mode: str = "separate", jpeg_quality: int = 90):
        """
        Initialize image processor.

        Args:
            target_height: Target height for downsampling (width adjusted to maintain aspect ratio)
            input_mode: "separate" for three separate images or "concatenated" for one concatenated image
            jpeg_quality: JPEG quality for encoding (1-100)
        """
        self.target_height = target_height
        self.input_mode = input_mode
        self.jpeg_quality = jpeg_quality

    def extract_front_cameras(self, frame: wod_e2ed_pb2.E2EDFrame) -> List[Tuple[np.ndarray, str]]:
        """
        Extract front-facing camera images.

        Args:
            frame: E2EDFrame object

        Returns:
            List of (image_array, camera_name) tuples ordered as [FRONT_LEFT, FRONT, FRONT_RIGHT]
        """
        images = []
        camera_order = [2, 1, 3]  # FRONT_LEFT, FRONT, FRONT_RIGHT

        for camera_id in camera_order:
            for image_content in frame.frame.images:
                if image_content.name == camera_id:
                    try:
                        # Decode JPEG image
                        image = tf.io.decode_image(image_content.image).numpy()
                        camera_name = CAMERA_NAME_MAP.get(camera_id, f"CAMERA_{camera_id}")
                        images.append((image, camera_name))
                        break
                    except Exception as e:
                        logger.warning(f"Failed to decode image for camera {camera_id}: {e}")
                        return []

        if len(images) != 3:
            logger.warning(f"Expected 3 front cameras, got {len(images)}")

        return images

    def downsample_image(self, image: np.ndarray) -> np.ndarray:
        """
        Downsample image to target height maintaining aspect ratio.

        Args:
            image: Input image array

        Returns:
            Downsampled image array
        """
        original_height, original_width = image.shape[:2]
        aspect_ratio = original_width / original_height
        target_width = int(self.target_height * aspect_ratio)

        downsampled = cv2.resize(image, (target_width, self.target_height), interpolation=cv2.INTER_AREA)
        return downsampled

    def encode_image_to_base64(self, image: np.ndarray) -> str:
        """
        Encode image to base64 string.

        Args:
            image: Image array

        Returns:
            Base64 encoded string
        """
        # Encode to JPEG
        success, encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
        if not success:
            raise ValueError("Failed to encode image to JPEG")

        # Convert to base64
        base64_str = base64.b64encode(encoded.tobytes()).decode('utf-8')
        return base64_str

    def process_images_separate(self, frame: wod_e2ed_pb2.E2EDFrame) -> Optional[List[str]]:
        """
        Process images in separate mode (three separate base64 images).

        Args:
            frame: E2EDFrame object

        Returns:
            List of base64 encoded images [FRONT_LEFT, FRONT, FRONT_RIGHT] or None if failed
        """
        images = self.extract_front_cameras(frame)
        if len(images) != 3:
            logger.warning("Could not extract all 3 front cameras")
            return None

        base64_images = []
        for image, camera_name in images:
            try:
                downsampled = self.downsample_image(image)
                base64_str = self.encode_image_to_base64(downsampled)
                base64_images.append(base64_str)
            except Exception as e:
                logger.warning(f"Failed to process image for {camera_name}: {e}")
                return None

        return base64_images

    def process_images_concatenated(self, frame: wod_e2ed_pb2.E2EDFrame) -> Optional[str]:
        """
        Process images in concatenated mode (one concatenated image).

        Args:
            frame: E2EDFrame object

        Returns:
            Base64 encoded concatenated image or None if failed
        """
        images = self.extract_front_cameras(frame)
        if len(images) != 3:
            logger.warning("Could not extract all 3 front cameras")
            return None

        try:
            # Downsample each image
            downsampled_images = []
            for image, camera_name in images:
                downsampled = self.downsample_image(image)
                downsampled_images.append(downsampled)

            # Concatenate horizontally (left-center-right)
            concatenated = np.concatenate(downsampled_images, axis=1)

            # Encode to base64
            base64_str = self.encode_image_to_base64(concatenated)
            return base64_str
        except Exception as e:
            logger.warning(f"Failed to concatenate images: {e}")
            return None

    def process_images(self, frame: wod_e2ed_pb2.E2EDFrame) -> Optional[List[str]]:
        """
        Process images according to configured mode.

        Args:
            frame: E2EDFrame object

        Returns:
            List of base64 encoded images or None if failed
        """
        if self.input_mode == "separate":
            return self.process_images_separate(frame)
        elif self.input_mode == "concatenated":
            concatenated = self.process_images_concatenated(frame)
            return [concatenated] if concatenated else None
        else:
            raise ValueError(f"Unknown input_mode: {self.input_mode}")
