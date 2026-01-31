"""Prompt builder for VLM input."""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builder for VLM prompts."""

    def __init__(self, prompt_template_path: str):
        """
        Initialize prompt builder.

        Args:
            prompt_template_path: Path to prompt template file
        """
        self.prompt_template_path = prompt_template_path
        self.template = self._load_template()

    def _load_template(self) -> str:
        """Load prompt template from file."""
        try:
            with open(self.prompt_template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to load prompt template: {e}")
            return self._get_default_template()

    def _get_default_template(self) -> str:
        """Get default prompt template."""
        return """You are an expert labeller of driving scenarios. Input: - 3 frames of multi-view images collected from the ego-vehicle over the last 1 second - Current high-level intent (string) - 4-second past trajectory (16 steps at 4 Hz) - Expert 5-second future trajectory (20 steps at 4 Hz) Task: 1. Inspect the input and decide, for each object class below, whether at least one critical instance of that class is present (i.e., it materially affects the ego-vehicle's future trajectory). A vehicle can be a car, bus, truck, motorcyclist, scooter, etc. traffic_element includes traffic signs and traffic lights. road_hazard may include hazardous road conditions, road debris, obstacles, etc. A conflicting_vehicle is a vehicle that may potentially conflict with the ego's future path. Object classes to audit: - nearby_vehicle - pedestrian - cyclist - construction - traffic_element - weather_condition - road_hazard - emergency_vehicle - animal - special_vehicle - conflicting_vehicle - door_opening_vehicle 2. Output "yes" or "no" for every class (no omissions). 3. Compose a concise natural-language description explaining why the expert safe driver plans the given future trajectory. - Mention only the classes you marked "yes" - Describe how each of those critical objects or conditions influences the trajectory. - Do not invent objects or conditions not present in the input. 4. From the expert's 5-second future trajectory, assign exactly one category from each list: - speed ∈ { keep, accelerate, decelerate } - command ∈ { straight, yield, left_turn, right_turn, lane_follow, lane_change_left, lane_change_right, reverse } Choose the label that best summarises the overall behaviour of the expert future trajectory. - If none fits, use 'other', but do this sparingly. Output format (strict JSON, no extra keys, no commentary): {  "critical_objects": { "nearby_vehicle": "yes | no", "pedestrian": "yes | no", "cyclist": "yes | no", "construction": "yes | no", "traffic_element": "yes | no", "weather_condition": "yes | no", "road_hazard": "yes | no", "emergency_vehicle": "yes | no", "animal": "yes | no", "special_vehicle": "yes | no", "conflicting_vehicle": "yes | no", "door_opening_vehicle": "yes | no" }, "explanation": "100-word description that references only the classes marked 'yes'", "meta_behaviour": { "speed": "keep | accelerate | decelerate | other", "command": "straight | yield | left_turn | right_turn | lane_follow | lane_change_left | lane_change_right | reverse | other"}}"""

    def build_prompt(self, trajectory_data: Dict[str, Any]) -> str:
        """
        Build VLM prompt from trajectory data.

        Args:
            trajectory_data: Dictionary with past_trajectory, future_trajectory, and ego_status

        Returns:
            Formatted prompt string
        """
        past_traj = trajectory_data.get("past_trajectory", [])
        future_traj = trajectory_data.get("future_trajectory", [])
        ego_status = trajectory_data.get("ego_status", {})

        # Format trajectories as text
        past_traj_text = self._format_trajectory(past_traj)
        future_traj_text = self._format_trajectory(future_traj)
        intent = ego_status.get("intent", "UNKNOWN")

        # Build prompt with trajectory information
        prompt = self.template + "\n\n"
        prompt += f"Current intent: {intent}\n"
        prompt += f"Past trajectory (4 seconds, 16 points at 4Hz):\n{past_traj_text}\n\n"
        prompt += f"Future trajectory (5 seconds, 20 points at 4Hz):\n{future_traj_text}\n"

        return prompt

    def _format_trajectory(self, trajectory: List[List[float]]) -> str:
        """
        Format trajectory as readable text.

        Args:
            trajectory: List of [x, y, z] coordinates

        Returns:
            Formatted text string
        """
        if not trajectory:
            return "[]"

        # Format as list of tuples with limited precision
        formatted_points = [f"({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})" for p in trajectory]
        return "[" + ", ".join(formatted_points) + "]"
