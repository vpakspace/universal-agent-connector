"""
Setup script for AI Agent Connector
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="universal-agent-connector",
    version="1.0.0",
    author="Pankaj Kumar",
    author_email="badal.aiworld@gmail.com",
    description="Enterprise-grade MCP infrastructure with ontology-driven semantic routing for AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cloudbadal007/universal-agent-connector",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Flask",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    include_package_data=True,
    zip_safe=False,
)





