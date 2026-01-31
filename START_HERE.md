# Waymo E2E Dataset Processing Pipeline

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API key
export ONE_API_KEY_KEWEI="your_api_key_here"

# 3. Configure dataset
nano config.yaml  # Set your dataset path

# 4. Validate setup
python validate_setup.py

# 5. Run pipeline
python waymo_e2e_processor.py --config config.yaml
```

## 📋 What's Included

### Core Pipeline
- **waymo_e2e_processor.py** - Main pipeline orchestrator
- **src/** - 8 core processing modules
- **config.yaml** - Configuration template

### Documentation
- **README.md** - Comprehensive guide
- **QUICKSTART.md** - 5-minute setup
- **DEPLOYMENT.md** - Remote server setup
- **TROUBLESHOOTING.md** - FAQ and solutions
- **FILE_INDEX.md** - Complete file reference

### Helper Scripts
- **validate_setup.py** - Verify environment
- **quickstart.py** - Interactive setup wizard
- **monitor.py** - Real-time monitoring
- **analyze_results.py** - Results analysis
- **generate_report.py** - Report generation
- **export_results.py** - Export to CSV/JSONL
- **validate_results.py** - Results validation
- **merge_results.py** - Merge multiple runs
- **cleanup.py** - Archive and cleanup
- **compare_results.py** - Compare runs
- **deployment_checklist.py** - Pre-deployment check
- **generate_configs.py** - Config generation
- **examples.py** - Usage examples

## 🎯 Key Features

✅ **1Hz Sampling** - Extract frames at 1Hz from 10Hz dataset
✅ **Dual Image Modes** - Separate or concatenated images
✅ **Robust Error Handling** - Graceful frame skipping and retries
✅ **Checkpoint System** - Resume from any point
✅ **VLM Integration** - Support for multiple models
✅ **Comprehensive Logging** - Detailed monitoring
✅ **Production Ready** - Error handling, validation, testing

## 📊 Project Statistics

- **3,500+** lines of code
- **1,500+** lines of documentation
- **30+** files
- **8** core modules
- **13** helper scripts
- **5** documentation files

## 🔧 Configuration

### Image Processing Modes
```yaml
# Separate images (default)
image_processing:
  input_mode: "separate"

# Concatenated image
image_processing:
  input_mode: "concatenated"
```

### VLM Models
```yaml
vlm_api:
  model_name: "gemini-2.5-flash"      # Fast
  # or "gpt-4o-20241120"              # Powerful
  # or "gemini-3-pro"                 # Advanced
```

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| README.md | Main documentation and usage guide |
| QUICKSTART.md | 5-minute setup and common commands |
| DEPLOYMENT.md | Remote server deployment guide |
| TROUBLESHOOTING.md | FAQ and solutions |
| FILE_INDEX.md | Complete file reference |
| PROJECT_COMPLETION_REPORT.md | Project overview |

## 🛠️ Common Commands

```bash
# Setup and validation
python validate_setup.py              # Validate environment
python quickstart.py                  # Interactive setup
python deployment_checklist.py        # Pre-deployment check

# Configuration
python generate_configs.py fast       # Generate fast config
python generate_configs.py quality    # Generate quality config

# Monitoring
python monitor.py                     # Real-time monitoring
tail -f output/processing.log         # View logs

# Analysis
python analyze_results.py output/results
python generate_report.py output/results
python validate_results.py output/results

# Export and merge
python export_results.py output/results --format csv
python merge_results.py ./merged output1/results output2/results

# Maintenance
python cleanup.py --archive           # Archive results
python cleanup.py --cleanup           # Clean up
python compare_results.py dir1 dir2   # Compare runs
```

## 🚀 Deployment

### Local Testing
```bash
python waymo_e2e_processor.py --config config.yaml --max-frames 10
```

### Full Processing
```bash
python waymo_e2e_processor.py --config config.yaml
```

### Remote Server
```bash
# Copy to remote
scp -r . user@remote:/path/to/pipeline/

