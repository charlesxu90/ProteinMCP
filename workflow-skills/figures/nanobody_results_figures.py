#!/usr/bin/env python3
"""
Generate figures for Nanobody Design Results.

This script creates publication-ready figures from nanobody design results:
1. Main figure: Quality metrics overview (4-panel)
2. Supplementary figure: Detailed analysis with rankings and sequence composition
3. Comparison figure: Top designs comparison

Usage:
    python nanobody_results_figures.py --results_dir /path/to/results/nanobody_design
"""

import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd
from pathlib import Path

# Color palette
COLORS = {
    'primary': '#1abc9c',      # Teal - nanobody/success
    'secondary': '#3498db',    # Blue - structure
    'warning': '#e74c3c',      # Red - low quality
    'accent': '#9b59b6',       # Purple - processing
    'highlight': '#f39c12',    # Orange - highlights
    'green': '#27ae60',        # Green - good
    'dark': '#2c3e50',         # Dark gray - text
    'light': '#7f8c8d',        # Light gray
    'background': '#f8f9fa',   # Very light gray
}

# Quality thresholds for nanobody designs
THRESHOLDS = {
    'design_ptm_good': 0.80,
    'design_ptm_acceptable': 0.75,
    'iptm_good': 0.20,
    'iptm_acceptable': 0.15,
    'pae_good': 18,
    'pae_acceptable': 20,
    'rmsd_good': 5,
    'rmsd_acceptable': 10,
}


def prettify_ax(ax):
    """Apply consistent styling to axes."""
    for i, spine in enumerate(ax.spines.values()):
        if i in [1, 3]:  # Right and top
            spine.set_visible(False)
    ax.tick_params(direction='out', length=3, color='k')
    ax.set_axisbelow(True)


def load_metrics(results_dir):
    """Load metrics from the results directory."""
    results_path = Path(results_dir)

    # Try different possible metric file locations
    possible_paths = [
        results_path / 'designs' / 'final_ranked_designs' / 'all_designs_metrics.csv',
        results_path / 'all_designs_metrics.csv',
        results_path / 'metrics.csv',
    ]

    for metrics_file in possible_paths:
        if metrics_file.exists():
            df = pd.read_csv(metrics_file)
            print(f"Loaded {len(df)} designs from {metrics_file}")
            return df

    raise FileNotFoundError(f"No metrics file found in {results_dir}")


