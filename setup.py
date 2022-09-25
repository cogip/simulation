#!/usr/bin/env python3

from setuptools import setup, find_packages
from pathlib import Path

cwd = Path(__file__).resolve().parent

name = 'cogip-tools'
version = '1.0'
release = '1.0.0'

readme_filename = cwd / "README.md"
long_description = readme_filename.open().read()

marker_platform_x86_64 = "platform_machine=='x86_64'"

required_packages = [
    # Common packages
    "py-spy==0.3.11",
    "pydantic==1.9.0",
    "pyserial==3.5",
    "python-dotenv==0.19.2",

    # Packages specific to monitor
    "PySide6==6.3.2;" + marker_platform_x86_64,
    "sysv-ipc==1.1.0;" + marker_platform_x86_64,
    "typer==0.4.1;" + marker_platform_x86_64,

    # Packages specific to Copilot and Robotcam
    "aiohttp==3.8.1",
    "aioserial==1.3.0",
    "fastapi==0.75.0",
    "Jinja2==3.0.3",
    "opencv-contrib-python==4.5.5.64",
    "polling2==0.5.0",
    "protobuf==3.19.4",
    "python-socketio==5.5.1",
    "requests==2.27.1",
    "uvicorn[standard]==0.17.6",
    "websocket-client==1.3.1",

    # Packages specific to documentation
    "MarkupSafe==2.0.1;" + marker_platform_x86_64,
    "mkdocs==1.3.0;" + marker_platform_x86_64,
    "mkdocs-gen-files==0.3.3;" + marker_platform_x86_64,
    "mkdocs-literate-nav==0.4.1;" + marker_platform_x86_64,
    "mkdocs-material==8.2.13;" + marker_platform_x86_64,
    "mkdocstrings==0.17.0;" + marker_platform_x86_64,
    "pymdown-extensions==9.4;" + marker_platform_x86_64,

    # Packages specific to developers
    "flake8==3.9.2;" + marker_platform_x86_64,
]

setup(
    name=name,
    version=release,
    description='COGIP Simulation Tools',
    author='COGIP Team',
    author_email='cogip35@gmail.com',
    url='https://github.com/cogip/simulation',
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.8',
    install_requires=required_packages,
    packages=find_packages(),
    package_data={
        "cogip.tools.copilot": [
            "static/css/*",
            "static/css/external/*",
            "static/img/*",
            "static/js/*",
            "static/js/external/*",
            "templates/*"
        ],
        "cogip.tools.robotcam": [
            "data/*"
        ]

    },
    entry_points={
        'console_scripts': [
            'cogip-monitor=cogip.tools.monitor.main:main',
            'cogip-replay=cogip.tools.replay.main:main',
            'cogip-copilot=cogip.tools.copilot.main:main',
            'cogip-detector=cogip.tools.detector.__main__:main',
            'cogip-robotcam=cogip.tools.robotcam.main:main',
            'cogip-lidarusb=cogip.tools.lidarusb.main:main',
            'cogip-lidarpf=cogip.tools.lidarpf.main:main'
        ]
    }
)
