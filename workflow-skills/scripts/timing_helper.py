#!/usr/bin/env python3
"""
Timing Helper for Fitness Modeling Workflow

This module provides functions to track execution time for each step
in the fitness modeling workflow. Timing data is saved to execution_timeline.json
which is used by the visualization script to generate the timeline panel.

Usage:
    from timing_helper import record_step_start, record_step_end, get_timing_summary

    # At the start of a step:
    record_step_start("/path/to/results", "MSA")

    # ... execute the step ...

    # At the end of a step:
    record_step_end("/path/to/results", "MSA")

    # Get summary at the end:
    get_timing_summary("/path/to/results")
"""

import json
import time
from pathlib import Path
from datetime import datetime


def get_timeline_path(results_dir):
    """Get path to execution_timeline.json"""
    return Path(results_dir) / "execution_timeline.json"


def load_timeline(results_dir):
    """Load existing timeline or create empty one"""
    timeline_path = get_timeline_path(results_dir)
    if timeline_path.exists():
        with open(timeline_path) as f:
            return json.load(f)
    return []


def save_timeline(results_dir, timeline):
    """Save timeline to JSON file"""
    timeline_path = get_timeline_path(results_dir)
    with open(timeline_path, 'w') as f:
        json.dump(timeline, f, indent=2)


def record_step_start(results_dir, step_name):
    """
    Record the start time of a step.

    Args:
        results_dir: Path to the results directory
        step_name: Name of the step (e.g., "MSA", "PLMC", "EV+OneHot", "ESM", "ProtTrans", "Plot")
    """
    timeline = load_timeline(results_dir)
    # Remove any existing incomplete entry for this step
    timeline = [s for s in timeline if s.get('name') != step_name]
    timeline.append({
        'name': step_name,
        'start_time': time.time(),
        'start_datetime': datetime.now().isoformat(),
        'status': 'running'
    })
    save_timeline(results_dir, timeline)
    print(f"[TIMING] Started step: {step_name} at {datetime.now().strftime('%H:%M:%S')}")


def record_step_end(results_dir, step_name):
    """
    Record the end time of a step and calculate duration.

    Args:
        results_dir: Path to the results directory
        step_name: Name of the step to complete
    """
    timeline = load_timeline(results_dir)
    step_found = False
    for step in timeline:
        if step.get('name') == step_name and step.get('status') == 'running':
            end_time = time.time()
            start_time = step['start_time']
            duration_minutes = (end_time - start_time) / 60
            step['end_time'] = end_time
            step['end_datetime'] = datetime.now().isoformat()
            step['duration'] = round(duration_minutes, 2)
            step['status'] = 'completed'
            # Calculate relative start time from first step
            first_start = min(s.get('start_time', float('inf')) for s in timeline)
            step['start'] = round((start_time - first_start) / 60, 2)
            step_found = True
            break

    if step_found:
        save_timeline(results_dir, timeline)
        duration = next((s['duration'] for s in timeline if s['name'] == step_name), 0)
        print(f"[TIMING] Completed step: {step_name} in {duration:.2f} minutes")
    else:
        print(f"[TIMING] Warning: No running step found with name: {step_name}")


def get_timing_summary(results_dir):
    """
    Get a summary of all step timings.

    Args:
        results_dir: Path to the results directory

    Returns:
        list: Timeline data with step information
    """
    timeline = load_timeline(results_dir)
    completed_steps = [s for s in timeline if s.get('status') == 'completed']
    total_time = sum(s.get('duration', 0) for s in completed_steps)

    print(f"\n{'='*50}")
    print("EXECUTION TIMELINE SUMMARY")
    print(f"{'='*50}")
    for step in completed_steps:
        print(f"  {step['name']:15} : {step['duration']:6.2f} min (started at +{step['start']:.2f} min)")
    print(f"{'='*50}")
    print(f"  {'TOTAL':15} : {total_time:6.2f} min")
    print(f"{'='*50}\n")

    return timeline


def reset_timeline(results_dir):
    """
    Reset the timeline (clear all entries).

    Args:
        results_dir: Path to the results directory
    """
    save_timeline(results_dir, [])
    print("[TIMING] Timeline reset")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Timing helper for fitness modeling workflow')
    parser.add_argument('action', choices=['start', 'end', 'summary', 'reset'],
                        help='Action to perform')
    parser.add_argument('--results-dir', '-d', type=str, required=True,
                        help='Path to results directory')
    parser.add_argument('--step', '-s', type=str,
                        help='Step name (required for start/end actions)')

    args = parser.parse_args()

    if args.action == 'start':
        if not args.step:
            parser.error("--step is required for 'start' action")
        record_step_start(args.results_dir, args.step)
    elif args.action == 'end':
        if not args.step:
            parser.error("--step is required for 'end' action")
        record_step_end(args.results_dir, args.step)
    elif args.action == 'summary':
        get_timing_summary(args.results_dir)
    elif args.action == 'reset':
        reset_timeline(args.results_dir)