# On remote server
pip install -r requirements.txt
export ONE_API_KEY_KEWEI="your_key"
nano config.yaml
python waymo_e2e_processor.py --config config.yaml
```

### Background Execution
```bash
# Using nohup
nohup python waymo_e2e_processor.py --config config.yaml > pipeline.log 2>&1 &

# Using screen
screen -S waymo-pipeline
python waymo_e2e_processor.py --config config.yaml

# Using tmux
tmux new-session -d -s waymo-pipeline
tmux send-keys -t waymo-pipeline "python waymo_e2e_processor.py --config config.yaml" Enter
```

## 📊 Output Format

Each processed frame generates a JSON file with:
- **metadata**: Frame info and processing details
- **input_data**: Trajectories and ego status
- **vlm_response**: VLM annotations (critical objects, explanation, behavior)

## ⚙️ Performance

- **Per-frame time**: 3-6 seconds
- **For 10,000 frames**: ~8-17 hours
- **Memory usage**: ~500MB-1GB
- **Disk usage**: ~1-2GB per 1000 frames

## 🔍 Troubleshooting

### API Key Error
```bash
export ONE_API_KEY_KEWEI="your_api_key_here"
```

### Dataset Not Found
```bash
# Update config.yaml with correct path
nano config.yaml
```

### Out of Memory
```yaml
# Reduce image quality in config.yaml
image_processing:
  jpeg_quality: 60
```

### Rate Limiting
```yaml
# Increase retry delay in config.yaml
vlm_api:
  retry_delay_seconds: 5.0
```

See **TROUBLESHOOTING.md** for more solutions.

## 📚 Documentation Structure

```
Documentation/
├── README.md                    # Main guide (this file)
├── QUICKSTART.md               # 5-minute setup
├── DEPLOYMENT.md               # Remote deployment
├── TROUBLESHOOTING.md          # FAQ and solutions
├── FILE_INDEX.md               # File reference
└── PROJECT_COMPLETION_REPORT.md # Project overview
```

## 🎓 Examples

Run usage examples:
```bash
python examples.py
```

Examples include:
1. Basic pipeline usage
2. Image processing modes
3. Trajectory extraction
4. Prompt building
5. Output handling

## ✅ Pre-Deployment Checklist

```bash
python deployment_checklist.py
```

Verifies:
- All files present
- Configuration valid
- Environment setup
- Dependencies installed
- Waymo SDK available

## 📞 Support

### Getting Help
1. Check **TROUBLESHOOTING.md** for common issues
2. Run `python validate_setup.py` to diagnose problems
3. Review logs in `output/processing.log`
4. Check configuration in `config.yaml`

### Diagnostic Tools
- `python validate_setup.py` - Environment validation
- `python examples.py` - Usage examples
- `python validate_results.py` - Results validation
- `python monitor.py` - Real-time monitoring

## 🎯 Next Steps

1. **Read Documentation**
   - Start with README.md (this file)
   - Follow QUICKSTART.md for setup

2. **Validate Setup**
   ```bash
   python validate_setup.py
   ```

3. **Configure**
   ```bash
   nano config.yaml
   ```

4. **Test**
   ```bash
   python waymo_e2e_processor.py --config config.yaml --max-frames 10
   ```

5. **Deploy**
   ```bash
   python waymo_e2e_processor.py --config config.yaml
   ```

6. **Monitor**
   ```bash
   python monitor.py
   ```

7. **Analyze**
   ```bash
   python analyze_results.py output/results
   ```

## 📋 Project Information

- **Status**: ✅ Complete and Ready for Deployment
- **Version**: 1.0.0
- **Last Updated**: 2026-01-31
- **Total Lines**: 5,000+
- **Files**: 30+
- **Modules**: 8
- **Scripts**: 13

## 📄 License

This pipeline uses the Waymo Open Dataset, which is licensed under the Apache License 2.0.

## 🙏 Acknowledgments

- Waymo Open Dataset team
- Poutine paper authors
- OpenAI/Azure for VLM APIs

---

**Ready to get started?** Follow the Quick Start section above or read QUICKSTART.md for detailed instructions.

**Questions?** Check TROUBLESHOOTING.md or run `python validate_setup.py` for diagnostics.

**Deploying to remote server?** See DEPLOYMENT.md for detailed instructions.
