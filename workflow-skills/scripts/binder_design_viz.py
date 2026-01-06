#!/usr/bin/env python3
"""
Binder Design Visualization Script

Generates separate figures after binder design workflow:
1. Design Quality Comparison - Bar chart comparing pLDDT scores across designs
2. Interface Quality - Bar chart of interface pAE scores
3. Design Metrics Table - Table showing all metrics for each design
4. Quality Distribution - Scatter plot of pLDDT vs pAE with quality zones
5. Design Ranking - Horizontal bar chart ranking designs by composite score
6. Execution Timeline - Gantt chart showing step execution times

Each figure is saved as a separate 4x4 inch file.
"""

import argparse
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from matplotlib.table import Table
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns

# Color palettes from plot_style_utils (matching fitness_modeling_viz.py)
CAT_PALETTE = sns.color_palette('colorblind')
DIV_PALETTE = sns.color_palette("BrBG_r", 100)
SEQ_PALETTE = sns.cubehelix_palette(100, start=0.5, rot=-0.75)
GRAY = [0.5, 0.5, 0.5]

# Figure size for individual plots
FIGSIZE = (4, 4)

# Quality thresholds for binder designs
QUALITY_THRESHOLDS = {
    'plddt_good': 80,
    'plddt_acceptable': 70,
    'pae_good': 5,
    'pae_acceptable': 10,
    'i_pae_good': 10,
    'i_pae_acceptable': 15,
    'i_ptm_good': 0.6,
    'i_ptm_acceptable': 0.4,
}


def prettify_ax(ax):
    """Make axes more pleasant to look at"""
    for i, spine in enumerate(ax.spines.values()):
        if i == 3 or i == 1:  # top and right
            spine.set_visible(False)
    ax.set_frameon = True
    ax.tick_params(direction='out', length=3, color='k')
    ax.set_axisbelow(True)


def simple_ax(figsize=FIGSIZE, **kwargs):
    """Shortcut to make and 'prettify' a simple figure with 1 axis"""
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, **kwargs)
    prettify_ax(ax)
    return fig, ax


def set_pub_plot_context(context="talk"):
    """Set publication-quality plot context"""
    sns.set(style="white", context=context)


def save_for_pub(fig, path, dpi=300, include_raster=True):
    """Save figure in publication-ready formats"""
    fig.savefig(path + ".pdf", dpi=dpi, bbox_inches='tight', transparent=True)
    if include_raster:
        fig.savefig(path + ".png", dpi=dpi, bbox_inches='tight', transparent=True)


def load_design_metrics(results_dir: Path) -> pd.DataFrame:
    """Load design metrics from results directory."""
    # Try different possible file names
    possible_names = [
        "design_metrics.csv",
        "metrics.csv",
        "all_designs_metrics.csv",
        "binder_metrics.csv",
    ]

    for name in possible_names:
        csv_path = results_dir / name
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            print(f"Loaded metrics from {csv_path}")
            return df

    # Try to find in subdirectories
    for subdir in results_dir.iterdir():
        if subdir.is_dir():
            for name in possible_names:
                csv_path = subdir / name
                if csv_path.exists():
                    df = pd.read_csv(csv_path)
                    print(f"Loaded metrics from {csv_path}")
                    return df

    print("No metrics file found, generating mock data for demonstration")
    return generate_mock_data()


def generate_mock_data(n_designs=8) -> pd.DataFrame:
    """Generate mock data for demonstration."""
    np.random.seed(42)

    designs = []
    for i in range(1, n_designs + 1):
        designs.append({
            'design_name': f'design_{i:03d}',
            'plddt': np.random.normal(78, 8),
            'pae': np.random.exponential(5) + 2,
            'i_pae': np.random.exponential(6) + 3,
            'i_ptm': np.random.beta(5, 3),
            'i_plddt': np.random.normal(75, 10),
            'ptm': np.random.beta(6, 3),
        })

    df = pd.DataFrame(designs)
    # Clip values to reasonable ranges
    df['plddt'] = df['plddt'].clip(50, 95)
    df['pae'] = df['pae'].clip(2, 25)
    df['i_pae'] = df['i_pae'].clip(3, 30)
    df['i_ptm'] = df['i_ptm'].clip(0.2, 0.9)
    df['i_plddt'] = df['i_plddt'].clip(45, 90)
    df['ptm'] = df['ptm'].clip(0.3, 0.95)

    return df


def calculate_composite_score(df: pd.DataFrame) -> pd.Series:
    """Calculate composite quality score for ranking designs."""
    # Normalize each metric to 0-1 scale (higher is better)
    scores = pd.DataFrame()

    # pLDDT: higher is better (0-100 scale)
    if 'plddt' in df.columns:
        scores['plddt'] = df['plddt'] / 100

    # pAE: lower is better (invert)
    if 'pae' in df.columns:
        scores['pae'] = 1 - (df['pae'] / 30).clip(0, 1)

    # i_pae: lower is better (invert)
    if 'i_pae' in df.columns:
        scores['i_pae'] = 1 - (df['i_pae'] / 30).clip(0, 1)

    # i_ptm: higher is better
    if 'i_ptm' in df.columns:
        scores['i_ptm'] = df['i_ptm']

    # Calculate weighted average
    weights = {'plddt': 0.3, 'pae': 0.2, 'i_pae': 0.3, 'i_ptm': 0.2}

    composite = pd.Series(0.0, index=df.index)
    total_weight = 0
    for col, weight in weights.items():
        if col in scores.columns:
            composite += scores[col] * weight
            total_weight += weight

    if total_weight > 0:
        composite /= total_weight

    return composite