def create_main_figure(df, output_dir):
    """
    Create main figure: Quality metrics overview (4-panel).

    Panel A: Design pTM scores
    Panel B: Design-to-Target iPTM
    Panel C: Min PAE to target
    Panel D: Filter RMSD
    """
    n_designs = len(df)
    x_pos = np.arange(n_designs)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Nanobody Design Quality Assessment', fontsize=16, fontweight='bold', y=0.98)

    # Sort by final rank if available
    if 'final_rank' in df.columns:
        df = df.sort_values('final_rank').reset_index(drop=True)
        x_labels = [f"#{int(r)}" for r in df['final_rank']]
    else:
        x_labels = [f"{i+1}" for i in range(n_designs)]

    # Panel A: Design pTM (structural confidence)
    ax = axes[0, 0]
    prettify_ax(ax)

    ptm_values = df['design_ptm'].values
    ptm_colors = [COLORS['primary'] if v >= THRESHOLDS['design_ptm_good']
                  else COLORS['highlight'] if v >= THRESHOLDS['design_ptm_acceptable']
                  else COLORS['warning'] for v in ptm_values]

    bars = ax.bar(x_pos, ptm_values, color=ptm_colors, alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.axhline(y=THRESHOLDS['design_ptm_good'], color=COLORS['primary'], linestyle='--',
               alpha=0.7, label=f'Good (>{THRESHOLDS["design_ptm_good"]})')
    ax.axhline(y=THRESHOLDS['design_ptm_acceptable'], color=COLORS['highlight'], linestyle='--',
               alpha=0.7, label=f'Acceptable (>{THRESHOLDS["design_ptm_acceptable"]})')

    ax.set_xlabel('Design Rank', fontsize=11)
    ax.set_ylabel('Design pTM', fontsize=11)
    ax.set_title('A. Nanobody Structural Confidence', fontsize=12, fontweight='bold', loc='left')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, rotation=45, ha='right')
    ax.set_ylim(0, 1)
    ax.legend(loc='lower right', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    # Panel B: Design-to-Target iPTM (binding prediction)
    ax = axes[0, 1]
    prettify_ax(ax)

    iptm_values = df['design_to_target_iptm'].values
    iptm_colors = [COLORS['primary'] if v >= THRESHOLDS['iptm_good']
                   else COLORS['highlight'] if v >= THRESHOLDS['iptm_acceptable']
                   else COLORS['warning'] for v in iptm_values]

    bars = ax.bar(x_pos, iptm_values, color=iptm_colors, alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.axhline(y=THRESHOLDS['iptm_good'], color=COLORS['primary'], linestyle='--',
               alpha=0.7, label=f'Good (>{THRESHOLDS["iptm_good"]})')
    ax.axhline(y=THRESHOLDS['iptm_acceptable'], color=COLORS['highlight'], linestyle='--',
               alpha=0.7, label=f'Acceptable (>{THRESHOLDS["iptm_acceptable"]})')

    ax.set_xlabel('Design Rank', fontsize=11)
    ax.set_ylabel('Design-to-Target iPTM', fontsize=11)
    ax.set_title('B. Binding Prediction Score', fontsize=12, fontweight='bold', loc='left')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, rotation=45, ha='right')
    ax.legend(loc='upper right', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    # Panel C: Min PAE to target (lower is better)
    ax = axes[1, 0]
    prettify_ax(ax)

    pae_values = df['min_design_to_target_pae'].values
    pae_colors = [COLORS['primary'] if v <= THRESHOLDS['pae_good']
                  else COLORS['highlight'] if v <= THRESHOLDS['pae_acceptable']
                  else COLORS['warning'] for v in pae_values]

    bars = ax.bar(x_pos, pae_values, color=pae_colors, alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.axhline(y=THRESHOLDS['pae_good'], color=COLORS['primary'], linestyle='--',
               alpha=0.7, label=f'Good (<{THRESHOLDS["pae_good"]})')
    ax.axhline(y=THRESHOLDS['pae_acceptable'], color=COLORS['highlight'], linestyle='--',
               alpha=0.7, label=f'Acceptable (<{THRESHOLDS["pae_acceptable"]})')

    ax.set_xlabel('Design Rank', fontsize=11)
    ax.set_ylabel('Min PAE to Target (lower is better)', fontsize=11)
    ax.set_title('C. Interface Alignment Error', fontsize=12, fontweight='bold', loc='left')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, rotation=45, ha='right')
    ax.legend(loc='upper right', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    # Panel D: Filter RMSD (designability)
    ax = axes[1, 1]
    prettify_ax(ax)

    rmsd_values = df['filter_rmsd'].values
    rmsd_colors = [COLORS['primary'] if v <= THRESHOLDS['rmsd_good']
                   else COLORS['highlight'] if v <= THRESHOLDS['rmsd_acceptable']
                   else COLORS['warning'] for v in rmsd_values]

    bars = ax.bar(x_pos, rmsd_values, color=rmsd_colors, alpha=0.85, edgecolor='white', linewidth=0.5)
    ax.axhline(y=THRESHOLDS['rmsd_good'], color=COLORS['primary'], linestyle='--',
               alpha=0.7, label=f'Good (<{THRESHOLDS["rmsd_good"]} A)')
    ax.axhline(y=THRESHOLDS['rmsd_acceptable'], color=COLORS['highlight'], linestyle='--',
               alpha=0.7, label=f'Acceptable (<{THRESHOLDS["rmsd_acceptable"]} A)')

    ax.set_xlabel('Design Rank', fontsize=11)
    ax.set_ylabel('Filter RMSD (A, lower is better)', fontsize=11)
    ax.set_title('D. Backbone Designability', fontsize=12, fontweight='bold', loc='left')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, rotation=45, ha='right')
    ax.legend(loc='upper right', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Save
    output_path = Path(output_dir)
    fig.savefig(output_path / 'nanobody_results_main.pdf', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'nanobody_results_main.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"Saved: {output_path / 'nanobody_results_main.pdf'}")
    print(f"Saved: {output_path / 'nanobody_results_main.png'}")


def create_supplementary_figure(df, output_dir):
    """
    Create supplementary figure: Detailed analysis.

    Panel A: Quality metrics heatmap
    Panel B: Secondary structure composition
    Panel C: Interface metrics (H-bonds, delta SASA)
    Panel D: Design summary
    """
    n_designs = len(df)

    # Sort by final rank
    if 'final_rank' in df.columns:
        df = df.sort_values('final_rank').reset_index(drop=True)

    fig = plt.figure(figsize=(14, 12))
    gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.25)

    fig.suptitle('Nanobody Design - Supplementary Analysis', fontsize=16, fontweight='bold', y=0.98)

    # Panel A: Quality Metrics Heatmap
    ax = fig.add_subplot(gs[0, 0])

    # Normalize metrics (0-1 scale, higher is better)
    metrics_normalized = np.array([
        df['design_ptm'].values,  # Already 0-1, higher is better
        df['design_to_target_iptm'].values * 3,  # Scale up for visibility
        1 - df['min_design_to_target_pae'].values / 30,  # Lower is better, invert
        1 - df['filter_rmsd'].values / 25,  # Lower is better, invert
    ])
    metrics_normalized = np.clip(metrics_normalized, 0, 1)

    im = ax.imshow(metrics_normalized, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
    ax.set_xticks(np.arange(n_designs))
    ax.set_xticklabels([f"#{int(r)}" for r in df['final_rank']] if 'final_rank' in df.columns
                       else [f"{i+1}" for i in range(n_designs)], rotation=45, ha='right')
    ax.set_yticks(np.arange(4))
    ax.set_yticklabels(['Design pTM', 'iPTM (scaled)', 'PAE (inv)', 'RMSD (inv)'])
    ax.set_title('A. Normalized Quality Metrics', fontsize=12, fontweight='bold', loc='left')

    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Score (higher is better)', fontsize=9)

    # Add text annotations
    for i in range(4):
        for j in range(n_designs):
            val = metrics_normalized[i, j]
            color = 'white' if val < 0.5 else 'black'
            ax.text(j, i, f'{val:.2f}', ha='center', va='center', fontsize=7, color=color)

    # Panel B: Secondary Structure Composition
    ax = fig.add_subplot(gs[0, 1])
    prettify_ax(ax)

    x_pos = np.arange(n_designs)
    width = 0.25

    if all(col in df.columns for col in ['loop', 'helix', 'sheet']):
        loop_vals = df['loop'].values
        helix_vals = df['helix'].values
        sheet_vals = df['sheet'].values

        ax.bar(x_pos - width, loop_vals, width, label='Loop', color=COLORS['primary'], alpha=0.85)
        ax.bar(x_pos, helix_vals, width, label='Helix', color=COLORS['secondary'], alpha=0.85)
        ax.bar(x_pos + width, sheet_vals, width, label='Sheet', color=COLORS['highlight'], alpha=0.85)

        ax.set_xlabel('Design Rank', fontsize=11)
        ax.set_ylabel('Fraction', fontsize=11)
        ax.set_title('B. Secondary Structure Composition', fontsize=12, fontweight='bold', loc='left')
        ax.set_xticks(x_pos)
        ax.set_xticklabels([f"#{int(r)}" for r in df['final_rank']] if 'final_rank' in df.columns
                           else [f"{i+1}" for i in range(n_designs)], rotation=45, ha='right')
        ax.legend(loc='upper right', fontsize=9)
        ax.set_ylim(0, 1)
        ax.yaxis.grid(True, linestyle='--', alpha=0.5)
    else:
        ax.text(0.5, 0.5, 'Secondary structure\ndata not available',
                ha='center', va='center', fontsize=12, color=COLORS['light'])
        ax.set_title('B. Secondary Structure Composition', fontsize=12, fontweight='bold', loc='left')

    # Panel C: Interface Metrics
    ax = fig.add_subplot(gs[1, 0])
    prettify_ax(ax)

    if 'plip_hbonds_refolded' in df.columns and 'delta_sasa_refolded' in df.columns:
        # Scatter plot of H-bonds vs delta SASA
        hbonds = df['plip_hbonds_refolded'].values
        sasa = df['delta_sasa_refolded'].values

        scatter = ax.scatter(hbonds, sasa, c=df['design_to_target_iptm'].values,
                            cmap='viridis', s=150, alpha=0.8, edgecolor='white', linewidth=1.5)

        # Add labels
        for i, (h, s) in enumerate(zip(hbonds, sasa)):
            rank = int(df['final_rank'].iloc[i]) if 'final_rank' in df.columns else i+1
            ax.annotate(f'#{rank}', (h, s), xytext=(5, 5), textcoords='offset points', fontsize=8)

        ax.set_xlabel('H-bonds at Interface', fontsize=11)
        ax.set_ylabel('Delta SASA (A²)', fontsize=11)
        ax.set_title('C. Interface Quality Metrics', fontsize=12, fontweight='bold', loc='left')

        cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
        cbar.set_label('iPTM Score', fontsize=9)
        ax.grid(True, linestyle='--', alpha=0.3)
    else:
        ax.text(0.5, 0.5, 'Interface metrics\ndata not available',
                ha='center', va='center', fontsize=12, color=COLORS['light'])
        ax.set_title('C. Interface Quality Metrics', fontsize=12, fontweight='bold', loc='left')

    # Panel D: Summary Statistics
    ax = fig.add_subplot(gs[1, 1])
    ax.axis('off')

    # Calculate statistics
    n_good_ptm = (df['design_ptm'] >= THRESHOLDS['design_ptm_good']).sum()
    n_good_iptm = (df['design_to_target_iptm'] >= THRESHOLDS['iptm_good']).sum()
    n_good_pae = (df['min_design_to_target_pae'] <= THRESHOLDS['pae_good']).sum()
    n_good_rmsd = (df['filter_rmsd'] <= THRESHOLDS['rmsd_good']).sum()

    # Best design
    best_idx = 0  # Rank 1 is best
    if 'final_rank' in df.columns:
        best_idx = df['final_rank'].idxmin()

    best_design = df.iloc[best_idx] if 'final_rank' not in df.columns else df[df['final_rank'] == 1].iloc[0]

    # CDR sequence info
    cdr_seq = best_design.get('designed_sequence', 'N/A')
    if len(str(cdr_seq)) > 40:
        cdr_seq = str(cdr_seq)[:37] + '...'

    summary_text = f"""
NANOBODY DESIGN SUMMARY
{'='*45}

Total Designs Evaluated: {n_designs}

Quality Breakdown:
- Good pTM (>{THRESHOLDS['design_ptm_good']}): {n_good_ptm}/{n_designs} ({100*n_good_ptm/n_designs:.0f}%)
- Good iPTM (>{THRESHOLDS['iptm_good']}): {n_good_iptm}/{n_designs} ({100*n_good_iptm/n_designs:.0f}%)
- Good PAE (<{THRESHOLDS['pae_good']}): {n_good_pae}/{n_designs} ({100*n_good_pae/n_designs:.0f}%)
- Good RMSD (<{THRESHOLDS['rmsd_good']} A): {n_good_rmsd}/{n_designs} ({100*n_good_rmsd/n_designs:.0f}%)

Top Design (Rank #1): {best_design.get('id', 'N/A')}
- Design pTM: {best_design['design_ptm']:.3f}
- iPTM: {best_design['design_to_target_iptm']:.3f}
- Min PAE: {best_design['min_design_to_target_pae']:.2f}
- Filter RMSD: {best_design['filter_rmsd']:.2f} A
- H-bonds: {best_design.get('plip_hbonds_refolded', 'N/A')}
- Delta SASA: {best_design.get('delta_sasa_refolded', 'N/A'):.1f} A²

CDR Sequence: {cdr_seq}

{'='*45}
"""

    ax.text(0.02, 0.98, summary_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor=COLORS['background'], alpha=0.9, edgecolor=COLORS['light']))
    ax.set_title('D. Design Summary', fontsize=12, fontweight='bold', loc='left')

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Save
    output_path = Path(output_dir)
    fig.savefig(output_path / 'nanobody_results_supplementary.pdf', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'nanobody_results_supplementary.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"Saved: {output_path / 'nanobody_results_supplementary.pdf'}")
    print(f"Saved: {output_path / 'nanobody_results_supplementary.png'}")


def create_top_designs_comparison(df, output_dir, top_n=5):
    """
    Create comparison figure for top N designs.
    """
    # Sort by final rank
    if 'final_rank' in df.columns:
        df = df.sort_values('final_rank').head(top_n).reset_index(drop=True)
    else:
        df = df.head(top_n).reset_index(drop=True)

    n_designs = len(df)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f'Top {n_designs} Nanobody Designs Comparison', fontsize=14, fontweight='bold', y=1.02)

    x_pos = np.arange(n_designs)
    x_labels = [f"#{int(r)}\n{df['id'].iloc[i]}" for i, r in enumerate(df['final_rank'])] if 'final_rank' in df.columns else [f"Design {i+1}" for i in range(n_designs)]

    # Panel 1: Structural Quality
    ax = axes[0]
    prettify_ax(ax)

    width = 0.35
    ax.bar(x_pos - width/2, df['design_ptm'], width, label='Design pTM', color=COLORS['primary'], alpha=0.85)
    ax.bar(x_pos + width/2, df['design_to_target_iptm'] * 3, width, label='iPTM (x3)', color=COLORS['secondary'], alpha=0.85)

    ax.set_xlabel('Design', fontsize=11)
    ax.set_ylabel('Score', fontsize=11)
    ax.set_title('Structural Quality', fontsize=12, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, fontsize=8)
    ax.legend(loc='lower right', fontsize=9)
    ax.set_ylim(0, 1)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    # Panel 2: Interface Quality
    ax = axes[1]
    prettify_ax(ax)

    ax.bar(x_pos - width/2, df['min_design_to_target_pae'], width, label='Min PAE', color=COLORS['highlight'], alpha=0.85)
    ax.bar(x_pos + width/2, df['filter_rmsd'], width, label='Filter RMSD', color=COLORS['accent'], alpha=0.85)

    ax.set_xlabel('Design', fontsize=11)
    ax.set_ylabel('Value (lower is better)', fontsize=11)
    ax.set_title('Interface & Designability', fontsize=12, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, fontsize=8)
    ax.legend(loc='upper right', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    # Panel 3: CDR Length and H-bonds
    ax = axes[2]
    prettify_ax(ax)

    if 'num_design' in df.columns:
        cdr_lengths = df['num_design'].values
    elif 'designed_sequence' in df.columns:
        cdr_lengths = df['designed_sequence'].apply(len).values
    else:
        cdr_lengths = np.ones(n_designs) * 25

    hbonds = df.get('plip_hbonds_refolded', pd.Series([0]*n_designs)).values

    ax.bar(x_pos - width/2, cdr_lengths, width, label='CDR Length', color=COLORS['green'], alpha=0.85)
    ax.bar(x_pos + width/2, hbonds * 5, width, label='H-bonds (x5)', color=COLORS['warning'], alpha=0.85)

    ax.set_xlabel('Design', fontsize=11)
    ax.set_ylabel('Value', fontsize=11)
    ax.set_title('CDR Properties', fontsize=12, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, fontsize=8)
    ax.legend(loc='upper right', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()

    # Save
    output_path = Path(output_dir)
    fig.savefig(output_path / 'nanobody_results_top_designs.pdf', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'nanobody_results_top_designs.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"Saved: {output_path / 'nanobody_results_top_designs.pdf'}")
    print(f"Saved: {output_path / 'nanobody_results_top_designs.png'}")


def main():
    parser = argparse.ArgumentParser(description='Generate figures for Nanobody Design results')
    parser.add_argument('--results_dir', type=str, required=True,
                        help='Path to nanobody design results directory')
    parser.add_argument('--output_dir', type=str, default=None,
                        help='Output directory for figures (default: results_dir)')
    parser.add_argument('--top_n', type=int, default=5,
                        help='Number of top designs to compare (default: 5)')
    args = parser.parse_args()

    results_dir = Path(args.results_dir).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else results_dir

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nNanobody Design Results - Figure Generation")
    print(f"{'='*50}")
    print(f"Results directory: {results_dir}")
    print(f"Output directory: {output_dir}")
    print()

    # Load data
    df = load_metrics(results_dir)

    # Generate figures
    print("\nGenerating main figure...")
    create_main_figure(df, output_dir)

    print("\nGenerating supplementary figure...")
    create_supplementary_figure(df, output_dir)

    print("\nGenerating top designs comparison...")
    create_top_designs_comparison(df, output_dir, top_n=args.top_n)

    print(f"\n{'='*50}")
    print("Figure generation complete!")
    print(f"Output files saved to: {output_dir}")


if __name__ == '__main__':
    main()
