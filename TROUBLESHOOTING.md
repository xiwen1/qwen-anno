# Troubleshooting FAQ

## Installation and Setup Issues

### Q: "ModuleNotFoundError: No module named 'tensorflow'"
**A:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Q: "ModuleNotFoundError: No module named 'waymo_open_dataset'"
**A:** The Waymo SDK is already installed. If missing, install it:
```bash
pip install waymo-open-dataset-tf-2-12-0==1.6.7
```

### Q: "Environment variable ONE_API_KEY_KEWEI not set"
**A:** Set the API key:
```bash
export ONE_API_KEY_KEWEI="your_api_key_here"
```

Make it persistent by adding to `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export ONE_API_KEY_KEWEI="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### Q: "Configuration file not found: config.yaml"
**A:** Create a configuration file:
```bash
# Copy the default config
cp config.yaml config_custom.yaml

# Edit with your settings
nano config_custom.yaml

# Run with custom config
python waymo_e2e_processor.py --config config_custom.yaml
```

## Dataset and File Issues

### Q: "No files found matching pattern: /path/to/dataset"
**A:** Verify the dataset path:
```bash
# Check if files exist
ls /path/to/waymo/dataset/training.tfrecord*

# Update config.yaml with correct path
nano config.yaml
```

### Q: "Failed to parse E2EDFrame"
**A:** This is a warning for corrupted frames. The pipeline will skip them. Check logs:
```bash
tail -f output/processing.log
```

### Q: "Disk full" error
**A:** Free up disk space:
```bash
# Check disk usage
df -h

# Archive old results
python cleanup.py --archive

# Remove old results
python cleanup.py --cleanup
```

## API and VLM Issues

### Q: "VLM API call failed: 401 Unauthorized"
**A:** API key is invalid or expired:
```bash
# Verify API key
echo $ONE_API_KEY_KEWEI

# Update with new key
export ONE_API_KEY_KEWEI="new_api_key_here"
```

### Q: "VLM API call failed: 429 Too Many Requests"
**A:** Rate limiting. Increase retry delay:
```yaml
# In config.yaml
vlm_api:
  retry_delay_seconds: 5.0  # Increase from 2.0
  max_retries: 5  # Increase from 3
```

### Q: "VLM API call failed: 500 Internal Server Error"
**A:** Server error. The pipeline will retry automatically. If persistent:
```bash
# Check API status
# Try again later
python waymo_e2e_processor.py --config config.yaml --resume
```

### Q: "VLM API call failed: timeout"
**A:** Increase timeout:
```yaml
# In config.yaml
vlm_api:
  timeout_seconds: 120  # Increase from 60
```

### Q: "Failed to parse VLM response as JSON"
**A:** VLM returned invalid JSON. Check logs:
```bash
tail -f output/processing.log | grep "VLM response"
```

The frame will be skipped and logged. Check the raw response in logs.

## Processing Issues

### Q: "Out of memory" error
**A:** Reduce image quality or size:
```yaml
# In config.yaml
image_processing:
  jpeg_quality: 60  # Reduce from 90
  target_height: 384  # Reduce from 512 (not recommended)
```

Or process fewer frames at a time:
```bash
python waymo_e2e_processor.py --config config.yaml --max-frames 100
```

### Q: "Processing is very slow"
**A:** Optimize configuration:
```yaml
# In config.yaml
image_processing:
  input_mode: "concatenated"  # Faster than separate
  jpeg_quality: 80  # Lower quality

processing:
  checkpoint_interval: 50  # Save less frequently

vlm_api:
  model_name: "gemini-2.5-flash"  # Faster model
  retry_delay_seconds: 1.0  # Shorter delay
```

### Q: "Processing stopped unexpectedly"
**A:** Check logs and resume:
```bash
# Check logs
tail -100 output/processing.log

# Resume from checkpoint
python waymo_e2e_processor.py --config config.yaml --resume
```

### Q: "Checkpoint file is corrupted"
**A:** Delete and restart:
```bash
# Remove corrupted checkpoint
rm output/checkpoint.json

# Restart processing (will reprocess from beginning)
python waymo_e2e_processor.py --config config.yaml
```

## Output and Results Issues

### Q: "No results files created"
**A:** Check if processing started:
```bash
# Check logs
cat output/processing.log

# Check checkpoint
cat output/checkpoint.json

# Verify dataset path
grep "path:" config.yaml
```

### Q: "Results files are empty or incomplete"
**A:** Processing may still be running:
```bash
# Monitor progress
python monitor.py

# Check logs
tail -f output/processing.log
```

### Q: "Results validation fails"
**A:** Check result structure:
```bash
# Validate results
python validate_results.py output/results

# Check specific result
cat output/results/frame_name.json | python -m json.tool
```

### Q: "Cannot export results to CSV"
**A:** Check if results exist:
```bash
# List results
ls output/results/ | head

