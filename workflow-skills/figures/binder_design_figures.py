#!/usr/bin/env python3
"""
Binder Design Workflow - Figure Generation Script

This script generates publication-ready figures for the Binder Design workflow:
1. Main Figure: Multi-panel visualization of binder design quality metrics
2. Supplementary Figure: Detailed per-design analysis and interface metrics
3. Workflow Overview: Schematic diagram of the BindCraft pipeline

Usage:
    python binder_design_figures.py --results_dir /path/to/results

The script expects the following files in the results directory:
    - metrics.csv: Design quality metrics (columns: design_name, plddt, pae, interface_score, ptm)
    - designs/: Directory containing designed PDB structures

Output files:
    - binder_design_main.pdf/png: Main multi-panel figure
    - binder_design_supplementary.pdf/png: Detailed analysis figure
    - binder_workflow_overview.pdf/png: Workflow schematic
"""

import argparse
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import numpy as np

# Color palette - consistent with other workflow figures
COLORS = {
    'primary': '#2ecc71',      # Green - success/quality
    'secondary': '#3498db',    # Blue - input/structure
    'warning': '#e74c3c',      # Red - low quality/errors
    'accent': '#9b59b6',       # Purple - processing
    'highlight': '#f39c12',    # Orange - tools/MCP
    'teal': '#1abc9c',         # Teal - highlights
    'dark': '#2c3e50',         # Dark gray - text
    'light': '#7f8c8d',        # Light gray - secondary text
    'background': '#f8f9fa',   # Very light gray - background
    'white': '#ffffff',        # White
}

# Quality thresholds for binder designs
QUALITY_THRESHOLDS = {
    'plddt_good': 80,          # pLDDT > 80 is good
    'plddt_acceptable': 70,    # pLDDT > 70 is acceptable
    'pae_good': 5,             # pAE < 5 is good
    'pae_acceptable': 10,      # pAE < 10 is acceptable
    'interface_good': -10,     # Interface score < -10 is good (more negative = better)
}


def prettify_ax(ax):
    """Apply consistent styling to axes."""
    for i, spine in enumerate(ax.spines.values()):
        if i in [1, 3]:  # Right and top spines
            spine.set_visible(False)
    ax.tick_params(direction='out', length=3, color='k')
    ax.set_axisbelow(True)


def draw_rounded_box(ax, x, y, width, height, color, text,
                     fontsize=10, text_color='white', alpha=0.9,
                     boxstyle='round,pad=0.02,rounding_size=0.1'):
    """Draw a rounded rectangle with centered text."""
    box = FancyBboxPatch(
        (x - width/2, y - height/2), width, height,
        boxstyle=boxstyle,
        facecolor=color,
        edgecolor='none',
        alpha=alpha,
        transform=ax.transData,
        zorder=2
    )
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            color=text_color, fontweight='bold', zorder=3,
            wrap=True)
    return box


def draw_arrow(ax, start, end, color=None, style='simple',
               connectionstyle='arc3,rad=0', linewidth=2):
    """Draw an arrow between two points."""
    if color is None:
        color = COLORS['dark']
    arrow = FancyArrowPatch(
        start, end,
        arrowstyle=f'->,head_length=0.4,head_width=0.2',
        connectionstyle=connectionstyle,
        color=color,
        linewidth=linewidth,
        zorder=1
    )
    ax.add_patch(arrow)
    return arrow


def generate_mock_data(n_designs=10):
    """Generate mock data for demonstration when no real data available."""
    np.random.seed(42)

    data = {
        'design_name': [f'design_{i:03d}' for i in range(1, n_designs + 1)],
        'plddt': np.random.normal(75, 10, n_designs).clip(50, 95),
        'pae': np.random.exponential(6, n_designs).clip(2, 20),
        'interface_score': np.random.normal(-8, 4, n_designs).clip(-20, 0),
        'ptm': np.random.normal(0.7, 0.1, n_designs).clip(0.4, 0.95),
        'binding_energy': np.random.normal(-15, 5, n_designs).clip(-30, 0),
        'interface_buried_sasa': np.random.normal(1500, 300, n_designs).clip(800, 2500),
    }
    return data


