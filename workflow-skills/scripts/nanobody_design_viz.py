#!/usr/bin/env python3
"""
Nanobody Design Visualization Script (BoltzGen)

Generates eight separate figures after nanobody design workflow:
1. Quality Score Distribution - Histogram of quality scores
2. Structure Quality Assessment - Scatter plot (pTM vs iPTM)
3. Normalized Metrics Heatmap - Heatmap of normalized metrics per design
4. Metrics Statistics Table - Table with Mean, Std, Min, Max
5. Quality Statistics Boxplot - Boxplots with threshold lines
6. Interface Metrics - H-bonds vs delta SASA scatter
7. Top 5 Designs Table - Table showing best designs
8. Metrics Correlation - Correlation heatmap

Each figure is saved as a separate file.
"""

import argparse
import os
from pathlib import Path
from typing import Optional, List, Dict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
import seaborn as sns

# Color palettes
CAT_PALETTE = sns.color_palette('colorblind')
GRAY = [0.5, 0.5, 0.5]

# Custom colormap (red-yellow-green)
RYG_CMAP = LinearSegmentedColormap.from_list('ryg', ['#d73027', '#fee08b', '#1a9850'])
GYR_CMAP = LinearSegmentedColormap.from_list('gyr', ['#1a9850', '#fee08b', '#d73027'])

# Nanobody-specific quality thresholds
THRESHOLDS = {
    'pTM': 0.8,           # >0.8 good
    'iPTM': 0.5,          # >0.5 good interface
    'pAE': 5,             # <5 good (lower is better)
    'H_bonds': 3,         # >=3 good
    'delta_SASA': 400,    # Higher is better
}

# Figure size for individual figures
FIGSIZE = (5, 4)
FIGSIZE_WIDE = (5, 4)
FIGSIZE_TALL = (5, 4)


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


def load_design_data(results_dir: Path) -> pd.DataFrame:
    """Load nanobody design data from results directory.

    Args:
        results_dir: Path to results directory

    Looks for:
    1. designs/final_ranked_designs/all_designs_metrics.csv
    2. all_designs_metrics.csv (in results_dir)
    """
    search_paths = [
        results_dir / 'designs' / 'final_ranked_designs' / 'all_designs_metrics.csv',
        results_dir / 'all_designs_metrics.csv',
    ]

    for csv_path in search_paths:
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            print(f"Loaded {len(df)} designs from {csv_path}")
            return df

    raise FileNotFoundError(f"No design stats CSV found in {results_dir}")