# Export with error details
python export_results.py output/results --format csv 2>&1 | head -20
```

## Monitoring and Analysis Issues

### Q: "Monitor script shows no data"
**A:** Processing may not have started:
```bash
# Check if pipeline is running
ps aux | grep waymo_e2e_processor

# Check logs
tail output/processing.log

# Check checkpoint
cat output/checkpoint.json
```

### Q: "Analysis script shows no results"
**A:** Results may not exist yet:
```bash
# Check results directory
ls output/results/ | wc -l

# Wait for processing to complete
python monitor.py
```

### Q: "Report generation fails"
**A:** Check results format:
```bash
# Validate results first
python validate_results.py output/results

# Generate report with error details
python generate_report.py output/results report.txt 2>&1
```

## Remote Server Issues

### Q: "SSH connection drops during processing"
**A:** Use background execution:
```bash
# Option 1: nohup
nohup python waymo_e2e_processor.py --config config.yaml > pipeline.log 2>&1 &

# Option 2: screen
screen -S waymo-pipeline
python waymo_e2e_processor.py --config config.yaml
# Detach: Ctrl+A, then D

# Option 3: tmux
tmux new-session -d -s waymo-pipeline
tmux send-keys -t waymo-pipeline "python waymo_e2e_processor.py --config config.yaml" Enter
```

### Q: "Cannot transfer results back to local machine"
**A:** Use rsync or scp:
```bash
# Copy all results
scp -r user@remote:/path/to/output/results ./results_remote

# Or use rsync (more efficient)
rsync -avz user@remote:/path/to/output/results/ ./results_remote/
```

### Q: "Remote server runs out of disk space"
**A:** Archive and clean up:
```bash
# On remote server
python cleanup.py --archive
python cleanup.py --cleanup

# Transfer archive to local
scp user@remote:/path/to/results_archive_*.tar.gz ./
```

## Performance Tuning

### Q: "How to make processing faster?"
**A:** Optimize configuration:
```yaml
# Use fast model
vlm_api:
  model_name: "gemini-2.5-flash"

# Use concatenated images
image_processing:
  input_mode: "concatenated"
  jpeg_quality: 80

# Save checkpoint less frequently
processing:
  checkpoint_interval: 50

# Reduce retry delays
vlm_api:
  retry_delay_seconds: 1.0
  max_retries: 2
```

### Q: "How to improve result quality?"
**A:** Optimize for quality:
```yaml
# Use powerful model
vlm_api:
  model_name: "gpt-4o-20241120"

# Use separate images
image_processing:
  input_mode: "separate"
  jpeg_quality: 95

# More retries
vlm_api:
  max_retries: 5
  retry_delay_seconds: 3.0
```

### Q: "How to balance speed and quality?"
**A:** Use balanced configuration:
```bash
python generate_configs.py balanced
python waymo_e2e_processor.py --config config_balanced.yaml
```

## Debugging

### Q: "How to enable debug logging?"
**A:** Set log level to DEBUG:
```bash
python waymo_e2e_processor.py --config config.yaml --log-level DEBUG
```

Or in config.yaml:
```yaml
logging:
  level: "DEBUG"
```

### Q: "How to see detailed error messages?"
**A:** Check logs:
```bash
# View all errors
grep ERROR output/processing.log

# View last 50 lines
tail -50 output/processing.log

# Search for specific error
grep "specific_error" output/processing.log
```

### Q: "How to test with sample data?"
**A:** Run examples:
```bash
# Run usage examples
python examples.py

# Test with small dataset
python waymo_e2e_processor.py --config config.yaml --max-frames 10
```

## Getting Help

### Diagnostic Steps
1. Run validation: `python validate_setup.py`
2. Check logs: `tail -f output/processing.log`
3. Verify config: `cat config.yaml`
4. Check environment: `echo $ONE_API_KEY_KEWEI`
5. Test with sample: `python examples.py`

### Information to Provide When Asking for Help
- Error message (full text)
- Last 50 lines of log file
- Configuration file (with sensitive data removed)
- Output of `python validate_setup.py`
- Steps to reproduce the issue

### Resources
- README.md - Main documentation
- QUICKSTART.md - Quick start guide
- DEPLOYMENT.md - Deployment guide
- FILE_INDEX.md - File organization
- PROJECT_COMPLETION_REPORT.md - Project overview

## Common Solutions Summary

| Issue | Solution |
|-------|----------|
| API key not found | `export ONE_API_KEY_KEWEI="key"` |
| Dataset not found | Update `config.yaml` with correct path |
| Out of memory | Reduce `jpeg_quality` or `max_frames` |
| Rate limiting | Increase `retry_delay_seconds` |
| Slow processing | Use `concatenated` mode and fast model |
| Processing stopped | Run with `--resume` flag |
| Disk full | Run `python cleanup.py --archive` |
| SSH disconnected | Use `nohup`, `screen`, or `tmux` |
| Results validation fails | Run `python validate_results.py` |
| No results created | Check logs and verify dataset path |

---

**Last Updated**: 2026-01-31

**Version**: 1.0.0