def get_color_for_value(value, threshold_good, threshold_acceptable, higher_is_better=True):
    """Get color based on quality thresholds."""
    if higher_is_better:
        if value >= threshold_good:
            return CAT_PALETTE[2]  # Green
        elif value >= threshold_acceptable:
            return CAT_PALETTE[1]  # Orange
        else:
            return CAT_PALETTE[3]  # Red
    else:
        if value <= threshold_good:
            return CAT_PALETTE[2]  # Green
        elif value <= threshold_acceptable:
            return CAT_PALETTE[1]  # Orange
        else:
            return CAT_PALETTE[3]  # Red


def plot_plddt_comparison(df: pd.DataFrame, output_path: str = None):
    """
    Plot 1: Bar chart comparing pLDDT scores across designs.
    """
    fig, ax = simple_ax(figsize=FIGSIZE)

    # Sort by pLDDT (descending)
    df_sorted = df.sort_values('plddt', ascending=False).reset_index(drop=True)

    n_designs = len(df_sorted)
    x_pos = np.arange(n_designs)

    # Color bars based on quality thresholds
    colors = [get_color_for_value(v, QUALITY_THRESHOLDS['plddt_good'],
                                   QUALITY_THRESHOLDS['plddt_acceptable'],
                                   higher_is_better=True)
              for v in df_sorted['plddt']]

    bars = ax.bar(x_pos, df_sorted['plddt'], color=colors, alpha=0.9, width=0.7)

    # Add threshold lines
    ax.axhline(y=QUALITY_THRESHOLDS['plddt_good'], color=CAT_PALETTE[2],
               linestyle='--', alpha=0.7, linewidth=1, label=f"Good (>{QUALITY_THRESHOLDS['plddt_good']})")
    ax.axhline(y=QUALITY_THRESHOLDS['plddt_acceptable'], color=CAT_PALETTE[1],
               linestyle='--', alpha=0.7, linewidth=1, label=f"Acceptable (>{QUALITY_THRESHOLDS['plddt_acceptable']})")

    ax.set_title('Design pLDDT Scores', fontsize=12, fontweight='bold', pad=10)
    ax.set_ylabel('pLDDT', fontsize=10)
    ax.set_xlabel('Design', fontsize=10)
    ax.set_xticks(x_pos)

    # Simplify labels
    labels = [name.replace('design_', '').lstrip('0') for name in df_sorted['design_name']]
    ax.set_xticklabels(labels, fontsize=9)

    ax.set_ylim(0, 100)
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)
    ax.legend(loc='lower right', fontsize=8)

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png, {output_path}.pdf")

    return fig


def plot_interface_pae(df: pd.DataFrame, output_path: str = None):
    """
    Plot 2: Bar chart of interface pAE scores.
    """
    fig, ax = simple_ax(figsize=FIGSIZE)

    # Use i_pae if available, otherwise use pae
    pae_col = 'i_pae' if 'i_pae' in df.columns else 'pae'
    threshold_good = QUALITY_THRESHOLDS['i_pae_good'] if pae_col == 'i_pae' else QUALITY_THRESHOLDS['pae_good']
    threshold_acc = QUALITY_THRESHOLDS['i_pae_acceptable'] if pae_col == 'i_pae' else QUALITY_THRESHOLDS['pae_acceptable']

    # Sort by pAE (ascending - lower is better)
    df_sorted = df.sort_values(pae_col, ascending=True).reset_index(drop=True)

    n_designs = len(df_sorted)
    x_pos = np.arange(n_designs)

    # Color bars based on quality thresholds (lower is better)
    colors = [get_color_for_value(v, threshold_good, threshold_acc, higher_is_better=False)
              for v in df_sorted[pae_col]]

    bars = ax.bar(x_pos, df_sorted[pae_col], color=colors, alpha=0.9, width=0.7)

    # Add threshold lines
    ax.axhline(y=threshold_good, color=CAT_PALETTE[2],
               linestyle='--', alpha=0.7, linewidth=1, label=f"Good (<{threshold_good})")
    ax.axhline(y=threshold_acc, color=CAT_PALETTE[1],
               linestyle='--', alpha=0.7, linewidth=1, label=f"Acceptable (<{threshold_acc})")

    title = 'Interface pAE Scores' if pae_col == 'i_pae' else 'pAE Scores'
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.set_ylabel('pAE (lower is better)', fontsize=10)
    ax.set_xlabel('Design', fontsize=10)
    ax.set_xticks(x_pos)

    labels = [name.replace('design_', '').lstrip('0') for name in df_sorted['design_name']]
    ax.set_xticklabels(labels, fontsize=9)

    ax.yaxis.grid(True, linestyle='--', alpha=0.4)
    ax.legend(loc='upper right', fontsize=8)

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png, {output_path}.pdf")

    return fig


