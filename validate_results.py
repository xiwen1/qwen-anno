#!/usr/bin/env python3
"""
Validate results for correctness and completeness.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

def load_results(results_dir: str) -> List[Dict[str, Any]]:
    """Load all result JSON files."""
    results = []
    results_path = Path(results_dir)

    if not results_path.exists():
        print(f"Results directory not found: {results_dir}")
        return results

    for json_file in sorted(results_path.glob("*.json")):
        try:
            with open(json_file, 'r') as f:
                result = json.load(f)
                results.append(result)
        except Exception as e:
            print(f"Warning: Failed to load {json_file}: {e}")

    return results

def validate_result_structure(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a single result structure."""
    errors = []

    # Check required top-level keys
    required_keys = ["metadata", "input_data", "vlm_response"]
    for key in required_keys:
        if key not in result:
            errors.append(f"Missing key: {key}")

    # Validate metadata
    metadata = result.get("metadata", {})
    metadata_keys = ["frame_name", "timestamp_micros", "processing_timestamp", "model_name"]
    for key in metadata_keys:
        if key not in metadata:
            errors.append(f"Missing metadata key: {key}")

    # Validate input_data
    input_data = result.get("input_data", {})
    input_keys = ["past_trajectory", "future_trajectory", "ego_status"]
    for key in input_keys:
        if key not in input_data:
            errors.append(f"Missing input_data key: {key}")

    # Validate trajectories
    past_traj = input_data.get("past_trajectory", [])
    if len(past_traj) != 16:
        errors.append(f"Past trajectory has {len(past_traj)} points, expected 16")

    future_traj = input_data.get("future_trajectory", [])
    if len(future_traj) != 20:
        errors.append(f"Future trajectory has {len(future_traj)} points, expected 20")

    # Validate ego_status
    ego_status = input_data.get("ego_status", {})
    ego_keys = ["velocity", "speed", "intent"]
    for key in ego_keys:
        if key not in ego_status:
            errors.append(f"Missing ego_status key: {key}")

    # Validate VLM response
    vlm_response = result.get("vlm_response", {})
    vlm_keys = ["critical_objects", "explanation", "meta_behaviour"]
    for key in vlm_keys:
        if key not in vlm_response:
            errors.append(f"Missing vlm_response key: {key}")

    # Validate critical_objects
    critical_objects = vlm_response.get("critical_objects", {})
    required_objects = [
        "nearby_vehicle", "pedestrian", "cyclist", "construction",
        "traffic_element", "weather_condition", "road_hazard",
        "emergency_vehicle", "animal", "special_vehicle",
        "conflicting_vehicle", "door_opening_vehicle"
    ]
    for obj in required_objects:
        if obj not in critical_objects:
            errors.append(f"Missing critical object: {obj}")
        elif critical_objects[obj] not in ["yes", "no"]:
            errors.append(f"Invalid value for {obj}: {critical_objects[obj]}")

    # Validate meta_behaviour
    meta_behaviour = vlm_response.get("meta_behaviour", {})
    if "speed" not in meta_behaviour:
        errors.append("Missing speed in meta_behaviour")
    if "command" not in meta_behaviour:
        errors.append("Missing command in meta_behaviour")

    return len(errors) == 0, errors

def validate_all_results(results: List[Dict]) -> Dict[str, Any]:
    """Validate all results."""
    total = len(results)
    valid = 0
    invalid = 0
    errors_by_type = {}

    for i, result in enumerate(results):
        is_valid, errors = validate_result_structure(result)
        if is_valid:
            valid += 1
        else:
            invalid += 1
            for error in errors:
                error_type = error.split(":")[0]
                if error_type not in errors_by_type:
                    errors_by_type[error_type] = []
                errors_by_type[error_type].append(error)

    return {
        "total": total,
        "valid": valid,
        "invalid": invalid,
        "validity_rate": (valid / total * 100) if total > 0 else 0,
        "errors_by_type": errors_by_type,
    }

def print_validation_report(validation_result: Dict[str, Any]):
    """Print validation report."""
    print("\n" + "=" * 70)
    print("RESULTS VALIDATION REPORT")
    print("=" * 70)

    print(f"\nTotal results: {validation_result['total']}")
    print(f"Valid results: {validation_result['valid']}")
    print(f"Invalid results: {validation_result['invalid']}")
    print(f"Validity rate: {validation_result['validity_rate']:.1f}%")

    if validation_result['errors_by_type']:
        print("\n" + "-" * 70)
        print("ERRORS BY TYPE")
        print("-" * 70)

        for error_type, errors in validation_result['errors_by_type'].items():
            print(f"\n{error_type}: {len(errors)} occurrences")
            # Show first 3 examples
            for error in errors[:3]:
                print(f"  - {error}")
            if len(errors) > 3:
                print(f"  ... and {len(errors) - 3} more")

    print("\n" + "=" * 70 + "\n")

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        results_dir = "./output/results"
    else:
        results_dir = sys.argv[1]

    print(f"Validating results from: {results_dir}")
    results = load_results(results_dir)

    if not results:
        print("No results found")
        return 1

    print(f"Loaded {len(results)} results\n")

    # Validate
    validation_result = validate_all_results(results)
    print_validation_report(validation_result)

    # Return exit code based on validity
    return 0 if validation_result['invalid'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
