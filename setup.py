from importlib.machinery import SourceFileLoader
from pathlib import Path

from setuptools import setup

description = 'Experiment in an alternative to jupyter notebooks'
THIS_DIR = Path(__file__).resolve().parent
try:
    long_description = THIS_DIR.joinpath('README.md').read_text()
except FileNotFoundError:
    long_description = description

# avoid loading the package before requirements are installed:
version = SourceFileLoader('version', 'notbook/version.py').load_module()

setup(
    name='notbook',
    version=version.VERSION,
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX :: Linux',
        'Environment :: MacOS X',
    ],
    author='Samuel Colvin',
    author_email='s@muelcolvin.com',
    url='https://github.com/samuelcolvin/notbook',
    license='MIT',
    packages=['notbook'],
    entry_points="""
        [console_scripts]
        notbook=notbook.__main__:cli
    """,
    python_requires='>=3.8',
    zip_safe=True,
    install_requires=[
        'watchgod>=0.6',
    ],
)
