"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from os import name
from setuptools import setup

APP = ['editor.py']
DATA_FILES = ['logo.ico']
OPTIONS = {
    'packages': ['i18n'],
}

setup(
    name="RouteMaster",
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