def plot_metrics_table(df: pd.DataFrame, output_path: str = None):
    """
    Plot 3: Table showing all metrics for each design.
    """
    fig = plt.figure(figsize=FIGSIZE)
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Design Metrics Summary', fontsize=12, fontweight='bold', pad=10)

    # Select columns to display
    display_cols = ['design_name']
    metric_cols = []
    for col in ['plddt', 'pae', 'i_pae', 'i_ptm', 'ptm']:
        if col in df.columns:
            metric_cols.append(col)
    display_cols.extend(metric_cols)

    # Calculate composite score
    df = df.copy()
    df['score'] = calculate_composite_score(df)
    metric_cols.append('score')
    display_cols.append('score')

    # Sort by composite score
    df_sorted = df.sort_values('score', ascending=False).head(8).reset_index(drop=True)

    n_rows = len(df_sorted) + 1  # +1 for header
    n_cols = len(display_cols)

    table = ax.table(
        cellText=[['']*n_cols for _ in range(n_rows)],
        loc='center',
        cellLoc='center',
        bbox=[0.0, 0.05, 1.0, 0.9]
    )

    # Style header
    header_labels = ['Design', 'pLDDT', 'pAE', 'i_pAE', 'i_pTM', 'pTM', 'Score'][:n_cols]
    for j, label in enumerate(header_labels):
        cell = table[(0, j)]
        cell.set_text_props(text=label, fontweight='bold', fontsize=8)
        cell.set_facecolor('#E8E8E8')

    # Fill data
    for i, (_, row) in enumerate(df_sorted.iterrows()):
        for j, col in enumerate(display_cols):
            cell = table[(i+1, j)]
            val = row[col]
            if col == 'design_name':
                text = val.replace('design_', '').lstrip('0')
            elif col == 'score':
                text = f'{val:.2f}'
            elif col in ['plddt', 'i_plddt']:
                text = f'{val:.1f}'
            elif col in ['pae', 'i_pae']:
                text = f'{val:.1f}'
            elif col in ['ptm', 'i_ptm']:
                text = f'{val:.2f}'
            else:
                text = f'{val:.2f}'
            cell.set_text_props(text=text, fontsize=8)

            # Highlight best score row
            if i == 0 and col == 'score':
                cell.set_facecolor('#D4EDDA')  # Light green

    table.auto_set_font_size(False)
    for key, cell in table.get_celld().items():
        cell.set_edgecolor('#CCCCCC')
        cell.set_height(0.1)

    # Add best design annotation
    best_design = df_sorted.iloc[0]['design_name'].replace('design_', '').lstrip('0')
    best_score = df_sorted.iloc[0]['score']
    ax.text(0.5, 0.01, f'Best: Design {best_design} (score={best_score:.2f})',
            ha='center', va='bottom', transform=ax.transAxes, fontsize=9, fontweight='bold')

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png, {output_path}.pdf")

    return fig