def extract_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Extract and standardize key metrics from nanobody design dataframe.

    Maps nanobody-specific columns to standardized metric names for visualization.
    """
    metrics = pd.DataFrame()

    # Design identifier
    if 'id' in df.columns:
        metrics['Design'] = df['id']
    elif 'file_name' in df.columns:
        metrics['Design'] = df['file_name']
    else:
        metrics['Design'] = [f'design_{i:03d}' for i in range(1, len(df) + 1)]

    # Status from pass_filters
    if 'pass_filters' in df.columns:
        metrics['Status'] = df['pass_filters'].apply(lambda x: 'Passed' if x else 'Failed')
    else:
        metrics['Status'] = 'Unknown'

    # Structure quality metrics
    if 'design_ptm' in df.columns:
        metrics['pTM'] = df['design_ptm']

    if 'design_to_target_iptm' in df.columns:
        metrics['iPTM'] = df['design_to_target_iptm']

    if 'min_design_to_target_pae' in df.columns:
        metrics['pAE'] = df['min_design_to_target_pae']

    # Interface metrics
    if 'plip_hbonds_refolded' in df.columns:
        metrics['H_bonds'] = df['plip_hbonds_refolded']

    if 'delta_sasa_refolded' in df.columns:
        metrics['delta_SASA'] = df['delta_sasa_refolded']

    # Liability metrics
    if 'liability_score' in df.columns:
        metrics['liability_score'] = df['liability_score']

    if 'liability_num_violations' in df.columns:
        metrics['liability_violations'] = df['liability_num_violations']

    # RMSD
    if 'filter_rmsd' in df.columns:
        metrics['filter_rmsd'] = df['filter_rmsd']

    # Pre-computed scores from BoltzGen
    if 'quality_score' in df.columns:
        metrics['quality_score'] = df['quality_score']

    if 'final_rank' in df.columns:
        metrics['final_rank'] = df['final_rank']

    return metrics


def plot_quality_score_distribution(metrics: pd.DataFrame, output_path: str = None):
    """
    Plot 1: Quality score distribution histogram.
    Uses pre-computed quality_score from BoltzGen CSV.
    """
    fig, ax = simple_ax(figsize=FIGSIZE)

    if 'quality_score' not in metrics.columns:
        ax.text(0.5, 0.5, 'No quality_score data available',
                ha='center', va='center', transform=ax.transAxes)
        if output_path:
            save_for_pub(fig, output_path)
        return fig

    scores = metrics['quality_score'].values
    status = metrics['Status'].values if 'Status' in metrics.columns else ['Unknown'] * len(metrics)
    has_failed = 'Failed' in status

    bins = np.linspace(0, 1, 11)

    if has_failed:
        # Separate passed and failed scores
        passed_mask = np.array(status) == 'Passed'
        failed_mask = np.array(status) == 'Failed'

        passed_scores = scores[passed_mask]
        failed_scores = scores[failed_mask]

        # Create stacked histogram
        ax.hist([failed_scores, passed_scores], bins=bins, stacked=True,
                color=['#d73027', '#1a9850'], alpha=0.8, edgecolor='white', linewidth=1,
                label=['Failed', 'Passed'])

        # Calculate means
        mean_passed = np.mean(passed_scores) if len(passed_scores) > 0 else 0
        mean_failed = np.mean(failed_scores) if len(failed_scores) > 0 else 0

        # Add mean lines
        if len(passed_scores) > 0:
            ax.axvline(x=mean_passed, color='darkgreen', linestyle='-', linewidth=2,
                       label=f'Mean Passed ({mean_passed:.2f})')
        if len(failed_scores) > 0:
            ax.axvline(x=mean_failed, color='darkred', linestyle=':', linewidth=2,
                       label=f'Mean Failed ({mean_failed:.2f})')

        # Add summary text
        summary = f"Passed: {len(passed_scores)} | Failed: {len(failed_scores)}"
        ax.text(0.98, 0.98, summary, transform=ax.transAxes, fontsize=10,
                ha='right', va='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    else:
        # Single histogram
        mean_score = np.mean(scores)
        counts, bin_edges, patches = ax.hist(scores, bins=bins, color=CAT_PALETTE[0],
                                              alpha=0.8, edgecolor='white', linewidth=1)

        # Add count labels on bars
        for count, patch in zip(counts, patches):
            if count > 0:
                x = patch.get_x() + patch.get_width() / 2
                y = patch.get_height()
                ax.text(x, y + 0.1, f'{int(count)}', ha='center', va='bottom', fontsize=10)

        # Add mean line
        ax.axvline(x=mean_score, color='red', linestyle='-', linewidth=2, label=f'Mean ({mean_score:.2f})')

    # Add threshold line
    ax.axvline(x=0.6, color='gray', linestyle='--', linewidth=2, label='Good threshold')

    # Add note about score source
    ax.text(0.5, 0.02, "Quality Score from BoltzGen", transform=ax.transAxes, fontsize=9,
            ha='center', va='bottom', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    ax.set_xlabel('Quality Score (0.0-1.0)', fontsize=13)
    ax.set_ylabel('Number of Designs', fontsize=13)
    ax.set_xlim(0, 1)
    ax.legend(loc='upper left', fontsize=9)

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png")

    return fig


def plot_structure_quality_assessment(metrics: pd.DataFrame, output_path: str = None):
    """
    Plot 2: Structure quality assessment scatter plot (iPTM vs pTM).
    X-axis: iPTM (interface confidence)
    Y-axis: pTM (structure confidence)
    Color: pAE (inverted, lower is better)
    """
    fig, ax = simple_ax(figsize=FIGSIZE_WIDE)

    # Get data
    ptm = metrics['pTM'].values if 'pTM' in metrics.columns else np.zeros(len(metrics))
    iptm = metrics['iPTM'].values if 'iPTM' in metrics.columns else np.zeros(len(metrics))
    pae = metrics['pAE'].values if 'pAE' in metrics.columns else np.ones(len(metrics)) * 10

    # Invert pAE for coloring (lower pAE = better = higher score)
    pae_max = max(pae.max(), 30)
    pae_inv = 1 - np.clip(pae, 0, pae_max) / pae_max

    # Small uniform dot size for clean appearance
    dot_size = 60

    # Plot all designs colored by inverted pAE
    scatter = ax.scatter(iptm, ptm, c=pae_inv, s=dot_size, cmap=RYG_CMAP,
                        alpha=0.85, edgecolors='white', linewidth=0.8, vmin=0, vmax=1)

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('pAE Quality (inverted)', fontsize=12)

    # Add threshold lines
    ax.axhline(y=THRESHOLDS['pTM'], color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axvline(x=THRESHOLDS['iPTM'], color='gray', linestyle='--', linewidth=1.5, alpha=0.7)

    ax.set_xlabel('iPTM (Interface Confidence)', fontsize=13)
    ax.set_ylabel('pTM (Structure Confidence)', fontsize=13)

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png")

    return fig


def plot_normalized_heatmap(metrics: pd.DataFrame, output_path: str = None):
    """
    Plot 3: Normalized metrics heatmap.
    Shows pTM, iPTM, pAE(inv), H_bonds, delta_SASA for each design.
    """
    # Prepare data first to determine dimensions
    n_designs = len(metrics)
    design_labels = [str(i+1).zfill(3) for i in range(n_designs)]

    # Normalize metrics
    data = []
    row_labels = []

    if 'pTM' in metrics.columns:
        data.append(metrics['pTM'].values)
        row_labels.append('pTM')

    if 'iPTM' in metrics.columns:
        data.append(metrics['iPTM'].values)
        row_labels.append('iPTM')

    if 'pAE' in metrics.columns:
        pae = metrics['pAE'].values
        pae_inv = 1 - (pae - pae.min()) / (pae.max() - pae.min() + 1e-6)
        data.append(pae_inv)
        row_labels.append('pAE (inv)')

    if 'H_bonds' in metrics.columns:
        hbonds = metrics['H_bonds'].values
        hbonds_norm = np.clip(hbonds, 0, 10) / 10  # Cap at 10
        data.append(hbonds_norm)
        row_labels.append('H-bonds')

    if 'delta_SASA' in metrics.columns:
        sasa = metrics['delta_SASA'].values
        sasa_norm = (sasa - sasa.min()) / (sasa.max() - sasa.min() + 1e-6)
        data.append(sasa_norm)
        row_labels.append('delta SASA')

    data = np.array(data)
    n_rows = len(row_labels)

    # Calculate figure size to make heatmap region square
    cell_size = 0.6
    fig_width = n_designs * cell_size + 2.5
    fig_height = n_rows * cell_size + 1.5
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    # Create heatmap with square cells
    im = ax.imshow(data, cmap=RYG_CMAP, aspect='equal', vmin=0, vmax=1)

    # Add text annotations
    for i in range(len(row_labels)):
        for j in range(n_designs):
            text = f'{data[i, j]:.2f}'
            color = 'white' if data[i, j] < 0.4 or data[i, j] > 0.7 else 'black'
            ax.text(j, i, text, ha='center', va='center', fontsize=9, color=color)

    # Set ticks
    ax.set_xticks(np.arange(n_designs))
    ax.set_xticklabels(design_labels, fontsize=10)
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=10)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Normalized Score (0-1)', fontsize=10)

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png")

    return fig


def plot_metrics_statistics_table(metrics: pd.DataFrame, output_path: str = None):
    """
    Plot 4: Metrics statistics table (Mean, Std, Min, Max).
    """
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.axis('off')

    # Calculate statistics
    stats_data = []
    metric_names = ['pTM', 'iPTM', 'pAE', 'H_bonds', 'delta_SASA']

    for metric in metric_names:
        if metric in metrics.columns:
            values = metrics[metric].values
            mean_val = np.mean(values)
            std_val = np.std(values)
            min_val = np.min(values)
            max_val = np.max(values)

            stats_data.append([metric, f'{mean_val:.2f}', f'{std_val:.2f}',
                              f'{min_val:.2f}', f'{max_val:.2f}'])

    # Create table
    col_labels = ['Metric', 'Mean', 'Std', 'Min', 'Max']
    table = ax.table(cellText=stats_data, colLabels=col_labels,
                     loc='center', cellLoc='center',
                     colWidths=[0.18, 0.15, 0.15, 0.15, 0.15])

    # Style table
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.8)

    # Style header
    for j in range(len(col_labels)):
        table[(0, j)].set_facecolor('#404040')
        table[(0, j)].set_text_props(color='white', fontweight='bold')

    # Style alternating rows
    for i in range(1, len(stats_data) + 1):
        for j in range(len(col_labels)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f0f0f0')

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png")

    return fig


def plot_quality_boxplot(metrics: pd.DataFrame, output_path: str = None):
    """
    Plot 5: Quality statistics boxplot with threshold lines and outliers.
    """
    fig, axes = plt.subplots(1, 4, figsize=(10, 4))

    metric_configs = [
        ('pTM', 'pTM', THRESHOLDS['pTM'], True),
        ('iPTM', 'iPTM', THRESHOLDS['iPTM'], True),
        ('pAE', 'pAE', THRESHOLDS['pAE'], False),
        ('H_bonds', 'H-bonds', THRESHOLDS['H_bonds'], True),
    ]

    for ax, (metric, label, threshold, higher_better) in zip(axes, metric_configs):
        if metric in metrics.columns:
            data = metrics[metric].values

            # Create boxplot with outliers shown
            bp = ax.boxplot(data, patch_artist=True, widths=0.6, showfliers=True,
                           flierprops=dict(marker='o', markerfacecolor='red', markersize=6,
                                          markeredgecolor='darkred', alpha=0.7))
            bp['boxes'][0].set_facecolor(CAT_PALETTE[0])
            bp['boxes'][0].set_alpha(0.7)

            # Add threshold line
            ax.axhline(y=threshold, color='green', linestyle='--', linewidth=2, alpha=0.8)

            # Style
            ax.set_xlabel(label, fontsize=11)
            ax.set_xticklabels([''])
            prettify_ax(ax)
        else:
            ax.text(0.5, 0.5, f'No {metric} data', ha='center', va='center', transform=ax.transAxes)
            ax.axis('off')

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png")

    return fig


def plot_interface_metrics(metrics: pd.DataFrame, output_path: str = None):
    """
    Plot 6: Interface metrics scatter (H-bonds vs delta_SASA).
    X-axis: H_bonds
    Y-axis: delta_SASA
    Color: iPTM
    """
    fig, ax = simple_ax(figsize=FIGSIZE)

    # Get data
    hbonds = metrics['H_bonds'].values if 'H_bonds' in metrics.columns else np.zeros(len(metrics))
    sasa = metrics['delta_SASA'].values if 'delta_SASA' in metrics.columns else np.zeros(len(metrics))
    iptm = metrics['iPTM'].values if 'iPTM' in metrics.columns else np.ones(len(metrics)) * 0.5

    # Create scatter plot
    scatter = ax.scatter(hbonds, sasa, c=iptm, cmap='plasma',
                        s=60, alpha=0.85, edgecolors='white', linewidth=0.8)

    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('iPTM', fontsize=12)

    # Add threshold lines
    ax.axvline(x=THRESHOLDS['H_bonds'], color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axhline(y=THRESHOLDS['delta_SASA'], color='gray', linestyle='--', linewidth=1.5, alpha=0.7)

    ax.set_xlabel('H-bonds', fontsize=13)
    ax.set_ylabel('delta SASA', fontsize=13)

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png")

    return fig


def plot_top5_designs_table(metrics: pd.DataFrame, output_path: str = None):
    """
    Plot 7: Top 5 designs table with metrics.
    Ranks by: 1) Status (Passed first), 2) quality_score or final_rank.
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis('off')

    # Get metrics for ranking
    status = metrics['Status'].values if 'Status' in metrics.columns else ['Unknown'] * len(metrics)

    # Use final_rank if available, otherwise quality_score
    if 'final_rank' in metrics.columns:
        rank_values = metrics['final_rank'].values
    elif 'quality_score' in metrics.columns:
        rank_values = -metrics['quality_score'].values  # Negate for descending order
    else:
        rank_values = np.arange(len(metrics))

    # Create ranking: Status first (Passed=0, Failed=1), then by rank
    status_score = np.array([0 if s == 'Passed' else 1 for s in status])
    combined_rank = status_score * 1000 + rank_values

    n_designs = min(5, len(metrics))
    ranked_indices = np.argsort(combined_rank)[:n_designs]

    # Prepare table data
    table_data = []
    colors = []
    for rank, idx in enumerate(ranked_indices, 1):
        design = metrics['Design'].iloc[idx] if 'Design' in metrics.columns else f'design_{idx+1:03d}'
        ptm_val = metrics['pTM'].iloc[idx] if 'pTM' in metrics.columns else 0
        iptm_val = metrics['iPTM'].iloc[idx] if 'iPTM' in metrics.columns else 0
        pae_val = metrics['pAE'].iloc[idx] if 'pAE' in metrics.columns else 0
        hbonds_val = metrics['H_bonds'].iloc[idx] if 'H_bonds' in metrics.columns else 0

        # Get status
        design_status = status[idx]

        # Color based on status
        if design_status == 'Passed':
            row_color = ['#90EE90'] * 7
        else:
            row_color = ['#FFB6C1'] * 7

        table_data.append([rank, design, f'{ptm_val:.2f}', f'{iptm_val:.2f}',
                          f'{pae_val:.1f}', f'{int(hbonds_val)}', design_status])
        colors.append(row_color)

    # Create table
    col_labels = ['#', 'Design', 'pTM', 'iPTM', 'pAE', 'H-bonds', 'Status']

    table = ax.table(cellText=table_data, colLabels=col_labels,
                     loc='center', cellLoc='center',
                     cellColours=colors,
                     colWidths=[0.06, 0.28, 0.10, 0.10, 0.10, 0.10, 0.12])

    # Style table
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 2.0)

    # Style header
    for j in range(len(col_labels)):
        table[(0, j)].set_facecolor('#404040')
        table[(0, j)].set_text_props(color='white', fontweight='bold')

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png")

    return fig


