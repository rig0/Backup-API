# Backup-API
An API that fetches remote files and backups to store locally. Intended to run on a NAS or Backup Server. Tested on Debian 12

### Prerequisites
```bash
sudo apt install python3-full python3-env python3-pip rsync git
```
### Clone
```bash
git clone https://rigslab.com/Rambo/Backup-API.git
```

### Use `start-api.sh` to start api in virtual environment
```bash
cd Backup-API
```
```bash
chmod +x ./start-api.sh && ./start-api.sh
```

### Use `update.sh` to fetch latest version
```bash
cd Backup-API
```
```bash
chmod +x ./update.sh && ./update.sh
```

## Example .env

Create a .env file in the same directory as the api. Then [generate](https://it-tools.tech/token-generator) and store the AUTH_TOKEN there.

```bash
AUTH_TOKEN=Your-Generated-API-Token-Here
```

## Example API call using curl

```bash
curl --location 'http://SERVER_IP:7792/backup' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer AUTH_TOKEN' \
--data '{
    "remote_user": "user",
    "remote_host": "remote ip",
    "remote_folder": "/remote/folder/",
    "local_folder": "/local/folder/"
}'
```

## Using the  `/gitea` entry point

This entry point is for fetching a gitea backup from a public server.
For this entry we need to hande a few variables locally.

### Edit the .nvm file with the GITEA_ variables

```bash
AUTH_TOKEN=API-Token
# gitea specific options
GITEA_HOST=Gitea-Server-IP
GITEA_USER=Gitea-Server-User
GITEA_LOCAL_DIR=/nas/backup/directory
```
### Example API call of for gitea backup

```bash
curl --location 'http://SERVER_IP:7792/gitea' \
--header "Content-Type: application/json" \
--header "Authorization: Bearer $AUTH_TOKEN" \
--data "{
    \"backup_folder\": \"$BACKUP_DIR\"
}"
```

## System service
### Create a system service
```bash
sudo nano /etc/systemd/system/backup-api.service
```

### Paste the following & change accordingly
```bash
[Unit]
Description=Backup API
After=network.target

[Service]
User=user
Group=user
WorkingDirectory=/home/user/backup-api
ExecStart=/home/user/backup-api/start-api.sh
Restart=always

Environment="PATH=/home/user/backup-api/venv/bin:/usr/bin"

[Install]
WantedBy=multi-user.target
```

### Reload daemon
```bash
sudo systemctl daemon-reload
```

### Start service
```bash
sudo systemctl start backup-api
```

### Enable on boot
```bash
sudo systemctl enable backup-api
```