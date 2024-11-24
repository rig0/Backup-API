from flask import Flask, request, jsonify
import subprocess
import os
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

            # run cleanup script
            #sub_folder = os.path.basename(remote_folder)
            #full_path = os.path.join(local_folder, sub_folder)
            #subprocess.run(['./cleanup.sh', full_path], capture_output=True, text=True)

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
