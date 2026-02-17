# /monitor-restart Command

Restart the Pipeline Monitor server (stop then start).

## Usage

When the user types `/monitor-restart`:

1. Stop any running server on port 8111
2. Start fresh server
3. Open the browser

## Implementation

Execute the following:

```bash
echo "=== Restarting Pipeline Monitor ==="
echo ""

PROJECT_DIR="/Users/oliviagao/project/starbridge"
LOG_FILE="/tmp/pipeline-monitor.log"

# Stop server
echo "Stopping server..."
if lsof -ti :8111 > /dev/null 2>&1; then
  lsof -ti :8111 | xargs kill -9 2>/dev/null
  echo "  Stopped Pipeline Monitor server"
else
  echo "  Pipeline Monitor server was not running"
fi

# Brief pause to ensure port is released
sleep 1

# Start server
echo ""
echo "Starting server..."
cd "$PROJECT_DIR" && python -m agent.server > "$LOG_FILE" 2>&1 &
sleep 2

# Verify server started
if ! lsof -i :8111 > /dev/null 2>&1; then
  echo ""
  echo "ERROR: Server failed to start. Check $LOG_FILE for details."
  exit 1
fi

# Open browser
open http://localhost:8111
echo ""
echo "Pipeline Monitor restarted and opened in browser"
echo "Log: $LOG_FILE"
```

## Notes

- Useful after making changes to server.py or pipeline-explorer.html
- Forces fresh server instance (doesn't reuse existing)
- Waits 1 second after stopping to ensure port is released
- Same behavior as running `/monitor-stop` then `/monitor`
