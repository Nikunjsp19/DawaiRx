"""Setup script for DawaiRx"""

from setuptools import setup, find_packages

setup(
    name="dawai-rx",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "pymongo>=4.6.0",
        "pydantic>=2.5.0",
        "pyyaml>=6.0.1",
        "click>=8.1.7",
    ],
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "dawai-rx=src.cli.main:cli",
        ],
    },
)

