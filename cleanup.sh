#!/bin/bash

# Directory containing the backup files
BACKUP_DIR=$1

# Change to the backup directory
cd "$BACKUP_DIR" || { echo "Backup directory not found!"; exit 1; }

# List files sorted by modification time (newest first), excluding directories
BACKUP_FILES=($(ls -tp | grep -v /))

# Check if there are more than 7 files
if [ "${#BACKUP_FILES[@]}" -gt 7 ]; then
    # Get files to delete (all except the 7 most recent)
    FILES_TO_DELETE=("${BACKUP_FILES[@]:7}")

    # Remove the old files
    for file in "${FILES_TO_DELETE[@]}"; do
        echo "Removing: $file"
        rm -f "$file"
    done
else
    echo "No files to delete. Only ${#BACKUP_FILES[@]} backups found."
fi
