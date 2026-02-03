#!/usr/bin/env python3
"""
Web-based visualization tool for comparing multiple processing runs.
Allows side-by-side comparison of images and VLM outputs across different runs.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import base64
from flask import Flask, render_template_string, request, jsonify

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Waymo E2E Processing Runs Comparison</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }

        .header p {
            opacity: 0.9;
            font-size: 14px;
        }

        .controls {
            background: white;
            padding: 20px;
            margin: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .control-group {
            margin-bottom: 15px;
        }

        .control-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #555;
        }

        select, input[type="text"], input[type="number"] {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            width: 100%;
            max-width: 400px;
        }

        select:focus, input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }

        button {
            padding: 10px 20px;
            background-color: #667eea;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: background-color 0.3s;
        }

        button:hover {
            background-color: #5568d3;
        }

        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .stat-label {
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: 5px;
        }

        .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }

        .comparison-container {
            margin: 20px;
        }

        .frame-card {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }

        .frame-header {
            background: #f9f9f9;
            padding: 15px;
            border-bottom: 2px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .frame-title {
            font-weight: 600;
            font-size: 16px;
            color: #333;
        }

        .frame-meta {
            font-size: 12px;
            color: #999;
        }

        .frame-content {
            padding: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }

        .run-column {
            border: 1px solid #eee;
            border-radius: 4px;
            padding: 15px;
            background: #fafafa;
        }

        .run-title {
            font-weight: 600;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
            color: #667eea;
        }

        .image-container {
            width: 100%;
            max-height: 400px;
            background: #000;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .image-container img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }

        .cot-content {
            background: white;
            padding: 12px;
            border-radius: 4px;
            border-left: 4px solid #667eea;
            font-size: 13px;
            line-height: 1.6;
            max-height: 300px;
            overflow-y: auto;
        }

        .cot-label {
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }

        .metadata {
            font-size: 11px;
            color: #999;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #eee;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #999;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .error {
            background-color: #fee;
            color: #c00;
            padding: 15px;
            border-radius: 4px;
            margin: 20px;
            border-left: 4px solid #c00;
        }

        .tabs {
            display: flex;
            gap: 0;
            margin-bottom: 20px;
            border-bottom: 2px solid #ddd;
        }

        .tab {
            padding: 12px 20px;
            background: none;
            border: none;
            cursor: pointer;
            font-weight: 600;
            color: #999;
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
            transition: all 0.3s;
        }

        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .scene-comparison {
            margin: 20px 0;
        }

        .comparison-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }

        .info-box {
            background: #eef;
            border-left: 4px solid #667eea;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-size: 13px;
            line-height: 1.6;
        }

        @media (max-width: 768px) {
            .frame-content {
                grid-template-columns: 1fr;
            }

            .comparison-grid {
                grid-template-columns: 1fr;
            }

            .button-group {
                flex-direction: column;
            }

            button {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚗 Waymo E2E Processing Runs Comparison</h1>
        <p>Compare images and VLM outputs across multiple processing runs</p>
    </div>

    <div class="controls">
        <h2>Configuration</h2>

        <div class="control-group">
            <label>Select Runs:</label>
            <div id="runSelectors"></div>
        </div>

        <div class="button-group">
            <button onclick="loadComparison()">Load Comparison</button>
            <button onclick="clearComparison()">Clear</button>
        </div>

        <div class="info-box" id="infoBox" style="display: none;"></div>

        <div id="stats" class="stats" style="display: none;"></div>
    </div>

    <div id="content"></div>

    <script>
        let availableRuns = {{ runs_json | safe }};
        let commonFrames = {{ common_frames_json | safe }};

        function initializeRunSelectors() {
            const container = document.getElementById('runSelectors');
            availableRuns.forEach((run, index) => {
                const label = document.createElement('label');
                label.style.display = 'inline-block';
                label.style.marginRight = '20px';
                label.style.marginBottom = '10px';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.value = run;
                checkbox.id = `run-${run}`;
                checkbox.checked = index < 3; // Check first 3 by default

                const labelText = document.createElement('span');
                labelText.textContent = run;
                labelText.style.marginLeft = '8px';

                label.appendChild(checkbox);
                label.appendChild(labelText);
                container.appendChild(label);
            });
        }

        function loadComparison() {
            const selectedRuns = Array.from(
                document.querySelectorAll('input[id^="run-"]:checked')
            ).map(cb => cb.value);

            if (selectedRuns.length < 1) {
                alert('Please select at least one run');
                return;
            }

            const content = document.getElementById('content');
            content.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading comparison data...</p></div>';

            fetch('/api/comparison', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({runs: selectedRuns})
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    content.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                    return;
                }

                renderComparison(data, selectedRuns);

                // Show stats
                const statsDiv = document.getElementById('stats');
                statsDiv.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-label">Common Frames</div>
                        <div class="stat-value">${data.frames.length}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Selected Runs</div>
                        <div class="stat-value">${selectedRuns.length}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Unique Scenes</div>
                        <div class="stat-value">${new Set(data.frames.map(f => f.split('-')[0])).size}</div>
                    </div>
                `;
                statsDiv.style.display = 'grid';

                // Show info
                const infoBox = document.getElementById('infoBox');
                infoBox.innerHTML = `
                    <strong>Selected Runs:</strong> ${selectedRuns.join(', ')}<br>
                    <strong>Common Frames:</strong> ${data.frames.length}<br>
                    <strong>Comparison Type:</strong> Side-by-side image and VLM output comparison
                `;
                infoBox.style.display = 'block';
            })
            .catch(err => {
                content.innerHTML = `<div class="error">Error loading data: ${err.message}</div>`;
            });
        }

        function renderComparison(data, runs) {
            const content = document.getElementById('content');
            content.innerHTML = '';

            if (data.frames.length === 0) {
                content.innerHTML = '<div class="error">No common frames found across selected runs</div>';
                return;
            }

            data.frames.forEach((frameName, index) => {
                const frameCard = document.createElement('div');
                frameCard.className = 'frame-card';

                const frameHeader = document.createElement('div');
                frameHeader.className = 'frame-header';
                frameHeader.innerHTML = `
                    <div>
                        <div class="frame-title">${index + 1}. ${frameName}</div>
                        <div class="frame-meta">Scene: ${frameName.split('-')[0].substring(0, 8)}... | Frame ID: ${frameName.split('-')[1]}</div>
                    </div>
                    <div class="frame-meta">${index + 1} / ${data.frames.length}</div>
                `;

                const frameContent = document.createElement('div');
                frameContent.className = 'frame-content';

                runs.forEach(run => {
                    const frameData = data.data[run]?.[frameName];
                    if (frameData) {
                        const column = document.createElement('div');
                        column.className = 'run-column';

                        column.innerHTML = `
                            <div class="run-title">📊 ${run}</div>

                            <div class="image-container" id="img-${run}">
                                <img src="data:image/jpeg;base64,${frameData.image}" alt="Image for ${run}">
                            </div>

                            <div>
                                <div class="cot-label">Chain-of-Thought Analysis</div>
                                <div class="cot-content">
                                    ${frameData.vlm_response ? renderVLMResponse(frameData.vlm_response) : '<em>No VLM response</em>'}
                                </div>
                            </div>

                            <div class="metadata">
                                <strong>Timestamp:</strong> ${frameData.timestamp || 'N/A'}<br>
                                <strong>Model:</strong> ${frameData.model || 'N/A'}<br>
                                <strong>Status:</strong> ✓ Processed
                            </div>
                        `;

                        frameContent.appendChild(column);
                    }
                });

                frameCard.appendChild(frameHeader);
                frameCard.appendChild(frameContent);
                content.appendChild(frameCard);
            });
        }

        function renderVLMResponse(response) {
            if (typeof response === 'string') {
                return `<pre>${response}</pre>`;
            } else if (typeof response === 'object') {
                if (response.explanation) {
                    return `
                        <div><strong>Explanation:</strong></div>
                        <p>${response.explanation}</p>
                        ${response.meta_behaviour ? `
                            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd;">
                                <strong>Behavior:</strong><br>
                                Speed: ${response.meta_behaviour.speed}<br>
                                Command: ${response.meta_behaviour.command}
                            </div>
                        ` : ''}
                    `;
                }
                return `<pre>${JSON.stringify(response, null, 2)}</pre>`;
            }
            return '<em>Invalid response format</em>';
        }

        function clearComparison() {
            document.getElementById('content').innerHTML = '';
            document.getElementById('stats').style.display = 'none';
            document.getElementById('infoBox').style.display = 'none';
        }

        // Initialize on load
        document.addEventListener('DOMContentLoaded', initializeRunSelectors);
    </script>
</body>
</html>
"""


