#!/bin/bash
# Purpose: Runs a Python script in the background using nohup and monitors the nohup.out log file,
#          truncating it when it exceeds a specified size to prevent it from growing too large.
# Usage: Save this script as manage_nohup.sh, make it executable with 'chmod +x manage_nohup.sh',
#        then run with 'nohup ./manage_nohup.sh &'. Ensure 'stonybrook_scraper.py'
#        is in the same directory. Adjust MAXSIZE (in bytes) to change the log size limit.
LOGFILE="nohup.out"
MAXSIZE=$((100 * 1024 * 1024))  # 100MB in bytes

# Run the Python command with nohup
nohup python stonybrook_scraper.py &

# Monitor log size in the background
while true; do
    if [ -f "$LOGFILE" ]; then
        # More robust way to get file size that works across different systems
        if command -v stat >/dev/null 2>&1; then
            # Try different stat formats and use the first one that returns just a number
            SIZE=$(stat -c%s "$LOGFILE" 2>/dev/null || stat -f%z "$LOGFILE" 2>/dev/null || wc -c < "$LOGFILE" 2>/dev/null)
            # Remove any whitespace and ensure we have a number
            SIZE=$(echo "$SIZE" | tr -d ' \t\n\r')
            # Check if SIZE is actually a number
            if [[ "$SIZE" =~ ^[0-9]+$ ]]; then
                if [ "$SIZE" -gt "$MAXSIZE" ]; then
                    echo "$(date): Log file size ($SIZE bytes) exceeds limit ($MAXSIZE bytes). Truncating..."
                    > "$LOGFILE"  # Truncate to zero
                fi
            else
                echo "$(date): Warning: Could not determine file size properly. Skipping size check."
            fi
        else
            # Fallback method using wc if stat is not available
            SIZE=$(wc -c < "$LOGFILE" 2>/dev/null | tr -d ' \t\n\r')
            if [[ "$SIZE" =~ ^[0-9]+$ ]] && [ "$SIZE" -gt "$MAXSIZE" ]; then
                echo "$(date): Log file size ($SIZE bytes) exceeds limit ($MAXSIZE bytes). Truncating..."
                > "$LOGFILE"  # Truncate to zero
            fi
        fi
    fi
    sleep 300  # Check every 5 minutes
done