def plot_quality_scatter(df: pd.DataFrame, output_path: str = None):
    """
    Plot 4: Scatter plot of pLDDT vs pAE with quality zones.
    """
    fig, ax = simple_ax(figsize=FIGSIZE)

    pae_col = 'i_pae' if 'i_pae' in df.columns else 'pae'
    pae_good = QUALITY_THRESHOLDS['i_pae_good'] if pae_col == 'i_pae' else QUALITY_THRESHOLDS['pae_good']

    # Calculate composite scores for coloring
    scores = calculate_composite_score(df)

    # Scatter plot
    scatter = ax.scatter(df['plddt'], df[pae_col], c=scores, cmap='viridis',
                        s=80, alpha=0.8, edgecolors='white', linewidth=0.5)

    # Add quality zone rectangles
    # Good zone (top-left: high pLDDT, low pAE)
    rect_good = Rectangle((QUALITY_THRESHOLDS['plddt_good'], 0),
                          100 - QUALITY_THRESHOLDS['plddt_good'], pae_good,
                          linewidth=0, facecolor=CAT_PALETTE[2], alpha=0.1)
    ax.add_patch(rect_good)

    # Add threshold lines
    ax.axvline(x=QUALITY_THRESHOLDS['plddt_good'], color=CAT_PALETTE[2],
               linestyle='--', alpha=0.5, linewidth=1)
    ax.axhline(y=pae_good, color=CAT_PALETTE[2],
               linestyle='--', alpha=0.5, linewidth=1)

    # Add design labels
    for i, row in df.iterrows():
        label = row['design_name'].replace('design_', '').lstrip('0')
        ax.annotate(label, (row['plddt'], row[pae_col]),
                   fontsize=7, alpha=0.7,
                   xytext=(3, 3), textcoords='offset points')

    ax.set_title('Quality Distribution', fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel('pLDDT (higher is better)', fontsize=10)
    ylabel = 'Interface pAE' if pae_col == 'i_pae' else 'pAE'
    ax.set_ylabel(f'{ylabel} (lower is better)', fontsize=10)

    ax.set_xlim(50, 100)

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('Composite Score', fontsize=9)

    # Add "Good Zone" label
    ax.text(QUALITY_THRESHOLDS['plddt_good'] + 2, pae_good - 1, 'Good Zone',
            fontsize=8, color=CAT_PALETTE[2], alpha=0.8, fontweight='bold')

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png, {output_path}.pdf")

    return fig


def plot_design_ranking(df: pd.DataFrame, output_path: str = None):
    """
    Plot 5: Horizontal bar chart ranking designs by composite score.
    """
    fig, ax = simple_ax(figsize=FIGSIZE)

    # Calculate composite scores and sort
    df = df.copy()
    df['score'] = calculate_composite_score(df)
    df_sorted = df.sort_values('score', ascending=True).reset_index(drop=True)

    n_designs = len(df_sorted)
    y_pos = np.arange(n_designs)

    # Use sequential palette for ranking
    colors = [CAT_PALETTE[i % len(CAT_PALETTE)] for i in range(n_designs)]
    colors = colors[::-1]  # Reverse so best is at top

    bars = ax.barh(y_pos, df_sorted['score'], color=colors, alpha=0.9, height=0.7)

    ax.set_title('Design Ranking', fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel('Composite Score', fontsize=10)
    ax.set_yticks(y_pos)

    # Labels with rank
    labels = []
    for i, (_, row) in enumerate(df_sorted.iterrows()):
        rank = n_designs - i
        name = row['design_name'].replace('design_', '').lstrip('0')
        labels.append(f"#{rank}: {name}")
    ax.set_yticklabels(labels, fontsize=9)

    ax.set_xlim(0, 1)
    ax.xaxis.grid(True, linestyle='--', alpha=0.4)

    # Add score labels on bars
    for bar, (_, row) in zip(bars, df_sorted.iterrows()):
        width = bar.get_width()
        ax.text(width + 0.02, bar.get_y() + bar.get_height()/2,
                f'{row["score"]:.2f}', va='center', fontsize=8)

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png, {output_path}.pdf")

    return fig


def infer_timeline_from_files(results_dir: Path) -> list:
    """
    Infer execution timeline from file modification timestamps.
    Returns list of steps with start times and durations in minutes.
    """
    import glob

    # Define files to check for each step
    step_files = {
        'Config': ['config.json', '*.json'],
        'RFdiffusion': ['*/trajectory_*.pdb', '**/rfdiff*'],
        'ProteinMPNN': ['*/seqs/*.fa', '**/mpnn*'],
        'AlphaFold2': ['*/af2_*.pdb', '**/af2*', '**/alphafold*'],
        'Analysis': ['design_metrics.csv', 'metrics.csv', '*_metrics.csv'],
        'Plot': ['binder_design_*.png', '*_summary.png']
    }

    step_times = {}

    for step_name, patterns in step_files.items():
        times = []
        for pattern in patterns:
            matches = glob.glob(str(results_dir / pattern), recursive=True)
            for match in matches:
                try:
                    mtime = os.path.getmtime(match)
                    times.append(mtime)
                except:
                    pass
        if times:
            step_times[step_name] = {
                'start': min(times),
                'end': max(times)
            }

    if not step_times:
        return None

    # Convert to relative times in minutes
    all_times = [t['start'] for t in step_times.values()] + [t['end'] for t in step_times.values()]
    base_time = min(all_times)

    steps = []
    step_order = ['Config', 'RFdiffusion', 'ProteinMPNN', 'AlphaFold2', 'Analysis', 'Plot']

    for step_name in step_order:
        if step_name in step_times:
            start_min = (step_times[step_name]['start'] - base_time) / 60
            end_min = (step_times[step_name]['end'] - base_time) / 60
            duration = max(end_min - start_min, 0.5)  # Minimum 0.5 min duration
            steps.append({
                'name': step_name,
                'start': round(start_min, 1),
                'duration': round(duration, 1)
            })

    return steps if steps else None


def plot_execution_timeline(timeline_path: Path, results_dir: Path = None, output_path: str = None):
    """
    Plot 6: Gantt chart of execution timeline.
    """
    fig, ax = simple_ax(figsize=FIGSIZE)
    ax.set_title('Execution Timeline', fontsize=12, fontweight='bold', pad=10)

    # Default timeline for binder design
    default_steps = [
        {'name': 'Config', 'start': 0, 'duration': 1},
        {'name': 'RFdiffusion', 'start': 1, 'duration': 30},
        {'name': 'ProteinMPNN', 'start': 31, 'duration': 5},
        {'name': 'AlphaFold2', 'start': 36, 'duration': 20},
        {'name': 'Analysis', 'start': 56, 'duration': 2},
        {'name': 'Plot', 'start': 58, 'duration': 1},
    ]

    steps = None

    # Priority 1: Load from timeline JSON if exists
    if timeline_path is not None and timeline_path.exists():
        with open(timeline_path) as f:
            loaded_data = json.load(f)

        steps = []
        for step in loaded_data:
            if step.get('status') == 'completed' and 'duration' in step:
                if 'start' not in step:
                    if 'start_time' in step and loaded_data:
                        first_start = min(s.get('start_time', float('inf'))
                                          for s in loaded_data if 'start_time' in s)
                        step['start'] = (step['start_time'] - first_start) / 60
                    else:
                        step['start'] = 0
                steps.append(step)

        if steps:
            print(f"Loaded timeline from execution_timeline.json ({len(steps)} steps)")
        else:
            steps = None

    # Priority 2: Infer from file timestamps
    if steps is None and results_dir is not None:
        inferred_steps = infer_timeline_from_files(results_dir)
        if inferred_steps:
            total_inferred = max(s['start'] + s['duration'] for s in inferred_steps)
            if total_inferred <= 1440:  # 24 hours in minutes
                steps = inferred_steps
                print(f"Inferred timeline from file timestamps (total: {total_inferred:.1f} min)")

    # Priority 3: Use defaults
    if steps is None:
        steps = default_steps
        print("Using default timeline (no timing data available)")

    # Calculate total time
    total_time = max(s['start'] + s['duration'] for s in steps)

    # Use colorblind palette for timeline bars
    colors = [CAT_PALETTE[i % len(CAT_PALETTE)] for i in range(len(steps))]

    y_positions = list(range(len(steps)-1, -1, -1))

    for i, (step, y_pos) in enumerate(zip(steps, y_positions)):
        ax.barh(y_pos, step['duration'], left=step['start'], height=0.6,
                color=colors[i], edgecolor='white', linewidth=0.5)

        # Add step label
        ax.text(-0.5, y_pos, f"Step {i+1}:\n{step['name']}", ha='right', va='center',
                fontsize=8)

    # Add total time bar
    ax.barh(-1, total_time, left=0, height=0.6, color=GRAY, alpha=0.8)
    ax.text(-0.5, -1, f"Total: ~{int(total_time)} minutes", ha='right', va='center',
            fontsize=8, fontweight='bold')

    ax.set_xlabel('Time (minutes)', fontsize=10)
    ax.set_xlim(-1, total_time * 1.1)
    ax.set_ylim(-2, len(steps))
    ax.set_yticks([])
    ax.xaxis.grid(True, linestyle='--', alpha=0.4)

    # Remove y-axis
    ax.spines['left'].set_visible(False)

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png, {output_path}.pdf")

    return fig


def create_separate_figures(results_dir: str, output_prefix: str = None):
    """
    Create separate visualization figures for binder design.

    Args:
        results_dir: Path to results directory
        output_prefix: Path prefix for saving (without extension)

    Returns:
        list: Paths to saved figures
    """
    results_dir = Path(results_dir)

    if output_prefix is None:
        output_prefix = str(results_dir / "binder_design")

    # Set publication-quality plot context
    set_pub_plot_context(context="talk")

    # Load data
    df = load_design_metrics(results_dir)

    if df.empty:
        print("Error: No design metrics found in", results_dir)
        return None

    saved_files = []

    # Figure 1: pLDDT comparison
    fig1 = plot_plddt_comparison(df, f"{output_prefix}_plddt_comparison")
    saved_files.append(f"{output_prefix}_plddt_comparison.png")
    plt.close(fig1)

    # Figure 2: Interface pAE
    fig2 = plot_interface_pae(df, f"{output_prefix}_interface_pae")
    saved_files.append(f"{output_prefix}_interface_pae.png")
    plt.close(fig2)

    # Figure 3: Metrics table
    fig3 = plot_metrics_table(df, f"{output_prefix}_metrics_table")
    saved_files.append(f"{output_prefix}_metrics_table.png")
    plt.close(fig3)

    # Figure 4: Quality scatter
    fig4 = plot_quality_scatter(df, f"{output_prefix}_quality_scatter")
    saved_files.append(f"{output_prefix}_quality_scatter.png")
    plt.close(fig4)

    # Figure 5: Design ranking
    fig5 = plot_design_ranking(df, f"{output_prefix}_design_ranking")
    saved_files.append(f"{output_prefix}_design_ranking.png")
    plt.close(fig5)

    # Figure 6: Execution timeline
    timeline_path = results_dir / "execution_timeline.json"
    fig6 = plot_execution_timeline(timeline_path, results_dir, f"{output_prefix}_execution_timeline")
    saved_files.append(f"{output_prefix}_execution_timeline.png")
    plt.close(fig6)

    print(f"\nGenerated {len(saved_files)} separate figures:")
    for f in saved_files:
        print(f"  - {f}")

    return saved_files


def create_merged_figure(results_dir: str, output_prefix: str = None):
    """
    Create a single merged figure with all panels.

    Layout: 2 rows x 3 columns
    Row 1: pLDDT comparison, Interface pAE, Quality scatter
    Row 2: Design ranking, Metrics table, Execution timeline

    Args:
        results_dir: Path to results directory
        output_prefix: Path prefix for saving (without extension)

    Returns:
        str: Path to saved merged figure
    """
    results_dir = Path(results_dir)

    if output_prefix is None:
        output_prefix = str(results_dir / "binder_design_summary")

    # Set publication-quality plot context
    set_pub_plot_context(context="talk")

    # Load data
    df = load_design_metrics(results_dir)

    if df.empty:
        print("Error: No design metrics found in", results_dir)
        return None

    # Create figure with 2x3 grid
    fig = plt.figure(figsize=(12, 8))

    # Create subplots
    ax1 = fig.add_subplot(2, 3, 1)  # pLDDT comparison
    prettify_ax(ax1)
    ax2 = fig.add_subplot(2, 3, 2)  # Interface pAE
    prettify_ax(ax2)
    ax3 = fig.add_subplot(2, 3, 3)  # Quality scatter
    prettify_ax(ax3)
    ax4 = fig.add_subplot(2, 3, 4)  # Design ranking
    prettify_ax(ax4)
    ax5 = fig.add_subplot(2, 3, 5)  # Metrics table
    ax6 = fig.add_subplot(2, 3, 6)  # Execution timeline
    prettify_ax(ax6)

    # Generate plots on axes
    _plot_plddt_comparison_ax(ax1, df)
    _plot_interface_pae_ax(ax2, df)
    _plot_quality_scatter_ax(ax3, df)
    _plot_design_ranking_ax(ax4, df)
    _plot_metrics_table_ax(ax5, df)

    timeline_path = results_dir / "execution_timeline.json"
    _plot_execution_timeline_ax(ax6, timeline_path, results_dir)

    plt.tight_layout()

    # Save figures
    save_for_pub(fig, output_prefix, include_raster=True)

    plt.close(fig)

    print(f"\nSaved merged figure: {output_prefix}.png, {output_prefix}.pdf")

    return f"{output_prefix}.png"


# Internal functions for merged figure (take ax parameter)
def _plot_plddt_comparison_ax(ax, df):
    """Internal: Plot pLDDT comparison on given axis."""
    df_sorted = df.sort_values('plddt', ascending=False).reset_index(drop=True)
    n_designs = len(df_sorted)
    x_pos = np.arange(n_designs)

    colors = [get_color_for_value(v, QUALITY_THRESHOLDS['plddt_good'],
                                   QUALITY_THRESHOLDS['plddt_acceptable'],
                                   higher_is_better=True)
              for v in df_sorted['plddt']]

    ax.bar(x_pos, df_sorted['plddt'], color=colors, alpha=0.9, width=0.7)
    ax.axhline(y=QUALITY_THRESHOLDS['plddt_good'], color=CAT_PALETTE[2],
               linestyle='--', alpha=0.7, linewidth=1)
    ax.axhline(y=QUALITY_THRESHOLDS['plddt_acceptable'], color=CAT_PALETTE[1],
               linestyle='--', alpha=0.7, linewidth=1)

    ax.set_title('Design pLDDT Scores', fontsize=10, fontweight='bold', pad=8)
    ax.set_ylabel('pLDDT', fontsize=9)
    ax.set_xlabel('Design', fontsize=9)
    ax.set_xticks(x_pos)
    labels = [name.replace('design_', '').lstrip('0') for name in df_sorted['design_name']]
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 100)
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)


