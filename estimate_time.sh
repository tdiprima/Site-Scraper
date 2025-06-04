#!/bin/bash

QUEUE_FILE="queue.txt"
PAUSE=1.5
PROCESS=1

if [ ! -f "$QUEUE_FILE" ]; then
  echo "File $QUEUE_FILE not found!"
  exit 1
fi

LINES=$(wc -l < "$QUEUE_FILE")
if [ "$LINES" -eq 0 ]; then
  echo "No URLs left in $QUEUE_FILE. All done!"
  exit 0
fi

# Total seconds as a float, then convert to int for bash math
PER_ITEM=$(echo "$PAUSE + $PROCESS" | bc)
TOTAL_SEC=$(echo "$LINES * $PER_ITEM" | bc)
TOTAL_SEC_INT=$(printf "%.0f" "$TOTAL_SEC")  # round to nearest integer

DAYS=$((TOTAL_SEC_INT / 86400))
HOURS=$(( (TOTAL_SEC_INT % 86400) / 3600 ))
MINUTES=$(( (TOTAL_SEC_INT % 3600) / 60 ))
SECONDS=$((TOTAL_SEC_INT % 60))

echo "🕒 $LINES URLs left in $QUEUE_FILE"
echo "⏳ Estimated time to finish: ${DAYS}d ${HOURS}h ${MINUTES}m ${SECONDS}s"
