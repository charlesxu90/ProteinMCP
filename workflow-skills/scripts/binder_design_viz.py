#!/usr/bin/env python3
"""
Binder Design Visualization Script

Generates eight separate figures after binder design workflow:
1. Composite Score Distribution - Histogram of quality scores
2. Quality Assessment - Scatter plot (pLDDT vs Interface, colored by pAE)
3. Normalized Metrics Heatmap - Heatmap of normalized metrics per design
4. Metrics Statistics Table - Table with Mean, Std, Min, Max, Pass Rate
5. Quality Statistics Boxplot - Boxplots with threshold lines
6. SASA vs Binding Energy - Scatter plot colored by pLDDT
7. Top 5 Designs Table - Table showing best designs
8. Metrics Correlation - Correlation heatmap

Each figure is saved as a separate file.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.table import Table
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns

# Color palettes
CAT_PALETTE = sns.color_palette('colorblind')
GRAY = [0.5, 0.5, 0.5]

# Custom colormap (red-yellow-green)
RYG_CMAP = LinearSegmentedColormap.from_list('ryg', ['#d73027', '#fee08b', '#1a9850'])
GYR_CMAP = LinearSegmentedColormap.from_list('gyr', ['#1a9850', '#fee08b', '#d73027'])

# Quality thresholds
THRESHOLDS = {
    'pLDDT': 80,      # Higher is better, threshold for "good"
    'pAE': 4,         # Lower is better, threshold for "good"
    'Interface': -13, # Lower (more negative) is better
    'pTM': 0.8,       # Higher is better
}

# Figure size
FIGSIZE = (6, 5)
FIGSIZE_WIDE = (8, 5)
FIGSIZE_TALL = (6, 6)


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
    """Load design data from results directory.

    Tries multiple CSV files in order of preference:
    1. final_design_stats.csv
    2. mpnn_design_stats.csv
    3. trajectory_stats.csv
    """
    for csv_name in ['final_design_stats.csv', 'mpnn_design_stats.csv', 'trajectory_stats.csv']:
        csv_path = results_dir / 'designs' / csv_name
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            print(f"Loaded {len(df)} designs from {csv_path}")
            return df

    # Try root directory
    for csv_name in ['final_design_stats.csv', 'mpnn_design_stats.csv']:
        csv_path = results_dir / csv_name
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            print(f"Loaded {len(df)} designs from {csv_path}")
            return df

    raise FileNotFoundError(f"No design stats CSV found in {results_dir}")


def extract_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Extract key metrics from design dataframe."""
    metrics = pd.DataFrame()

    # Try different column naming conventions
    if 'Design' in df.columns:
        metrics['Design'] = df['Design']
    elif 'design' in df.columns:
        metrics['Design'] = df['design']
    else:
        metrics['Design'] = [f'design_{i:03d}' for i in range(1, len(df) + 1)]

    # pLDDT
    for col in ['Average_pLDDT', 'pLDDT', 'average_pLDDT']:
        if col in df.columns:
            metrics['pLDDT'] = df[col] * 100 if df[col].max() <= 1 else df[col]
            break

    # pTM
    for col in ['Average_pTM', 'pTM', 'average_pTM']:
        if col in df.columns:
            metrics['pTM'] = df[col]
            break

    # pAE
    for col in ['Average_pAE', 'pAE', 'average_pAE']:
        if col in df.columns:
            metrics['pAE'] = df[col]
            break

    # Interface Score (dG or similar)
    for col in ['Average_dG', 'dG', 'interface_score', 'Interface_Score']:
        if col in df.columns:
            metrics['Interface'] = df[col]
            break

    # SASA
    for col in ['Average_dSASA', 'dSASA', 'sasa', 'SASA']:
        if col in df.columns:
            metrics['SASA'] = df[col]
            break

    # Binding Energy (same as dG often)
    if 'Interface' in metrics.columns:
        metrics['BindingEnergy'] = metrics['Interface']

    return metrics


