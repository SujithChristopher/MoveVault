#!/usr/bin/env python3
"""Verify credentials file exists and is valid."""

import json
import os
import sys

def main():
    if os.path.exists('.credentials'):
        print('SUCCESS: Credentials file exists')
        try:
            with open('.credentials', 'r') as f:
                data = json.load(f)
            print('SUCCESS: Credentials file is valid JSON')
            institution = data.get('base_folder', 'unknown')
            print(f'SUCCESS: Institution: {institution}')
            return 0
        except Exception as e:
            print(f'ERROR: Credentials file invalid: {e}')
            return 1
    else:
        print('ERROR: Credentials file not found!')
        return 1

if __name__ == '__main__':
    sys.exit(main())