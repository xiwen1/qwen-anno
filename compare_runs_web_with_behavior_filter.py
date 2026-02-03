#!/usr/bin/env python3
"""
Web-based visualization tool with Behavior Difference Filtering.
Allows side-by-side comparison and filtering of runs by behavior mismatches.
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

    def _get_behavior_mismatches(self, comparison_data: Dict, selected_runs: List[str]) -> Dict:
        """Identify frames with behavior mismatches across runs."""
        mismatches = {
            "behavior_mismatch": [],
            "speed_mismatch": [],
            "command_mismatch": []
        }

        for frame_name in comparison_data["frames"]:
            behaviors = {}
            for run_name in selected_runs:
                frame_data = comparison_data["data"][run_name].get(frame_name)
                if frame_data and frame_data.get("vlm_response"):
                    vlm_resp = frame_data["vlm_response"]
                    if isinstance(vlm_resp, dict) and "meta_behaviour" in vlm_resp:
                        behaviors[run_name] = vlm_resp["meta_behaviour"]

            if not behaviors:
                continue

            speeds = [b.get("speed") for b in behaviors.values() if b.get("speed")]
            commands = [b.get("command") for b in behaviors.values() if b.get("command")]

            speed_mismatch = len(set(speeds)) > 1 if speeds else False
            command_mismatch = len(set(commands)) > 1 if commands else False

            if speed_mismatch or command_mismatch:
                mismatches["behavior_mismatch"].append(frame_name)
            if speed_mismatch:
                mismatches["speed_mismatch"].append(frame_name)
            if command_mismatch:
                mismatches["command_mismatch"].append(frame_name)

        return mismatches

    def _setup_routes(self):
        @self.app.route("/")
        def index():
            runs_list = sorted(self.runs.keys())
            common_frames = self._get_common_frames(runs_list[:3]) if len(runs_list) >= 1 else []

            html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Waymo E2E Comparison with Behavior Filtering</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; }
        .controls { background: white; padding: 20px; margin: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .control-group { margin-bottom: 15px; }
        .control-group label { display: block; font-weight: bold; margin-bottom: 8px; }
        .filter-options { margin: 15px 0; padding: 15px; background: #f9f9f9; border-left: 4px solid #667eea; }
        .filter-option { margin: 8px 0; }
        .filter-option input { margin-right: 8px; }
        button { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer; margin: 5px 5px 5px 0; }
        button:hover { background: #5568d3; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .stat-label { font-size: 12px; color: #999; font-weight: bold; }
        .stat-value { font-size: 24px; font-weight: bold; color: #667eea; }
        .frame-card { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 20px; }
        .frame-header { background: #f9f9f9; padding: 15px; border-bottom: 2px solid #ddd; }
        .frame-title { font-weight: bold; font-size: 16px; }
        .mismatch-flag { color: #ff6b6b; margin-left: 10px; }
        .frame-content { padding: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
        .run-column { border: 1px solid #eee; border-radius: 4px; padding: 15px; background: #fafafa; }
        .run-column.mismatch { border-color: #ff6b6b; background: #fff5f5; }
        .run-title { font-weight: bold; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #667eea; color: #667eea; }
        .run-title.mismatch { color: #ff6b6b; border-bottom-color: #ff6b6b; }
        .image-container { width: 100%; max-height: 400px; background: #000; border-radius: 4px; overflow: hidden; margin-bottom: 15px; display: flex; align-items: center; justify-content: center; }
        .image-container img { max-width: 100%; max-height: 100%; object-fit: contain; }
        .behavior-info { background: white; padding: 12px; border-radius: 4px; border-left: 4px solid #667eea; margin: 10px 0; font-size: 13px; line-height: 1.6; }
        .behavior-value { font-weight: bold; color: #667eea; }
        .behavior-value.different { color: #ff6b6b; }
        .loading { text-align: center; padding: 40px; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .error { background: #fee; color: #c00; padding: 15px; border-radius: 4px; margin: 20px; border-left: 4px solid #c00; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚗 Waymo E2E Comparison with Behavior Filtering</h1>
        <p>Filter and compare runs by VLM behavior (speed & command) mismatches</p>
    </div>

    <div class="controls">
        <div class="control-group">
            <label>Select Runs to Compare:</label>
            <div id="runSelectors"></div>
        </div>

        <div class="filter-options">
            <label style="font-weight: bold; display: block; margin-bottom: 10px;">Filter Options:</label>
            <div class="filter-option">
                <input type="checkbox" id="filter-all-diffs" checked>
                <label for="filter-all-diffs">Show Only Behavior Differences (Any)</label>
            </div>
            <div class="filter-option">
                <input type="checkbox" id="filter-speed-only">
                <label for="filter-speed-only">Speed Mismatch Only</label>
            </div>
            <div class="filter-option">
                <input type="checkbox" id="filter-command-only">
                <label for="filter-command-only">Command Mismatch Only</label>
            </div>
        </div>

        <button onclick="loadComparison()">Load Comparison</button>
        <button onclick="clearComparison()">Clear</button>

        <div id="infoBox" style="display: none; background: #eef; border-left: 4px solid #667eea; padding: 15px; margin: 15px 0; border-radius: 4px; font-size: 13px;"></div>
        <div id="stats" class="stats" style="display: none;"></div>
    </div>

    <div id="content"></div>

    <script>
        let runs = {| safe %};
        let currentData = null;
        let selectedRuns = [];

        function initRunSelectors() {
            const container = document.getElementById('runSelectors');
            runs.forEach((run, idx) => {
                const label = document.createElement('label');
                label.style.display = 'inline-block';
                label.style.marginRight = '20px';
                label.style.marginBottom = '10px';

                const cb = document.createElement('input');
                cb.type = 'checkbox';
                cb.value = run;
                cb.id = 'run-' + run;
                cb.checked = idx < 3;

                const text = document.createElement('span');
                text.textContent = run;
                text.style.marginLeft = '8px';

                label.appendChild(cb);
                label.appendChild(text);
                container.appendChild(label);
            });
        }

        function loadComparison() {
            selectedRuns = Array.from(document.querySelectorAll('input[id^="run-"]:checked')).map(cb => cb.value);
            if (!selectedRuns.length) {
                alert('Select at least one run');
                return;
            }

            document.getElementById('content').innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading...</p></div>';

            fetch('/api/comparison', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({runs: selectedRuns})
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('content').innerHTML = '<div class="error">Error: ' + data.error + '</div>';
                    return;
                }
                currentData = data;
                applyFiltersAndRender();

                let behaviorDiffs = data.behavior_mismatches.behavior_mismatch.length;
                let speedDiffs = data.behavior_mismatches.speed_mismatch.length;
                let commandDiffs = data.behavior_mismatches.command_mismatch.length;

                document.getElementById('stats').innerHTML = `
                    <div class="stat-card"><div class="stat-label">Total Frames</div><div class="stat-value">${data.frames.length}</div></div>
                    <div class="stat-card"><div class="stat-label">Behavior Mismatches</div><div class="stat-value">${behaviorDiffs}</div></div>
                    <div class="stat-card"><div class="stat-label">Speed Mismatches</div><div class="stat-value">${speedDiffs}</div></div>
                    <div class="stat-card"><div class="stat-label">Command Mismatches</div><div class="stat-value">${commandDiffs}</div></div>
                `;
                document.getElementById('stats').style.display = 'grid';

                document.getElementById('infoBox').innerHTML = `
                    <strong>Runs:</strong> ${selectedRuns.join(', ')}<br>
                    <strong>Total:</strong> ${data.frames.length} frames | <strong>Mismatches:</strong> ${behaviorDiffs}
                `;
                document.getElementById('infoBox').style.display = 'block';
            })
            .catch(err => {
                document.getElementById('content').innerHTML = '<div class="error">Error: ' + err.message + '</div>';
            });
        }

        function applyFiltersAndRender() {
            if (!currentData) return;

            const filterAll = document.getElementById('filter-all-diffs').checked;
            const filterSpeed = document.getElementById('filter-speed-only').checked;
            const filterCommand = document.getElementById('filter-command-only').checked;

            let framesToShow = currentData.frames;

            if (filterAll || filterSpeed || filterCommand) {
                const allMismatches = new Set([
                    ...(filterAll ? currentData.behavior_mismatches.behavior_mismatch : []),
                    ...(filterSpeed ? currentData.behavior_mismatches.speed_mismatch : []),
                    ...(filterCommand ? currentData.behavior_mismatches.command_mismatch : [])
                ]);
                framesToShow = currentData.frames.filter(f => allMismatches.has(f));
            }

            renderFrames(framesToShow);
        }

        function renderFrames(frames) {
            const container = document.getElementById('content');
            container.innerHTML = '';

            if (!frames.length) {
                container.innerHTML = '<div class="error">No frames match the filter</div>';
                return;
            }

            frames.forEach((frameName, idx) => {
                const card = document.createElement('div');
                card.className = 'frame-card';

                const hasMismatch = currentData.behavior_mismatches.behavior_mismatch.includes(frameName);
                const sceneId = frameName.split('-')[0].substring(0, 8);
                const frameId = frameName.split('-')[1];

                card.innerHTML = `
                    <div class="frame-header">
                        <div class="frame-title">${idx+1}. ${frameName}${hasMismatch ? '<span class="mismatch-flag">⚠️ Mismatch</span>' : ''}</div>
                        <div style="font-size: 12px; color: #999;">Scene: ${sceneId}... | Frame: ${frameId} | ${idx+1}/${frames.length}</div>
                    </div>
                    <div class="frame-content" id="content-${frameName}"></div>
                `;

                const contentDiv = card.querySelector(`#content-${frameName}`);

                selectedRuns.forEach(run => {
                    const frameData = currentData.data[run][frameName];
                    if (!frameData) return;

                    const behaviors = {};
                    selectedRuns.forEach(r => {
                        const fd = currentData.data[r][frameName];
                        if (fd && fd.vlm_response && fd.vlm_response.meta_behaviour) {
                            behaviors[r] = fd.vlm_response.meta_behaviour;
                        }
                    });

                    const runBehavior = behaviors[run];
                    const isMismatch = runBehavior && (
                        Object.values(behaviors).filter(b => b.speed).map(b => b.speed).filter((v, i, a) => a.indexOf(v) === i).length > 1 ||
                        Object.values(behaviors).filter(b => b.command).map(b => b.command).filter((v, i, a) => a.indexOf(v) === i).length > 1
                    );

                    const col = document.createElement('div');
                    col.className = 'run-column' + (isMismatch ? ' mismatch' : '');

                    const speedDiff = runBehavior && Object.values(behaviors).filter(b => b.speed).map(b => b.speed).filter((v, i, a) => a.indexOf(v) === i).length > 1;
                    const cmdDiff = runBehavior && Object.values(behaviors).filter(b => b.command).map(b => b.command).filter((v, i, a) => a.indexOf(v) === i).length > 1;

                    col.innerHTML = `
                        <div class="run-title${isMismatch ? ' mismatch' : ''}">📊 ${run}</div>
                        ${frameData.image ? '<div class="image-container"><img src="data:image/jpeg;base64,' + frameData.image + '"></div>' : ''}
                        ${frameData.vlm_response && frameData.vlm_response.explanation ? `<div class="behavior-info"><strong>Analysis:</strong><p>${frameData.vlm_response.explanation}</p></div>` : ''}
                        ${runBehavior ? `
                            <div class="behavior-info">
                                <strong>Behavior:</strong><br>
                                Speed: <span class="behavior-value${speedDiff ? ' different' : ''}">${runBehavior.speed}</span><br>
                                Command: <span class="behavior-value${cmdDiff ? ' different' : ''}">${runBehavior.command}</span>
                            </div>
                        ` : ''}
                    `;

                    contentDiv.appendChild(col);
                });

                container.appendChild(card);
            });
        }

        function clearComparison() {
            document.getElementById('content').innerHTML = '';
            document.getElementById('stats').style.display = 'none';
            document.getElementById('infoBox').style.display = 'none';
        }

        document.addEventListener('DOMContentLoaded', initRunSelectors);
        document.getElementById('filter-all-diffs').addEventListener('change', applyFiltersAndRender);
        document.getElementById('filter-speed-only').addEventListener('change', applyFiltersAndRender);
        document.getElementById('filter-command-only').addEventListener('change', applyFiltersAndRender);
    </script>
</body>
</html>
            """.replace('{runs_json | safe %}', json.dumps(sorted(self.runs.keys())))

            return html

        @self.app.route("/api/comparison", methods=["POST"])
        def get_comparison():
            try:
                data = request.json
                selected_runs = data.get("runs", [])

                common_frames = self._get_common_frames(selected_runs)

                comparison_data = {
                    "frames": common_frames[:100],
                    "data": {}
                }

                for run_name in selected_runs:
                    comparison_data["data"][run_name] = {}
                    for frame_name in common_frames[:100]:
                        frame_data = self._load_frame_data(run_name, frame_name)
                        if frame_data:
                            comparison_data["data"][run_name][frame_name] = frame_data

                behavior_mismatches = self._get_behavior_mismatches(comparison_data, selected_runs)
                comparison_data["behavior_mismatches"] = behavior_mismatches

                return jsonify(comparison_data)

            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def run(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
        """Start the Flask server."""
        print(f"Found {len(self.runs)} run(s):")
        for run_name in sorted(self.runs.keys()):
            print(f"  ✓ {run_name}")

        if not self.runs:
            print("\nNo valid runs found!")
            return

        print(f"\nStarting server at http://{host}:{port}")
        print(f"Press Ctrl+C to stop")
        self.app.run(host=host, port=port, debug=debug)


def main():
    parser = argparse.ArgumentParser(description="Compare runs with behavior filtering")
    parser.add_argument("--output-dir", type=str, default="./output")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")

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
