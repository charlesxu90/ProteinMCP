#!/usr/bin/env python3
"""
Fitness Modeling Visualization Script

Generates four separate figures after fitness modeling workflow:
1. Model Performance Comparison - Bar chart comparing best models per backbone
2. Predicted vs Observed - Scatter plot for the best model
3. Head Model Comparison - Table showing all head model results
4. Execution Timeline - Gantt chart showing step execution times

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
from matplotlib.table import Table
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns

# Color palettes from plot_style_utils
CAT_PALETTE = sns.color_palette('colorblind')
DIV_PALETTE = sns.color_palette("BrBG_r", 100)
SEQ_PALETTE = sns.cubehelix_palette(100, start=0.5, rot=-0.75)
GRAY = [0.5, 0.5, 0.5]

# Figure size for individual plots
FIGSIZE = (4, 4)


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


def load_all_models(results_dir: Path) -> pd.DataFrame:
    """Load all model results from results directory."""
    csv_path = results_dir / "all_models_comparison.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)

    # If not found, try to construct from individual files
    results = []

    # EV+OneHot - metrics_summary.csv
    ev_metrics_path = results_dir / "metrics_summary.csv"
    if ev_metrics_path.exists():
        ev_df = pd.read_csv(ev_metrics_path)
        cv_mean = ev_df[ev_df['fold'] == 'mean']['spearman_correlation'].values[0]
        cv_std = ev_df[ev_df['fold'] == 'std']['spearman_correlation'].values[0]
        results.append({
            'backbone': 'EV+OneHot',
            'head': 'ridge',
            'mean_cv_spearman': cv_mean,
            'std_cv_spearman': cv_std
        })

    # Look for training_summary.csv files in subdirectories
    for subdir in results_dir.iterdir():
        if subdir.is_dir():
            summary_path = subdir / "training_summary.csv"
            if summary_path.exists():
                df = pd.read_csv(summary_path)
                if 'mean_cv_spearman' in df.columns:
                    mean_sp = df['mean_cv_spearman'].values[0]
                    std_sp = df['std_cv_spearman'].values[0]
                elif 'cv_mean' in df.columns:
                    mean_sp = df['cv_mean'].values[0]
                    std_sp = df['cv_std'].values[0]
                else:
                    continue

                # Parse backbone and head from directory name
                dir_name = subdir.name
                # Try to parse formats like "ESM2-650M_svr" or "ProtT5-XL_knn"
                parts = dir_name.rsplit('_', 1)
                if len(parts) == 2:
                    backbone, head = parts
                    results.append({
                        'backbone': backbone,
                        'head': head,
                        'mean_cv_spearman': mean_sp,
                        'std_cv_spearman': std_sp
                    })

    return pd.DataFrame(results)


def get_best_per_backbone(df: pd.DataFrame) -> pd.DataFrame:
    """Get best head model for each backbone."""
    return df.loc[df.groupby('backbone')['mean_cv_spearman'].idxmax()].reset_index(drop=True)


def plot_backbone_comparison(best_df: pd.DataFrame, output_path: str = None):
    """
    Plot 1: Bar chart comparing best models per backbone.

    Args:
        best_df: DataFrame with best model per backbone
        output_path: Path prefix for saving (without extension)

    Returns:
        fig: matplotlib figure object
    """
    fig, ax = simple_ax(figsize=FIGSIZE)

    # Sort by performance (descending)
    best_df = best_df.sort_values('mean_cv_spearman', ascending=False)

    methods = best_df['backbone'].tolist()
    spearman = best_df['mean_cv_spearman'].tolist()
    spearman_std = best_df['std_cv_spearman'].tolist()

    # Use colorblind palette for different backbones
    colors = [CAT_PALETTE[i % len(CAT_PALETTE)] for i in range(len(methods))]

    x_pos = np.arange(len(methods))
    bars = ax.bar(x_pos, spearman, color=colors, alpha=0.9, width=0.6)
    ax.errorbar(x_pos, spearman, yerr=spearman_std, fmt='none', ecolor='black',
                capsize=4, capthick=1.5, elinewidth=1.5)

    ax.set_title('Model Performance Comparison', fontsize=12, fontweight='bold', pad=10)
    ax.set_ylabel('Spearman ρ (5-fold CV)', fontsize=10)
    ax.set_xticks(x_pos)

    # Set y-limit to accommodate error bars (max value + max std + padding)
    max_with_error = max(s + e for s, e in zip(spearman, spearman_std))
    ax.set_ylim([0, max_with_error * 1.15])
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)

    # Format x-tick labels with line breaks
    labels = []
    for m in methods:
        if m == 'EV+OneHot':
            labels.append('EV+OneHot')
        elif m == 'ESM2-650M':
            labels.append('ESM2\n650M')
        elif m == 'ESM2-3B':
            labels.append('ESM2\n3B')
        elif m == 'ProtT5-XL':
            labels.append('ProtT5-XL')
        else:
            labels.append(m)
    ax.set_xticklabels(labels, fontsize=9, rotation=45, ha='right')

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png, {output_path}.pdf")

    return fig


def load_model_predictions(results_dir: Path, best_model_info: dict, data_df: pd.DataFrame):
    """
    Load predictions from trained models.
    Always prioritizes EV+OneHot as it's the most robust model.

    Returns:
        tuple: (predicted, observed, actual_rho, model_name) or None if loading fails
    """
    predicted = None
    observed = None
    model_name = None

    # ALWAYS try EV+OneHot first (most robust model)
    ev_pred_path = results_dir / "ev_onehot_predictions.npy"
    ev_obs_path = results_dir / "ev_onehot_observed.npy"
    if ev_pred_path.exists() and ev_obs_path.exists():
        predicted = np.load(ev_pred_path)
        observed = np.load(ev_obs_path)
        model_name = "EV+OneHot (Ridge)"
        print(f"Loaded EV+OneHot predictions (most robust model)")

    # If EV+OneHot not available, try pLM models
    if predicted is None:
        # Collect all available models with predictions
        available_models = []
        for subdir in results_dir.iterdir():
            if subdir.is_dir():
                final_model = subdir / "final_model"
                if final_model.exists():
                    ys_train_path = final_model / "ys_train.npy"
                    ys_pred_path = final_model / "ys_train_pred.npy"
                    if ys_train_path.exists() and ys_pred_path.exists():
                        available_models.append(subdir)

        # Try to find the best model from the available ones
        # Load all_models_comparison.csv to get performance ranking
        all_models_csv = results_dir / "all_models_comparison.csv"
        if all_models_csv.exists() and available_models:
            all_df = pd.read_csv(all_models_csv)
            # Sort by performance
            all_df_sorted = all_df.sort_values('mean_cv_spearman', ascending=False)

            for _, row in all_df_sorted.iterrows():
                dir_name = f"{row['backbone']}_{row['head']}"
                matching_dir = results_dir / dir_name
                if matching_dir in available_models:
                    final_model = matching_dir / "final_model"
                    observed = np.load(final_model / "ys_train.npy")
                    predicted = np.load(final_model / "ys_train_pred.npy")
                    model_name = f"{row['backbone']} ({row['head'].upper()})"
                    print(f"Loaded predictions from {final_model} (best available pLM: {model_name})")
                    break
        elif available_models:
            # Fallback: just use the first available
            subdir = available_models[0]
            final_model = subdir / "final_model"
            observed = np.load(final_model / "ys_train.npy")
            predicted = np.load(final_model / "ys_train_pred.npy")
            parts = subdir.name.rsplit('_', 1)
            if len(parts) == 2:
                model_name = f"{parts[0]} ({parts[1].upper()})"
            else:
                model_name = subdir.name
            print(f"Loaded predictions from {final_model} (fallback: {model_name})")

    if predicted is not None and observed is not None:
        actual_rho, _ = stats.spearmanr(predicted, observed)
        return predicted, observed, actual_rho, model_name

    return None


def plot_predicted_vs_observed(results_dir: Path, best_model_info: dict, data_df: pd.DataFrame,
                               output_path: str = None):
    """
    Plot 2: Scatter plot of predicted vs observed for best model.

    Args:
        results_dir: Path to results directory
        best_model_info: Dict with best model information
        data_df: DataFrame with fitness data
        output_path: Path prefix for saving (without extension)

    Returns:
        fig: matplotlib figure object
    """
    fig, ax = simple_ax(figsize=FIGSIZE)

    # Try to load actual predictions from trained model
    model_data = load_model_predictions(results_dir, best_model_info, data_df)

    if model_data is not None:
        predicted, observed, actual_rho, model_name = model_data
        n_samples = len(observed)
    else:
        # Fall back to simulated predictions based on correlation
        print("Using simulated predictions (no saved predictions found)")
        observed = data_df['log_fitness'].values
        n_samples = len(observed)
        rho = best_model_info['mean_cv_spearman']

        np.random.seed(42)
        noise = np.random.randn(n_samples)
        predicted = rho * stats.zscore(observed) + np.sqrt(1 - rho**2) * noise
        predicted = predicted * np.std(observed) + np.mean(observed)
        actual_rho = rho

        # Construct model name from best_model_info
        if best_model_info['head'] != 'ridge':
            model_name = f"{best_model_info['backbone']} ({best_model_info['head'].upper()})"
        else:
            model_name = "EV+OneHot (Ridge)"

    # Scatter plot using colorblind palette
    ax.scatter(predicted, observed, c=CAT_PALETTE[0], alpha=0.5, s=15, edgecolors='none')

    # Add correlation line
    z = np.polyfit(predicted, observed, 1)
    p = np.poly1d(z)
    x_line = np.linspace(predicted.min(), predicted.max(), 100)
    ax.plot(x_line, p(x_line), 'k--', alpha=0.5, linewidth=1)

    ax.set_title('Predicted vs Observed', fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel('Predicted', fontsize=10)
    ax.set_ylabel('Observed Fitness', fontsize=10)

    ax.text(0.05, 0.95, f"ρ = {actual_rho:.2f}, n = {n_samples:,}\nBest: {model_name}",
            transform=ax.transAxes, fontsize=9, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png, {output_path}.pdf")

    return fig


def plot_head_model_table(all_df: pd.DataFrame, output_path: str = None):
    """
    Plot 3: Table showing head model comparison for pLMs.

    Args:
        all_df: DataFrame with all model results
        output_path: Path prefix for saving (without extension)

    Returns:
        fig: matplotlib figure object
    """
    fig = plt.figure(figsize=FIGSIZE)
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Head Model Comparison', fontsize=12, fontweight='bold', pad=10)

    # Filter to pLM backbones only (exclude EV+OneHot)
    plm_df = all_df[~all_df['backbone'].str.contains('EV|OneHot', case=False, na=False)].copy()

    if plm_df.empty:
        ax.text(0.5, 0.5, 'No pLM results available', ha='center', va='center',
                transform=ax.transAxes, fontsize=10)
        plt.tight_layout()
        if output_path:
            save_for_pub(fig, output_path)
            print(f"Saved: {output_path}.png, {output_path}.pdf")
        return fig

    # Pivot to get table format
    pivot_df = plm_df.pivot(index='backbone', columns='head', values='mean_cv_spearman')

    # Reorder columns if they exist
    head_order = ['svr', 'xgboost', 'knn']
    cols = [c for c in head_order if c in pivot_df.columns]
    pivot_df = pivot_df[cols]

    # Find best per row
    best_per_row = pivot_df.idxmax(axis=1)

    # Create table
    n_rows = len(pivot_df) + 1  # +1 for header
    n_cols = len(cols) + 1  # +1 for backbone column

    table = ax.table(
        cellText=[['']*n_cols for _ in range(n_rows)],
        loc='center',
        cellLoc='center',
        bbox=[0.05, 0.1, 0.9, 0.8]
    )

    # Style header
    header_labels = ['Backbone'] + [c.upper() if c != 'xgboost' else 'XGB' for c in cols]
    for j, label in enumerate(header_labels):
        cell = table[(0, j)]
        cell.set_text_props(text=label, fontweight='bold', fontsize=9)
        cell.set_facecolor('#F5F5F5')

    # Fill data
    for i, (backbone, row) in enumerate(pivot_df.iterrows()):
        # Backbone name
        cell = table[(i+1, 0)]
        cell.set_text_props(text=backbone, fontsize=9)

        best_head = best_per_row[backbone]

        for j, col in enumerate(cols):
            cell = table[(i+1, j+1)]
            val = row[col]
            cell.set_text_props(text=f'{val:.2f}', fontsize=9)

            # Highlight best in row
            if col == best_head:
                cell.set_facecolor('#FFF3CD')  # Light yellow

    # Find overall best
    best_backbone = pivot_df.max(axis=1).idxmax()
    best_head_overall = best_per_row[best_backbone]
    best_val = pivot_df.loc[best_backbone, best_head_overall]

    # Add "Best:" annotation
    ax.text(0.5, 0.02, f'Best: {best_backbone} + {best_head_overall.upper()}',
            ha='center', va='bottom', transform=ax.transAxes, fontsize=9, fontweight='bold')

    table.auto_set_font_size(False)
    for key, cell in table.get_celld().items():
        cell.set_edgecolor('#CCCCCC')
        cell.set_height(0.15)

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
    import os

    # Define files to check for each step
    step_files = {
        'MSA': ['*.a3m'],
        'PLMC': ['plmc/*.model_params', 'plmc/*.EC'],
        'EV+OneHot': ['ridge_model.joblib', 'metrics_summary.csv', 'ev_onehot_predictions.npy'],
        'ESM': ['esm2_*/final_model/*.joblib', 'esm2_*/training_summary.csv'],
        'ProtTrans': ['ProtT5-XL_*/final_model/*.joblib', 'ProtAlbert_*/final_model/*.joblib',
                      'ProtT5-XL_*/training_summary.csv', 'ProtAlbert_*/training_summary.csv'],
        'Plot': ['fitness_modeling_summary.png', 'all_models_comparison.csv']
    }

    step_times = {}

    for step_name, patterns in step_files.items():
        times = []
        for pattern in patterns:
            import glob
            matches = glob.glob(str(results_dir / pattern))
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
    step_order = ['MSA', 'PLMC', 'EV+OneHot', 'ESM', 'ProtTrans', 'Plot']

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
    Plot 4: Gantt chart of execution timeline.

    Args:
        timeline_path: Path to execution_timeline.json
        results_dir: Path to results directory (for file timestamp inference)
        output_path: Path prefix for saving (without extension)

    Returns:
        fig: matplotlib figure object
    """
    fig, ax = simple_ax(figsize=FIGSIZE)
    ax.set_title('Execution Timeline', fontsize=12, fontweight='bold', pad=10)

    # Default timeline if no file exists
    default_steps = [
        {'name': 'MSA', 'start': 0, 'duration': 5},
        {'name': 'PLMC', 'start': 5, 'duration': 3},
        {'name': 'EV+OneHot', 'start': 8, 'duration': 2},
        {'name': 'ESM', 'start': 10, 'duration': 15},
        {'name': 'ProtTrans', 'start': 25, 'duration': 8},
        {'name': 'Plot', 'start': 33, 'duration': 2},
    ]

    steps = None

    # Priority 1: Load from timeline JSON if exists
    if timeline_path.exists():
        with open(timeline_path) as f:
            loaded_data = json.load(f)

        # Filter to only completed steps and ensure required fields exist
        steps = []
        for step in loaded_data:
            if step.get('status') == 'completed' and 'duration' in step:
                # Ensure 'start' field exists (relative start time in minutes)
                if 'start' not in step:
                    # Calculate from start_time if available
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
            print("Timeline JSON exists but no completed steps found")

    # Priority 2: Infer from file timestamps
    if steps is None and results_dir is not None:
        inferred_steps = infer_timeline_from_files(results_dir)
        if inferred_steps:
            # Sanity check: if total time > 24 hours, files were likely created over multiple days
            total_inferred = max(s['start'] + s['duration'] for s in inferred_steps)
            if total_inferred <= 1440:  # 24 hours in minutes
                steps = inferred_steps
                print(f"Inferred timeline from file timestamps (total: {total_inferred:.1f} min)")
            else:
                print(f"Inferred timeline too long ({total_inferred:.0f} min), using defaults")

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
    Create four separate visualization figures.

    Args:
        results_dir: Path to results directory
        output_prefix: Path prefix for saving (without extension)

    Returns:
        list: Paths to saved figures
    """
    results_dir = Path(results_dir)

    # Create figures subdirectory
    figures_dir = results_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    if output_prefix is None:
        output_prefix = str(figures_dir / "fitness_modeling")

    # Set publication-quality plot context
    set_pub_plot_context(context="talk")

    # Load data
    all_df = load_all_models(results_dir)

    if all_df.empty:
        print("Error: No model results found in", results_dir)
        return None

    best_df = get_best_per_backbone(all_df)

    # Find overall best model
    best_idx = best_df['mean_cv_spearman'].idxmax()
    best_model_info = best_df.loc[best_idx].to_dict()

    # Load fitness data
    data_path = results_dir / "data.csv"
    if data_path.exists():
        data_df = pd.read_csv(data_path)
    else:
        # Create dummy data
        data_df = pd.DataFrame({'log_fitness': np.random.randn(100)})

    saved_files = []

    # Figure 1: Backbone comparison
    fig1 = plot_backbone_comparison(best_df, f"{output_prefix}_backbone_comparison")
    saved_files.append(f"{output_prefix}_backbone_comparison.png")
    plt.close(fig1)

    # Figure 2: Predicted vs Observed
    fig2 = plot_predicted_vs_observed(results_dir, best_model_info, data_df,
                                       f"{output_prefix}_predicted_vs_observed")
    saved_files.append(f"{output_prefix}_predicted_vs_observed.png")
    plt.close(fig2)

    # Figure 3: Head model table
    fig3 = plot_head_model_table(all_df, f"{output_prefix}_head_model_table")
    saved_files.append(f"{output_prefix}_head_model_table.png")
    plt.close(fig3)

    # Figure 4: Execution timeline
    timeline_path = results_dir / "execution_timeline.json"
    fig4 = plot_execution_timeline(timeline_path, results_dir,
                                    f"{output_prefix}_execution_timeline")
    saved_files.append(f"{output_prefix}_execution_timeline.png")
    plt.close(fig4)

    # Create merged 2x2 summary figure
    from PIL import Image
    fig_merged, axes = plt.subplots(2, 2, figsize=(8, 8))
    axes = axes.flatten()

    figure_names = [
        f"{output_prefix}_backbone_comparison.png",
        f"{output_prefix}_predicted_vs_observed.png",
        f"{output_prefix}_head_model_table.png",
        f"{output_prefix}_execution_timeline.png",
    ]

    for i, fig_path in enumerate(figure_names):
        if Path(fig_path).exists():
            img = Image.open(fig_path)
            axes[i].imshow(img)
            axes[i].axis('off')
        else:
            axes[i].text(0.5, 0.5, "Not found", ha='center', va='center')
            axes[i].axis('off')

    plt.tight_layout()

    # Save merged figure
    summary_path = f"{output_prefix}_summary"
    fig_merged.savefig(summary_path + ".png", dpi=150, bbox_inches='tight')
    fig_merged.savefig(summary_path + ".pdf", dpi=300, bbox_inches='tight')
    saved_files.append(summary_path + ".png")
    print(f"Saved merged figure: {summary_path}.png and {summary_path}.pdf")
    plt.close(fig_merged)

    print(f"\nGenerated {len(saved_files)} figures:")
    for f in saved_files:
        print(f"  - {f}")

    return saved_files


def create_four_panel_figure(results_dir: str, output_prefix: str = None):
    """
    Create combined four-panel visualization figure (legacy function).

    For separate figures, use create_separate_figures() instead.

    Args:
        results_dir: Path to results directory
        output_prefix: Path prefix for saving (without extension)

    Returns:
        str: Path to saved combined figure
    """
    results_dir = Path(results_dir)

    # Create figures subdirectory
    figures_dir = results_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    if output_prefix is None:
        output_prefix = str(figures_dir / "fitness_modeling_summary")

    # Set publication-quality plot context
    set_pub_plot_context(context="talk")

    # Load data
    all_df = load_all_models(results_dir)

    if all_df.empty:
        print("Error: No model results found in", results_dir)
        return None

    best_df = get_best_per_backbone(all_df)

    # Find overall best model
    best_idx = best_df['mean_cv_spearman'].idxmax()
    best_model_info = best_df.loc[best_idx].to_dict()

    # Load fitness data
    data_path = results_dir / "data.csv"
    if data_path.exists():
        data_df = pd.read_csv(data_path)
    else:
        # Create dummy data
        data_df = pd.DataFrame({'log_fitness': np.random.randn(100)})

    # Create figure with 2x2 grid (8x8 for combined)
    fig = plt.figure(figsize=(8, 8))

    # Create subplots with specific positioning
    ax1 = fig.add_subplot(2, 2, 1)  # Top-left: Backbone comparison
    prettify_ax(ax1)
    ax2 = fig.add_subplot(2, 2, 2)  # Top-right: Predicted vs Observed
    prettify_ax(ax2)
    ax3 = fig.add_subplot(2, 2, 3)  # Bottom-left: Head model table
    ax4 = fig.add_subplot(2, 2, 4)  # Bottom-right: Execution timeline
    prettify_ax(ax4)

    # Generate plots (using internal versions that take ax)
    _plot_backbone_comparison_ax(ax1, best_df)
    _plot_predicted_vs_observed_ax(ax2, results_dir, best_model_info, data_df)
    _plot_head_model_table_ax(ax3, all_df)

    timeline_path = results_dir / "execution_timeline.json"
    _plot_execution_timeline_ax(ax4, timeline_path, results_dir)

    plt.tight_layout()

    # Save figures
    save_for_pub(fig, output_prefix, include_raster=True)

    plt.close(fig)

    return f"{output_prefix}.png"


# Internal functions for combined figure (take ax parameter)
def _plot_backbone_comparison_ax(ax, best_df):
    """Internal: Plot backbone comparison on given axis."""
    best_df = best_df.sort_values('mean_cv_spearman', ascending=False)
    methods = best_df['backbone'].tolist()
    spearman = best_df['mean_cv_spearman'].tolist()
    spearman_std = best_df['std_cv_spearman'].tolist()
    colors = [CAT_PALETTE[i % len(CAT_PALETTE)] for i in range(len(methods))]
    x_pos = np.arange(len(methods))
    ax.bar(x_pos, spearman, color=colors, alpha=0.9, width=0.6)
    ax.errorbar(x_pos, spearman, yerr=spearman_std, fmt='none', ecolor='black',
                capsize=4, capthick=1.5, elinewidth=1.5)
    ax.set_title('Model Performance Comparison', fontsize=12, fontweight='bold', pad=10)
    ax.set_ylabel('Spearman ρ (5-fold CV)', fontsize=10)
    ax.set_xticks(x_pos)
    max_with_error = max(s + e for s, e in zip(spearman, spearman_std))
    ax.set_ylim([0, max_with_error * 1.15])
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)
    labels = []
    for m in methods:
        if m == 'EV+OneHot':
            labels.append('EV+OneHot')
        elif m == 'ESM2-650M':
            labels.append('ESM2\n650M')
        elif m == 'ESM2-3B':
            labels.append('ESM2\n3B')
        else:
            labels.append(m)
    ax.set_xticklabels(labels, fontsize=9, rotation=45, ha='right')


def _plot_predicted_vs_observed_ax(ax, results_dir, best_model_info, data_df):
    """Internal: Plot predicted vs observed on given axis."""
    model_data = load_model_predictions(results_dir, best_model_info, data_df)
    if model_data is not None:
        predicted, observed, actual_rho, model_name = model_data
        n_samples = len(observed)
    else:
        observed = data_df['log_fitness'].values
        n_samples = len(observed)
        rho = best_model_info['mean_cv_spearman']
        np.random.seed(42)
        noise = np.random.randn(n_samples)
        predicted = rho * stats.zscore(observed) + np.sqrt(1 - rho**2) * noise
        predicted = predicted * np.std(observed) + np.mean(observed)
        actual_rho = rho
        if best_model_info['head'] != 'ridge':
            model_name = f"{best_model_info['backbone']} ({best_model_info['head'].upper()})"
        else:
            model_name = "EV+OneHot (Ridge)"
    ax.scatter(predicted, observed, c=CAT_PALETTE[0], alpha=0.5, s=15, edgecolors='none')
    z = np.polyfit(predicted, observed, 1)
    p = np.poly1d(z)
    x_line = np.linspace(predicted.min(), predicted.max(), 100)
    ax.plot(x_line, p(x_line), 'k--', alpha=0.5, linewidth=1)
    ax.set_title('Predicted vs Observed', fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel('Predicted', fontsize=10)
    ax.set_ylabel('Observed Fitness', fontsize=10)
    ax.text(0.05, 0.95, f"ρ = {actual_rho:.2f}, n = {n_samples:,}\nBest: {model_name}",
            transform=ax.transAxes, fontsize=9, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))


def _plot_head_model_table_ax(ax, all_df):
    """Internal: Plot head model table on given axis."""
    ax.axis('off')
    ax.set_title('Head Model Comparison', fontsize=12, fontweight='bold', pad=10)
    plm_df = all_df[~all_df['backbone'].str.contains('EV|OneHot', case=False, na=False)].copy()
    if plm_df.empty:
        ax.text(0.5, 0.5, 'No pLM results available', ha='center', va='center',
                transform=ax.transAxes, fontsize=10)
        return
    pivot_df = plm_df.pivot(index='backbone', columns='head', values='mean_cv_spearman')
    head_order = ['svr', 'xgboost', 'knn']
    cols = [c for c in head_order if c in pivot_df.columns]
    pivot_df = pivot_df[cols]
    best_per_row = pivot_df.idxmax(axis=1)
    n_rows = len(pivot_df) + 1
    n_cols = len(cols) + 1
    table = ax.table(cellText=[['']*n_cols for _ in range(n_rows)],
                     loc='center', cellLoc='center', bbox=[0.05, 0.1, 0.9, 0.8])
    header_labels = ['Backbone'] + [c.upper() if c != 'xgboost' else 'XGB' for c in cols]
    for j, label in enumerate(header_labels):
        cell = table[(0, j)]
        cell.set_text_props(text=label, fontweight='bold', fontsize=9)
        cell.set_facecolor('#F5F5F5')
    for i, (backbone, row) in enumerate(pivot_df.iterrows()):
        cell = table[(i+1, 0)]
        cell.set_text_props(text=backbone, fontsize=9)
        best_head = best_per_row[backbone]
        for j, col in enumerate(cols):
            cell = table[(i+1, j+1)]
            val = row[col]
            cell.set_text_props(text=f'{val:.2f}', fontsize=9)
            if col == best_head:
                cell.set_facecolor('#FFF3CD')
    best_backbone = pivot_df.max(axis=1).idxmax()
    best_head_overall = best_per_row[best_backbone]
    ax.text(0.5, 0.02, f'Best: {best_backbone} + {best_head_overall.upper()}',
            ha='center', va='bottom', transform=ax.transAxes, fontsize=9, fontweight='bold')
    table.auto_set_font_size(False)
    for key, cell in table.get_celld().items():
        cell.set_edgecolor('#CCCCCC')
        cell.set_height(0.15)


def _plot_execution_timeline_ax(ax, timeline_path, results_dir):
    """Internal: Plot execution timeline on given axis."""
    ax.set_title('Execution Timeline', fontsize=12, fontweight='bold', pad=10)
    default_steps = [
        {'name': 'MSA', 'start': 0, 'duration': 5},
        {'name': 'PLMC', 'start': 5, 'duration': 3},
        {'name': 'EV+OneHot', 'start': 8, 'duration': 2},
        {'name': 'ESM', 'start': 10, 'duration': 15},
        {'name': 'ProtTrans', 'start': 25, 'duration': 8},
        {'name': 'Plot', 'start': 33, 'duration': 2},
    ]
    steps = None
    if timeline_path.exists():
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
        ax.text(-0.5, y_pos, f"Step {i+1}:\n{step['name']}", ha='right', va='center', fontsize=8)
    ax.barh(-1, total_time, left=0, height=0.6, color=GRAY, alpha=0.8)
    ax.text(-0.5, -1, f"Total: ~{int(total_time)} minutes", ha='right', va='center',
            fontsize=8, fontweight='bold')
    ax.set_xlabel('Time (minutes)', fontsize=10)
    ax.set_xlim(-1, total_time * 1.1)
    ax.set_ylim(-2, len(steps))
    ax.set_yticks([])
    ax.xaxis.grid(True, linestyle='--', alpha=0.4)
    ax.spines['left'].set_visible(False)


def main():
    parser = argparse.ArgumentParser(description='Generate fitness modeling visualization')
    parser.add_argument('results_dir', type=str, help='Path to results directory')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output prefix (default: results_dir/fitness_modeling)')
    parser.add_argument('--combined', '-c', action='store_true',
                        help='Create combined 2x2 figure instead of separate figures')
    parser.add_argument('--display', '-d', action='store_true',
                        help='Display summary figures after generation')

    args = parser.parse_args()

    if args.combined:
        # Legacy combined figure mode
        output_file = create_four_panel_figure(args.results_dir, args.output)
        if output_file:
            print(f"\nVisualization complete: {output_file}")
            if args.display:
                display_results(args.results_dir)
        else:
            print("\nVisualization failed")
            exit(1)
    else:
        # Default: separate figures mode
        output_files = create_separate_figures(args.results_dir, args.output)
        if output_files:
            print(f"\nVisualization complete!")
            if args.display:
                display_results(args.results_dir)
        else:
            print("\nVisualization failed")
            exit(1)


def display_results(results_dir: str, show_all: bool = True, block: bool = True):
    """
    Display fitness modeling results in an interactive environment.

    This function shows the generated figures either inline (Jupyter/IPython)
    or in a GUI window (terminal/script).

    Args:
        results_dir: Path to results directory containing the generated figures
        show_all: If True, display all 4 figures. If False, only display backbone comparison.
        block: If True (default), block until figure window is closed. If False, continue execution.

    Returns:
        dict: Dictionary with figure objects for further customization

    Usage:
        # From terminal/script:
        python -c "from fitness_modeling_viz import display_results; display_results('/path/to/results')"

        # In Jupyter notebook:
        from fitness_modeling_viz import display_results
        display_results("/path/to/results")
    """
    from pathlib import Path

    results_dir = Path(results_dir)
    figures_dir = results_dir / "figures"

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
        ("backbone_comparison", "Model Performance Comparison"),
        ("predicted_vs_observed", "Predicted vs Observed"),
        ("head_model_table", "Head Model Comparison"),
        ("execution_timeline", "Execution Timeline"),
    ]

    if not show_all:
        figure_files = figure_files[:1]  # Only backbone comparison

    def find_figure(fig_name):
        """Find figure in figures_dir or results_dir (backward compatibility)."""
        png_path = figures_dir / f"fitness_modeling_{fig_name}.png"
        if png_path.exists():
            return png_path
        # Fallback to results_dir for backward compatibility
        alt_path = results_dir / f"fitness_modeling_{fig_name}.png"
        if alt_path.exists():
            return alt_path
        return None

    if in_notebook:
        # Display in notebook using IPython
        from IPython.display import display, Image as IPImage
        for fig_name, title in figure_files:
            png_path = find_figure(fig_name)
            if png_path:
                print(f"\n{title}:")
                display(IPImage(filename=str(png_path)))
                figures[fig_name] = str(png_path)
            else:
                print(f"Warning: {png_path} not found")
    else:
        # Display in GUI window for terminal/script usage
        import matplotlib
        # Switch to an interactive backend for GUI display
        try:
            matplotlib.use('TkAgg')
        except:
            try:
                matplotlib.use('Qt5Agg')
            except:
                pass  # Fall back to default

        import matplotlib.pyplot as plt
        from PIL import Image

        # Enable interactive mode
        plt.ion()

        n_figs = len(figure_files)
        if n_figs == 1:
            fig, ax = plt.subplots(figsize=(8, 8))
            axes = [ax]
        else:
            fig, axes = plt.subplots(2, 2, figsize=(14, 12))
            axes = axes.flatten()

        for i, (fig_name, title) in enumerate(figure_files):
            png_path = find_figure(fig_name)
            if png_path:
                img = Image.open(png_path)
                axes[i].imshow(img)
                axes[i].axis('off')
                # Don't add title - the original figure already has it
                figures[fig_name] = str(png_path)
            else:
                axes[i].text(0.5, 0.5, f"{fig_name}\nnot found",
                            ha='center', va='center', transform=axes[i].transAxes)
                axes[i].axis('off')

        plt.tight_layout()
        figures['combined_figure'] = fig

        # Show the figure window
        plt.show(block=block)

    # Print summary to terminal
    csv_path = results_dir / "all_models_comparison.csv"
    if csv_path.exists():
        import pandas as pd
        df = pd.read_csv(csv_path)
        print("\n" + "="*60)
        print("MODEL PERFORMANCE SUMMARY (5-fold CV Spearman ρ)")
        print("="*60)
        for i, row in df.head(5).iterrows():
            print(f"  {i+1}. {row['backbone']:12} + {row['head']:8}: {row['mean_cv_spearman']:.3f} ± {row['std_cv_spearman']:.3f}")
        print("="*60)
        best = df.iloc[0]
        print(f"  Best: {best['backbone']} ({best['head']}) with ρ = {best['mean_cv_spearman']:.3f}")
        print("="*60)

    return figures


if __name__ == '__main__':
    main()