def _plot_interface_pae_ax(ax, df):
    """Internal: Plot interface pAE on given axis."""
    pae_col = 'i_pae' if 'i_pae' in df.columns else 'pae'
    threshold_good = QUALITY_THRESHOLDS['i_pae_good'] if pae_col == 'i_pae' else QUALITY_THRESHOLDS['pae_good']
    threshold_acc = QUALITY_THRESHOLDS['i_pae_acceptable'] if pae_col == 'i_pae' else QUALITY_THRESHOLDS['pae_acceptable']

    df_sorted = df.sort_values(pae_col, ascending=True).reset_index(drop=True)
    n_designs = len(df_sorted)
    x_pos = np.arange(n_designs)

    colors = [get_color_for_value(v, threshold_good, threshold_acc, higher_is_better=False)
              for v in df_sorted[pae_col]]

    ax.bar(x_pos, df_sorted[pae_col], color=colors, alpha=0.9, width=0.7)
    ax.axhline(y=threshold_good, color=CAT_PALETTE[2], linestyle='--', alpha=0.7, linewidth=1)
    ax.axhline(y=threshold_acc, color=CAT_PALETTE[1], linestyle='--', alpha=0.7, linewidth=1)

    title = 'Interface pAE Scores' if pae_col == 'i_pae' else 'pAE Scores'
    ax.set_title(title, fontsize=10, fontweight='bold', pad=8)
    ax.set_ylabel('pAE (lower is better)', fontsize=9)
    ax.set_xlabel('Design', fontsize=9)
    ax.set_xticks(x_pos)
    labels = [name.replace('design_', '').lstrip('0') for name in df_sorted['design_name']]
    ax.set_xticklabels(labels, fontsize=8)
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)


