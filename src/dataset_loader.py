"""Dataset loader for Waymo E2E dataset."""

import tensorflow as tf
import logging
from typing import Iterator, Optional
from waymo_open_dataset.protos import end_to_end_driving_data_pb2 as wod_e2ed_pb2

logger = logging.getLogger(__name__)


class WaymoE2EDatasetLoader:
    """Loader for Waymo E2E dataset from TFRecord files."""

    def __init__(self, dataset_path: str, sampling_frequency_hz: int = 1):
        """
        Initialize dataset loader.

        Args:
            dataset_path: Path pattern to TFRecord files (e.g., '/path/to/training.tfrecord*')
            sampling_frequency_hz: Sampling frequency in Hz (1Hz means every 10th frame from 10Hz dataset)
        """
        self.dataset_path = dataset_path
        self.sampling_frequency_hz = sampling_frequency_hz
        self.sampling_interval = int(10 / sampling_frequency_hz)  # 10Hz dataset

    def load_dataset(self) -> tf.data.Dataset:
        """
        Load TFRecord dataset.

        Returns:
            TensorFlow dataset iterator
        """
        filenames = tf.io.matching_files(self.dataset_path)
        num_files = tf.size(filenames).numpy()
        if num_files == 0:
            raise FileNotFoundError(f"No files found matching pattern: {self.dataset_path}")

        # Convert to list and sort for deterministic ordering
        filenames_list = sorted(filenames.numpy().astype(str).tolist())
        num_files = len(filenames_list)

        logger.info(f"Found {num_files} TFRecord files")
        logger.debug(f"Files in order: {filenames_list}")

        dataset = tf.data.TFRecordDataset(filenames_list, compression_type='')
        return dataset

    def sample_frames_at_target_frequency(self, dataset: tf.data.Dataset) -> Iterator[bytes]:
        """
        Sample frames at target frequency.

        Args:
            dataset: TensorFlow dataset

        Yields:
            Sampled frame bytes
        """
        dataset_iter = dataset.as_numpy_iterator()
        frame_count = 0

        for frame_bytes in dataset_iter:
            if frame_count % self.sampling_interval == 0:
                yield frame_bytes
            frame_count += 1

    def parse_e2ed_frame(self, frame_bytes: bytes) -> Optional[wod_e2ed_pb2.E2EDFrame]:
        """
        Parse E2EDFrame from bytes.

        Args:
            frame_bytes: Raw frame bytes

        Returns:
            Parsed E2EDFrame or None if parsing fails
        """
        try:
            frame = wod_e2ed_pb2.E2EDFrame()
            frame.ParseFromString(frame_bytes)
            return frame
        except Exception as e:
            logger.warning(f"Failed to parse E2EDFrame: {e}")
            return None

    def get_frame_iterator(self, max_frames: Optional[int] = None) -> Iterator[wod_e2ed_pb2.E2EDFrame]:
        """
        Get iterator over parsed frames with consistent ordering.

        Args:
            max_frames: Maximum number of frames to process (None for all)

        Yields:
            Parsed E2EDFrame objects
        """
        dataset = self.load_dataset()
        frame_count = 0

        logger.info(f"Starting frame iteration with sampling frequency {self.sampling_frequency_hz}Hz "
                   f"(sampling interval: every {self.sampling_interval}th frame)")

        for frame_bytes in self.sample_frames_at_target_frequency(dataset):
            if max_frames and frame_count >= max_frames:
                break

            frame = self.parse_e2ed_frame(frame_bytes)
            if frame:
                yield frame
                frame_count += 1
            else:
                logger.warning(f"Skipping frame {frame_count} due to parsing error")
