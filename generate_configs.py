#!/usr/bin/env python3
"""
Generate configuration files for different scenarios.
"""

import sys
import yaml
from pathlib import Path

def create_config_fast():
    """Create configuration for fast processing."""
    return {
        'dataset': {
            'path': '/path/to/waymo/dataset/training.tfrecord*',
            'sampling_frequency_hz': 1,
        },
        'image_processing': {
            'target_height': 512,
            'cameras': ['FRONT_LEFT', 'FRONT', 'FRONT_RIGHT'],
            'input_mode': 'concatenated',  # Faster
            'jpeg_quality': 80,  # Lower quality for speed
        },
        'trajectory': {
            'past_duration_seconds': 4,
            'past_frequency_hz': 4,
            'future_duration_seconds': 5,
            'future_frequency_hz': 4,
        },
        'vlm_api': {
            'model_name': 'gemini-2.5-flash',  # Fast model
            'api_key_env_var': 'ONE_API_KEY_KEWEI',
            'system_prompt': 'You are an expert labeller of driving scenarios.',
            'prompt_template_path': './input_prompt.txt',
            'max_retries': 2,  # Fewer retries
            'retry_delay_seconds': 1.0,  # Shorter delay
            'timeout_seconds': 60,
        },
        'processing': {
            'batch_size': 1,
            'checkpoint_interval': 50,  # Save less frequently
            'max_workers': 1,
            'max_frames': None,
        },
        'output': {
            'output_dir': './output',
            'results_subdir': 'results',
            'checkpoint_file': 'checkpoint.json',
            'log_file': 'processing.log',
            'save_images': False,
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'console_output': True,
            'file_output': True,
        },
    }

def create_config_quality():
    """Create configuration for high-quality results."""
    return {
        'dataset': {
            'path': '/path/to/waymo/dataset/training.tfrecord*',
            'sampling_frequency_hz': 1,
        },
        'image_processing': {
            'target_height': 512,
            'cameras': ['FRONT_LEFT', 'FRONT', 'FRONT_RIGHT'],
            'input_mode': 'separate',  # Better quality
            'jpeg_quality': 95,  # High quality
        },
        'trajectory': {
            'past_duration_seconds': 4,
            'past_frequency_hz': 4,
            'future_duration_seconds': 5,
            'future_frequency_hz': 4,
        },
        'vlm_api': {
            'model_name': 'gpt-4o-20241120',  # Powerful model
            'api_key_env_var': 'ONE_API_KEY_KEWEI',
            'system_prompt': 'You are an expert labeller of driving scenarios.',
            'prompt_template_path': './input_prompt.txt',
            'max_retries': 5,  # More retries
            'retry_delay_seconds': 3.0,  # Longer delay
            'timeout_seconds': 120,
        },
        'processing': {
            'batch_size': 1,
            'checkpoint_interval': 10,  # Save frequently
            'max_workers': 1,
            'max_frames': None,
        },
        'output': {
            'output_dir': './output',
            'results_subdir': 'results',
            'checkpoint_file': 'checkpoint.json',
            'log_file': 'processing.log',
            'save_images': False,
        },
        'logging': {
            'level': 'DEBUG',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'console_output': True,
            'file_output': True,
        },
    }

def create_config_balanced():
    """Create balanced configuration."""
    return {
        'dataset': {
            'path': '/path/to/waymo/dataset/training.tfrecord*',
            'sampling_frequency_hz': 1,
        },
        'image_processing': {
            'target_height': 512,
            'cameras': ['FRONT_LEFT', 'FRONT', 'FRONT_RIGHT'],
            'input_mode': 'separate',
            'jpeg_quality': 90,
        },
        'trajectory': {
            'past_duration_seconds': 4,
            'past_frequency_hz': 4,
            'future_duration_seconds': 5,
            'future_frequency_hz': 4,
        },
        'vlm_api': {
            'model_name': 'gemini-2.5-flash',
            'api_key_env_var': 'ONE_API_KEY_KEWEI',
            'system_prompt': 'You are an expert labeller of driving scenarios.',
            'prompt_template_path': './input_prompt.txt',
            'max_retries': 3,
            'retry_delay_seconds': 2.0,
            'timeout_seconds': 60,
        },
        'processing': {
            'batch_size': 1,
            'checkpoint_interval': 20,
            'max_workers': 1,
            'max_frames': None,
        },
        'output': {
            'output_dir': './output',
            'results_subdir': 'results',
            'checkpoint_file': 'checkpoint.json',
            'log_file': 'processing.log',
            'save_images': False,
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'console_output': True,
            'file_output': True,
        },
    }

def create_config_testing():
    """Create configuration for testing."""
    return {
        'dataset': {
            'path': '/path/to/waymo/dataset/training.tfrecord*',
            'sampling_frequency_hz': 1,
        },
        'image_processing': {
            'target_height': 512,
            'cameras': ['FRONT_LEFT', 'FRONT', 'FRONT_RIGHT'],
            'input_mode': 'concatenated',
            'jpeg_quality': 70,
        },
        'trajectory': {
            'past_duration_seconds': 4,
            'past_frequency_hz': 4,
            'future_duration_seconds': 5,
            'future_frequency_hz': 4,
        },
        'vlm_api': {
            'model_name': 'gemini-2.5-flash',
            'api_key_env_var': 'ONE_API_KEY_KEWEI',
            'system_prompt': 'You are an expert labeller of driving scenarios.',
            'prompt_template_path': './input_prompt.txt',
            'max_retries': 2,
            'retry_delay_seconds': 1.0,
            'timeout_seconds': 60,
        },
        'processing': {
            'batch_size': 1,
            'checkpoint_interval': 5,
            'max_workers': 1,
            'max_frames': 100,  # Test with 100 frames
        },
        'output': {
            'output_dir': './output_test',
            'results_subdir': 'results',
            'checkpoint_file': 'checkpoint.json',
            'log_file': 'processing.log',
            'save_images': False,
        },
        'logging': {
            'level': 'DEBUG',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'console_output': True,
            'file_output': True,
        },
    }

def save_config(config: dict, filename: str):
    """Save configuration to YAML file."""
    with open(filename, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    print(f"✓ Created {filename}")

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python generate_configs.py [fast|quality|balanced|testing|all]")
        print("\nExamples:")
        print("  python generate_configs.py fast")
        print("  python generate_configs.py quality")
        print("  python generate_configs.py all")
        return 1

    scenario = sys.argv[1].lower()

    configs = {
        'fast': ('config_fast.yaml', create_config_fast),
        'quality': ('config_quality.yaml', create_config_quality),
        'balanced': ('config_balanced.yaml', create_config_balanced),
        'testing': ('config_testing.yaml', create_config_testing),
    }

    if scenario == 'all':
        for name, (filename, creator) in configs.items():
            config = creator()
            save_config(config, filename)
    elif scenario in configs:
        filename, creator = configs[scenario]
        config = creator()
        save_config(config, filename)
    else:
        print(f"Unknown scenario: {scenario}")
        return 1

    print("\n✓ Configuration files generated successfully!")
    print("\nUsage:")
    print("  python waymo_e2e_processor.py --config config_fast.yaml")
    print("  python waymo_e2e_processor.py --config config_quality.yaml")
    print("  python waymo_e2e_processor.py --config config_balanced.yaml")
    print("  python waymo_e2e_processor.py --config config_testing.yaml")

    return 0

if __name__ == "__main__":
    sys.exit(main())
