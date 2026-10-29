from setuptools import setup, find_packages

setup(
    name="lazymeta",
    version="1.0.0",
    description="High-throughput 30-day automated bulk scheduler for Meta Graph API",
    author="exploriot",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.0.0",
        "requests>=2.28.0",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
        "urllib3>=1.26.0",
    ],
    entry_points={
        "console_scripts": [
            "lazymeta = lazymeta.cli:main",
        ],
    },
)
