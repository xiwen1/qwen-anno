"""VLM API client with retry logic."""

import logging
import time
import json
from typing import Optional, Dict, Any
import sys
import os

logger = logging.getLogger(__name__)


class VLMClient:
    """Client for calling VLM API with retry logic."""

    def __init__(self, api_key: str, model_name: str, max_retries: int = 3,
                 retry_delay_seconds: float = 2.0, timeout_seconds: int = 60):
        """
        Initialize VLM client.

        Args:
            api_key: API key for VLM service
            model_name: Model name to use
            max_retries: Maximum number of retries
            retry_delay_seconds: Initial delay between retries (exponential backoff)
            timeout_seconds: Timeout for API calls
        """
        self.api_key = api_key
        self.model_name = model_name
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.timeout_seconds = timeout_seconds

        # Import test.py's call_vlm_with_oneapi function
        self._import_vlm_caller()

    def _import_vlm_caller(self):
        """Import VLM caller from test.py."""
        try:
            # Add parent directory to path to import test.py
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from test import call_vlm_with_oneapi
            self.call_vlm_with_oneapi = call_vlm_with_oneapi
        except ImportError as e:
            logger.error(f"Failed to import call_vlm_with_oneapi from test.py: {e}")
            raise

    def call_vlm(self, system_prompt: str, user_prompt: str,
                 video_frames_base64: Optional[list] = None) -> Optional[str]:
        """
        Call VLM API with retry logic.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt with trajectory information
            video_frames_base64: List of base64 encoded images

        Returns:
            VLM response text or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                response = self.call_vlm_with_oneapi(
                    api_key=self.api_key,
                    model_name=self.model_name,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    image_paths=None,
                    video_frames_base64=video_frames_base64,
                )
                return response
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay_seconds * (2 ** attempt)
                    logger.warning(f"VLM API call failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"VLM API call failed after {self.max_retries} attempts: {e}")
                    return None

    def parse_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse VLM response JSON.

        Args:
            response_text: Raw response text from VLM

        Returns:
            Parsed JSON dictionary or None if parsing fails
        """
        try:
            # Try to extract JSON from response
            # VLM might include extra text before/after JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                logger.warning("No JSON found in VLM response")
                return None

            json_str = response_text[start_idx:end_idx]
            parsed = json.loads(json_str)

            # Validate response structure
            if not self._validate_response_structure(parsed):
                logger.warning("VLM response structure is invalid")
                return None

            return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse VLM response as JSON: {e}")
            return None

    def _validate_response_structure(self, response: Dict[str, Any]) -> bool:
        """
        Validate VLM response structure.

        Args:
            response: Parsed response dictionary

        Returns:
            True if valid, False otherwise
        """
        required_keys = ["critical_objects", "explanation", "meta_behaviour"]
        if not all(key in response for key in required_keys):
            logger.warning(f"Missing required keys in response: {required_keys}")
            return False

        # Validate critical_objects
        required_objects = [
            "nearby_vehicle", "pedestrian", "cyclist", "construction",
            "traffic_element", "weather_condition", "road_hazard",
            "emergency_vehicle", "animal", "special_vehicle",
            "conflicting_vehicle", "door_opening_vehicle"
        ]
        critical_objects = response.get("critical_objects", {})
        if not all(obj in critical_objects for obj in required_objects):
            logger.warning(f"Missing object classes in critical_objects")
            return False

        # Validate meta_behaviour
        meta_behaviour = response.get("meta_behaviour", {})
        if "speed" not in meta_behaviour or "command" not in meta_behaviour:
            logger.warning("Missing speed or command in meta_behaviour")
            return False

        return True
