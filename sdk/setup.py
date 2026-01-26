"""
Setup script for Universal Agent Connector Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="universal-agent-connector",
    version="0.1.0",
    author="Universal Agent Connector Team",
    author_email="support@universal-agent-connector.com",
    description="Official Python SDK for Universal Agent Connector - AI agent management and database integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/universal-agent-connector/python-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai agent database connector sql llm openai anthropic",
    project_urls={
        "Documentation": "https://docs.universal-agent-connector.com",
        "Source": "https://github.com/universal-agent-connector/python-sdk",
        "Tracker": "https://github.com/universal-agent-connector/python-sdk/issues",
    },
)
