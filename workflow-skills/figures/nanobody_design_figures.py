#!/usr/bin/env python3
"""
Generate figures for Nanobody Design workflow.

This script creates:
1. Main figure: High-level workflow overview for the main manuscript
2. Supplementary figure: Detailed step-by-step workflow with all 7 steps

Usage:
    python nanobody_design_figures.py
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import matplotlib.patheffects as path_effects
import numpy as np
from pathlib import Path

# Color palette
COLORS = {
    'input': '#3498db',       # Blue - input files
    'config': '#9b59b6',      # Purple - configuration
    'process': '#27ae60',     # Green - processing steps
    'output': '#e74c3c',      # Red - outputs
    'mcp': '#f39c12',         # Orange - MCP tools
    'background': '#f8f9fa',  # Light gray background
    'text': '#2c3e50',        # Dark text
    'arrow': '#7f8c8d',       # Gray arrows
    'boltzgen': '#1abc9c',    # Teal - BoltzGen specific
    'step_bg': '#ecf0f1',     # Step background
}


def prettify_ax(ax):
    """Remove spines and ticks for clean visualization."""
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def draw_rounded_box(ax, x, y, width, height, label, color, fontsize=10,
                      text_color='white', alpha=1.0, sublabel=None):
    """Draw a rounded rectangle with label."""
    box = FancyBboxPatch(
        (x - width/2, y - height/2), width, height,
        boxstyle="round,pad=0.03,rounding_size=0.05",
        facecolor=color, edgecolor='white', linewidth=2, alpha=alpha
    )
    ax.add_patch(box)

    # Main label
    if sublabel:
        ax.text(x, y + 0.02, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=text_color)
        ax.text(x, y - 0.04, sublabel, ha='center', va='center',
                fontsize=fontsize-2, color=text_color, style='italic')
    else:
        ax.text(x, y, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=text_color)

    return box


def draw_arrow(ax, start, end, color=None, style='simple', connectionstyle='arc3,rad=0'):
    """Draw an arrow between two points."""
    if color is None:
        color = COLORS['arrow']

    arrow = FancyArrowPatch(
        start, end,
        arrowstyle='-|>',
        color=color,
        linewidth=2,
        connectionstyle=connectionstyle,
        mutation_scale=15
    )
    ax.add_patch(arrow)
    return arrow


def draw_step_box(ax, x, y, width, height, step_num, title, description, color):
    """Draw a step box with number badge."""
    # Main box
    box = FancyBboxPatch(
        (x - width/2, y - height/2), width, height,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        facecolor='white', edgecolor=color, linewidth=2
    )
    ax.add_patch(box)

    # Step number circle
    circle = Circle((x - width/2 + 0.03, y + height/2 - 0.03), 0.025,
                   facecolor=color, edgecolor='white', linewidth=1.5)
    ax.add_patch(circle)
    ax.text(x - width/2 + 0.03, y + height/2 - 0.03, str(step_num),
            ha='center', va='center', fontsize=8, fontweight='bold', color='white')

    # Title
    ax.text(x, y + 0.02, title, ha='center', va='center',
            fontsize=9, fontweight='bold', color=COLORS['text'])

    # Description
    ax.text(x, y - 0.025, description, ha='center', va='center',
            fontsize=7, color=COLORS['text'], style='italic')


def create_main_figure():
    """
    Create the main figure: High-level Nanobody Design workflow.

    This figure shows the conceptual flow suitable for main manuscript.
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 0.6)
    prettify_ax(ax)

    # Title
    ax.text(0.5, 0.55, 'Nanobody Design Workflow', ha='center', va='center',
            fontsize=16, fontweight='bold', color=COLORS['text'])
    ax.text(0.5, 0.50, 'BoltzGen-powered CDR loop design for VHH antibodies',
            ha='center', va='center', fontsize=10, color=COLORS['text'], style='italic')

    # Input section (left)
    draw_rounded_box(ax, 0.12, 0.30, 0.18, 0.12, 'Target Structure',
                     COLORS['input'], sublabel='CIF/PDB file')

    # Configuration (second from left)
    draw_rounded_box(ax, 0.32, 0.30, 0.16, 0.12, 'Configuration',
                     COLORS['config'], sublabel='YAML config')

    # BoltzGen MCP (center) - larger box
    draw_rounded_box(ax, 0.54, 0.30, 0.20, 0.16, 'BoltzGen MCP',
                     COLORS['boltzgen'], fontsize=12, sublabel='nanobody-anything')

    # Design Process (second from right)
    draw_rounded_box(ax, 0.76, 0.30, 0.16, 0.12, 'CDR Design',
                     COLORS['process'], sublabel='Cysteine-filtered')

    # Output (right)
    draw_rounded_box(ax, 0.92, 0.30, 0.14, 0.12, 'Nanobodies',
                     COLORS['output'], sublabel='PDB structures')

    # Arrows
    draw_arrow(ax, (0.21, 0.30), (0.24, 0.30))
    draw_arrow(ax, (0.40, 0.30), (0.44, 0.30))
    draw_arrow(ax, (0.64, 0.30), (0.68, 0.30))
    draw_arrow(ax, (0.84, 0.30), (0.85, 0.30))

    # Bottom annotation - key features
    features = [
        ('VHH Single-Domain', 0.20),
        ('CDR Loop Optimization', 0.40),
        ('Cysteine Filtering', 0.60),
        ('Multiple Designs', 0.80)
    ]

    for label, x in features:
        ax.text(x, 0.10, label, ha='center', va='center', fontsize=8,
                color=COLORS['text'], style='italic',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=COLORS['step_bg'],
                         edgecolor='none'))

    # Legend
    legend_items = [
        ('Input', COLORS['input']),
        ('Config', COLORS['config']),
        ('MCP Tool', COLORS['boltzgen']),
        ('Process', COLORS['process']),
        ('Output', COLORS['output']),
    ]

    for i, (label, color) in enumerate(legend_items):
        x = 0.12 + i * 0.15
        box = FancyBboxPatch((x - 0.02, 0.02), 0.04, 0.02,
                             boxstyle="round,pad=0.01", facecolor=color, edgecolor='none')
        ax.add_patch(box)
        ax.text(x + 0.04, 0.03, label, ha='left', va='center', fontsize=7, color=COLORS['text'])

    plt.tight_layout()
    return fig


