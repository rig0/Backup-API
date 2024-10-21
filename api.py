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
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header.split(" ")[1] != AUTH_TOKEN:
            return jsonify({'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/backup', methods=['POST'])
@token_required
def backup():
    # Extract details from the request
    data = request.get_json()
    remote_user = data.get('remote_user')
    remote_host = data.get('remote_host')
    remote_folder = data.get('remote_folder')
    local_folder = data.get('local_folder')

    # Construct the rsync command
    rsync_command = [
        'rsync',
        '-avz',  # Options: archive mode, verbose, compress
        f'{remote_user}@{remote_host}:{remote_folder}',
        local_folder
    ]

    try:
        # Run the rsync command
        result = subprocess.run(rsync_command, capture_output=True, text=True)
        
        # Check if rsync was successful
        if result.returncode == 0:
            return jsonify({'message': 'Backup completed successfully', 'output': result.stdout}), 200
        else:
            return jsonify({'message': 'Backup failed', 'error': result.stderr}), 500

    except Exception as e:
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7792)
