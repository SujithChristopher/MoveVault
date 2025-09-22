"""Build script for ActiGraph S3 Uploader using PyInstaller."""

import PyInstaller.__main__
import os
import sys
import shutil
from pathlib import Path

def build_executable():
    """Build the executable using PyInstaller."""
    
    # Get the current directory
    current_dir = Path(__file__).parent
    
    # Define build parameters
    app_name = "ActiGraphUploader"
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
    build_executable()