@dataclass
class RunInfo:
    name: str
    path: Path
    results_dir: Path
    images_dir: Path
    processing_order_path: Path


class ComparisonServer:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.runs: Dict[str, RunInfo] = {}
        self.app = Flask(__name__)
        self._setup_routes()
        self._discover_runs()

    def _discover_runs(self):
        """Discover available runs in output directory."""
        if not self.output_dir.exists():
            print(f"Output directory not found: {self.output_dir}")
            return

        for run_path in self.output_dir.iterdir():
            if run_path.is_dir():
                results_dir = run_path / "results"
                images_dir = run_path / "images"
                processing_order = run_path / "processing_order.json"

                if results_dir.exists():
                    self.runs[run_path.name] = RunInfo(
                        name=run_path.name,
                        path=run_path,
                        results_dir=results_dir,
                        images_dir=images_dir,
                        processing_order_path=processing_order
                    )

    def _get_common_frames(self, selected_runs: List[str]) -> List[str]:
        """Find frames common to all selected runs."""
        if not selected_runs:
            return []

        frame_sets = []
        for run_name in selected_runs:
            if run_name not in self.runs:
                continue

            run = self.runs[run_name]
            result_files = set(
                f.stem for f in run.results_dir.glob("*.json")
                if f.name != "processing_order.json"
            )
            frame_sets.append(result_files)

        if not frame_sets:
            return []

        # Intersection of all frame sets
        common = frame_sets[0]
        for frame_set in frame_sets[1:]:
            common &= frame_set

        return sorted(list(common))

    def _load_frame_data(self, run_name: str, frame_name: str) -> Optional[Dict]:
        """Load frame data including images and VLM response."""
        run = self.runs.get(run_name)
        if not run:
            return None

        result_file = run.results_dir / f"{frame_name}.json"
        if not result_file.exists():
            return None

        try:
            with open(result_file) as f:
                result = json.load(f)

            data = {
                "vlm_response": result.get("vlm_response"),
                "timestamp": result.get("metadata", {}).get("timestamp_micros"),
                "model": result.get("metadata", {}).get("model_name"),
            }

            # Load image
            if run.images_dir.exists():
                # Try to find the first image for this frame
                frame_images = run.images_dir / frame_name
                if frame_images.exists():
                    images = list(frame_images.glob("*.jpg"))
                    if images:
                        with open(images[0], "rb") as img_file:
                            data["image"] = base64.b64encode(img_file.read()).decode()

            return data
        except Exception as e:
            print(f"Error loading frame data for {run_name}/{frame_name}: {e}")
            return None

    def _setup_routes(self):
        @self.app.route("/")
        def index():
            runs_list = sorted(self.runs.keys())
            common_frames = self._get_common_frames(runs_list[:3]) if len(runs_list) >= 1 else []

            return render_template_string(
                HTML_TEMPLATE,
                runs_json=json.dumps(runs_list),
                common_frames_json=json.dumps(common_frames)
            )

        @self.app.route("/api/comparison", methods=["POST"])
        def get_comparison():
            try:
                data = request.json
                selected_runs = data.get("runs", [])

                # Get common frames
                common_frames = self._get_common_frames(selected_runs)

                # Load data for all common frames
                comparison_data = {
                    "frames": common_frames[:100],  # Limit to first 100 for performance
                    "data": {}
                }

                for run_name in selected_runs:
                    comparison_data["data"][run_name] = {}
                    for frame_name in common_frames[:100]:
                        frame_data = self._load_frame_data(run_name, frame_name)
                        if frame_data:
                            comparison_data["data"][run_name][frame_name] = frame_data

                return jsonify(comparison_data)

            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def run(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
        """Start the Flask server."""
        print(f"Found {len(self.runs)} run(s):")
        for run_name in sorted(self.runs.keys()):
            print(f"  ✓ {run_name}")

        if not self.runs:
            print("\nNo valid runs found! Make sure you have processed data with results/ directory.")
            return

        print(f"\nStarting server at http://{host}:{port}")
        print(f"Press Ctrl+C to stop")
        self.app.run(host=host, port=port, debug=debug)


def main():
    parser = argparse.ArgumentParser(
        description="Web-based comparison tool for Waymo E2E processing runs"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Output directory containing run folders (default: ./output)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Server host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Server port (default: 5000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    args = parser.parse_args()

    try:
        server = ComparisonServer(args.output_dir)
        server.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
