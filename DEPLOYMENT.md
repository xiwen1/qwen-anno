# Deployment Guide for Waymo E2E Pipeline

## Overview

This guide provides instructions for deploying the Waymo E2E dataset processing pipeline on a remote server.

## Prerequisites

- Python 3.8+
- Access to Waymo E2E dataset (TFRecord files)
- API key for VLM service (OneAPI)
- Sufficient disk space for output results

## Deployment Steps

### 1. Prepare Remote Server

```bash
# SSH into remote server
ssh user@remote-server

# Create working directory
mkdir -p /data/waymo-e2e-processing
cd /data/waymo-e2e-processing

# Clone or copy the pipeline code
# Option A: Clone from repository
git clone <repository-url> .

# Option B: Copy files
scp -r /local/path/to/pipeline/* user@remote-server:/data/waymo-e2e-processing/
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python validate_setup.py
```

### 3. Configure Environment

```bash
# Set API key
export ONE_API_KEY_KEWEI="your_api_key_here"

# Make it persistent (add to ~/.bashrc or ~/.zshrc)
echo 'export ONE_API_KEY_KEWEI="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Configure Dataset Path

Edit `config.yaml` to set the correct dataset path:

```yaml
dataset:
  path: "/path/to/waymo/dataset/training.tfrecord*"
  sampling_frequency_hz: 1
```

### 5. Adjust Configuration for Remote Server

Optimize configuration based on server resources:

```yaml
# For high-performance servers
processing:
  checkpoint_interval: 50  # Save less frequently
  max_workers: 1  # Keep at 1 for API rate limiting

# For limited resources
image_processing:
  jpeg_quality: 80  # Reduce quality to save space
  target_height: 512  # Keep at 512 as per requirements

# For faster processing
vlm_api:
  retry_delay_seconds: 1.0  # Reduce retry delay
  timeout_seconds: 120  # Increase timeout for slow networks
```

### 6. Run Pipeline

#### Option A: Direct Execution

```bash
# Run with default configuration
python waymo_e2e_processor.py --config config.yaml

# Run with specific parameters
python waymo_e2e_processor.py \
    --config config.yaml \
    --max-frames 1000 \
    --log-level INFO
```

#### Option B: Background Execution (Recommended)

```bash
# Using nohup
nohup python waymo_e2e_processor.py --config config.yaml > pipeline.log 2>&1 &

# Using screen
screen -S waymo-pipeline
python waymo_e2e_processor.py --config config.yaml
# Detach: Ctrl+A, then D

# Using tmux
tmux new-session -d -s waymo-pipeline
tmux send-keys -t waymo-pipeline "python waymo_e2e_processor.py --config config.yaml" Enter
```

#### Option C: Scheduled Execution (cron)

```bash
# Edit crontab
crontab -e

# Add entry to run daily at 2 AM
0 2 * * * cd /data/waymo-e2e-processing && python waymo_e2e_processor.py --config config.yaml >> cron.log 2>&1
```

### 7. Monitor Progress

```bash
# Check logs in real-time
tail -f output/processing.log

# Check output directory
ls -lh output/results/ | head -20

# Check checkpoint
cat output/checkpoint.json | python -m json.tool

# Analyze results
python analyze_results.py output/results
```

### 8. Resume Processing

If processing is interrupted:

```bash
# Resume from checkpoint
python waymo_e2e_processor.py --config config.yaml --resume

# Or with specific parameters
python waymo_e2e_processor.py \
    --config config.yaml \
    --resume \
    --log-level DEBUG
```

## Performance Optimization

### 1. Parallel Processing on Multiple Machines

Process different dataset shards on different machines:

```bash
# Machine 1: Process first 5000 frames
python waymo_e2e_processor.py \
    --config config.yaml \
    --max-frames 5000

# Machine 2: Process next 5000 frames
# (Modify dataset path to point to different shard)
python waymo_e2e_processor.py \
    --config config.yaml \
    --max-frames 5000 \
    --dataset-path "/path/to/dataset/shard2.tfrecord*"
```

### 2. Optimize Image Processing

```yaml
image_processing:
  target_height: 512  # Keep as required
  jpeg_quality: 85    # Balance quality and size
  input_mode: "concatenated"  # Faster than separate
```

### 3. Adjust Checkpoint Interval

```yaml
processing:
  checkpoint_interval: 50  # Save every 50 frames instead of 10
```

### 4. Increase Retry Delays

```yaml
vlm_api:
  retry_delay_seconds: 1.0  # Reduce from 2.0
  max_retries: 2  # Reduce from 3 if API is stable
```

## Troubleshooting

### Issue: Out of Memory

```bash
# Reduce image quality
# Edit config.yaml:
image_processing:
  jpeg_quality: 70

# Or reduce target height (not recommended)
image_processing:
  target_height: 384
```

### Issue: API Rate Limiting

```bash
# Increase retry delay
vlm_api:
  retry_delay_seconds: 5.0

# Or reduce max_frames to process in smaller batches
processing:
  max_frames: 100
```

### Issue: Disk Space

```bash
# Check available space
df -h

# Archive old results
tar -czf results_backup_$(date +%Y%m%d).tar.gz output/results/
rm -rf output/results/*

# Resume processing
python waymo_e2e_processor.py --config config.yaml --resume
```

### Issue: Network Timeout

```bash
# Increase timeout
vlm_api:
  timeout_seconds: 180

# Increase retry delay
vlm_api:
  retry_delay_seconds: 5.0
```

## Monitoring and Maintenance

### 1. Set Up Log Rotation

```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/waymo-pipeline > /dev/null <<EOF
/data/waymo-e2e-processing/output/processing.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 user user
}
EOF
```

### 2. Monitor Disk Usage

```bash
# Check output directory size
du -sh output/

# Monitor in real-time
watch -n 60 'du -sh output/'
```

### 3. Generate Reports

```bash
# Analyze results periodically
python analyze_results.py output/results > results_report.txt

# Check processing statistics
cat output/summary.json | python -m json.tool
```

## Data Transfer

### Transfer Results Back to Local Machine

```bash
# Copy all results
scp -r user@remote-server:/data/waymo-e2e-processing/output/results ./results_remote

# Copy specific results
scp user@remote-server:/data/waymo-e2e-processing/output/summary.json ./

# Use rsync for efficient transfer
rsync -avz user@remote-server:/data/waymo-e2e-processing/output/results/ ./results_remote/
```

## Cleanup

### After Processing Completes

```bash
# Archive results
tar -czf results_final_$(date +%Y%m%d).tar.gz output/results/

# Remove temporary files
rm -rf output/results/*.tmp

# Keep checkpoint for reference
cp output/checkpoint.json checkpoint_final.json

# Clean up logs
gzip output/processing.log
```

## Best Practices

1. **Always use checkpoint system**: Enables resuming from any point
2. **Monitor logs regularly**: Catch issues early
3. **Test with small dataset first**: Verify setup with `--max-frames 10`
4. **Use background execution**: Prevents interruption from SSH disconnection
5. **Archive results regularly**: Prevent data loss
6. **Document configuration**: Keep track of settings used
7. **Version control**: Track changes to configuration and code

## Support

For issues during deployment:
1. Check `output/processing.log` for detailed error messages
2. Run `python validate_setup.py` to verify setup
3. Test with small dataset: `python waymo_e2e_processor.py --config config.yaml --max-frames 10`
4. Review configuration in `config.yaml`
5. Check API key and network connectivity