def plot_metrics_correlation(metrics: pd.DataFrame, output_path: str = None):
    """
    Plot 8: Correlation heatmap of metrics.
    """
    fig, ax = plt.subplots(figsize=FIGSIZE)

    # Select numeric columns
    metric_cols = ['pTM', 'iPTM', 'pAE', 'H_bonds', 'delta_SASA']
    available_cols = [col for col in metric_cols if col in metrics.columns]

    if len(available_cols) < 2:
        ax.text(0.5, 0.5, 'Insufficient metrics for correlation',
                ha='center', va='center', transform=ax.transAxes)
        ax.axis('off')
        if output_path:
            save_for_pub(fig, output_path)
        return fig

    # Calculate correlation matrix
    corr_matrix = metrics[available_cols].corr()

    # Create heatmap
    im = ax.imshow(corr_matrix.values, cmap='RdYlGn', vmin=-1, vmax=1, aspect='auto')

    # Add text annotations
    for i in range(len(available_cols)):
        for j in range(len(available_cols)):
            val = corr_matrix.iloc[i, j]
            color = 'white' if abs(val) > 0.6 else 'black'
            ax.text(j, i, f'{val:.2f}', ha='center', va='center', fontsize=12,
                   fontweight='bold', color=color)

    # Set ticks
    ax.set_xticks(np.arange(len(available_cols)))
    ax.set_xticklabels(available_cols, fontsize=11)
    ax.set_yticks(np.arange(len(available_cols)))
    ax.set_yticklabels(available_cols, fontsize=11)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Correlation', fontsize=10)

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png")

    return fig