def _plot_quality_scatter_ax(ax, df):
    """Internal: Plot quality scatter on given axis."""
    pae_col = 'i_pae' if 'i_pae' in df.columns else 'pae'
    pae_good = QUALITY_THRESHOLDS['i_pae_good'] if pae_col == 'i_pae' else QUALITY_THRESHOLDS['pae_good']

    scores = calculate_composite_score(df)

    scatter = ax.scatter(df['plddt'], df[pae_col], c=scores, cmap='viridis',
                        s=60, alpha=0.8, edgecolors='white', linewidth=0.5)

    rect_good = Rectangle((QUALITY_THRESHOLDS['plddt_good'], 0),
                          100 - QUALITY_THRESHOLDS['plddt_good'], pae_good,
                          linewidth=0, facecolor=CAT_PALETTE[2], alpha=0.1)
    ax.add_patch(rect_good)

    ax.axvline(x=QUALITY_THRESHOLDS['plddt_good'], color=CAT_PALETTE[2], linestyle='--', alpha=0.5, linewidth=1)
    ax.axhline(y=pae_good, color=CAT_PALETTE[2], linestyle='--', alpha=0.5, linewidth=1)

    ax.set_title('Quality Distribution', fontsize=10, fontweight='bold', pad=8)
    ax.set_xlabel('pLDDT', fontsize=9)
    ylabel = 'Interface pAE' if pae_col == 'i_pae' else 'pAE'
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_xlim(50, 100)

    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('Score', fontsize=8)


