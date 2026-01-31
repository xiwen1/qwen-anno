# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Key
```bash
export ONE_API_KEY_KEWEI="your_api_key_here"
```

### 3. Configure Dataset
Edit `config.yaml` and set your dataset path:
```yaml
dataset:
  path: "/path/to/waymo/dataset/training.tfrecord*"
```

### 4. Validate Setup
```bash
python validate_setup.py
```

### 5. Run Pipeline
```bash
# Test with 10 frames first
python waymo_e2e_processor.py --config config.yaml --max-frames 10

# Run full processing
python waymo_e2e_processor.py --config config.yaml
```

## Interactive Setup

For a guided setup experience:
```bash
python quickstart.py
```

This will:
- Check your environment
- Validate dependencies
- Configure dataset path
- Choose image processing mode
- Select VLM model
- Run a test with sample data

## Common Commands

### Monitor Progress
```bash
# Real-time monitoring
python monitor.py --output-dir ./output --interval 5

# Check logs
tail -f output/processing.log

# View checkpoint
cat output/checkpoint.json | python -m json.tool
```

### Analyze Results
```bash
# Generate analysis report
python analyze_results.py output/results

# Export to CSV
python export_results.py output/results --format csv

# Export to JSONL
python export_results.py output/results --format jsonl

# Export statistics
python export_results.py output/results --format stats
```

### Merge Multiple Runs
```bash
python merge_results.py ./merged_output ./output1/results ./output2/results
```

### Resume Processing
```bash
python waymo_e2e_processor.py --config config.yaml --resume
```

## Image Processing Modes

### Separate Mode (Default)
Three separate images sent to VLM:
```yaml
image_processing:
  input_mode: "separate"
```

### Concatenated Mode
Single horizontally-concatenated image:
```yaml
image_processing:
  input_mode: "concatenated"
```

## VLM Model Selection

### Fast Model (Recommended)
```yaml
vlm_api:
  model_name: "gemini-2.5-flash"
```

### Powerful Model
```yaml
vlm_api:
  model_name: "gpt-4o-20241120"
```

### Advanced Model
```yaml
vlm_api:
  model_name: "gemini-3-pro"
```

## Performance Tuning

### For Faster Processing
```yaml
processing:
  checkpoint_interval: 50  # Save less frequently

image_processing:
  jpeg_quality: 80  # Reduce quality

vlm_api:
  retry_delay_seconds: 1.0  # Faster retries
```

### For Limited Resources
```yaml
image_processing:
  jpeg_quality: 70  # Lower quality
  target_height: 384  # Smaller images (not recommended)

processing:
  max_frames: 100  # Process in batches
```

### For Stability
```yaml
vlm_api:
  max_retries: 5  # More retries
  retry_delay_seconds: 5.0  # Longer delays
  timeout_seconds: 180  # Longer timeout
```

## Troubleshooting

### API Key Error
```bash
# Set API key
export ONE_API_KEY_KEWEI="your_api_key_here"

# Verify it's set
echo $ONE_API_KEY_KEWEI
```

### Dataset Not Found
```bash
# Check dataset path
ls /path/to/waymo/dataset/training.tfrecord*

# Update config.yaml with correct path
nano config.yaml
```

### Out of Memory
```bash
# Reduce image quality in config.yaml
image_processing:
  jpeg_quality: 60
```

### API Rate Limiting
```bash
# Increase retry delay in config.yaml
vlm_api:
  retry_delay_seconds: 5.0
```

## Next Steps

1. **Read the full documentation**: See `README.md`
2. **Review deployment guide**: See `DEPLOYMENT.md`
3. **Check examples**: Run `python examples.py`
4. **Monitor processing**: Run `python monitor.py`
5. **Analyze results**: Run `python analyze_results.py output/results`

## Support

- **Setup validation**: `python validate_setup.py`
- **Usage examples**: `python examples.py`
- **Results analysis**: `python analyze_results.py output/results`
- **Real-time monitoring**: `python monitor.py`
- **Documentation**: See `README.md` and `DEPLOYMENT.md`
