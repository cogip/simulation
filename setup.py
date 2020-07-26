#!/usr/bin/env python3

from setuptools import setup, find_packages
# from sphinx.setup_command import BuildDoc
# import sphinx
from pathlib import Path

cwd = Path(__file__).resolve().parent

name = 'cogip-simulator'
version = '1.0'
release = '1.0.0'

readme_filename =  cwd / "README.md"
long_description = readme_filename.open().read()

required_packages = [
    "PyQt5==5.13.1",
    "sphinx==2.2.1",
    "autodoc==0.5.0",
    "pydantic==1.6.1",
    "sphinxcontrib-drawio==0.0.7",
    "sphinx-argparse==0.2.5",
    "python-dotenv==0.10.3"
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
    python_requires='>=3.6',
    install_requires=required_packages,
    packages=find_packages(),
    scripts=['bin/simulator.py'],
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