def _plot_design_ranking_ax(ax, df):
    """Internal: Plot design ranking on given axis."""
    df = df.copy()
    df['score'] = calculate_composite_score(df)
    df_sorted = df.sort_values('score', ascending=True).reset_index(drop=True)

    n_designs = len(df_sorted)
    y_pos = np.arange(n_designs)

    colors = [CAT_PALETTE[i % len(CAT_PALETTE)] for i in range(n_designs)][::-1]

    bars = ax.barh(y_pos, df_sorted['score'], color=colors, alpha=0.9, height=0.7)

    ax.set_title('Design Ranking', fontsize=10, fontweight='bold', pad=8)
    ax.set_xlabel('Composite Score', fontsize=9)
    ax.set_yticks(y_pos)

    labels = []
    for i, (_, row) in enumerate(df_sorted.iterrows()):
        rank = n_designs - i
        name = row['design_name'].replace('design_', '').lstrip('0')
        labels.append(f"#{rank}: {name}")
    ax.set_yticklabels(labels, fontsize=8)

    ax.set_xlim(0, 1)
    ax.xaxis.grid(True, linestyle='--', alpha=0.4)


def _plot_metrics_table_ax(ax, df):
    """Internal: Plot metrics table on given axis."""
    ax.axis('off')
    ax.set_title('Design Metrics Summary', fontsize=10, fontweight='bold', pad=8)

    display_cols = ['design_name']
    metric_cols = []
    for col in ['plddt', 'pae', 'i_pae', 'i_ptm']:
        if col in df.columns:
            metric_cols.append(col)
    display_cols.extend(metric_cols)

    df = df.copy()
    df['score'] = calculate_composite_score(df)
    metric_cols.append('score')
    display_cols.append('score')

    df_sorted = df.sort_values('score', ascending=False).head(6).reset_index(drop=True)

    n_rows = len(df_sorted) + 1
    n_cols = len(display_cols)

    table = ax.table(cellText=[['']*n_cols for _ in range(n_rows)],
                     loc='center', cellLoc='center', bbox=[0.0, 0.05, 1.0, 0.9])

    header_labels = ['Design', 'pLDDT', 'pAE', 'i_pAE', 'i_pTM', 'Score'][:n_cols]
    for j, label in enumerate(header_labels):
        cell = table[(0, j)]
        cell.set_text_props(text=label, fontweight='bold', fontsize=7)
        cell.set_facecolor('#E8E8E8')

    for i, (_, row) in enumerate(df_sorted.iterrows()):
        for j, col in enumerate(display_cols):
            cell = table[(i+1, j)]
            val = row[col]
            if col == 'design_name':
                text = val.replace('design_', '').lstrip('0')
            elif col == 'score':
                text = f'{val:.2f}'
            elif col in ['plddt', 'i_plddt']:
                text = f'{val:.1f}'
            else:
                text = f'{val:.1f}'
            cell.set_text_props(text=text, fontsize=7)
            if i == 0 and col == 'score':
                cell.set_facecolor('#D4EDDA')

    table.auto_set_font_size(False)
    for key, cell in table.get_celld().items():
        cell.set_edgecolor('#CCCCCC')
        cell.set_height(0.12)


def _plot_execution_timeline_ax(ax, timeline_path, results_dir):
    """Internal: Plot execution timeline on given axis."""
    ax.set_title('Execution Timeline', fontsize=10, fontweight='bold', pad=8)

    default_steps = [
        {'name': 'Config', 'start': 0, 'duration': 1},
        {'name': 'RFdiffusion', 'start': 1, 'duration': 30},
        {'name': 'ProteinMPNN', 'start': 31, 'duration': 5},
        {'name': 'AlphaFold2', 'start': 36, 'duration': 20},
        {'name': 'Analysis', 'start': 56, 'duration': 2},
        {'name': 'Plot', 'start': 58, 'duration': 1},
    ]

    steps = None
    if timeline_path is not None and timeline_path.exists():
        with open(timeline_path) as f:
            loaded_data = json.load(f)
        steps = [s for s in loaded_data if s.get('status') == 'completed' and 'duration' in s]
        if not steps:
            steps = None

    if steps is None and results_dir is not None:
        inferred_steps = infer_timeline_from_files(results_dir)
        if inferred_steps:
            total_inferred = max(s['start'] + s['duration'] for s in inferred_steps)
            if total_inferred <= 1440:
                steps = inferred_steps

    if steps is None:
        steps = default_steps

    total_time = max(s['start'] + s['duration'] for s in steps)
    colors = [CAT_PALETTE[i % len(CAT_PALETTE)] for i in range(len(steps))]
    y_positions = list(range(len(steps)-1, -1, -1))

    for i, (step, y_pos) in enumerate(zip(steps, y_positions)):
        ax.barh(y_pos, step['duration'], left=step['start'], height=0.6,
                color=colors[i], edgecolor='white', linewidth=0.5)
        ax.text(-0.5, y_pos, f"{step['name']}", ha='right', va='center', fontsize=7)

    ax.barh(-1, total_time, left=0, height=0.6, color=GRAY, alpha=0.8)
    ax.text(-0.5, -1, f"Total: ~{int(total_time)}m", ha='right', va='center', fontsize=7, fontweight='bold')

    ax.set_xlabel('Time (minutes)', fontsize=9)
    ax.set_xlim(-1, total_time * 1.1)
    ax.set_ylim(-2, len(steps))
    ax.set_yticks([])
    ax.xaxis.grid(True, linestyle='--', alpha=0.4)
    ax.spines['left'].set_visible(False)


