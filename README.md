# Backup-API

An API that fetches remote files to backup. Intended to run on a NAS to fetch remote backups.

Create an .env file and store the AUTH_TOKEN there.

Example curl:

curl --location 'http://SERVER_IP:7792/backup' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer AUTH_TOKEN' \
--data '{
    "remote_user": "user",
    "remote_host": "remote ip",
    "remote_folder": "/remote/folder/",
    "local_folder": "/local/folder/"
}'