def calculate_composite_score(metrics: pd.DataFrame) -> np.ndarray:
    """Calculate composite quality score.

    Composite Score = 0.3*pLDDT(norm) + 0.3*pAE(inv,norm) + 0.2*Interface(inv,norm) + 0.2*pTM
    """
    scores = np.zeros(len(metrics))

    # Normalize pLDDT (0-100 -> 0-1)
    if 'pLDDT' in metrics.columns:
        plddt_norm = metrics['pLDDT'].values / 100
        scores += 0.3 * plddt_norm

    # Normalize pAE (inverted, lower is better)
    if 'pAE' in metrics.columns:
        pae = metrics['pAE'].values
        pae_inv = 1 - (pae - pae.min()) / (pae.max() - pae.min() + 1e-6)
        scores += 0.3 * pae_inv

    # Normalize Interface (inverted, more negative is better)
    if 'Interface' in metrics.columns:
        interface = metrics['Interface'].values
        interface_inv = 1 - (interface - interface.min()) / (interface.max() - interface.min() + 1e-6)
        scores += 0.2 * interface_inv

    # pTM (already 0-1)
    if 'pTM' in metrics.columns:
        scores += 0.2 * metrics['pTM'].values

    return scores


def plot_composite_score_distribution(metrics: pd.DataFrame, output_path: str = None):
    """
    Plot 1: Composite score distribution histogram.
    """
    fig, ax = simple_ax(figsize=FIGSIZE)

    scores = calculate_composite_score(metrics)
    mean_score = np.mean(scores)

    # Create histogram
    bins = np.linspace(0, 1, 11)
    counts, bin_edges, patches = ax.hist(scores, bins=bins, color=CAT_PALETTE[0],
                                          alpha=0.8, edgecolor='white', linewidth=1)

    # Add count labels on bars
    for count, patch in zip(counts, patches):
        if count > 0:
            x = patch.get_x() + patch.get_width() / 2
            y = patch.get_height()
            ax.text(x, y + 0.1, f'{int(count)}', ha='center', va='bottom', fontsize=10)

    # Add threshold and mean lines
    ax.axvline(x=0.6, color='green', linestyle='--', linewidth=2, label='Good threshold')
    ax.axvline(x=mean_score, color='red', linestyle='-', linewidth=2, label=f'Mean ({mean_score:.2f})')

    # Add formula box
    formula = "Composite Score = 0.3×pLDDT(norm) + 0.3×pAE(inv,norm)\n+ 0.2×Interface(inv,norm) + 0.2×pTM"
    ax.text(0.5, 0.15, formula, transform=ax.transAxes, fontsize=9,
            ha='center', va='bottom', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    ax.set_xlabel('Composite Quality Score (0.0-1.0)', fontsize=11)
    ax.set_ylabel('Number of Designs (0-6)', fontsize=11)
    ax.set_xlim(0, 1)
    ax.legend(loc='upper left', fontsize=9)

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png")

    return fig


def plot_quality_assessment(metrics: pd.DataFrame, output_path: str = None):
    """
    Plot 2: Quality assessment scatter plot (pLDDT vs Interface Score).
    Colored by pAE, size by pTM.
    """
    fig, ax = simple_ax(figsize=FIGSIZE_WIDE)

    # Get data
    plddt = metrics['pLDDT'].values if 'pLDDT' in metrics.columns else np.zeros(len(metrics))
    interface = metrics['Interface'].values if 'Interface' in metrics.columns else np.zeros(len(metrics))
    pae = metrics['pAE'].values if 'pAE' in metrics.columns else np.ones(len(metrics)) * 5
    ptm = metrics['pTM'].values if 'pTM' in metrics.columns else np.ones(len(metrics)) * 0.5

    # Calculate composite score for coloring
    composite = calculate_composite_score(metrics)

    # Create size based on pAE (lower pAE = larger marker)
    sizes = 100 + (10 - pae) * 50  # Scale sizes
    sizes = np.clip(sizes, 50, 400)

    # Color by composite score
    scatter = ax.scatter(interface, plddt, c=composite, s=sizes, cmap=RYG_CMAP,
                        alpha=0.8, edgecolors='white', linewidth=1, vmin=0, vmax=1)

    # Add labels for designs
    for i, (x, y) in enumerate(zip(interface, plddt)):
        design_name = metrics['Design'].iloc[i] if 'Design' in metrics.columns else f'{i+1:03d}'
        # Shorten name
        short_name = design_name.split('_')[-1] if '_' in str(design_name) else str(design_name)
        ax.annotate(short_name, (x, y), xytext=(5, 5), textcoords='offset points', fontsize=8)

    # Mark best design
    best_idx = np.argmax(composite)
    ax.annotate('Best', (interface[best_idx], plddt[best_idx]),
                xytext=(10, -10), textcoords='offset points',
                fontsize=10, fontweight='bold', color='darkgreen')

    # Add threshold lines
    ax.axhline(y=THRESHOLDS['pLDDT'], color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axvline(x=THRESHOLDS['Interface'], color='gray', linestyle='--', linewidth=1.5, alpha=0.7)

    # Shade good regions
    ax.fill_between([ax.get_xlim()[0], THRESHOLDS['Interface']], THRESHOLDS['pLDDT'], 100,
                    color='green', alpha=0.1, label='Good region')

    # Add text labels for regions
    ax.text(0.02, 0.98, 'Good Structure', transform=ax.transAxes, fontsize=9,
            ha='left', va='top', style='italic', color='gray')
    ax.text(0.98, 0.5, 'Good\nInterface', transform=ax.transAxes, fontsize=9,
            ha='right', va='center', style='italic', color='gray', rotation=90)

    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8, label='Quality Score')

    # Legend for sizes
    legend_elements = [
        plt.scatter([], [], s=100, c='gray', alpha=0.5, label='2Å (pAE)'),
        plt.scatter([], [], s=200, c='gray', alpha=0.5, label='5Å (pAE)'),
        plt.scatter([], [], s=300, c='gray', alpha=0.5, label='8Å (pAE)'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=8, title='pAE')

    ax.set_xlabel('Interface Score (REU)', fontsize=11)
    ax.set_ylabel('pLDDT Score', fontsize=11)

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png")

    return fig


def plot_normalized_heatmap(metrics: pd.DataFrame, output_path: str = None):
    """
    Plot 3: Normalized metrics heatmap.
    Shows pLDDT, pAE(inv), Interface(inv), pTM for each design.
    """
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)

    # Prepare data
    n_designs = len(metrics)
    design_labels = [str(i+1).zfill(3) for i in range(n_designs)]

    # Normalize metrics
    data = []
    row_labels = []

    if 'pLDDT' in metrics.columns:
        plddt_norm = metrics['pLDDT'].values / 100
        data.append(plddt_norm)
        row_labels.append('pLDDT')

    if 'pAE' in metrics.columns:
        pae = metrics['pAE'].values
        pae_inv = 1 - (pae - pae.min()) / (pae.max() - pae.min() + 1e-6)
        data.append(pae_inv)
        row_labels.append('pAE (inv)')

    if 'Interface' in metrics.columns:
        interface = metrics['Interface'].values
        interface_inv = 1 - (interface - interface.min()) / (interface.max() - interface.min() + 1e-6)
        data.append(interface_inv)
        row_labels.append('Interface (inv)')

    if 'pTM' in metrics.columns:
        data.append(metrics['pTM'].values)
        row_labels.append('pTM\n(higher is better)')

    data = np.array(data)

    # Create heatmap
    im = ax.imshow(data, cmap=RYG_CMAP, aspect='auto', vmin=0, vmax=1)

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
    Plot 4: Metrics statistics table (Mean, Std, Min, Max, Pass Rate).
    """
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.axis('off')

    # Calculate statistics
    stats_data = []
    metric_names = ['pLDDT', 'pAE', 'Interface', 'pTM']

    for metric in metric_names:
        if metric in metrics.columns:
            values = metrics[metric].values
            mean_val = np.mean(values)
            std_val = np.std(values)
            min_val = np.min(values)
            max_val = np.max(values)

            # Calculate pass rate
            threshold = THRESHOLDS.get(metric, 0)
            if metric in ['pLDDT', 'pTM']:
                pass_count = np.sum(values >= threshold)
            else:  # pAE and Interface (lower is better)
                pass_count = np.sum(values <= threshold)
            pass_rate = f"{100*pass_count/len(values):.0f}% ({pass_count}/{len(values)})"

            stats_data.append([metric, f'{mean_val:.1f}', f'{std_val:.1f}',
                              f'{min_val:.1f}', f'{max_val:.1f}', pass_rate])

    # Create table
    col_labels = ['Metric', 'Mean', 'Std', 'Min', 'Max', 'Pass Rate']
    table = ax.table(cellText=stats_data, colLabels=col_labels,
                     loc='center', cellLoc='center',
                     colWidths=[0.15, 0.12, 0.12, 0.12, 0.12, 0.18])

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
    Plot 5: Quality statistics boxplot with threshold lines.
    """
    fig, axes = plt.subplots(1, 4, figsize=(10, 4))

    metric_configs = [
        ('pLDDT', 'pLDDT', THRESHOLDS['pLDDT'], True),
        ('pAE', 'pAE', THRESHOLDS['pAE'], False),
        ('Interface', 'Interface', THRESHOLDS['Interface'], False),
        ('pTM', 'pTM', THRESHOLDS['pTM'], True),
    ]

    for ax, (metric, label, threshold, higher_better) in zip(axes, metric_configs):
        if metric in metrics.columns:
            data = metrics[metric].values

            # Create boxplot
            bp = ax.boxplot(data, patch_artist=True, widths=0.6)
            bp['boxes'][0].set_facecolor(CAT_PALETTE[0])
            bp['boxes'][0].set_alpha(0.7)

            # Add threshold line
            ax.axhline(y=threshold, color='green', linestyle='--', linewidth=2, alpha=0.8)

            # Style
            ax.set_xlabel(label, fontsize=11)
            ax.set_ylabel(label, fontsize=11)
            ax.set_xticklabels([label])
            prettify_ax(ax)
        else:
            ax.text(0.5, 0.5, f'No {metric} data', ha='center', va='center', transform=ax.transAxes)
            ax.axis('off')

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png")

    return fig


def plot_sasa_vs_binding_energy(metrics: pd.DataFrame, output_path: str = None):
    """
    Plot 6: SASA vs Binding Energy scatter plot colored by pLDDT.
    """
    fig, ax = simple_ax(figsize=FIGSIZE)

    # Get data
    sasa = metrics['SASA'].values if 'SASA' in metrics.columns else np.zeros(len(metrics))
    binding_energy = metrics['BindingEnergy'].values if 'BindingEnergy' in metrics.columns else metrics['Interface'].values
    plddt = metrics['pLDDT'].values if 'pLDDT' in metrics.columns else np.ones(len(metrics)) * 80

    # Create scatter plot
    scatter = ax.scatter(sasa, binding_energy, c=plddt, cmap='plasma',
                        s=100, alpha=0.8, edgecolors='white', linewidth=1)

    # Add design labels
    for i, (x, y) in enumerate(zip(sasa, binding_energy)):
        design_name = metrics['Design'].iloc[i] if 'Design' in metrics.columns else f'{i+1:03d}'
        short_name = design_name.split('_')[-1] if '_' in str(design_name) else str(design_name)[-3:]
        ax.annotate(short_name, (x, y), xytext=(5, 5), textcoords='offset points', fontsize=9)

    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('pLDDT', fontsize=10)

    ax.set_xlabel('Interface Buried SASA (μ)', fontsize=11)
    ax.set_ylabel('Binding Energy (REU)', fontsize=11)

    plt.tight_layout()

    if output_path:
        save_for_pub(fig, output_path)
        print(f"Saved: {output_path}.png")

    return fig


def plot_top5_designs_table(metrics: pd.DataFrame, output_path: str = None):
    """
    Plot 7: Top 5 designs table.
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis('off')

    # Calculate composite scores and rank
    composite = calculate_composite_score(metrics)
    n_designs = min(5, len(metrics))  # Top 5 or all if fewer
    ranked_indices = np.argsort(composite)[::-1][:n_designs]

    # Prepare table data
    table_data = []
    colors = []
    for rank, idx in enumerate(ranked_indices, 1):
        design = metrics['Design'].iloc[idx] if 'Design' in metrics.columns else f'design_{idx+1:03d}'
        interface = metrics['Interface'].iloc[idx] if 'Interface' in metrics.columns else 0
        plddt = metrics['pLDDT'].iloc[idx] if 'pLDDT' in metrics.columns else 0
        pae = metrics['pAE'].iloc[idx] if 'pAE' in metrics.columns else 0

        # Determine status based on metrics
        if plddt >= 85 and pae <= 3:
            status = 'Excellent'
            row_color = ['#90EE90'] * 6  # Light green
        elif plddt >= 75:
            status = 'Good'
            row_color = ['#98FB98'] * 6  # Pale green
        else:
            status = 'Acceptable'
            row_color = ['#FFE4B5'] * 6  # Moccasin

        table_data.append([rank, design, f'{interface:.1f}', f'{plddt:.1f}', f'{pae:.1f}', status])
        colors.append(row_color)

    # Create table
    col_labels = ['Rank', 'Design', 'Interface', 'pLDDT', 'pAE', 'Status']

    table = ax.table(cellText=table_data, colLabels=col_labels,
                     loc='center', cellLoc='center',
                     cellColours=colors,
                     colWidths=[0.08, 0.25, 0.13, 0.1, 0.08, 0.15])

    # Style table
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 2.0)

    # Style header (row 0 is the header when using colLabels)
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
    metric_cols = ['pLDDT', 'pAE', 'Interface', 'pTM']
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

    Args:
        metrics: DataFrame with extracted metrics
        output_path: Path to save figure (without extension)

    Returns:
        matplotlib.figure.Figure: The merged figure
    """
    # Create figure with 2 rows x 4 columns
    fig = plt.figure(figsize=(20, 10))

    # Panel titles
    panel_titles = [
        'A. Composite Score Distribution',
        'B. Quality Assessment',
        'C. Normalized Metrics Heatmap',
        'D. Metrics Statistics',
        'E. Quality Boxplot',
        'F. SASA vs Binding Energy',
        'G. Top 5 Designs',
        'H. Metrics Correlation',
    ]

    # --- Panel A: Composite Score Distribution ---
    ax1 = fig.add_subplot(2, 4, 1)
    scores = calculate_composite_score(metrics)
    mean_score = np.mean(scores)
    bins = np.linspace(0, 1, 11)
    counts, bin_edges, patches = ax1.hist(scores, bins=bins, color=CAT_PALETTE[0],
                                          alpha=0.8, edgecolor='white', linewidth=1)
    for count, patch in zip(counts, patches):
        if count > 0:
            x = patch.get_x() + patch.get_width() / 2
            y = patch.get_height()
            ax1.text(x, y + 0.1, f'{int(count)}', ha='center', va='bottom', fontsize=8)
    ax1.axvline(x=0.6, color='green', linestyle='--', linewidth=1.5, label='Good threshold')
    ax1.axvline(x=mean_score, color='red', linestyle='-', linewidth=1.5, label=f'Mean ({mean_score:.2f})')
    ax1.set_xlabel('Composite Quality Score', fontsize=9)
    ax1.set_ylabel('Number of Designs', fontsize=9)
    ax1.set_xlim(0, 1)
    ax1.legend(loc='upper left', fontsize=7)
    ax1.set_title(panel_titles[0], fontsize=10, fontweight='bold', loc='left')
    prettify_ax(ax1)

    # --- Panel B: Quality Assessment ---
    ax2 = fig.add_subplot(2, 4, 2)
    plddt = metrics['pLDDT'].values if 'pLDDT' in metrics.columns else np.zeros(len(metrics))
    interface = metrics['Interface'].values if 'Interface' in metrics.columns else np.zeros(len(metrics))
    composite = calculate_composite_score(metrics)
    pae = metrics['pAE'].values if 'pAE' in metrics.columns else np.ones(len(metrics)) * 5
    sizes = 50 + (10 - pae) * 30
    sizes = np.clip(sizes, 30, 250)
    scatter2 = ax2.scatter(interface, plddt, c=composite, s=sizes, cmap=RYG_CMAP,
                          alpha=0.8, edgecolors='white', linewidth=0.5, vmin=0, vmax=1)
    ax2.axhline(y=THRESHOLDS['pLDDT'], color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax2.axvline(x=THRESHOLDS['Interface'], color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax2.set_xlabel('Interface Score (REU)', fontsize=9)
    ax2.set_ylabel('pLDDT Score', fontsize=9)
    ax2.set_title(panel_titles[1], fontsize=10, fontweight='bold', loc='left')
    prettify_ax(ax2)

    # --- Panel C: Normalized Heatmap ---
    ax3 = fig.add_subplot(2, 4, 3)
    n_designs = len(metrics)
    design_labels = [str(i+1).zfill(3) for i in range(n_designs)]
    data = []
    row_labels = []
    if 'pLDDT' in metrics.columns:
        plddt_norm = metrics['pLDDT'].values / 100
        data.append(plddt_norm)
        row_labels.append('pLDDT')
    if 'pAE' in metrics.columns:
        pae = metrics['pAE'].values
        pae_inv = 1 - (pae - pae.min()) / (pae.max() - pae.min() + 1e-6)
        data.append(pae_inv)
        row_labels.append('pAE (inv)')
    if 'Interface' in metrics.columns:
        interface = metrics['Interface'].values
        interface_inv = 1 - (interface - interface.min()) / (interface.max() - interface.min() + 1e-6)
        data.append(interface_inv)
        row_labels.append('Interface (inv)')
    if 'pTM' in metrics.columns:
        data.append(metrics['pTM'].values)
        row_labels.append('pTM')
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
    metric_names = ['pLDDT', 'pAE', 'Interface', 'pTM']
    for metric in metric_names:
        if metric in metrics.columns:
            values = metrics[metric].values
            mean_val = np.mean(values)
            std_val = np.std(values)
            min_val = np.min(values)
            max_val = np.max(values)
            threshold = THRESHOLDS.get(metric, 0)
            if metric in ['pLDDT', 'pTM']:
                pass_count = np.sum(values >= threshold)
            else:
                pass_count = np.sum(values <= threshold)
            pass_rate = f"{100*pass_count/len(values):.0f}%"
            stats_data.append([metric, f'{mean_val:.1f}', f'{std_val:.1f}',
                              f'{min_val:.1f}', f'{max_val:.1f}', pass_rate])
    col_labels = ['Metric', 'Mean', 'Std', 'Min', 'Max', 'Pass']
    table4 = ax4.table(cellText=stats_data, colLabels=col_labels,
                       loc='center', cellLoc='center',
                       colWidths=[0.18, 0.14, 0.14, 0.14, 0.14, 0.14])
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
    for metric in ['pLDDT', 'pAE', 'Interface', 'pTM']:
        if metric in metrics.columns:
            metric_data.append(metrics[metric].values)
            metric_labels.append(metric)
    if metric_data:
        bp = ax5.boxplot(metric_data, patch_artist=True)
        colors = [CAT_PALETTE[i % len(CAT_PALETTE)] for i in range(len(metric_data))]
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax5.set_xticklabels(metric_labels, fontsize=8)
        ax5.set_ylabel('Value', fontsize=9)
    ax5.set_title(panel_titles[4], fontsize=10, fontweight='bold', loc='left')
    prettify_ax(ax5)

    # --- Panel F: SASA vs Binding Energy ---
    ax6 = fig.add_subplot(2, 4, 6)
    sasa = metrics['SASA'].values if 'SASA' in metrics.columns else np.zeros(len(metrics))
    binding = metrics['Interface'].values if 'Interface' in metrics.columns else np.zeros(len(metrics))
    plddt = metrics['pLDDT'].values if 'pLDDT' in metrics.columns else np.ones(len(metrics)) * 80
    scatter6 = ax6.scatter(sasa, binding, c=plddt, cmap='plasma',
                          s=60, alpha=0.8, edgecolors='white', linewidth=0.5)
    ax6.set_xlabel('Interface SASA', fontsize=9)
    ax6.set_ylabel('Binding Energy (REU)', fontsize=9)
    ax6.set_title(panel_titles[5], fontsize=10, fontweight='bold', loc='left')
    prettify_ax(ax6)

    # --- Panel G: Top 5 Designs Table ---
    ax7 = fig.add_subplot(2, 4, 7)
    ax7.axis('off')
    composite = calculate_composite_score(metrics)
    n_top = min(5, len(metrics))
    ranked_indices = np.argsort(composite)[::-1][:n_top]
    table_data = []
    colors = []
    for rank, idx in enumerate(ranked_indices, 1):
        design = metrics['Design'].iloc[idx] if 'Design' in metrics.columns else f'design_{idx+1:03d}'
        short_name = str(design).split('_')[-1] if '_' in str(design) else str(design)[-10:]
        interface = metrics['Interface'].iloc[idx] if 'Interface' in metrics.columns else 0
        plddt = metrics['pLDDT'].iloc[idx] if 'pLDDT' in metrics.columns else 0
        pae = metrics['pAE'].iloc[idx] if 'pAE' in metrics.columns else 0
        if plddt >= 85 and pae <= 3:
            status = 'Excellent'
            row_color = ['#90EE90'] * 5
        elif plddt >= 75:
            status = 'Good'
            row_color = ['#98FB98'] * 5
        else:
            status = 'Acceptable'
            row_color = ['#FFE4B5'] * 5
        table_data.append([rank, short_name, f'{interface:.1f}', f'{plddt:.1f}', status])
        colors.append(row_color)
    col_labels = ['#', 'Design', 'dG', 'pLDDT', 'Status']
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
    metric_cols = ['pLDDT', 'pAE', 'Interface', 'pTM']
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

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path + ".png", dpi=150, bbox_inches='tight')
        fig.savefig(output_path + ".pdf", dpi=300, bbox_inches='tight')
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

    if output_prefix is None:
        output_prefix = str(results_dir / "binder_design")

    # Set publication-quality plot context
    set_pub_plot_context(context="talk")

    # Load data
    df = load_design_data(results_dir)
    metrics = extract_metrics(df)

    if len(metrics) == 0:
        print("Error: No design data found")
        return None

    saved_files = []

    # Figure 1: Composite Score Distribution
    fig1 = plot_composite_score_distribution(metrics, f"{output_prefix}_composite_score")
    saved_files.append(f"{output_prefix}_composite_score.png")
    plt.close(fig1)

    # Figure 2: Quality Assessment
    fig2 = plot_quality_assessment(metrics, f"{output_prefix}_quality_assessment")
    saved_files.append(f"{output_prefix}_quality_assessment.png")
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

    # Figure 6: SASA vs Binding Energy
    fig6 = plot_sasa_vs_binding_energy(metrics, f"{output_prefix}_sasa_binding_energy")
    saved_files.append(f"{output_prefix}_sasa_binding_energy.png")
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


def display_results(results_dir: str, show_all: bool = True, block: bool = True) -> Dict:
    """
    Display binder design results interactively.

    Args:
        results_dir: Path to results directory containing generated figures
        show_all: If True, display all 8 figures. If False, only display summary.
        block: If True (default), block until figure window is closed.

    Returns:
        dict: Dictionary with figure objects
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
        ("composite_score", "Composite Score Distribution"),
        ("quality_assessment", "Quality Assessment"),
        ("normalized_heatmap", "Normalized Metrics Heatmap"),
        ("statistics_table", "Metrics Statistics"),
        ("quality_boxplot", "Quality Boxplot"),
        ("sasa_binding_energy", "SASA vs Binding Energy"),
        ("top5_designs", "Top 5 Designs"),
        ("correlation", "Metrics Correlation"),
    ]

    if not show_all:
        figure_files = figure_files[:4]  # Only first 4 figures

    if in_notebook:
        # Display in notebook using IPython
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
        # Display in GUI window
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
        n_cols = 4
        n_rows = (n_figs + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 5 * n_rows))
        axes = axes.flatten() if n_figs > 1 else [axes]

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

        # Hide unused axes
        for i in range(len(figure_files), len(axes)):
            axes[i].axis('off')

        plt.tight_layout()
        figures['combined_figure'] = fig

        plt.show(block=block)

    return figures


def main():
    parser = argparse.ArgumentParser(description='Generate binder design visualization')
    parser.add_argument('results_dir', type=str, help='Path to results directory')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output prefix (default: results_dir/binder_design)')
    parser.add_argument('--display', '-d', action='store_true',
                        help='Display results after generation')

    args = parser.parse_args()

    output_files = create_all_figures(args.results_dir, args.output)

    if output_files:
        print(f"\nVisualization complete!")
        if args.display:
            display_results(args.results_dir)
    else:
        print("\nVisualization failed")
        exit(1)


if __name__ == '__main__':
    main()
