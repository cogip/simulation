#!/usr/bin/env python3

from setuptools import setup, find_packages
# from sphinx.setup_command import BuildDoc
# import sphinx
from pathlib import Path

cwd = Path(__file__).resolve().parent

name = 'cogip-simulator'
version = '1.0'
release = '1.0.0'

readme_filename = cwd / "README.md"
long_description = readme_filename.open().read()

required_packages = [
    "flake8==3.8.3",
    "mkdocs==1.1.2",
    "mkdocs-material==5.5.12",
    "mkdocstrings==0.13.2",
    "psutil==5.7.2",
    "ptvsd==4.3.2",
    "pydantic==1.7.3",
    "pymdown-extensions==8.0",
    "pyserial==3.5",
    "PySide2==5.15.0",
    "python-dotenv==0.14.0",
    "sysv-ipc==1.0.1"
]

# cmdclass = {'build_doc': BuildDoc}

# sphinx.build_main(['setup.py', '-b', 'html', 'doc/source', 'doc/build'])

setup(
    name=name,
    version=release,
    description='COGIP Simulator',
    author='COGIP Team',
    author_email='',
    url='https://github.com/cogip/',
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.7',
    install_requires=required_packages,
    packages=find_packages(),
    entry_points = {
        'console_scripts': ['simulator=cogip.__main__:main'],
    },
    # cmdclass=cmdclass,
    # command_options={
    #     'build_doc': {
    #         'project': ('setup.py', name),
    #         'version': ('setup.py', version),
    #         'release': ('setup.py', release),
    #         'source_dir': ('setup.py', 'doc/source'),
    #         'build_dir': ('setup.py', 'doc/build')
    #     }
    # },
)
