from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).parent.resolve()


setup(
    name="prompt-grapher",
    version="1.4.1",
    author="geekprateek",
    description="Generate repository-specific Cursor rules, AGENTS.md, onboarding docs, and AI memory packs from Graphify dependency graphs.",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    py_modules=["cli"],
    include_package_data=True,
    install_requires=[
        "click>=8.1.7",
        "graphifyy>=0.8.14",
        "networkx>=3.2",
        "openai>=1.30.0",
        "python-dotenv>=1.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=8.2.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "prompt-grapher=cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
