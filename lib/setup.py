#!/usr/bin/env python3
"""
Setup script for n8n workflow validation and visualization tools.
"""
from setuptools import setup, find_packages

setup(
    name="n8n-workflow-tools",
    version="1.0.0",
    description="Validation and visualization tools for n8n workflows",
    author="n8n Community",
    py_modules=[
        'n8n_validator',
        'n8n_visualizer',
        'n8n_validate', 
        'n8n_visualize'
    ],
    install_requires=[
        'jsonschema>=4.0.0',
        'pillow>=9.0.0',
        'matplotlib>=3.5.0',
        'networkx>=2.8.0',
        'requests>=2.28.0'
    ],
    entry_points={
        'console_scripts': [
            'n8n-validate=n8n_validate:main',
            'n8n-visualize=n8n_visualize:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.8',
)