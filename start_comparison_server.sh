#!/bin/bash
# Quick start script for the web comparison tool

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Waymo E2E Web Comparison Tool ===${NC}"
echo ""

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}Flask not found. Installing...${NC}"
    pip install flask
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install Flask${NC}"
        exit 1
    fi
    echo -e "${GREEN}Flask installed successfully${NC}"
fi

# Get output directory
OUTPUT_DIR=${1:-.output}

if [ ! -d "$OUTPUT_DIR" ]; then
    echo -e "${RED}Output directory not found: $OUTPUT_DIR${NC}"
    exit 1
fi

# Check for runs
RUN_COUNT=$(find "$OUTPUT_DIR" -mindepth 1 -maxdepth 1 -type d ! -name ".*" | wc -l)

if [ "$RUN_COUNT" -eq 0 ]; then
    echo -e "${RED}No run directories found in $OUTPUT_DIR${NC}"
    echo -e "${YELLOW}Expected structure:${NC}"
    echo "  $OUTPUT_DIR/run_1/results/"
    echo "  $OUTPUT_DIR/run_2/results/"
    echo "  ..."
    exit 1
fi

echo -e "${GREEN}Found $RUN_COUNT run(s) in $OUTPUT_DIR${NC}"
echo ""

# Start the server
echo -e "${BLUE}Starting web server...${NC}"
echo -e "${YELLOW}Open your browser and go to: http://127.0.0.1:5000${NC}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 compare_runs_web.py --output-dir "$OUTPUT_DIR"
