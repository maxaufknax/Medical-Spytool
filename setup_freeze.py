#!/usr/bin/env python3
"""
Setup script for cx_Freeze to create Medical-Spytool executable
"""

import sys
import os
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_options = {
    'packages': [
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog', 
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'numpy',
        'pandas',
        'requests',
        'lxml',
        'bs4',
        'wordcloud',
        'openpyxl',
        'xml.etree.ElementTree',
        'urllib.parse',
        'urllib.request',
        'json',
        'csv',
        'queue',
        'threading',
        'time',
        'os',
        'sys',
        'webbrowser',
        'dnb_spytool',
        'dnb_spytool.analytics',
        'dnb_spytool.api',
        'dnb_spytool.gui',
        'dnb_spytool.utils'
    ],
    'excludes': [
        'test',
        'tests',
        'unittest',
        'pdb',
        'doctest',
        'difflib'
    ],
    'include_files': [
        ('README.md', 'README.md'),
        ('LICENSE', 'LICENSE'),
        ('requirements.txt', 'requirements.txt'),
        ('RELEASE_NOTES_v1.1.md', 'RELEASE_NOTES_v1.1.md'),
    ],
    'zip_include_packages': ['*'],
    'zip_exclude_packages': [],
    'silent': False,
    'optimize': 2,
}

# GUI applications require a different base on Windows (the default is for a console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"
elif sys.platform == "darwin":
    base = None
else:  # Linux and others
    base = None

# Main executable
executables = [
    Executable(
        'dnb_spytool/__main__.py',
        base=base,
        target_name='Medical-Spytool',
        icon=None,  # Add icon path if available
        shortcut_name='Medical Spytool',
        shortcut_dir='DesktopFolder',
    )
]

# Setup configuration
setup(
    name='Medical-Spytool',
    version='1.1.0',
    description='Medical Literature Research Tool - Search DNB and PubMed databases',
    author='Medical Spytool Team',
    url='https://github.com/maxaufknax/Medical-Spytool',
    options={'build_exe': build_options},
    executables=executables,
    requires=[
        'tkinter',
        'matplotlib',
        'requests',
        'pandas',
        'numpy',
        'lxml',
        'beautifulsoup4',
        'wordcloud',
        'openpyxl'
    ]
)
