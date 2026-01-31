#!/usr/bin/env python3
"""
Simplified OneAPI VLM Caller
Contains only core API call input/output code
"""
import os
import base64
from openai import AzureOpenAI

# OneAPI Configuration
AZURE_API_BASE = "https://llm-proxy.perflab.nvidia.com"
AZURE_API_VERSION = "2025-02-01-preview"

# Available models configuration
AVAILABLE_MODELS: list[str] = [
    "gpt-4o-20241120",
    "gemini-2.5-flash",
    "gemini-3-pro",
]

os.environ['ONE_API_KEY_KEWEI'] = 'eyJhbGciOiJIUzI1NiJ9.eyJpZCI6IjY2MzhlOTE0LWJhZjYtNDZiZS1hYTM0LWRjYmNhNzllNTZhNiIsInNlY3JldCI6IjE0SUhEakFzazRUN1RlS3MwUFpWbjljV2E2MnNTM01FeDdkbVJCa3BOUjg9In0.C9_xBevXesxqo4FkUOV7eo7V3dYe5ZXweeT0cS3M_oU'
    

def encode_image_to_base64(image_path: str) -> str:
    """Encode image to base64 string"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_vlm_with_oneapi(
    api_key: str,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    image_paths: list = None,
    video_frames_base64: list = None,
):
    """
    Call VLM model using OneAPI
    
    Args:
        api_key: OneAPI key
        model_name: Model name, e.g., "gpt-4o-20241120" or "gemini-2.5-flash"
        system_prompt: System prompt
        user_prompt: User prompt
        image_paths: List of image paths (optional)
        video_frames_base64: List of pre-encoded video frames in base64 (optional)
    
    Returns:
        VLM response text
    """
    # Initialize client
    client = AzureOpenAI(
        api_key=api_key,
        api_version=AZURE_API_VERSION,
        azure_endpoint=AZURE_API_BASE,
    )
    
    # Build user message content
    content = [{"type": "text", "text": user_prompt}]
    
    # Add images if provided
    if image_paths:
        for img_path in image_paths:
            img_b64 = encode_image_to_base64(img_path)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_b64}",
                    "detail": "high"  # or "low"
                },
            })
    
    # Add video frames if provided
    if video_frames_base64:
        for frame_b64 in video_frames_base64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{frame_b64}",
                    "detail": "high"
                },
            })
    
    # Build complete messages
    messages = [
        {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
        {"role": "user", "content": content},
    ]
    
    # Call API
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
    )
    
    # Extract response text
    response_text = ""
    if response.choices and response.choices[0].message:
        response_text = response.choices[0].message.content or ""
    
    # Extract token usage (optional)
    usage = getattr(response, "usage", None)
    if usage:
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        print(f"Token usage: prompt={prompt_tokens}, completion={completion_tokens}")
    
    return response_text


# ========== Usage Example ==========
if __name__ == "__main__":
    # Get API key from environment variable
    api_key = os.getenv("ONE_API_KEY_KEWEI")
    if not api_key:
        print("Error: Please set ONE_API_KEY_KEWEI environment variable")
        exit(1)
    
    # Configure parameters
    model_name = "gemini-2.5-flash"  # or "gemini-2.5-flash"
    # model_name = "gpt-4o-20241120"  # or "gemini-2.5-flash"
    system_prompt = "You are a helpful AI assistant for video analysis."
    user_prompt = "Please describe what you see in these images."
    
    # Example 1: Using image paths
    # image_paths = ["frame1.jpg", "frame2.jpg"]
    image_paths = ["photo.jpg"]
    response = call_vlm_with_oneapi(
        api_key=api_key,
        model_name=model_name,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        image_paths=image_paths,
    )
    
    # Example 2: Using pre-encoded base64 data
    # video_frames_base64 = [base64_frame1, base64_frame2, ...]
    # response = call_vlm_with_oneapi(
    #     api_key=api_key,
    #     model_name=model_name,
    #     system_prompt=system_prompt,
    #     user_prompt=user_prompt,
    #     video_frames_base64=video_frames_base64,
    # )
    
    print("VLM Response:")
    print(response)