def create_merged_figure(metrics: pd.DataFrame, output_path: str = None) -> plt.Figure:
    """
    Create a merged figure with all 8 panels arranged in a 2x4 grid.
    """
    fig = plt.figure(figsize=(16, 8))

    panel_titles = [
        'A. Quality Score Distribution',
        'B. Structure Quality (pTM vs iPTM)',
        'C. Normalized Metrics Heatmap',
        'D. Metrics Statistics',
        'E. Quality Boxplot',
        'F. Interface Metrics',
        'G. Top 5 Designs',
        'H. Metrics Correlation',
    ]

    # --- Panel A: Quality Score Distribution ---
    ax1 = fig.add_subplot(2, 4, 1)
    if 'quality_score' in metrics.columns:
        scores = metrics['quality_score'].values
        status = metrics['Status'].values if 'Status' in metrics.columns else ['Unknown'] * len(metrics)
        has_failed = 'Failed' in status
        bins = np.linspace(0, 1, 11)

        if has_failed:
            passed_mask = np.array(status) == 'Passed'
            failed_mask = np.array(status) == 'Failed'
            passed_scores = scores[passed_mask]
            failed_scores = scores[failed_mask]
            ax1.hist([failed_scores, passed_scores], bins=bins, stacked=True,
                    color=['#d73027', '#1a9850'], alpha=0.8, edgecolor='white', linewidth=1,
                    label=['Failed', 'Passed'])
        else:
            mean_score = np.mean(scores)
            ax1.hist(scores, bins=bins, color=CAT_PALETTE[0], alpha=0.8, edgecolor='white', linewidth=1)
            ax1.axvline(x=mean_score, color='red', linestyle='-', linewidth=1.5, label=f'Mean ({mean_score:.2f})')

        ax1.axvline(x=0.6, color='gray', linestyle='--', linewidth=1.5, label='Threshold')
        ax1.set_xlabel('Quality Score', fontsize=9)
        ax1.set_ylabel('Count', fontsize=9)
        ax1.set_xlim(0, 1)
        ax1.legend(loc='upper left', fontsize=6)
    ax1.set_title(panel_titles[0], fontsize=10, fontweight='bold', loc='left')
    prettify_ax(ax1)

    # --- Panel B: Structure Quality Assessment ---
    ax2 = fig.add_subplot(2, 4, 2)
    ptm = metrics['pTM'].values if 'pTM' in metrics.columns else np.zeros(len(metrics))
    iptm = metrics['iPTM'].values if 'iPTM' in metrics.columns else np.zeros(len(metrics))
    pae = metrics['pAE'].values if 'pAE' in metrics.columns else np.ones(len(metrics)) * 10
    pae_max = max(pae.max(), 30)
    pae_inv = 1 - np.clip(pae, 0, pae_max) / pae_max
    dot_size = 40
    scatter2 = ax2.scatter(iptm, ptm, c=pae_inv, s=dot_size, cmap=RYG_CMAP,
                          alpha=0.85, edgecolors='white', linewidth=0.5, vmin=0, vmax=1)
    ax2.axhline(y=THRESHOLDS['pTM'], color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax2.axvline(x=THRESHOLDS['iPTM'], color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax2.set_xlabel('iPTM', fontsize=9)
    ax2.set_ylabel('pTM', fontsize=9)
    ax2.set_title(panel_titles[1], fontsize=10, fontweight='bold', loc='left')
    prettify_ax(ax2)

    # --- Panel C: Normalized Heatmap ---
    ax3 = fig.add_subplot(2, 4, 3)
    n_designs = len(metrics)
    design_labels = [str(i+1).zfill(3) for i in range(n_designs)]
    data = []
    row_labels = []
    if 'pTM' in metrics.columns:
        data.append(metrics['pTM'].values)
        row_labels.append('pTM')
    if 'iPTM' in metrics.columns:
        data.append(metrics['iPTM'].values)
        row_labels.append('iPTM')
    if 'pAE' in metrics.columns:
        pae = metrics['pAE'].values
        pae_inv = 1 - (pae - pae.min()) / (pae.max() - pae.min() + 1e-6)
        data.append(pae_inv)
        row_labels.append('pAE (inv)')
    if 'H_bonds' in metrics.columns:
        hbonds = metrics['H_bonds'].values
        hbonds_norm = np.clip(hbonds, 0, 10) / 10
        data.append(hbonds_norm)
        row_labels.append('H-bonds')
    data = np.array(data)
    im3 = ax3.imshow(data, cmap=RYG_CMAP, aspect='auto', vmin=0, vmax=1)
    for i in range(len(row_labels)):
        for j in range(n_designs):
            text = f'{data[i, j]:.2f}'
            color = 'white' if data[i, j] < 0.4 or data[i, j] > 0.7 else 'black'
            ax3.text(j, i, text, ha='center', va='center', fontsize=7, color=color)
    ax3.set_xticks(np.arange(n_designs))
    ax3.set_xticklabels(design_labels, fontsize=8)
    ax3.set_yticks(np.arange(len(row_labels)))
    ax3.set_yticklabels(row_labels, fontsize=8)
    ax3.set_title(panel_titles[2], fontsize=10, fontweight='bold', loc='left')

    # --- Panel D: Metrics Statistics Table ---
    ax4 = fig.add_subplot(2, 4, 4)
    ax4.axis('off')
    stats_data = []
    metric_names = ['pTM', 'iPTM', 'pAE', 'H_bonds', 'delta_SASA']
    for metric in metric_names:
        if metric in metrics.columns:
            values = metrics[metric].values
            mean_val = np.mean(values)
            std_val = np.std(values)
            min_val = np.min(values)
            max_val = np.max(values)
            stats_data.append([metric, f'{mean_val:.2f}', f'{std_val:.2f}',
                              f'{min_val:.2f}', f'{max_val:.2f}'])
    col_labels = ['Metric', 'Mean', 'Std', 'Min', 'Max']
    table4 = ax4.table(cellText=stats_data, colLabels=col_labels,
                       loc='center', cellLoc='center',
                       colWidths=[0.20, 0.16, 0.16, 0.16, 0.16])
    table4.auto_set_font_size(False)
    table4.set_fontsize(9)
    table4.scale(1.0, 1.6)
    for j in range(len(col_labels)):
        table4[(0, j)].set_facecolor('#404040')
        table4[(0, j)].set_text_props(color='white', fontweight='bold')
    ax4.set_title(panel_titles[3], fontsize=10, fontweight='bold', loc='left')

    # --- Panel E: Quality Boxplot ---
    ax5 = fig.add_subplot(2, 4, 5)
    metric_data = []
    metric_labels = []
    for metric in ['pTM', 'iPTM', 'pAE', 'H_bonds']:
        if metric in metrics.columns:
            metric_data.append(metrics[metric].values)
            metric_labels.append(metric)
    if metric_data:
        bp = ax5.boxplot(metric_data, patch_artist=True, showfliers=True,
                        flierprops=dict(marker='o', markerfacecolor='red', markersize=4,
                                       markeredgecolor='darkred', alpha=0.7))
        colors = [CAT_PALETTE[i % len(CAT_PALETTE)] for i in range(len(metric_data))]
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax5.set_xticklabels(metric_labels, fontsize=8)
    ax5.set_title(panel_titles[4], fontsize=10, fontweight='bold', loc='left')
    prettify_ax(ax5)

    # --- Panel F: Interface Metrics ---
    ax6 = fig.add_subplot(2, 4, 6)
    hbonds = metrics['H_bonds'].values if 'H_bonds' in metrics.columns else np.zeros(len(metrics))
    sasa = metrics['delta_SASA'].values if 'delta_SASA' in metrics.columns else np.zeros(len(metrics))
    iptm = metrics['iPTM'].values if 'iPTM' in metrics.columns else np.ones(len(metrics)) * 0.5
    scatter6 = ax6.scatter(hbonds, sasa, c=iptm, cmap='plasma',
                          s=60, alpha=0.8, edgecolors='white', linewidth=0.5)
    ax6.set_xlabel('H-bonds', fontsize=9)
    ax6.set_ylabel('delta SASA', fontsize=9)
    ax6.set_title(panel_titles[5], fontsize=10, fontweight='bold', loc='left')
    prettify_ax(ax6)

    # --- Panel G: Top 5 Designs Table ---
    ax7 = fig.add_subplot(2, 4, 7)
    ax7.axis('off')
    status_arr = metrics['Status'].values if 'Status' in metrics.columns else ['Unknown'] * len(metrics)
    if 'final_rank' in metrics.columns:
        rank_values = metrics['final_rank'].values
    elif 'quality_score' in metrics.columns:
        rank_values = -metrics['quality_score'].values
    else:
        rank_values = np.arange(len(metrics))
    status_score = np.array([0 if s == 'Passed' else 1 for s in status_arr])
    combined_rank = status_score * 1000 + rank_values
    n_top = min(5, len(metrics))
    ranked_indices = np.argsort(combined_rank)[:n_top]
    table_data = []
    colors = []
    for rank, idx in enumerate(ranked_indices, 1):
        design = metrics['Design'].iloc[idx] if 'Design' in metrics.columns else f'design_{idx+1:03d}'
        short_name = str(design).split('_')[-1] if '_' in str(design) else str(design)[-10:]
        ptm = metrics['pTM'].iloc[idx] if 'pTM' in metrics.columns else 0
        iptm = metrics['iPTM'].iloc[idx] if 'iPTM' in metrics.columns else 0
        status = status_arr[idx]
        if status == 'Passed':
            row_color = ['#90EE90'] * 5
        else:
            row_color = ['#FFB6C1'] * 5
        table_data.append([rank, short_name, f'{ptm:.2f}', f'{iptm:.2f}', status])
        colors.append(row_color)
    col_labels = ['#', 'Design', 'pTM', 'iPTM', 'Status']
    table7 = ax7.table(cellText=table_data, colLabels=col_labels,
                       loc='center', cellLoc='center', cellColours=colors,
                       colWidths=[0.08, 0.3, 0.15, 0.15, 0.2])
    table7.auto_set_font_size(False)
    table7.set_fontsize(9)
    table7.scale(1.0, 1.8)
    for j in range(len(col_labels)):
        table7[(0, j)].set_facecolor('#404040')
        table7[(0, j)].set_text_props(color='white', fontweight='bold')
    ax7.set_title(panel_titles[6], fontsize=10, fontweight='bold', loc='left')

    # --- Panel H: Metrics Correlation ---
    ax8 = fig.add_subplot(2, 4, 8)
    metric_cols = ['pTM', 'iPTM', 'pAE', 'H_bonds', 'delta_SASA']
    available_cols = [col for col in metric_cols if col in metrics.columns]
    if len(available_cols) >= 2:
        corr_matrix = metrics[available_cols].corr()
        im8 = ax8.imshow(corr_matrix.values, cmap='RdYlGn', vmin=-1, vmax=1, aspect='auto')
        for i in range(len(available_cols)):
            for j in range(len(available_cols)):
                val = corr_matrix.iloc[i, j]
                color = 'white' if abs(val) > 0.6 else 'black'
                ax8.text(j, i, f'{val:.2f}', ha='center', va='center', fontsize=9,
                        fontweight='bold', color=color)
        ax8.set_xticks(np.arange(len(available_cols)))
        ax8.set_xticklabels(available_cols, fontsize=8)
        ax8.set_yticks(np.arange(len(available_cols)))
        ax8.set_yticklabels(available_cols, fontsize=8)
    ax8.set_title(panel_titles[7], fontsize=10, fontweight='bold', loc='left')

    # Adjust spacing
    plt.subplots_adjust(left=0.05, right=0.98, top=0.95, bottom=0.08, wspace=0.25, hspace=0.3)

    if output_path:
        fig.savefig(output_path + ".png", dpi=200, bbox_inches='tight', facecolor='white')
        fig.savefig(output_path + ".pdf", dpi=300, bbox_inches='tight', facecolor='white')
        print(f"Saved merged figure: {output_path}.png and {output_path}.pdf")

    return fig


def create_all_figures(results_dir: str, output_prefix: str = None, merged: bool = True) -> List[str]:
    """
    Create all eight visualization figures.

    Args:
        results_dir: Path to results directory
        output_prefix: Path prefix for saving (without extension)
        merged: If True, also generate a merged figure with all 8 panels

    Returns:
        list: Paths to saved figures
    """
    results_dir = Path(results_dir)

    # Create figures subdirectory
    figures_dir = results_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    if output_prefix is None:
        output_prefix = str(figures_dir / "nanobody_design")

    # Set publication-quality plot context
    set_pub_plot_context(context="talk")

    # Load data
    df = load_design_data(results_dir)
    metrics = extract_metrics(df)

    if len(metrics) == 0:
        print("Error: No design data found")
        return None

    # Print summary
    n_passed = (metrics['Status'] == 'Passed').sum() if 'Status' in metrics.columns else 0
    n_failed = (metrics['Status'] == 'Failed').sum() if 'Status' in metrics.columns else 0
    print(f"Status: {n_passed} Passed, {n_failed} Failed")

    saved_files = []

    # Figure 1: Quality Score Distribution
    fig1 = plot_quality_score_distribution(metrics, f"{output_prefix}_quality_score")
    saved_files.append(f"{output_prefix}_quality_score.png")
    plt.close(fig1)

    # Figure 2: Structure Quality Assessment
    fig2 = plot_structure_quality_assessment(metrics, f"{output_prefix}_structure_quality")
    saved_files.append(f"{output_prefix}_structure_quality.png")
    plt.close(fig2)

    # Figure 3: Normalized Heatmap
    fig3 = plot_normalized_heatmap(metrics, f"{output_prefix}_normalized_heatmap")
    saved_files.append(f"{output_prefix}_normalized_heatmap.png")
    plt.close(fig3)

    # Figure 4: Metrics Statistics Table
    fig4 = plot_metrics_statistics_table(metrics, f"{output_prefix}_statistics_table")
    saved_files.append(f"{output_prefix}_statistics_table.png")
    plt.close(fig4)

    # Figure 5: Quality Boxplot
    fig5 = plot_quality_boxplot(metrics, f"{output_prefix}_quality_boxplot")
    saved_files.append(f"{output_prefix}_quality_boxplot.png")
    plt.close(fig5)

    # Figure 6: Interface Metrics
    fig6 = plot_interface_metrics(metrics, f"{output_prefix}_interface_metrics")
    saved_files.append(f"{output_prefix}_interface_metrics.png")
    plt.close(fig6)

    # Figure 7: Top 5 Designs Table
    fig7 = plot_top5_designs_table(metrics, f"{output_prefix}_top5_designs")
    saved_files.append(f"{output_prefix}_top5_designs.png")
    plt.close(fig7)

    # Figure 8: Metrics Correlation
    fig8 = plot_metrics_correlation(metrics, f"{output_prefix}_correlation")
    saved_files.append(f"{output_prefix}_correlation.png")
    plt.close(fig8)

    # Generate merged figure if requested
    if merged:
        merged_fig = create_merged_figure(metrics, f"{output_prefix}_summary")
        saved_files.append(f"{output_prefix}_summary.png")
        plt.close(merged_fig)

    print(f"\nGenerated {len(saved_files)} figures:")
    for f in saved_files:
        print(f"  - {f}")

    return saved_files


def show_summary_figure(results_dir: str, output_prefix: str = None, block: bool = True) -> plt.Figure:
    """
    Display the merged summary figure interactively.
    """
    results_dir = Path(results_dir)
    figures_dir = results_dir / "figures"

    if output_prefix is None:
        output_prefix = str(figures_dir / "nanobody_design")

    summary_path = Path(f"{output_prefix}_summary.png")

    if not summary_path.exists():
        print(f"Summary figure not found at {summary_path}")
        print("Run create_all_figures() first to generate the figures.")
        return None

    # Check if in notebook
    in_notebook = False
    try:
        from IPython import get_ipython
        ipython = get_ipython()
        if ipython is not None and 'IPKernelApp' in ipython.config:
            in_notebook = True
    except (ImportError, AttributeError):
        pass

    if in_notebook:
        from IPython.display import display, Image as IPImage
        print("Nanobody Design Summary:")
        display(IPImage(filename=str(summary_path)))
        return None
    else:
        import matplotlib
        try:
            matplotlib.use('TkAgg')
        except:
            try:
                matplotlib.use('Qt5Agg')
            except:
                pass

        from PIL import Image

        plt.ion()
        img = Image.open(summary_path)

        fig, ax = plt.subplots(figsize=(16, 8))
        ax.imshow(img)
        ax.axis('off')
        ax.set_title('Nanobody Design Summary', fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.show(block=block)

        return fig


def main():
    parser = argparse.ArgumentParser(description='Generate nanobody design visualization')
    parser.add_argument('results_dir', type=str, help='Path to results directory')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output prefix (default: results_dir/figures/nanobody_design)')
    parser.add_argument('--display', '-d', action='store_true',
                        help='Display summary figure after generation')

    args = parser.parse_args()

    output_files = create_all_figures(args.results_dir, args.output)

    if output_files:
        print(f"\nVisualization complete!")
        if args.display:
            show_summary_figure(args.results_dir, args.output)
    else:
        print("\nVisualization failed")
        exit(1)


if __name__ == '__main__':
    main()
