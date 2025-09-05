#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open("README.md") as f:
    long_description = f.read()

setup(
    name="ratelimiter",
    version="1.0.0",
    description="A Python CLI rate limiter with multiple algorithms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Henry Tan",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "limiter=ratelimiter.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)

