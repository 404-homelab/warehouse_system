#!/usr/bin/env python3
"""
AUTO-UPDATE SERVER
==================
Serves updates to deployed Warehouse System instances.

Supports two channels:
- stable: Production-ready releases
- testing: Beta releases for testing

Directory structure:
  updates/
    stable/
      1.0.0/
        warehouse_v1.0.0.zip
        manifest.json
      1.0.1/
        warehouse_v1.0.1.zip
        manifest.json
    testing/
      1.1.0-beta/
        warehouse_v1.1.0-beta.zip
        manifest.json

Usage:
  python3 update_server.py
  
  Then access:
  http://localhost:8080
"""

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import os
import json
import hashlib
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configuration
UPDATE_DIR = 'updates'
CHANNELS = ['stable', 'testing']

# Ensure directories exist
for channel in CHANNELS:
    os.makedirs(f"{UPDATE_DIR}/{channel}", exist_ok=True)


def get_file_checksum(filepath):
    """Calculate SHA256 checksum of file"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_latest_version(channel):
    """Get latest version info for a channel"""
    channel_dir = f"{UPDATE_DIR}/{channel}"
    
    if not os.path.exists(channel_dir):
        return None
    
    # Find all version directories
    versions = []
    for item in os.listdir(channel_dir):
        version_dir = os.path.join(channel_dir, item)
        if os.path.isdir(version_dir):
            manifest_path = os.path.join(version_dir, 'manifest.json')
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    manifest['version_dir'] = version_dir
                    versions.append(manifest)
    
    if not versions:
        return None
    
    # Sort by version (semantic versioning)
    def version_key(v):
        # Handle beta/testing versions
        version = v['version'].replace('-beta', '').replace('-alpha', '')
        return tuple(map(int, version.split('.')))
    
    versions.sort(key=version_key, reverse=True)
    
    return versions[0]


@app.route('/')
def index():
    """Server info page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Warehouse Update Server</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #0066cc; }
            .channel { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .version { font-weight: bold; color: #006600; }
            pre { background: #f0f0f0; padding: 10px; border-radius: 3px; overflow-x: auto; }
            .info { background: #e6f3ff; padding: 10px; border-left: 4px solid #0066cc; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>🔄 Warehouse Auto-Update Server</h1>
        <p>Serving updates for deployed Warehouse System instances.</p>
        
        <h2>Available Channels:</h2>
    """
    
    for channel in CHANNELS:
        version_info = get_latest_version(channel)
        html += f'<div class="channel">'
        html += f'<h3>📦 {channel.upper()}</h3>'
        
        if version_info:
            html += f'<p>Latest version: <span class="version">{version_info["version"]}</span></p>'
            html += f'<p>Released: {version_info.get("release_date", "Unknown")}</p>'
            if 'changelog' in version_info:
                html += f'<p>Changelog:</p><pre>{version_info["changelog"]}</pre>'
        else:
            html += '<p>No versions available</p>'
        
        html += '</div>'
    
    html += """
        <div class="info">
        <h2>📡 API Endpoints:</h2>
        <ul>
            <li><code>GET /api/version/{channel}</code> - Get latest version info</li>
            <li><code>GET /api/download/{channel}/{version}</code> - Download update package</li>
            <li><code>GET /api/list/{channel}</code> - List all versions</li>
        </ul>
        </div>
        
        <div class="info">
        <h2>🔧 Client Configuration:</h2>
        <p>On the deployed server, configure the update client:</p>
        <pre>python3 update_client.py --server http://YOUR_IP:8080 --channel stable</pre>
        </div>
    </body>
    </html>
    """
    
    return html


@app.route('/api/version/<channel>')
def get_version(channel):
    """Get latest version info for channel"""
    if channel not in CHANNELS:
        return jsonify({'error': 'Invalid channel'}), 400
    
    version_info = get_latest_version(channel)
    
    if not version_info:
        return jsonify({'error': 'No versions available'}), 404
    
    # Add download URL
    version_info['download_url'] = f"{request.url_root}api/download/{channel}/{version_info['version']}"
    
    # Calculate checksum if not in manifest
    if 'checksum' not in version_info:
        zip_file = os.path.join(version_info['version_dir'], version_info['filename'])
        if os.path.exists(zip_file):
            version_info['checksum'] = get_file_checksum(zip_file)
    
    # Remove internal fields
    version_info.pop('version_dir', None)
    
    return jsonify(version_info)


@app.route('/api/download/<channel>/<version>')
def download_update(channel, version):
    """Download update package"""
    if channel not in CHANNELS:
        return jsonify({'error': 'Invalid channel'}), 400
    
    version_dir = f"{UPDATE_DIR}/{channel}/{version}"
    
    if not os.path.exists(version_dir):
        return jsonify({'error': 'Version not found'}), 404
    
    manifest_path = os.path.join(version_dir, 'manifest.json')
    
    if not os.path.exists(manifest_path):
        return jsonify({'error': 'Manifest not found'}), 404
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    zip_file = os.path.join(version_dir, manifest['filename'])
    
    if not os.path.exists(zip_file):
        return jsonify({'error': 'Update file not found'}), 404
    
    return send_file(zip_file, as_attachment=True, download_name=manifest['filename'])


@app.route('/api/list/<channel>')
def list_versions(channel):
    """List all available versions for channel"""
    if channel not in CHANNELS:
        return jsonify({'error': 'Invalid channel'}), 400
    
    channel_dir = f"{UPDATE_DIR}/{channel}"
    
    if not os.path.exists(channel_dir):
        return jsonify({'versions': []})
    
    versions = []
    
    for item in os.listdir(channel_dir):
        version_dir = os.path.join(channel_dir, item)
        if os.path.isdir(version_dir):
            manifest_path = os.path.join(version_dir, 'manifest.json')
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    versions.append({
                        'version': manifest['version'],
                        'release_date': manifest.get('release_date'),
                        'size': os.path.getsize(os.path.join(version_dir, manifest['filename']))
                    })
    
    return jsonify({'channel': channel, 'versions': versions})


@app.route('/api/stats')
def stats():
    """Server statistics"""
    stats_data = {
        'channels': {}
    }
    
    for channel in CHANNELS:
        version_info = get_latest_version(channel)
        stats_data['channels'][channel] = {
            'latest_version': version_info['version'] if version_info else None,
            'total_versions': len(os.listdir(f"{UPDATE_DIR}/{channel}")) if os.path.exists(f"{UPDATE_DIR}/{channel}") else 0
        }
    
    return jsonify(stats_data)


if __name__ == '__main__':
    print("=" * 60)
    print("🔄 WAREHOUSE UPDATE SERVER")
    print("=" * 60)
    print()
    print("Channels:")
    for channel in CHANNELS:
        version_info = get_latest_version(channel)
        if version_info:
            print(f"  📦 {channel}: v{version_info['version']}")
        else:
            print(f"  📦 {channel}: No versions")
    print()
    print("Server starting on http://0.0.0.0:8080")
    print("Ctrl+C to stop")
    print()
    
    app.run(host='0.0.0.0', port=8080, debug=True)
