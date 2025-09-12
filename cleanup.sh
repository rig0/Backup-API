#!/bin/bash

# Root backups directory (change this if needed)
BACKUP_ROOT=$1

# Function to clean up backups in a given directory
cleanup_backups() {
    local dir="$1"

    if [ -d "$dir" ]; then
        echo "Processing: $dir"

        # Find all .tar.gz files, sort by modification time (newest first),
        # skip the first 7, and delete the rest
        find "$dir" -maxdepth 1 -type f -name "*.tar.gz" \
            -printf "%T@ %p\n" | sort -nr | awk 'NR>7 {print $2}' | while read -r oldfile; do
                echo "Deleting old backup: $oldfile"
                rm -f "$oldfile"
            done
    else
        echo "Directory not found: $dir"
    fi
}

# --- Gitea backups (directly inside Backups/Gitea) ---
cleanup_backups "$BACKUP_ROOT/Gitea"

# --- Dockge backups (inside Backups/Dockge/*/) ---
for server_dir in "$BACKUP_ROOT/Dockge"/*/; do
    [ -d "$server_dir" ] || continue
    cleanup_backups "$server_dir"
done