def create_supplementary_figure():
    """
    Create the supplementary figure: Detailed step-by-step workflow.

    Shows all 7 steps with MCP tool details.
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    prettify_ax(ax)

    # Title
    ax.text(0.5, 0.96, 'Nanobody Design Workflow - Detailed Steps', ha='center', va='center',
            fontsize=16, fontweight='bold', color=COLORS['text'])
    ax.text(0.5, 0.92, 'Complete 7-step protocol using BoltzGen MCP for VHH antibody design',
            ha='center', va='center', fontsize=10, color=COLORS['text'], style='italic')

    # Step definitions
    steps = [
        {
            'num': 0, 'title': 'Setup Results Directory',
            'desc': 'Create output structure',
            'mcp': None,
            'color': COLORS['process']
        },
        {
            'num': 1, 'title': 'Prepare BoltzGen Config',
            'desc': 'Generate YAML configuration',
            'mcp': None,
            'color': COLORS['config']
        },
        {
            'num': 2, 'title': 'Validate Configuration',
            'desc': 'Check config validity',
            'mcp': 'validate_config',
            'color': COLORS['boltzgen']
        },
        {
            'num': 3, 'title': 'Submit Design Job',
            'desc': 'nanobody-anything protocol',
            'mcp': 'submit_generic_boltzgen',
            'color': COLORS['boltzgen']
        },
        {
            'num': 4, 'title': 'Monitor Progress',
            'desc': 'Check job status & logs',
            'mcp': 'get_job_status / get_job_log',
            'color': COLORS['boltzgen']
        },
        {
            'num': 5, 'title': 'Get Job Results',
            'desc': 'Retrieve completed designs',
            'mcp': 'get_job_result',
            'color': COLORS['boltzgen']
        },
        {
            'num': 6, 'title': 'Analyze Nanobodies',
            'desc': 'Summarize & evaluate',
            'mcp': None,
            'color': COLORS['output']
        },
    ]

    # Layout: 4 steps on top row, 3 steps on bottom row
    top_row_y = 0.70
    bottom_row_y = 0.40
    box_width = 0.18
    box_height = 0.14

    # Top row: Steps 0-3
    top_positions = [0.14, 0.36, 0.58, 0.80]
    for i, step in enumerate(steps[:4]):
        x = top_positions[i]
        draw_step_box(ax, x, top_row_y, box_width, box_height,
                     step['num'], step['title'], step['desc'], step['color'])

        # Add MCP tool label if present
        if step['mcp']:
            ax.text(x, top_row_y - 0.055, f"boltzgen_mcp:", ha='center', va='top',
                   fontsize=6, color=COLORS['mcp'], fontweight='bold')
            ax.text(x, top_row_y - 0.075, step['mcp'], ha='center', va='top',
                   fontsize=6, color=COLORS['mcp'])

        # Arrow to next step
        if i < 3:
            draw_arrow(ax, (x + box_width/2 + 0.01, top_row_y),
                      (top_positions[i+1] - box_width/2 - 0.01, top_row_y))

    # Arrow from Step 3 down to Step 4
    draw_arrow(ax, (0.80, top_row_y - box_height/2 - 0.01),
               (0.80, bottom_row_y + box_height/2 + 0.01),
               connectionstyle='arc3,rad=0')

    # Bottom row: Steps 4-6
    bottom_positions = [0.80, 0.50, 0.20]
    for i, step in enumerate(steps[4:]):
        x = bottom_positions[i]
        draw_step_box(ax, x, bottom_row_y, box_width, box_height,
                     step['num'], step['title'], step['desc'], step['color'])

        # Add MCP tool label if present
        if step['mcp']:
            ax.text(x, bottom_row_y - 0.055, f"boltzgen_mcp:", ha='center', va='top',
                   fontsize=6, color=COLORS['mcp'], fontweight='bold')
            ax.text(x, bottom_row_y - 0.075, step['mcp'], ha='center', va='top',
                   fontsize=6, color=COLORS['mcp'])

        # Arrow to next step (going left)
        if i < 2:
            draw_arrow(ax, (x - box_width/2 - 0.01, bottom_row_y),
                      (bottom_positions[i+1] + box_width/2 + 0.01, bottom_row_y))

    # Input/Output boxes
    # Input box (top left)
    input_box_x, input_box_y = 0.08, 0.85
    draw_rounded_box(ax, input_box_x, input_box_y, 0.12, 0.06, 'Inputs',
                     COLORS['input'], fontsize=9)
    ax.text(input_box_x, input_box_y - 0.05, 'TARGET_CIF\nTARGET_CHAIN',
            ha='center', va='top', fontsize=7, color=COLORS['text'])

    # Output box (bottom left)
    output_box_x, output_box_y = 0.08, 0.25
    draw_rounded_box(ax, output_box_x, output_box_y, 0.12, 0.06, 'Outputs',
                     COLORS['output'], fontsize=9)
    ax.text(output_box_x, output_box_y - 0.05, 'designs/*.pdb\nNanobody-target\ncomplexes',
            ha='center', va='top', fontsize=7, color=COLORS['text'])

    # BoltzGen MCP server box (center bottom)
    mcp_box_x, mcp_box_y = 0.50, 0.15
    mcp_box = FancyBboxPatch(
        (mcp_box_x - 0.15, mcp_box_y - 0.05), 0.30, 0.08,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        facecolor=COLORS['mcp'], edgecolor='white', linewidth=2, alpha=0.3
    )
    ax.add_patch(mcp_box)
    ax.text(mcp_box_x, mcp_box_y, 'BoltzGen MCP Server', ha='center', va='center',
            fontsize=10, fontweight='bold', color=COLORS['mcp'])
    ax.text(mcp_box_x, mcp_box_y - 0.03, 'GPU-accelerated nanobody CDR design',
            ha='center', va='center', fontsize=7, color=COLORS['text'], style='italic')

    # Key features box (right side)
    features_x = 0.92
    features_y = 0.55

    ax.text(features_x, features_y + 0.08, 'Key Features', ha='center', va='center',
            fontsize=10, fontweight='bold', color=COLORS['text'])

    features = [
        'VHH Single-Domain Design',
        'CDR Loop Optimization',
        'Cysteine Filtering',
        'Multiple Design Generation',
        'Scaffold Support (optional)'
    ]

    for i, feature in enumerate(features):
        y = features_y - i * 0.035
        ax.text(features_x, y, f'\u2022 {feature}', ha='center', va='center',
               fontsize=7, color=COLORS['text'])

    # Legend
    legend_items = [
        ('Setup/Process', COLORS['process']),
        ('Configuration', COLORS['config']),
        ('BoltzGen MCP', COLORS['boltzgen']),
        ('Output/Analysis', COLORS['output']),
        ('MCP Tools', COLORS['mcp']),
    ]

    ax.text(0.50, 0.05, 'Legend:', ha='right', va='center', fontsize=8,
            fontweight='bold', color=COLORS['text'])

    for i, (label, color) in enumerate(legend_items):
        x = 0.52 + i * 0.10
        box = FancyBboxPatch((x - 0.015, 0.04), 0.03, 0.02,
                             boxstyle="round,pad=0.01", facecolor=color, edgecolor='none')
        ax.add_patch(box)
        ax.text(x + 0.025, 0.05, label, ha='left', va='center', fontsize=6, color=COLORS['text'])

    plt.tight_layout()
    return fig


def main():
    """Generate all figures."""
    output_dir = Path(__file__).parent

    print("Generating Nanobody Design workflow figures...")

    # Main figure
    print("  Creating main figure...")
    fig_main = create_main_figure()
    fig_main.savefig(output_dir / 'nanobody_design_main.png', dpi=300,
                     bbox_inches='tight', facecolor='white')
    fig_main.savefig(output_dir / 'nanobody_design_main.pdf',
                     bbox_inches='tight', facecolor='white')
    plt.close(fig_main)
    print("    Saved: nanobody_design_main.png/pdf")

    # Supplementary figure
    print("  Creating supplementary figure...")
    fig_supp = create_supplementary_figure()
    fig_supp.savefig(output_dir / 'nanobody_design_supplementary.png', dpi=300,
                     bbox_inches='tight', facecolor='white')
    fig_supp.savefig(output_dir / 'nanobody_design_supplementary.pdf',
                     bbox_inches='tight', facecolor='white')
    plt.close(fig_supp)
    print("    Saved: nanobody_design_supplementary.png/pdf")

    print("\nAll figures generated successfully!")
    print(f"Output directory: {output_dir}")


if __name__ == '__main__':
    main()
