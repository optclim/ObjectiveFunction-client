from setuptools import setup, find_packages
from sphinx.setup_command import BuildDoc

name = 'ObjectiveFunction-client'
version = '0.1'
release = '0.1.0'
author = 'Magnus Hagdorn'

setup(
    name=name,
    packages=find_packages(),
    version=release,
    include_package_data=True,
    install_requires=[
        'requests',
        'configobj',
        'numpy>=1.21.0',
        'pandas',
        'dfo-ls',
    ],
    cmdclass={'build_sphinx': BuildDoc},
    command_options={
        'build_sphinx': {
            'project': ('setup.py', name),
            'version': ('setup.py', version),
            'release': ('setup.py', release),
            'copyright': ('setup.py', author),
            'source_dir': ('setup.py', 'docs')}},
    setup_requires=['sphinx'],
    extras_require={
        'docs': [
            'sphinx<4.0',
            'sphinx_rtd_theme',
            'sphinxcontrib.httpdomain',
        ],
        'lint': [
            'flake8>=3.5.0',
        ],
        'testing': [
            'pytest',
            'requests_mock',
        ],
    },
    entry_points={
        'console_scripts': [
            'objfun-manage=ObjectiveFunction_client.manage:main',
            'objfun-nlopt = ObjectiveFunction_client.optimise:main',
            'objfun-dfols = ObjectiveFunction_client.dfols:main',
            'objfun-example-model = ObjectiveFunction_client.example:main',
        ],
    },
    author=author,
    description="Client ObjectiveFunction optimisation framework",
)
