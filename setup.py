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
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "jinja2>=3.1.2",
        "python-multipart>=0.0.6",
        "bcrypt>=4.1.0",
        "pyjwt>=2.8.0",
        "python-jose[cryptography]>=3.3.0",
        "reportlab>=4.0.0",
        "Pillow>=10.0.0",
    ],
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "dawai-rx=src.cli.main:cli",
        ],
    },
)
