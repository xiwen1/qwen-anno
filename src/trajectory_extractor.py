"""Trajectory extractor for Waymo E2E dataset."""

import numpy as np
import logging
from typing import List, Tuple, Dict, Any
from waymo_open_dataset.protos import end_to_end_driving_data_pb2 as wod_e2ed_pb2

logger = logging.getLogger(__name__)

# Intent mapping
INTENT_MAP = {
    0: "UNKNOWN",
    1: "GO_STRAIGHT",
    2: "GO_LEFT",
    3: "GO_RIGHT",
}


class TrajectoryExtractor:
    """Extractor for trajectories and ego status from E2EDFrame."""

    def __init__(self, past_duration_seconds: int = 4, past_frequency_hz: int = 4,
                 future_duration_seconds: int = 5, future_frequency_hz: int = 4):
        """
        Initialize trajectory extractor.

        Args:
            past_duration_seconds: Duration of past trajectory in seconds
            past_frequency_hz: Frequency of past trajectory in Hz
            future_duration_seconds: Duration of future trajectory in seconds
            future_frequency_hz: Frequency of future trajectory in Hz
        """
        self.past_duration_seconds = past_duration_seconds
        self.past_frequency_hz = past_frequency_hz
        self.future_duration_seconds = future_duration_seconds
        self.future_frequency_hz = future_frequency_hz

        self.expected_past_points = past_duration_seconds * past_frequency_hz
        self.expected_future_points = future_duration_seconds * future_frequency_hz

    def extract_past_trajectory(self, frame: wod_e2ed_pb2.E2EDFrame) -> List[List[float]]:
        """
        Extract past trajectory.

        Args:
            frame: E2EDFrame object

        Returns:
            List of [x, y, z] coordinates (16 points for 4 seconds at 4Hz)
        """
        past_states = frame.past_states
        trajectory = []

        for i in range(len(past_states.pos_x)):
            x = float(past_states.pos_x[i])
            y = float(past_states.pos_y[i])
            z = float(past_states.pos_z[i])
            trajectory.append([x, y, z])

        return trajectory

    def extract_future_trajectory(self, frame: wod_e2ed_pb2.E2EDFrame) -> List[List[float]]:
        """
        Extract future trajectory.

        Args:
            frame: E2EDFrame object

        Returns:
            List of [x, y, z] coordinates (20 points for 5 seconds at 4Hz)
        """
        future_states = frame.future_states
        trajectory = []

        for i in range(len(future_states.pos_x)):
            x = float(future_states.pos_x[i])
            y = float(future_states.pos_y[i])
            z = float(future_states.pos_z[i])
            trajectory.append([x, y, z])

        return trajectory

    def extract_ego_status(self, frame: wod_e2ed_pb2.E2EDFrame) -> Dict[str, Any]:
        """
        Extract ego vehicle status.

        Args:
            frame: E2EDFrame object

        Returns:
            Dictionary with velocity, speed, and intent
        """
        past_states = frame.past_states

        # Get last velocity
        vel_x = float(past_states.vel_x[-1]) if past_states.vel_x else 0.0
        vel_y = float(past_states.vel_y[-1]) if past_states.vel_y else 0.0

        # Calculate speed
        speed = np.sqrt(vel_x ** 2 + vel_y ** 2)

        # Get intent
        intent = INTENT_MAP.get(frame.intent, "UNKNOWN")

        return {
            "velocity": [vel_x, vel_y],
            "speed": float(speed),
            "intent": intent,
        }

    def format_trajectory_as_text(self, trajectory: List[List[float]]) -> str:
        """
        Format trajectory as text string.

        Args:
            trajectory: List of [x, y, z] coordinates

        Returns:
            Formatted text string
        """
        # Format as list of tuples
        formatted = str([tuple(point) for point in trajectory])
        return formatted

    def validate_frame(self, frame: wod_e2ed_pb2.E2EDFrame) -> Tuple[bool, str]:
        """
        Validate if a frame has complete trajectory data.

        Args:
            frame: E2EDFrame object

        Returns:
            Tuple of (is_valid, error_message)
        """
        past_states = frame.past_states
        future_states = frame.future_states

        # Check past trajectory
        past_x_len = len(past_states.pos_x)
        past_y_len = len(past_states.pos_y)
        past_z_len = len(past_states.pos_z)

        if past_x_len != past_y_len or past_x_len != past_z_len:
            return False, (
                f"Past trajectory arrays have mismatched lengths: "
                f"pos_x={past_x_len}, pos_y={past_y_len}, pos_z={past_z_len}"
            )

        if past_x_len != self.expected_past_points:
            return False, (
                f"Expected {self.expected_past_points} past points, got {past_x_len}"
            )

        # Check future trajectory
        future_x_len = len(future_states.pos_x)
        future_y_len = len(future_states.pos_y)
        future_z_len = len(future_states.pos_z)

        if future_x_len != future_y_len or future_x_len != future_z_len:
            return False, (
                f"Future trajectory arrays have mismatched lengths: "
                f"pos_x={future_x_len}, pos_y={future_y_len}, pos_z={future_z_len}"
            )

        if future_x_len != self.expected_future_points:
            return False, (
                f"Expected {self.expected_future_points} future points, got {future_x_len}"
            )

        return True, ""

    def extract_all(self, frame: wod_e2ed_pb2.E2EDFrame) -> Dict[str, Any]:
        """
        Extract all trajectory and status information.

        Args:
            frame: E2EDFrame object

        Returns:
            Dictionary with past_trajectory, future_trajectory, and ego_status

        Raises:
            ValueError: If frame does not have complete trajectory data
        """
        is_valid, error_msg = self.validate_frame(frame)
        if not is_valid:
            raise ValueError(error_msg)

        past_traj = self.extract_past_trajectory(frame)
        future_traj = self.extract_future_trajectory(frame)
        ego_status = self.extract_ego_status(frame)

        return {
            "past_trajectory": past_traj,
            "future_trajectory": future_traj,
            "ego_status": ego_status,
        }
