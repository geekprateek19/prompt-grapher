from setuptools import setup, find_packages

setup(
    name='prompt-grapher',
    version='1.1.0',
    author='geekprateek',
    description='CLI tool to extract codebase structural DNA via Graphify and dynamically generate context-aware .cursorrules.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click>=8.0.0',
        'networkx>=3.0',
        'openai>=1.0.0',
        'python-dotenv>=1.0.0'
    ],
    entry_points={
        'console_scripts': [
            'prompt-grapher=cli:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)