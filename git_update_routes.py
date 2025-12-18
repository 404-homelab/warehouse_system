# Add these routes to app.py (around line 1500)

@app.route('/api/git/status', methods=['GET'])
def git_status():
    """Get git repository status"""
    try:
        import subprocess
        
        # Check if git repo
        if not os.path.exists('.git'):
            return jsonify({
                'success': False,
                'error': 'Not a git repository',
                'is_git_repo': False
            })
        
        # Get current version/commit
        current = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).strip()
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()
        
        # Get remote URL
        try:
            remote = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], text=True).strip()
        except:
            remote = 'Unknown'
        
        # Fetch updates (don't pull yet)
        subprocess.run(['git', 'fetch', 'origin'], capture_output=True, timeout=10)
        
        # Check if updates available
        local = subprocess.check_output(['git', 'rev-parse', '@'], text=True).strip()
        remote_commit = subprocess.check_output(['git', 'rev-parse', '@{u}'], text=True).strip()
        
        updates_available = local != remote_commit
        
        # Get commit log if updates available
        changelog = []
        if updates_available:
            log_output = subprocess.check_output(
                ['git', 'log', '--oneline', '--decorate', 'HEAD..@{u}'],
                text=True
            )
            changelog = log_output.strip().split('\n') if log_output.strip() else []
        
        # Get last update time
        last_commit_time = subprocess.check_output(
            ['git', 'log', '-1', '--format=%cd', '--date=iso'],
            text=True
        ).strip()
        
        return jsonify({
            'success': True,
            'is_git_repo': True,
            'current_commit': current,
            'branch': branch,
            'remote_url': remote,
            'updates_available': updates_available,
            'commits_behind': len(changelog),
            'changelog': changelog,
            'last_update': last_commit_time
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Git command timeout'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/update', methods=['POST'])
def git_update():
    """Perform git pull update"""
    try:
        import subprocess
        import sys
        
        # Check if git repo
        if not os.path.exists('.git'):
            return jsonify({'success': False, 'error': 'Not a git repository'})
        
        # Backup database
        import shutil
        from datetime import datetime
        backup_name = f"warehouse.db.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy('warehouse.db', backup_name)
        
        # Pull updates
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': f'Git pull failed: {result.stderr}'
            })
        
        # Update dependencies
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '--break-system-packages'],
            capture_output=True,
            timeout=60
        )
        
        # Log action
        db.log_action('GIT_UPDATE', None, 'Admin', 'Updated from git')
        
        return jsonify({
            'success': True,
            'message': 'Update complete. Restart required.',
            'output': result.stdout,
            'backup': backup_name
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Update timeout'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/restart', methods=['POST'])
def git_restart():
    """Restart the application"""
    try:
        import subprocess
        import os
        import signal
        
        # Log action
        db.log_action('APP_RESTART', None, 'Admin', 'Restarting application')
        
        # Try restart script
        if os.path.exists('restart.sh'):
            subprocess.Popen(['bash', 'restart.sh'])
        else:
            # Kill current process - systemd will restart
            os.kill(os.getpid(), signal.SIGTERM)
        
        return jsonify({'success': True, 'message': 'Restarting...'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/git/auto-update', methods=['POST'])
def git_auto_update_config():
    """Configure auto-update settings"""
    try:
        data = request.json
        
        # Load or create config
        config = {}
        config_file = 'git_update_config.json'
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        
        # Update settings
        config['auto_update'] = data.get('auto_update', False)
        config['check_interval'] = data.get('check_interval', 86400)  # Daily
        config['auto_restart'] = data.get('auto_restart', True)
        
        # Save
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Setup/remove cron job based on auto_update
        if data.get('auto_update'):
            setup_auto_update_cron()
        else:
            remove_auto_update_cron()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def setup_auto_update_cron():
    """Setup cron job for auto updates"""
    try:
        import subprocess
        
        # Check if cron script exists
        if not os.path.exists('auto-update-cron.sh'):
            return
        
        # Copy to cron.daily
        subprocess.run([
            'sudo', 'cp', 
            'auto-update-cron.sh', 
            '/etc/cron.daily/warehouse-update'
        ], check=True)
        
        subprocess.run([
            'sudo', 'chmod', '+x',
            '/etc/cron.daily/warehouse-update'
        ], check=True)
        
    except Exception as e:
        print(f"Failed to setup cron: {e}")


def remove_auto_update_cron():
    """Remove cron job"""
    try:
        import subprocess
        subprocess.run(['sudo', 'rm', '-f', '/etc/cron.daily/warehouse-update'])
    except:
        pass
