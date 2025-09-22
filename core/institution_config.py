"""Institution-specific configuration for MoveVault."""

import os
import sys

# Institution configurations
INSTITUTIONS = {
    'Ranipet': {
        'base_folder': 'Ranipet',
        'display_name': 'Ranipet Medical Center',
        'app_name': 'MoveVault_Ranipet'
    },
    'Manipal': {
        'base_folder': 'Manipal',
        'display_name': 'Manipal Hospital',
        'app_name': 'MoveVault_Manipal'
    },
    'Ludhiana': {
        'base_folder': 'Ludhiana',
        'display_name': 'Ludhiana Medical Center',
        'app_name': 'MoveVault_Ludhiana'
    },
    'CMC': {
        'base_folder': 'CMC',
        'display_name': 'Christian Medical College',
        'app_name': 'MoveVault_CMC'
    }
}

def get_institution_config():
    """Get the current institution configuration based on build-time setting or environment variable."""
    # First, try to get from build-time embedded institution file
    try:
        if getattr(sys, 'frozen', False):
            # Running as executable, look for embedded institution in PyInstaller temp directory
            if hasattr(sys, '_MEIPASS'):
                institution_file = os.path.join(sys._MEIPASS, '.institution')
            else:
                app_dir = os.path.dirname(sys.executable)
                institution_file = os.path.join(app_dir, '.institution')
        else:
            # Running as script, look in current directory
            institution_file = '.institution'

        if os.path.exists(institution_file):
            with open(institution_file, 'r') as f:
                institution = f.read().strip()
                if institution in INSTITUTIONS:
                    return INSTITUTIONS[institution]
    except Exception as e:
        print(f"Failed to load embedded institution: {e}")

    # Fallback to environment variable
    institution = os.getenv('MOVEVAULT_INSTITUTION', 'Ranipet')

    if institution in INSTITUTIONS:
        return INSTITUTIONS[institution]

    # Default fallback
    print(f"Warning: Unknown institution '{institution}', defaulting to Ranipet")
    return INSTITUTIONS['Ranipet']

def get_current_institution():
    """Get the current institution name."""
    config = get_institution_config()
    for name, cfg in INSTITUTIONS.items():
        if cfg == config:
            return name
    return 'Ranipet'

def get_base_folder():
    """Get the base folder for the current institution."""
    return get_institution_config()['base_folder']

def get_display_name():
    """Get the display name for the current institution."""
    return get_institution_config()['display_name']

def get_app_name():
    """Get the app name for the current institution."""
    return get_institution_config()['app_name']