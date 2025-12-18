#!/usr/bin/env python3
"""Test if translations load correctly"""

import json
import os

print("Testing translations...")
print(f"Current directory: {os.getcwd()}")
print(f"Files in static/: {os.listdir('static') if os.path.exists('static') else 'static/ not found'}")

if os.path.exists('static/translations.json'):
    print("✓ translations.json exists")
    
    with open('static/translations.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ Loaded {len(data)} languages: {', '.join(data.keys())}")
    
    # Check structure
    if 'sv' in data:
        print(f"✓ Swedish has sections: {', '.join(data['sv'].keys())}")
        if 'nav' in data['sv']:
            print(f"✓ nav has keys: {', '.join(data['sv']['nav'].keys())}")
    else:
        print("✗ Swedish (sv) not found!")
else:
    print("✗ static/translations.json NOT FOUND!")
    print("\nYou need to copy translations.json to static/ folder")
    print("Run: cp /path/to/warehouse_system/static/translations.json static/")
