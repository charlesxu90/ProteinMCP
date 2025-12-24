#!/usr/bin/env python3
"""
ProteinMCP - Setup Script

This setup script enables installation of ProteinMCP as a Python package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

# Read requirements from requirements.txt
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#')
        ]
    # Filter out built-in modules
    builtin_modules = {'subprocess', 'yaml'}
    requirements = [req for req in requirements if req not in builtin_modules]
    # Fix yaml -> PyYAML
    requirements = ['PyYAML' if req == 'yaml' else req for req in requirements]

setup(
    name="proteinmcp",
    version="0.1.0",
    author="ProteinMCP Team",
    author_email="",
    description="Protein Engineering Model Context Protocol Package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/charlesxu90/proteinmcp",
    packages=find_packages(),
    package_dir={"proteinmcp": "src"},
    include_package_data=True,
    package_data={
        'proteinmcp': [
            'prompts/*.md',
            'mcp/configs/*.yaml',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'proteinmcp=src.mcp_cli:main',
            'pmcp=src.mcp_cli:main',
            'proteinskill=src.skill_cli:main',
            'pskill=src.skill_cli:main',
        ],
    },
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-cov>=4.0',
            'black>=23.0',
            'flake8>=6.0',
            'mypy>=1.0',
        ],
    },
    zip_safe=False,
)
