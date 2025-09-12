from flask import Flask, request, jsonify
import subprocess
import os, glob
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
        # Use ssh-keyscan to retrieve the SSH key from the remote host
        result = subprocess.run(
            ['ssh-keyscan', remote_host],
            capture_output=True,
            text=True
        )

        # Check if the command was successful
        if result.returncode == 0:
            # Append the key to the known_hosts file
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
    Keeps only the most recent N (.tar.gz) backups
    inside Gitea and Dockge structure.
    """
    # --- Gitea backups ---
    gitea_dir = os.path.join(root_dir, "Gitea")
    _cleanup_dir(gitea_dir, keep)

    # --- Dockge backups (one per server) ---
    dockge_root = os.path.join(root_dir, "Dockge")
    if os.path.isdir(dockge_root):
        for server_dir in os.listdir(dockge_root):
            full_path = os.path.join(dockge_root, server_dir)
            if os.path.isdir(full_path):
                # apply cleanup to this folder
                _cleanup_dir(full_path, keep)

                # apply cleanup to any subfolders (optional)
                for subfolder in os.listdir(full_path):
                    subfolder_path = os.path.join(full_path, subfolder)
                    if os.path.isdir(subfolder_path):
                        _cleanup_dir(subfolder_path, keep)



def _cleanup_dir(dir_path, keep):
    # Only look at .tar.gz files directly inside this folder
    files = glob.glob(os.path.join(dir_path, "*.tar.gz"))
    if len(files) <= keep:
        return

    # Sort by filename (assuming filenames include date)
    files.sort(reverse=True)
    old_files = files[keep:]

    for f in old_files:
        try:
            os.remove(f)
            print(f"Deleted {f}")
        except Exception as e:
            print(f"Failed to delete {f}: {e}")



def run_rsync(remote_user, remote_host, remote_folder, local_folder):
    # Construct the rsync command
    rsync_command = [
        'rsync',
        '-avz',
        #'--no-g',
        f'{remote_user}@{remote_host}:{remote_folder}',
        local_folder
    ]
    try:
        # Run the rsync command
        result = subprocess.run(rsync_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            # change permissions to allow group rwx
            subprocess.run(['chmod', '-R', '770', local_folder], capture_output=True, text=True)

            # run cleanup
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

    # Add the remote host's key to known_hosts
    if not add_host_to_known_hosts(remote_host):
        return jsonify({'message': 'Failed to add host to known_hosts'}), 500

    rsync_result = run_rsync(remote_user, remote_host, remote_folder, local_folder)
    return rsync_result
    

@app.route('/gitea', methods=['POST'])
@token_required
def gitea():
    data = request.get_json()
    backup_folder = data.get('backup_folder')

    GITEA_HOST = os.getenv('GITEA_HOST')
    GITEA_USER = os.getenv('GITEA_USER')
    GITEA_LOCAL_DIR = os.getenv('GITEA_LOCAL_DIR')

    # Add the remote host's key to known_hosts
    if not add_host_to_known_hosts(GITEA_HOST):
        return jsonify({'message': 'Failed to add host to known_hosts'}), 500

    rsync_result = run_rsync(GITEA_USER, GITEA_HOST, backup_folder, GITEA_LOCAL_DIR)
    return rsync_result

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7792)
