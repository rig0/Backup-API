from flask import Flask, request, jsonify
import subprocess
import os, glob, datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Get the token from the environment variable
AUTH_TOKEN = os.getenv('AUTH_TOKEN')

# Authorization decorator
def token_required(f):
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header.split(" ")[1] != AUTH_TOKEN:
            return jsonify({'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def add_host_to_known_hosts(remote_host):
    """Use ssh-keyscan to add the host key to known_hosts"""
    try:
        result = subprocess.run(['ssh-keyscan', remote_host], capture_output=True, text=True)
        if result.returncode == 0:
            known_hosts_path = os.path.expanduser('~/.ssh/known_hosts')
            with open(known_hosts_path, 'a') as f:
                f.write(result.stdout)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error adding host to known_hosts: {e}")
        return False

def cleanup_backups(root_dir, keep=7):
    """
    Keeps only the most recent N (.tar.gz) backups inside all subfolders of root_dir.
    """
    if not os.path.isdir(root_dir):
        print(f"[cleanup] Root dir {root_dir} does not exist")
        return

    # Walk all subdirectories
    for dirpath, _, _ in os.walk(root_dir):
        _cleanup_dir(dirpath, keep)

def _cleanup_dir(dir_path, keep):
    """Helper: cleanup a single directory recursively, keep newest by filename, never delete today"""
    if not os.path.isdir(dir_path):
        return

    # Find all .tar.gz files
    files = glob.glob(os.path.join(dir_path, "*.tar.gz"))
    if not files:
        return

    today = datetime.date.today()
    # Filter out today's files
    files_to_consider = [f for f in files if datetime.date.fromtimestamp(os.path.getmtime(f)) < today]

    if len(files_to_consider) <= keep:
        print(f"[cleanup] Nothing to delete in {dir_path}")
        return

    # Sort by filename (assuming backup filenames include date, newest first)
    files_to_consider.sort(reverse=True)

    # Delete older backups beyond 'keep'
    old_files = files_to_consider[keep:]
    for f in old_files:
        try:
            os.remove(f)
            print(f"[cleanup] Deleted {f}")
        except Exception as e:
            print(f"[cleanup] Failed to delete {f}: {e}")

def run_rsync(remote_user, remote_host, remote_folder, local_folder):
    rsync_command = ['rsync', '-avz', f'{remote_user}@{remote_host}:{remote_folder}', local_folder]
    try:
        result = subprocess.run(rsync_command, capture_output=True, text=True)
        if result.returncode == 0:
            # Change permissions
            subprocess.run(['chmod', '-R', '770', local_folder], capture_output=True, text=True)

            # Run cleanup
            BACKUP_DIR = os.getenv('BACKUP_DIR')
            if BACKUP_DIR:
                cleanup_backups(BACKUP_DIR, keep=7)

            return jsonify({'message': 'Backup completed successfully', 'output': result.stdout}), 200
        else:
            return jsonify({'message': 'Backup failed', 'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

@app.route('/backup', methods=['POST'])
@token_required
def backup():
    data = request.get_json()
    remote_user = data.get('remote_user')
    remote_host = data.get('remote_host')
    remote_folder = data.get('remote_folder')
    local_folder = data.get('local_folder')

    if not add_host_to_known_hosts(remote_host):
        return jsonify({'message': 'Failed to add host to known_hosts'}), 500

    return run_rsync(remote_user, remote_host, remote_folder, local_folder)

@app.route('/gitea', methods=['POST'])
@token_required
def gitea():
    data = request.get_json()
    backup_folder = data.get('backup_folder')

    GITEA_HOST = os.getenv('GITEA_HOST')
    GITEA_USER = os.getenv('GITEA_USER')
    GITEA_LOCAL_DIR = os.getenv('GITEA_LOCAL_DIR')

    if not add_host_to_known_hosts(GITEA_HOST):
        return jsonify({'message': 'Failed to add host to known_hosts'}), 500

    return run_rsync(GITEA_USER, GITEA_HOST, backup_folder, GITEA_LOCAL_DIR)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7792)
