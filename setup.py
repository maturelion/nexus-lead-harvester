from setuptools import setup, find_packages

setup(
    name="nexus-harvester",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "dnspython",
        "requests"
    ],
    entry_points={
        'console_scripts': [
            'nexus-hunt=nexus_harvester.cli:main',
        ],
    },
    author="Sky Lion Pride",
    description="Autonomous lead extraction and technical vulnerability analysis engine.",
)
