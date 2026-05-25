from setuptools import setup, find_packages

setup(
    name="smart_crawler",
    version="1.0.0",
    description="Fast async security web crawler with graph visualization pipelines",
    author="Hemalatha C",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires= [
        "aiohttp>=3.9.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=5.0.0",
        "networkx>=3.0",
        "matplotlib>=3.7.0",
        "pandas>=2.0.0",
    ],
    extras_require={
        "spa":["playwright>=1.40.0"],
    },
    entry_points={
        "console_scripts": [
            "smartcrawler=main:main"
        ],
    },
    )