def load_metrics(results_dir):
    """Load metrics from results directory or generate mock data."""
    metrics_file = Path(results_dir) / 'metrics.csv'

    if metrics_file.exists():
        try:
            import pandas as pd
            df = pd.read_csv(metrics_file)
            data = df.to_dict('list')
            print(f"Loaded {len(df)} designs from {metrics_file}")
            return data
        except Exception as e:
            print(f"Warning: Could not load metrics.csv: {e}")
            print("Using mock data for demonstration")
    else:
        print(f"Note: {metrics_file} not found. Using mock data for demonstration")

    return generate_mock_data()


def create_main_figure(data, output_dir):
    """
    Create the main multi-panel figure for binder design quality.

    Panel A: pLDDT distribution across designs
    Panel B: pAE comparison
    Panel C: Interface score ranking
    Panel D: PTM/quality summary
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Binder Design Quality Assessment', fontsize=14, fontweight='bold', y=0.98)

    n_designs = len(data['design_name'])
    x_pos = np.arange(n_designs)

    # Panel A: pLDDT Distribution
    ax = axes[0, 0]
    prettify_ax(ax)

    plddt_colors = [COLORS['primary'] if v >= QUALITY_THRESHOLDS['plddt_good']
                   else COLORS['highlight'] if v >= QUALITY_THRESHOLDS['plddt_acceptable']
                   else COLORS['warning'] for v in data['plddt']]

    bars = ax.bar(x_pos, data['plddt'], color=plddt_colors, alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.axhline(y=QUALITY_THRESHOLDS['plddt_good'], color=COLORS['primary'], linestyle='--',
               alpha=0.7, label=f'Good (>{QUALITY_THRESHOLDS["plddt_good"]})')
    ax.axhline(y=QUALITY_THRESHOLDS['plddt_acceptable'], color=COLORS['highlight'], linestyle='--',
               alpha=0.7, label=f'Acceptable (>{QUALITY_THRESHOLDS["plddt_acceptable"]})')

    ax.set_xlabel('Design', fontsize=11)
    ax.set_ylabel('pLDDT Score', fontsize=11)
    ax.set_title('A. Predicted Local Distance Difference Test', fontsize=12, fontweight='bold', loc='left')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([d.replace('design_', '') for d in data['design_name']], rotation=45, ha='right')
    ax.set_ylim(0, 100)
    ax.legend(loc='lower right', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    # Panel B: pAE Comparison
    ax = axes[0, 1]
    prettify_ax(ax)

    pae_colors = [COLORS['primary'] if v <= QUALITY_THRESHOLDS['pae_good']
                  else COLORS['highlight'] if v <= QUALITY_THRESHOLDS['pae_acceptable']
                  else COLORS['warning'] for v in data['pae']]

    bars = ax.bar(x_pos, data['pae'], color=pae_colors, alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.axhline(y=QUALITY_THRESHOLDS['pae_good'], color=COLORS['primary'], linestyle='--',
               alpha=0.7, label=f'Good (<{QUALITY_THRESHOLDS["pae_good"]})')
    ax.axhline(y=QUALITY_THRESHOLDS['pae_acceptable'], color=COLORS['highlight'], linestyle='--',
               alpha=0.7, label=f'Acceptable (<{QUALITY_THRESHOLDS["pae_acceptable"]})')

    ax.set_xlabel('Design', fontsize=11)
    ax.set_ylabel('pAE Score (lower is better)', fontsize=11)
    ax.set_title('B. Predicted Aligned Error', fontsize=12, fontweight='bold', loc='left')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([d.replace('design_', '') for d in data['design_name']], rotation=45, ha='right')
    ax.legend(loc='upper right', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    # Panel C: Interface Score Ranking
    ax = axes[1, 0]
    prettify_ax(ax)

    # Sort by interface score (more negative is better)
    sorted_indices = np.argsort(data['interface_score'])
    sorted_names = [data['design_name'][i] for i in sorted_indices]
    sorted_scores = [data['interface_score'][i] for i in sorted_indices]

    interface_colors = [COLORS['primary'] if v <= QUALITY_THRESHOLDS['interface_good']
                       else COLORS['highlight'] for v in sorted_scores]

    bars = ax.barh(np.arange(n_designs), sorted_scores, color=interface_colors, alpha=0.85,
                   edgecolor='white', linewidth=0.5)
    ax.axvline(x=QUALITY_THRESHOLDS['interface_good'], color=COLORS['primary'], linestyle='--',
               alpha=0.7, label=f'Good (<{QUALITY_THRESHOLDS["interface_good"]})')

    ax.set_xlabel('Interface Score (REU, lower is better)', fontsize=11)
    ax.set_ylabel('Design (ranked)', fontsize=11)
    ax.set_title('C. Interface Score Ranking', fontsize=12, fontweight='bold', loc='left')
    ax.set_yticks(np.arange(n_designs))
    ax.set_yticklabels([n.replace('design_', '') for n in sorted_names])
    ax.legend(loc='lower right', fontsize=9)
    ax.xaxis.grid(True, linestyle='--', alpha=0.5)

    # Add rank labels
    for i, (bar, score) in enumerate(zip(bars, sorted_scores)):
        ax.text(bar.get_width() - 0.5, bar.get_y() + bar.get_height()/2,
                f'#{i+1}', ha='right', va='center', fontsize=8, color='white', fontweight='bold')

    # Panel D: PTM Summary
    ax = axes[1, 1]
    prettify_ax(ax)

    ptm_colors = [COLORS['primary'] if v >= 0.8
                  else COLORS['highlight'] if v >= 0.6
                  else COLORS['warning'] for v in data['ptm']]

    bars = ax.bar(x_pos, data['ptm'], color=ptm_colors, alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.axhline(y=0.8, color=COLORS['primary'], linestyle='--', alpha=0.7, label='Good (>0.8)')
    ax.axhline(y=0.6, color=COLORS['highlight'], linestyle='--', alpha=0.7, label='Acceptable (>0.6)')

    ax.set_xlabel('Design', fontsize=11)
    ax.set_ylabel('pTM Score', fontsize=11)
    ax.set_title('D. Predicted Template Modeling Score', fontsize=12, fontweight='bold', loc='left')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([d.replace('design_', '') for d in data['design_name']], rotation=45, ha='right')
    ax.set_ylim(0, 1)
    ax.legend(loc='lower right', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Save figures
    output_path = Path(output_dir)
    fig.savefig(output_path / 'binder_design_main.pdf', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'binder_design_main.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"Saved: {output_path / 'binder_design_main.pdf'}")
    print(f"Saved: {output_path / 'binder_design_main.png'}")


def create_supplementary_figure(data, output_dir):
    """
    Create supplementary figure with detailed per-design analysis.

    Panel A: Quality metrics heatmap
    Panel B: Interface analysis (buried SASA vs binding energy)
    Panel C: Quality score distribution
    Panel D: Design selection summary
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Binder Design - Supplementary Analysis', fontsize=14, fontweight='bold', y=0.98)

    n_designs = len(data['design_name'])

    # Panel A: Quality Metrics Heatmap
    ax = axes[0, 0]

    # Normalize metrics for heatmap (0-1 scale, higher is better)
    metrics_normalized = np.array([
        np.array(data['plddt']) / 100,  # pLDDT: higher is better
        1 - np.array(data['pae']) / 20,  # pAE: lower is better, invert
        1 - (np.array(data['interface_score']) + 20) / 20,  # Interface: more negative is better
        np.array(data['ptm']),  # PTM: higher is better
    ])

    im = ax.imshow(metrics_normalized, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
    ax.set_xticks(np.arange(n_designs))
    ax.set_xticklabels([d.replace('design_', '') for d in data['design_name']], rotation=45, ha='right')
    ax.set_yticks(np.arange(4))
    ax.set_yticklabels(['pLDDT', 'pAE (inv)', 'Interface (inv)', 'pTM'])
    ax.set_title('A. Normalized Quality Metrics', fontsize=12, fontweight='bold', loc='left')

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Normalized Score (higher is better)', fontsize=9)

    # Add text annotations
    for i in range(4):
        for j in range(n_designs):
            val = metrics_normalized[i, j]
            color = 'white' if val < 0.5 else 'black'
            ax.text(j, i, f'{val:.2f}', ha='center', va='center', fontsize=8, color=color)

    # Panel B: Interface Analysis
    ax = axes[0, 1]
    prettify_ax(ax)

    if 'interface_buried_sasa' in data and 'binding_energy' in data:
        scatter = ax.scatter(data['interface_buried_sasa'], data['binding_energy'],
                            c=data['plddt'], cmap='viridis', s=100, alpha=0.8, edgecolor='white')
        ax.set_xlabel('Interface Buried SASA ($\\AA^2$)', fontsize=11)
        ax.set_ylabel('Binding Energy (REU)', fontsize=11)
        cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
        cbar.set_label('pLDDT', fontsize=9)

        # Add design labels
        for i, name in enumerate(data['design_name']):
            ax.annotate(name.replace('design_', ''),
                       (data['interface_buried_sasa'][i], data['binding_energy'][i]),
                       xytext=(5, 5), textcoords='offset points', fontsize=7, alpha=0.7)
    else:
        # Fallback: pLDDT vs pAE scatter
        scatter = ax.scatter(data['plddt'], data['pae'],
                            c=data['interface_score'], cmap='viridis_r', s=100, alpha=0.8, edgecolor='white')
        ax.set_xlabel('pLDDT Score', fontsize=11)
        ax.set_ylabel('pAE Score', fontsize=11)
        cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
        cbar.set_label('Interface Score', fontsize=9)

    ax.set_title('B. Interface Analysis', fontsize=12, fontweight='bold', loc='left')
    ax.grid(True, linestyle='--', alpha=0.3)

    # Panel C: Quality Score Distribution
    ax = axes[1, 0]
    prettify_ax(ax)

    # Calculate composite quality score
    quality_scores = (
        np.array(data['plddt']) / 100 * 0.3 +
        (1 - np.array(data['pae']) / 20) * 0.3 +
        (1 - (np.array(data['interface_score']) + 20) / 20) * 0.2 +
        np.array(data['ptm']) * 0.2
    )

    bins = np.linspace(0, 1, 11)
    ax.hist(quality_scores, bins=bins, color=COLORS['secondary'], alpha=0.7, edgecolor='white')
    ax.axvline(x=0.7, color=COLORS['primary'], linestyle='--', linewidth=2, label='Good threshold')
    ax.axvline(x=np.mean(quality_scores), color=COLORS['warning'], linestyle='-', linewidth=2,
               label=f'Mean ({np.mean(quality_scores):.2f})')

    ax.set_xlabel('Composite Quality Score', fontsize=11)
    ax.set_ylabel('Number of Designs', fontsize=11)
    ax.set_title('C. Quality Score Distribution', fontsize=12, fontweight='bold', loc='left')
    ax.legend(loc='upper left', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    # Panel D: Design Selection Summary
    ax = axes[1, 1]
    ax.axis('off')

    # Calculate statistics
    n_good_plddt = sum(1 for v in data['plddt'] if v >= QUALITY_THRESHOLDS['plddt_good'])
    n_good_pae = sum(1 for v in data['pae'] if v <= QUALITY_THRESHOLDS['pae_good'])
    n_good_interface = sum(1 for v in data['interface_score'] if v <= QUALITY_THRESHOLDS['interface_good'])
    n_high_quality = sum(1 for i in range(n_designs)
                         if data['plddt'][i] >= QUALITY_THRESHOLDS['plddt_good']
                         and data['pae'][i] <= QUALITY_THRESHOLDS['pae_good'])

    # Find best design
    best_idx = np.argmax(quality_scores)
    best_design = data['design_name'][best_idx]

    summary_text = f"""
    DESIGN SUMMARY
    {'='*40}

    Total Designs: {n_designs}

    Quality Breakdown:
    - Good pLDDT (>{QUALITY_THRESHOLDS['plddt_good']}): {n_good_plddt}/{n_designs} ({100*n_good_plddt/n_designs:.0f}%)
    - Good pAE (<{QUALITY_THRESHOLDS['pae_good']}): {n_good_pae}/{n_designs} ({100*n_good_pae/n_designs:.0f}%)
    - Good Interface (<{QUALITY_THRESHOLDS['interface_good']}): {n_good_interface}/{n_designs} ({100*n_good_interface/n_designs:.0f}%)

    High-Quality Designs: {n_high_quality}/{n_designs}
    (pLDDT >{QUALITY_THRESHOLDS['plddt_good']} AND pAE <{QUALITY_THRESHOLDS['pae_good']})

    Best Design: {best_design}
    - pLDDT: {data['plddt'][best_idx]:.1f}
    - pAE: {data['pae'][best_idx]:.1f}
    - Interface: {data['interface_score'][best_idx]:.1f}
    - pTM: {data['ptm'][best_idx]:.2f}
    - Composite Score: {quality_scores[best_idx]:.3f}

    {'='*40}
    Recommendation: {'Proceed to validation' if n_high_quality > 0 else 'Consider re-running design'}
    """

    ax.text(0.05, 0.95, summary_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor=COLORS['background'], alpha=0.8, edgecolor=COLORS['light']))
    ax.set_title('D. Selection Summary', fontsize=12, fontweight='bold', loc='left')

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Save figures
    output_path = Path(output_dir)
    fig.savefig(output_path / 'binder_design_supplementary.pdf', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'binder_design_supplementary.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"Saved: {output_path / 'binder_design_supplementary.pdf'}")
    print(f"Saved: {output_path / 'binder_design_supplementary.png'}")


def create_workflow_overview(output_dir):
    """
    Create a schematic diagram of the Binder Design workflow.

    Shows the BindCraft pipeline: Input -> Design -> Validation -> Output
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')
    ax.set_aspect('equal')

    # Title
    ax.text(7, 7.5, 'Binder Design Workflow', ha='center', va='center',
            fontsize=16, fontweight='bold', color=COLORS['dark'])
    ax.text(7, 7.1, 'BindCraft-based de novo binder generation', ha='center', va='center',
            fontsize=11, color=COLORS['light'], style='italic')

    # === Row 1: Input Stage ===
    y1 = 5.5

    # Target PDB
    draw_rounded_box(ax, 1.5, y1, 2.2, 1.2, COLORS['secondary'], 'Target\nPDB', fontsize=10)

    # Arrow
    draw_arrow(ax, (2.7, y1), (3.5, y1), color=COLORS['dark'])

    # Config Generation
    draw_rounded_box(ax, 4.8, y1, 2.4, 1.2, COLORS['accent'], 'Config\nGeneration', fontsize=10)

    # Arrow
    draw_arrow(ax, (6.1, y1), (7.0, y1), color=COLORS['dark'])

    # Design Parameters box
    params_box = FancyBboxPatch((7.2, y1-0.6), 2.6, 1.2,
                                 boxstyle='round,pad=0.02,rounding_size=0.1',
                                 facecolor=COLORS['background'], edgecolor=COLORS['light'],
                                 alpha=0.9, linewidth=1.5)
    ax.add_patch(params_box)
    ax.text(8.5, y1+0.3, 'Parameters', ha='center', va='center', fontsize=9, fontweight='bold', color=COLORS['dark'])
    ax.text(8.5, y1-0.1, '- Binder length', ha='center', va='center', fontsize=8, color=COLORS['light'])
    ax.text(8.5, y1-0.35, '- Target chains', ha='center', va='center', fontsize=8, color=COLORS['light'])

    # === Row 2: Design Stage (Main) ===
    y2 = 3.5

    # BindCraft MCP (main box)
    mcp_box = FancyBboxPatch((2.5, y2-0.9), 9, 1.8,
                              boxstyle='round,pad=0.02,rounding_size=0.15',
                              facecolor=COLORS['highlight'], edgecolor='none',
                              alpha=0.15)
    ax.add_patch(mcp_box)
    ax.text(7, y2+0.65, 'BindCraft MCP', ha='center', va='center', fontsize=11,
            fontweight='bold', color=COLORS['highlight'])

    # Sub-components
    draw_rounded_box(ax, 3.8, y2-0.15, 2.0, 0.9, COLORS['primary'], 'RFdiffusion', fontsize=9)
    draw_rounded_box(ax, 6.3, y2-0.15, 2.0, 0.9, COLORS['teal'], 'ProteinMPNN', fontsize=9)
    draw_rounded_box(ax, 8.8, y2-0.15, 2.0, 0.9, COLORS['secondary'], 'AlphaFold2', fontsize=9)

    # Arrows between sub-components
    draw_arrow(ax, (4.9, y2-0.15), (5.2, y2-0.15), color=COLORS['dark'], linewidth=1.5)
    draw_arrow(ax, (7.4, y2-0.15), (7.7, y2-0.15), color=COLORS['dark'], linewidth=1.5)

    # Labels under sub-components
    ax.text(3.8, y2-0.75, 'Structure\nGeneration', ha='center', va='center', fontsize=7, color=COLORS['light'])
    ax.text(6.3, y2-0.75, 'Sequence\nDesign', ha='center', va='center', fontsize=7, color=COLORS['light'])
    ax.text(8.8, y2-0.75, 'Structure\nValidation', ha='center', va='center', fontsize=7, color=COLORS['light'])

    # Arrows from Row 1 to Row 2
    draw_arrow(ax, (4.8, y1-0.7), (4.8, y2+0.7), color=COLORS['dark'], linewidth=1.5)
    draw_arrow(ax, (8.5, y1-0.7), (8.5, y2+0.7), color=COLORS['dark'], linewidth=1.5)

    # === Row 3: Output Stage ===
    y3 = 1.5

    # Arrow from design stage
    draw_arrow(ax, (7, y2-0.9), (7, y3+0.7), color=COLORS['dark'], linewidth=2)

    # Output boxes
    draw_rounded_box(ax, 3.5, y3, 2.2, 1.0, COLORS['secondary'], 'PDB\nStructures', fontsize=9)
    draw_rounded_box(ax, 6.2, y3, 2.2, 1.0, COLORS['primary'], 'Quality\nMetrics', fontsize=9)
    draw_rounded_box(ax, 8.9, y3, 2.2, 1.0, COLORS['accent'], 'Analysis\nFigures', fontsize=9)

    # Arrows to outputs
    draw_arrow(ax, (5.8, y3+0.3), (4.7, y3+0.3), color=COLORS['dark'], linewidth=1.5)
    draw_arrow(ax, (7.5, y3+0.3), (8.5, y3+0.3), color=COLORS['dark'], linewidth=1.5)

    # === Legend ===
    legend_y = 0.4
    legend_items = [
        (COLORS['secondary'], 'Input/Structure'),
        (COLORS['accent'], 'Processing'),
        (COLORS['highlight'], 'MCP Tools'),
        (COLORS['primary'], 'Output/Quality'),
    ]

    ax.text(1, legend_y+0.3, 'Legend:', fontsize=9, fontweight='bold', color=COLORS['dark'])
    for i, (color, label) in enumerate(legend_items):
        x = 2.5 + i * 2.8
        rect = Rectangle((x-0.2, legend_y-0.15), 0.4, 0.3, facecolor=color, alpha=0.9)
        ax.add_patch(rect)
        ax.text(x+0.35, legend_y, label, fontsize=8, va='center', color=COLORS['dark'])

    # === Process Flow Labels ===
    ax.text(1.5, y1+0.9, '1. Input', fontsize=9, fontweight='bold', color=COLORS['dark'], ha='center')
    ax.text(1.5, y2+0.65, '2. Design', fontsize=9, fontweight='bold', color=COLORS['dark'], ha='center')
    ax.text(1.5, y3+0.3, '3. Output', fontsize=9, fontweight='bold', color=COLORS['dark'], ha='center')

    plt.tight_layout()

    # Save figures
    output_path = Path(output_dir)
    fig.savefig(output_path / 'binder_workflow_overview.pdf', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'binder_workflow_overview.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"Saved: {output_path / 'binder_workflow_overview.pdf'}")
    print(f"Saved: {output_path / 'binder_workflow_overview.png'}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate publication-ready figures for Binder Design workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--results_dir', type=str, default='.',
                        help='Directory containing metrics.csv and design results')
    parser.add_argument('--output_dir', type=str, default=None,
                        help='Output directory for figures (default: same as results_dir)')
    parser.add_argument('--main-only', action='store_true',
                        help='Generate only the main figure')
    parser.add_argument('--supplementary-only', action='store_true',
                        help='Generate only the supplementary figure')
    parser.add_argument('--workflow-only', action='store_true',
                        help='Generate only the workflow overview')

    args = parser.parse_args()

    results_dir = Path(args.results_dir).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else results_dir

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nBinder Design Figure Generation")
    print(f"{'='*50}")
    print(f"Results directory: {results_dir}")
    print(f"Output directory: {output_dir}")
    print()

    # Load data
    data = load_metrics(results_dir)

    # Generate figures based on flags
    if args.main_only:
        create_main_figure(data, output_dir)
    elif args.supplementary_only:
        create_supplementary_figure(data, output_dir)
    elif args.workflow_only:
        create_workflow_overview(output_dir)
    else:
        # Generate all figures
        print("\nGenerating main figure...")
        create_main_figure(data, output_dir)

        print("\nGenerating supplementary figure...")
        create_supplementary_figure(data, output_dir)

        print("\nGenerating workflow overview...")
        create_workflow_overview(output_dir)

    print(f"\n{'='*50}")
    print("Figure generation complete!")
    print(f"Output files saved to: {output_dir}")


if __name__ == '__main__':
    main()
