#!/usr/bin/env python3
"""
AUTO-UPDATE CLIENT
==================
Checks for updates from update server and installs them automatically.

Supports two channels:
- stable: Production-ready releases
- testing: Beta releases for testing

Configuration in update_config.json
"""

import os
import sys
import json
import requests
import shutil
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path

# Configuration
CONFIG_FILE = 'update_config.json'
VERSION_FILE = 'VERSION'
BACKUP_DIR = 'backups/updates'

class UpdateClient:
    def __init__(self):
        self.load_config()
        self.current_version = self.get_current_version()
        
    def load_config(self):
        """Load update configuration"""
        if not os.path.exists(CONFIG_FILE):
            # Create default config
            self.config = {
                'update_server': 'http://your-computer.local:8080',
                'channel': 'stable',  # or 'testing'
                'auto_update': True,
                'check_interval': 3600,  # seconds
                'backup_before_update': True
            }
            self.save_config()
        else:
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
    
    def save_config(self):
        """Save configuration"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"📝 Configuration saved to {CONFIG_FILE}")
    
    def get_current_version(self):
        """Get current installed version"""
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r') as f:
                return f.read().strip()
        return '0.0.0'
    
    def check_for_updates(self):
        """Check if updates are available"""
        try:
            url = f"{self.config['update_server']}/api/version/{self.config['channel']}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"❌ Failed to check for updates: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to update server: {e}")
            return None
    
    def compare_versions(self, v1, v2):
        """Compare two version strings (e.g., '1.2.3' vs '1.2.4')"""
        def version_tuple(v):
            # Remove beta/alpha suffixes for comparison
            clean_version = v.replace('-beta', '').replace('-alpha', '').replace('-rc', '')
            try:
                return tuple(map(int, clean_version.split('.')))
            except ValueError:
                # Fallback if version format is unexpected
                return (0, 0, 0)
        
        return version_tuple(v2) > version_tuple(v1)
    
    def download_update(self, version_info):
        """Download update package"""
        try:
            url = version_info['download_url']
            filename = f"update_{version_info['version']}.zip"
            
            print(f"📥 Downloading update {version_info['version']}...")
            
            response = requests.get(url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filename, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            progress = (downloaded / total_size) * 100
                            print(f"\r  Progress: {progress:.1f}%", end='')
            
            print("\n✅ Download complete")
            
            # Verify checksum
            if 'checksum' in version_info:
                if self.verify_checksum(filename, version_info['checksum']):
                    print("✅ Checksum verified")
                    return filename
                else:
                    print("❌ Checksum mismatch! Update may be corrupted.")
                    os.remove(filename)
                    return None
            
            return filename
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def verify_checksum(self, filename, expected_checksum):
        """Verify file checksum (SHA256)"""
        sha256 = hashlib.sha256()
        with open(filename, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest() == expected_checksum
    
    def create_backup(self):
        """Create backup before update"""
        if not self.config.get('backup_before_update', True):
            return None
        
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_v{self.current_version}_{timestamp}.zip"
            backup_path = os.path.join(BACKUP_DIR, backup_name)
            
            print(f"📦 Creating backup...")
            
            # Files/folders to backup
            items_to_backup = [
                'warehouse.db',
                'app.py',
                'database.py',
                'barcode_generator.py',
                'templates/',
                'static/',
                'update_config.json',
                'VERSION'
            ]
            
            # Create zip backup
            shutil.make_archive(backup_path.replace('.zip', ''), 'zip', 
                              '.', ','.join(items_to_backup))
            
            print(f"✅ Backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"⚠️  Backup failed: {e}")
            return None
    
    def install_update(self, update_file):
        """Install downloaded update"""
        try:
            print(f"📦 Installing update...")
            
            # Extract update
            import zipfile
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                # List files that will be updated
                print("Files to be updated:")
                for name in zip_ref.namelist():
                    print(f"  - {name}")
                
                # Extract all
                zip_ref.extractall('.')
            
            # Update version file
            if os.path.exists(VERSION_FILE):
                with open(VERSION_FILE, 'r') as f:
                    new_version = f.read().strip()
                    print(f"✅ Updated to version {new_version}")
            
            # Clean up
            os.remove(update_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            return False
    
    def rollback(self, backup_path):
        """Rollback to backup"""
        try:
            print(f"🔄 Rolling back to backup...")
            
            import zipfile
            with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                zip_ref.extractall('.')
            
            print(f"✅ Rollback complete")
            return True
            
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False
    
    def restart_service(self):
        """Restart the warehouse service"""
        print("🔄 Restarting service...")
        
        # Method 0: Use restart.sh if it exists
        if os.path.exists('restart.sh'):
            try:
                print("📌 Using restart.sh...")
                # Make sure it's executable
                os.chmod('restart.sh', 0o755)
                result = subprocess.run(['./restart.sh'], capture_output=True, timeout=10, text=True)
                if result.returncode == 0:
                    print(result.stdout)
                    print("✅ Service restarted via restart.sh")
                    return
                else:
                    print(f"⚠️  restart.sh failed: {result.stderr}")
            except Exception as e:
                print(f"⚠️  restart.sh failed: {e}")
        
        # Try different restart methods
        restart_methods = [
            # Method 1: Systemd service
            (['sudo', 'systemctl', 'restart', 'warehouse'], 'Systemd service'),
            # Method 2: Supervisord
            (['sudo', 'supervisorctl', 'restart', 'warehouse'], 'Supervisord'),
            # Method 3: Kill current process
            (['pkill', '-f', 'app.py'], 'Kill app.py'),
        ]
        
        restarted = False
        
        for cmd, method in restart_methods:
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ Restarted via {method}")
                    restarted = True
                    break
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                continue
        
        if not restarted:
            print("\n⚠️  Automatic restart failed. Please restart manually:")
            print("   Option 1 (script):  ./restart.sh")
            print("   Option 2 (systemd): sudo systemctl restart warehouse")
            print("   Option 3 (manual):  pkill -f app.py && python3 app.py &")


    
    def update(self):
        """Main update process"""
        print("=" * 60)
        print("🔄 WAREHOUSE AUTO-UPDATE")
        print("=" * 60)
        print(f"Current version: {self.current_version}")
        print(f"Channel: {self.config['channel']}")
        print(f"Update server: {self.config['update_server']}")
        print()
        
        # Check for updates
        print("🔍 Checking for updates...")
        version_info = self.check_for_updates()
        
        if not version_info:
            print("❌ Could not check for updates")
            return False
        
        available_version = version_info.get('version')
        
        if not available_version:
            print("❌ Invalid response from update server")
            return False
        
        print(f"Latest version: {available_version}")
        
        # Compare versions
        if not self.compare_versions(self.current_version, available_version):
            print("✅ Already up to date!")
            return True
        
        print(f"\n🎉 New version available: {available_version}")
        
        # Show changelog
        if 'changelog' in version_info:
            print("\n📝 Changelog:")
            for line in version_info['changelog'].split('\n'):
                print(f"  {line}")
        
        # Confirm update
        if not self.config.get('auto_update', False):
            response = input("\n❓ Install update? (y/N): ")
            if response.lower() != 'y':
                print("❌ Update cancelled")
                return False
        
        print("\n🚀 Starting update process...")
        
        # Create backup
        backup_path = self.create_backup()
        
        # Download update
        update_file = self.download_update(version_info)
        
        if not update_file:
            print("❌ Update failed: Could not download")
            return False
        
        # Install update
        if self.install_update(update_file):
            print("\n✅ Update installed successfully!")
            print(f"Version: {self.current_version} → {available_version}")
            
            # Restart service
            if self.config.get('auto_restart', True):
                self.restart_service()
            else:
                print("\n⚠️  Auto-restart disabled. Please restart manually:")
                if os.path.exists('restart.sh'):
                    print("   ./restart.sh")
                else:
                    print("   python3 app.py")
            
            return True
        else:
            print("\n❌ Update failed during installation")
            
            # Rollback
            if backup_path and os.path.exists(backup_path):
                response = input("❓ Rollback to backup? (Y/n): ")
                if response.lower() != 'n':
                    self.rollback(backup_path)
            
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Warehouse Auto-Update Client')
    parser.add_argument('--check', action='store_true', help='Check for updates only')
    parser.add_argument('--channel', choices=['stable', 'testing'], help='Set update channel')
    parser.add_argument('--server', help='Set update server URL')
    parser.add_argument('--auto', action='store_true', help='Enable auto-update')
    parser.add_argument('--manual', action='store_true', help='Disable auto-update')
    
    args = parser.parse_args()
    
    client = UpdateClient()
    
    # Update configuration if provided
    if args.channel:
        client.config['channel'] = args.channel
        client.save_config()
        print(f"✅ Channel set to: {args.channel}")
    
    if args.server:
        client.config['update_server'] = args.server
        client.save_config()
        print(f"✅ Update server set to: {args.server}")
    
    if args.auto:
        client.config['auto_update'] = True
        client.save_config()
        print("✅ Auto-update enabled")
    
    if args.manual:
        client.config['auto_update'] = False
        client.save_config()
        print("✅ Auto-update disabled (manual updates only)")
    
    # Check or update
    if args.check:
        print("🔍 Checking for updates...")
        version_info = client.check_for_updates()
        if version_info:
            print(f"Current: {client.current_version}")
            print(f"Latest: {version_info.get('version')}")
            
            if client.compare_versions(client.current_version, version_info.get('version')):
                print("🎉 Update available!")
            else:
                print("✅ Up to date!")
    else:
        client.update()


if __name__ == '__main__':
    main()