def main():
    parser = argparse.ArgumentParser(description='Generate binder design visualization')
    parser.add_argument('results_dir', type=str, help='Path to results directory')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output prefix (default: results_dir/binder_design)')
    parser.add_argument('--merged', '-m', action='store_true',
                        help='Create merged figure instead of separate figures')

    args = parser.parse_args()

    if args.merged:
        output_file = create_merged_figure(args.results_dir, args.output)
        if output_file:
            print(f"\nVisualization complete: {output_file}")
        else:
            print("\nVisualization failed")
            exit(1)
    else:
        output_files = create_separate_figures(args.results_dir, args.output)
        if output_files:
            print(f"\nVisualization complete!")
        else:
            print("\nVisualization failed")
            exit(1)


def display_results(results_dir: str, show_all: bool = True, block: bool = True):
    """
    Display binder design results in an interactive environment.

    This function shows the generated figures either inline (Jupyter/IPython)
    or in a GUI window (terminal/script).

    Args:
        results_dir: Path to results directory containing the generated figures
        show_all: If True, display all figures. If False, only display main metrics.
        block: If True (default), block until figure window is closed.

    Returns:
        dict: Dictionary with figure paths for further reference
    """
    from pathlib import Path

    results_dir = Path(results_dir)

    # Check if we're in an interactive notebook environment
    in_notebook = False
    try:
        from IPython import get_ipython
        ipython = get_ipython()
        if ipython is not None and 'IPKernelApp' in ipython.config:
            in_notebook = True
    except (ImportError, AttributeError):
        pass

    figures = {}
    figure_files = [
        ("plddt_comparison", "Design pLDDT Scores"),
        ("interface_pae", "Interface pAE Scores"),
        ("quality_scatter", "Quality Distribution"),
        ("design_ranking", "Design Ranking"),
        ("metrics_table", "Design Metrics Summary"),
        ("execution_timeline", "Execution Timeline"),
    ]

    if not show_all:
        figure_files = figure_files[:3]

    if in_notebook:
        from IPython.display import display, Image as IPImage
        for fig_name, title in figure_files:
            png_path = results_dir / f"binder_design_{fig_name}.png"
            if png_path.exists():
                print(f"\n{title}:")
                display(IPImage(filename=str(png_path)))
                figures[fig_name] = str(png_path)
            else:
                print(f"Warning: {png_path} not found")
    else:
        import matplotlib
        try:
            matplotlib.use('TkAgg')
        except:
            try:
                matplotlib.use('Qt5Agg')
            except:
                pass

        import matplotlib.pyplot as plt
        from PIL import Image

        plt.ion()

        n_figs = len(figure_files)
        fig, axes = plt.subplots(2, 3, figsize=(14, 9))
        axes = axes.flatten()

        for i, (fig_name, title) in enumerate(figure_files):
            png_path = results_dir / f"binder_design_{fig_name}.png"
            if png_path.exists():
                img = Image.open(png_path)
                axes[i].imshow(img)
                axes[i].axis('off')
                figures[fig_name] = str(png_path)
            else:
                axes[i].text(0.5, 0.5, f"{fig_name}\nnot found",
                            ha='center', va='center', transform=axes[i].transAxes)
                axes[i].axis('off')

        plt.tight_layout()
        figures['combined_figure'] = fig
        plt.show(block=block)

    # Print summary
    csv_path = results_dir / "design_metrics.csv"
    if not csv_path.exists():
        csv_path = results_dir / "metrics.csv"

    if csv_path.exists():
        df = pd.read_csv(csv_path)
        df['score'] = calculate_composite_score(df)
        df_sorted = df.sort_values('score', ascending=False)

        print("\n" + "="*60)
        print("BINDER DESIGN SUMMARY")
        print("="*60)
        print(f"Total designs: {len(df)}")
        print(f"\nTop 3 designs by composite score:")
        for i, (_, row) in enumerate(df_sorted.head(3).iterrows()):
            name = row['design_name'].replace('design_', '').lstrip('0')
            plddt = row.get('plddt', 'N/A')
            pae = row.get('i_pae', row.get('pae', 'N/A'))
            print(f"  {i+1}. Design {name}: pLDDT={plddt:.1f}, pAE={pae:.1f}, score={row['score']:.2f}")
        print("="*60)

    return figures


if __name__ == '__main__':
    main()
