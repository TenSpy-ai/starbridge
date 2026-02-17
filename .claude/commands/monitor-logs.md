# /monitor-logs Command

Show recent logs from the Pipeline Monitor server.

## Usage

When the user types `/monitor-logs`:

1. Check if log file exists
2. Show the last 50 lines from the log file
3. Indicate if server is currently running

## Implementation

Execute the following:

```bash
echo "=== Pipeline Monitor Server Logs ==="
echo ""

LOG_FILE="/tmp/pipeline-monitor.log"
DB_FILE="/Users/oliviagao/project/starbridge/data/pipeline.db"

# Check server status
echo "Server Status:"
ERRORS=$(grep -ci "error" "$LOG_FILE" 2>/dev/null || echo "0")

if lsof -i :8111 > /dev/null 2>&1; then
  echo "  Pipeline Monitor (8111): RUNNING ($ERRORS errors in log)"
else
  echo "  Pipeline Monitor (8111): STOPPED ($ERRORS errors in log)"
fi

# Show DB info
echo ""
echo "Pipeline Database:"
if [ -f "$DB_FILE" ]; then
  RUNS=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM runs;" 2>/dev/null || echo "?")
  LATEST=$(sqlite3 "$DB_FILE" "SELECT target_company || ' (' || status || ')' FROM runs ORDER BY id DESC LIMIT 1;" 2>/dev/null || echo "?")
  echo "  $DB_FILE"
  echo "  Total runs: $RUNS | Latest: $LATEST"
else
  echo "  No database found (will be created on first run)"
fi

echo ""
echo "=== Server Log ($LOG_FILE) ==="
if [ -f "$LOG_FILE" ]; then
  echo "(Last 50 lines)"
  tail -50 "$LOG_FILE"
else
  echo "(No log file found - server may not have been started with /monitor)"
fi

echo ""
echo "=== End of Logs ==="
echo "Tip: Use 'tail -f $LOG_FILE' to follow logs in real-time"
```

## Notes

- Shows last 50 lines from the log file
- Displays current server status (running/stopped)
- Shows pipeline database stats (total runs, latest run)
- Log file only exists if server was started via `/monitor`
- For real-time logs, use `tail -f /tmp/pipeline-monitor.log`
