"""Build script for MoveVault using PyInstaller."""

import PyInstaller.__main__
import os
import sys
import shutil
import argparse
import json
from pathlib import Path
from core.institution_config import INSTITUTIONS

def build_executable(institution=None):
    """Build the executable using PyInstaller."""

    # Get the current directory
    current_dir = Path(__file__).parent

    # Determine institution and app name
    if institution and institution in INSTITUTIONS:
        app_name = INSTITUTIONS[institution]['app_name']
    else:
        # If no institution specified, use generic name
        app_name = "MoveVault"
        institution = None

    main_script = str(current_dir / "main.py")
    
    # PyInstaller arguments
    args = [
        main_script,
        '--name', app_name,
        '--onefile',
        '--windowed',  # No console window
        '--clean',
        '--noconfirm',
        f'--distpath={current_dir / "dist"}',
        f'--workpath={current_dir / "build"}',
        f'--specpath={current_dir}',
        '--hidden-import', 'packaging.version',
        '--hidden-import', 'packaging.requirements',
        '--hidden-import', 'packaging.specifiers',
        '--hidden-import', 'requests',
        '--hidden-import', 'boto3',
        '--hidden-import', 'PySide6.QtCore',
        '--hidden-import', 'PySide6.QtWidgets',
        '--hidden-import', 'PySide6.QtGui',
        '--collect-all', 'packaging',
    ]
    
    # Add DemoData if it exists
    demo_data_path = current_dir / "DemoData"
    if demo_data_path.exists():
        args.extend(['--add-data', f'{demo_data_path}:DemoData'])
        print(f"Including DemoData folder: {demo_data_path}")
    else:
        print("DemoData folder not found, skipping...")
    
    # Add credentials file if it exists (for embedded builds)
    credentials_path = current_dir / ".credentials"
    if credentials_path.exists():
        args.extend(['--add-data', f'{credentials_path}:.'])
        print(f"Including embedded credentials file: {credentials_path}")
    else:
        print("Credentials file not found, building without embedded credentials...")

    # Add institution file if specified (for embedded builds)
    if institution:
        institution_file = current_dir / ".institution"
        with open(institution_file, 'w') as f:
            f.write(institution)
        args.extend(['--add-data', f'{institution_file}:.'])
        print(f"Including embedded institution file: {institution_file}")
    else:
        print("No institution specified, building generic version...")
    
    # Add platform-specific arguments
    if sys.platform == "win32":
        # Windows-specific settings - keep onefile for Windows
        pass  # No icon for now, can be added later
    elif sys.platform == "darwin":
        # macOS-specific settings - use onedir mode to avoid security issues
        # Remove --onefile and --windowed for macOS to avoid conflicts
        if '--onefile' in args:
            args.remove('--onefile')
        if '--windowed' in args:
            args.remove('--windowed')
        args.extend([
            '--onedir',  # Use directory mode for macOS
            '--windowed',  # macOS can handle windowed + onedir
        ])
    
    print(f"Building {app_name} executable...")
    print(f"Platform: {sys.platform}")
    print(f"Arguments: {' '.join(args)}")
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print(f"\nBuild completed! Executable is in: {current_dir / 'dist'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build MoveVault executable')
    parser.add_argument('--institution', choices=list(INSTITUTIONS.keys()),
                       help='Institution to build for (creates institution-specific binary)')
    parser.add_argument('--all', action='store_true',
                       help='Build binaries for all institutions')

    args = parser.parse_args()

    if args.all:
        print("Building binaries for all institutions...")
        for institution in INSTITUTIONS.keys():
            print(f"\n{'='*50}")
            print(f"Building for institution: {institution}")
            print(f"{'='*50}")
            build_executable(institution)
    else:
        build_executable(args.institution)